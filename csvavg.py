#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import pandas as pd
import numpy as np

# ================== CONFIG ==================
SOURCE_FOLDER = r"C:\seti\mapdata_radec"     # Ahol az RA/DEC szerinti alkönyvtárak vannak
DEST_FOLDER = r"C:\seti\dataavg_radec"       # Ahová az összevont átlagfájlok kerülnek
LOG_FILE = r"C:\seti\dataavg_radec\csvavg.log"
# ============================================

# Mappa létrehozása, ha nem létezik
if not os.path.exists(DEST_FOLDER):
    os.makedirs(DEST_FOLDER)

# Logging beállítása
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("📊 csvavg_radec.py - Almappák adatainak átlagolása\n")
logging.info("=== csvavg_radec.py start ===")

if not os.path.exists(SOURCE_FOLDER):
    print(f"❌ HIBA: A forrás mappa nem létezik: {SOURCE_FOLDER}")
    exit(1)

# Alkonnyvtárak listázása
mappak = sorted([d for d in os.listdir(SOURCE_FOLDER) if os.path.isdir(os.path.join(SOURCE_FOLDER, d))])

if not mappak:
    print("❌ Nem találhatók alkönyvtárak a megadott forrásmappában!")
    logging.warning("No subdirectories found")
    exit(1)

print(f"Talált alkönyvtárak száma: {len(mappak)}\n")

success_count = 0
error_count = 0

for mappa in mappak:
    mappa_teljes_ut = os.path.join(SOURCE_FOLDER, mappa)
    
    # Kikeressük a mappában lévő összes CSV fájlt (az _info.json-t átugorjuk)
    csv_fajlok = [f for f in os.listdir(mappa_teljes_ut) if f.endswith(".csv")]
    
    if not csv_fajlok:
        continue
    
    print(f"📁 {mappa}/ feldolgozása ({len(csv_fajlok)} fájl)...")
    
    adat_listak = []
    frekvencia_tengely = None
    oszlop_nevek = None
    
    for fajlnev in csv_fajlok:
        fajl_ut = os.path.join(mappa_teljes_ut, fajlnev)
        try:
            df = pd.read_csv(fajl_ut, sep=",")
            df.columns = df.columns.str.strip()
            
            # Az első fájlnál elmentjük a struktúrát és a pontos frekvenciákat
            if frekvencia_tengely is None and "frequency_hz" in df.columns:
                frekvencia_tengely = df["frequency_hz"].values
                # Minden numerikus oszlopot átlagolunk, kivéve az időbélyeget és a számlálót
                oszlop_nevek = [col for col in df.columns if col not in ["timestamp_utc", "frequency_hz"]]
            
            # Elmentjük a numerikus adatokat egy nagy listába
            adat_listak.append(df[oszlop_nevek].values)
            
        except Exception as e:
            logging.error(f"Hiba a(z) {fajlnev} fájl beolvasásakor: {e}")
            
    if len(adat_listak) == 0:
        print(f"  ❌ {mappa} - Nem sikerült adatot beolvasni")
        error_count += 1
        continue
        
    try:
        # 3D tömbbé alakítjuk (fájlok száma, sorok száma, oszlopok száma)
        # és tengely mentén kiszámoljuk a tiszta számtani átlagot (mean)
        osszesitett_tomb = np.array(adat_listak)
        atlagolt_tomb = np.mean(osszesitett_tomb, axis=0)
        
        # Új DataFrame építése a kiszámolt átlagokból
        uj_df = pd.DataFrame(atlagolt_tomb, columns=oszlop_nevek)
        
        # Visszaszúrjuk a fix frekvencia oszlopot az elejére
        uj_df.insert(0, "frequency_hz", frekvencia_tengely)
        
        # Ha a szoftverben volt mérésszámláló, azt egész számmá alakítjuk
        if "measurement_count" in uj_df.columns:
            uj_df["measurement_count"] = uj_df["measurement_count"].round().astype(int)
            
        # A mentendő fájl neve pontosan a mappa neve lesz (pl. ra195_dec+0039.csv)
        kimeneti_fajlnev = f"{mappa}.csv"
        kimeneti_ut = os.path.join(DEST_FOLDER, kimeneti_fajlnev)
        
        # Mentés vesszővel elválasztva, indexoszlop nélkül
        uj_df.to_csv(kimeneti_ut, index=False, sep=",")
        print(f"  ✅ Mentve -> {kimeneti_fajlnev}")
        logging.info(f"Sikeres átlagolás: {mappa} -> {kimeneti_fajlnev} ({len(csv_fajlok)} fájlból)")
        success_count += 1
        
    except Exception as e:
        print(f"  ❌ Hiba az átlagolás során ebben a mappában: {mappa} ({e})")
        logging.error(f"Átlagolási hiba a(z) {mappa} mappában: {e}")
        error_count += 1

# ================ ÖSSZEFOGLALÓ ================
print("\n" + "="*70)
print("✅ ÁTLAGOLÁS KÉSZ")
print(f"Sikeresen összevont mappák: {success_count} | Hiba: {error_count}")
print(f"Végeredmény helye: {DEST_FOLDER}")
print("="*70)
logging.info("=== csvavg_radec.py end ===\n")
