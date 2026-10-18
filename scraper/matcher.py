"""Connects official pitches to BFV clubs, scheduled matches, and realistic weekly training plans."""

import re
from typing import List, Dict, Any, Optional, Tuple

from scraper.config import SLOT_STARTS, SLOT_LEN

# Well-known mapping of clubs to their official home ground BSA or Sportpark
KNOWN_CLUB_HOME_GROUNDS = {
    "TSV Grünwald": "Sportpark Grünwald",
    "SV Heimstetten": "Sportpark Heimstetten",
    "FC Ismaning": "Sportpark Ismaning",
    "SV Pullach": "Sportplatz Gistelstraße Pullach",
    "TSV 1921 Schäftlarn": "Sportplatz Hohenschäftlarn",
    "TSV Sauerlach": "Hauptplatz TSV Sauerlach",
    "SpFrd. 1948 Aying": "Sportgelände Helfendorf / Aying",
    "SV Helfendorf": "Sportgelände Helfendorf / Aying",
    "VfR Garching": "Sportpark Stadion am See Garching",
    "FC Hochbrück": "Sportanlage Hochbrück (Garching)",
    "SpVgg Unterhaching": "Sportpark Unterhaching (uhlsport PARK & Grünau)",
    "TSV Unterhaching": "Sportpark Unterhaching (uhlsport PARK & Grünau)",
    "SV Lohhof": "Hans-Bayer-Stadion / Sportpark Lohhof",
    "FC Teutonia München": "Bezirkssportanlage Thusnelda-Lang-Brumann-Straße",
    "FC Hertha München": "Bezirkssportanlage Surheimer Weg",
    "FC Wacker München": "Bezirkssportanlage Demleitnerstraße",
    "SV Aubing": "Bezirkssportanlage Kronwinklerstraße (Aubing)",
    "SV Aubing München": "Bezirkssportanlage Kronwinklerstraße (Aubing)",
    "ESV SpFrd. München-Neuaubing": "Bezirkssportanlage Hans-Dietrich-Genscher-Straße",
    "SpVgg Feldmoching": "Bezirkssportanlage Ebereschenstraße",
    "SV Allach 1949": "Bezirkssportanlage Franz-Nißl-Straße (Allach)",
    "TSV Allach 09": "Bezirkssportanlage Franz-Nißl-Straße (Allach)",
    "TSV Großhadern": "Bezirkssportanlage Ludwig-Hunger-Straße (Hadern)",
    "FC Neuhadern": "Bezirkssportanlage Ludwig-Hunger-Straße (Hadern)",
    "FC Neuhadern München": "Bezirkssportanlage Ludwig-Hunger-Straße (Hadern)",
    "TSV Moosach-Hartmannshofen": "Bezirkssportanlage Franz-Mader-Straße (Moosach)",
    "SV München Laim": "Bezirkssportanlage Agnes-Bernauer-Straße (Laim)",
    "SV Waldeck-Obermenzing": "Bezirkssportanlage Meyerbeerstraße (Obermenzing)",
    "DJK Pasing": "Bezirkssportanlage Am Durchblick (Pasing)",
    "TSV Solln": "Bezirkssportanlage Herterichstraße",
    "TSV Milbertshofen": "Bezirkssportanlage Moosacher Straße",
    "SC München": "Bezirkssportanlage Agilolfingerstraße",
    "FC Stern München": "Bezirkssportanlage Feldbergstraße",
    "TSV Trudering": "Bezirkssportanlage Feldbergstraße",
    "SV Neuperlach": "Bezirkssportanlage Bert-Brecht-Allee (Neuperlach)",
    "DJK Fasangarten": "Bezirkssportanlage Görzer Straße (Ramersdorf)",
    "FC Aschheim": "Sportpark Aschheim",
    "TSV Feldkirchen": "Sportgelände Richthofenstraße Feldkirchen",
    "TSV Feldkirchen bei München": "Sportgelände Richthofenstraße Feldkirchen",
    "TSV Haar": "Sportpark Haar (Höglweg)",
    "TSV Gräfelfing": "Sportanlage Hubert-Reißner-Straße Gräfelfing",
    "TSV Neuried": "Sportpark Neuried",
    "TSV Ottobrunn": "Sportanlage am Haidgraben Ottobrunn",
    "SV Planegg-Krailling": "Sportpark Planegg (Hofmarkstraße)",
    "SV Putzbrunn": "Sportanlage Florianseck Putzbrunn",
    "TSV Straßlach": "Sportplatz Straßlach",
    "SV DJK Taufkirchen": "Sport- und Freizeitpark Köglweg Taufkirchen",
    "FC Unterföhring": "Sportpark Bergstraße Unterföhring",
    "TSV Hohenbrunn-Riemerling": "Sportcampus Riemerling / Hohenbrunn",
    "SpVgg Höhenkirchen": "Sportplatzweg Höhenkirchen",
    "TSV Grasbrunn-Neukeferloh": "Sportpark Grasbrunn",
    "TSV Brunnthal": "Sportanlage Jahnstraße Brunnthal",
    "TSV Oberhaching-Deisenhofen": "Sportzentrum Deisenhofen / Oberhaching",
    "SV Baierbrunn": "Sport- und Bürgerzentrum Baierbrunn",
    "FC Phönix Schleißheim": "Sportgelände Theodor-Heuss-Straße Oberschleißheim",
    "TSV Neubiberg-Ottobrunn": "Sportpark Neubiberg (Zwergerstraße)",
    "FC Alte Haide-DSC": "Bezirkssportanlage Guerickestraße (Alte Haide)",
    "SpVgg 1906 Haidhausen": "Bezirkssportanlage Bauernfeindstraße",
    "Rot-Weiß Oberföhring": "Bezirkssportanlage Englschalkinger Straße"
}


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
    pitches: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Match a BFV venue name and address to an official pitch (never public Bolzplätze)."""
    norm_v_name = normalize_str(venue_name)
    norm_v_addr = normalize_str(venue_addr)

    # Only official sports facilities host BFV matches
    official_pitches = [p for p in pitches if p.get("access") != "Öffentlich"]

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

    # 3. Match on municipality name for suburban Sportparks
    for p in official_pitches:
        d = p.get("district", "").lower()
        if len(d) >= 4 and d in norm_v_name:
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

    # Step 2: Match scheduled BFV matches to pitches
    for m in matches:
        p = match_venue_to_pitch(m['venue_name'], m['venue_addr'], pitches)
        if not p:
            # Fallback: check if host club has a known home ground
            host = m.get("home", "").strip()
            if host in KNOWN_CLUB_HOME_GROUNDS:
                p = get_pitch_by_name(pitches, KNOWN_CLUB_HOME_GROUNDS[host])
            elif m.get("reported_by_club", "").strip() in KNOWN_CLUB_HOME_GROUNDS:
                p = get_pitch_by_name(pitches, KNOWN_CLUB_HOME_GROUNDS[m["reported_by_club"].strip()])

        if not p:
            unmatched_venues.add(f"{m['venue_name']} ({m['venue_addr']})")
            continue

        matched_count += 1
        slot_idx = find_best_slot_index(m["minute_start"])
        date_key = m["date"]

        occ = {
            "id": f"{p['id']}_{date_key}_{slot_idx}",
            "pitchId": p['id'],
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

        # Prevent duplicate occupations for the same pitch, date, and slot
        existing = [o for o in p["occupations"] if o["date"] == date_key and o["slot_idx"] == slot_idx]
        if not existing:
            p["occupations"].append(occ)

        # Associate club to pitch if not already set
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
        if p.get("club") and "Heimspielstätte" not in p['desc']:
            p['desc'] = f"Heimspielstätte von {p['club']}. " + p['desc']

    stats = {
        "total_matches": len(matches),
        "matched_matches": matched_count,
        "unmatched_venues": list(unmatched_venues),
        "clubs_connected": len(club_pitch_map)
    }

    if verbose:
        print(f"[Matcher] Successfully matched {matched_count}/{len(matches)} BFV matches to official pitches.")
        print(f"[Matcher] Connected {len(club_pitch_map)} football clubs to their home pitches.")

    return pitches, stats
