import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u

def galactic_to_radec(l, b):
    """
    Galaktikus koordinátákat (l, b) RA/DEC-re konvertál.
    
    Paraméterek:
    l (float): Galaktikus hosszúság fokban
    b (float): Galaktikus szélesség fokban
    
    Visszatérési érték:
    tuple: (RA órában, DEC fokban)
    """
    # Galaktikus koordináták létrehozása
    galactic = SkyCoord(l=l*u.degree, b=b*u.degree, frame='galactic')
    
    # ICRS keretbe konvertálás (RA/DEC)
    icrs = galactic.icrs
    
    # RA órákra konvertálása (1 óra = 15 fok)
    ra_hours = icrs.ra.hour
    dec_degrees = icrs.dec.degree
    
    return ra_hours, dec_degrees

def format_output(ra_hours, dec_degrees):
    """
    Kimeneti formátum RA órában és DEC fokban.
    """
    ra_hour = int(ra_hours)
    ra_min = int((ra_hours - ra_hour) * 60)
    ra_sec = ((ra_hours - ra_hour) * 60 - ra_min) * 60
    
    dec_deg = int(dec_degrees)
    dec_arcmin = int((dec_degrees - dec_deg) * 60)
    dec_arcsec = ((dec_degrees - dec_deg) * 60 - dec_arcmin) * 60
    
    return f"RA: {ra_hour:02d}h{ra_min:02d}m{ra_sec:06.3f}s, DEC: {dec_deg:+03d}°{dec_arcmin:02d}'{dec_arcsec:06.3f}\""

# Felhasználás
if __name__ == "__main__":
    # Példa: l=100, b=0
    l = float(input("Galaktikus hosszúság (l) fokban: "))
    b = float(input("Galaktikus szélesség (b) fokban: "))
    
    ra, dec = galactic_to_radec(l, b)
    print(format_output(ra, dec))