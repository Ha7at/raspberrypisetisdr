import os
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

# Hivatalos csillagászati koordináta könyvtárak az Astropy-ból
from astropy.coordinates import SkyCoord
import astropy.units as u

import matplotlib
matplotlib.use("TkAgg")

# ================== BEÁLLÍTÁSOK ==================
mappa_utvonal = r"C:\seti\dataavg_radec"   
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

print("📂 CSV fájlok beolvasása és koordináták elemzése...")

for fajlnev in os.listdir(mappa_utvonal):
    if fajlnev.endswith(".csv") and not fajlnev.startswith("_"):
        match_fajl = re.search(r"ra(\d+)_dec([+-]\d+)", fajlnev, re.IGNORECASE)
        
        if match_fajl:
            ra_center = float(match_fajl.group(1))
            dec_center = float(match_fajl.group(2))
            
            try:
                df = pd.read_csv(os.path.join(mappa_utvonal, fajlnev), sep=",")
                df.columns = df.columns.str.strip()
                
                if melyik_oszlop in df.columns:
                    nyers_jel = df[melyik_oszlop].values
                    kalibralt_jel = nyers_jel - base_jelszint
                    frekvenciak_mhz = df["frequency_hz"].values / 1e6
                    hasznos_mask = (frekvenciak_mhz > 1419.6) & (frekvenciak_mhz < 1421.2)
                    
                    max_jel = np.max(kalibralt_jel[hasznos_mask])
                    
                    irany_adatok[(ra_center, dec_center)] = {
                        'db': max_jel,
                        'mappa': fajlnev  
                    }
            except:
                pass

if not irany_adatok:
    print("❌ HIBA: Nincs beolvasható adat a megadott koordináta-mintával!")
    exit(1)

print(f"✅ Sikeresen feldolgozva: {len(irany_adatok)} égi irány. Térkép generálása...")

# Az ablak magasságát 7-ről 5.5-re vettem, hogy az északi félgömb levágás után ne legyen túl nyújtott
fig, ax = plt.subplots(figsize=(12, 5.5), facecolor="#0c0d0d")
ax.set_facecolor("#111314")

vmin, vmax = 0.0, 1.1
cmap = plt.get_cmap("plasma")

poligon_lista = []
poligon_mappak = []

# UNIVERZÁLIS, LINEÁRIS TRANSZFORMÁCIÓ: Minden elem ezt használja
def ToMapCoords(ra_deg):
    ra_norm = ra_deg % 360
    if ra_norm > 180:
        return 360 - ra_norm   # Bal oldali pozitív szakasz (12h -> 24h)
    return -ra_norm            # Jobb oldali negatív szakasz (0h -> 12h)

for (ra_c, dec_c), adat in irany_adatok.items():
    valos_db = adat['db']
    
    x_start = ToMapCoords(ra_c)
    width = -COORD_STEP
    y_start = dec_c
    
    # Biztonsági szűrő a 12h-s égi szakadáshoz a térkép szélén
    if abs(ToMapCoords(ra_c) - ToMapCoords(ra_c + COORD_STEP)) > 100:
        continue
        
    szin_index = np.clip((valos_db - vmin) / (vmax - vmin), 0, 1)
    arc_szin = cmap(szin_index)
    
    rect = Rectangle((x_start, y_start), width, COORD_STEP, 
                     facecolor=arc_szin, edgecolor="none", alpha=0.85, zorder=3, picker=True)
    ax.add_patch(rect)
    
    poligon_lista.append(rect)
    poligon_mappak.append((adat['mappa'], valos_db, ra_c))


# =========================================================================
# ✨ TEJÚT FŐSÍK VONALA (ASTROPY MOTORRAL - TŰPONTOS)
# =========================================================================
def rajzol_tejut_vonal():
    l_points = np.linspace(0, 360, 1000) * u.deg
    b_points = np.zeros(1000) * u.deg
    
    gal_coords = SkyCoord(l=l_points, b=b_points, frame='galactic')
    eq_coords = gal_coords.transform_to('icrs')
    
    ra_deg_list = eq_coords.ra.deg
    dec_deg_list = eq_coords.dec.deg
    
    x_points = np.array([ToMapCoords(ra) for ra in ra_deg_list])
    y_points = np.array(dec_deg_list)
    
    for i in range(len(x_points) - 1):
        if abs(x_points[i] - x_points[i+1]) < 100:
            ax.plot([x_points[i], x_points[i+1]], [y_points[i], y_points[i+1]], 
                    color="#aaaaaa", linewidth=1.2, linestyle="--", alpha=0.6, zorder=2)

