# 🛰️ Raspberry Pi Hydrogen-Line SDR Monitor

Amatőr hydrogen-line rádiócsillágászati és SETI megfigyelőrendszer RSP1A SDR vevővel, Raspberry Pi-n alapulva.

---

## 📡 Rendszer leírása

Ez a projekt egy egyszerű, de hatékony eszközt nyújt a **21 cm-es hydrogen-line (1420,4058 MHz)** folyamatos monitorozásához. A rendszer alkalmas:

- 🔭 Amatőr rádiócsillágászatra (tejút-struktúra feltérképezése)
- 🔍 SETI monitoring (rendellenes jelek keresése)
- 📊 Galaktikus hidrogén-emisszió mérésére
- 🗺️ Adatok galaktikus koordináták szerinti archiválására

---

## 🔧 Hardver

| Komponens | Leírás |
|-----------|--------|
| **SDR vevő** | SDRplay RSP1A |
| **Antenna** | 2,4 m parabolaantenna |
| **Azimut** | 218° |
| **Eleváció** | 70° |
| **Frekvencia** | 1420,4058 MHz (hydrogen line) |
| **Számítógép** | Raspberry Pi |
| **Tárolás** | USB pendrive (ESD-USB) |

> ⚠️ Az antenna iránya változtatható. A `csvkoord.py`-ban az `ANT_AZ` és `ANT_EL` értékeket kell frissíteni, ha az antenna iránya megváltozik.

---

## 📂 Adatfolyam

```
Raspberry Pi (hi.py)
    ↓  4 percenként CSV mentés
USB pendrive: /media/pi/ESD-USB/hydrogen/
    ↓  manuális másolás
Windows: C:\seti\hydrogen\
    ↓
csvkoord.py (galaktikus koordináták szerinti rendezés)
    ↓
C:\seti\mapdata\  (pl. l175_b+045\)
    ↓
csvavg.py (spektrum átlagolás)
    ↓
C:\seti\dataavg\average_spectrum.csv
    ↓
dbkep.py (képfeldolgozás / megjelenítés)
```

---

## 📥 Telepítés Raspberry Pi-re

### 1. Függőségek

```bash
sudo apt update
sudo apt install python3-pip git
pip3 install numpy
```

### 2. SoapySDR és RSP1A driver telepítése

```bash
# SoapySDR
sudo apt install libsoapysdr-dev soapysdr-tools

# SDRplay API (le kell tölteni a sdrplay.com-ról)
# https://www.sdrplay.com/downloads/
# Majd:
sudo ./SDRplay_RSP_API-ARM32-X.Y.Z.run

# SoapySDR SDRplay plugin
sudo apt install soapysdr-module-all
# vagy forrásból:
# https://github.com/pothosware/SoapySDRPlay
```

### 3. Kód letöltése

```bash
git clone https://github.com/Ha7at/raspberrypisetisdr.git
cd raspberrypisetisdr
```

### 4. Konfiguráció (`hi.py`)

A `hi.py` tetején található `CONFIG` részben állítható:

```python
CENTER_FREQ     = 1420.4058e6   # Hydrogen line [Hz]
SAMPLE_RATE     = 2e6           # 2 MHz sávszélesség
GAIN_DB         = 32            # Erősítés [dB]
FFT_BIN_HZ      = 2000          # FFT felbontás
INTEGRATIONS    = 24            # Integrációk száma
INTEGRATION_TIME = 10           # Integrációs idő [s]
OUTPUT_DIR      = "/media/pi/ESD-USB/hydrogen"
```

---

## ⚙️ Szoftver komponensek

### `hi.py` – Adatgyűjtés (Raspberry Pi)

- RSP1A SDR vevőn keresztül gyűjt spektrumdatokat
- Frekvencia: 1420,4058 MHz (hydrogen line)
- 4 percenként ment egy CSV fájlt (pl. `20260330_0747.csv`)
- Az adatokat USB pendrive-ra menti: `/media/pi/ESD-USB/hydrogen/`

