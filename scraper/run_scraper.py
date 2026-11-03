"""Command-line entry point to run the KickNow multi-city pitch and football association scraper."""

import os
import sys

# Ensure repository root is in python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import argparse
import time

from scraper.config import BFV_LEAGUE_QUERIES, CITIES
from scraper.bfv_scraper import scrape_bfv_data
from scraper.pitch_scraper import get_all_pitches
from scraper.osm_importer import get_multi_city_pitches
from scraper.fussball_de_scraper import scrape_all_cities_matches, scrape_all_cities_clubs
from scraper.matcher import connect_pitches_and_matches
from scraper.exporter import export_json, update_kicknow_data_js


def main():
    parser = argparse.ArgumentParser(
        description="KickNow Scraper: Scrapes pitches, clubs, and matches across Munich, Nuremberg, Berlin, Hamburg, Cologne, and Frankfurt."
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "offline"],
        default="quick",
        help="Scraping mode: 'quick' (top clubs, fast), 'full' (extensive clubs and municipal geodata), 'offline' (curated base only)."
    )
    parser.add_argument(
        "--max-clubs",
        type=int,
        default=None,
        help="Maximum number of BFV clubs to scrape schedule PDFs for."
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory to save JSON artifacts."
    )
    parser.add_argument(
        "--update-app",
        action="store_true",
        default=True,
        help="Automatically update kicknow/js/data.js with scraped data."
    )
    parser.add_argument(
        "--no-live-photon",
        action="store_true",
        help="Skip live Photon and municipal geodata queries."
    )

    args = parser.parse_args()
    start_time = time.time()
    print("=================================================================")
    print(f" KickNow Multi-City Scraper starting (Mode: {args.mode})")
    print("=================================================================")

    # 1. Scrape Munich + Multi-City Pitches (Nuremberg, Berlin, Hamburg, Cologne, Frankfurt)
    include_live = (args.mode != "offline") and not args.no_live_photon
    munich_pitches = get_all_pitches(include_live_photon=include_live, verbose=True)
    for p in munich_pitches:
        p.setdefault("city", "München")

    extra_cities = [k for k in CITIES.keys() if k != "munich"]
    multi_pitches = get_multi_city_pitches(city_keys=extra_cities, live_osm=(args.mode == "full" and include_live))
    pitches = munich_pitches + multi_pitches

    # 2. Scrape Clubs and Matches across Munich (BFV) and Regional Associations (BFV, BFV Berlin, HFV, FVM, HFV Hessen)
    if args.mode == "offline":
        print("[Scraper] Offline mode selected; loading curated regional clubs and schedules.")
        bfv_data = {"clubs": [], "matches": [], "venues": {}}
        regional_matches = scrape_all_cities_matches(city_keys=extra_cities, live=False)
        regional_clubs = scrape_all_cities_clubs(city_keys=extra_cities, live=False)
    else:
        max_clubs = args.max_clubs if args.max_clubs is not None else (12 if args.mode == "quick" else 30)
        bfv_data = scrape_bfv_data(queries=BFV_LEAGUE_QUERIES, max_clubs=max_clubs, verbose=True)
        regional_matches = scrape_all_cities_matches(city_keys=extra_cities, live=(args.mode == "full"))
        regional_clubs = scrape_all_cities_clubs(city_keys=extra_cities, live=(args.mode == "full"))

    all_matches = bfv_data["matches"] + regional_matches
    all_clubs = bfv_data["clubs"] + regional_clubs

    # 3. Match Venues & Connect Games to Pitches
    updated_pitches, stats = connect_pitches_and_matches(
        pitches=pitches,
        matches=all_matches,
        verbose=True
    )

    # 4. Export Artifacts
    os.makedirs(args.output_dir, exist_ok=True)
    export_json(updated_pitches, os.path.join(args.output_dir, "scraped_pitches.json"))
    export_json(updated_pitches, os.path.join(args.output_dir, "multi_city_pitches.json"))
    export_json(all_matches, os.path.join(args.output_dir, "bfv_matches.json"))
    export_json(all_clubs, os.path.join(args.output_dir, "bfv_clubs.json"))

    if args.update_app:
        target_js = "kicknow/js/data.js"
        update_kicknow_data_js(updated_pitches, target_data_js=target_js)

    elapsed = time.time() - start_time
    print("=================================================================")
    print(f" KickNow Multi-City Scraper finished in {elapsed:.2f}s")
    print(f" Total pitches (all 6 cities): {len(updated_pitches)}")
    print(f" Total clubs collected: {len(all_clubs)}")
    print(f" Total matches collected: {len(all_matches)}")
    print(f" Matched occupations: {stats.get('matched_matches', 0)}")
    print("=================================================================")


if __name__ == "__main__":
    main()
