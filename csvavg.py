#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np

# ================= CONFIG =================
DATA_FOLDER = r"C:\pi_sdr\seti\data"
OUTPUT_FILE = r"C:\pi_sdr\seti\dataavg\average_spectrum.csv"
# ==========================================

csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]

if not csv_files:
    print("Nincs CSV fájl a mappában!")
    exit()

print(f"{len(csv_files)} fájl feldolgozása...")

df_list = []

for file in csv_files:
    path = os.path.join(DATA_FOLDER, file)
    try:
        df = pd.read_csv(path)

        # Biztonság: csak a szükséges oszlopok
        df = df[["frequency_hz", "power_db"]]

        df_list.append(df)

    except Exception as e:
        print(f"Hiba {file}: {e}")

# Összefűzés
all_data = pd.concat(df_list)

# ================= ÁTLAGOLÁS =================
avg_data = all_data.groupby("frequency_hz", as_index=False).mean()

# Időbélyeg hozzáadása (egy közös)
avg_data.insert(0, "timestamp_utc", pd.Timestamp.utcnow().isoformat())

# ============================================

# Mentés
avg_data.to_csv(OUTPUT_FILE, index=False)

print(f"Kész! Mentve ide: {OUTPUT_FILE}")