import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

import matplotlib
matplotlib.use("TkAgg")

# ================== BEÁLLÍTÁSOK ==================
mappa_utvonal = r"C:\seti\mapdata_radec"   
baseline_utvonal = r"C:\seti\baseline.csv"  
melyik_oszlop = "power_db_smoothed"        
COORD_STEP = 5  
# =================================================

if not os.path.exists(mappa_utvonal) or not os.path.exists(baseline_utvonal):
    print("❌ HIBA: Ellenőrizd az elérési utakat!")
    exit(1)

base_df = pd.read_csv(baseline_utvonal, sep=",")
base_df.columns = base_df.columns.str.strip()
base_jelszint = base_df[melyik_oszlop].values

irany_adatok = {}

print("📂 Mappaszerkezet beolvasása folyamatos négyzetrácshoz...")

for gyoker, mappak, fajlok in os.walk(mappa_utvonal):
    m_nev = os.path.basename(gyoker)
    match_mappa = re.search(r"ra(\d+)_dec([+-]\d+)", m_nev, re.IGNORECASE)
    
    if match_mappa:
        ra_center = float(match_mappa.group(1))
        dec_center = float(match_mappa.group(2))
        
        db_lista = []
        for fajlnev in fajlok:
            if fajlnev.endswith(".csv") and not fajlnev.startswith("_"):
                try:
                    df = pd.read_csv(os.path.join(gyoker, fajlnev), sep=",")
                    df.columns = df.columns.str.strip()
                    if melyik_oszlop in df.columns:
                        nyers_jel = df[melyik_oszlop].values
                        kalibralt_jel = nyers_jel - base_jelszint
                        frekvenciak_mhz = df["frequency_hz"].values / 1e6
                        hasznos_mask = (frekvenciak_mhz > 1419.6) & (frekvenciak_mhz < 1421.2)
                        db_lista.append(np.max(kalibralt_jel[hasznos_mask]))
                except:
                    pass
        
        if db_lista:
            irany_adatok[(ra_center, dec_center)] = {
                'db': np.mean(db_lista),
                'mappa': m_nev
            }

if not irany_adatok:
    print("❌ HIBA: Nincs beolvasható adat!")
    exit(1)

print(f"✅ Sikeresen feldolgozva: {len(irany_adatok)} égi irány. Folyamatos négyzetrács generálása...")

fig = plt.figure(figsize=(12, 7), facecolor="#0c0d0d")
ax = fig.add_subplot(111, projection="mollweide")
ax.set_facecolor("#111314")

vmin, vmax = 0.0, 1.1
cmap = plt.get_cmap("plasma")

poligon_lista = []
poligon_mappak = []

for (ra_c, dec_c), adat in irany_adatok.items():
    valos_db = adat['db']
    
    ra_adj = ra_c
    if ra_adj > 180.0:
        ra_adj -= 360.0
        
    ra_min, ra_max = ra_adj, ra_adj + COORD_STEP
    dec_min, dec_max = dec_c, dec_c + COORD_STEP
    
    # 🔥 BIZTONSÁGI JAVÍTÁS: Szigorúan behúzzuk a határokat a matematikai élek alá, 
    # hogy az arcsin hiba teljesen eltűnjön a széleken!
    ra_min_s = np.clip(ra_min, -179.99, 179.99)
    ra_max_s = np.clip(ra_max, -179.99, 179.99)
    dec_min_s = np.clip(dec_min, -89.99, 89.99)
    dec_max_s = np.clip(dec_max, -89.99, 89.99)
    
    corners = [
        (np.radians(ra_min_s), np.radians(dec_min_s)),
        (np.radians(ra_max_s), np.radians(dec_min_s)),
        (np.radians(ra_max_s), np.radians(dec_max_s)),
        (np.radians(ra_min_s), np.radians(dec_max_s))
    ]
    
    szin_index = np.clip((valos_db - vmin) / (vmax - vmin), 0, 1)
    arc_szin = cmap(szin_index)
    
    poly = Polygon(corners, facecolor=arc_szin, edgecolor="none", alpha=0.75, zorder=3, picker=True)
    ax.add_patch(poly)
    
    poligon_lista.append(poly)
    poligon_mappak.append((adat['mappa'], valos_db, ra_c))

