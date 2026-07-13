import os
import re
import pandas as pd
import numpy as np

# ================== BEÁLLÍTÁSOK ==================
SOURCE_FOLDER = r"C:\seti\hydrogen"          
BASELINE_FILE = r"C:\seti\baseline.csv"      
BEST_PERCENT = 10                            # Szűkítjük 10%-ra a legbiztonságosabb hideg pontokért
# =================================================

if not os.path.exists(SOURCE_FOLDER):
    print(f"❌ HIBA: A forrás mappa nem létezik: {SOURCE_FOLDER}")
    exit(1)

fajlok = sorted([f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".csv")])
print(f"Talált nyers fájlok száma a forrásban: {len(fajlok)}")

fajl_energia_lista = []

print("🔍 Intelligens fájlelemzés (Cygnus és RFI szűréssel)...")
for fajlnev in fajlok:
    # BIZTONSÁGI SZŰRŐ: Ha a fájl nevében benne van, hogy a Cygnus zónájában készült 
    # (időben vagy koordinátában), azt kíméletlenül kihagyjuk a háttérzaj-alapból!
    if "20260707_20" in fajlnev or "20260707_19" in fajlnev or "20260708_11" in fajlnev or "20260708_12" in fajlnev:
        continue
        
    teljes_ut = os.path.join(SOURCE_FOLDER, fajlnev)
    try:
        df = pd.read_csv(teljes_ut, sep=",")
        df.columns = df.columns.str.strip()
        
        if "frequency_hz" in df.columns and "power_db_smoothed" in df.columns:
            linear_power = 10 ** (df["power_db_smoothed"].values / 10.0)
            atlag_energia = np.mean(linear_power)
            
            fajl_energia_lista.append({
                "utvonal": teljes_ut,
                "energia": atlag_energia
            })
    except:
        pass

fajl_energia_lista = sorted(fajl_energia_lista, key=lambda x: x["energia"])
darabszam = max(1, int(len(fajl_energia_lista) * (BEST_PERCENT / 100.0)))
kiválasztott_fajlok = fajl_energia_lista[:darabszam]

print(f"🎯 Siker! Kiválasztva a legcsendesebb, tiszta éjszakai {darabszam} db háttérfájl.")

Mester_frekvenciak = None
Mester_teljesitmeny_linear = None

for t in kiválasztott_fajlok:
    df = pd.read_csv(t["utvonal"], sep=",")
    df.columns = df.columns.str.strip()
    freqs = df["frequency_hz"].values
    p_db = df["power_db_smoothed"].values
    p_lin = 10 ** (p_db / 10.0)
    
    if Mester_frekvenciak is None:
        Mester_frekvenciak = freqs
        Mester_teljesitmeny_linear = p_lin
    else:
        Mester_teljesitmeny_linear += p_lin

Mester_teljesitmeny_linear /= len(kiválasztott_fajlok)
Mester_power_db = 10 * np.log10(Mester_teljesitmeny_linear)

baseline_df = pd.DataFrame({
    "frequency_hz": Mester_frekvenciak.astype(int),
    "power_db_smoothed": np.round(Mester_power_db, 3)
})
baseline_df.to_csv(BASELINE_FILE, index=False, sep=",")
print(f"✅ Új, megtisztított Mester Alapvonal elmentve: {BASELINE_FILE}")
