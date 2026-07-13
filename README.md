hi.py Adatrögzitö raspberry pi sdr-re ami létrehozza a csv fájlokat 1 perces mért adatok, és rögziti
a raspberry pi pendrivera hydrogen mappába 
   fájlnevek az aktuális dátum idö.  A rögzitett frekvencia tartomámy 1418,605MHz-1424,604 MHz ig 
 A  mentett fájlok a már a feldolgozoszámitogépen a C:seti\usbdata mappába kell másolni .
 hydrogenf.py usbdata mappában lévö fájlokbol létrehozza a hydrogen mappába az 1420,406Mhz +- 1MHz adat fájlokat 
 aminek nevei megörzi az eredeti fájlnevet az idó adatokkal. 
 csvkoord.py hydrogen mappában lévö fájlokat za antenna beállitása alapján iránya és nyilásszög  rögzités ideje mapdata_radec mappában 
 létrehozza a az égi koordinátál szerinti mappát és bemásolja az oda valo fájlokat. 
 Közben még szüri a a vett adatokat hogy csak az éjszakai csendesebb idöben rögzitettek vettek kerüljenek be az almappákba. 
 csvavg.py átlagolja mapdata_radec almappáiban lévö fájlokat majd létrehozza a égi koordináták nevei alapján az átlag csv fájlokat.
 mapras.py csvavg és a baseline csv adatokbol megrajzolja az égbolt térképet. 
 plot.py csvavg és a baseline csv adatokbol létre hozza a hi line spectrogrammot. 
 baselineavg.py hydrogen mappábol át kell másolni azokat a fájlokat amik az égbolt leghidegg pontjához tartoznak ez adja
 baseline.csv aminek a szerepe hogy mért értékekböl kivonja az sdr és az erösitési lánc karakterisztikáját és az alapzajt. 
