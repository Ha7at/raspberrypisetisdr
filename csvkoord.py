#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import json
import logging
from datetime import datetime
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, FK5, Galactic
from astropy.time import Time
import astropy.units as u

# ================== CONFIG ==================
SOURCE_FOLDER = r"C:\pi_sdr\seti\data"
DEST_FOLDER = r"C:\pi_sdr\seti\kep"
LOG_FILE = r"C:\pi_sdr\seti\csvkoord.log"

# ANTENNA (RÖGZÍTETT!)
ANT_AZ = 177
ANT_EL = 77
BEAM_WIDTH = 5

# MEGFIGYELŐHELY (Erdőkertes, HU)
LAT = 47.523
LON = 19.325
ELEV_M = 150

# KOORDINÁTA BINNING
COORD_STEP = 5

# ============================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🔧 csvkoord.py - Galaktikus koordináta szerinti rendezés\n")
logging.info("=== csvkoord.py start ===")

loc = EarthLocation(lat=LAT*u.deg, lon=LON*u.deg, height=ELEV_M*u.m)

def csv_filename_to_timestamp(filename):
    """CSV fájlnévből kinyeri az időt: YYYYMMDD_HHMM.csv"""
    try:
        base = filename.replace(".csv", "")
        date_part = base[:8]
        time_part = base[9:13]
        
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        
        dt = datetime(year, month, day, hour, minute, 0)
        return dt
    except Exception as e:
        logging.error(f"Időfeldolgozás hiba '{filename}': {e}")
        return None

def get_galactic_coords(dt):
    """Adott időpontban a fix antenna irányából galaktikus koordináták"""
    try:
        t = Time(dt, scale='utc')
        altaz = AltAz(
            alt=ANT_EL*u.deg,
            az=ANT_AZ*u.deg,
            location=loc,
            obstime=t
        )
        fk5 = SkyCoord(altaz.transform_to(FK5(equinox='J2000')))
        gal = fk5.transform_to(Galactic)
        return gal.l.deg, gal.b.deg
    except Exception as e:
        logging.error(f"Galaktikus koordináta hiba {dt}: {e}")
        return None, None

def get_folder_name(l, b):
    """Galaktikus koordináták szerinti mappa név (5 fokos binning)"""
    l_bin = int(l // COORD_STEP * COORD_STEP)
    b_bin = int(b // COORD_STEP * COORD_STEP)
    return f"l{l_bin:03d}_b{b_bin:+04d}"

# ================ CSV FELDOLGOZÁSA ================
print(f"📡 CSV fájlok feldolgozása: {SOURCE_FOLDER}\n")

csv_files = sorted([f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".csv")])

if not csv_files:
    print("❌ Nincs CSV fájl!")
    logging.warning("No CSV files found")
    exit(1)

print(f"Talált: {len(csv_files)} fájl\n")

stats = {}
copied_count = 0
skipped_count = 0
error_count = 0

for file in csv_files:
    dt = csv_filename_to_timestamp(file)
    if dt is None:
        print(f"  ❌ {file} - nem értelmezhető filename")
        error_count += 1
        continue
    
    l_gal, b_gal = get_galactic_coords(dt)
    if l_gal is None:
        print(f"  ❌ {file} - koordináta hiba")
        error_count += 1
        continue
    
    folder_name = get_folder_name(l_gal, b_gal)
    dest_path = os.path.join(DEST_FOLDER, folder_name)
    
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        logging.info(f"New folder: {folder_name}")
    
    metadata_file = os.path.join(dest_path, "_info.json")
    if not os.path.exists(metadata_file):
        metadata = {
            "antenna_az_deg": ANT_AZ,
            "antenna_el_deg": ANT_EL,
            "beam_width_deg": BEAM_WIDTH,
            "galactic_l_deg": round(l_gal, 2),
            "galactic_b_deg": round(b_gal, 2),
            "observer_lat": LAT,
            "observer_lon": LON,
            "observer_elev_m": ELEV_M,
            "first_observation": dt.isoformat(),
            "file_count": 0
        }
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    src_file = os.path.join(SOURCE_FOLDER, file)
    dst_file = os.path.join(dest_path, file)
    
    if os.path.exists(dst_file):
        print(f"  ⏭️  {file} → {folder_name}/ (már ott van)")
        skipped_count += 1
        logging.info(f"Skipped (exists): {file}")
    else:
        try:
            shutil.copy2(src_file, dst_file)
            print(f"  ✅ {file} → {folder_name}/ (l={l_gal:.1f}°, b={b_gal:.1f}°)")
            copied_count += 1
            logging.info(f"Copied: {file} → {folder_name}")
            
            if folder_name not in stats:
                stats[folder_name] = {"count": 0}
            stats[folder_name]["count"] += 1
            
        except Exception as e:
            print(f"  ❌ {file} - másolás hiba: {e}")
            error_count += 1
            logging.error(f"Copy error {file}: {e}")

# ================ ÖSSZEFOGLALÓ ================
print("\n" + "="*70)
print("✅ FELDOLGOZÁS KÉSZ")
print("="*70)
print(f"Másolva: {copied_count}")
print(f"Átugrom (már ott): {skipped_count}")
print(f"Hiba: {error_count}")
print(f"\n📁 Koordináta mappák: {len(stats)}")
for folder_name in sorted(stats.keys()):
    print(f"  {folder_name}/: {stats[folder_name]['count']} fájl")
print("="*70)
logging.info("=== csvkoord.py end ===\n")
