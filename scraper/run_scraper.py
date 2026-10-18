"""Command-line entry point to run the KickNow pitch and BFV match scraper."""

import os
import sys

# Ensure repository root is in python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import argparse
import time

from scraper.bfv_scraper import scrape_bfv_data
from scraper.pitch_scraper import get_all_pitches
from scraper.matcher import connect_pitches_and_matches
from scraper.exporter import export_json, update_kicknow_data_js


def main():
    parser = argparse.ArgumentParser(
        description="KickNow Scraper: Scrapes soccer pitches in Munich & Landkreis München and attaches BFV club matches."
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "offline"],
        default="quick",
        help="Scraping mode: 'quick' (top clubs, fast), 'full' (extensive clubs and geodata), 'offline' (curated base only)."
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
        help="Skip live Photon geodata queries."
    )

    args = parser.parse_args()
    start_time = time.time()
    print("=================================================================")
    print(f" KickNow Scraper starting (Mode: {args.mode})")
    print("=================================================================")

    # 1. Scrape Pitches
    include_live = (args.mode != "offline") and not args.no_live_photon
    pitches = get_all_pitches(include_live_photon=include_live, verbose=True)

    # 2. Scrape BFV Matches and Clubs
    if args.mode == "offline":
        print("[BFV Scraper] Offline mode selected; skipping BFV network requests.")
        bfv_data = {"clubs": [], "matches": [], "venues": {}}
    else:
        max_clubs = args.max_clubs if args.max_clubs is not None else (12 if args.mode == "quick" else 30)
        from scraper.config import BFV_LEAGUE_QUERIES
        queries = BFV_LEAGUE_QUERIES
        bfv_data = scrape_bfv_data(queries=queries, max_clubs=max_clubs, verbose=True)

    # 3. Match Venues & Connect Games to Pitches
    updated_pitches, stats = connect_pitches_and_matches(
        pitches=pitches,
        matches=bfv_data["matches"],
        verbose=True
    )

    # 4. Export Artifacts
    os.makedirs(args.output_dir, exist_ok=True)
    export_json(updated_pitches, os.path.join(args.output_dir, "scraped_pitches.json"))
    export_json(bfv_data["matches"], os.path.join(args.output_dir, "bfv_matches.json"))
    export_json(bfv_data["clubs"], os.path.join(args.output_dir, "bfv_clubs.json"))

    if args.update_app:
        target_js = "kicknow/js/data.js"
        update_kicknow_data_js(updated_pitches, target_data_js=target_js)

    elapsed = time.time() - start_time
    print("=================================================================")
    print(f" KickNow Scraper finished in {elapsed:.2f}s")
    print(f" Total pitches: {len(updated_pitches)}")
    print(f" BFV matches collected: {len(bfv_data['matches'])}")
    print(f" Matched occupations: {stats.get('matched_matches', 0)}")
    print("=================================================================")


if __name__ == "__main__":
    main()
