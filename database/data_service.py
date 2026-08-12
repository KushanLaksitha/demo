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
    Region, Crop, Production, Price, Prediction, Alert, Recommendation, Feedback, User, UserPreferences
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
