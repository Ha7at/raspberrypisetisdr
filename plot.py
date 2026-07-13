import os
import re
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# Kényszerített stabil Windows grafikus motor
import matplotlib
matplotlib.use("TkAgg")

# ================== BEÁLLÍTÁSOK ==================
mappa_utvonal = r"C:\seti\dataavg_radec"   # Az átlagolt irányok mappája
baseline_utvonal = r"C:\seti\baseline.csv"  # A Mester Alapvonal fájl
melyik_oszlop = "power_db_smoothed"        # Az oszlopnév
OUTPUT_KEP_DIR = r"C:\seti\kep"            # Ahová az egyedi képek kerülnek
# =================================================

if not os.path.exists(mappa_utvonal):
    print(f"❌ HIBA: Az adatmappa nem létezik: {mappa_utvonal}")
    exit(1)

if not os.path.exists(baseline_utvonal):
    print(f"❌ HIBA: A Mester Alapvonal fájl nem található! ({baseline_utvonal})")
    exit(1)

# Célmappa létrehozása a képeknek
os.makedirs(OUTPUT_KEP_DIR, exist_ok=True)

# 1. LÉPÉS: A Mester Alapvonal (Baseline) beolvasása
print(f"📡 Mester Alapvonal betöltése: {baseline_utvonal}...")
try:
    ref_df = pd.read_csv(baseline_utvonal, sep=",")
    ref_df.columns = ref_df.columns.str.strip()
    ref_jelszint = ref_df[melyik_oszlop].values
except Exception as e:
    print(f"❌ HIBA: Nem sikerült beolvasni a baseline fájlt: {e}")
    exit(1)

# 2. LÉPÉS: Adatfájlok összegyűjtése
csv_fajlok = []
for gyoker, _, fajlok in os.walk(mappa_utvonal):
    for f in fajlok:
        if f.endswith(".csv") and not f.startswith("_"):
            csv_fajlok.append(os.path.join(gyoker, f))

print(f"Talált fájlok száma: {len(csv_fajlok)}")
print("🖼️ Egyedi spektrumgrafikonok generálása és mentése folyamatban...\n")

mentett_szamlalo = 0

for teljes_ut in csv_fajlok:
    fajlnev = os.path.basename(teljes_ut)
    mappanev = os.path.basename(os.path.dirname(teljes_ut))
    
    ra_fok = None
    dec_fok = None
    
    # Koordináták kinyerése JSON-ből vagy fájlnévből
    json_ut = os.path.join(os.path.dirname(teljes_ut), "_info.json")
    if os.path.exists(json_ut):
        try:
            with open(json_ut, "r") as jf:
                jsdata = json.load(jf)
                ra_fok = jsdata.get("center_ra_deg") or jsdata.get("galactic_l_deg")
                dec_fok = jsdata.get("center_dec_deg") or jsdata.get("galactic_b_deg")
        except:
            pass
            
    if ra_fok is None or dec_fok is None:
        szoveg = fajlnev + "_" + mappanev
        match = re.search(r"ra(\d+)_dec([+-]\d+)", szoveg, re.IGNORECASE)
        if match:
            ra_fok = float(match.group(1))
            dec_fok = float(match.group(2))

    if ra_fok is not None and dec_fok is not None:
        ra_ora = ra_fok / 15.0
        
        # Tisztított tiszta mappanév / fájlnév képmentéshez (Pl: ra285_dec+035)
        tiszta_nev = f"ra{int(ra_fok):03d}_dec{int(dec_fok):+04d}"
        
        try:
            df = pd.read_csv(teljes_ut, sep=",")
            df.columns = df.columns.str.strip()
            
            f_hz = df["frequency_hz"].values
            jelerosseg_db = df[melyik_oszlop].values
            
            # Mester alapvonal levonás
            kalibralt_jel = jelerosseg_db - ref_jelszint
            
            # Radiális sebesség km/s konverzió
            F0_HZ = 1420405751.786  
            C_KMS = 299792.458      
            sebességek_kms = C_KMS * (F0_HZ - f_hz) / F0_HZ
            
            v_mask = (sebességek_kms > -190) & (sebességek_kms < 190)
            x_v = sebességek_kms[v_mask]
            y_v = kalibralt_jel[v_mask]
            
            if len(x_v) > 10:
                # Tudományos simítás
                y_v_smooth = savgol_filter(y_v, window_length=41, polyorder=3)
                # Kért módosítás: 0 dB alatti értékek levágása
                y_v_smooth = np.clip(y_v_smooth, a_min=0.0, a_max=None)
                
                # --- EGYEDI GRAFIKON LÉTREHOZÁSA ---
                fig = plt.figure(figsize=(10, 6), facecolor="#0c0d0d")
                ax = plt.axes()
                ax.set_facecolor("#111314")
                
                # Alapértelmezett színek (Tejút / Háttér égbolt)
                vonal_szin = "#ff9900" # Narancssárga
                cim_kiegeszites = ""
                
                # Cygnus A régió intelligens felismerése és neon-zöld kiemelése
                if 285 <= ra_fok <= 305:
                    vonal_szin = "#00ff66"
                    cim_kiegeszites = " [⭐ CYGNUS A RÁDIÓGALAXIS TARTOMÁNY]"
                
                # Görbe felrajzolása
                plt.plot(x_v, y_v_smooth, color=vonal_szin, linewidth=2.5, label=f"Mért profil: {tiszta_nev}")
                
                # Esztétika és tengelybeállítások (Kért módosítás: 0.0 - 0.7 dB skála nagyítás)
                ax.set_ylim(0.0, 1.2)
                plt.xlim(-190, 190)
                
                plt.axhline(0, color="#777777", linestyle="-", linewidth=0.8)
                plt.axvline(0, color="#ff3333", linestyle=":", linewidth=1.5, label="Nyugvó hidrogén (LSR = 0 km/s)")
                
                plt.xlabel("Radiális Sebesség (Radial Velocity) [km/s]", color="#cccccc", fontsize=11)
                plt.ylabel("Mester Kalibrált Jelerősség [dB]", color="#cccccc", fontsize=11)
                plt.title(f"Rádióspektrum profil: {tiszta_nev}{cim_kiegeszites}\nKoordináta: RA {ra_ora:.2f}h | DEC {dec_fok:+.1f}°", color="#ffffff", fontsize=12, pad=12)
                
                plt.grid(True, color="#343434", linestyle="--", linewidth=0.5)
                ax.tick_params(colors="#cccccc", labelsize=10)
                
                plt.legend(loc="upper right", facecolor="#111314", edgecolor="#343434", labelcolor="#cccccc")
                plt.tight_layout()
                
                # Mentés a koordináta nevével a C:\seti\kep\ mappába
                kimeneti_kep_ut = os.path.join(OUTPUT_KEP_DIR, f"{tiszta_nev}.png")
                plt.savefig(kimeneti_kep_ut, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
                
                # Bezárjuk a memóriából a grafikont, hogy ne fogyassza el a RAM-ot a 29 fájlnál
                plt.close(fig)
                
                print(f"  ✅ Elmentve: {tiszta_nev}.png")
                mentett_szamlalo += 1
        except Exception as e:
            print(f"  ❌ Hiba a(z) {fajlnev} mentésekor: {e}")

print("\n" + "="*60)
print(f"🎉 KÉSZ! Összesen {mentett_szamlalo} egyedi spektrumkép lett legenerálva.")
print(f"📂 Keresd a képeket ebben a mappában: {OUTPUT_KEP_DIR}")
print("="*60)
