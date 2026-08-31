"""
Smart Recommendation Engine — analyses ML predictions and generates
actionable farming, trading, and weather recommendations.

Each recommendation is a dict:
  {
    "type": "price" | "production" | "weather" | "combined",
    "severity": "info" | "positive" | "warning" | "critical",
    "icon": str,          # MDIcon name
    "title": str,         # short heading
    "message": str,       # detailed advice
    "vegetable": str,     # relevant crop (if applicable)
  }
"""

# ═══════════════════════════════════════════════════════════════════════════
# Thresholds
# ═══════════════════════════════════════════════════════════════════════════

PRICE_SURGE_PCT = 15.0        # % above current → "sell soon"
PRICE_DROP_PCT = 10.0         # % below current → "hold stock"
HEAVY_RAIN_MM = 150.0         # mm → heavy-rain advisory
LOW_RAIN_MM = 40.0            # mm → dry-spell advisory
HIGH_PRODUCTION_MULT = 1.30   # 130% of lag → oversupply
LOW_PRODUCTION_MULT = 0.70    # 70% of lag → shortage


def generate_recommendations(predictions, current_prices=None):
    """Generate a list of recommendation dicts from ML predictions.

    Parameters
    ----------
    predictions : dict — output of ml_engine.run_all_predictions()
        Expected keys:
        - price_predictions: {veg: predicted_price}
        - production_predictions: {veg: predicted_production}
        - rainfall_prediction: float (mm)
        - current_weather: {temperature, rainfall, humidity}
        - season: str
        - district: str

    current_prices : dict — {vegetable_name: current_price_per_kg}
        Used to compare predicted vs. current price. If None,
        price-change recommendations are skipped.

    Returns
    -------
    list[dict] — recommendation items sorted by severity
    """
    recs = []

    price_preds = predictions.get("price_predictions", {})
    prod_preds = predictions.get("production_predictions", {})
    rainfall_pred = predictions.get("rainfall_prediction")
    season = predictions.get("season", "")
    district = predictions.get("district", "")

    if current_prices is None:
        current_prices = {}

    # ──────────────────────────────────────────────────────────────────
    # 1. Price-based recommendations
    # ──────────────────────────────────────────────────────────────────
    for veg, pred_price in price_preds.items():
        if pred_price is None:
            continue
        cur_price = current_prices.get(veg)

        if cur_price and cur_price > 0:
            change_pct = ((pred_price - cur_price) / cur_price) * 100

            if change_pct >= PRICE_SURGE_PCT:
                recs.append({
                    "type": "price",
                    "severity": "positive",
                    "icon": "trending-up",
                    "title": f"{veg} Price Rising",
                    "message": (
                        f"AI predicts {veg} price will reach Rs.{pred_price:.0f}/kg "
                        f"(+{change_pct:.0f}% from current Rs.{cur_price:.0f}/kg). "
                        f"Consider selling soon to maximise revenue."
                    ),
                    "vegetable": veg,
                })
            elif change_pct <= -PRICE_DROP_PCT:
                recs.append({
                    "type": "price",
                    "severity": "warning",
                    "icon": "trending-down",
                    "title": f"{veg} Price Declining",
                    "message": (
                        f"AI forecasts {veg} price dropping to Rs.{pred_price:.0f}/kg "
                        f"({change_pct:.0f}% from current Rs.{cur_price:.0f}/kg). "
                        f"Consider holding stock and waiting for market recovery."
                    ),
                    "vegetable": veg,
                })
            else:
                recs.append({
                    "type": "price",
                    "severity": "info",
                    "icon": "chart-line",
                    "title": f"{veg} Price Stable",
                    "message": (
                        f"{veg} price predicted at Rs.{pred_price:.0f}/kg "
                        f"(~{change_pct:+.0f}% change). "
                        f"Good time for steady market supply."
                    ),
                    "vegetable": veg,
                })
        else:
            # No current price available — just report the prediction
            recs.append({
                "type": "price",
                "severity": "info",
                "icon": "chart-line",
                "title": f"{veg} Price Forecast",
                "message": (
                    f"AI predicts {veg} price at approximately Rs.{pred_price:.0f}/kg "
                    f"for the upcoming period in {district}."
                ),
                "vegetable": veg,
            })

    # ──────────────────────────────────────────────────────────────────
    # 2. Production-based recommendations
    # ──────────────────────────────────────────────────────────────────
    for veg, pred_prod in prod_preds.items():
        if pred_prod is None:
            continue

        # Use a baseline average for comparison (from dataset mean ~1342 Mt)
        # In practice we could use production_lag_1 per veg
        baseline = 1300.0  # approximate seasonal baseline

        if pred_prod > baseline * HIGH_PRODUCTION_MULT:
            recs.append({
                "type": "production",
                "severity": "warning",
                "icon": "package-variant",
                "title": f"{veg} Supply Surplus Expected",
                "message": (
                    f"High supply predicted for {veg} ({pred_prod:.0f} Mt). "
                    f"Market may be oversaturated — diversify crops or plan early sales "
                    f"to avoid price drops from oversupply."
                ),
                "vegetable": veg,
            })
        elif pred_prod < baseline * LOW_PRODUCTION_MULT:
            recs.append({
                "type": "production",
                "severity": "positive",
                "icon": "store",
                "title": f"{veg} Supply Shortage Predicted",
                "message": (
                    f"Low supply predicted for {veg} ({pred_prod:.0f} Mt). "
                    f"This creates a premium pricing opportunity — "
                    f"focus resources on {veg} production for higher returns."
                ),
                "vegetable": veg,
            })

    # ──────────────────────────────────────────────────────────────────
    # 3. Weather-based recommendations
    # ──────────────────────────────────────────────────────────────────
    if rainfall_pred is not None:
        if rainfall_pred > HEAVY_RAIN_MM:
            recs.append({
                "type": "weather",
                "severity": "critical",
                "icon": "weather-pouring",
                "title": "Heavy Rainfall Alert",
                "message": (
                    f"AI forecasts heavy rainfall ({rainfall_pred:.0f}mm) for {district}. "
                    f"Protect outdoor crops, improve field drainage, and delay "
                    f"any scheduled planting. Monitor for fungal disease risk."
                ),
                "vegetable": None,
            })
        elif rainfall_pred < LOW_RAIN_MM:
            recs.append({
                "type": "weather",
                "severity": "warning",
                "icon": "weather-sunny",
                "title": "Low Rainfall — Dry Spell",
                "message": (
                    f"Predicted rainfall only {rainfall_pred:.0f}mm for {district}. "
                    f"Increase irrigation schedules and consider mulching to retain "
                    f"soil moisture. Drought-sensitive crops need extra attention."
                ),
                "vegetable": None,
            })
        else:
            recs.append({
                "type": "weather",
                "severity": "info",
                "icon": "weather-partly-cloudy",
                "title": "Favorable Weather Ahead",
                "message": (
                    f"Moderate rainfall predicted ({rainfall_pred:.0f}mm) for {district}. "
                    f"Conditions look favorable for most crops — ideal window for planting."
                ),
                "vegetable": None,
            })

    # ──────────────────────────────────────────────────────────────────
    # 4. Combined cross-model insights
    # ──────────────────────────────────────────────────────────────────
    for veg in price_preds:
        pred_price = price_preds.get(veg)
        pred_prod = prod_preds.get(veg)
        cur_price = current_prices.get(veg)

        if pred_price is None or pred_prod is None:
            continue

        price_rising = (cur_price and cur_price > 0 and
                        ((pred_price - cur_price) / cur_price) * 100 >= 10.0)
        low_supply = pred_prod < 1300.0 * LOW_PRODUCTION_MULT

        if price_rising and low_supply:
            recs.append({
                "type": "combined",
                "severity": "positive",
                "icon": "star-circle",
                "title": f"Market Opportunity: {veg}",
                "message": (
                    f"Supply shortage predicted for {veg} with prices also rising. "
                    f"This is a strong market opportunity — prioritize {veg} "
                    f"production for maximum returns this {season} season."
                ),
                "vegetable": veg,
            })

        # Heavy rain + production risk
        if rainfall_pred and rainfall_pred > HEAVY_RAIN_MM and pred_prod is not None:
            if pred_prod < 1300.0:
                recs.append({
                    "type": "combined",
                    "severity": "critical",
                    "icon": "alert-octagon",
                    "title": f"Weather Risk for {veg}",
                    "message": (
                        f"Heavy rain ({rainfall_pred:.0f}mm) combined with lower "
                        f"predicted {veg} yield ({pred_prod:.0f} Mt). Take preventive "
                        f"measures: improve drainage, apply fungicide, and consider "
                        f"protected cultivation methods."
                    ),
                    "vegetable": veg,
                })

    # ──────────────────────────────────────────────────────────────────
    # Season-specific tip (always append one)
    # ──────────────────────────────────────────────────────────────────
    if season == "Maha":
        recs.append({
            "type": "weather",
            "severity": "info",
            "icon": "leaf",
            "title": "Maha Season Tip",
            "message": (
                "Maha season (Oct-Mar) typically brings Northeast monsoon rains. "
                "Focus on rain-fed crops and ensure adequate drainage in low-lying fields."
            ),
            "vegetable": None,
        })
    else:
        recs.append({
            "type": "weather",
            "severity": "info",
            "icon": "white-balance-sunny",
            "title": "Yala Season Tip",
            "message": (
                "Yala season (Apr-Sep) is typically drier. Plan irrigation schedules "
                "carefully and consider drought-resistant crop varieties."
            ),
            "vegetable": None,
        })

    # Sort: critical first, then warning, positive, info
    severity_order = {"critical": 0, "warning": 1, "positive": 2, "info": 3}
    recs.sort(key=lambda r: severity_order.get(r["severity"], 9))

    return recs
