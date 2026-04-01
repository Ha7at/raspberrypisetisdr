#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from scipy.optimize import curve_fit

# ================= CONFIG =================
INPUT_FOLDER = r"C:\seti\dataavg"
BASELINE_FILE = r"C:\seti\hydrogen\baseline.csv"
OUTPUT_FOLDER = r"C:\seti\kep"
LOG_FILE = os.path.join(OUTPUT_FOLDER, "dbkepg.log")

# Plot beállítások
FIGSIZE = (14, 12)
DPI = 300
H_LINE_FREQ = 1420.405751768e6  # Hidrogénvonal Hz-ben

# ==========================================

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🎨 dbkepg.py - Gauss-görbe illesztés és vizualizáció\n")
logging.info("=== dbkepg.py start ===")

# Output mappa
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Baseline beolvasása
if not os.path.exists(BASELINE_FILE):
    print(f"❌ Baseline fájl nem létezik: {BASELINE_FILE}")
    logging.error(f"Baseline file not found: {BASELINE_FILE}")
    exit(1)

baseline = pd.read_csv(BASELINE_FILE)
print(f"✅ Baseline beolvasva: {len(baseline)} bin\n")
logging.info(f"Baseline loaded: {len(baseline)} bins")

# CSV fájlok keresése (dataavg/ mappából)
csv_files = sorted([f for f in os.listdir(INPUT_FOLDER)
                   if f.startswith("avg_") and f.endswith(".csv")])

if not csv_files:
    print("❌ Nincs avg_*.csv fájl!")
    logging.error("No avg CSV files found")
    exit(1)

print(f"Talált: {len(csv_files)} fájl\n")


def gaussian(x, amplitude, center, sigma):
    """Gauss-görbe függvény."""
    return amplitude * np.exp(-((x - center) ** 2) / (2 * sigma ** 2))


