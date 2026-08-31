"""
ML Prediction Engine — loads trained .pkl models and generates predictions.

Models:
  • best_price_model.pkl     — RandomForest   → Price (Rs/kg)
  • best_production_model.pkl — GradientBoosting → Production Volume (Mt)
  • best_weather_model.pkl   — GradientBoosting → Rainfall (mm)

All feature ordering and categorical encoding follow model_metadata.json
and encoders.json produced by the training pipeline.
"""
import os
import json
import threading
import joblib
from datetime import datetime, date

import numpy as np

# ─── Paths ────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUTPUTS_DIR = os.path.join(_BASE_DIR, "AgriSense_outputs")
_MODELS_DIR = os.path.join(_OUTPUTS_DIR, "models")
_METADATA_PATH = os.path.join(_OUTPUTS_DIR, "model_metadata.json")
_ENCODERS_PATH = os.path.join(_OUTPUTS_DIR, "encoders.json")

# ─── Singleton model cache (thread-safe lazy load) ────────────────────────
_lock = threading.Lock()
_models = {}        # key → loaded sklearn model
_metadata = None    # parsed model_metadata.json
_encoders = None    # parsed encoders.json


# ══════════════════════════════════════════════════════════════════════════
# Loading helpers
# ══════════════════════════════════════════════════════════════════════════

