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
from datetime import date, timedelta, datetime

from database.db_connection import get_session
from database.models import (
    Region, Crop, Production, Price, Climate, Prediction, Alert, Recommendation, Feedback, User, UserPreferences,
    OfficialCommunication
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
        q = db.query(Price).filter(Price.crop_id == crop_id)
        if region_id:
            q = q.filter(Price.region_id == region_id)
        rows = q.order_by(Price.date.desc()).limit(weeks).all()
        rows = sorted(rows, key=lambda r: r.date)
        return [(r.date.strftime("%d %b"), float(r.price)) for r in rows]
    finally:
        db.close()


@db_safe(default=list)
def get_production_history(crop_id, region_id=None, weeks=12):
    db = get_session()
    try:
        q = db.query(Production).filter(Production.crop_id == crop_id)
        if region_id:
            q = q.filter(Production.region_id == region_id)
        rows = q.order_by(Production.record_date.desc()).limit(weeks).all()
        rows = sorted(rows, key=lambda r: r.record_date)
        return [(r.record_date.strftime("%d %b"), float(r.quantity)) for r in rows]
    finally:
        db.close()


@db_safe(default=lambda: [2025, 2024, 2023, 2022, 2021])
def get_available_record_years(crop_id=None):
    """Returns sorted list of unique years in descending order."""
    db = get_session()
    try:
        from sqlalchemy import func
        q_p = db.query(func.year(Price.date).label("yr"))
        if crop_id:
            q_p = q_p.filter(Price.crop_id == crop_id)
        years_p = {r[0] for r in q_p.distinct().all() if r[0]}

        q_prod = db.query(func.year(Production.record_date).label("yr"))
        if crop_id:
            q_prod = q_prod.filter(Production.crop_id == crop_id)
        years_prod = {r[0] for r in q_prod.distinct().all() if r[0]}

        all_years = sorted(years_p | years_prod, reverse=True)
        return all_years if all_years else [2025, 2024, 2023, 2022, 2021]
    finally:
        db.close()


@db_safe(default=lambda: ([], {}))
def get_price_history_by_year(crop_id, year, region_id=None):
    """
    Returns (data, stats) for a specific year.
    data: [(month_name, avg_price), ...] for all 12 months.
    stats: {
        "avg": float,
        "min": float,
        "max": float,
        "min_month": str,
        "max_month": str,
        "total_records": int,
        "year": int
    }
    """
    db = get_session()
    try:
        from sqlalchemy import func
        import calendar

        q = db.query(
            func.month(Price.date).label("m"),
            func.avg(Price.price).label("avg_p"),
            func.min(Price.price).label("min_p"),
            func.max(Price.price).label("max_p"),
            func.count(Price.price_id).label("cnt")
        ).filter(Price.crop_id == crop_id, func.year(Price.date) == int(year))
        if region_id:
            q = q.filter(Price.region_id == region_id)
        rows = q.group_by(func.month(Price.date)).order_by(func.month(Price.date)).all()

        if not rows:
            return [], {}

        data = []
        all_avgs = []
        min_overall = float("inf")
        max_overall = float("-inf")
        min_month = ""
        max_month = ""
        total_records = 0

        for r in rows:
            m_num = int(r.m)
            m_abbr = calendar.month_abbr[m_num]
            avg_p = round(float(r.avg_p), 2)
            min_p = round(float(r.min_p), 2)
            max_p = round(float(r.max_p), 2)
            cnt = int(r.cnt)

            data.append((m_abbr, avg_p))
            all_avgs.append(avg_p)
            total_records += cnt

            if min_p < min_overall:
                min_overall = min_p
                min_month = m_abbr
            if max_p > max_overall:
                max_overall = max_p
                max_month = m_abbr

        overall_avg = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else 0.0

        stats = {
            "avg": overall_avg,
            "min": min_overall if min_overall != float("inf") else 0.0,
            "max": max_overall if max_overall != float("-inf") else 0.0,
            "min_month": min_month,
            "max_month": max_month,
            "total_records": total_records,
            "year": int(year),
        }
        return data, stats
    finally:
        db.close()


@db_safe(default=lambda: ([], {}))
def get_production_history_by_year(crop_id, year, region_id=None):
    """
    Returns (data, stats) for a specific year.
    data: [(month_name, total_quantity), ...] for all 12 months.
    stats: {
        "total": float,
        "avg": float,
        "min": float,
        "max": float,
        "min_month": str,
        "max_month": str,
        "total_records": int,
        "year": int
    }
    """
    db = get_session()
    try:
        from sqlalchemy import func
        import calendar

        q = db.query(
            func.month(Production.record_date).label("m"),
            func.sum(Production.quantity).label("tot_q"),
            func.avg(Production.quantity).label("avg_q"),
            func.min(Production.quantity).label("min_q"),
            func.max(Production.quantity).label("max_q"),
            func.count(Production.production_id).label("cnt")
        ).filter(Production.crop_id == crop_id, func.year(Production.record_date) == int(year))
        if region_id:
            q = q.filter(Production.region_id == region_id)
        rows = q.group_by(func.month(Production.record_date)).order_by(func.month(Production.record_date)).all()

        if not rows:
            return [], {}

        data = []
        totals = []
        min_overall = float("inf")
        max_overall = float("-inf")
        min_month = ""
        max_month = ""
        total_records = 0

        for r in rows:
            m_num = int(r.m)
            m_abbr = calendar.month_abbr[m_num]
            tot_q = round(float(r.tot_q), 2)
            cnt = int(r.cnt)

            data.append((m_abbr, tot_q))
            totals.append(tot_q)
            total_records += cnt

            if tot_q < min_overall:
                min_overall = tot_q
                min_month = m_abbr
            if tot_q > max_overall:
                max_overall = tot_q
                max_month = m_abbr

        total_sum = round(sum(totals), 2)
        month_avg = round(total_sum / len(totals), 2) if totals else 0.0

        stats = {
            "total": total_sum,
            "avg": month_avg,
            "min": min_overall if min_overall != float("inf") else 0.0,
            "max": max_overall if max_overall != float("-inf") else 0.0,
            "min_month": min_month,
            "max_month": max_month,
            "total_records": total_records,
            "year": int(year),
        }
        return data, stats
    finally:
        db.close()


@db_safe(default=dict)
def get_trader_stocks(user_id=None):
    """Returns {crop_name: quantity_kg} saved for trader, or default realistic baseline."""
    default_baseline = {
        "Beans": 850.0,
        "Cabbage": 120.0,
        "Carrots": 2100.0,
        "Leeks": 600.0,
        "Okra": 450.0,
    }
    if not user_id:
        return default_baseline

    db = get_session()
    try:
        import json
        pref = db.query(UserPreferences).filter_by(user_id=user_id).first()
        if pref and pref.notification_settings and pref.notification_settings.startswith("{"):
            try:
                data = json.loads(pref.notification_settings)
                if isinstance(data, dict) and "stocks" in data and isinstance(data["stocks"], dict):
                    stocks = default_baseline.copy()
                    for k, v in data["stocks"].items():
                        try:
                            stocks[k] = float(v)
                        except Exception:
                            pass
                    return stocks
            except Exception:
                pass
        return default_baseline
    finally:
        db.close()


@db_safe(default=lambda: False)
def save_trader_stock(user_id, crop_name, quantity_kg):
    """Saves updated stock quantity for a crop."""
    if not user_id:
        return False
    db = get_session()
    try:
        import json
        pref = db.query(UserPreferences).filter_by(user_id=user_id).first()
        if not pref:
            pref = UserPreferences(user_id=user_id, notification_settings="{}")
            db.add(pref)

        data = {}
        if pref.notification_settings and pref.notification_settings.startswith("{"):
            try:
                data = json.loads(pref.notification_settings)
            except Exception:
                data = {}
        if "stocks" not in data or not isinstance(data["stocks"], dict):
            data["stocks"] = get_trader_stocks(user_id)

        data["stocks"][crop_name] = max(0.0, float(quantity_kg))
        pref.notification_settings = json.dumps(data)
        db.commit()
        return True
    finally:
        db.close()


@db_safe(default=dict)
def get_trader_inventory_summary(user_id=None, region_id=None):
    """
    Returns real inventory data derived from DB prices, production supply, and trader stock quantities:
    - Real latest wholesale prices from Price table
    - Real production supply from Production table
    - Real computed crop valuations and total inventory value
    """
    db = get_session()
    try:
        from datetime import datetime
        stocks = get_trader_stocks(user_id)
        crops = db.query(Crop).order_by(Crop.crop_name).all()

        region = db.query(Region).filter_by(region_id=region_id).first() if region_id else None
        district = region.district if region else "Kandy"

        items = []
        total_value = 0.0

        CROP_ICONS = {
            "Beans": "seed",
            "Cabbage": "flower-tulip",
            "Carrots": "carrot",
            "Leeks": "sprout",
            "Okra": "leaf",
        }

        for c in crops:
            # 1. Real latest price from DB
            pq = db.query(Price).filter_by(crop_id=c.crop_id)
            if region_id:
                pq = pq.filter_by(region_id=region_id)
            latest_p = pq.order_by(Price.date.desc()).first()
            prev_p = pq.order_by(Price.date.desc()).offset(1).first()

            price = float(latest_p.price) if latest_p else 200.0
            prev_price = float(prev_p.price) if prev_p else price
            chg_pct = round(((price - prev_price) / prev_price * 100), 1) if prev_price else 0.0

            # 2. Real regional production supply from DB
            prq = db.query(Production).filter_by(crop_id=c.crop_id)
            if region_id:
                prq = prq.filter_by(region_id=region_id)
            latest_prod = prq.order_by(Production.record_date.desc()).first()
            prod_qty = float(latest_prod.quantity) if latest_prod else 0.0

            # 3. Stock quantity in kg
            qty_kg = float(stocks.get(c.crop_name, 500.0))
            if qty_kg >= 1000:
                qty_str = f"{qty_kg / 1000:.1f} tons"
            else:
                qty_str = f"{qty_kg:,.0f} kg"

            # 4. Computed valuation
            item_val = qty_kg * price
            total_value += item_val

            # 5. Tag based on stock level & supply
            if qty_kg < 200:
                tag = "LOW STOCK"
                tag_bg = (0.99, 0.88, 0.88, 1)
                tag_fg = (0.85, 0.20, 0.20, 1)
            elif qty_kg > 1500:
                tag = "SURPLUS"
                tag_bg = (0.88, 0.94, 0.99, 1)
                tag_fg = (0.15, 0.45, 0.75, 1)
            elif qty_kg >= 400:
                tag = "OPTIMAL"
                tag_bg = (0.88, 0.96, 0.88, 1)
                tag_fg = (0.13, 0.65, 0.22, 1)
            else:
                tag = "FAIR"
                tag_bg = (0.99, 0.96, 0.82, 1)
                tag_fg = (0.75, 0.50, 0.05, 1)

            rec_date_str = latest_p.date.strftime("%d %b %Y") if (latest_p and latest_p.date) else "Recent"

            items.append({
                "crop": c.crop_name,
                "crop_id": c.crop_id,
                "category": c.category,
                "icon": CROP_ICONS.get(c.crop_name, "leaf"),
                "price": price,
                "price_str": f"Rs. {price:,.2f} / kg",
                "price_change_pct": chg_pct,
                "qty": qty_kg,
                "qty_str": qty_str,
                "value": item_val,
                "value_str": f"Rs. {item_val:,.2f}",
                "regional_supply_mt": prod_qty,
                "tag": tag,
                "tag_bg": tag_bg,
                "tag_fg": tag_fg,
                "recorded_date": rec_date_str,
            })

        now = datetime.now()
        sync_time_str = now.strftime("%A, %I:%M %p")

        return {
            "total_value": total_value,
            "total_value_str": f"Rs. {total_value:,.2f}",
            "total_categories": len(items),
            "district": district,
            "sync_time": sync_time_str,
            "items": items,
        }
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
def ensure_sample_alerts_if_empty(user_id, role="farmer", district="Matale"):
    """Populates realistic multi-category alerts if user has fewer than 3 alerts."""
    db = get_session()
    try:
        count = db.query(Alert).filter_by(user_id=user_id).count()
        if count >= 3:
            return
        
        sample_farmer = [
            ("price_spike", f"Beans wholesale price predicted to spike to Rs.420/kg (+24%) in {district}. Favorable window for harvesting and early selling."),
            ("price_drop", f"Cabbage price forecast to drop to Rs.105/kg (-16%) in {district}. Hold harvest or explore Dambulla economic center."),
            ("heavy_rain", f"Heavy rainfall predicted (165mm) in {district}. Protect crops from waterlogging and delay scheduled fertilizer application."),
            ("production_surplus", f"Beans harvest surplus expected (4,200 Mt, 137% of seasonal average). Plan distributed market sales to avoid glut."),
            ("official_notice", f"Agrarian Services Advisory: Fall Armyworm (සේනා දළඹු) surveillance active in {district}. Report suspicious crop damage to AI officer."),
        ]
        sample_trader = [
            ("price_spike", f"Carrots wholesale price surging (+22%) in {district} wholesale market due to transport constraints."),
            ("production_shortage", f"Leeks production shortage predicted (2,400 Mt, only 63% of seasonal average). High retail demand expected."),
            ("drought_risk", f"Dry spell forecast (22mm rain) in {district}. Transport routes and open-air drying yards operating under clear skies."),
            ("official_notice", f"Dambulla Dedicated Economic Centre: Extended night wholesale receiving hours active for vegetable consignments."),
        ]
        sample_policy = [
            ("production_shortage", "National harvest shortage projected for Leeks and Carrots in Q3. Buffer stock intervention and price stabilization recommended."),
            ("production_surplus", f"Cabbage oversupply alert across {district} (142% of seasonal baseline). Inter-district redistribution advised to prevent crop loss."),
            ("heavy_rain", f"Precipitation anomaly: Monsoon rainfall variance exceeding 170mm in {district} agricultural watershed."),
            ("official_notice", "Ministry of Agriculture: Vegetable Price Stabilization and National Cold-Chain Monitoring Task Force convened."),
        ]

        templates = sample_farmer
        if role == "trader":
            templates = sample_trader
        elif role == "policymaker":
            templates = sample_policy

        for atype, msg in templates:
            exists = db.query(Alert).filter_by(user_id=user_id, alert_type=atype).first()
            if not exists:
                db.add(Alert(alert_type=atype, message=msg, user_id=user_id, is_read=False))
        db.commit()
    finally:
        db.close()


@db_safe(default=lambda: 0)
def broadcast_admin_alert(message, alert_type="official_notice", target_role=None):
    """Broadcast an announcement or alert from Admin to active users."""
    db = get_session()
    try:
        q = db.query(User).filter_by(is_active=True)
        if target_role and target_role != "all":
            q = q.filter_by(user_type=target_role)
        users = q.all()
        count = 0
        for u in users:
            db.add(Alert(alert_type=alert_type, message=message, user_id=u.user_id, is_read=False))
            count += 1
        db.commit()
        return count
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


@db_safe(default=list)
def ensure_sample_recommendations_if_empty(user_id, role="farmer", district="Matale"):
    """Populates realistic multi-category recommendations if user has fewer than 3."""
    db = get_session()
    try:
        count = db.query(Recommendation).filter_by(user_id=user_id).count()
        if count >= 3:
            return
        
        sample_farmer_recs = [
            ("price", f"Beans Price Surge: Predicted to rise to Rs. 420/kg (+24%). Harvest mature pods this weekend and dispatch early to Pettah or Dambulla for maximum profits."),
            ("weather", f"Heavy Rainfall Expected ({district}): Clear drainage furrows and elevate nursery beds. Delay urea application by 4 days to prevent nutrient leaching."),
            ("production", f"Leeks Supply Shortage: Low regional output predicted this season. Prioritize Leeks cultivation and water allocation for higher price margins."),
            ("combined", f"Crop Diversification Advisory: Inter-crop Okra with legumes to maximize soil nitrogen fixation while market demand remains steady in {district}."),
        ]
        sample_trader_recs = [
            ("price", f"Carrots Wholesale Window: Wholesale buying prices are trending up (+22%) in {district}. Secure direct forward contracts with farmer cooperatives."),
            ("production", f"Cabbage Supply Surplus: Expecting 140% of seasonal volume. Coordinate cold storage transport to prevent localized price collapse."),
            ("weather", f"Transport Route Advisory: Dry spell forecast in {district} ensures clear road conditions across central wholesale corridors."),
            ("combined", f"Inventory Optimization: High demand for Beans and Leeks in Colombo markets; stock up early ahead of weekend trading cycles."),
        ]
        sample_policy_recs = [
            ("production", f"National Harvest Shortage: Leeks output below 70% threshold. Implement regional redistribution from Nuwara Eliya to Colombo."),
            ("price", f"Wholesale Price Stabilization: Price volatility index elevated for Carrots. Activate cooperative purchasing centers."),
            ("weather", f"Climate Resilience Alert: Monsoonal rainfall excess predicted in {district}. Deploy regional flood prevention advisory teams."),
            ("combined", f"Long-term Agro-Policy: Encourage drought-resistant varieties for upcoming Yala season in intermediate rainfall zones."),
        ]

        templates = sample_farmer_recs
        if role == "trader":
            templates = sample_trader_recs
        elif role == "policymaker":
            templates = sample_policy_recs

        for rtype, rmsg in templates:
            exists = db.query(Recommendation).filter_by(user_id=user_id, message=rmsg).first()
            if not exists:
                db.add(Recommendation(message=rmsg, user_id=user_id))
        db.commit()
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

# -----------------------------------------------------------------
# Price & Production by Date utilities
# -----------------------------------------------------------------

@db_safe(default=lambda: None)
def get_price_by_date(crop_id, target_date, region_id=None, allow_nearest=True):
    """Return the price (float) for a specific crop on a given date.
    Returns None if no record exists within ±7 days."""
    db = get_session()
    try:
        q = db.query(Price).filter(Price.crop_id == crop_id, Price.date == target_date)
        if region_id:
            q = q.filter(Price.region_id == region_id)
        row = q.first()
        if row:
            return float(row.price)
        if allow_nearest:
            min_d = target_date - timedelta(days=7)
            max_d = target_date + timedelta(days=7)
            q_near = db.query(Price).filter(Price.crop_id == crop_id, Price.date >= min_d, Price.date <= max_d)
            if region_id:
                q_near = q_near.filter(Price.region_id == region_id)
            rows = q_near.all()
            if rows:
                best = min(rows, key=lambda r: abs((r.date - target_date).days))
                return float(best.price)
        return None
    finally:
        db.close()

@db_safe(default=lambda: None)
def get_production_by_date(crop_id, target_date, region_id=None, allow_nearest=True):
    """Return the production quantity (float) for a specific crop on a given date.
    Returns None if no record exists within ±7 days."""
    db = get_session()
    try:
        q = db.query(Production).filter(Production.crop_id == crop_id, Production.record_date == target_date)
        if region_id:
            q = q.filter(Production.region_id == region_id)
        row = q.first()
        if row:
            return float(row.quantity)
        if allow_nearest:
            min_d = target_date - timedelta(days=7)
            max_d = target_date + timedelta(days=7)
            q_near = db.query(Production).filter(Production.crop_id == crop_id, Production.record_date >= min_d, Production.record_date <= max_d)
            if region_id:
                q_near = q_near.filter(Production.region_id == region_id)
            rows = q_near.all()
            if rows:
                best = min(rows, key=lambda r: abs((r.record_date - target_date).days))
                return float(best.quantity)
        return None
    finally:
        db.close()

@db_safe(default=lambda: {"price": [], "production": []})
def get_price_production_range(crop_id, start_date, end_date, region_id=None):
    """Return price and production data for a crop between start_date and end_date.
    Returns dict with 'price': [(date_str, price)], 'production': [(date_str, qty)]."""
    db = get_session()
    try:
        price_q = db.query(Price).filter(Price.crop_id == crop_id, Price.date >= start_date, Price.date <= end_date)
        prod_q = db.query(Production).filter(Production.crop_id == crop_id, Production.record_date >= start_date, Production.record_date <= end_date)
        if region_id:
            price_q = price_q.filter(Price.region_id == region_id)
            prod_q = prod_q.filter(Production.region_id == region_id)
        price_rows = price_q.order_by(Price.date).all()
        prod_rows = prod_q.order_by(Production.record_date).all()
        price_data = [(r.date.strftime("%d %b %Y"), float(r.price)) for r in price_rows]
        prod_data = [(r.record_date.strftime("%d %b %Y"), float(r.quantity)) for r in prod_rows]
        return {"price": price_data, "production": prod_data}
    finally:
        db.close()


@db_safe(default=lambda: None)
def get_latest_record_date(crop_id=None):
    """Return the most recent date available in Price records."""
    db = get_session()
    try:
        q = db.query(Price.date)
        if crop_id:
            q = q.filter(Price.crop_id == crop_id)
        r = q.order_by(Price.date.desc()).first()
        return r[0] if r else None
    finally:
        db.close()


@db_safe(default=lambda: None)
def get_earliest_record_date(crop_id=None):
    """Return the earliest date available in Price records."""
    db = get_session()
    try:
        q = db.query(Price.date)
        if crop_id:
            q = q.filter(Price.crop_id == crop_id)
        r = q.order_by(Price.date.asc()).first()
        return r[0] if r else None
    finally:
        db.close()


@db_safe(default=dict)
def get_policymaker_dashboard_data():
    """
    Returns all real data needed for the Policymaker dashboard:
    - food_security_score: index 0-100 based on production / AI-predicted demand
    - food_security_change: change vs previous period
    - yield_growth_pct: avg yield growth % across all crops/regions
    - yield_growth_label: human-readable trend label (Growing/Stable/Declining)
    - heatmap_regions: list of {name, district, total_mt, intensity} per region
    - pvd_crops: list of {crop, prod_mt, pred_mt, shortfall_label, is_surplus} per crop
    - insight: auto-generated strategic insight from real data
    - sync_time: timestamp string
    - total_regions: count of monitored regions
    """
    from datetime import datetime
    db = get_session()
    try:
        crops = db.query(Crop).order_by(Crop.crop_name).all()
        regions = db.query(Region).order_by(Region.region_id).all()

        # ── 1. Regional heatmap data ─────────────────────────────────
        heatmap_regions = []
        all_totals = []
        for reg in regions:
            total_mt = 0.0
            for c in crops:
                latest = (db.query(Production)
                          .filter_by(crop_id=c.crop_id, region_id=reg.region_id)
                          .order_by(Production.record_date.desc()).first())
                if latest:
                    total_mt += float(latest.quantity)
            all_totals.append(total_mt)
            heatmap_regions.append({
                "name": reg.region_name,
                "district": reg.district,
                "region_id": reg.region_id,
                "total_mt": total_mt,
                "intensity": 0.0,
            })

        max_t = max(all_totals) if all_totals else 1.0
        for item in heatmap_regions:
            item["intensity"] = round(item["total_mt"] / max_t, 2) if max_t > 0 else 0.5

        # ── 2. Production vs AI-Predicted Demand per crop ────────────
        pvd_crops = []
        total_prod = 0.0
        total_pred = 0.0

        for c in crops:
            crop_prod = 0.0
            prev_prod = 0.0
            for reg in regions:
                latest_p = (db.query(Production)
                            .filter_by(crop_id=c.crop_id, region_id=reg.region_id)
                            .order_by(Production.record_date.desc()).first())
                prev_p = (db.query(Production)
                          .filter_by(crop_id=c.crop_id, region_id=reg.region_id)
                          .order_by(Production.record_date.desc()).offset(1).first())
                if latest_p:
                    crop_prod += float(latest_p.quantity)
                if prev_p:
                    prev_prod += float(prev_p.quantity)

            # AI predicted production (latest future prediction as 'demand target')
            pred_row = (db.query(Prediction)
                        .filter_by(crop_id=c.crop_id, prediction_type="production")
                        .order_by(Prediction.prediction_date.desc()).first())
            pred_val = float(pred_row.prediction_value) if pred_row else crop_prod * 1.1

            diff = crop_prod - pred_val
            is_surplus = diff >= 0
            if is_surplus:
                diff_label = f"Surplus: +{diff/1000:.1f}k Mt"
            else:
                diff_label = f"Shortfall: {diff/1000:.1f}k Mt"

            max_bar = max(crop_prod, pred_val)
            pvd_crops.append({
                "crop": c.crop_name,
                "prod_mt": crop_prod,
                "pred_mt": pred_val,
                "max_bar": max_bar,
                "prod_label": f"{crop_prod/1000:.1f}k Mt",
                "pred_label": f"{pred_val/1000:.1f}k Mt",
                "shortfall_label": diff_label,
                "is_surplus": is_surplus,
                "diff": diff,
            })

            total_prod += crop_prod
            total_pred += pred_val

        # ── 3. Food Security Score ───────────────────────────────────
        coverage = (total_prod / total_pred * 100) if total_pred > 0 else 75.0
        food_security_score = round(min(coverage, 100.0), 1)

        prev_total = 0.0
        for c in crops:
            for reg in regions:
                prev_r = (db.query(Production)
                          .filter_by(crop_id=c.crop_id, region_id=reg.region_id)
                          .order_by(Production.record_date.desc()).offset(1).first())
                if prev_r:
                    prev_total += float(prev_r.quantity)
        prev_coverage = (prev_total / total_pred * 100) if (total_pred > 0 and prev_total > 0) else food_security_score
        food_sec_change = round(food_security_score - prev_coverage, 1)

        # ── 4. Yield Growth ──────────────────────────────────────────
        growth_pcts = []
        for c in crops:
            for reg in regions:
                latest_pr = (db.query(Production)
                             .filter_by(crop_id=c.crop_id, region_id=reg.region_id)
                             .order_by(Production.record_date.desc()).first())
                prev_pr = (db.query(Production)
                           .filter_by(crop_id=c.crop_id, region_id=reg.region_id)
                           .order_by(Production.record_date.desc()).offset(1).first())
                if latest_pr and prev_pr and prev_pr.quantity:
                    pct = ((float(latest_pr.quantity) - float(prev_pr.quantity))
                           / float(prev_pr.quantity) * 100)
                    growth_pcts.append(pct)

        yield_growth = round(sum(growth_pcts) / len(growth_pcts), 1) if growth_pcts else 0.0
        if yield_growth > 2:
            yield_label = "↑ Growing"
        elif yield_growth < -2:
            yield_label = "↓ Declining"
        else:
            yield_label = "↔ Stable"

        # ── 5. Strategic Insight (auto from data) ───────────────────
        shortfall_crops = [p for p in pvd_crops if not p["is_surplus"]]
        surplus_crops = [p for p in pvd_crops if p["is_surplus"]]

        if shortfall_crops:
            worst = min(shortfall_crops, key=lambda x: x["diff"])
            insight = (
                f"{worst['crop']} production is {abs(worst['diff']/1000):.1f}k Mt below "
                f"AI-predicted demand. Consider supply chain interventions to prevent market shortages."
            )
        elif surplus_crops:
            best = max(surplus_crops, key=lambda x: x["diff"])
            insight = (
                f"{best['crop']} shows a surplus of {best['diff']/1000:.1f}k Mt above predicted demand. "
                f"Market prices may ease — consider export or strategic storage allocation."
            )
        else:
            insight = ("All crop productions are aligned with AI-predicted demand. "
                       "Market stability is maintained across monitored regions.")

        sync_time = datetime.now().strftime("%A, %I:%M %p")

        return {
            "food_security_score": food_security_score,
            "food_security_change": food_sec_change,
            "yield_growth_pct": yield_growth,
            "yield_growth_label": yield_label,
            "heatmap_regions": heatmap_regions,
            "pvd_crops": pvd_crops,
            "insight": insight,
            "sync_time": sync_time,
            "total_regions": len(regions),
        }
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECURE OFFICIAL POLICY COMMUNICATIONS (POLICYMAKER <-> ADMIN)
# ══════════════════════════════════════════════════════════════════════════════

@db_safe(default=lambda: (False, "Database error"))
def send_official_communication(sender_id, subject, message, category="Policy Advisory",
                                priority="Normal", parent_id=None, receiver_id=None):
    """
    Submits an official confidential communication / dispatch.
    If receiver_id is None, automatically routes to the first active Admin.
    """
    db = get_session()
    try:
        if not receiver_id:
            admin_user = db.query(User).filter_by(user_type="admin", is_active=True).first()
            if admin_user:
                receiver_id = admin_user.user_id

        comm = OfficialCommunication(
            sender_id=sender_id,
            receiver_id=receiver_id,
            subject=subject.strip(),
            category=category.strip() or "Policy Advisory",
            priority=priority.strip() or "Normal",
            message=message.strip(),
            parent_id=parent_id,
            status="Pending Admin Review" if not parent_id else "In Review",
            is_read_by_receiver=False,
            is_read_by_sender=True,
        )
        db.add(comm)

        # If replying to a parent thread, update the root thread's status
        if parent_id:
            parent = db.query(OfficialCommunication).filter_by(comm_id=parent_id).first()
            if parent:
                parent.is_read_by_receiver = False
                parent.status = "Action Taken" if priority == "Urgent / Confidential" else "In Review"

        db.commit()
        return True, comm.comm_id
    finally:
        db.close()


@db_safe(default=list)
def get_policymaker_communications(user_id):
    """
    Returns all root communication threads involving this policymaker,
    including any replies exchanged with the Admin desk.
    """
    db = get_session()
    try:
        from datetime import datetime
        threads = (
            db.query(OfficialCommunication)
            .filter(
                OfficialCommunication.parent_id.is_(None),
                (OfficialCommunication.sender_id == user_id) | (OfficialCommunication.receiver_id == user_id)
            )
            .order_by(OfficialCommunication.created_at.desc())
            .all()
        )

        result = []
        for t in threads:
            replies = (
                db.query(OfficialCommunication)
                .filter_by(parent_id=t.comm_id)
                .order_by(OfficialCommunication.created_at.asc())
                .all()
            )
            replies_data = []
            for r in replies:
                replies_data.append({
                    "comm_id": r.comm_id,
                    "sender_id": r.sender_id,
                    "sender_name": f"{r.sender.first_name} {r.sender.last_name}" if r.sender else "Admin Desk",
                    "sender_role": r.sender.user_type if r.sender else "admin",
                    "message": r.message,
                    "created_at": r.created_at.strftime("%b %d, %Y • %I:%M %p") if r.created_at else "",
                })

            result.append({
                "comm_id": t.comm_id,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "message": t.message,
                "status": t.status,
                "created_at": t.created_at.strftime("%b %d, %Y • %I:%M %p") if t.created_at else "",
                "sender_id": t.sender_id,
                "sender_name": f"{t.sender.first_name} {t.sender.last_name}" if t.sender else "Policymaker",
                "sender_role": t.sender.user_type if t.sender else "policymaker",
                "sender_district": t.sender.region.district if (t.sender and t.sender.region) else "National",
                "is_read": t.is_read_by_sender if t.sender_id == user_id else t.is_read_by_receiver,
                "reply_count": len(replies_data),
                "replies": replies_data,
            })
        return result
    finally:
        db.close()


@db_safe(default=list)
def get_admin_communications():
    """
    Returns all root communications from policymakers for the Admin Console.
    """
    db = get_session()
    try:
        from datetime import datetime
        threads = (
            db.query(OfficialCommunication)
            .filter(OfficialCommunication.parent_id.is_(None))
            .order_by(OfficialCommunication.created_at.desc())
            .all()
        )

        result = []
        for t in threads:
            replies = (
                db.query(OfficialCommunication)
                .filter_by(parent_id=t.comm_id)
                .order_by(OfficialCommunication.created_at.asc())
                .all()
            )
            replies_data = []
            for r in replies:
                replies_data.append({
                    "comm_id": r.comm_id,
                    "sender_id": r.sender_id,
                    "sender_name": f"{r.sender.first_name} {r.sender.last_name}" if r.sender else "Admin Desk",
                    "sender_role": r.sender.user_type if r.sender else "admin",
                    "message": r.message,
                    "created_at": r.created_at.strftime("%b %d, %Y • %I:%M %p") if r.created_at else "",
                })

            result.append({
                "comm_id": t.comm_id,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "message": t.message,
                "status": t.status,
                "created_at": t.created_at.strftime("%b %d, %Y • %I:%M %p") if t.created_at else "",
                "sender_id": t.sender_id,
                "sender_name": f"{t.sender.first_name} {t.sender.last_name}" if t.sender else "Policymaker",
                "sender_role": t.sender.user_type if t.sender else "policymaker",
                "sender_district": t.sender.region.district if (t.sender and t.sender.region) else "National",
                "is_read": t.is_read_by_receiver,
                "reply_count": len(replies_data),
                "replies": replies_data,
            })
        return result
    finally:
        db.close()


@db_safe(default=lambda: (False, "Database error"))
def reply_official_communication(sender_id, parent_id, message, new_status="Action Taken"):
    """
    Adds an official reply into a communication thread.
    """
    db = get_session()
    try:
        parent = db.query(OfficialCommunication).filter_by(comm_id=parent_id).first()
        if not parent:
            return False, "Parent thread not found."

        reply = OfficialCommunication(
            sender_id=sender_id,
            receiver_id=parent.sender_id if parent.sender_id != sender_id else parent.receiver_id,
            subject=f"Re: {parent.subject}",
            category=parent.category,
            priority=parent.priority,
            message=message.strip(),
            parent_id=parent_id,
            status=new_status,
            is_read_by_receiver=False,
            is_read_by_sender=True,
        )
        db.add(reply)
        parent.status = new_status
        parent.is_read_by_receiver = False
        db.commit()
        return True, reply.comm_id
    finally:
        db.close()


@db_safe(default=lambda: False)
def mark_communication_read(comm_id, is_admin=False):
    """Marks a thread and its replies as read."""
    db = get_session()
    try:
        thread = db.query(OfficialCommunication).filter_by(comm_id=comm_id).first()
        if thread:
            if is_admin:
                thread.is_read_by_receiver = True
            else:
                thread.is_read_by_sender = True
            replies = db.query(OfficialCommunication).filter_by(parent_id=thread.comm_id).all()
            for r in replies:
                if is_admin:
                    r.is_read_by_receiver = True
                else:
                    r.is_read_by_sender = True
            db.commit()
            return True
        return False
    finally:
        db.close()


@db_safe(default=lambda: 0)
def get_unread_communication_count(user_id=None, is_admin=False):
    """Returns number of unread official communications."""
    db = get_session()
    try:
        if is_admin:
            return db.query(OfficialCommunication).filter_by(parent_id=None, is_read_by_receiver=False).count()
        elif user_id:
            return (
                db.query(OfficialCommunication)
                .filter(
                    OfficialCommunication.parent_id.is_(None),
                    OfficialCommunication.sender_id == user_id,
                    OfficialCommunication.is_read_by_sender == False
                )
                .count()
            )
        return 0
    finally:
        db.close()


@db_safe(default=lambda: False)
def ensure_sample_communications_if_empty():
    """Seeds authentic sample policy communications if none exist."""
    db = get_session()
    try:
        if db.query(OfficialCommunication).count() > 0:
            return False

        policy_user = db.query(User).filter_by(user_type="policymaker").first()
        admin_user = db.query(User).filter_by(user_type="admin").first()

        if not policy_user or not admin_user:
            return False

        now = datetime.utcnow()

        # Thread 1: Urgent Buffer Stock Intervention
        c1 = OfficialCommunication(
            sender_id=policy_user.user_id,
            receiver_id=admin_user.user_id,
            subject="Urgent: National Buffer Stock & Dambulla Market Stabilization",
            category="Price Stabilization",
            priority="Urgent / Confidential",
            message=(
                "Analysis of regional market production indicates an impending shortfall of Leeks & Carrots "
                "across Nuwara Eliya and Kandy supply corridors. We request immediate authorization to release "
                "strategic vegetable reserves and coordinate inter-district logistics to prevent speculative price inflation."
            ),
            status="Action Taken",
            is_read_by_receiver=True,
            is_read_by_sender=True,
            created_at=now - timedelta(days=2, hours=4),
        )
        db.add(c1)
        db.commit()

        # Reply to Thread 1 from Admin
        r1 = OfficialCommunication(
            sender_id=admin_user.user_id,
            receiver_id=policy_user.user_id,
            subject="Re: Urgent: National Buffer Stock & Dambulla Market Stabilization",
            category="Price Stabilization",
            priority="Urgent / Confidential",
            message=(
                "Directive acknowledged and reviewed by Central Agricultural Administration. "
                "Strategic warehouse reserves in Welimada and Dambulla have been authorized for staged release. "
                "Regional Agrarian Officers in Kandy and Matale have been notified."
            ),
            parent_id=c1.comm_id,
            status="Action Taken",
            is_read_by_receiver=True,
            is_read_by_sender=True,
            created_at=now - timedelta(days=1, hours=22),
        )
        db.add(r1)

        # Thread 2: Monsoon Fertilizer & Yield Subsidy
        c2 = OfficialCommunication(
            sender_id=policy_user.user_id,
            receiver_id=admin_user.user_id,
            subject="Q3 Vegetable Subsidy & High-Yield Seed Quota Allocation",
            category="Policy Advisory",
            priority="High Priority",
            message=(
                "Proposal submitted for priority organic fertilizer and certified seed allocation for "
                "smallholder vegetable clusters in Matale and Kandy to mitigate predicted monsoon precipitation shifts."
            ),
            status="Pending Admin Review",
            is_read_by_receiver=False,
            is_read_by_sender=True,
            created_at=now - timedelta(hours=6),
        )
        db.add(c2)
        db.commit()
        return True
    finally:
        db.close()

