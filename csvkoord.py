#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import pandas as pd
from skyfield.api import Topos, load
from skyfield.data import hipparcos
import numpy as np

# ================== CONFIG ==================
SOURCE_FOLDER = r"C:\pi_sdr\seti\data"
DEST_FOLDER = r"C:\pi_sdr\seti\kep"
COORD_STEP = 5  # fokonkénti "kocka"

# Antenna és hely
ANT_AZ = 177      # fok
ANT_EL = 77       # fok
LAT = 47.523      # Erdőkertes
LON = 19.325
ELEV_M = 150      # kb tengerszint feletti magasság

# ============================================

# Skyfield setup
ts = load.timescale()
t = ts.now()
earth = load('de421.bsp')['earth']
observer = earth + Topos(latitude_degrees=LAT, longitude_degrees=LON, elevation_m=ELEV_M)

# Átalakítás horizont -> égi koordináták (RA, Dec)
from skyfield.positionlib import ICRF
from skyfield.api import Angle
from skyfield.api import Star

def horizontal_to_icrf(az, el, observer, t):
    from skyfield.api import Star
    from skyfield.api import Topos
    from skyfield.api import Angle
    from skyfield.api import load
    from skyfield import almanac
    
    # Skyfield az/el: az=0 É, el=0 horizont
    alt = Angle(degrees=el)
    azm = Angle(degrees=az)
    astrometric = observer.at(t).from_altaz(alt, azm)
    ra, dec, distance = astrometric.radec()
    return ra, dec

# Egyszerűsített: Skyfield-hez szükséges a Topos-ra váltás
# Itt az antenna mutatási pontját konvertáljuk galaktikus koordinátává
from astropy.coordinates import SkyCoord, AltAz, EarthLocation, FK5, Galactic
from astropy.time import Time
import astropy.units as u

# Földrajzi hely
loc = EarthLocation(lat=LAT*u.deg, lon=LON*u.deg, height=ELEV_M*u.m)

# Idő
time = Time.now()

# AltAz koordináták az antenna irányából
altaz = AltAz(alt=ANT_EL*u.deg, az=ANT_AZ*u.deg, location=loc, obstime=time)

# FK5 (ICRS) koordináták
fk5 = SkyCoord(altaz.transform_to(FK5(equinox='J2000')))

# Galaktikus koordináták
gal = fk5.transform_to(Galactic)
l = gal.l.deg
b = gal.b.deg

# Mappa kiválasztása
def get_folder_name(l, b):
    l_bin = int(l // COORD_STEP * COORD_STEP)
    b_bin = int(b // COORD_STEP * COORD_STEP)
    return f"l{l_bin}_b{b_bin}"

folder_name = get_folder_name(l, b)
dest_path = os.path.join(DEST_FOLDER, folder_name)
if not os.path.exists(dest_path):
    os.makedirs(dest_path)

# CSV fájlok másolása
csv_files = [f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".csv")]
for file in csv_files:
    shutil.copy2(os.path.join(SOURCE_FOLDER, file), dest_path)
    print(f"Copied {file} -> {dest_path}")

print(f"Galaktikus koordináták: l={l:.2f}°, b={b:.2f}°")
print(f"Fájlok mentve a {dest_path} mappába")
