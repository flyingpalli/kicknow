"""Scraper for clubs and official matches from the Bavarian Football Association (BFV - bfv.de).

Supports both Munich (Upper Bavaria / Oberbayern) and Nuremberg (Middle Franconia / Mittelfranken).
"""

import os
import re
import sys
import time
import tempfile
import subprocess
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

from scraper.config import (
    BFV_BASE_URL,
    BFV_CLUB_SEARCH_URL,
    BFV_SCHEDULE_PDF_URL,
    BFV_LEAGUE_QUERIES,
    NUREMBERG_BFV_QUERIES,
    NUREMBERG_MUNICIPALITIES,
    HTTP_HEADERS,
    LANDKREIS_MUNICIPALITIES
)


def search_clubs(query: str, timeout: int = 10, city_key: str = "munich") -> List[Dict[str, str]]:
    """Search for football clubs on bfv.de matching the given query and region."""
    url = BFV_CLUB_SEARCH_URL.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error querying clubs for '{query}': {e}", file=sys.stderr)
        return []

    pattern = (
        r'<a\s+class="bfv-profile-teaser__card-link"\s+href="([^"]+)".*?'
        r'<h2 class="bfv-profile-teaser__title">([^<]+)</h2>.*?'
        r'<div class="bfv-profile-teaser__address">\s*<span>([^<]*)</span>\s*<span>([^<]*)</span>'
    )
    raw_clubs = re.findall(pattern, html, re.DOTALL)
    results = []

    for href, name, street, city in raw_clubs:
        name = name.strip()
        street = street.strip()
        city = city.strip()
        club_id = href.rstrip("/").split("/")[-1]

        if city_key == "nuremberg":
            plz_match = re.search(r"\b(90\d{3}|91\d{3})\b", city)
            is_nbg = (
                plz_match is not None
                or "Nürnberg" in city
                or "Nürnberg" in name
                or any(m.lower() in city.lower() for m in NUREMBERG_MUNICIPALITIES)
            )
            if is_nbg:
                results.append({
                    "id": club_id,
                    "name": name,
                    "street": street,
                    "city": city,
                    "region_city": "Nürnberg",
                    "association": "BFV",
                    "address": f"{street}, {city}" if street else city,
                    "url": urllib.parse.urljoin(BFV_BASE_URL, href)
                })
        else:
            # Filter: keep clubs in Munich area (PLZ 80xxx, 81xxx, 82xxx, 85xxx) or matching Landkreis
            plz_match = re.search(r"\b(80\d{3}|81\d{3}|82\d{3}|85\d{3})\b", city)
            is_munich_area = plz_match is not None or "München" in city or "München" in name
            is_landkreis = any(m.lower() in city.lower() for m in LANDKREIS_MUNICIPALITIES)

            if is_munich_area or is_landkreis:
                results.append({
                    "id": club_id,
                    "name": name,
                    "street": street,
                    "city": city,
                    "region_city": "München",
                    "association": "BFV",
                    "address": f"{street}, {city}" if street else city,
                    "url": urllib.parse.urljoin(BFV_BASE_URL, href)
                })

    return results