def fit_gaussian(freq_mhz, power):
    """
    Gauss-görbét illeszt a (freq_mhz, power) adatokra.
    Visszaad: (popt, r_squared, rmse) vagy None ha sikertelen.
    """
    # NaN szűrés
    mask = np.isfinite(freq_mhz) & np.isfinite(power)
    x = freq_mhz[mask]
    y = power[mask]

    if len(x) < 4:
        return None

    # Kezdeti becslések
    amplitude0 = y.max() - y.min()
    center0 = x[y.argmax()]
    sigma0 = max((x[-1] - x[0]) / 6.0, 1e-6)

    try:
        popt, _ = curve_fit(
            gaussian, x, y,
            p0=[amplitude0, center0, sigma0],
            bounds=([-np.inf, x[0], 1e-6], [np.inf, x[-1], np.inf]),
            maxfev=10000
        )
        y_fit = gaussian(x, *popt)
        ss_res = np.sum((y - y_fit) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1.0 - ss_res / ss_tot if ss_tot != 0 else np.nan
        rmse = np.sqrt(ss_res / len(y))
        return popt, r_squared, rmse
    except Exception as exc:
        logging.debug(f"Gaussian fit failed: {exc}")
        return None


# Feldolgozás
processed_count = 0
error_count = 0

for file in csv_files:
    input_path = os.path.join(INPUT_FOLDER, file)

    try:
        # Beolvasás
        df = pd.read_csv(input_path)

        # Szükséges oszlopok
        if "frequency_hz" not in df.columns or "power_db_smoothed" not in df.columns:
            print(f"  ⚠️  {file} - hiányzó oszlopok")
            logging.warning(f"Missing columns in {file}")
            continue

        # Koordináta név kinyerése
        coord_name = file.replace("avg_", "").replace(".csv", "")

        # =============== BASELINE LEVONÁS ===============
        df_merged = pd.merge(
            df,
            baseline[["frequency_hz", "baseline_db"]],
            on="frequency_hz",
            how="left"
        )
        df_merged["power_db_corrected"] = (
            df_merged["power_db_smoothed"] - df_merged["baseline_db"]
        )

        freq_mhz = df_merged["frequency_hz"].values / 1e6
        power_smoothed = df_merged["power_db_smoothed"].values
        power_corrected = df_merged["power_db_corrected"].values

        # =============== GAUSS ILLESZTÉS ===============
        fit_smoothed = fit_gaussian(freq_mhz, power_smoothed)
        fit_corrected = fit_gaussian(freq_mhz, power_corrected)

        # =============== PLOT ===============
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=FIGSIZE, dpi=DPI)

        h_mhz = H_LINE_FREQ / 1e6

        # ========== SUBPLOT 1: Simított + Gauss ==========
        ax1.plot(freq_mhz, power_smoothed, color='blue', linewidth=1.5,
                 label='Simított spektrum')
        ax1.axvline(h_mhz, color='red', linestyle='--', linewidth=2,
                    label=f'H-vonal ({h_mhz:.4f} MHz)', alpha=0.7)

        if fit_smoothed is not None:
            popt, r2, rmse = fit_smoothed
            amp, ctr, sig = popt
            gauss_y = gaussian(freq_mhz, *popt)
            ax1.plot(freq_mhz, gauss_y, color='orange', linewidth=2,
                     linestyle='--', label='Gauss illesztés')
            title1 = (
                f"{coord_name} - Simított + Gauss illesztés\n"
                f"Amp: {amp:.2f} dB | Ctr: {ctr:.4f} MHz | "
                f"σ: {sig:.4f} MHz | R²: {r2:.4f} | RMSE: {rmse:.4f}"
            )
        else:
            title1 = f"{coord_name} - Simított (Gauss illesztés sikertelen)"
            logging.warning(f"{coord_name}: Gaussian fit failed for smoothed data")

        ax1.set_title(title1, fontsize=11, fontweight='bold')
        ax1.set_ylabel('Teljesítmény (dB)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best', fontsize=10)

        # ========== SUBPLOT 2: Baseline-korrigált + Gauss ==========
        ax2.plot(freq_mhz, power_corrected, color='darkblue', linewidth=1.5,
                 label='Baseline-korrigált')
        ax2.axvline(h_mhz, color='red', linestyle='--', linewidth=2,
                    label=f'H-vonal ({h_mhz:.4f} MHz)', alpha=0.7)
        ax2.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

        if fit_corrected is not None:
            popt_c, r2_c, rmse_c = fit_corrected
            amp_c, ctr_c, sig_c = popt_c
            gauss_y_c = gaussian(freq_mhz, *popt_c)
            ax2.plot(freq_mhz, gauss_y_c, color='orange', linewidth=2,
                     linestyle='--', label='Gauss illesztés')
            title2 = (
                f"{coord_name} - Baseline-korrigált + Gauss illesztés\n"
                f"Amp: {amp_c:.2f} dB | Ctr: {ctr_c:.4f} MHz | "
                f"σ: {sig_c:.4f} MHz | R²: {r2_c:.4f} | RMSE: {rmse_c:.4f}"
            )
        else:
            title2 = f"{coord_name} - Baseline-korrigált (Gauss illesztés sikertelen)"
            logging.warning(f"{coord_name}: Gaussian fit failed for corrected data")

        ax2.set_title(title2, fontsize=11, fontweight='bold')
        ax2.set_ylabel('Teljesítmény (dB)', fontsize=11)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best', fontsize=10)

        # ========== SUBPLOT 3: Reziduálisok ==========
        if fit_corrected is not None:
            residuals = power_corrected - gaussian(freq_mhz, *popt_c)
            valid = np.isfinite(residuals)
            ax3.plot(freq_mhz[valid], residuals[valid], color='purple',
                     linewidth=1.0, label='Reziduálisok (actual - fit)')
            ax3.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.6)
            ax3.axvline(h_mhz, color='red', linestyle='--', linewidth=1.5, alpha=0.6)

            # Hisztogram a másodlagos tengelyen
            ax3_hist = ax3.twinx()
            ax3_hist.hist(residuals[valid], bins=40, color='purple',
                          alpha=0.25, label='Eloszlás')
            ax3_hist.set_ylabel('Darabszám', fontsize=10, color='purple')

            rmse_res = np.sqrt(np.mean(residuals[valid] ** 2))
            title3 = (
                f"{coord_name} - Reziduálisok\n"
                f"RMSE: {rmse_res:.4f} dB | "
                f"Min: {residuals[valid].min():.4f} | Max: {residuals[valid].max():.4f}"
            )
            lines1, labels1 = ax3.get_legend_handles_labels()
            lines2, labels2 = ax3_hist.get_legend_handles_labels()
            ax3.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=10)
        else:
            ax3.text(0.5, 0.5, 'Reziduálisok nem elérhetők\n(Gauss illesztés sikertelen)',
                     transform=ax3.transAxes, ha='center', va='center',
                     fontsize=12, color='red')
            title3 = f"{coord_name} - Reziduálisok (nem elérhető)"

        ax3.set_title(title3, fontsize=11, fontweight='bold')
        ax3.set_xlabel('Frekvencia (MHz)', fontsize=11)
        ax3.set_ylabel('Reziduális (dB)', fontsize=11)
        ax3.grid(True, alpha=0.3)

        # Layout és mentés
        plt.tight_layout()
        output_file = f"gauss_{coord_name}.png"
        output_path = os.path.join(OUTPUT_FOLDER, output_file)
        plt.savefig(output_path, dpi=DPI)
        plt.close()

        print(f"  ✅ {coord_name}")
        print(f"      → {output_file}")
        if fit_corrected is not None:
            print(f"      Gauss amp: {amp_c:.2f} dB | ctr: {ctr_c:.4f} MHz | "
                  f"σ: {sig_c:.4f} MHz | R²: {r2_c:.4f}")

        processed_count += 1
        logging.info(
            f"Plotted: {coord_name} | "
            f"Smoothed fit: {'OK' if fit_smoothed else 'FAILED'} | "
            f"Corrected fit: {'OK' if fit_corrected else 'FAILED'}"
        )

    except Exception as e:
        print(f"  ❌ {file} - Hiba: {e}")
        logging.error(f"Error processing {file}: {e}")
        error_count += 1

print("\n" + "=" * 70)
print("✅ GAUSS ILLESZTÉS KÉSZ")
print("=" * 70)
print(f"Feldolgozva: {processed_count}")
print(f"Hiba: {error_count}")
print(f"Output mappa: {OUTPUT_FOLDER}")
logging.info(f"=== dbkepg.py end === Processed: {processed_count}, Errors: {error_count}\n")
