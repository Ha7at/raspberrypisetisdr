#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import logging

# ================== CONFIG ==================
HYDROGEN_FOLDER = r"C:\seti\hydrogen"
BASELINE_FILE = os.path.join(HYDROGEN_FOLDER, "baseline.csv")
LOG_FILE = os.path.join(HYDROGEN_FOLDER, "baseline_calc.log")

PERCENTILE = 8  # 10. percentilis (robusztus)

# ==========================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("📊 baseline_calc.py - Baseline kalkulálás")
print(f"Mappa: {HYDROGEN_FOLDER}\n")
logging.info("=== baseline_calc.py start ===")

# CSV fájlok keresése (csak .csv, nem baseline.csv)
csv_files = sorted([f for f in os.listdir(HYDROGEN_FOLDER) 
                    if f.endswith(".csv") and f != "baseline.csv"])

if not csv_files:
    print("❌ Nincs CSV fájl a hydrogen mappában!")
    logging.warning("No CSV files found")
    exit(1)

print(f"Talált: {len(csv_files)} fájl\n")
print(f"Módszer: {PERCENTILE}. percentilis\n")

# Összes adat gyűjtése
all_data = []
processed_count = 0

for file in csv_files:
    path = os.path.join(HYDROGEN_FOLDER, file)
    
    try:
        df = pd.read_csv(path)
        
        # Szükséges oszlopok
        if "frequency_hz" in df.columns and "power_db" in df.columns:
            df = df[["frequency_hz", "power_db"]].copy()
            all_data.append(df)
            print(f"  ✅ {file} - {len(df)} pont")
            processed_count += 1
        else:
            print(f"  ⚠️  {file} - hiányzó oszlopok")
            logging.warning(f"Missing columns in {file}")
    except Exception as e:
        print(f"  ❌ {file} - {e}")
        logging.error(f"Error reading {file}: {e}")

if not all_data:
    print("❌ Nincs feldolgozható adat!")
    logging.error("No data to process")
    exit(1)

# Összefűzés
combined = pd.concat(all_data, ignore_index=True)
print(f"\n📈 Összesen feldolgozva: {len(combined)} pont\n")

# Baseline kalkulálás: frekvenciánként percentilis
print(f"🔧 Baseline számítása ({PERCENTILE}. percentilis)...\n")

baseline = combined.groupby("frequency_hz", as_index=False).agg({
    'power_db': [
        ('min', 'min'),
        ('p05', lambda x: np.percentile(x, 5)),
        ('p10', lambda x: np.percentile(x, PERCENTILE)),
        ('median', 'median'),
        ('mean', 'mean'),
        ('max', 'max'),
        ('count', 'count')
    ]
}).reset_index(drop=True)

# Oszlopnevek
baseline.columns = ['frequency_hz', 'min_db', 'p05_db', f'p{PERCENTILE}_db', 
                    'median_db', 'mean_db', 'max_db', 'measurement_count']

# Baseline érték: p10_db
baseline.insert(2, 'baseline_db', baseline[f'p{PERCENTILE}_db'])

print(f"✅ {len(baseline)} frekvencia bin\n")
print(f"Baseline statisztika:")
print(f"  Min: {baseline['baseline_db'].min():.2f} dB")
print(f"  Mean: {baseline['baseline_db'].mean():.2f} dB")
print(f"  Max: {baseline['baseline_db'].max():.2f} dB\n")

# Mentés
baseline.to_csv(BASELINE_FILE, index=False)
print(f"✅ Mentve: {BASELINE_FILE}\n")
logging.info(f"Baseline saved: {len(baseline)} bins from {processed_count} files")

print("="*70)
print("✅ BASELINE ELKÉSZÜLT!")
print("="*70)
logging.info("=== baseline_calc.py end ===\n")
