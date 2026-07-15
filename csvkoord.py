#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import json
import logging
import re
import math
from datetime import datetime
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
import astropy.units as u

# ================== CONFIG ==================
SOURCE_FOLDER = r"C:\seti\hydrogen"          # Nyers mérési fájlok helye
DEST_FOLDER = r"C:\seti\mapdata_radec"       # Célmappa
LOG_FILE = r"C:\seti\mapdata_radec\csvkoord_radec.log"

# ANTENNA REÁLIS FIZIKAI HELYZETE ERDŐKERTESEN
ANT_AZ = 177.0     # Fix Azimut
ANT_EL = 81.0      # Fix Eleváció a 12 cm emelés és szoftveres hangolás után
BEAM_WIDTH = 4   # Sugárszélesség

# MEGFIGYELŐHELY (Erdőkertes, HU)
LAT = 47.523
LON = 19.325
ELEV_M = 150

# 6 FOKOS CSOPORTOSÍTÁS NEM ÖSSZEHASONLÍTÁSHOZ
COORD_STEP = 4
# ============================================

if not os.path.exists(DEST_FOLDER):
    os.makedirs(DEST_FOLDER)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
print("🔧 csvkoord.py - CSILLAGIDŐ-KOMPENZÁLT (LST), NAPI 4 PERCES ELTOLÓDÁST JAVÍTÓ RENDEZÉS\n")

# Erdőkertes fizikai elhelyezkedése az Astropy számára
loc = EarthLocation(lat=LAT*u.deg, lon=LON*u.deg, height=ELEV_M*u.m)

def csv_filename_to_timestamp(filename):
    try:
        base = filename.replace(".csv", "")
        match_ido = re.search(r"(\d{8})_(\d{4})", base)
        if match_ido:
            date_part = match_ido.group(1)
            time_part = match_ido.group(2)
            return datetime(int(date_part[:4]), int(date_part[4:6]), int(date_part[6:8]), int(time_part[:2]), int(time_part[2:4]), 0)
    except:
        return None

def get_radec_coords(dt):
    try:
        # 1. Átváltjuk a fájl polgári idejét Astropy Time objektummá (UTC)
        t = Time(dt, scale='utc', location=loc)
        
        # 🔥 A TRÓFEA: Lekérjük a Helyi Látszólagos Csillagidőt (LST) Erdőkertesre.
        # Ez a sor automatikusan kezeli a napi 4 perces égi sietést a dátum alapján!
        lst_hours = t.sidereal_time('apparent').hour
        
        # 2. Kiszámoljuk az AltAz koordináta-keretet az adott pillanatra
        altaz_frame = AltAz(obstime=t, location=loc)
        altaz_coord = SkyCoord(alt=ANT_EL*u.deg, az=ANT_AZ*u.deg, frame=altaz_frame)
        
        # 3. Átforgatjuk az égi egyenlítői rendszerbe (ICRS)
        radec_coord = altaz_coord.transform_to('icrs')
        
        ra_deg = radec_coord.ra.degree
        dec_deg = radec_coord.dec.degree
        
        # Bevált 1.5 fokos szoftveres Azimut korrekció vízszintesen
        ra_deg = (ra_deg - 1.5) % 360
        
        return ra_deg, dec_deg, lst_hours
    except:
        return None, None, None

def get_folder_name(ra, dec):
    # Szigorú standard lefelé kerekítés math.floor-ral a tiszta dobozokért
    ra_bin = int(math.floor(ra / COORD_STEP) * COORD_STEP)
    dec_bin = int(math.floor(dec / COORD_STEP) * COORD_STEP)
    return f"ra{ra_bin:03d}_dec{dec_bin:+04d}"

# ================ CSV FELDOLGOZÁSA ================
csv_files = sorted([f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".csv")])
print(f"📡 CSV fájlok vizsgálata a '{SOURCE_FOLDER}' mappában...")
print(f"Talált nyers fájlok száma: {len(csv_files)}\n")

stats = {}
copied_count, skipped_count, filtered_count = 0, 0, 0

for file in csv_files:
    dt_utc = csv_filename_to_timestamp(file)
    if dt_utc is None: continue
    
    # IDŐSZŰRŐ A NAPPALI ZAJ ELLEN (Kihagyjuk a meleg órákat: 10:00 és 17:00 UTC között)
    if 10 <= dt_utc.hour < 17:
        filtered_count += 1
        continue
    
    ra_gal, dec_gal, lst_h = get_radec_coords(dt_utc)
    if ra_gal is None: continue
    
    folder_name = get_folder_name(ra_gal, dec_gal)
    dest_path = os.path.join(DEST_FOLDER, folder_name)
    os.makedirs(dest_path, exist_ok=True)
    
    metadata_file = os.path.join(dest_path, "_info.json")
    if not os.path.exists(metadata_file):
        metadata = {
            "antenna_az_deg_nominal": ANT_AZ,
            "antenna_el_deg_nominal": ANT_EL,
            "software_az_offset_deg": -1.5,
            "beam_width_deg": BEAM_WIDTH,
            "center_ra_deg": round(ra_gal, 2),
            "center_dec_deg": round(dec_gal, 2),
            "coordinate_system": "Equatorial (RA/DEC) - SIDEREAL TIME COMPENSATED"
        }
        with open(metadata_file, "w") as f: 
            json.dump(metadata, f, indent=2)
    
    dst_file = os.path.join(dest_path, file)
    if os.path.exists(dst_file):
        skipped_count += 1
    else:
        try:
            shutil.copy2(os.path.join(SOURCE_FOLDER, file), dst_file)
            print(f"✅ {file} → {folder_name}/ (RA={ra_gal:.1f}°, DEC={dec_gal:.1f}°, LST={lst_h:.2f}h)")
            copied_count += 1
            if folder_name not in stats: stats[folder_name] = 0
            stats[folder_name] += 1
        except:
            pass

print("\n" + "="*70)
print("✅ TISZTÍTOTT CSILLAGIDŐ-ALAPÚ RENDEZÉS KÉSZ")
print(f"Másolva: {copied_count} | Kiszűrt nappali zajfájl: {filtered_count} | Átugorva: {skipped_count}")
print("="*70)
