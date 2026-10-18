# KickNow Pitch & BFV Match Scraper

Ein modularer Web-Scraper für **KickNow**, der alle Fußballplätze in **München** und allen **29 Gemeinden des Landkreises München** erfasst, mit den offiziellen Spielansetzungen des **Bayerischen Fußball-Verbandes (BFV - bfv.de)** verknüpft und realistische Vereinstrainingspläne generiert.

## Übersicht & Funktionen

1. **Vollständige Platzabdeckung (Stadt & Landkreis München)**:
   - **Offizielle Plätze (60 Komplexe)**: Städtische Bezirkssportanlagen (BSA) in allen Münchner Stadtbezirken (inklusive Außenbezirken wie Aubing, Allach, Feldmoching, Hasenbergl, Moosach, Laim, Hadern, Solln) sowie die offiziellen Sportparks aller 29 Gemeinden im Landkreis München (z. B. Garching, Unterhaching, Ismaning, Grünwald, Heimstetten, Haar, Planegg, Ottobrunn, Sauerlach, Aying, Schäftlarn, Baierbrunn, Straßlach, Taufkirchen, Unterschleißheim).
   - **Inoffizielle Plätze (72+ Plätze)**: Kommunale Bolzplätze, Asphaltplätze, Schlacke-/Hartplätze (Tenne/Cinder), Bolzkäfige und Spielwiesen aus den Registern des Baureferats der Landeshauptstadt München und den Gemeindeverzeichnissen des Landkreises.
   - **Attribute**: Geokoordinaten (lat/lng), Belag (`Rasenplatz`, `Kunstrasen`, `Hartplatz`, `Asphalt`), Käfig-Status (`cage: true/false`), Maße, Adresse, Stadtteil / Landkreisgemeinde, Zugangsart (`Öffentlich` vs. `Vereinsgelände`), Ausstattung (`flutlicht`, `umkleide`, `toiletten`).

2. **Reale Trainingszeiten & Schulsport-Logik**:
   - **Offizielle Vereinsplätze**:
     - Vormittags (08:30 - 13:00 Uhr): Schulsport (Städt. Gymnasium / Realschule) auf städtischen Bezirkssportanlagen.
     - Spätnachmittag (16:00 - 19:00 Uhr): Strukturiertes Jugendtraining des jeweiligen Heimvereins (U11-U15 und U17/U19).
     - Haupttrainingszeit (19:00 - 20:30 Uhr): 1. Mannschaft (Herren / Damen) im festen Rhythmus (Di/Do bzw. Mo/Mi).
     - Spätabend (20:30 - 22:00 Uhr): 2. Mannschaft / Senioren (AH / Ü32).
     - Wochenende: Priorität für offizielle BFV-Punktspiele und Jugend-Ligaspieltage.
   - **Inoffizielle Bolzplätze & Käfige**:
     - **Kein Vereinstraining**: Öffentliche Bolzplätze sind frei von Vereinstraining.
     - Tagsüber frei zum Kicken, abends und am Wochenende Treffpunkt für Freizeitkicker und offene KickNow-Spiele.

3. **Verknüpfung mit bfv.de über alle Spielklassen**:
   - Durchsucht BFV-Vereinsprofile und -Ligen in München und allen 29 Landkreisgemeinden.
   - Lädt unverschlüsselte PDF-Spielpläne (`https://service.bfv.de/rest/pdfexport/vereinsspiele?id={club_id}`) herunter.
   - Deckt alle Spielklassen ab: Regionalliga Bayern, Bayernliga Süd, Landesliga, Bezirksliga, Kreisliga München, Kreisklasse, A-Klasse, B-Klasse sowie Junioren- und Pokalspiele.
   - Extrahiert Datum, Anstoßzeit, Heim- und Gastmannschaft, Liga und genaue Spielstätte mit Straßenadresse.

4. **Belegungs-Mapping (Occupations)**:
   - Verknüpft offizielle BFV-Spiele über Adressnormalisierung, Geocoding und Heimstätten-Mapping mit den erfassten Vereinsplätzen.
   - Weist Partien den 90-Minuten-Zeitslots von KickNow zu (08:30 bis 22:00 Uhr).
   - Hinterlegt den Heimverein beim jeweiligen Platz und blockiert Slots bei BFV-Spielen verlässlich vor Vereinstrainings.

5. **Präzise Geokoordinaten (Meterschärfe)**:
   - Alle 132 Plätze (60 offizielle Bezirkssportanlagen und Sportparks, 72 Bolzplätze und Käfige) wurden auf exakte Dach- bzw. Spielfeld-Zentroidkoordinaten referenziert.
   - Beseitigt frühere Ungenauigkeiten von 400 m bis über 4 km.
   - Persistente Koordinatentabelle in .

6. **Datenexport**:
   - `data/scraped_pitches.json`: Strukturierter JSON-Datensatz aller 132 Plätze inkl. Metadaten und Belegungen.
   - `data/bfv_matches.json`: Alle erfassten BFV-Partien (über 2.500 Partien) mit Spielort und Anstoßzeit.
   - `data/bfv_clubs.json`: Alle erfassten Vereine mit Anschrift und BFV-ID.
   - Direkte Aktualisierung von `kicknow/js/data.js` zur sofortigen Nutzung in der Web-App.

---

## Projektstruktur

```
scraper/
├── config.py           # Geografische Bounding-Box, alle 29 Gemeinden, Stadtbezirke, Ligen
├── bfv_scraper.py      # BFV-Vereinssuche und PDF-Spielplan-Parser für alle Ligen
├── pitch_scraper.py    # Erfassung offizieller BSAs & kommunaler Bolzplätze/Käfige
├── matcher.py          # Adressabgleich, Heimstätten-Mapping und Belegungszuweisung
├── exporter.py         # JSON-Export und Generierung von data.js mit Trainingslogik
├── run_scraper.py      # CLI-Ausführungstool
├── test_scraper.py     # Unit- und Integrationstests
└── README.md           # Dokumentation
```

---

## Verwendung

### 1. Tests ausführen
```bash
python3 -m unittest scraper/test_scraper.py
```

### 2. Schneller Scrape (Quick Mode)
Erfasst Plätze und Spielpläne der wichtigsten Vereine und aktualisiert direkt die App:
```bash
python3 scraper/run_scraper.py --mode quick --update-app
```

### 3. Umfangreicher Scrape (Full Mode)
Erfasst Vereine aus allen Ligen und Gemeinden:
```bash
python3 scraper/run_scraper.py --max-clubs 35 --update-app
```

### 4. Offline-Modus (ohne Netzwerkzugriff)
Nutzt den kuratierten Basisbestand ohne externe API-Aufrufe:
```bash
python3 scraper/run_scraper.py --mode offline --update-app
```