**Futtatás:**
```bash
python3 hi.py
```

**CSV formátum:**
```
timestamp_utc,frequency_hz,power_db
2026-03-30T07:47:00+00:00,1419406250.0,-45.23
...
```

---

### `csvkoord.py` – Galaktikus koordináták szerinti rendezés (Windows)

- A `C:\seti\hydrogen\` mappából olvassa a CSV fájlokat
- Az antenna irányából kiszámítja a galaktikus koordinátákat (astropy)
- Galaktikus koordináták szerint mappákba rendezi az adatokat
- Pl.: `C:\seti\mapdata\l175_b+045\`
- Minden mappába egy `_info.json` metaadat fájl is kerül

**Konfiguráció (`csvkoord.py` tetején):**
```python
SOURCE_FOLDER = r"C:\seti\hydrogen"
DEST_FOLDER   = r"C:\seti\mapdata"
LOG_FILE      = r"C:\seti\csvkoord.log"

ANT_AZ    = 218   # Antenna azimut [°]
ANT_EL    = 70    # Antenna eleváció [°]
LAT       = 47.523
LON       = 19.325
```

**Futtatás:**
```bash
python csvkoord.py
```

---

### `csvavg.py` – Spektrum átlagolás (Windows)

- A `C:\seti\hydrogen\` mappából olvassa az összes CSV-t
- Frekvencia szerint csoportosít és átlagol
- Eredmény: `C:\seti\dataavg\average_spectrum.csv`

**Futtatás:**
```bash
python csvavg.py
```

---

### `dbkep.py` – Képfeldolgozás / megjelenítés (Windows)

- Az átlagolt spektrum adatokból képet generál

**Futtatás:**
```bash
python dbkep.py
```

---

## 🚀 Használati útmutató

### Lépésenkénti folyamat:

**1. Raspberry Pi – adatgyűjtés**
```bash
python3 hi.py
# Fut folyamatosan, 4 percenként ment egy CSV-t
```

**2. Pendrive cseréje / másolás Windowsra**
- A pendrive-ot csatlakoztasd a Windows PC-hez
- Másold a `hydrogen` mappa tartalmát `C:\seti\hydrogen\`-ba

**3. Windows – koordináta szerinti rendezés**
```bash
python csvkoord.py
# C:\seti\hydrogen\ → C:\seti\mapdata\
```

**4. Windows – spektrum átlagolás**
```bash
python csvavg.py
# C:\seti\hydrogen\ → C:\seti\dataavg\average_spectrum.csv
```

**5. Windows – megjelenítés**
```bash
python dbkep.py
```

---

## 📊 Adatstruktúra

```
C:\seti\
├── hydrogen\               ← hi.py kimenet (pendrive-ról másolva)
│   ├── 20260330_0747.csv
│   ├── 20260330_0751.csv
│   └── ...
├── mapdata\                ← csvkoord.py kimenet
│   ├── l175_b+045\
│   │   ├── _info.json
│   │   ├── 20260330_0747.csv
│   │   └── ...
│   └── ...
└── dataavg\                ← csvavg.py kimenet
    └── average_spectrum.csv
```

---

## 🛠️ Hibaelhárítás

| Hiba | Megoldás |
|------|----------|
| `SoapySDR: No devices found` | Ellenőrizd az RSP1A csatlakozást és a drivert |
| `No CSV file found` | Ellenőrizd, hogy a `C:\seti\hydrogen\` mappa nem üres |
| `astropy` import hiba | `pip install astropy` |
| `pandas` import hiba | `pip install pandas` |

---

## 📚 Források

- [SDRplay RSP1A](https://www.sdrplay.com/rsp1a/)
- [SoapySDR](https://github.com/pothosware/SoapySDR)
- [Hydrogen Line – Wikipedia](https://en.wikipedia.org/wiki/Hydrogen_line)
- [Astropy](https://www.astropy.org/)
- [SETI Institute](https://www.seti.org/)
- [Amateur Radio Astronomy](https://www.nrao.edu/)
