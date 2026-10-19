"""
ML Prediction Engine — AgriSense v2
====================================
Connects to the trained models exported in `agrisense_export/`.

Models loaded:
  • agrisense_export/models/price_lstm_{crop}.keras   — Keras LSTM (per crop)
  • agrisense_export/scalers/price_scaler_{crop}.pkl  — MinMaxScaler for LSTM
  • agrisense_export/models/production_rf.pkl          — Random Forest (production)
  • agrisense_export/models/production_rf_features.pkl — RF feature list
  • agrisense_export/models/sarima_{crop}.pkl          — SARIMA fitted model (lazy-loaded)

LSTM input:  shape (batch, 13, 11)
  Features (in order):
    Price (Rs/kg), ma_4, ma_12, lag_1, lag_4,
    yoy_change, District_enc, Season_enc, month, week_sin, week_cos

RF features (in order from production_rf_features.pkl):
    Veg_enc, Dist_enc, Year, Season_enc, Cultivated Area (ha), prod_lag_1

Public API (backward-compatible with existing callers):
  preload_models()                        → bool
  predict_price(crop, district, ...)      → float | None
  predict_production(vegetable, district, ...)  → float | None
  predict_price_sarima(crop, steps)       → list[float] | None
  run_all_predictions(district, vegetable_names, current_weather, lag_data) → dict
"""

import os
import math
import threading
import joblib
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=UserWarning)

import numpy as np

# ─── Paths ────────────────────────────────────────────────────────────────────
_BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXPORT_DIR  = os.path.join(_BASE_DIR, "agrisense_export")
_MODELS_DIR  = os.path.join(_EXPORT_DIR, "models")
_SCALERS_DIR = os.path.join(_EXPORT_DIR, "scalers")

# ─── Constants from training pipeline ─────────────────────────────────────────
LOOKBACK       = 13          # LSTM sequence length (weeks)
N_FEATURES     = 11          # number of LSTM input features
VEGETABLES     = ["Beans", "Cabbage", "Carrots", "Leeks", "Okra"]
DISTRICTS      = ["Kandy", "Matale"]          # sorted alphabetically → enc 0/1

# Categorical encodings must match training (alphabetical sort used in notebook)
_VEG_ENC  = {v: i for i, v in enumerate(sorted(VEGETABLES))}   # Beans→0 … Okra→4
_DIST_ENC = {d: i for i, d in enumerate(sorted(DISTRICTS))}    # Kandy→0, Matale→1
_SEASON_ENC = {"Maha": 0, "Yala": 1}

# ─── Thread-safe singleton caches ─────────────────────────────────────────────
_lock           = threading.Lock()
_lstm_models    = {}   # crop_lower → keras model
_lstm_scalers   = {}   # crop_lower → MinMaxScaler
_rf_model       = None
_rf_features    = None   # list[str]
_sarima_models  = {}   # crop_lower → fitted SARIMAXResults (lazy)
_models_loaded  = False


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════

def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


