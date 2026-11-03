"""Configuration for the KickNow multi-city pitch and football association scraper."""

# Geographic bounding box covering City of Munich and Landkreis München
BBOX = {
    "south": 47.95,
    "west": 11.35,
    "north": 48.33,
    "east": 11.85
}

# Multi-city presets for national coverage (Munich, Nuremberg, Berlin, Hamburg, Cologne, Frankfurt)
CITIES = {
    "munich": {
        "name": "München",
        "bbox": (47.95, 11.35, 48.33, 11.85),
        "center": (48.137154, 11.576124),
        "association": "BFV",
        "plz_prefixes": ("80", "81", "82", "85"),
        "osm_districts": ["München", "Landkreis München"],
        "photon_queries": [
            "Bezirkssportanlage München",
            "Bolzplatz München",
            "Bolzplatz Landkreis München"
        ]
    },
    "nuremberg": {
        "name": "Nürnberg",
        "bbox": (49.35, 10.95, 49.55, 11.25),
        "center": (49.452102, 11.076665),
        "association": "BFV",
        "plz_prefixes": ("90", "91"),
        "osm_districts": ["Nürnberg", "Fürth", "Erlangen"],
        "municipal_endpoints": {
            "arcgis_spielflaechen": (
                "https://geoportal.nuernberg.de/server/rest/services/"
                "Fachdaten/Spielflaechen/MapServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
            ),
            "sportservice_html": "https://www.nuernberg.de/internet/sportservice_nbg/sportstaetten_sportplaetze.html"
        },
        "photon_queries": [
            "Sportanlage Nürnberg",
            "Sportplatz Nürnberg",
            "Sportpark Nürnberg",
            "Bolzplatz Nürnberg",
            "Sportanlage Fürth"
        ]
    },
    "berlin": {
        "name": "Berlin",
        "bbox": (52.33, 13.08, 52.68, 13.76),
        "center": (52.520008, 13.404954),
        "association": "BFV_BERLIN",
        "plz_prefixes": ("10", "12", "13", "14"),
        "osm_districts": [
            "Mitte", "Friedrichshain-Kreuzberg", "Pankow", "Charlottenburg-Wilmersdorf",
            "Spandau", "Steglitz-Zehlendorf", "Tempelhof-Schöneberg", "Neukölln",
            "Treptow-Köpenick", "Marzahn-Hellersdorf", "Lichtenberg", "Reinickendorf"
        ],
        "municipal_endpoints": {
            "wfs_sportstandorte": (
                "https://gdi.berlin.de/services/wfs/sportstandorte?SERVICE=WFS&VERSION=2.0.0"
                "&REQUEST=GetFeature&TYPENAMES=sportstandorte:sportstandorte&COUNT=1085"
                "&outputFormat=application/json&SRSNAME=EPSG:4326"
            ),
            "wfs_spielplaetze": (
                "https://gdi.berlin.de/services/wfs/gruenanlagen?SERVICE=WFS&VERSION=2.0.0"
                "&REQUEST=GetFeature&TYPENAMES=gruenanlagen:spielplaetze&COUNT=1900"
                "&outputFormat=application/json&SRSNAME=EPSG:4326"
            )
        },
        "photon_queries": [
            "Sportanlage Berlin",
            "Stadion Berlin",
            "Bolzplatz Berlin"
        ]
    },
    "hamburg": {
        "name": "Hamburg",
        "bbox": (53.38, 9.70, 53.75, 10.35),
        "center": (53.551086, 9.993682),
        "association": "HFV",
        "plz_prefixes": ("20", "21", "22"),
        "osm_districts": [
            "Hamburg-Mitte", "Altona", "Eimsbüttel", "Hamburg-Nord",
            "Wandsbek", "Bergedorf", "Harburg"
        ],
        "municipal_endpoints": {
            "ogc_sportstaetten": "https://api.hamburg.de/datasets/v1/sportstaetten/collections/sportstaetten/items?f=json&limit=1000",
            "ogc_spielplaetze": "https://api.hamburg.de/datasets/v1/spielplaetze/collections/spielplaetze_hh/items?f=json&limit=500",
            "hfv_clubs_url": "https://www.hfv.de/vereine/"
        },
        "photon_queries": [
            "Sportanlage Hamburg",
            "Sportpark Hamburg",
            "Bolzplatz Hamburg"
        ]
    },
    "cologne": {
        "name": "Köln",
        "bbox": (50.83, 6.77, 51.08, 7.16),
        "center": (50.937531, 6.960279),
        "association": "FVM",
        "plz_prefixes": ("50", "51"),
        "osm_districts": [
            "Innenstadt", "Rodenkirchen", "Lindenthal", "Ehrenfeld", "Nippes",
            "Chorweiler", "Porz", "Kalk", "Mülheim"
        ],
        "municipal_endpoints": {
            "arcgis_spielangebote": (
                "https://geoportal.stadt-koeln.de/arcgis/rest/services/"
                "freizeit_natur_sport/spielangebote/MapServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json"
            ),
            "kunstrasen_csv": "https://www.offenedaten-koeln.de/sites/default/files/distribution/20200922_Kunstrasen_Prioritaetenliste.csv"
        },
        "photon_queries": [
            "Bezirkssportanlage Köln",
            "Sportanlage Köln",
            "Sportplatz Köln",
            "Stadion Köln",
            "Bolzplatz Köln"
        ]
    },
    "frankfurt": {
        "name": "Frankfurt",
        "bbox": (50.01, 8.47, 50.23, 8.80),
        "center": (50.110924, 8.682127),
        "association": "HFV_HESSEN",
        "plz_prefixes": ("60", "65"),
        "osm_districts": [
            "Innenstadt", "Bornheim", "Sachsenhausen", "Bockenheim", "Nordend",
            "Westend", "Ostend", "Gallus", "Niederrad", "Rödelheim", "Höchst"
        ],
        "municipal_endpoints": {
            "wfs_sportstaetten": (
                "https://geowebdienste.frankfurt.de/WFS_Sportstaetten?service=WFS&version=1.0.0"
                "&request=GetFeature&typename=Sportstaetten&srsName=EPSG:4326"
            )
        },
        "photon_queries": [
            "Sportanlage Frankfurt am Main",
            "Sportplatz Frankfurt am Main",
            "Bolzplatz Frankfurt am Main"
        ]
    }
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

# Municipalities and districts in the Nuremberg / Mittelfranken region (BFV)
NUREMBERG_MUNICIPALITIES = [
    "Nürnberg", "Fürth", "Erlangen", "Schwabach", "Zirndorf", "Stein",
    "Oberasbach", "Feucht", "Altdorf", "wendelstein", "Röthenbach", "Lauf"
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

# Search queries covering leagues, club categories, and geographic areas in Munich
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

# Targeted BFV queries for Nuremberg and Mittelfranken
NUREMBERG_BFV_QUERIES = [
    "1. FC Nürnberg", "TB Johannis 1888", "TSV Buch", "ASV Nürnberg Pfeil Phönix",
    "ATV 1873 Frankonia Nürnberg", "DJK Eibach", "Post SV Nürnberg", "SV Eyüp Sultan",
    "SpVgg Mögeldorf", "TSV Kornburg", "SGV Nürnberg-Fürth", "SV Laufamholz",
    "TSV Altenfurt", "TSV Fischbach", "DJK Falke Nürnberg", "SC Germania Nürnberg",
    "Tuspo Nürnberg", "ASC Boxdorf", "ASV Buchenbühl", "FC Bayern Kickers Nürnberg",
    "Nürnberg", "Fürth", "Erlangen", "Zirndorf", "Stein", "Feucht", "Schwabach"
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

# Fussball.de AJAX endpoints (DFBnet national platform for BFV Berlin, HFV Hamburg, FVM Cologne, HFV Hessen)
FUSSBALL_DE_CLUB_SEARCH_URL = "https://www.fussball.de/ajax.search.club.loadmore/-/max/100/mime-type/JSON/offset/{offset}/or/false/plz/{query}"
FUSSBALL_DE_CLUB_MATCHPLAN_URL = "https://www.fussball.de/ajax.club.matchplan/-/id/{club_id}/max/40/mime-type/JSON/mode/PAGE/offset/0/show-filter/false"

# Photon geocoder API endpoint
PHOTON_API_URL = "https://photon.komoot.io/api/"
