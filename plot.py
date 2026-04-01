import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from mpl_toolkits.mplot3d import Axes3D

# --- Könyvtár ---
DATA_DIR = r"C:\seti\hydrogen"   # ide tedd a kiválasztott CSV-ket

files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".csv")])
print(f"Fájlok száma: {len(files)}")

all_times = []
all_freqs = None
all_power = []

# --- CSV-k beolvasása ---
for fname in files:
    path = os.path.join(DATA_DIR, fname)

    # idő a fájlnévből (YYYYMMDD_HHMM)
    try:
        t = datetime.strptime(fname.replace(".csv", ""), "%Y%m%d_%H%M")
    except ValueError:
        print(f"Skipping file with unexpected format: {fname}")
        continue
    
    all_times.append(t)

    df = pd.read_csv(path)

    if all_freqs is None:
        all_freqs = df["frequency_hz"].values

    # Szűrés: csak -40 dB feletti értékek
    power_filtered = df["power_db"].values.copy()
    power_filtered[power_filtered < -40] = np.nan
    
    all_power.append(power_filtered)

all_power = np.array(all_power)

# --- Idő tengely percben ---
t0 = all_times[0]
time_minutes = np.array([(t - t0).total_seconds() / 60 for t in all_times])

# --- 3D rács ---
F, T = np.meshgrid(all_freqs, time_minutes)

# --- 3D ábra ---
fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(111, projection="3d")

surf = ax.plot_surface(
    F,
    T,
    all_power,
    cmap="viridis",
    linewidth=0,
    antialiased=True
)

ax.set_xlabel("Frekvencia [Hz]")
ax.set_ylabel("Idő [perc]")
ax.set_zlabel("Teljesítmény [dB]")
ax.set_title("3D SETI spektrum (SoapyPower, 4 perces minták) - csak -40 dB feletti")

fig.colorbar(surf, shrink=0.5, aspect=10, label="dB")
plt.tight_layout()
plt.show()