class NumpyLSTMModel:
    """Pure NumPy forward pass for the 2-layer LSTM + 2-layer Dense Keras models.
    Requires only numpy and h5py (no TensorFlow/PyTorch installation required).
    Architecture:
      • InputLayer (batch, 13, 11)
      • LSTM (units=64, return_sequences=True, activation='tanh', recurrent_activation='sigmoid')
      • LSTM (units=32, return_sequences=False, activation='tanh', recurrent_activation='sigmoid')
      • Dense (units=16, activation='relu')
      • Dense (units=1, activation='linear')
    """
    def __init__(self, keras_path):
        import zipfile
        import io
        import h5py
        with zipfile.ZipFile(keras_path, "r") as z:
            with h5py.File(io.BytesIO(z.read("model.weights.h5")), "r") as f:
                self.w_lstm1 = np.array(f["layers/lstm/cell/vars/0"], dtype=np.float32)
                self.u_lstm1 = np.array(f["layers/lstm/cell/vars/1"], dtype=np.float32)
                self.b_lstm1 = np.array(f["layers/lstm/cell/vars/2"], dtype=np.float32)

                self.w_lstm2 = np.array(f["layers/lstm_1/cell/vars/0"], dtype=np.float32)
                self.u_lstm2 = np.array(f["layers/lstm_1/cell/vars/1"], dtype=np.float32)
                self.b_lstm2 = np.array(f["layers/lstm_1/cell/vars/2"], dtype=np.float32)

                self.w_dense1 = np.array(f["layers/dense/vars/0"], dtype=np.float32)
                self.b_dense1 = np.array(f["layers/dense/vars/1"], dtype=np.float32)

                self.w_dense2 = np.array(f["layers/dense_1/vars/0"], dtype=np.float32)
                self.b_dense2 = np.array(f["layers/dense_1/vars/1"], dtype=np.float32)

    def predict(self, X, verbose=0):
        # X shape: (batch_size, seq_len, 11)
        batch_size, seq_len, _ = X.shape

        # Layer 1: LSTM(64, return_sequences=True)
        h1 = np.zeros((batch_size, 64), dtype=np.float32)
        c1 = np.zeros((batch_size, 64), dtype=np.float32)
        seq_out = []
        for t in range(seq_len):
            xt = X[:, t, :]
            z = xt @ self.w_lstm1 + h1 @ self.u_lstm1 + self.b_lstm1
            zi, zf, zc, zo = np.split(z, 4, axis=-1)
            i = _sigmoid(zi)
            f = _sigmoid(zf)
            c1 = f * c1 + i * np.tanh(zc)
            h1 = _sigmoid(zo) * np.tanh(c1)
            seq_out.append(h1)
        seq_out = np.stack(seq_out, axis=1)

        # Layer 2: LSTM(32, return_sequences=False)
        h2 = np.zeros((batch_size, 32), dtype=np.float32)
        c2 = np.zeros((batch_size, 32), dtype=np.float32)
        for t in range(seq_len):
            xt = seq_out[:, t, :]
            z = xt @ self.w_lstm2 + h2 @ self.u_lstm2 + self.b_lstm2
            zi, zf, zc, zo = np.split(z, 4, axis=-1)
            i = _sigmoid(zi)
            f = _sigmoid(zf)
            c2 = f * c2 + i * np.tanh(zc)
            h2 = _sigmoid(zo) * np.tanh(c2)

        # Dense 1 (relu)
        d1 = np.maximum(0.0, h2 @ self.w_dense1 + self.b_dense1)
        # Dense 2 (linear)
        out = d1 @ self.w_dense2 + self.b_dense2
        return out


# ─── Mobile Export Precomputed Fallbacks ───────────────────────────────────────
_mobile_export_data = None


def _get_mobile_export():
    global _mobile_export_data
    if _mobile_export_data is not None:
        return _mobile_export_data
    try:
        path = os.path.join(_EXPORT_DIR, "data", "mobile_export.json")
        if os.path.exists(path):
            import json
            with open(path, "r", encoding="utf-8") as f:
                _mobile_export_data = json.load(f)
    except Exception as e:
        print(f"[ML] Error loading mobile_export.json: {e}")
        _mobile_export_data = {}
    return _mobile_export_data or {}


def _normalize_crop(name):
    if not name:
        return "beans"
    n = str(name).strip().lower()
    if n in ("bean", "beans"):
        return "beans"
    if n in ("carrot", "carrots"):
        return "carrots"
    if n in ("leek", "leeks"):
        return "leeks"
    if n in ("cabbage", "cabbages"):
        return "cabbage"
    if n in ("okra", "ladies finger", "lady's finger", "bandakka"):
        return "okra"
    return n


def _canonical_veg(name):
    k = _normalize_crop(name)
    mapping = {
        "beans": "Beans",
        "cabbage": "Cabbage",
        "carrots": "Carrots",
        "leeks": "Leeks",
        "okra": "Okra",
    }
    return mapping.get(k, name.capitalize() if name else "Beans")


def _get_precomputed_price(crop, district="Kandy"):
    data = _get_mobile_export()
    forecasts = data.get("next_week_price_forecast", [])
    crop_norm = _normalize_crop(crop)
    dist_norm = (district or "Kandy").strip().capitalize()
    for item in forecasts:
        if _normalize_crop(item.get("vegetable")) == crop_norm:
            if item.get("district", "").strip().capitalize() == dist_norm:
                return float(item.get("predicted_price_rs_per_kg", 0.0))
    for item in forecasts:
        if _normalize_crop(item.get("vegetable")) == crop_norm:
            return float(item.get("predicted_price_rs_per_kg", 0.0))
    return None


def _get_precomputed_production(crop, district="Kandy"):
    data = _get_mobile_export()
    forecasts = data.get("next_season_production_forecast", [])
    crop_norm = _normalize_crop(crop)
    dist_norm = (district or "Kandy").strip().capitalize()
    for item in forecasts:
        if _normalize_crop(item.get("vegetable")) == crop_norm:
            if item.get("district", "").strip().capitalize() == dist_norm:
                return float(item.get("predicted_production_mt", 0.0))
    for item in forecasts:
        if _normalize_crop(item.get("vegetable")) == crop_norm:
            return float(item.get("predicted_production_mt", 0.0))
    return None


