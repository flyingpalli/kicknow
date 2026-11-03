"""Connects official pitches to clubs, scheduled matches, and realistic weekly training plans across all 6 cities."""

import re
from typing import List, Dict, Any, Optional, Tuple

from scraper.config import SLOT_STARTS, SLOT_LEN

# Well-known mapping of clubs to their official home ground BSA or Sportpark across all 6 cities
KNOWN_CLUB_HOME_GROUNDS: Dict[str, str] = {   '1. FC Köln': 'Parkplatz Bezirkssportanlage Bocklemünd',
    '1. FC Nürnberg': 'Eichenkreuz Sportanlage Marienberg',
    '1. FC Nürnberg II': 'Sportanlage Valznerweiher (1. FCN Jugend)',
    '1. FC PV Nord e.V.': 'Gustav-Böß-Sportanlage',
    '1. FC Schöneberg': 'Hanne-Sobek-Sportanlage',
    '1. FC Turbohorn': 'Sportanlage Gammer Weg 49a',
    '1. FC Union Köln': 'Bezirkssportanlage Nippes',
    '1. FFC Elbinsel': 'Sportanlage Brucknerstr. 24',
    '1. FSV Köln 99': 'Parkplatz Bezirkssportanlage',
    '1. Jugend-Fußball-Schule Köln': 'Bezirkssportanlage Rodenkirchen',
    '1. Rödelheimer Fc': 'Sportanlage Bundespolizei',
    '1.FC Besiktas': 'Sportanlage Auguststraße / Eingang Kleine Hamburger Str. 6',
    '1.FC Lübars': 'Sportanlage Chausseestraße',
    '1.FC Marzahn 94': 'Sportanlage Holzmarktstraße',
    '1.FC Novi Pazar 1895': 'Sportanlage Lehrter Straße - Poststadion',
    '1.FC Turbo United': 'Sportanlage Klinikweg',
    '1.FC Union Berlin': 'Sportanlage Cornelius-Fredricks-Str.',
    '1.FC Vikt. Sindlingen': 'Sportanlage Palleskestraße',
    '1.FC Wacker Lankwitz': 'Sportanlage NNW-Platz/Kokswiese',
    '1.FC Wilmersdorf': 'Sportanlage Neues Ufer',
    '1.FFV Spandau': 'Sportanlage Nordufer',
    '1.SV Ethio Addis FFM': 'Sportanlage Kleinfeld Walter-Richter-Halle',
    '1.Traber FC Mariendorf': 'Sportanlage Wullenweberstraße',
    'AFG Colonia': 'Bezirkssportanlage Chorweiler',
    'AGAGBHH': 'Sportanlage Vogesenstraße 11',
    'AKM Köln': 'Bezirkssportanlage Bocklemünd',
    'AS Nippes': 'Sportanlage Venloer Straße/Kolkrabenweg',
    'AS United': 'Sportanlage Uhlenhoffweg',
    'ASC Boxdorf': 'Sportparkgraben',
    'ASV Bergedorf': 'Sportanlage Rüschweg 12',
    'ASV Berlin': 'Kurt-Ritter-Sportplatz',
    'ASV Buchenbühl Nürnberg': 'Max-Morlock-Stadion',
    'ASV Nürnberg Pfeil Phönix': 'Sigena Sportanlage',
    'ATV 1873 Frankonia Nürnberg': 'Sportanlage Fischbach',
    'Adlershofer BC': 'Sportplatz Stade Napoléon',
    'Aimnation': 'Sportplatz Stralsunder Straße',
    'Alemannia 06 Haselhorst': 'Sportplatz Ungarnstraße',
    'Alsterbrüder': 'Sportanlage Königshütter Str. 21 (Dulsberg-Süd/überlassen an HSV)',
    'Alstertal-Langenhorn': 'Sportanlage Habichtstr. 14 (Schützenhof)',
    'Alt Nettelnburger SC': 'Sportanlage Langenfort 70a',
    'Altengamme': 'Sportanlage Elligersweg (Meister-Francke-Straße)',
    'Altenwerder': 'Sportanlage Marckmannstr. 125',
    'Altona 93': 'Sportanlage Anckelmannplatz 2f (Oskar-Keßlau-Sportanlage)',
    'Anadolu e.V. Köln': 'Jupp-Röhrig-Sportanlage',
    'Anadoluspor': 'Stadion Rehberge',
    'Artemis Sport Ffm': 'Sportanlage Sondershausenstraße 7',
    'Askania Coepenick': 'Werner-Kluge-Sportanlage',
    'Ataspor e.V. 74 Köln-Porz': 'Sportanlage Eythstraße',
    'Atlantik-97': 'Sportanlage Finksweg 82a',
    'Atletico Hamburg': 'Sportanlage Finkenau (überlassen an K.S. Polonia)',
    'Außensportanlage TV 1875 Sindlingen e.V.': 'Außensportanlage TV 1875 Sindlingen e.V.',
    'B.S.C. Reinickendorf': 'Lilli-Henoch-Sportplatz',
    'B.W. Berolina Mitte': 'Sportplatz Alt-Stralau',
    'BB U': 'Sportanlage Beethovenstr. 51 (überlassen an UH Adler)',
    'BCC': 'Sportplatz Hellweg',
    'BCM Moorweide': 'Sportanlage Tönsfeldtstr. 2 (Kreuzkirche)',
    'BSC SW Ffm': 'Sportanlage Internationale Schule Frankfurt',
    'BSG Edscha': 'Sportanlage Salzburger Weg',
    'Baris': 'Eichenkreuz-Sportanlage',
    'Beachfeld Eintracht Frankfurt e.V. Standort West': 'Sportanlage Beachfeld Eintracht Frankfurt e.V. '
                                                        'Standort West',
    'Bergedorf-West': 'Sportanlage Außenmühlenweg 23 a (Außenmühle)',
    'Bergstedt': 'Sportanlage Brandesstr. 9 (Wilstorfer Höh)',
    'Berlin Cricket Academy': 'Sportplatz Körtestraße',
    'Berlin Eagles Cricket Club': 'Sportplatz Virchowstraße',
    'Berlin Hilalspor': 'Sportplatz Waldeckpark',
    'Berliner AK 07': 'Poststadion Moabit (BERLINER AK 07)',
    'Bosna Köln': 'Parkplatz Sportanlage',
    'Bundeswehr': 'Sportanlage Holstenhofweg 85 (Douaumont-Kaserne)',
    'Bunte Liga Köln': 'Sportplatz am Bieselwald',
    'Bäng, Boom, Bäng Ballfieber': 'Sportplatz Brucknerstraße',
    'Bühnen-Sport-Club Köln 1961': 'Spielplatz Blücherpark IV/Am Sportplatz 1',
    'CfB Ford Köln-Niehl 09/52 e.V.': 'Am Sportplatz',
    'Cologne 11': 'Sportplatz Schulzentrum Wahn',
    'Cologne FC': 'Weiden Sportplatz',
    'Conc.Eschersheim': 'Sportanlage Johann Wolfgang Goethe-Universität',
    'Creu-Höchst': 'Sportanlage Hessenkolleg',
    'Croatia Köln e.V.': 'Sportplatzstraße',
    'DJK Eibach': 'Sportplatz DJK Eibach',
    'DJK Falke Nürnberg': 'Vereinsgaststätte Sportpark Ziegelstein',
    'DJK Fasangarten': 'Bezirkssportanlage Görzer Straße (Ramersdorf)',
    'DJK Grün-Weiß Nippes 1919 e.V.': 'Franz-Kremer-Stadion',
    'DJK Löwe Köln e.V. 1950': 'RheinEnergieSTADION',
    'DJK Nürnberg-Eibach': 'Am Sportplatz',
    'DJK Pasing': 'Bezirkssportanlage Am Durchblick (Pasing)',
    'DJK Roland Köln-West e.V.': 'Stadion',
    'DJK SW Griesheim': 'Sportanlage DFB-Campus',
    'DJK Zeilsheim': 'Sportanlage Bornheimer Hang',
    'Ditib Chorweiler': 'Sportplatzstraße',
    'Dreieich Panthers': 'Sportanlage Deutsche Bank Park Trainingsplätze',
    'ESV Blau-Gold Ffm': 'Sportanlage Römerstadtwiese',
    'ESV SpFrd. München-Neuaubing': 'Bezirkssportanlage Hans-Dietrich-Genscher-Straße',
    'Eimsbütteler TV': 'Sportpark Eimsbüttel (ETV Hamburg)',
    'Eintracht Frankfurt': 'Sportanlage Bonames - Nordpark',
    'FC  Croatia FFm': 'Sportanlage Louisa',
    'FC Alte Haide-DSC': 'Bezirkssportanlage Guerickestraße (Alte Haide)',
    'FC Aschheim': 'Sportpark Aschheim',
    'FC Dynamo Frankfurt': 'Sportanlage Phil.-Theol. Hochschule Sankt Georgen',
    'FC Ethio Addis Frankfurt': 'Deutsche Bank Park (Stadion)',
    'FC Fort.Ffm': 'Sportanlage Altenhöferallee',
    'FC Frankfurt City': 'Sportanlage Sportstätte Frankfurt-Sossenheim',
    'FC Hertha München': 'Bezirkssportanlage Surheimer Weg',
    'FC Hochbrück': 'Sportanlage Hochbrück (Garching)',
    'FC Ismaning': 'Sportpark Ismaning',
    'FC Neuhadern': 'Bezirkssportanlage Ludwig-Hunger-Straße (Hadern)',
    'FC Neuhadern München': 'Bezirkssportanlage Ludwig-Hunger-Straße (Hadern)',
    'FC Phönix Schleißheim': 'Sportgelände Theodor-Heuss-Straße Oberschleißheim',
    'FC Stern München': 'Bezirkssportanlage Feldbergstraße',
    'FC Teutonia München': 'Bezirkssportanlage Thusnelda-Lang-Brumann-Straße',
    'FC Unterföhring': 'Sportpark Bergstraße Unterföhring',
    'FC Wacker München': 'Bezirkssportanlage Demleitnerstraße',
    'FSV Frankfurt': 'Sportanlage am Bornheimer Hang (FSV Frankfurt)',
    'Fußball-Club St. Pauli von 1910 e.V.': 'Sportanlage Wendenstr. 164',
    'Hamburger Fußball Verband': 'Sportanlage Jenfelder Allee 70 a-c (LLZ HFV)',
    'Höchster THC e.V.': 'Sportanlage Höchster THC e.V.',
    'Post SV Nürnberg': 'Sportplatz am Fuchsloch',
    'Rot-Weiß Oberföhring': 'Bezirkssportanlage Englschalkinger Straße',
    'SC Fortuna Köln': 'Südstadion & Sportpark Süd (Fortuna Köln)',
    'SC Germania Nürnberg': 'Restaurant Sportpark Ebensee',
    'SC München': 'Bezirkssportanlage Agilolfingerstraße',
    'SGV Nürnberg-Fürth 1883': 'Sportpark Süd',
    'SV Allach 1949': 'Bezirkssportanlage Franz-Nißl-Straße (Allach)',
    'SV Aubing': 'Bezirkssportanlage Kronwinklerstraße (Aubing)',
    'SV Aubing München': 'Bezirkssportanlage Kronwinklerstraße (Aubing)',
    'SV Baierbrunn': 'Sport- und Bürgerzentrum Baierbrunn',
    'SV Blau-Gelb Frankfurt e.V.': 'Sportanlage SV Blau-Gelb Frankfurt e.V.',
    'SV DJK Taufkirchen': 'Sport- und Freizeitpark Köglweg Taufkirchen',
    'SV Eyüp Sultan Nürnberg': 'Sportplatz',
    'SV Fühlingen-Chorweiler': 'Sportanlage SV Fühlingen-Chorweiler',
    'SV Heimstetten': 'Sportpark Heimstetten',
    'SV Helfendorf': 'Sportgelände Helfendorf / Aying',
    'SV Laufamholz Nürnberg': 'Sportpark West',
    'SV Lohhof': 'Hans-Bayer-Stadion / Sportpark Lohhof',
    'SV München Laim': 'Bezirkssportanlage Agnes-Bernauer-Straße (Laim)',
    'SV Neuperlach': 'Bezirkssportanlage Bert-Brecht-Allee (Neuperlach)',
    'SV Orplid Niddainsel Frankfurt e.V.': 'Sportanlage SV Orplid Niddainsel Frankfurt e.V.',
    'SV Planegg-Krailling': 'Sportpark Planegg (Hofmarkstraße)',
    'SV Pullach': 'Sportplatz Gistelstraße Pullach',
    'SV Putzbrunn': 'Sportanlage Florianseck Putzbrunn',
    'SV Schwaig': 'Sportpark Pegnitztal - SV Schwaig',
    'SV Wacker': 'Sportanlage SV Wacker',
    'SV Waldeck-Obermenzing': 'Bezirkssportanlage Meyerbeerstraße (Obermenzing)',
    'SpFrd. 1948 Aying': 'Sportgelände Helfendorf / Aying',
    'SpVgg 1906 Haidhausen': 'Bezirkssportanlage Bauernfeindstraße',
    'SpVgg Feldmoching': 'Bezirkssportanlage Ebereschenstraße',
    'SpVgg Höhenkirchen': 'Sportplatzweg Höhenkirchen',
    'SpVgg Mögeldorf 2000 Nürnberg': 'Am Sportplatz',
    'SpVgg Unterhaching': 'Sportpark Unterhaching (uhlsport PARK & Grünau)',
    'Sportverein Eidelstedt von 1880 e.V.': 'Sportanlage Redingskamp 25 (SV Eidelstedt)',
    'TB Johannis 1888': 'Sportpark Johannis (TB Johannis 1888)',
    'TSG Niederrad e.V.': 'Sportanlage TSG Niederrad e.V.',
    'TSV 1921 Schäftlarn': 'Sportplatz Hohenschäftlarn',
    'TSV Allach 09': 'Bezirkssportanlage Franz-Nißl-Straße (Allach)',
    'TSV Altenfurt Nürnberg': 'Rangers Sportpark',
    'TSV Brunnthal': 'Sportanlage Jahnstraße Brunnthal',
    'TSV Buch Nürnberg': 'Sportanlage ASN Pfeil Phönix',
    'TSV Feldkirchen': 'Sportgelände Richthofenstraße Feldkirchen',
    'TSV Feldkirchen bei München': 'Sportgelände Richthofenstraße Feldkirchen',
    'TSV Feucht 04': 'TSV Feucht 04',
    'TSV Fischbach Nürnberg': 'Sportpark Nord',
    'TSV Grasbrunn-Neukeferloh': 'Sportpark Grasbrunn',
    'TSV Großhadern': 'Bezirkssportanlage Ludwig-Hunger-Straße (Hadern)',
    'TSV Gräfelfing': 'Sportanlage Hubert-Reißner-Straße Gräfelfing',
    'TSV Grünwald': 'Sportpark Grünwald',
    'TSV Haar': 'Sportpark Haar (Höglweg)',
    'TSV Hohenbrunn-Riemerling': 'Sportcampus Riemerling / Hohenbrunn',
    'TSV Kornburg': 'Sportpark Valznerweiher',
    'TSV Milbertshofen': 'Bezirkssportanlage Moosacher Straße',
    'TSV Moosach-Hartmannshofen': 'Bezirkssportanlage Franz-Mader-Straße (Moosach)',
    'TSV Neubiberg-Ottobrunn': 'Sportpark Neubiberg (Zwergerstraße)',
    'TSV Neuried': 'Sportpark Neuried',
    'TSV Oberhaching-Deisenhofen': 'Sportzentrum Deisenhofen / Oberhaching',
    'TSV Ochenbruck': 'Sportplatz TSV Ochenbruck',
    'TSV Ottobrunn': 'Sportanlage am Haidgraben Ottobrunn',
    'TSV Sauerlach': 'Hauptplatz TSV Sauerlach',
    'TSV Solln': 'Bezirkssportanlage Herterichstraße',
    'TSV Straßlach': 'Sportplatz Straßlach',
    'TSV Trudering': 'Bezirkssportanlage Feldbergstraße',
    'TSV Unterhaching': 'Sportpark Unterhaching (uhlsport PARK & Grünau)',
    'TV 1874 Bergen-Enkheim e.V.': 'Sportanlage TV 1874 Bergen-Enkheim e.V.',
    'Turn- und Sportverein Duwo 08 e.V.': 'Sportanlage Sthamerstr. 30 (TSV Duwo 08)',
    'Tuspo Nürnberg': 'Sportparkgraben',
    'Türkiyemspor Berlin': 'Sportanlage Katzbachstadion (Türkiyemspor Berlin)',
    'VfR Garching': 'Sportpark Stadion am See Garching'}