def _ensure_loaded():
    """Thread-safe lazy load of all models + metadata + encoders."""
    global _models, _metadata, _encoders
    if _metadata is not None:
        return  # already loaded
    with _lock:
        if _metadata is not None:
            return  # double-check after acquiring lock
        try:
            with open(_METADATA_PATH, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
            with open(_ENCODERS_PATH, "r", encoding="utf-8") as f:
                _encoders = json.load(f)
            for key in ("price_model", "production_model", "weather_model"):
                model_file = os.path.join(_OUTPUTS_DIR, _metadata[key]["file"])
                _models[key] = joblib.load(model_file)  # joblib handles cross-numpy-version pkl correctly
            print("[ML] All 3 models loaded successfully.")
        except Exception as e:
            print(f"[ML] Model loading failed: {e}")
            _metadata = {}  # prevent re-attempts on every call


def get_encoders():
    """Return the encoder mapping dict (Season / Vegetable / District → int)."""
    _ensure_loaded()
    return _encoders or {}


# ══════════════════════════════════════════════════════════════════════════
# Categorical encoding
# ══════════════════════════════════════════════════════════════════════════

def encode_value(category_type, value):
    """Encode a single categorical value using encoders.json.
    category_type: 'Season' | 'Vegetable' | 'District'
    value: e.g. 'Maha', 'Beans', 'Kandy'
    Returns integer code, or 0 as fallback.
    """
    _ensure_loaded()
    if not _encoders or category_type not in _encoders:
        return 0
    return _encoders[category_type].get(value, 0)


def _current_season():
    """Return 'Maha' or 'Yala' based on the current month."""
    m = datetime.now().month
    return "Maha" if m in (10, 11, 12, 1, 2, 3) else "Yala"


# ══════════════════════════════════════════════════════════════════════════
# Individual model predictions
# ══════════════════════════════════════════════════════════════════════════

def predict_price(vegetable, district, season=None,
                  temperature=26.0, rainfall=140.0, humidity=80.0,
                  cultivated_area=100.0, yield_per_ha=10.0,
                  price_lag_1=200.0, price_lag_2=195.0, price_lag_3=190.0,
                  price_rolling_mean_3=None,
                  week_no=None, month=None, year=None):
    """Predict price (Rs/kg) for a vegetable in a district.

    Features required (exact order from model_metadata.json):
      Week No, Month, Year, Season_enc, Vegetable_enc, District_enc,
      Temperature (°C), Rainfall (mm), Humidity (%),
      Cultivated Area (ha), Yield (Mt/ha),
      Price_lag_1, Price_lag_2, Price_lag_3, Price_rolling_mean_3
    """
    _ensure_loaded()
    model = _models.get("price_model")
    if model is None:
        return None

    now = datetime.now()
    if season is None:
        season = _current_season()
    if week_no is None:
        week_no = now.isocalendar()[1]
    if month is None:
        month = now.month
    if year is None:
        year = now.year
    if price_rolling_mean_3 is None:
        price_rolling_mean_3 = round((price_lag_1 + price_lag_2 + price_lag_3) / 3, 2)

    features = np.array([[
        week_no, month, year,
        encode_value("Season", season),
        encode_value("Vegetable", vegetable),
        encode_value("District", district),
        temperature, rainfall, humidity,
        cultivated_area, yield_per_ha,
        price_lag_1, price_lag_2, price_lag_3,
        price_rolling_mean_3,
    ]], dtype=np.float64)

    try:
        pred = model.predict(features)[0]
        return round(float(pred), 2)
    except Exception as e:
        print(f"[ML] Price prediction error: {e}")
        return None


def predict_production(vegetable, district, season=None,
                       cultivated_area=100.0,
                       temperature=26.0, rainfall=140.0, humidity=80.0,
                       production_lag_1=1000.0,
                       year=None):
    """Predict production volume (Mt) for a vegetable in a district.

    Features required (exact order from model_metadata.json):
      Year, Season_enc, Vegetable_enc, District_enc,
      Cultivated Area (ha), Temperature (°C), Rainfall (mm), Humidity (%),
      Production_lag_1
    """
    _ensure_loaded()
    model = _models.get("production_model")
    if model is None:
        return None

    now = datetime.now()
    if season is None:
        season = _current_season()
    if year is None:
        year = now.year

    features = np.array([[
        year,
        encode_value("Season", season),
        encode_value("Vegetable", vegetable),
        encode_value("District", district),
        cultivated_area, temperature, rainfall, humidity,
        production_lag_1,
    ]], dtype=np.float64)

    try:
        pred = model.predict(features)[0]
        return round(float(pred), 2)
    except Exception as e:
        print(f"[ML] Production prediction error: {e}")
        return None


def predict_rainfall(district, temperature=26.0, humidity=80.0,
                     rainfall_lag_1=120.0,
                     month=None, year=None):
    """Predict rainfall (mm) for a district.

    Features required (exact order from model_metadata.json):
      Month, Year, District_enc, Temperature (°C), Humidity (%),
      Rainfall_lag_1
    """
    _ensure_loaded()
    model = _models.get("weather_model")
    if model is None:
        return None

    now = datetime.now()
    if month is None:
        month = now.month
    if year is None:
        year = now.year

    features = np.array([[
        month, year,
        encode_value("District", district),
        temperature, humidity,
        rainfall_lag_1,
    ]], dtype=np.float64)

    try:
        pred = model.predict(features)[0]
        return round(float(max(0, pred)), 2)  # rainfall can't be negative
    except Exception as e:
        print(f"[ML] Rainfall prediction error: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# Batch prediction for a user's context
# ══════════════════════════════════════════════════════════════════════════

def run_all_predictions(district, vegetable_names,
                        current_weather=None, lag_data=None):
    """Run price + production + weather predictions for each vegetable
    in the given district.

    Parameters
    ----------
    district : str            — 'Kandy' or 'Matale'
    vegetable_names : list    — e.g. ['Beans', 'Cabbage', 'Carrots']
    current_weather : dict    — {temperature, rainfall, humidity} (optional)
    lag_data : dict           — keyed by vegetable, values are dicts with
                                 price_lag_1/2/3, production_lag_1, etc.

    Returns
    -------
    dict with keys:
      'price_predictions'      — {vegetable: predicted_price}
      'production_predictions'  — {vegetable: predicted_production}
      'rainfall_prediction'     — predicted rainfall (mm) for the district
      'current_weather'         — the weather dict used
    """
    _ensure_loaded()

    if current_weather is None:
        current_weather = {"temperature": 26.0, "rainfall": 140.0, "humidity": 80.0}
    if lag_data is None:
        lag_data = {}

    season = _current_season()
    results = {
        "price_predictions": {},
        "production_predictions": {},
        "rainfall_prediction": None,
        "current_weather": current_weather,
        "season": season,
        "district": district,
    }

    # Weather prediction (once per district)
    rainfall_pred = predict_rainfall(
        district=district,
        temperature=current_weather.get("temperature", 26.0),
        humidity=current_weather.get("humidity", 80.0),
        rainfall_lag_1=current_weather.get("rainfall", 120.0),
    )
    results["rainfall_prediction"] = rainfall_pred

    # Per-vegetable predictions
    for veg in vegetable_names:
        veg_lags = lag_data.get(veg, {})

        price = predict_price(
            vegetable=veg, district=district, season=season,
            temperature=current_weather.get("temperature", 26.0),
            rainfall=current_weather.get("rainfall", 140.0),
            humidity=current_weather.get("humidity", 80.0),
            cultivated_area=veg_lags.get("cultivated_area", 100.0),
            yield_per_ha=veg_lags.get("yield_per_ha", 10.0),
            price_lag_1=veg_lags.get("price_lag_1", 200.0),
            price_lag_2=veg_lags.get("price_lag_2", 195.0),
            price_lag_3=veg_lags.get("price_lag_3", 190.0),
        )
        results["price_predictions"][veg] = price

        production = predict_production(
            vegetable=veg, district=district, season=season,
            cultivated_area=veg_lags.get("cultivated_area", 100.0),
            temperature=current_weather.get("temperature", 26.0),
            rainfall=current_weather.get("rainfall", 140.0),
            humidity=current_weather.get("humidity", 80.0),
            production_lag_1=veg_lags.get("production_lag_1", 1000.0),
        )
        results["production_predictions"][veg] = production

    return results


def preload_models():
    """Explicitly trigger model loading (call on app startup)."""
    _ensure_loaded()
    return bool(_models)
