import os
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# Kényszerített univerzális grafikus megjelenítő Windows alá
import matplotlib
matplotlib.use("TkAgg")

# ================== BEÁLLÍTÁSOK ==================
DIA_MAPPA = r"C:\seti\dia"                  # Ide kell másolnod a vizsgálandó fájlokat
baseline_utvonal = r"C:\seti\baseline.csv"  # A Mester Alapvonal fájl
melyik_oszlop = "power_db_smoothed"        # Az oszlopnév
# =================================================

if not os.path.exists(DIA_MAPPA):
    os.makedirs(DIA_MAPPA)
    print(f"🟩 Létrehoztam a hiányzó mappát: {DIA_MAPPA}")
    print("👉 Kérlek, másolj bele pár összehasonlítandó CSV fájlt, majd indítsd el újra a programot!")
    exit(0)

if not os.path.exists(baseline_utvonal):
    print(f"❌ HIBA: A Mester Alapvonal nem található itt: {baseline_utvonal}")
    exit(1)

# 1. Baseline betöltése
print(f"📡 Mester Alapvonal betöltése...")
base_df = pd.read_csv(baseline_utvonal, sep=",")
base_df.columns = base_df.columns.str.strip()
base_jelszint = base_df[melyik_oszlop].values

# 2. A dia mappában lévő CSV fájlok összegyűjtése
csv_fajlok = sorted([f for f in os.listdir(DIA_MAPPA) if f.endswith(".csv")])

if not csv_fajlok:
    print(f"⚠️ A {DIA_MAPPA} mappa üres! Másolj bele fájlokat az összehasonlításhoz.")
    exit(0)

print(f"📊 Összehasonlító grafikon készítése {len(csv_fajlok)} db fájlból...")

# Grafikon felépítése
fig = plt.figure(figsize=(11, 6.5), facecolor="#0c0d0d")
ax = plt.axes()
ax.set_facecolor("#111314")

# Professzionális csillagászati színpaletta az egyedi görbékhez
szin_paletta = ["#00ff66", "#00e5ff", "#ff9900", "#ff0055", "#cc00ff", "#ffff00", "#ffffff"]

F0_HZ = 1420405751.786  
C_KMS = 299792.458      

# 3. Fájlok beolvasása és rárajzolása egyetlen képre
for idx, f_nev in enumerate(csv_fajlok):
    try:
        teljes_ut = os.path.join(DIA_MAPPA, f_nev)
        df = pd.read_csv(teljes_ut, sep=",")
        df.columns = df.columns.str.strip()
        
        frekvenciak_hz = df["frequency_hz"].values
        nyers_jel = df[melyik_oszlop].values
        kalibralt_jel = nyers_jel - base_jelszint
        
        # Átváltás km/s sebességre
        sebességek_kms = C_KMS * (F0_HZ - frekvenciak_hz) / F0_HZ
        v_mask = (sebességek_kms > -190) & (sebességek_kms < 190)
        
        x_v = sebességek_kms[v_mask]
        y_v = kalibralt_jel[v_mask]
        
        sort_idx = np.argsort(x_v)
        x_v = x_v[sort_idx]
        y_v_smooth = savgol_filter(y_v[sort_idx], window_length=41, polyorder=3)
        y_v_smooth = np.clip(y_v_smooth, a_min=0.0, a_max=None)
        
        # 🔥 INTELLIGENS CÍMKE: Megpróbáljuk kivenni a koordinátát a fájlnévből vagy az időbélyegből
        match_radec = re.search(r"ra\d+_dec[+-]\d+", f_nev, re.IGNORECASE)
        if match_radec:
            label_nev = match_radec.group(0).upper()
        else:
            # Ha sima időbélyeges a fájl, ráírjuk a nevét és az UTC órát
            match_ora = re.search(r"_(\d{4})", f_nev)
            ora_str = f" ({match_ora.group(1)[:2]}:{match_ora.group(1)[2:]} UTC)" if match_ora else ""
            label_nev = f_nev.replace(".csv", "") + ora_str
            
        # Szín kiválasztása (ha több fájl van mint szín, körbeugrik a palettán)
        görbe_szin = szin_paletta[idx % len(szin_paletta)]
        
        # Görbe felrajzolása
        plt.plot(x_v, y_v_smooth, color=görbe_szin, linewidth=2.0, alpha=0.85, label=f"🛰️ {label_nev}")
        print(f"  ✅ Sikeresen rárajzolva: {label_nev}")
    except Exception as e:
        print(f"  ❌ Hiba a(z) {f_nev} fájl feldolgozásakor: {e}")

# Fix csillagászati ablak a részletek kibontásához (1.2 dB felső határ)
ax.set_ylim(0.0, 1.2)
plt.xlim(-190, 190)

plt.axhline(0, color="#777777", linestyle="-", linewidth=0.8)
plt.axvline(0, color="#ff3333", linestyle=":", linewidth=1.5, label="Nyugvó hidrogén (0 km/s)")

plt.xlabel("Radiális Sebesség (Radial Velocity) [km/s]", color="#cccccc", fontsize=11)
plt.ylabel("Mester Kalibrált Jelerősség [dB]", color="#cccccc", fontsize=11)
plt.title("Erdőkertes SETI Obszervatórium – Spektrumvonal Összehasonlító Diagram", color="#ffffff", fontsize=13, pad=15)

plt.grid(True, color="#343434", linestyle="--", linewidth=0.5)
ax.tick_params(colors="#cccccc", labelsize=10)

# A jelmagyarázat elhelyezése jól láthatóan a jobb felső sarokban
plt.legend(loc="upper right", facecolor="#111314", edgecolor="#444444", labelcolor="#cccccc", fontsize=10, framealpha=0.9)
plt.tight_layout()

output_png = r"C:\seti\dia\osszehasonlito_grafikon.png"
plt.savefig(output_png, dpi=200, facecolor='#0c0d0d', edgecolor='none')
print(f"\n🎯 KÉSZ! Az összehasonlító grafikon elmentve ide: {output_png}")
plt.show()