# Csillagképek
def rajzol_csillagkep(ra_list, dec_list):
    try:
        ra_adj = np.where(ra_list > 180, ra_list - 360, ra_list)
        for i in range(len(ra_adj) - 1):
            if abs(ra_adj[i] - ra_adj[i + 1]) < 150:
                d1 = np.clip(dec_list[i], -89.9, 89.9)
                d2 = np.clip(dec_list[i+1], -89.9, 89.9)
                ax.plot([np.radians(ra_adj[i]), np.radians(ra_adj[i + 1])],
                        [np.radians(d1), np.radians(d2)],
                        color="#ffffff", linewidth=0.5, alpha=0.15, zorder=1)
    except: pass

rajzol_csillagkep(np.array([88.7, 81.3, 78.6, 83.0, 84.1, 85.2, 88.7]), np.array([7.4, 6.3, -8.2, -9.6, -1.9, -0.3, 7.4]))
rajzol_csillagkep(np.array([165.5, 166.4, 178.5, 183.0, 194.4, 202.5, 210.4]), np.array([56.5, 61.7, 53.7, 57.0, 54.9, 49.3, 43.1]))
rajzol_csillagkep(np.array([10.1, 28.6, 15.0, 37.9, 23.4]), np.array([59.1, 63.7, 60.7, 56.5, 59.2]))
rajzol_csillagkep(np.array([310.4, 302.2, 294.0, 306.4, 302.2, 297.7]), np.array([45.3, 40.3, 34.4, 40.2, 40.3, 51.2]))

def jelol_forras(ra_ora, dec_fok, nev):
    rf = ra_ora * 15
    if rf > 180: rf -= 360
    ax.scatter(np.radians(rf), np.radians(dec_fok), color="#ffffff", marker="+", s=100, linewidths=1, zorder=4)
    ax.text(np.radians(rf) + 0.03, np.radians(dec_fok) + 0.03, nev, color="#ffffff", fontsize=8, alpha=0.7, zorder=4)

jelol_forras(19.98, 40.73, "Cygnus A")
jelol_forras(23.39, 58.81, "Cas A")

sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = plt.colorbar(sm, orientation="horizontal", pad=0.08, shrink=0.6, ax=ax)
cbar.set_label("24 Órás Folytonos Rádiótöbblet [dB]", color="#cccccc", fontsize=9)
cbar.ax.tick_params(colors="#cccccc", labelsize=8)

ax.grid(True, color="#444444", linestyle=":")
ax.tick_params(colors="#cccccc", labelsize=9)
plt.title("SETI Rádiómérések - Professzionális Folytonos Pixel-Rács Térkép", color="#ffffff", fontsize=12, pad=15)
plt.tight_layout()

def on_pick(event):
    for i, poly in enumerate(poligon_lista):
        if poly == event.artist:
            m_nev, db_val, ra_c = poligon_mappak[i]
            ra_ora = ra_c / 15.0
            print("\n" + "🧱"*20)
            print(f"🟩 KATTINTOTT PIXEL MAPPA: {m_nev}")
            print(f"📊 Átlagos jelszint:      {db_val:.4f} dB")
            print(f"⏰ Pozíció:               {ra_ora:.2f} óra")
            print("🧱"*20)

fig.canvas.mpl_connect('pick_event', on_pick)

output_map_png = r"C:\seti\kalibralt_csillagterkep.png"
plt.savefig(output_map_png, dpi=300, facecolor='#0c0d0d', edgecolor='none')
print(f"\n🎯 SIKER! A folyamatos pixelrácsos térkép hiba nélkül elmentve ide: {output_map_png}")
plt.show()
