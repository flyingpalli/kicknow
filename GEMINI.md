# KickNow Repository Context and Architecture

## Project Overview

KickNow is a mobile web application for soccer players in Munich. The application helps users find football pitches, check real-time availability, join open matches, and reserve slots.

The web client runs as a client-side single-page application. It uses plain HTML, CSS custom properties, and vanilla JavaScript. It renders maps with MapLibre GL JS using custom vector styles, with Leaflet available as a fallback.

```
kicknow/
├── assets/                # App icons and branding assets
├── css/                   # Stylesheets and visual design tokens
├── js/                    # Application logic, static data, and icon definitions
├── server/                # Local development server and network scripts
├── vendor/                # Vendored libraries (MapLibre GL JS, Leaflet)
├── KickNow starten.bat    # Windows server launcher
├── Netzwerk einrichten... # Windows firewall configuration
├── index.html             # Main entry point and shell structure
├── manifest.webmanifest   # PWA manifest
└── start.sh               # Shell script for Unix environments
data/                      # Scraped raw data, coordinate lookup tables, and BFV datasets
scraper/                   # Scraper scripts, matcher, and app exporter
```

## Detailed File Catalog

### Root Directory

- `GEMINI.md`: Context file documenting repository structure, file roles, and system architecture.
- `KickNow App-Designsystem und Platzsuche.png`: Design board showing typography, color tokens, and search UI components.
- `KickNow Fußballplatz-App Designboard.png`: Moodboard and reference layout for the mobile interface.
- `One Pager Fußballplatz-App.docx`: Product specification document in Microsoft Word format.
- `One Pager Fußballplatz-App.pdf`: Product specification document in PDF format.
- `dings.png`: Visual design asset showing UI components.
- `kicknow-logo.svg`: Vector logo for the KickNow brand.
- `main.png`: Visual target for the primary map screen and the bottom sheet.
- `pitch.png`: Visual target for the pitch card preview component.
- `pitch_detail.png`: Visual target for the pitch details page and the booking calendar.
- `trustedFolders.json`: Configuration for editor workspace trust.

### Data Directory (`data/`)

- `data/bfv_clubs.json`: Bavarian Football Association (BFV) club records for Munich and Landkreis municipalities. Contains club IDs, official club names, home ground assignments, and league tags.
- `data/bfv_matches.json`: Scheduled matches and league fixtures across Munich and suburban districts. Contains kick-off times, participating teams, league designations, and venue addresses.
- `data/precise_pitch_coordinates.json`: Master lookup table containing meter-accurate WGS84 rooftop and centroid coordinates for all 132 pitch complexes. Prevents geographic drift and district center snapping.
- `data/scraped_pitches.json`: Extracted dataset of 132 soccer pitches across Munich and all 29 Landkreis municipalities. Contains surface types, cage attributes, pitch dimensions, amenities, home clubs, and linked BFV match occupations.

### Web Application Core (`kicknow/`)

- `kicknow/index.html`: Entry HTML document. Configures viewport, loads fonts, declares app shell structure, and mounts scripts.
- `kicknow/manifest.webmanifest`: Progressive Web App (PWA) manifest. Controls app title, standalone display mode, theme colors, and home screen icon definitions.
- `kicknow/start.sh`: Shell script for macOS and Linux. Detects active local network IP addresses, starts a Python HTTP server on port 8080, and prints device connection URLs.
- `kicknow/KickNow starten.bat`: Windows batch script. Launches `server/server.ps1` in PowerShell with execution policy bypass.
- `kicknow/Netzwerk einrichten (einmalig).bat`: Windows batch wrapper. Runs `server/setup-network.ps1` with administrator privileges.

### Server and Network (`kicknow/server/`)

- `kicknow/server/server.py`: Python static file HTTP server. Emits strict HTTP headers (`no-cache`, `no-store`, `must-revalidate`) to prevent stale assets on mobile devices.
- `kicknow/server/server.ps1`: Pure PowerShell HTTP listener. Serves static files on Windows systems without external runtimes.
- `kicknow/server/setup-network.ps1`: Windows network setup script. Adds URL reservations and opens a firewall rule for local subnet devices.

### Styling (`kicknow/css/`)

- `kicknow/css/app.css`: Primary stylesheet. Contains CSS variables, typography, layout rules, bottom sheet animations, card components, search dropdown styles, and map control customizations.

### Application Logic (`kicknow/js/`)

- `kicknow/js/app.js`: Main client controller. Manages application state, screen navigation, MapLibre GL map setup, fallback Leaflet rendering, user location tracking, search filtering, pitch selection, reservations, and match chats.
- `kicknow/js/art.js`: Procedural graphic generator. Renders inline SVG icons, pitch banners, terrain textures, and player avatars.
- `kicknow/js/data.js`: Mock and static data module. Provides 132 pitch objects, Munich district coordinates, seed players, reviews, and dynamic occupancy slot generation based on BFV schedules.
- `kicknow/js/data.backup.js`: Backup copy of an earlier version of `data.js`.

