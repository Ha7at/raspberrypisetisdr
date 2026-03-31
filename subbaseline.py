#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import logging

# ================== CONFIG ==================
INPUT_FOLDER = r"C:\seti\dataavg"      # avg_*.csv innen
BASELINE_FILE = r"C:\seti\hydrogen\baseline.csv"
OUTPUT_FOLDER = r"C:\seti\dataavg_corrected"
LOG_FILE = r"C:\seti\subtract_baseline.log"

# ==========================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🔧 subtract_baseline.py - Baseline levonás\n")
logging.info("=== subtract_baseline.py start ===")

# Output mappa
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Baseline beolvasása
if not os.path.exists(BASELINE_FILE):
    print(f"❌ Baseline fájl nem létezik: {BASELINE_FILE}")
    logging.error(f"Baseline file not found: {BASELINE_FILE}")
    exit(1)

baseline = pd.read_csv(BASELINE_FILE)
print(f"✅ Baseline beolvasva: {len(baseline)} bin\n")
logging.info(f"Baseline loaded: {len(baseline)} bins")

# avg_*.csv fájlok keresése
csv_files = sorted([f for f in os.listdir(INPUT_FOLDER) 
                    if f.startswith("avg_") and f.endswith(".csv")])

if not csv_files:
    print("❌ Nincs avg_*.csv fájl!")
    logging.warning("No avg_*.csv files found")
    exit(1)

print(f"Talált: {len(csv_files)} fájl\n")

# Feldolgozás
processed_count = 0
error_count = 0

for file in csv_files:
    input_path = os.path.join(INPUT_FOLDER, file)
    output_file = file.replace("avg_", "avg_").replace(".csv", "_corrected.csv")
    output_path = os.path.join(OUTPUT_FOLDER, output_file)
    
    try:
        # Beolvasás
        data = pd.read_csv(input_path)
        
        # Szükséges oszlopok ellenőrzése
        if "frequency_hz" not in data.columns or "power_db_avg" not in data.columns:
            print(f"  ⚠️  {file} - hiányzó oszlopok")
            logging.warning(f"Missing columns in {file}")
            continue
        
        # Baseline merge (frequency_hz alapján)
        data_merged = pd.merge(
            data,
            baseline[["frequency_hz", "baseline_db"]],
            on="frequency_hz",
            how="left"
        )
        
        # Baseline levonás
        data_merged["power_db_corrected"] = data_merged["power_db_avg"] - data_merged["baseline_db"]
        
        # Munka oszlopok eltávolítása
        result = data_merged.drop(columns=["baseline_db"])
        
        # Mentés
        result.to_csv(output_path, index=False)
        
        print(f"  ✅ {file}")
        print(f"      → {output_file}")
        print(f"      Korrekció: {data_merged['power_db_corrected'].min():.2f} … {data_merged['power_db_corrected'].max():.2f} dB")
        
        processed_count += 1
        logging.info(f"Processed: {file} → {output_file}")
        
    except Exception as e:
        print(f"  ❌ {file} - Hiba: {e}")
        logging.error(f"Error processing {file}: {e}")
        error_count += 1

print("\n" + "="*70)
print("✅ BASELINE LEVONÁS KÉSZ")
print("="*70)
print(f"Feldolgozva: {processed_count}")
print(f"Hiba: {error_count}")
print(f"Output mappa: {OUTPUT_FOLDER}")
logging.info(f"=== subtract_baseline.py end === Processed: {processed_count}, Errors: {error_count}\n")