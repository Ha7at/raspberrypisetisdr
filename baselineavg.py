import os
import pandas as pd
import numpy as np

# ================== BEÁLLÍTÁSOK ==================
FORRAS_MAPPA = r"C:\seti\baseline"     # Ide másold be a kora délutáni fájlokat!
KIMENETI_FAJL = r"C:\seti\baseline.csv"      # A végleges, tiszta új Baseline helye
MELYIK_OSZLOP = "power_db_smoothed"          # Az oszlopnév
# =================================================

if not os.path.exists(FORRAS_MAPPA):
    os.makedirs(FORRAS_MAPPA)
    print(f"🟩 Létrehoztam a mappát: {FORRAS_MAPPA}")
    print("👉 Kérlek, másolj bele néhány UTC 12:00 és 14:00 között készült nyers CSV fájlt, majd indítsd el újra a programot!")
    exit(0)

# Összegyűjtjük a CSV fájlokat
csv_fajlok = [f for f in os.listdir(FORRAS_MAPPA) if f.endswith(".csv")]

if not csv_fajlok:
    print(f"⚠️ A {FORRAS_MAPPA} mappa üres! Másolj bele kora délutáni nyers fájlokat.")
    exit(0)

print(f"📡 Új Baseline generálása {len(csv_fajlok)} db délutáni fájl átlagolásával...")

frekvenciak_hz = None
osszes_linearis_energia = None

# Végigmegyünk a fájlokon és lineáris tartományban átlagolunk a precíz matematikaért
for f_nev in csv_fajlok:
    try:
        teljes_ut = os.path.join(FORRAS_MAPPA, f_nev)
        df = pd.read_csv(teljes_ut, sep=",")
        df.columns = df.columns.str.strip()
        
        # Átváltás decibelből lineáris energiává (mW) az átlagoláshoz
        p_linear = 10 ** (df[MELYIK_OSZLOP].values / 10.0)
        
        if osszes_linearis_energia is None:
            frekvenciak_hz = df["frequency_hz"].values
            osszes_linearis_energia = p_linear
        else:
            osszes_linearis_energia += p_linear
    except Exception as e:
        print(f"  ❌ Hiba a(z) {f_nev} fájlnál: {e}")

# Kiszámoljuk az átlagot lineárisan
atlag_linearis = osszes_linearis_energia / len(csv_fajlok)

# Visszaalakítjuk decibelbe (dB)
atlag_db = 10 * np.log10(atlag_linearis)

# Létrehozzuk a tiszta új Baseline DataFrame-et
uj_base_df = pd.DataFrame({
    "frequency_hz": frekvenciak_hz.astype(int),
    MELYIK_OSZLOP: np.round(atlag_db, 3)
})

# Elmentjük a lemezre a régi baseline.csv helyére
uj_base_df.to_csv(KIMENETI_FAJL, index=False, sep=",")

print("\n" + "⭐"*20)
print("✅ SIKER! Az új, hidrogénmentes Mester Alapvonal elkészült!")
print(f"💾 Elmentve ide: {KIMENETI_FAJL}")
print("⭐"*20)
