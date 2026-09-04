"""
Thin query layer between the UI screens and the database.
Every function opens its own short-lived session so screens never
have to manage SQLAlchemy sessions directly.

All functions are wrapped with @db_safe so that if MySQL is
unreachable (server not running, wrong .env credentials, etc.) the
app shows an empty/default result instead of crashing the whole UI.
Screens can still detect the failure via `last_db_error_occurred()`
if they want to show a "can't reach the database" message.
"""
import functools
from datetime import date, timedelta

from database.db_connection import get_session
from database.models import (
    Region, Crop, Production, Price, Climate, Prediction, Alert, Recommendation, Feedback, User, UserPreferences
)

_last_db_error = {"occurred": False, "message": ""}


def last_db_error_occurred():
    """Returns (True, message) if the most recent DB call failed."""
    return _last_db_error["occurred"], _last_db_error["message"]


def clear_db_error():
    _last_db_error["occurred"] = False
    _last_db_error["message"] = ""


def db_safe(default):
    """Decorator: run the wrapped function, and on ANY exception (most
    commonly MySQL being unreachable) log it, record it for the UI,
    and return `default` instead of propagating the crash."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                clear_db_error()
                return result
            except Exception as e:
                print(f"[DB] {fn.__name__} failed: {e}")
                _last_db_error["occurred"] = True
                _last_db_error["message"] = (
                    "Can't reach the database right now. Please make sure MySQL is "
                    "running and your .env settings are correct."
                )
                return default() if callable(default) else default
        return wrapper
    return decorator


@db_safe(default=list)
def get_all_crops():
    db = get_session()
    try:
        return [(c.crop_id, c.crop_name) for c in db.query(Crop).order_by(Crop.crop_name).all()]
    finally:
        db.close()


@db_safe(default=list)
def get_all_regions():
    db = get_session()
    try:
        return [(r.region_id, r.region_name, r.district) for r in db.query(Region).all()]
    finally:
        db.close()


@db_safe(default=list)
def get_user_preferred_crop_ids(user_id):
    db = get_session()
    try:
        pref = db.query(UserPreferences).filter_by(user_id=user_id).first()
        if not pref or not pref.preferred_crops:
            return []
        return [int(x) for x in pref.preferred_crops.split(",") if x.strip()]
    finally:
        db.close()


@db_safe(default=lambda: False)
def set_user_preferred_crop_ids(user_id, crop_ids):
    db = get_session()
    try:
        pref = db.query(UserPreferences).filter_by(user_id=user_id).first()
        value = ",".join(str(c) for c in crop_ids)
        if pref:
            pref.preferred_crops = value
        else:
            pref = UserPreferences(user_id=user_id, preferred_crops=value)
            db.add(pref)
        db.commit()
        return True
    finally:
        db.close()


@db_safe(default=list)
def get_price_history(crop_id, region_id=None, weeks=12):
    db = get_session()
    try:
        cutoff = date.today() - timedelta(weeks=weeks)
        q = db.query(Price).filter(Price.crop_id == crop_id, Price.date >= cutoff)
        if region_id:
            q = q.filter(Price.region_id == region_id)
        rows = q.order_by(Price.date).all()
        return [(r.date.strftime("%d %b"), float(r.price)) for r in rows]
    finally:
        db.close()


@db_safe(default=list)
def get_production_history(crop_id, region_id=None, weeks=12):
    db = get_session()
    try:
        cutoff = date.today() - timedelta(weeks=weeks)
        q = db.query(Production).filter(Production.crop_id == crop_id, Production.record_date >= cutoff)
        if region_id:
            q = q.filter(Production.region_id == region_id)
        rows = q.order_by(Production.record_date).all()
        return [(r.record_date.strftime("%d %b"), float(r.quantity)) for r in rows]
    finally:
        db.close()


@db_safe(default=dict)
def get_latest_predictions(prediction_type="price", region_id=None, limit_per_crop=4):
    """Returns {crop_name: [(date_str, value), ...]} for upcoming predictions."""
    db = get_session()
    try:
        q = db.query(Prediction).filter(Prediction.prediction_type == prediction_type,
                                          Prediction.prediction_date >= date.today())
        if region_id:
            q = q.filter(Prediction.region_id == region_id)
        rows = q.order_by(Prediction.crop_id, Prediction.prediction_date).all()
        result = {}
        for r in rows:
            name = r.crop.crop_name
            result.setdefault(name, [])
            if len(result[name]) < limit_per_crop:
                result[name].append((r.prediction_date.strftime("%d %b"), float(r.prediction_value)))
        return result
    finally:
        db.close()


@db_safe(default=list)
def get_alerts_for_user(user_id, unread_only=False):
    db = get_session()
    try:
        q = db.query(Alert).filter_by(user_id=user_id)
        if unread_only:
            q = q.filter_by(is_read=False)
        rows = q.order_by(Alert.created_at.desc()).all()
        return [{"id": a.alert_id, "type": a.alert_type, "message": a.message,
                  "created_at": a.created_at, "is_read": a.is_read} for a in rows]
    finally:
        db.close()


@db_safe(default=lambda: False)
def mark_alert_read(alert_id):
    db = get_session()
    try:
        a = db.query(Alert).filter_by(alert_id=alert_id).first()
        if a:
            a.is_read = True
            db.commit()
        return True
    finally:
        db.close()


@db_safe(default=list)
def get_recommendations_for_user(user_id):
    db = get_session()
    try:
        rows = db.query(Recommendation).filter_by(user_id=user_id).order_by(
            Recommendation.created_at.desc()).all()
        return [{"id": r.recommendation_id, "message": r.message, "created_at": r.created_at} for r in rows]
    finally:
        db.close()


@db_safe(default=lambda: False)
def submit_feedback(user_id, message, rating=None):
    db = get_session()
    try:
        db.add(Feedback(user_id=user_id, message=message, rating=rating))
        db.commit()
        return True
    finally:
        db.close()


@db_safe(default=lambda: (None, 0))
def get_average_rating():
    db = get_session()
    try:
        rows = db.query(Feedback.rating).filter(Feedback.rating.isnot(None)).all()
        values = [r[0] for r in rows]
        if not values:
            return None, 0
        return round(sum(values) / len(values), 1), len(values)
    finally:
        db.close()


@db_safe(default=list)
def get_all_feedback_for_admin():
    db = get_session()
    try:
        rows = db.query(Feedback).order_by(Feedback.submitted_at.desc()).all()
        out = []
        for f in rows:
            u = db.query(User).filter_by(user_id=f.user_id).first()
            out.append({
                "id": f.feedback_id,
                "message": f.message,
                "rating": f.rating,
                "status": f.status,
                "submitted_at": f.submitted_at,
                "from": f"{u.first_name} {u.last_name}" if u else "Unknown",
            })
        return out
    finally:
        db.close()


@db_safe(default=lambda: False)
def mark_feedback_reviewed(feedback_id):
    db = get_session()
    try:
        f = db.query(Feedback).filter_by(feedback_id=feedback_id).first()
        if f:
            f.status = "reviewed"
            db.commit()
        return True
    finally:
        db.close()


@db_safe(default=list)
def get_all_users_for_admin(role_filter=None, search_query=None):
    """Retrieves all user accounts for admin view with optional role filter and search."""
    db = get_session()
    try:
        q = db.query(User)
        if role_filter and role_filter.lower() != "all":
            q = q.filter(User.user_type == role_filter.lower())
        if search_query and search_query.strip():
            sq = f"%{search_query.strip().lower()}%"
            q = q.filter(
                (User.email.ilike(sq)) |
                (User.first_name.ilike(sq)) |
                (User.last_name.ilike(sq))
            )
        users = q.order_by(User.created_at.desc()).all()
        out = []
        for u in users:
            r = db.query(Region).filter_by(region_id=u.region_id).first() if u.region_id else None
            out.append({
                "user_id": u.user_id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "full_name": f"{u.first_name} {u.last_name}",
                "user_type": u.user_type,
                "region_id": u.region_id,
                "district": r.district if r else "Not specified",
                "is_active": u.is_active,
                "created_at": u.created_at,
            })
        return out
    finally:
        db.close()


def _is_last_active_admin(db, user):
    return user.user_type == "admin" and user.is_active and db.query(User).filter(
        User.user_type == "admin", User.is_active.is_(True)
    ).count() <= 1


@db_safe(default=lambda: (False, "Database error"))
def toggle_user_status_by_admin(user_id):
    """Toggles active/suspended status of a user."""
    db = get_session()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return False, "User not found."
        if _is_last_active_admin(db, user):
            return False, "The last active admin account cannot be suspended."
        user.is_active = not user.is_active
        db.commit()
        status_text = "activated" if user.is_active else "suspended"
        return True, f"Account for {user.email} is now {status_text}."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


@db_safe(default=lambda: (False, "Database error"))
def update_user_role_by_admin(user_id, new_role):
    """Updates user role by admin."""
    from database.auth_service import ALL_ROLES
    if new_role not in ALL_ROLES:
        return False, "Invalid role specified."
    db = get_session()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return False, "User not found."
        if new_role != "admin" and _is_last_active_admin(db, user):
            return False, "The last active admin account must remain an admin."
        user.user_type = new_role
        db.commit()
        return True, f"Role for {user.email} updated to {new_role.capitalize()}."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


@db_safe(default=lambda: (False, "Database error"))
def delete_user_by_admin(user_id):
    """Safely deletes user account and associated user data."""
    db = get_session()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return False, "User not found."
        if _is_last_active_admin(db, user):
            return False, "The last active admin account cannot be deleted."
        email = user.email
        # Cleanup dependent records first
        db.query(UserPreferences).filter_by(user_id=user_id).delete()
        db.query(Alert).filter_by(user_id=user_id).delete()
        db.query(Recommendation).filter_by(user_id=user_id).delete()
        db.query(Feedback).filter_by(user_id=user_id).delete()
        db.delete(user)
        db.commit()
        return True, f"User {email} has been permanently deleted."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()



@db_safe(default=lambda: (False, "Database error"))
def update_user_profile(user_id, first_name, last_name, region_id=None):
    """Updates user first name, last name, and region in DB, returning (True, updated_user_dict)."""
    db = get_session()
    try:
        user = db.query(User).filter_by(user_id=user_id).first()
        if not user:
            return False, "User not found."
        if first_name and first_name.strip():
            user.first_name = first_name.strip()
        if last_name and last_name.strip():
            user.last_name = last_name.strip()
        if region_id:
            user.region_id = region_id
        db.commit()

        region = db.query(Region).filter_by(region_id=user.region_id).first() if user.region_id else None
        updated = {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "user_type": user.user_type,
            "region_id": user.region_id,
            "region_name": region.region_name if region else None,
            "district": region.district if region else None,
        }
        return True, updated
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


@db_safe(default=list)
def get_market_summary(region_id=None):
    """Latest price per crop for the dashboard 'at a glance' cards."""
    db = get_session()
    try:
        crops = db.query(Crop).all()
        summary = []
        for c in crops:
            q = db.query(Price).filter_by(crop_id=c.crop_id)
            if region_id:
                q = q.filter_by(region_id=region_id)
            latest = q.order_by(Price.date.desc()).first()
            prev = q.order_by(Price.date.desc()).offset(1).first()
            change = None
            if latest and prev and prev.price:
                change = round(float((latest.price - prev.price) / prev.price) * 100, 1)
            summary.append({
                "crop": c.crop_name,
                "price": float(latest.price) if latest else None,
                "change_pct": change,
            })
        return summary
    finally:
        db.close()


@db_safe(default=dict)
def get_market_demand_trends(region_id=None):
    """Computes market demand levels and trends per crop and region-wide."""
    db = get_session()
    try:
        crops = db.query(Crop).order_by(Crop.crop_name).all()
        crop_trends = []
        high_demand_count = 0
        for c in crops:
            q = db.query(Price).filter_by(crop_id=c.crop_id)
            if region_id:
                q = q.filter_by(region_id=region_id)
            latest = q.order_by(Price.date.desc()).first()
            prev = q.order_by(Price.date.desc()).offset(1).first()
            change = 0.0
            if latest and prev and prev.price:
                change = round(float((latest.price - prev.price) / prev.price) * 100, 1)

            if change >= 4.0:
                status = "High Demand"
                trend = "Surging ▲"
                demand_score = f"+{change}%"
                level = "high"
                high_demand_count += 1
            elif change <= -4.0:
                status = "Supply Surplus"
                trend = "Easing ▼"
                demand_score = f"{change}%"
                level = "low"
            else:
                status = "Moderate Demand"
                trend = "Stable ↔"
                demand_score = f"{change:+.1f}%" if change != 0 else "0.0%"
                level = "medium"

            crop_trends.append({
                "crop": c.crop_name,
                "status": status,
                "trend": trend,
                "change_pct": change,
                "demand_score": demand_score,
                "level": level,
                "price": float(latest.price) if latest else 0.0,
            })

        overall_status = "High Market Demand" if high_demand_count >= 2 else "Balanced Market Demand"
        insight = (
            f"Strong buyer demand across markets. {high_demand_count} crops showing notable price upward momentum."
            if high_demand_count > 0 else
            "Market supply is well-balanced across crop categories with steady prices."
        )

        return {
            "overall_status": overall_status,
            "high_demand_count": high_demand_count,
            "insight": insight,
            "crop_trends": crop_trends,
        }
    finally:
        db.close()


@db_safe(default=dict)
def get_weather_impact_analysis(region_id=None):
    """Retrieves latest climate records and calculates agricultural weather impacts."""
    db = get_session()
    try:
        q = db.query(Climate)
        if region_id:
            q = q.filter_by(region_id=region_id)
        latest = q.order_by(Climate.record_date.desc()).first()

        if not latest:
            return {
                "rainfall_mm": 120.0,
                "avg_temp_c": 25.5,
                "humidity_pct": 72.0,
                "condition": "Moderate Rain",
                "record_date": "Recent",
                "harvest_risk": "Moderate Fungal Risk",
                "harvest_risk_detail": "Humidity ~72%. Monitor crops for early blight or leaf spot symptoms.",
                "irrigation_advice": "Reduce Irrigation",
                "irrigation_advice_detail": "Rainfall logged. Lower artificial irrigation by 30-40% this week.",
                "yield_impact": "+5.0% Favorable Growth",
                "yield_impact_detail": "Rainfall and mild temperature support healthy crop tissue growth.",
            }

        rain = float(latest.rainfall_mm or 0)
        temp = float(latest.avg_temp_c or 25)
        hum = float(latest.humidity_pct or 70)

        if rain > 150:
            cond = "Heavy Rain"
        elif rain > 70:
            cond = "Moderate Rain"
        else:
            cond = "Light Rain / Mild"

        if hum > 75 or rain > 150:
            risk = "High Fungal / Rot Risk"
            risk_detail = f"High humidity ({hum:.0f}%) & rainfall ({rain:.0f}mm) increase blight and fungal rot risk."
        elif hum > 60:
            risk = "Moderate Disease Risk"
            risk_detail = f"Humidity at {hum:.0f}%. Maintain proper field drainage and monitor crop leaves."
        else:
            risk = "Low Disease Risk"
            risk_detail = f"Humidity at {hum:.0f}%. Dry/optimal foliage environment."

        if rain > 100:
            irrigation = "Reduce Irrigation by 50%"
            irrigation_detail = "Sufficient rainfall logged. Pause or lower artificial watering to avoid waterlogging."
        elif rain > 40:
            irrigation = "Moderate Watering"
            irrigation_detail = "Provide light supplemental irrigation only on non-rainy days."
        else:
            irrigation = "Active Watering Needed"
            irrigation_detail = "Low rainfall recorded. Maintain regular watering schedules."

        if 20 <= temp <= 29 and 50 <= rain <= 180:
            yield_imp = "+6.2% Yield Boost"
            yield_detail = f"Current temp ({temp:.1f}°C) & rainfall foster optimal root and foliage growth."
        elif temp > 30:
            yield_imp = "-3.0% Heat Stress Risk"
            yield_detail = f"Elevated temperature ({temp:.1f}°C) may cause light moisture stress."
        else:
            yield_imp = "Stable Seasonal Growth"
            yield_detail = "Weather conditions align with seasonal baseline growth averages."

        return {
            "rainfall_mm": rain,
            "avg_temp_c": temp,
            "humidity_pct": hum,
            "condition": cond,
            "record_date": latest.record_date.strftime("%d %b %Y") if latest.record_date else "Recent",
            "harvest_risk": risk,
            "harvest_risk_detail": risk_detail,
            "irrigation_advice": irrigation,
            "irrigation_advice_detail": irrigation_detail,
            "yield_impact": yield_imp,
            "yield_impact_detail": yield_detail,
        }
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════
# ML INTEGRATION HELPERS
# ══════════════════════════════════════════════════════════════════════════

@db_safe(default=dict)
def get_latest_prices_for_crops(region_id=None):
    """Return {crop_name: latest_price_float} for all crops.
    Used to compare predicted vs. current price."""
    db = get_session()
    try:
        crops = db.query(Crop).all()
        result = {}
        for c in crops:
            q = db.query(Price).filter_by(crop_id=c.crop_id)
            if region_id:
                q = q.filter_by(region_id=region_id)
            latest = q.order_by(Price.date.desc()).first()
            if latest:
                result[c.crop_name] = float(latest.price)
        return result
    finally:
        db.close()


@db_safe(default=dict)
def get_lag_features_for_crops(region_id=None):
    """Return {crop_name: {price_lag_1, price_lag_2, price_lag_3,
    production_lag_1, cultivated_area, yield_per_ha}} derived from the
    most recent DB records.  Used as features for ML model input."""
    db = get_session()
    try:
        crops = db.query(Crop).all()
        result = {}
        for c in crops:
            # Price lags — last 3 prices
            pq = db.query(Price).filter_by(crop_id=c.crop_id)
            if region_id:
                pq = pq.filter_by(region_id=region_id)
            recent_prices = pq.order_by(Price.date.desc()).limit(3).all()
            price_lags = [float(r.price) for r in recent_prices]
            while len(price_lags) < 3:
                price_lags.append(200.0)  # fallback default

            # Production lag — last production record
            prq = db.query(Production).filter_by(crop_id=c.crop_id)
            if region_id:
                prq = prq.filter_by(region_id=region_id)
            last_prod = prq.order_by(Production.record_date.desc()).first()

            result[c.crop_name] = {
                "price_lag_1": price_lags[0],
                "price_lag_2": price_lags[1],
                "price_lag_3": price_lags[2],
                "production_lag_1": float(last_prod.quantity) if last_prod else 1000.0,
                "cultivated_area": 100.0,  # not in DB per-crop; use dataset average
                "yield_per_ha": 10.0,      # approximate
            }
        return result
    finally:
        db.close()


@db_safe(default=dict)
def get_current_weather(region_id=None):
    """Return the latest climate record as a dict suitable for ml_engine.
    Keys: temperature, rainfall, humidity."""
    db = get_session()
    try:
        q = db.query(Climate)
        if region_id:
            q = q.filter_by(region_id=region_id)
        latest = q.order_by(Climate.record_date.desc()).first()
        if not latest:
            return {"temperature": 26.0, "rainfall": 140.0, "humidity": 80.0}
        return {
            "temperature": float(latest.avg_temp_c or 26.0),
            "rainfall": float(latest.rainfall_mm or 140.0),
            "humidity": float(latest.humidity_pct or 80.0),
        }
    finally:
        db.close()


@db_safe(default=lambda: None)
def save_ml_prediction(prediction_type, prediction_value, prediction_date,
                       crop_id, region_id=None):
    """Save a single ML prediction to the prediction table."""
    db = get_session()
    try:
        pred = Prediction(
            prediction_type=prediction_type,
            prediction_value=round(prediction_value, 2),
            prediction_date=prediction_date,
            crop_id=crop_id,
            region_id=region_id,
        )
        db.add(pred)
        db.commit()
        return pred.prediction_id
    finally:
        db.close()


@db_safe(default=lambda: None)
def save_ml_alert(alert_type, message, user_id, prediction_id=None):
    """Save an ML-generated alert to the alert table."""
    db = get_session()
    try:
        alert = Alert(
            alert_type=alert_type,
            message=message,
            prediction_id=prediction_id,
            user_id=user_id,
        )
        db.add(alert)
        db.commit()
        return alert.alert_id
    finally:
        db.close()


@db_safe(default=lambda: None)
def save_ml_recommendation(message, user_id, prediction_id=None, region_id=None):
    """Save an ML-generated recommendation to the recommendation table."""
    db = get_session()
    try:
        rec = Recommendation(
            message=message,
            user_id=user_id,
            prediction_id=prediction_id,
            region_id=region_id,
        )
        db.add(rec)
        db.commit()
        return rec.recommendation_id
    finally:
        db.close()


@db_safe(default=lambda: None)
def get_last_ml_run_time(user_id):
    """Return the created_at of the most recent ML-generated recommendation
    for this user, so we can implement 24h caching."""
    db = get_session()
    try:
        latest = db.query(Recommendation).filter_by(user_id=user_id).order_by(
            Recommendation.created_at.desc()).first()
        return latest.created_at if latest else None
    finally:
        db.close()


@db_safe(default=lambda: False)
def clear_old_ml_data(user_id):
    """Remove old ML-generated alerts and recommendations for a user
    before inserting fresh ones (prevents unbounded growth)."""
    db = get_session()
    try:
        db.query(Alert).filter_by(user_id=user_id).delete()
        db.query(Recommendation).filter_by(user_id=user_id).delete()
        db.commit()
        return True
    finally:
        db.close()


@db_safe(default=dict)
def get_crop_name_to_id_map():
    """Return {crop_name: crop_id} mapping."""
    db = get_session()
    try:
        crops = db.query(Crop).all()
        return {c.crop_name: c.crop_id for c in crops}
    finally:
        db.close()


@db_safe(default=lambda: None)
def get_region_district(region_id):
    """Return the district name for a region_id."""
    db = get_session()
    try:
        r = db.query(Region).filter_by(region_id=region_id).first()
        return r.district if r else None
    finally:
        db.close()
