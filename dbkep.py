#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging

# ================= CONFIG =================
INPUT_FOLDER = r"C:\seti\dataavg"
BASELINE_FILE = r"C:\seti\hydrogen\baseline.csv"
OUTPUT_FOLDER = r"C:\seti\kep"
LOG_FILE = os.path.join(OUTPUT_FOLDER, "dbkep.log")

# Plot beállítások
FIGSIZE = (14, 8)
DPI = 300
H_LINE_FREQ = 1420.405751768e6  # Hidrogénvonal Hz-ben

# ==========================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🎨 dbkep.py - Spektrum rajzolás (simított + baseline korrigált)\n")
logging.info("=== dbkep.py start ===")

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

# CSV fájlok keresése (dataavg/ mappából)
csv_files = sorted([f for f in os.listdir(INPUT_FOLDER) 
                   if f.startswith("avg_") and f.endswith(".csv")])

if not csv_files:
    print("❌ Nincs avg_*.csv fájl!")
    logging.error("No avg CSV files found")
    exit(1)

print(f"Talált: {len(csv_files)} fájl\n")

# Feldolgozás
processed_count = 0
error_count = 0

for file in csv_files:
    input_path = os.path.join(INPUT_FOLDER, file)
    
    try:
        # Beolvasás
        df = pd.read_csv(input_path)
        
        # Szükséges oszlopok
        if "frequency_hz" not in df.columns or "power_db_smoothed" not in df.columns:
            print(f"  ⚠️  {file} - hiányzó oszlopok")
            logging.warning(f"Missing columns in {file}")
            continue
        
        # Koordináta név kinyerése
        coord_name = file.replace("avg_", "").replace(".csv", "")
        
        # =============== BASELINE LEVONÁS ===============
        # Merge baseline (frequency_hz alapján)
        df_merged = pd.merge(
            df,
            baseline[["frequency_hz", "baseline_db"]],
            on="frequency_hz",
            how="left"
        )
        
        # Baseline levonás
        df_merged["power_db_corrected"] = df_merged["power_db_smoothed"] - df_merged["baseline_db"]
        
        # =============== PLOT ===============
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=FIGSIZE, dpi=DPI)
        
        # X tengely: Frekvencia (MHz-ben)
        freq_mhz = df_merged["frequency_hz"].values / 1e6
        power_db_smoothed = df_merged["power_db_smoothed"].values
        power_db_corrected = df_merged["power_db_corrected"].values
        
        # ========== PLOT 1: Simított (eredeti) ==========
        ax1.plot(freq_mhz, power_db_smoothed, color='blue', linewidth=1.5, 
                label='Simított spektrum')
        ax1.axvline(H_LINE_FREQ / 1e6, color='red', linestyle='--', linewidth=2, 
                   label=f'H-vonal ({H_LINE_FREQ/1e6:.2f} MHz)', alpha=0.7)
        
        # Baseline rajzolása
        baseline_plot = pd.merge(
            df_merged[["frequency_hz"]],
            baseline[["frequency_hz", "baseline_db"]],
            on="frequency_hz",
            how="left"
        )
        ax1.plot(baseline_plot["frequency_hz"].values / 1e6, 
                baseline_plot["baseline_db"].values, 
                color='green', linewidth=1.5, linestyle=':', label='Baseline (zajszint)')
        
        # Statisztika 1
        max_power_1 = power_db_smoothed.max()
        max_freq_1 = freq_mhz[power_db_smoothed.argmax()]
        mean_power_1 = power_db_smoothed.mean()
        
        ax1.set_title(f'{coord_name} - Simított\nMax: {max_power_1:.2f} dB @ {max_freq_1:.2f} MHz | Mean: {mean_power_1:.2f} dB',
                    fontsize=12, fontweight='bold')
        ax1.set_ylabel('Teljesítmény (dB)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=10)
        
        # ========== PLOT 2: Baseline-korrigált ==========
        ax2.plot(freq_mhz, power_db_corrected, color='darkblue', linewidth=1.5, 
                label='Baseline-korrigált')
        ax2.axvline(H_LINE_FREQ / 1e6, color='red', linestyle='--', linewidth=2, 
                   label=f'H-vonal ({H_LINE_FREQ/1e6:.2f} MHz)', alpha=0.7)
        ax2.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
        
        # Statisztika 2
        max_power_2 = power_db_corrected.max()
        max_freq_2 = freq_mhz[power_db_corrected.argmax()]
        mean_power_2 = power_db_corrected.mean()
        
        ax2.set_title(f'{coord_name} - Baseline-korrigált\nMax: {max_power_2:.2f} dB @ {max_freq_2:.2f} MHz | Mean: {mean_power_2:.2f} dB',
                    fontsize=12, fontweight='bold')
        ax2.set_xlabel('Frekvencia (MHz)', fontsize=11)
        ax2.set_ylabel('Teljesítmény (dB)', fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best', fontsize=10)
        
        # Layout
        plt.tight_layout()
        
        # Mentés
        output_file = f"{coord_name}_baseline_corrected.png"
        output_path = os.path.join(OUTPUT_FOLDER, output_file)
        plt.savefig(output_path, dpi=DPI)
        plt.close()
        
        print(f"  ✅ {coord_name}")
        print(f"      → {output_file}")
        print(f"      Simított:        Max: {max_power_1:.2f} dB")
        print(f"      Korrigált:       Max: {max_power_2:.2f} dB")
        
        processed_count += 1
        logging.info(f"Plotted: {coord_name} - Original Max: {max_power_1:.2f} dB, Corrected Max: {max_power_2:.2f} dB")
        
    except Exception as e:
        print(f"  ❌ {file} - Hiba: {e}")
        logging.error(f"Error processing {file}: {e}")
        error_count += 1

print("\n" + "="*70)
print("✅ RAJZOLÁS KÉSZ (2 subplot / kép)")
print("="*70)
print(f"Feldolgozva: {processed_count}")
print(f"Hiba: {error_count}")
print(f"Output mappa: {OUTPUT_FOLDER}")
logging.info(f"=== dbkep.py end === Processed: {processed_count}, Errors: {error_count}\n")
