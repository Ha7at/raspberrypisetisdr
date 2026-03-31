#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd

# ================= CONFIG =================
DATA_FOLDER = r"C:\pi_sdr\seti\dataavg"
OUTPUT_FOLDER = r"C:\pi_sdr\seti\datak"
BASELINE_FILE = r"C:\pi_sdr\seti\dataavg\0.csv"
# ==========================================

# Kimeneti mappa létrehozása
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Baseline betöltése
baseline = pd.read_csv(BASELINE_FILE)
baseline = baseline[["frequency_hz", "power_db"]]
baseline = baseline.rename(columns={"power_db": "baseline_db"})

print("Baseline betöltve")

# CSV fájlok listája
csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

for file in csv_files:
    if file == "0.csv":
        continue  # baseline-t nem dolgozzuk fel

    path = os.path.join(DATA_FOLDER, file)

    try:
        df = pd.read_csv(path)

        # Ellenőrzés
        df = df[["timestamp_utc", "frequency_hz", "power_db"]]

        # Összepárosítás frekvencia alapján
        merged = pd.merge(df, baseline, on="frequency_hz", how="inner")

        # Kivonás
        merged["power_db"] = merged["power_db"] - merged["baseline_db"]

        # Csak a szükséges oszlopok
        result = merged[["timestamp_utc", "frequency_hz", "power_db"]]

        # Mentés
        out_path = os.path.join(OUTPUT_FOLDER, file)
        result.to_csv(out_path, index=False)

        print(f"Kész: {file}")

    except Exception as e:
        print(f"Hiba {file}: {e}")

print("Összes fájl feldolgozva.")