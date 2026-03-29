hydrogen_logger_clean.py
#!/usr/bin/env python3

import SoapySDR
from SoapySDR import *
import numpy as np
import time
import csv
from datetime import datetime, timezone
import os

# ================== CONFIG ==================
CENTER_FREQ = 1420.4058e6   # Hydrogen line [Hz]
SAMPLE_RATE = 2e6           # 2 MHz bandwidth
GAIN_DB = 40                # Fixed gain
FFT_BIN_HZ = 10e3           # 10 kHz bin
INTEGRATIONS = 8            # 8 × 30 s
INTEGRATION_TIME = 30       # seconds
OUTPUT_DIR = "/media/pi/KINGSTON/hydrogen"  # ÁLLÍTSD ÁT!
# ============================================

# Könyvtár létrehozása ha nincs
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Initializing SDRplay RSP1A...")

# SDR init
sdr = SoapySDR.Device(dict(driver="sdrplay"))

sdr.setSampleRate(SOAPY_SDR_RX, 0, SAMPLE_RATE)
sdr.setFrequency(SOAPY_SDR_RX, 0, CENTER_FREQ)
sdr.setGainMode(SOAPY_SDR_RX, 0, False)  # AGC OFF
sdr.setGain(SOAPY_SDR_RX, 0, GAIN_DB)

# Stream setup
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream)

print("SDR initialized, starting H-line logging...")

# FFT paraméterek
fft_size = int(SAMPLE_RATE / FFT_BIN_HZ)

while True:
    timestamp = datetime.now(timezone.utc)
    filename = f"{OUTPUT_DIR}/" + timestamp.strftime("%Y%m%d_%H%M.csv")

    print(f"Recording: {filename}")

    # spektrum gyűjtés
    spectrum_accum = np.zeros(fft_size)

    for i in range(INTEGRATIONS):
        print(f"  Integration {i+1}/{INTEGRATIONS}")

        samples = []
        start_time = time.time()

        while time.time() - start_time < INTEGRATION_TIME:
            buff = np.empty(4096, np.complex64)
            sr = sdr.readStream(rxStream, [buff], len(buff))
            if sr.ret > 0:
                samples.append(buff.copy())

        if len(samples) == 0:
            continue

        samples = np.concatenate(samples)

        # FFT
        fft = np.fft.fftshift(np.fft.fft(samples, n=fft_size))
        power = 10 * np.log10(np.abs(fft)**2)

        spectrum_accum += power

    # átlag
    spectrum_avg = spectrum_accum / INTEGRATIONS

    # frekvencia tengely
    freqs = np.linspace(
        CENTER_FREQ - SAMPLE_RATE/2,
        CENTER_FREQ + SAMPLE_RATE/2,
        fft_size
    )

    # CSV mentés
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc", "frequency_hz", "power_db"])

        for f_hz, p_db in zip(freqs, spectrum_avg):
            writer.writerow([timestamp.isoformat(), f_hz, p_db])

    print("Saved:", filename)

# cleanup (nem fut le végtelen ciklus miatt)
sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)