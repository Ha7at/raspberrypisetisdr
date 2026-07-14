import os
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.signal import savgol_filter

# Kényszerített stabil Windows grafikus motor háttérben mentéshez
import matplotlib
matplotlib.use("Agg")  

# ================== BEÁLLÍTÁSOK ==================
ALAP_MAPPA = r"C:\seti\mapdata_radec"       
BASELINE_UTVONAL = r"C:\seti\baseline.csv"  
KIMENETI_MAPPA = r"C:\seti\mappa_spektrumok" 
MELYIK_OSZLOP = "power_db_smoothed"        
MAX_GORBE_PER_MAPPA = 100                    
# =================================================

if not os.path.exists(ALAP_MAPPA) or not os.path.exists(BASELINE_UTVONAL):
    print("❌ HIBA: Ellenőrizd az elérési utakat!")
    exit(1)

if not os.path.exists(KIMENETI_MAPPA):
    os.makedirs(KIMENETI_MAPPA)

# 1. Baseline betöltése
print(f"📡 Mester Alapvonal betöltése: {BASELINE_UTVONAL}...")
base_df = pd.read_csv(BASELINE_UTVONAL, sep=",")
base_df.columns = base_df.columns.str.strip()
base_jelszint = base_df[MELYIK_OSZLOP].values

F0_HZ = 1420405751.786  
C_KMS = 299792.458      
cmap = plt.get_cmap("jet") # Sötétkék -> Zöld -> Sárga -> Piros

print("\n🔍 Idő-színkulcsos egyedi grafikonok gyártása...")
talalt_mappak = sorted([d for d in os.listdir(ALAP_MAPPA) if os.path.isdir(os.path.join(ALAP_MAPPA, d)) and "ra" in d])

for m_nev in talalt_mappak:
    teljes_mappa_ut = os.path.join(ALAP_MAPPA, m_nev)
    
    csv_fajlok = []
    for f in os.listdir(teljes_mappa_ut):
        if f.endswith(".csv") and not f.startswith("_"):
            match_ido = re.search(r"_(\d{4})", f)
            if match_ido:
                csv_fajlok.append((int(match_ido.group(1)), f))
                
    if not csv_fajlok:
        continue
        
    csv_fajlok = sorted(csv_fajlok, key=lambda x: x[0])
    fajl_darab = len(csv_fajlok)
    
    if fajl_darab > MAX_GORBE_PER_MAPPA:
        indices = np.linspace(0, fajl_darab - 1, MAX_GORBE_PER_MAPPA, dtype=int)
        kivalasztott_fajlok = [csv_fajlok[i] for i in indices]
    else:
        kivalasztott_fajlok = csv_fajlok

    print(f"📊 {m_nev} -> {len(kivalasztott_fajlok)} időszelet kirajzolása...")
    
    fig = plt.figure(figsize=(12, 6.5), facecolor="#0c0d0d")
    ax = plt.axes()
    ax.set_facecolor("#111314")
    
    darab = len(kivalasztott_fajlok)
    
    for idx, (idokod, f_nev) in enumerate(kivalasztott_fajlok):
        try:
            df = pd.read_csv(os.path.join(teljes_mappa_ut, f_nev), sep=",")
            df.columns = df.columns.str.strip()
            
            frekvenciak_hz = df["frequency_hz"].values
            nyers_jel = df[MELYIK_OSZLOP].values
            kalibralt_jel = nyers_jel - base_jelszint
            
            sebességek_kms = C_KMS * (F0_HZ - frekvenciak_hz) / F0_HZ
            v_mask = (sebességek_kms > -190) & (sebességek_kms < 190)
            
            x_v = sebességek_kms[v_mask]
            y_v = kalibralt_jel[v_mask]
            
            sort_idx = np.argsort(x_v)
            x_v = x_v[sort_idx]
            y_v = y_v[sort_idx]
            
            y_v_smooth = savgol_filter(y_v, window_length=41, polyorder=3)
            y_v_smooth = np.clip(y_v_smooth, a_min=0.0, a_max=None)
            
            szin = cmap(idx / (darab - 1)) if darab > 1 else cmap(0.5)
            ora_str = f"{f_nev[-8:-6]}:{f_nev[-6:-4]}" if len(f_nev) >= 13 else f_nev
            
            # 🔥 INTELLIGENS SZÍNKULCS: Feliratozzuk az elsőt, az utolsót és a köztes mérföldköveket is!
            lbl = None
            if darab <= 5:
                lbl = f"{ora_str} UTC"
            else:
                # Elosztjuk a feliratokat egyenletesen, hogy max 5 darab idősáv jelenjen meg a jelmagyarázatban
                if idx == 0:
                    lbl = f"🔵 Kezdet: {ora_str} UTC"
                elif idx == int(darab * 0.25):
                    lbl = f"🟢 Negyed: {ora_str} UTC"
                elif idx == int(darab * 0.5):
                    lbl = f"🟡 Közép: {ora_str} UTC"
                elif idx == int(darab * 0.75):
                    lbl = f"🟠 Háromnegyed: {ora_str} UTC"
                elif idx == darab - 1:
                    lbl = f"🔴 Vége: {ora_str} UTC"
            
            plt.plot(x_v, y_v_smooth, color=szin, linewidth=1.2, alpha=0.4, label=lbl)
        except:
            pass
            
    ax.set_ylim(0.0, 2.2)
    plt.xlim(-190, 190)
    
    plt.axhline(0, color="#777777", linestyle="-", linewidth=0.8)
    plt.axvline(0, color="#ff3333", linestyle=":", linewidth=1.2)
    
    plt.xlabel("Radiális Sebesség [km/s]", color="#cccccc", fontsize=10)
    plt.ylabel("Mester Kalibrált Jelerősség [dB]", color="#cccccc", fontsize=10)
    plt.title(f"Időben Rétegelt Spektrumvonalak – Koordináta: {m_nev}", color="#ffffff", fontsize=11, pad=12)
    
    plt.grid(True, color="#343434", linestyle="--", linewidth=0.5)
    ax.tick_params(colors="#cccccc", labelsize=9)
    
    # 🔥 JAVÍTÁS: A jelmagyarázatot áttesszük a jobb felső sarokba, tiszta háttérrel és jól olvasható betűkkel
    plt.legend(loc="upper right", facecolor="#111314", edgecolor="#444444", labelcolor="#cccccc", fontsize=9.5, framealpha=0.9)
    plt.tight_layout()
    
    fajl_kimenet = os.path.join(KIMENETI_MAPPA, f"spektrum_{m_nev}.png")
    plt.savefig(fajl_kimenet, dpi=200, facecolor='#0c0d0d', edgecolor='none')
    plt.close()

print(f"\n🎯 KÉSZ! Az összes egyedi idő-színkulcsos spektrumkép elmentve ide: {KIMENETI_MAPPA}")
