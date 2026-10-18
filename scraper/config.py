"""Configuration for the KickNow Munich and Landkreis pitch scraper."""

# Geographic bounding box covering City of Munich and Landkreis München
BBOX = {
    "south": 47.95,
    "west": 11.35,
    "north": 48.33,
    "east": 11.85
}

# All 29 municipalities in Landkreis München
LANDKREIS_MUNICIPALITIES = [
    "Aschheim", "Aying", "Baierbrunn", "Brunnthal", "Feldkirchen",
    "Garching bei München", "Gräfelfing", "Grasbrunn", "Grünwald", "Haar",
    "Hohenbrunn", "Höhenkirchen-Siegertsbrunn", "Ismaning", "Kirchheim bei München",
    "Neubiberg", "Neuried", "Oberhaching", "Oberschleißheim", "Ottobrunn",
    "Planegg", "Pullach im Isartal", "Putzbrunn", "Sauerlach", "Schäftlarn",
    "Straßlach-Dingharting", "Taufkirchen", "Unterföhring", "Unterhaching",
    "Unterschleißheim"
]

# Munich city districts (central and remote / outer border)
MUNICH_DISTRICTS = [
    "Altstadt-Lehel", "Ludwigsvorstadt-Isarvorstadt", "Maxvorstadt", "Schwabing-West",
    "Au-Haidhausen", "Sendling", "Sendling-Westpark", "Schwanthalerhöhe",
    "Neuhausen-Nymphenburg", "Moosach", "Milbertshofen-Am Hart", "Schwabing-Freimann",
    "Bogenhausen", "Berg am Laim", "Trudering-Riem", "Ramersdorf-Perlach",
    "Obergiesing-Fasangarten", "Untergiesing-Harlaching", "Thalkirchen-Obersendling-Forstenried-Fürstenried-Solln",
    "Hadern", "Pasing-Obermenzing", "Aubing-Lochhausen-Langwied", "Allach-Untermenzing",
    "Feldmoching-Hasenbergl", "Laim"
]

# Targeted league club queries covering Regionalliga, Bayernliga, Landesliga, Bezirksliga, Kreisliga, Kreisklasse, A-Klasse
BFV_KEY_CLUBS = [
    "SpVgg Unterhaching", "SV Heimstetten", "FC Ismaning", "TSV Grünwald",
    "VfR Garching", "SV Pullach", "SV Aubing", "SpVgg Feldmoching",
    "FC Teutonia München", "TSV Großhadern", "TSV Neuried", "SV Planegg-Krailling",
    "TSV Ottobrunn", "TSV Haar", "FC Unterföhring", "FC Aschheim",
    "TSV Gräfelfing", "TSV Sauerlach", "TSV Brunnthal", "SV DJK Taufkirchen",
    "TSV Hohenbrunn-Riemerling", "SpVgg Höhenkirchen", "TSV Grasbrunn-Neukeferloh",
    "TSV Feldkirchen bei München", "TSV 1921 Schäftlarn", "SpFrd. 1948 Aying",
    "SV Lohhof", "FC Hertha München", "FC Wacker München", "FC Stern München",
    "SV Waldeck-Obermenzing", "SV Allach 1949", "TSV Moosach-Hartmannshofen",
    "SV München Laim", "DJK Pasing", "FC Phönix Schleißheim", "TSV Neubiberg-Ottobrunn"
]

# Search queries covering leagues, club categories, and geographic areas
BFV_LEAGUE_QUERIES = BFV_KEY_CLUBS + [
    # Municipalities in Landkreis München
    "Aschheim", "Aying", "Baierbrunn", "Brunnthal", "Feldkirchen",
    "Garching", "Gräfelfing", "Grasbrunn", "Grünwald", "Haar",
    "Hohenbrunn", "Höhenkirchen", "Ismaning", "Kirchheim",
    "Neubiberg", "Neuried", "Oberhaching", "Oberschleißheim", "Ottobrunn",
    "Planegg", "Pullach", "Putzbrunn", "Sauerlach", "Schäftlarn",
    "Straßlach", "Taufkirchen", "Unterföhring", "Unterhaching",
    "Unterschleißheim", "Heimstetten",
    # Outer and central Munich districts
    "Aubing", "Allach", "Feldmoching", "Hasenbergl", "Pasing", "Laim", "Hadern",
    "Solln", "Moosach", "Milbertshofen", "Freimann", "Trudering", "Perlach", "Riem",
    "Giesing", "Sendling", "Schwabing", "Neuhausen", "Lochhausen", "Obermenzing", "Untermenzing"
]

# Time slot parameters matching KickNow frontend (9 slots á 90 minutes)
SLOT_STARTS = [510, 600, 690, 780, 870, 960, 1050, 1140, 1230]
SLOT_LEN = 90

# Standard HTTP headers for requests
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}

# BFV API and site endpoints
BFV_BASE_URL = "https://www.bfv.de"
BFV_CLUB_SEARCH_URL = "https://www.bfv.de/partial/suche/vereinsprofile?query={query}"
BFV_SCHEDULE_PDF_URL = "https://service.bfv.de/rest/pdfexport/vereinsspiele?id={club_id}"

# Photon geocoder API endpoint
PHOTON_API_URL = "https://photon.komoot.io/api/"