def normalize_str(s: str) -> str:
    """Normalize strings for robust fuzzy comparison."""
    if not s:
        return ""
    s = s.lower()
    s = s.replace("ß", "ss")
    s = s.replace("straße", "str").replace("strasse", "str").replace("str.", "str")
    s = s.replace("bezirkssportanlage", "bsa").replace("sportanlage", "sa").replace("sportpark", "sp")
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def find_best_slot_index(minute_start: int) -> int:
    """Find the closest 90-minute slot index for a given start time in minutes."""
    best_idx = 0
    min_diff = 999999
    for i, s_start in enumerate(SLOT_STARTS):
        diff = abs(s_start - minute_start)
        if diff < min_diff:
            min_diff = diff
            best_idx = i
    return best_idx


def match_venue_to_pitch(
    venue_name: str,
    venue_addr: str,
    pitches: List[Dict[str, Any]],
    city: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Match a venue name and address to an official pitch within the same city (never public Bolzplätze)."""
    norm_v_name = normalize_str(venue_name)
    norm_v_addr = normalize_str(venue_addr)

    # Only official sports facilities host association matches
    official_pitches = [p for p in pitches if p.get("access") != "Öffentlich"]
    if city:
        city_scoped = [p for p in official_pitches if not p.get("city") or p.get("city") == city]
        if city_scoped:
            official_pitches = city_scoped

    # 1. Match on street and house number
    if norm_v_addr:
        v_nums = re.findall(r"\d+", venue_addr)
        for p in official_pitches:
            norm_p_addr = normalize_str(p.get("address", ""))
            if not norm_p_addr:
                continue
            p_nums = re.findall(r"\d+", p.get("address", ""))
            if v_nums and p_nums and v_nums[0] == p_nums[0]:
                if norm_p_addr in norm_v_addr or norm_v_addr in norm_p_addr:
                    return p

    # 2. Match on venue name
    for p in official_pitches:
        norm_p_name = normalize_str(p.get("name", ""))
        if not norm_p_name:
            continue
        core_p = norm_p_name.replace("bsa", "").replace("sa", "").replace("sp", "")
        core_v = norm_v_name.replace("bsa", "").replace("sa", "").replace("sp", "")
        if len(core_p) >= 4 and len(core_v) >= 4:
            if core_p in core_v or core_v in core_p:
                return p

    # 3. Match on district / municipality name (excluding broad city names)
    city_names_norm = {"münchen", "muenchen", "nürnberg", "nuernberg", "berlin", "hamburg", "köln", "koeln", "frankfurt"}
    for p in official_pitches:
        d = p.get("district", "").lower()
        if len(d) >= 4 and d not in city_names_norm and d in norm_v_name:
            return p

    return None


def get_pitch_by_name(pitches: List[Dict[str, Any]], target_name: str) -> Optional[Dict[str, Any]]:
    """Lookup a pitch by its exact or normalized name."""
    norm_target = normalize_str(target_name)
    for p in pitches:
        if normalize_str(p.get("name", "")) == norm_target:
            return p
    return None


def connect_pitches_and_matches(
    pitches: List[Dict[str, Any]],
    matches: List[Dict[str, Any]],
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Connects matches to pitches and sets up realistic time slot occupations."""
    matched_count = 0
    unmatched_venues = set()
    club_pitch_map = {}

    # Step 1: Pre-assign known clubs to their official home grounds
    for club_name, pitch_name in KNOWN_CLUB_HOME_GROUNDS.items():
        p = get_pitch_by_name(pitches, pitch_name)
        if p and not p.get("club"):
            p["club"] = club_name
            club_pitch_map[club_name] = p["name"]

    for p in pitches:
        if p.get("club") and p.get("access") != "Öffentlich":
            club_pitch_map[p["club"]] = p["name"]

    # Step 2: Match scheduled association matches to pitches
    for m in matches:
        p = match_venue_to_pitch(m["venue_name"], m["venue_addr"], pitches, city=m.get("city"))
        if not p:
            host = m.get("home", "").strip()
            rep = m.get("reported_by_club", "").strip()
            if host in KNOWN_CLUB_HOME_GROUNDS:
                p = get_pitch_by_name(pitches, KNOWN_CLUB_HOME_GROUNDS[host])
            elif rep in KNOWN_CLUB_HOME_GROUNDS:
                p = get_pitch_by_name(pitches, KNOWN_CLUB_HOME_GROUNDS[rep])
            else:
                for cand_p in pitches:
                    if cand_p.get("access") != "Öffentlich" and cand_p.get("club") in (host, rep) and (host or rep):
                        p = cand_p
                        break

        if not p:
            unmatched_venues.add(f"{m['venue_name']} ({m['venue_addr']})")
            continue

        matched_count += 1
        slot_idx = find_best_slot_index(m["minute_start"])
        date_key = m["date"]

        occ = {
            "id": f"{p['id']}_{date_key}_{slot_idx}",
            "pitchId": p["id"],
            "date": date_key,
            "slot_idx": slot_idx,
            "start": SLOT_STARTS[slot_idx],
            "end": SLOT_STARTS[slot_idx] + SLOT_LEN,
            "time": m["time"],
            "type": "busy",
            "label": f"BFV-Spiel: {m['home']} – {m['away']} ({m['league']})",
            "home": m["home"],
            "away": m["away"],
            "league": m["league"],
            "reported_club": m.get("reported_by_club", "")
        }

        existing = [o for o in p["occupations"] if o["date"] == date_key and o["slot_idx"] == slot_idx]
        if not existing:
            p["occupations"].append(occ)

        host_club = m["home"]
        if host_club and not host_club.endswith(" 2") and not host_club.endswith(" 3") and not host_club.endswith(" II"):
            clean_host = host_club.strip()
        else:
            clean_host = m.get("reported_by_club", host_club).strip()

        if clean_host and not p.get("club"):
            p["club"] = clean_host
            club_pitch_map[clean_host] = p["name"]

    # Step 3: Enhance descriptions of pitches with associated clubs
    for p in pitches:
        if p.get("club") and "Heimspielstätte" not in p["desc"]:
            p["desc"] = f"Heimspielstätte von {p['club']}. " + p["desc"]

    stats = {
        "total_matches": len(matches),
        "matched_matches": matched_count,
        "unmatched_venues": list(unmatched_venues),
        "clubs_connected": len(club_pitch_map)
    }

    if verbose:
        print(f"[Matcher] Successfully matched {matched_count}/{len(matches)} matches to official pitches.")
        print(f"[Matcher] Connected {len(club_pitch_map)} football clubs to their home pitches.")

    return pitches, stats
