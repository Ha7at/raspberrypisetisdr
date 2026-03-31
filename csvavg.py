#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import logging
from scipy.signal import savgol_filter

# ================= CONFIG =================
KEP_FOLDER = r"C:\pi_sdr\seti\kep"
OUTPUT_FOLDER = r"C:\pi_sdr\seti\dataavg"
LOG_FILE = os.path.join(OUTPUT_FOLDER, "csvavg.log")

# Savitzky-Golay szűrés paraméterek
WINDOW_LENGTH = 51  # Páratlan szám (51, 101, 151...)
POLYORDER = 3       # Polinom rend (3-5 ajánlott)

# ==========================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("📊 csvavg.py - Koordinátánként átlagolás + Simítás\n")
logging.info("=== csvavg.py start ===")

# Output mappa
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Koordináta mappák keresése (l*_b*/)
coord_folders = sorted([d for d in os.listdir(KEP_FOLDER) 
                       if os.path.isdir(os.path.join(KEP_FOLDER, d)) 
                       and d.startswith("l") and "_b" in d])

if not coord_folders:
    print("❌ Nincs l*_b* mappa!")
    logging.error("No coordinate folders found")
    exit(1)

print(f"Talált: {len(coord_folders)} koordináta mappa")
print(f"Szűrés: Savitzky-Golay (window={WINDOW_LENGTH}, polyorder={POLYORDER})\n")

# Feldolgozás
processed_count = 0
error_count = 0

for coord_folder in coord_folders:
    coord_path = os.path.join(KEP_FOLDER, coord_folder)
    
    # CSV fájlok a mappában
    csv_files = sorted([f for f in os.listdir(coord_path) 
                       if f.endswith(".csv")])
    
    if not csv_files:
        print(f"  ⚠️  {coord_folder} - nincs CSV")
        logging.warning(f"No CSV files in {coord_folder}")
        continue
    
    try:
        df_list = []
        
        for file in csv_files:
            file_path = os.path.join(coord_path, file)
            try:
                df = pd.read_csv(file_path)
                
                # Szükséges oszlopok
                if "frequency_hz" in df.columns and "power_db" in df.columns:
                    df = df[["frequency_hz", "power_db"]].copy()
                    df_list.append(df)
                else:
                    logging.warning(f"Missing columns in {file}")
            except Exception as e:
                logging.error(f"Error reading {file}: {e}")
        
        if not df_list:
            print(f"  ⚠️  {coord_folder} - nincs feldolgozható adat")
            logging.warning(f"No processable data in {coord_folder}")
            continue
        
        # Összefűzés
        all_data = pd.concat(df_list, ignore_index=True)
        
        # ================= ÁTLAGOLÁS =================
        avg_data = all_data.groupby("frequency_hz", as_index=False).agg({
            'power_db': ['mean', 'std', 'min', 'max', 'count']
        }).reset_index(drop=True)
        
        # Oszlopnevek
        avg_data.columns = ['frequency_hz', 'power_db_avg', 'power_db_std', 
                           'power_db_min', 'power_db_max', 'measurement_count']
        
        # ================= SIMÍTÁS (Savitzky-Golay) =================
        # Szűrés csak akkor, ha van elég pont
        if len(avg_data) >= WINDOW_LENGTH:
            avg_data['power_db_smoothed'] = savgol_filter(
                avg_data['power_db_avg'].values,
                window_length=WINDOW_LENGTH,
                polyorder=POLYORDER
            )
        else:
            # Ha túl kevés pont: eredeti átlag
            avg_data['power_db_smoothed'] = avg_data['power_db_avg'].values
            logging.warning(f"{coord_folder}: Kevés pont ({len(avg_data)}), simítás kihagyva")
        
        # ============================================
        
        # Időbélyeg hozzáadása
        avg_data.insert(0, "timestamp_utc", pd.Timestamp.utcnow().isoformat())
        
        # Output filename
        output_file = f"avg_{coord_folder}.csv"
        output_path = os.path.join(OUTPUT_FOLDER, output_file)
        
        # Mentés
        avg_data.to_csv(output_path, index=False)
        
        print(f"  ✅ {coord_folder}")
        print(f"      → {output_file}")
        print(f"      Fájlok: {len(csv_files)}, Pontok: {len(avg_data)}")
        
        processed_count += 1
        logging.info(f"Processed: {coord_folder} ({len(csv_files)} files, {len(avg_data)} bins, smoothed)")
        
    except Exception as e:
        print(f"  ❌ {coord_folder} - Hiba: {e}")
        logging.error(f"Error processing {coord_folder}: {e}")
        error_count += 1

print("\n" + "="*70)
print("✅ ÁTLAGOLÁS + SIMÍTÁS KÉSZ")
print("="*70)
print(f"Feldolgozva: {processed_count}")
print(f"Hiba: {error_count}")
print(f"Output mappa: {OUTPUT_FOLDER}")
logging.info(f"=== csvavg.py end === Processed: {processed_count}, Errors: {error_count}\n")
