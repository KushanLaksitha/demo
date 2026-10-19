"""
Populates demo data (2 years of weekly price/production/climate history,
plus sample predictions, alerts, recommendations) for Matale & Kandy,
for the 5 AgriSense crops: Okra, Cabbage, Beans, Carrots, Leeks.

Run once after schema.sql has been applied:
    python database/seed_demo_data.py
"""
import random
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_connection import get_session, engine
from database.models import (
    Base, Region, Crop, Production, Price, Climate, Prediction, User,
    UserPreferences, Alert, Recommendation, Feedback
)
from utils.auth_utils import hash_password

random.seed(42)

# Base LKR/kg price + typical yearly cycle amplitude per crop
CROP_BASE_PRICE = {
    "Okra": (280, 60),
    "Cabbage": (140, 50),
    "Beans": (320, 70),
    "Carrots": (260, 55),
    "Leeks": (300, 65),
}
CROP_BASE_PRODUCTION = {   # kg per week per region (demo scale)
    "Okra": (4000, 900),
    "Cabbage": (9000, 2500),
    "Beans": (3500, 800),
    "Carrots": (5000, 1200),
    "Leeks": (3800, 900),
}


def run():
    Base.metadata.create_all(engine)  # safety net if schema.sql wasn't run
    db = get_session()

    try:
        regions = {r.district: r for r in db.query(Region).all()}
        if not regions:
            for name, dist in [("Matale Region", "Matale"), ("Kandy Region", "Kandy")]:
                r = Region(region_name=name, district=dist)
                db.add(r)
            db.commit()
            regions = {r.district: r for r in db.query(Region).all()}

        crops = {c.crop_name: c for c in db.query(Crop).all()}
        if not crops:
            for name in CROP_BASE_PRICE:
                db.add(Crop(crop_name=name, category="Vegetable"))
            db.commit()
            crops = {c.crop_name: c for c in db.query(Crop).all()}

        excel_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "AgriSense_Dataset_2021_2025_Cleaned.xlsx")
        if os.path.exists(excel_file):
            print("[Seed] Importing real 2021-2025 dataset from Excel...")
            from database.import_excel_dataset import run_import
            run_import()
        else:
            # Fallback synthetic data generator if Excel file is absent
            start = date.today() - timedelta(weeks=104)
            for week in range(104):
                d = start + timedelta(weeks=week)
                season = "Maha" if d.month in (10, 11, 12, 1, 2, 3) else "Yala"
                seasonal_factor = 1.15 if season == "Maha" else 0.9

                for district, region in regions.items():
                    for crop_name, crop in crops.items():
                        base_p, amp_p = CROP_BASE_PRICE[crop_name]
                        price_val = max(
                            50, base_p + amp_p * random.uniform(-0.6, 0.6)
                            + (20 if district == "Nuwara" else 0)
                        )
                        db.add(Price(price=round(price_val, 2), date=d,
                                      crop_id=crop.crop_id, region_id=region.region_id))

                        base_q, amp_q = CROP_BASE_PRODUCTION[crop_name]
                        qty = max(200, (base_q * seasonal_factor) + amp_q * random.uniform(-0.5, 0.5))
                        db.add(Production(season=season, quantity=round(qty, 2), unit="Mt",
                                            record_date=d, crop_id=crop.crop_id,
                                            region_id=region.region_id))

                    db.add(Climate(
                        record_date=d, region_id=region.region_id,
                        rainfall_mm=round(random.uniform(20, 220), 1),
                        avg_temp_c=round(random.uniform(22, 31), 1),
                        humidity_pct=round(random.uniform(55, 90), 1),
                    ))
            db.commit()

        # Re-fetch crops & regions after import
        crops = {c.crop_name: c for c in db.query(Crop).all()}
        regions = {r.district: r for r in db.query(Region).all()}

        # ---- demo predictions (next 4 weeks per crop, Matale) ----
        matale = regions["Matale"]
        forecast_start = date.today() + timedelta(weeks=1)
        for crop_name, crop in crops.items():
            base_p, amp_p = CROP_BASE_PRICE[crop_name]
            for w in range(4):
                fdate = forecast_start + timedelta(weeks=w)
                pred_price = round(base_p + amp_p * random.uniform(-0.3, 0.4), 2)
                db.add(Prediction(prediction_type="price", prediction_value=pred_price,
                                    prediction_date=fdate, crop_id=crop.crop_id,
                                    region_id=matale.region_id))
                base_q, amp_q = CROP_BASE_PRODUCTION[crop_name]
                pred_qty = round(base_q + amp_q * random.uniform(-0.2, 0.3), 2)
                db.add(Prediction(prediction_type="production", prediction_value=pred_qty,
                                    prediction_date=fdate, crop_id=crop.crop_id,
                                    region_id=matale.region_id))
        db.commit()

        # ---- demo users (one per role, already confirmed) ----
        demo_users = [
            ("farmer@agrisense.lk", "farmer", "Kasun", "Perera", "Matale"),
            ("trader@agrisense.lk", "trader", "Nadeesha", "Silva", "Kandy"),
            ("policy@agrisense.lk", "policymaker", "Ruwan", "Bandara", "Kandy"),
            ("admin@agrisense.lk", "admin", "System", "Admin", "Matale"),
        ]
        existing_emails = {u.email for u in db.query(User).all()}
        for email, role, fn, ln, dist in demo_users:
            if email in existing_emails:
                continue
            u = User(email=email, password=hash_password("Demo@1234"),
                      user_type=role, first_name=fn, last_name=ln,
                      region_id=regions[dist].region_id, is_active=True)
            db.add(u)
            db.commit()
            db.add(UserPreferences(user_id=u.user_id, preferred_crops=",".join(
                str(c.crop_id) for c in list(crops.values())[:3])))
            db.commit()

            if role != "admin":
                sample_role_alerts = {
                    "farmer": [
                        ("price_spike", f"Beans wholesale price predicted to spike to Rs.420/kg (+24%) in {dist}. Favorable window for early selling."),
                        ("price_drop", f"Cabbage price forecast to drop to Rs.105/kg (-16%) in {dist}. Hold harvest or explore alternative markets."),
                        ("heavy_rain", f"Heavy rainfall predicted (165mm) in {dist}. Protect crops from waterlogging and delay fertilizer application."),
                        ("production_surplus", f"Beans harvest surplus expected (4,200 Mt, 137% of baseline) in {dist}. Plan distributed sales."),
                        ("official_notice", f"Agrarian Services Advisory: Fall Armyworm (සේනා දළඹු) inspection active in {dist}. Report damage to AI officer."),
                    ],
                    "trader": [
                        ("price_spike", f"Carrots wholesale price surging (+22%) in {dist} wholesale market due to transport constraints."),
                        ("production_shortage", f"Leeks production shortage predicted (2,400 Mt, 63% of seasonal average). Premium pricing opportunity."),
                        ("drought_risk", f"Dry spell forecast (22mm rain) in {dist}. Produce drying yards operating under clear skies."),
                        ("official_notice", f"Dambulla Dedicated Economic Centre: Extended wholesale receiving hours active for produce traders."),
                    ],
                    "policymaker": [
                        ("production_shortage", "National harvest shortage projected for Leeks and Carrots in Q3. Buffer stock intervention recommended."),
                        ("production_surplus", f"Cabbage oversupply alert across {dist} (142% of baseline). Inter-district redistribution advised."),
                        ("heavy_rain", f"Precipitation anomaly: Monsoon rainfall variance exceeding 170mm in {dist} watershed."),
                        ("official_notice", "Ministry of Agriculture: Vegetable Price Stabilization and National Task Force convened."),
                    ],
                }
                for atype, amsg in sample_role_alerts.get(role, []):
                    db.add(Alert(alert_type=atype, message=amsg, user_id=u.user_id, is_read=False))
                db.add(Recommendation(
                    message=f"Good time to plan harvesting {list(crops.keys())[1]} — demand trending up in Kandy.",
                    user_id=u.user_id, region_id=regions[dist].region_id))
        db.commit()

        # ---- one demo feedback entry ----
        first_user = db.query(User).filter_by(user_type="farmer").first()
        if first_user and not db.query(Feedback).first():
            db.add(Feedback(message="Price chart page loads really fast, thanks!",
                              user_id=first_user.user_id))
            db.commit()

        # ---- sample official policy communications ----
        from database.data_service import ensure_sample_communications_if_empty
        ensure_sample_communications_if_empty()

        print("[Seed] Demo data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    run()

