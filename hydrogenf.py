#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd

# ================= CONFIG =================
INPUT_FOLDER = r"C:\seti\usbdata"
OUTPUT_FOLDER = r"C:\seti\hydrogen"

FREQ_MIN = 1419.500e6
FREQ_MAX = 1421.310e6
# ==========================================

print("📡 CSV frekvencia szűrés")
print(f"Tartomány: {FREQ_MIN/1e6:.3f} - {FREQ_MAX/1e6:.3f} MHz\n")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

csv_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".csv")]

if not csv_files:
    print("❌ Nincs CSV fájl!")
    exit(1)

processed = 0

for file in csv_files:
    input_path = os.path.join(INPUT_FOLDER, file)
    output_path = os.path.join(OUTPUT_FOLDER, file)

    try:
        df = pd.read_csv(input_path)

        # ellenőrzés
        if "frequency_hz" not in df.columns:
            print(f"⚠️  {file} - nincs frequency_hz oszlop")
            continue

        # ================= SZŰRÉS =================
        df_filtered = df[
            (df["frequency_hz"] >= FREQ_MIN) &
            (df["frequency_hz"] <= FREQ_MAX)
        ].copy()
        # ==========================================

        if len(df_filtered) == 0:
            print(f"⚠️  {file} - nincs adat a tartományban")
            continue

        # mentés (oszlopnevek változatlanok)
        df_filtered.to_csv(output_path, index=False)

        print(f"✅ {file} → {len(df_filtered)} pont")
        processed += 1

    except Exception as e:
        print(f"❌ {file} - hiba: {e}")

print("\n" + "="*60)
print(f"Kész! Feldolgozott fájlok: {processed}")
print(f"Mentési hely: {OUTPUT_FOLDER}")