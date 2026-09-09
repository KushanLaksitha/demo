"""
AgriSense Excel Dataset Importer
================================
Imports cleaned 2021-2025 dataset (AgriSense_Dataset_2021_2025_Cleaned.xlsx) into MySQL:
  1. Clears existing records from 'price', 'production', and 'climate' tables.
  2. Imports 2,285 weekly price records into 'price'.
  3. Imports matching production records (in Mt) for every market week into 'production'.
  4. Imports baseline monthly weather records (120 rows) + weekly weather entries into 'climate'.

Usage:
  python database/import_excel_dataset.py
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from database.db_connection import get_session, engine
from database.models import Base, Region, Crop, Price, Production, Climate


EXCEL_FILENAME = "AgriSense_Dataset_2021_2025_Cleaned.xlsx"
EXCEL_PATH = os.path.join(BASE_DIR, EXCEL_FILENAME)


def run_import():
    if not os.path.exists(EXCEL_PATH):
        print(f"[Error] Dataset file not found at: {EXCEL_PATH}")
        sys.exit(1)

    print(f"[*] Reading Excel dataset: {EXCEL_PATH}")
    xls = pd.ExcelFile(EXCEL_PATH)
    
    df_price = pd.read_excel(xls, "Weekly Prices")
    df_prod = pd.read_excel(xls, "Production Data")
    df_weather = pd.read_excel(xls, "Weather Data")

    print(f"[*] Loaded sheets:")
    print(f"    - Weekly Prices  : {len(df_price)} rows")
    print(f"    - Production Data: {len(df_prod)} rows")
    print(f"    - Weather Data   : {len(df_weather)} rows")

    # Clean duplicates in Weekly Prices
    df_price_clean = df_price.drop_duplicates(subset=["Date", "Vegetable", "District"]).copy()
    print(f"[*] Deduplicated Weekly Prices: {len(df_price_clean)} rows")

    # Ensure tables exist
    Base.metadata.create_all(engine)
    db = get_session()

    try:
        # 1. Resolve Regions
        regions = {r.district: r for r in db.query(Region).all()}
        if not regions:
            print("[*] Creating default regions (Matale, Kandy)...")
            for name, dist in [("Matale Region", "Matale"), ("Kandy Region", "Kandy")]:
                r = Region(region_name=name, district=dist)
                db.add(r)
            db.commit()
            regions = {r.district: r for r in db.query(Region).all()}

        # 2. Resolve Crops
        crops = {c.crop_name: c for c in db.query(Crop).all()}
        crop_names = ["Beans", "Cabbage", "Carrots", "Leeks", "Okra"]
        missing_crops = [cn for cn in crop_names if cn not in crops]
        if missing_crops:
            print(f"[*] Creating missing crops: {missing_crops}...")
            for cn in missing_crops:
                db.add(Crop(crop_name=cn, category="Vegetable"))
            db.commit()
            crops = {c.crop_name: c for c in db.query(Crop).all()}

        # 3. Clear existing price, production, climate records as requested
        print("[*] Clearing existing price, production, and climate records...")
        deleted_prices = db.query(Price).delete()
        deleted_prod = db.query(Production).delete()
        deleted_clim = db.query(Climate).delete()
        db.commit()
        print(f"    - Deleted {deleted_prices} price rows")
        print(f"    - Deleted {deleted_prod} production rows")
        print(f"    - Deleted {deleted_clim} climate rows")

        # 4. Build Production lookup: (Vegetable, District, Year, Season) -> Production Volume (Mt)
        prod_lookup = {}
        for _, r in df_prod.iterrows():
            veg = str(r["Vegetable"]).strip()
            dist = str(r["District"]).strip()
            yr = int(r["Year"])
            sea = str(r["Season"]).strip()
            vol = float(r["Production Volume (Mt)"])
            prod_lookup[(veg, dist, yr, sea)] = vol

        # 5. Build Weather lookup: (Year, Month, District) -> (avg_temp, rainfall, humidity)
        temp_col = [c for c in df_weather.columns if "temp" in c.lower()][0]
        rain_col = [c for c in df_weather.columns if "rain" in c.lower()][0]
        hum_col = [c for c in df_weather.columns if "humid" in c.lower()][0]

        weather_lookup = {}
        monthly_weather_dates = set()

        for _, r in df_weather.iterrows():
            dt = pd.to_datetime(r["Date"]).date()
            dist = str(r["District"]).strip()
            t_val = round(float(r[temp_col]), 2)
            r_val = round(float(r[rain_col]), 2)
            h_val = round(float(r[hum_col]), 2)
            weather_lookup[(dt.year, dt.month, dist)] = (t_val, r_val, h_val)
            monthly_weather_dates.add((dt, dist))

            # Insert baseline monthly climate record
            if dist in regions:
                db.add(Climate(
                    record_date=dt,
                    region_id=regions[dist].region_id,
                    rainfall_mm=r_val,
                    avg_temp_c=t_val,
                    humidity_pct=h_val,
                ))

        # 6. Insert Prices & Matching Production
        price_objects = []
        prod_objects = []
        inserted_dates_dist = set()

        for _, r in df_price_clean.iterrows():
            veg = str(r["Vegetable"]).strip()
            dist = str(r["District"]).strip()
            yr = int(r["Year"])
            sea = str(r["Season"]).strip()
            p_val = round(float(r["Price (Rs/kg)"]), 2)
            dt = pd.to_datetime(r["Date"]).date()

            crop_obj = crops.get(veg)
            reg_obj = regions.get(dist)

            if not crop_obj or not reg_obj:
                continue

            # Price record
            price_objects.append(Price(
                price=p_val,
                date=dt,
                crop_id=crop_obj.crop_id,
                region_id=reg_obj.region_id,
            ))

            # Production record (Volume in Mt)
            prod_vol = prod_lookup.get((veg, dist, yr, sea))
            if prod_vol is not None:
                prod_objects.append(Production(
                    season=sea,
                    quantity=round(prod_vol, 2),
                    unit="Mt",
                    record_date=dt,
                    crop_id=crop_obj.crop_id,
                    region_id=reg_obj.region_id,
                ))

            # Weekly climate record
            date_dist_key = (dt, dist)
            if date_dist_key not in monthly_weather_dates and date_dist_key not in inserted_dates_dist:
                inserted_dates_dist.add(date_dist_key)
                w_info = weather_lookup.get((dt.year, dt.month, dist))
                if w_info:
                    t_val, r_val, h_val = w_info
                    db.add(Climate(
                        record_date=dt,
                        region_id=reg_obj.region_id,
                        rainfall_mm=r_val,
                        avg_temp_c=t_val,
                        humidity_pct=h_val,
                    ))

        # Bulk save price and production records in chunks for efficiency
        print(f"[*] Inserting {len(price_objects)} price records...")
        db.bulk_save_objects(price_objects)

        print(f"[*] Inserting {len(prod_objects)} production records...")
        db.bulk_save_objects(prod_objects)

        db.commit()

        # 7. Verification statistics
        total_p = db.query(Price).count()
        total_prod = db.query(Production).count()
        total_clim = db.query(Climate).count()

        min_date = db.query(Price.date).order_by(Price.date.asc()).first()[0]
        max_date = db.query(Price.date).order_by(Price.date.desc()).first()[0]

        print("\n" + "=" * 50)
        print(" [SUCCESS] Excel Dataset Imported Successfully!")
        print("=" * 50)
        print(f"  • Total Prices in DB      : {total_p:,}")
        print(f"  • Total Productions in DB : {total_prod:,}")
        print(f"  • Total Climates in DB    : {total_clim:,}")
        print(f"  • Active Date Range       : {min_date} to {max_date}")
        print(f"  • Crops Populated         : {', '.join(sorted(crops.keys()))}")
        print(f"  • Districts Populated     : {', '.join(sorted(regions.keys()))}")
        print("=" * 50)

    except Exception as ex:
        db.rollback()
        print(f"[Error] Failed to import dataset: {ex}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_import()
