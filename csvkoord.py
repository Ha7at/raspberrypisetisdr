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
SOURCE_FOLDER = r"C:\seti\hydrogen"              # Ahol a hi.py készít CSV-ket
DEST_FOLDER = r"C:\seti\mapdata"                 # Végcél (galaktikus koordináta mappa)
LOG_FILE = r"C:\seti\csvkoord.log"

# ANTENNA (RÖG ZÍTETT!)
ANT_AZ = 177      # azimut (°, 0=É, 90=K, 180=D, 270=Ny)
ANT_EL = 77       # eleváció (°, 0=horizont, 90=zenit)
BEAM_WIDTH = 5    # nyílásszög

# MEGFIGYELŐHELY (Erdőkertes, HU)
LAT = 47.523
LON = 19.325
ELEV_M = 150

# KOORDINÁTA BINNING
COORD_STEP = 5    # 5 fokos "kocka" (l, b)

# ============================================

# Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🔧 csvkoord.py - Galaktikus koordináta szerinti rendezés\n")
logging.info("=== csvkoord.py start ===")

# Megfigyelőhely
loc = EarthLocation(lat=LAT*u.deg, lon=LON*u.deg, height=ELEV_M*u.m)

def csv_filename_to_timestamp(filename):
    """
    CSV fájlnévből kinyeri az időt
    Formátum: YYYYMMDD_HHMM.csv
    Pl: 20260327_0942.csv → 2026-03-27 09:42 UTC
    """
    try:
        # Kiterjesztés nélkül
        base = filename.replace(".csv", "")
        
        # Formátum: 20260327_0942
        date_part = base[:8]      # 20260327
        time_part = base[9:13]    # 0942
        
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
    """
    Adott időpontban a fix antenna irányából kiszámítja a galaktikus koordinátákat
    """
    try:
        # Astropy Time objektum
        t = Time(dt, scale='utc')
        
        # Horizont koordináták (antenna rögzített irányában)
        altaz = AltAz(
            alt=ANT_EL*u.deg,
            az=ANT_AZ*u.deg,
            location=loc,
            obstime=t
        )
        
        # Egyenlítői koordináták
        fk5 = SkyCoord(altaz.transform_to(FK5(equinox='J2000')))
        
        # Galaktikus koordináták
        gal = fk5.transform_to(Galactic)
        
        return gal.l.deg, gal.b.deg
    except Exception as e:
        logging.error(f"Galaktikus koordináta hiba {dt}: {e}")
        return None, None

def get_folder_name(l, b):
    """
    Galaktikus koordináták szerinti mappa név
    Pl: l175_b045 (5 fokos binning)
    """
    l_bin = int(l // COORD_STEP * COORD_STEP)
    b_bin = int(b // COORD_STEP * COORD_STEP)
    
    # Pozitív l, előjeles b
    return f"l{l_bin:03d}_b{b_bin:+04d}"

# ================ CSV FELDOLGOZÁSA ================
print(f"📡 CSV fájlok feldolgozása a {SOURCE_FOLDER} mappából...\n")

csv_files = sorted([f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".csv")])

if not csv_files:
    print("❌ Nincs CSV fájl!")
    logging.warning("No CSV files found")
    exit(1)

print(f"Talált: {len(csv_files)} fájl\n")

# Statisztika
stats = {}
copied_count = 0
skipped_count = 0
error_count = 0

for file in csv_files:
    # Idő kinyerése a fájlnévből
    dt = csv_filename_to_timestamp(file)
    if dt is None:
        print(f"  ❌ {file} - nem értelmezhető filename")
        error_count += 1
        continue
    
    # Galaktikus koordináták kiszámítása
    l_gal, b_gal = get_galactic_coords(dt)
    if l_gal is None:
        print(f"  ❌ {file} - koordináta hiba")
        error_count += 1
        continue
    
    # Mappa név
    folder_name = get_folder_name(l_gal, b_gal)
    dest_path = os.path.join(DEST_FOLDER, folder_name)
    
    # Mappa létrehozása
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        logging.info(f"New folder: {folder_name}")
    
    # Metaadatok JSON (csak az első fájlnál / vagy update-elve)
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
    
    # CSV másolása
    src_file = os.path.join(SOURCE_FOLDER, file)
    dst_file = os.path.join(dest_path, file)
    
    if os.path.exists(dst_file):
        print(f"  ⏭️  {file}")
        print(f"      → {folder_name}/ (már ott van)")
        skipped_count += 1
        logging.info(f"Skipped (exists): {file} → {folder_name}")
    else:
        try:
            shutil.copy2(src_file, dst_file)
            print(f"  ✅ {file}")
            print(f"      → {folder_name}/ (l={l_gal:.1f}°, b={b_gal:.1f}°, {dt})")
            copied_count += 1
            logging.info(f"Copied: {file} → {folder_name} ({dt})")
            
            # Statisztika
            if folder_name not in stats:
                stats[folder_name] = {"count": 0, "dates": []}
            stats[folder_name]["count"] += 1
            stats[folder_name]["dates"].append(dt.date().isoformat())
            
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

print(f"\n📁 Mappák summary:")
for folder_name in sorted(stats.keys()):
    info = stats[folder_name]
    dates = list(set(info["dates"]))  # Egyedi dátumok
    print(f"  {folder_name}/: {info['count']} fájl ({len(dates)} nap)")
    logging.info(f"  {folder_name}: {info['count']} files, {len(dates)} days")

print("="*70)
logging.info("=== csvkoord.py end ===\n")