def _load_keras_model(path):
    """Load a .keras model file using TensorFlow Keras or standalone keras if available.
    Otherwise seamlessly falls back to our pure NumPy NumpyLSTMModel.
    """
    try:
        import tensorflow as tf
        return tf.keras.models.load_model(path)
    except Exception:
        pass
    try:
        import keras
        return keras.models.load_model(path)
    except Exception:
        pass
    try:
        return NumpyLSTMModel(path)
    except Exception as e:
        print(f"[ML] NumpyLSTMModel fallback error for {path}: {e}")
        return None


def _ensure_loaded():
    """Thread-safe lazy load of LSTM + RF models and their scalers."""
    global _lstm_models, _lstm_scalers, _rf_model, _rf_features, _models_loaded
    if _models_loaded:
        return
    with _lock:
        if _models_loaded:
            return

        loaded_count = 0

        # ── LSTM price models ──────────────────────────────────────────────
        for veg in VEGETABLES:
            key  = veg.lower()
            mpath = os.path.join(_MODELS_DIR,  f"price_lstm_{key}.keras")
            spath = os.path.join(_SCALERS_DIR, f"price_scaler_{key}.pkl")

            try:
                model = _load_keras_model(mpath)
                if model is not None:
                    _lstm_models[key] = model
                    loaded_count += 1
                else:
                    print(f"[ML] LSTM model could not be loaded for {veg}")
            except Exception as e:
                print(f"[ML] LSTM model load error for {veg}: {e}")

            try:
                _lstm_scalers[key] = joblib.load(spath)
            except Exception as e:
                print(f"[ML] Scaler load error for {veg}: {e}")

        # ── Random Forest production model ─────────────────────────────────
        rf_path   = os.path.join(_MODELS_DIR, "production_rf.pkl")
        feat_path = os.path.join(_MODELS_DIR, "production_rf_features.pkl")
        try:
            _rf_model    = joblib.load(rf_path)
            _rf_features = joblib.load(feat_path)
            loaded_count += 1
            print(f"[ML] RF production model loaded. Features: {_rf_features}")
        except Exception as e:
            print(f"[ML] RF model load error: {e}")

        _models_loaded = True
        print(f"[ML] Model loading complete. {loaded_count} model(s) ready.")


def _load_sarima(crop_key):
    """Lazy-load a SARIMA model for a single crop (they are large ~530MB each)."""
    global _sarima_models
    if crop_key in _sarima_models:
        return _sarima_models[crop_key]
    path = os.path.join(_MODELS_DIR, f"sarima_{crop_key}.pkl")
    if not os.path.exists(path):
        print(f"[ML] SARIMA model not found: {path}")
        return None
    try:
        model = joblib.load(path)
        _sarima_models[crop_key] = model
        print(f"[ML] SARIMA model loaded for {crop_key}.")
        return model
    except Exception as e:
        print(f"[ML] SARIMA load error for {crop_key}: {e}")
        return None


def _current_season():
    """Return 'Maha' or 'Yala' based on current month."""
    m = datetime.now().month
    return "Maha" if m in (10, 11, 12, 1, 2, 3) else "Yala"


def _build_lstm_sequence(price_history, district, season, current_price):
    """
    Build the LSTM input sequence array: shape (1, LOOKBACK, N_FEATURES).

    price_history: list of recent prices (most recent last).
                   Should have >= LOOKBACK+1 entries; padded if shorter.
    district: str  e.g. 'Kandy'
    season:   str  e.g. 'Maha'
    current_price: float (latest known price)
    """
    now = datetime.now()
    month     = now.month
    week_no   = now.isocalendar()[1]
    week_sin  = math.sin(2 * math.pi * week_no / 52)
    week_cos  = math.cos(2 * math.pi * week_no / 52)
    dist_enc  = _DIST_ENC.get(district, 0)
    season_enc = _SEASON_ENC.get(season, 0)

    # Ensure enough price history — pad front with mean if needed
    hist = list(price_history)
    if len(hist) < LOOKBACK + 1:
        fill = hist[0] if hist else current_price
        hist = [fill] * (LOOKBACK + 1 - len(hist)) + hist

    # Use last (LOOKBACK+4) entries to compute rolling stats; take last LOOKBACK as window
    working = hist[-(LOOKBACK + 12):]   # enough for ma_12

    seq = []
    for i in range(len(working) - LOOKBACK, len(working)):
        window = working[max(0, i - 11):i + 1]   # up to 12 values for ma_12
        p     = working[i]
        ma4   = float(np.mean(working[max(0, i - 3):i + 1]))
        ma12  = float(np.mean(window[-12:]))
        lag1  = working[i - 1] if i >= 1 else p
        lag4  = working[i - 4] if i >= 4 else p
        # yoy not available at runtime → use 0
        yoy   = 0.0
        seq.append([p, ma4, ma12, lag1, lag4, yoy,
                    dist_enc, season_enc, month, week_sin, week_cos])

    # Take last LOOKBACK rows
    seq = seq[-LOOKBACK:]
    if len(seq) < LOOKBACK:
        pad = seq[0] if seq else [current_price, current_price, current_price,
                                   current_price, current_price, 0,
                                   dist_enc, season_enc, month, week_sin, week_cos]
        seq = [pad] * (LOOKBACK - len(seq)) + seq

    return np.array(seq, dtype=np.float32)   # shape (LOOKBACK, N_FEATURES)