def fetch_club_schedule_pdf(club_id: str, timeout: int = 12) -> Optional[bytes]:
    """Download the official schedule PDF for a club from service.bfv.de."""
    url = BFV_SCHEDULE_PDF_URL.format(club_id=club_id)
    req = urllib.request.Request(url, headers=HTTP_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if len(data) > 1000:
                return data
    except Exception as e:
        print(f"Error fetching schedule for club {club_id}: {e}", file=sys.stderr)
    return None


def parse_schedule_pdf(pdf_bytes: bytes, club_name: str = "", city_name: str = "München") -> List[Dict[str, Any]]:
    """Parse the PDF text layout of a BFV schedule into structured matches."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(pdf_bytes)
        tf_path = tf.name

    try:
        txt = subprocess.check_output(["pdftotext", "-layout", tf_path, "-"]).decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error executing pdftotext: {e}", file=sys.stderr)
        txt = ""
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)

    matches = []
    lines = txt.splitlines()

    # Match row pattern: e.g. "ME  Kreisliga  18.10.2026  11:30  FC Teutonia Mün.  -  TSV Poing"
    match_row_re = re.compile(
        r"(?:ME|FS|MS|PO|PK|SP)?\s*([A-Za-z0-9\-/\.\s]+?)\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})\s+(.*?)\s+-\s+(.*)"
    )

    for i, line in enumerate(lines):
        line_clean = line.strip()
        m = match_row_re.search(line_clean)
        if not m:
            continue

        league = m.group(1).strip()
        date_str = m.group(2).strip()
        time_str = m.group(3).strip()
        home = m.group(4).strip()
        away = m.group(5).strip()

        # Convert date to YYYY-MM-DD
        d_parts = date_str.split(".")
        if len(d_parts) == 3:
            iso_date = f"{d_parts[2]}-{d_parts[1]}-{d_parts[0]}"
        else:
            iso_date = date_str

        # Convert time to minutes from midnight
        t_parts = time_str.split(":")
        minute_start = int(t_parts[0]) * 60 + int(t_parts[1]) if len(t_parts) == 2 else 0

        # Look for the venue in the subsequent lines (1 to 3 lines down)
        venue_name = "Sportanlage"
        venue_addr = ""
        surface = "Rasenplatz"

        for j in range(i + 1, min(i + 4, len(lines))):
            cand = lines[j].strip()
            if not cand or match_row_re.search(cand):
                continue
            if "," in cand or any(w in cand for w in ["BSA", "Sportanlage", "Platz", "Kunstrasen", "Weg", "Str."]):
                parts = [p.strip() for p in cand.split(",") if p.strip()]
                if parts:
                    venue_name = parts[0]
                    venue_addr = ", ".join(parts[1:])
                break

        # Detect surface from venue name or address
        v_full = f"{venue_name} {venue_addr}".lower()
        if "kunstrasen" in v_full:
            surface = "Kunstrasen"
        elif "hartplatz" in v_full or "tenne" in v_full or "asche" in v_full:
            surface = "Hartplatz"
        elif "asphalt" in v_full or "beton" in v_full:
            surface = "Asphalt"
        else:
            surface = "Rasenplatz"

        matches.append({
            "date": iso_date,
            "date_display": date_str,
            "time": time_str,
            "minute_start": minute_start,
            "home": home,
            "away": away,
            "league": league,
            "venue_name": venue_name,
            "venue_addr": venue_addr,
            "surface": surface,
            "reported_by_club": club_name,
            "association": "BFV",
            "city": city_name,
            "source": "bfv.de"
        })

    return matches


def scrape_bfv_data(
    queries: Optional[List[str]] = None,
    max_clubs: int = 35,
    verbose: bool = True,
    city_key: str = "munich"
) -> Dict[str, Any]:
    """Scrapes BFV clubs and extracts all their scheduled matches and venues."""
    city_name = "Nürnberg" if city_key == "nuremberg" else "München"
    if queries is None:
        queries = NUREMBERG_BFV_QUERIES if city_key == "nuremberg" else BFV_LEAGUE_QUERIES

    discovered_clubs = {}
    clubs_by_query = {}
    if verbose:
        print(f"[BFV Scraper ({city_name})] Searching clubs for {len(queries)} queries...")

    for q in queries:
        found = search_clubs(q, city_key=city_key)
        clubs_by_query[q] = found
        for c in found:
            if c["id"] not in discovered_clubs:
                discovered_clubs[c["id"]] = c
        time.sleep(0.08)

    all_clubs = list(discovered_clubs.values())
    if verbose:
        print(f"[BFV Scraper ({city_name})] Discovered {len(all_clubs)} unique clubs.")

    # Round-robin select clubs across queries to ensure broad geographic representation
    selected_clubs = []
    seen_ids = set()
    while len(selected_clubs) < max_clubs:
        added_in_round = False
        for q in queries:
            cands = [c for c in clubs_by_query.get(q, []) if c["id"] not in seen_ids]
            if cands and len(selected_clubs) < max_clubs:
                c = cands[0]
                seen_ids.add(c["id"])
                selected_clubs.append(c)
                added_in_round = True
        if not added_in_round:
            break
    if verbose:
        print(f"[BFV Scraper ({city_name})] Fetching match schedules for {len(selected_clubs)} clubs...")

    all_matches = []
    venues = {}

    for idx, club in enumerate(selected_clubs, 1):
        if verbose:
            print(f"  [{idx}/{len(selected_clubs)}] Fetching schedule for '{club['name']}'...")
        pdf_data = fetch_club_schedule_pdf(club["id"])
        if not pdf_data:
            continue

        matches = parse_schedule_pdf(pdf_data, club_name=club["name"], city_name=city_name)
        all_matches.extend(matches)

        for m in matches:
            v_key = m["venue_name"]
            if v_key not in venues:
                venues[v_key] = {
                    "name": m["venue_name"],
                    "address": m["venue_addr"],
                    "surface": m["surface"],
                    "city": city_name,
                    "matches_count": 0,
                    "host_clubs": set()
                }
            venues[v_key]["matches_count"] += 1
            if m["home"]:
                venues[v_key]["host_clubs"].add(m["home"])

        time.sleep(0.12)

    for v in venues.values():
        v["host_clubs"] = sorted(list(v["host_clubs"]))

    if verbose:
        print(f"[BFV Scraper ({city_name})] Scrape complete. Extracted {len(all_matches)} matches across {len(venues)} venues.")

    return {
        "clubs": all_clubs,
        "scraped_clubs": selected_clubs,
        "matches": all_matches,
        "venues": venues
    }


def scrape_nuremberg_bfv_data(max_clubs: int = 15, verbose: bool = True) -> Dict[str, Any]:
    """Convenience wrapper to scrape Nuremberg & Mittelfranken clubs and schedules via BFV."""
    return scrape_bfv_data(queries=NUREMBERG_BFV_QUERIES, max_clubs=max_clubs, verbose=verbose, city_key="nuremberg")
