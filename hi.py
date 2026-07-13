# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
SDRplay RSP1A Hydrogen-Line Observer
21 cm band (1420.4058 MHz) spectroscopy with Low-IF mode
Optimized for Raspberry Pi - CSV only
"""

import SoapySDR
from SoapySDR import *
import numpy as np
import time
import csv
from datetime import datetime, timezone
import os

# ================== CONFIG ==================
CENTER_FREQ = 1420.4058e6      # Hydrogen line [Hz]
SAMPLE_RATE = 2e6               # 2 MHz bandwidth
RFGR = 4                         # RF/LNA gain: 0=max gain, 9=min
IFGR = 59                        # IF gain: 20-59 dB (max)
FFT_BIN_HZ = 2000               # 2 kHz bin resolution
INTEGRATIONS = 24                # Number of integration periods
INTEGRATION_TIME = 10            # Seconds per integration (24*10=240s=4min)
BUFFER_SIZE = 65536              # Read buffer size
OUTPUT_DIR = "/media/pi/ESD-USB/hydrogen"  # Output directory
USE_LOW_IF = True                # True = 1.62 MHz IF offset (DC-mentes)
USE_HAMMING_WINDOW = True        # Reduce spectral leakage
ENABLE_BIAST = True              # BiasT for external LNA
# ============================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("SDRplay RSP1A Hydrogen-Line Observer (21 cm)")
print("=" * 70)
print(f"Center Frequency: {CENTER_FREQ/1e6:.4f} MHz")
print(f"Sample Rate: {SAMPLE_RATE/1e6:.1f} MHz")
print(f"RF Gain (RFGR): {RFGR} (0=max gain, 9=min loss)")
print(f"IF Gain (IFGR): {IFGR} dB")
print(f"FFT Resolution: {FFT_BIN_HZ} Hz")
print(f"Integration: {INTEGRATIONS} x {INTEGRATION_TIME}s = {INTEGRATIONS * INTEGRATION_TIME}s (4 min per file)")
print(f"Low-IF Mode: {'Enabled' if USE_LOW_IF else 'Disabled'}")
print(f"Output Dir: {OUTPUT_DIR}")
print("=" * 70)

# ========== SDR INITIALIZATION ==========
print("\nInitializing SDRplay RSP1A...")

try:
    sdr = SoapySDR.Device(dict(driver="sdrplay"))
    print("✓ SDR device found")
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

# Sample rate & frequency
sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
print(f"✓ Sample Rate: {SAMPLE_RATE/1e6} MHz")
print(f"✓ Center Freq: {CENTER_FREQ/1e6:.4f} MHz")

# Gain configuration - DUAL GAIN (RF + IF)
sdr.setGainMode(SOAPY_SDR_RX, 0, False)  # AGC OFF
sdr.setGain(SOAPY_SDR_RX, 0, "RFGR", RFGR)
sdr.setGain(SOAPY_SDR_RX, 0, "IFGR", IFGR)
print(f"✓ RF Gain (RFGR): {RFGR}")
print(f"✓ IF Gain (IFGR): {IFGR} dB")

# Low-IF mode (DC offset removal)
if USE_LOW_IF:
    try:
        sdr.writeSetting("if_type", "1")  # 1 = 1.62 MHz IF
        print("✓ Low-IF Mode (1.62 MHz): Enabled")
    except Exception as e:
        print(f"⚠ Low-IF not available: {e}, using Zero-IF")

# BiasT (external LNA power supply)
if ENABLE_BIAST:
    try:
        sdr.writeSetting("biasT_ctrl", "true")
        print("✓ BiasT: Enabled (LNA power on)")
    except Exception as e:
        print(f"⚠ BiasT control not available: {e}")

# IQ correction
try:
    sdr.writeSetting("iqcorr_ctrl", "true")
    print("✓ IQ Correction: Enabled")
except Exception as e:
    print(f"⚠ IQ correction not available: {e}")

# Stream setup
print("\nSetting up RX stream...")
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)
print("✓ Stream activated")

# FFT parameters
fft_size = int(SAMPLE_RATE / FFT_BIN_HZ)
print(f"✓ FFT Size: {fft_size} bins")
print(f"✓ Frequency Range: {CENTER_FREQ/1e6:.4f} MHz ± {SAMPLE_RATE/2/1e6:.1f} MHz")

# Hamming window for spectral leakage reduction
if USE_HAMMING_WINDOW:
    window = np.hamming(fft_size)
    print("✓ Hamming Window: Enabled")
else:
    window = np.ones(fft_size)
    print("✓ Window: Rectangular (none)")

print("\n" + "=" * 70)
print("SDR initialization complete. Starting observations...")
print("=" * 70 + "\n")

# ========== MAIN OBSERVATION LOOP ==========

try:
    observation_count = 0
    
    while True:
        timestamp = datetime.now(timezone.utc)
        filename = f"{OUTPUT_DIR}/" + timestamp.strftime("%Y%m%d_%H%M.csv")

        print(f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] Recording: {timestamp.strftime('%Y%m%d_%H%M.csv')}")

        # Spectrum accumulation
        spectrum_accum = np.zeros(fft_size)
        total_samples = 0

        for i in range(INTEGRATIONS):
            print(f"  Integration {i+1}/{INTEGRATIONS}...", end=" ", flush=True)

            samples = []
            start_time = time.time()
            samples_read = 0

            # Read samples for INTEGRATION_TIME seconds
            while time.time() - start_time < INTEGRATION_TIME:
                buff = np.empty(BUFFER_SIZE, np.complex64)
                sr = sdr.readStream(rxStream, [buff], BUFFER_SIZE)
                
                if sr.ret > 0:
                    samples.append(buff[:sr.ret].copy())
                    samples_read += sr.ret
                elif sr.ret < 0:
                    print(f"⚠ Stream error: {sr.ret}")
                    break

            if len(samples) == 0:
                print("⚠ No samples read!")
                continue

            # Concatenate all samples
            full_samples = np.concatenate(samples)
            total_samples += len(full_samples)

            # Remove DC offset
            full_samples_centered = full_samples - np.mean(full_samples)

            # Apply window and FFT
            windowed = full_samples_centered[:fft_size] * window
            fft_result = np.fft.fftshift(np.fft.fft(windowed, n=fft_size))

            # Power calculation (dBFS - dB Full Scale)
            power_db = 10 * np.log10(np.abs(fft_result)**2 / fft_size + 1e-12)
            spectrum_accum += power_db

            elapsed = time.time() - start_time
            print(f"✓ ({samples_read:,} samples, {elapsed:.1f}s)")

        # Average spectrum
        spectrum_avg = spectrum_accum / INTEGRATIONS

        # Frequency axis
        freqs = np.linspace(
            CENTER_FREQ - SAMPLE_RATE/2,
            CENTER_FREQ + SAMPLE_RATE/2,
            fft_size
        )

        # ===== CSV SAVE (EXACT original format) =====
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp_utc", "frequency_hz", "power_db"])

            for f_hz, p_db in zip(freqs, spectrum_avg):
                writer.writerow([timestamp.isoformat(), f_hz, p_db])

        # Statistics
        max_power_idx = np.argmax(spectrum_avg)
        max_power_freq = freqs[max_power_idx]
        max_power_db = spectrum_avg[max_power_idx]
        mean_power_db = np.mean(spectrum_avg)
        std_power_db = np.std(spectrum_avg)
        snr_db = max_power_db - mean_power_db

        print(f"\n  Peak: {max_power_freq/1e6:.6f} MHz ({(max_power_freq-CENTER_FREQ)/1e3:+.2f} kHz)")
        print(f"  Power: {max_power_db:.2f} dBFS (Mean: {mean_power_db:.2f}, Std: {std_power_db:.2f})")
        print(f"  SNR: {snr_db:.2f} dB")
        print(f"  Total Samples: {total_samples:,}")
        print(f"  ✓ Saved: {filename}\n")

        observation_count += 1

except KeyboardInterrupt:
    print("\n\n⏹ Observation stopped by user (Ctrl+C)")

# ========== CLEANUP =====
print("\nCleaning up...")
sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)
print("✓ Stream closed")
print("✓ Done!")