# ══════════════════════════════════════════════════════════════════════════════
# Public prediction functions
# ══════════════════════════════════════════════════════════════════════════════

def predict_price(crop, district="Kandy", price_history=None,
                  current_price=200.0, season=None):
    """
    Predict next-week price (Rs/kg) for a crop using the per-crop LSTM model.

    Parameters
    ----------
    crop          : str   e.g. 'Beans'
    district      : str   'Kandy' | 'Matale'
    price_history : list  recent weekly prices, most recent last (at least 13)
    current_price : float latest known price (used when price_history is short)
    season        : str   'Maha' | 'Yala' (auto-detected if None)

    Returns
    -------
    float | None
    """
    _ensure_loaded()
    key = _normalize_crop(crop)
    dist_clean = (district or "Kandy").strip().capitalize()
    if dist_clean not in DISTRICTS:
        dist_clean = "Kandy"

    model  = _lstm_models.get(key)
    scaler = _lstm_scalers.get(key)
    if model is None or scaler is None:
        fb = _get_precomputed_price(key, dist_clean)
        return fb

    if season is None:
        season = _current_season()
    if price_history is None:
        price_history = [current_price] * (LOOKBACK + 1)

    try:
        seq = _build_lstm_sequence(price_history, dist_clean, season, current_price)

        # Scale using fitted scaler (all 11 features)
        seq_scaled = scaler.transform(seq)                          # (LOOKBACK, N_FEATURES)
        X = seq_scaled[np.newaxis, ...]                             # (1, LOOKBACK, N_FEATURES)

        pred_scaled = float(model.predict(X, verbose=0)[0][0])

        # Inverse-transform: price is col 0, fill rest with zeros
        dummy = np.zeros((1, N_FEATURES), dtype=np.float32)
        dummy[0, 0] = pred_scaled
        price_rs = float(scaler.inverse_transform(dummy)[0, 0])
        return round(max(10.0, price_rs), 2)
    except Exception as e:
        print(f"[ML] predict_price error for {crop}: {e}")
        fb = _get_precomputed_price(key, dist_clean)
        return fb


def predict_production(vegetable, district="Kandy", season=None,
                       year=None, cultivated_area=100.0, prod_lag_1=1000.0):
    """
    Predict production volume (Mt) using the Random Forest model.

    Parameters
    ----------
    vegetable      : str   e.g. 'Beans'
    district       : str   'Kandy' | 'Matale'
    season         : str   'Maha' | 'Yala' (auto-detected if None)
    year           : int   prediction year (defaults to current year)
    cultivated_area: float hectares (default 100.0)
    prod_lag_1     : float previous season's production (Mt)

    Returns
    -------
    float | None
    """
    _ensure_loaded()
    canon_veg = _canonical_veg(vegetable)
    dist_clean = (district or "Kandy").strip().capitalize()
    if dist_clean not in DISTRICTS:
        dist_clean = "Kandy"

    if _rf_model is None or _rf_features is None:
        return _get_precomputed_production(canon_veg, dist_clean)

    if season is None:
        season = _current_season()
    if year is None:
        year = datetime.now().year

    veg_enc    = _VEG_ENC.get(canon_veg, 0)
    dist_enc   = _DIST_ENC.get(dist_clean, 0)
    season_enc = _SEASON_ENC.get(season, 0)

    # Build feature vector in the exact order from production_rf_features.pkl
    feature_map = {
        "Veg_enc":              veg_enc,
        "Dist_enc":             dist_enc,
        "Year":                 float(year),
        "Season_enc":           season_enc,
        "Cultivated Area (ha)": cultivated_area,
        "prod_lag_1":           prod_lag_1,
    }

    try:
        import pandas as pd
        X = pd.DataFrame([[feature_map.get(f, 0.0) for f in _rf_features]],
                         columns=_rf_features)
        pred = float(_rf_model.predict(X)[0])
        return round(max(0.0, pred), 2)
    except Exception as e:
        print(f"[ML] predict_production error for {vegetable}: {e}")
        return _get_precomputed_production(canon_veg, dist_clean)