rajzol_tejut_vonal()


# =========================================================================
# 📍 FORRÁSOK MEGJELÖLÉSE
# =========================================================================
def jelol_forras(ra_ora, dec_fok, nev):
    x = ToMapCoords(ra_ora * 15.0)
    ax.scatter(x, dec_fok, color="#ffffff", marker="+", s=120, linewidths=1.2, zorder=4)
    ax.text(x + 2.0, dec_fok + 2.0, nev, color="#ffffff", fontsize=8, alpha=0.8, zorder=4)

jelol_forras(19.98, 40.73, "Cygnus A")
jelol_forras(23.39, 58.81, "Cas A")


# =========================================================================
# 🛠️ TENGELYFELIRATOK - KIZÁRÓLAG AZ ÉSZAKI ÉGBOLT (DEC 0° - 90°)
# =========================================================================
ax.grid(True, color="#333333", linestyle=":", linewidth=0.5)

map_ticks = np.array([150, 120, 90, 60, 30, 0, -30, -60, -90, -120, -150])

x_feliratok = []
for val in map_ticks:
    if val >= 0:
        valos_fok = 360 - val  # Bal oldal (12h -> 24h)
    else:
        valos_fok = -val       # Jobb oldal (0h -> 12h)
        
    ora = valos_fok / 15.0
    x_feliratok.append(f"{ora:.1f}h\n({int(valos_fok)}°)")

ax.set_xticks(map_ticks)
ax.set_xticklabels(x_feliratok, color="#cccccc", fontsize=8)

# 🔥 MÓDOSÍTVA: Csugyan a 0° és +90° közötti osztásokat jelenítjük meg
ax.set_yticks(np.arange(0, 91, 15))
ax.tick_params(axis='y', colors="#cccccc", labelsize=9)

# 🔥 MÓDOSÍTVA: A függőleges nézetet 0 és 90 fok közé zártuk be
ax.set_xlim(180, -180)
ax.set_ylim(0, 90)

ax.set_xlabel("Rektaszcenzió (RA óra / fok) — [Középen: UTC 0h/24h]", color="#cccccc", fontsize=9, labelpad=10)
ax.set_ylabel("Deklináció (DEC fok)", color="#cccccc", fontsize=9, labelpad=10)


# =========================================================================
# 🎨 SZÍNSKÁLA ÉS CÍM
# =========================================================================
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = plt.colorbar(sm, orientation="horizontal", pad=0.18, shrink=0.6, ax=ax)
cbar.set_label("24 Órás Folytonos Rádiótöbblet [dB]", color="#cccccc", fontsize=9)
cbar.ax.tick_params(colors="#cccccc", labelsize=8)

plt.title("SETI Rádiómérések - Precíziós Lineáris Csillagtérkép (0h Központú)", color="#ffffff", fontsize=12, pad=15)
plt.tight_layout()


# =========================================================================
# 🖱️ INTERAKTÍV KATTINTÁS KEZELŐ
# =========================================================================
def on_pick(event):
    for i, rect in enumerate(poligon_lista):
        if rect == event.artist:
            fajl_nev, db_val, ra_c = poligon_mappak[i]
            ra_ora = ra_c / 15.0
            print("\n" + "🧱"*20)
            print(f"🟩 KATTINTOTT PIXEL FÁJL:  {fajl_nev}")
            print(f"📊 Átlagos jelszint:      {db_val:.4f} dB")
            print(f"⏰ Pozíció:               {ra_ora:.2f} óra")
            print("🧱"*20)

fig.canvas.mpl_connect('pick_event', on_pick)

output_map_png = r"C:\seti\kalibralt_csillagterkep.png"
plt.savefig(output_map_png, dpi=300, facecolor='#0c0d0d', edgecolor='none')
print(f"\n🎯 SIKER! Az északi félgömbre szabott, hitelesített térkép elmentve ide: {output_map_png}")
plt.show()