### Visual Assets (`kicknow/assets/`)

- `kicknow/assets/icon-180.png`: High-resolution Apple Touch Icon for iOS home screen bookmarks.
- `kicknow/assets/icon-192.png`: Standard PWA app icon for Android and web launchers.
- `kicknow/assets/icon-512.png`: High-resolution PWA splash icon.
- `kicknow/assets/logo.svg`: Vector logo used in the header bar and splash screen.

### Third-Party Vendors (`kicknow/vendor/`)

- `kicknow/vendor/maplibre/maplibre-gl.js`: Vendored MapLibre GL JS library v4.7.1 for hardware-accelerated vector map rendering.
- `kicknow/vendor/maplibre/maplibre-gl.css`: Default stylesheet for MapLibre controls, attributions, and map canvas.
- `kicknow/vendor/maplibre/kicknow-style.js`: JavaScript export of the KickNow vector map style. Defines tile sources, ivory background fill, light green parks, and muted road networks.
- `kicknow/vendor/maplibre/kicknow-style.json`: JSON format of the KickNow custom vector map style.
- `kicknow/vendor/maplibre/positron.json`: Clean OpenMapTiles Positron style definition for vector tile basemaps.
- `kicknow/vendor/leaflet/leaflet.js`: Vendored Leaflet v1.9.4 library. Acts as a lightweight raster fallback for older devices or restricted WebGL contexts.
- `kicknow/vendor/leaflet/leaflet.css`: Default stylesheet for Leaflet markers and controls.

### Data Acquisition (`scraper/`)

- `scraper/config.py`: Central configuration module. Defines geographical bounding boxes, Munich city district mappings, the 29 Landkreis München municipalities, BFV league query parameters, and export paths.
- `scraper/pitch_scraper.py`: Primary pitch discovery and geocoding engine. Gathers 60 official facilities and 72 public Bolzplätze, incorporates rooftop coordinate overrides, and handles deduplication.
- `scraper/bfv_scraper.py`: BFV club and schedule extraction engine. Scrapes club directories across Munich leagues, fetches PDF match reports via the BFV REST API, and parses match schedules.
- `scraper/matcher.py`: Venue and schedule matching module. Normalizes venue addresses, resolves club home pitch relationships, maps BFV games to KickNow 90-minute time slots, and flags pitch occupancy.
- `scraper/exporter.py`: Data transformation and export engine. Serializes scraped records into JSON datasets under `data/`, synthesizes realistic club training schedules, and writes the production `kicknow/js/data.js` file.
- `scraper/run_scraper.py`: Command-line orchestration tool. Provides quick, full, and offline modes, along with direct application update flags.
- `scraper/test_scraper.py`: Automated test suite. Validates venue schema compliance, coordinate bounds, geocoding precision, BFV parsing, and schedule consistency.
- `scraper/README.md`: Technical documentation for the scraper subsystem. Details architecture, scheduling rules, and CLI invocation commands.

## Runtime Architecture and Data Flow

### 1. Bootstrapping
When `index.html` loads, the browser downloads vendor libraries, styles, and scripts. `app.js` initializes `state` from `localStorage` or defaults from `data.js`.

### 2. Map Initialization
`app.js` mounts a MapLibre GL map into `#map-canvas`. It applies the custom style from `vendor/maplibre/kicknow-style.js`. If MapLibre fails, `app.js` falls back to Leaflet.

### 3. Search and Filtering
The top search bar takes district names or pitch keywords. The suggestion box displays matching Munich boroughs and pitches. Tapping a borough shifts the search radius to that area. Tapping a pitch zooms the map directly to that pitch and opens its preview card.

### 4. Interactive Bottom Sheet
The bottom sheet supports dragging between collapsed, normal, and expanded states. It lists nearby pitches, current slot status (frei, belegt, spiel), and distance from the active center point.

### 5. Local State Persistence
Reservations, newly created pickup games, ratings, and favorites persist in browser `localStorage`. Resetting the demo from the profile screen restores default data.

### 6. Pitch Ingestion and Precision Geocoding Pipeline
The scraper extracts pitches from municipal sports office registers, district sports facilities, and public playground records. The pipeline applies verified rooftop coordinates from `data/precise_pitch_coordinates.json` to prevent positional inaccuracies. Each record receives surface attributes, cage status, dimensions, and amenities.

### 7. BFV League Match Integration
The scraper crawls BFV club listings across all competitive tiers in Munich and surrounding municipalities. It downloads official PDF schedules from the BFV service endpoint. The matcher maps team schedules to specific home grounds, reserving slots for league fixtures.

### 8. Realistic Occupancy and Training Schedule Model
The exporter synthesizes realistic weekly occupancy schedules based on pitch classification. Official club facilities host morning school sports, afternoon youth squads, evening senior squad training, and weekend league games. Public Bolzplätze and cages remain open without club reservations, serving casual pickup matches.