def predict_price_sarima(crop, steps=8):
    """
    Generate a multi-step price forecast using the SARIMA model for a crop.
    NOTE: SARIMA models are large (~530MB). They are lazy-loaded on first call.

    Parameters
    ----------
    crop  : str  e.g. 'Beans'
    steps : int  number of weeks to forecast (default 8)

    Returns
    -------
    list[float] | None   — forecasted prices for `steps` weeks ahead
    """
    key = _normalize_crop(crop)
    model = _load_sarima(key)
    if model is not None:
        try:
            forecast = model.get_forecast(steps=steps)
            values = forecast.predicted_mean.tolist()
            return [round(max(0.0, float(v)), 2) for v in values]
        except Exception as e:
            print(f"[ML] SARIMA forecast error for {crop}: {e}")

    # Fallback projection from LSTM baseline if SARIMA model unavailable
    base_p = predict_price(crop)
    if base_p is not None:
        # Generate smooth slight seasonal trend
        return [round(base_p * (1.0 + 0.015 * math.sin(i * 0.5)), 2) for i in range(1, steps + 1)]
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Batch prediction (called by recommendation_engine & dashboard)
# ══════════════════════════════════════════════════════════════════════════════

def run_all_predictions(district, vegetable_names,
                        current_weather=None, lag_data=None):
    """
    Run LSTM price + RF production predictions for each vegetable.

    Parameters
    ----------
    district       : str   'Kandy' | 'Matale'
    vegetable_names: list  e.g. ['Beans', 'Cabbage']
    current_weather: dict  {temperature, rainfall, humidity} (unused by new models,
                           kept for API compatibility with recommendation_engine)
    lag_data       : dict  keyed by vegetable name → dict with keys:
                           price_lag_1, price_lag_2, price_lag_3,
                           production_lag_1, cultivated_area, yield_per_ha,
                           price_history (optional list of recent weekly prices)

    Returns
    -------
    dict with keys:
      'price_predictions'       — {veg: predicted_price_float | None}
      'production_predictions'  — {veg: predicted_production_float | None}
      'rainfall_prediction'     — None  (no weather model in new export; kept for compat)
      'current_weather'         — the weather dict passed in
      'season'                  — current season string
      'district'                — district string
    """
    _ensure_loaded()

    if current_weather is None:
        current_weather = {"temperature": 26.0, "rainfall": 140.0, "humidity": 80.0}
    if lag_data is None:
        lag_data = {}

    season = _current_season()
    results = {
        "price_predictions":      {},
        "production_predictions": {},
        "rainfall_prediction":    None,   # no weather model in agrisense_export
        "current_weather":        current_weather,
        "season":                 season,
        "district":               district,
    }

    for veg in vegetable_names:
        veg_lags = lag_data.get(veg, {})

        # Build price history from lag values if no explicit history provided
        price_history = veg_lags.get("price_history", None)
        if price_history is None:
            p1 = veg_lags.get("price_lag_1", 200.0)
            p2 = veg_lags.get("price_lag_2", 195.0)
            p3 = veg_lags.get("price_lag_3", 190.0)
            # Oldest → newest
            price_history = [p3, p2, p1]

        price = predict_price(
            crop=veg,
            district=district,
            price_history=price_history,
            current_price=veg_lags.get("price_lag_1", 200.0),
            season=season,
        )
        results["price_predictions"][veg] = price

        production = predict_production(
            vegetable=veg,
            district=district,
            season=season,
            cultivated_area=veg_lags.get("cultivated_area", 100.0),
            prod_lag_1=veg_lags.get("production_lag_1", 1000.0),
        )
        results["production_predictions"][veg] = production

    return results


# ══════════════════════════════════════════════════════════════════════════════
# Startup helper
# ══════════════════════════════════════════════════════════════════════════════

def preload_models():
    """Trigger model loading explicitly (call at app startup in background)."""
    _ensure_loaded()
    return bool(_lstm_models) or (_rf_model is not None)
