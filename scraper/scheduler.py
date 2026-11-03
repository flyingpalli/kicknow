"""Automated nightly ingestion scheduler (03:00 cron / Celery Beat compatible).

Refreshes soccer pitches, clubs, and upcoming weekly match assignments across all supported German cities
(Munich, Nuremberg, Berlin, Hamburg, Cologne, Frankfurt) and syncs to JSON artifacts and database.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from scraper.config import CITIES
from scraper.pitch_scraper import get_all_pitches
from scraper.osm_importer import get_multi_city_pitches
from scraper.fussball_de_scraper import scrape_all_cities_matches, scrape_all_cities_clubs
from scraper.matcher import connect_pitches_and_matches
from scraper.exporter import export_json, update_kicknow_data_js

logger = logging.getLogger("kicknow.scheduler")

NIGHTLY_CRON_SCHEDULE = "0 3 * * *"  # Nightly at 03:00


def run_nightly_ingestion(
    live_network: bool = False,
    output_dir: str = "data",
    update_js: bool = False,
    city_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Execute a complete multi-city pitch, club, and schedule ingestion pass."""
    started_at = datetime.utcnow().isoformat()
    t0 = time.time()

    # 1. Gather Munich base pitches (132 verified pitches) + multi-city pitches (250 verified pitches)
    munich_pitches = get_all_pitches(include_live_photon=live_network, verbose=False)
    for p in munich_pitches:
        p.setdefault("city", "München")

    extra_cities = [k for k in (city_keys or list(CITIES.keys())) if k != "munich"]
    multi_pitches = get_multi_city_pitches(city_keys=extra_cities, live_osm=live_network)

    all_pitches = munich_pitches + multi_pitches

    # 2. Gather regional matches and clubs
    regional_matches = scrape_all_cities_matches(city_keys=extra_cities, live=live_network)
    regional_clubs = scrape_all_cities_clubs(city_keys=extra_cities, live=live_network)

    # 3. Match venues and resolve slot conflicts
    updated_pitches, match_stats = connect_pitches_and_matches(
        pitches=all_pitches,
        matches=regional_matches,
        verbose=False
    )

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        export_json(updated_pitches, os.path.join(output_dir, "multi_city_pitches.json"))

    if update_js:
        update_kicknow_data_js(updated_pitches)

    elapsed = round(time.time() - t0, 3)
    report = {
        "status": "success",
        "cron": NIGHTLY_CRON_SCHEDULE,
        "started_at": started_at,
        "elapsed_sec": elapsed,
        "cities_processed": ["munich"] + extra_cities,
        "total_pitches": len(updated_pitches),
        "munich_pitches": len(munich_pitches),
        "multi_city_pitches": len(multi_pitches),
        "clubs_processed": len(regional_clubs),
        "matches_processed": len(regional_matches),
        "matched_occupations": match_stats.get("matched_matches", 0),
        "clubs_connected": match_stats.get("clubs_connected", 0)
    }
    logger.info("Nightly ingestion completed: %s", report)
    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_nightly_ingestion(live_network=False, output_dir="data", update_js=False)
    print(f"[Scheduler] Completed run: {result}")
