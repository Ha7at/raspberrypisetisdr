from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
import astropy.units as u
import csv

# ===== HELY (Erdőkertes) =====
lat = 47.67
lon = 19.32
height = 150

location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=height*u.m)

# ===== BEVITEL =====
az = float(input("Azimut (fok): "))
el = float(input("Eleváció (fok): "))

# ===== IDŐ =====
start_time = Time.now()

# ===== BEÁLLÍTÁS =====
hours = 120
step_minutes = 20  # <-- EZT ÁLLÍTSD (pl. 1-5 perc ideális)

steps = int((hours * 60) / step_minutes)

# ===== CSV fájl =====
filename = "antenna_galactic_track.csv"

with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    
    # fejléc
    writer.writerow(["time_utc", "az_deg", "el_deg", "l_deg", "b_deg"])
    
    print("\n=== SZÁMOLÁS FOLYAMATBAN ===")
    
    for i in range(steps + 1):
        t = start_time + i * step_minutes * u.min
        
        # horizontális koordináta
        altaz = SkyCoord(
            az=az*u.deg,
            alt=el*u.deg,
            frame=AltAz(obstime=t, location=location)
        )
        
        # -> galaktikus
        gal = altaz.transform_to('galactic')
        
        # mentés CSV-be
        writer.writerow([
            t.iso,
            round(az, 2),
            round(el, 2),
            round(gal.l.deg, 4),
            round(gal.b.deg, 4)
        ])
        
        # konzolra is ír (ritkábban)
        if i % 1 == 0:
            print(f"{t.iso[:16]} | l={gal.l.deg:.2f}° b={gal.b.deg:.2f}°")

print(f"\nKész! Fájl mentve: {filename}")