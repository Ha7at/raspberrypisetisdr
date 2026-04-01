import os
import pandas as pd
import numpy as np
from datetime import datetime

# --- Könyvtár ---
DATA_DIR = r"C:\seti\hydrogen"

# Fájlok listázása (csak dátum formátumúak: YYYYMMDD_HHMM.csv)
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
print(f"Fájlok száma: {len(files)}")

# Jel keresés
signal_detections = []

for fname in files:
    path = os.path.join(DATA_DIR, fname)

    # idő a fájlnévből (YYYYMMDD_HHMM)
    try:
        t = datetime.strptime(fname.replace(".csv", ""), "%Y%m%d_%H%M")
    except ValueError:
        print(f"Skipping file with unexpected format: {fname}")
        continue

    df = pd.read_csv(path)

    # RFI szűrés: csak azokat az értékeket vesszük, amelyek nem típikus RFI zajok
    # RFI: folyamatos, erős interferencia - azt keressük, ami ebből kilóg
    
    power = df["power_db"].values
    frequency = df["frequency_hz"].values
    
    # Statisztika számítása
    median_power = np.median(power)
    std_power = np.std(power)
    
    # Küszöb: medián + 5*szórás (anomáliák keresése)
    threshold = median_power + 0.8 * std_power
    
    # Jeleket keressünk
    signal_indices = np.where(power > threshold)[0]
    
    if len(signal_indices) > 0:
        for idx in signal_indices:
            signal_detections.append({
                'time': t,
                'filename': fname,
                'frequency_hz': frequency[idx],
                'power_db': power[idx],
                'above_threshold': power[idx] - median_power
            })

# Eredmények kiírása
if signal_detections:
    print(f"\n{'='*80}")
    print(f"Talált jelek: {len(signal_detections)}")
    print(f"{'='*80}\n")
    
    detection_df = pd.DataFrame(signal_detections)
    detection_df = detection_df.sort_values('power_db', ascending=False)
    
    for idx, row in detection_df.head(20).iterrows():  # Top 20 jel
        print(f"Idő: {row['time']}")
        print(f"Fájl: {row['filename']}")
        print(f"Frekvencia: {row['frequency_hz']:.0f} Hz ({row['frequency_hz']/1e6:.2f} MHz)")
        print(f"Teljesítmény: {row['power_db']:.2f} dB")
        print(f"Anomália szint: {row['above_threshold']:.2f} dB")
        print("-" * 80)
    
    # CSV-be exportálás
    detection_df.to_csv(r"C:\seti\signal_detections.csv", index=False)
    print(f"\nEredmények mentve: C:\\seti\\signal_detections.csv")
else:
    print("Nem találtam anomáliákat!")