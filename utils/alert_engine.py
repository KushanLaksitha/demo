"""
Alert Engine — monitors ML predictions against critical thresholds
and generates alerts that should be persisted and shown to users.

Each alert dict:
  {
    "alert_type": str,     # e.g. "price_spike", "heavy_rain"
    "severity": "high" | "medium" | "low",
    "icon": str,           # MDIcon name
    "message": str,        # human-readable alert text
    "vegetable": str,      # relevant crop (or None for weather)
  }
"""

# ═══════════════════════════════════════════════════════════════════════════
# Threshold constants
# ═══════════════════════════════════════════════════════════════════════════

PRICE_SPIKE_PCT = 20.0       # predicted > 20% above current → high alert
PRICE_DROP_PCT = 15.0        # predicted < 15% below current → medium alert
HEAVY_RAIN_THRESHOLD = 150.0 # mm → heavy rain alert
DROUGHT_THRESHOLD = 30.0     # mm → drought risk alert
PROD_SURPLUS_MULT = 1.30     # 130% of baseline → supply surplus
PROD_SHORTAGE_MULT = 0.70    # 70% of baseline → supply shortage

# Approximate seasonal production baseline per vegetable (Mt)
# Derived from dataset averages
PRODUCTION_BASELINES = {
    "Beans":   3073.0,
    "Cabbage": 9000.0,
    "Carrots": 5000.0,
    "Leeks":   3800.0,
    "Okra":    4000.0,
}
DEFAULT_BASELINE = 1300.0


def generate_alerts(predictions, current_prices=None):
    """Analyse ML predictions and return a list of alert dicts for
    conditions that exceed critical thresholds.

    Parameters
    ----------
    predictions : dict — output of ml_engine.run_all_predictions()
    current_prices : dict — {vegetable_name: current_price_per_kg}

    Returns
    -------
    list[dict] — alert items (only threshold-exceeding conditions)
    """
    alerts = []

    price_preds = predictions.get("price_predictions", {})
    prod_preds = predictions.get("production_predictions", {})
    rainfall_pred = predictions.get("rainfall_prediction")
    district = predictions.get("district", "")

    if current_prices is None:
        current_prices = {}

    # ──────────────────────────────────────────────────────────────────
    # 1. Price alerts
    # ──────────────────────────────────────────────────────────────────
    for veg, pred_price in price_preds.items():
        if pred_price is None:
            continue
        cur_price = current_prices.get(veg)
        if not cur_price or cur_price <= 0:
            continue

        change_pct = ((pred_price - cur_price) / cur_price) * 100

        if change_pct >= PRICE_SPIKE_PCT:
            alerts.append({
                "alert_type": "price_spike",
                "severity": "high",
                "icon": "arrow-up-bold-circle",
                "message": (
                    f"🔴 {veg} price predicted to spike to Rs.{pred_price:.0f}/kg "
                    f"(+{change_pct:.0f}% from Rs.{cur_price:.0f}/kg) in {district}. "
                    f"Consider selling soon for maximum profit."
                ),
                "vegetable": veg,
            })
        elif change_pct <= -PRICE_DROP_PCT:
            alerts.append({
                "alert_type": "price_drop",
                "severity": "medium",
                "icon": "arrow-down-bold-circle",
                "message": (
                    f"🟡 {veg} price may drop to Rs.{pred_price:.0f}/kg "
                    f"({change_pct:.0f}% from Rs.{cur_price:.0f}/kg) in {district}. "
                    f"Hold stock or find alternative markets."
                ),
                "vegetable": veg,
            })

    # ──────────────────────────────────────────────────────────────────
    # 2. Weather alerts
    # ──────────────────────────────────────────────────────────────────
    if rainfall_pred is not None:
        if rainfall_pred > HEAVY_RAIN_THRESHOLD:
            alerts.append({
                "alert_type": "heavy_rain",
                "severity": "high",
                "icon": "weather-pouring",
                "message": (
                    f"🔴 Heavy rainfall predicted ({rainfall_pred:.0f}mm) in {district}. "
                    f"Protect crops from waterlogging and fungal disease. "
                    f"Postpone fertilizer application and outdoor planting."
                ),
                "vegetable": None,
            })
        elif rainfall_pred < DROUGHT_THRESHOLD:
            alerts.append({
                "alert_type": "drought_risk",
                "severity": "medium",
                "icon": "weather-sunny-alert",
                "message": (
                    f"🟡 Very low rainfall forecast ({rainfall_pred:.0f}mm) in {district}. "
                    f"Drought conditions possible — increase irrigation and "
                    f"apply mulching to conserve soil moisture."
                ),
                "vegetable": None,
            })

    # ──────────────────────────────────────────────────────────────────
    # 3. Production alerts
    # ──────────────────────────────────────────────────────────────────
    for veg, pred_prod in prod_preds.items():
        if pred_prod is None:
            continue

        baseline = PRODUCTION_BASELINES.get(veg, DEFAULT_BASELINE)

        if pred_prod > baseline * PROD_SURPLUS_MULT:
            alerts.append({
                "alert_type": "production_surplus",
                "severity": "medium",
                "icon": "package-variant-plus",
                "message": (
                    f"🟡 {veg} production surplus expected ({pred_prod:.0f} Mt, "
                    f"{((pred_prod / baseline) * 100):.0f}% of seasonal average). "
                    f"Prices may dip due to oversupply — plan early sales."
                ),
                "vegetable": veg,
            })
        elif pred_prod < baseline * PROD_SHORTAGE_MULT:
            alerts.append({
                "alert_type": "production_shortage",
                "severity": "high",
                "icon": "package-variant-minus",
                "message": (
                    f"🔴 {veg} production shortage predicted ({pred_prod:.0f} Mt, "
                    f"only {((pred_prod / baseline) * 100):.0f}% of seasonal average). "
                    f"Expect higher prices — opportunity for growers who can supply."
                ),
                "vegetable": veg,
            })

    # Sort: high severity first
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 9))

    return alerts
