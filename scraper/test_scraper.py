"""Unit and integration tests for the KickNow scraper."""

import unittest
from scraper.config import BBOX, SLOT_STARTS, LANDKREIS_MUNICIPALITIES
from scraper.matcher import normalize_str, find_best_slot_index, match_venue_to_pitch, connect_pitches_and_matches
from scraper.pitch_scraper import get_all_pitches, haversine_km
from scraper.exporter import update_kicknow_data_js


class TestKickNowScraper(unittest.TestCase):

    def test_config(self):
        self.assertGreater(BBOX["north"], BBOX["south"])
        self.assertGreater(BBOX["east"], BBOX["west"])
        self.assertEqual(len(SLOT_STARTS), 9)
        self.assertIn("Garching bei München", LANDKREIS_MUNICIPALITIES)
        self.assertIn("Unterhaching", LANDKREIS_MUNICIPALITIES)

    def test_haversine(self):
        # Distance between Marienplatz (48.1371, 11.5754) and Garching (48.2489, 11.6528) is ~13.7 km
        dist = haversine_km(48.1371, 11.5754, 48.2489, 11.6528)
        self.assertAlmostEqual(dist, 13.7, delta=1.5)

    def test_normalize_str(self):
        self.assertEqual(normalize_str("Surheimer Weg 3"), "surheimerweg3")
        self.assertEqual(normalize_str("Thusnelda-Lang-Brumann-Str. 14"), normalize_str("Thusnelda-Lang-Brumann-Straße 14"))
        self.assertEqual(normalize_str("Bezirkssportanlage Feldbergstraße"), normalize_str("BSA Feldbergstr."))

    def test_find_best_slot_index(self):
        # 11:30 = 690 minutes -> Slot index 2
        self.assertEqual(find_best_slot_index(690), 2)
        # 14:30 = 870 minutes -> Slot index 4
        self.assertEqual(find_best_slot_index(870), 4)
        # 09:00 = 540 minutes -> Closest is 08:30 (510) or 10:00 (600) -> Slot index 0 or 1
        self.assertIn(find_best_slot_index(540), [0, 1])

    def test_pitch_scraper_registry(self):
        pitches = get_all_pitches(include_live_photon=False, verbose=False)
        self.assertGreaterEqual(len(pitches), 40)
        
        # Check required fields
        required_keys = ["id", "name", "surface", "cage", "size", "lat", "lng", "address", "district", "access", "amenities", "desc"]
        for p in pitches:
            for k in required_keys:
                self.assertIn(k, p, f"Pitch {p.get('name')} missing {k}")

        # Check surfaces
        surfaces = set(p["surface"] for p in pitches)
        self.assertIn("Rasenplatz", surfaces)
        self.assertIn("Kunstrasen", surfaces)
        self.assertIn("Hartplatz", surfaces)
        self.assertIn("Asphalt", surfaces)

        # Check official and unofficial presence
        has_official = any(p["access"] != "Öffentlich" for p in pitches)
        has_unofficial = any(p["access"] == "Öffentlich" for p in pitches)
        self.assertTrue(has_official)
        self.assertTrue(has_unofficial)

    def test_matcher_and_occupations(self):
        pitches = [
            {
                "id": "p_test",
                "name": "Bezirkssportanlage Surheimer Weg",
                "address": "Surheimer Weg 3, 81379 München",
                "district": "Obersendling",
                "surface": "Kunstrasen",
                "occupations": [],
                "desc": "Sportanlage in Sendling."
            }
        ]
        sample_matches = [
            {
                "date": "2026-10-18",
                "time": "11:30",
                "minute_start": 690,
                "home": "FC Hertha München",
                "away": "FC Teutonia Mün.",
                "league": "Kreisliga",
                "venue_name": "BSA Surheimer Weg",
                "venue_addr": "Kunstrasen, Surheimer Weg 3, 81379 München",
                "reported_by_club": "FC Hertha München"
            }
        ]
        updated, stats = connect_pitches_and_matches(pitches, sample_matches, verbose=False)
        self.assertEqual(stats["matched_matches"], 1)
        self.assertEqual(len(updated[0]["occupations"]), 1)
        occ = updated[0]["occupations"][0]
        self.assertEqual(occ["slot_idx"], 2)
        self.assertEqual(occ["home"], "FC Hertha München")
        self.assertEqual(updated[0]["club"], "FC Hertha München")


    def test_landkreis_and_district_coverage(self):
        pitches = get_all_pitches(include_live_photon=False, verbose=False)
        self.assertGreaterEqual(len(pitches), 100)
        
        # Check Landkreis municipalities are represented
        districts = set(p["district"] for p in pitches)
        for m in ["Garching", "Unterhaching", "Grünwald", "Ismaning", "Haar", "Planegg", "Sauerlach", "Aying", "Schäftlarn"]:
            self.assertTrue(any(m in d for d in districts), f"Missing coverage for {m}")

        # Check unofficial pitches do not have club training assigned
        for p in pitches:
            if p["access"] == "Öffentlich":
                self.assertIsNone(p.get("club"))

    def test_precise_pitch_coordinates(self):
        pitches = get_all_pitches(include_live_photon=False, verbose=False)
        self.assertEqual(len(pitches), 132)

        for p in pitches:
            lat = p["lat"]
            lng = p["lng"]
            self.assertGreaterEqual(lat, 47.90)
            self.assertLessEqual(lat, 48.35)
            self.assertGreaterEqual(lng, 11.35)
            self.assertLessEqual(lng, 11.85)

        by_name = {p["name"]: p for p in pitches}
        nordbad = by_name.get("Bezirkssportanlage Schleißheimer Straße (Nordbad)")
        self.assertAlmostEqual(nordbad["lat"], 48.160143, places=4)
        self.assertAlmostEqual(nordbad["lng"], 11.564419, places=4)

        haching = by_name.get("Sportpark Unterhaching (uhlsport PARK & Grünau)")
        self.assertAlmostEqual(haching["lat"], 48.073781, places=4)
        self.assertAlmostEqual(haching["lng"], 11.615839, places=4)

        garching = by_name.get("Sportpark Stadion am See Garching")
        self.assertAlmostEqual(garching["lat"], 48.259881, places=4)
        self.assertAlmostEqual(garching["lng"], 11.643395, places=4)

    def test_known_club_home_ground_mapping(self):
        from scraper.matcher import KNOWN_CLUB_HOME_GROUNDS
        self.assertIn("TSV Grünwald", KNOWN_CLUB_HOME_GROUNDS)
        self.assertIn("SV Heimstetten", KNOWN_CLUB_HOME_GROUNDS)
        self.assertIn("FC Ismaning", KNOWN_CLUB_HOME_GROUNDS)

    def test_multi_city_config(self):
        from scraper.config import CITIES
        for city_key in ["munich", "nuremberg", "berlin", "hamburg", "cologne", "frankfurt"]:
            self.assertIn(city_key, CITIES)
            cfg = CITIES[city_key]
            self.assertIn("name", cfg)
            self.assertIn("bbox", cfg)
            self.assertIn("center", cfg)
            self.assertEqual(len(cfg["bbox"]), 4)

    def test_osm_importer(self):
        from scraper.osm_importer import parse_osm_elements, fetch_osm_pitches, get_multi_city_pitches
        sample_elements = [
            {
                "id": 999888,
                "lat": 52.5200,
                "lon": 13.4050,
                "tags": {
                    "name": "Bolzplatz Alexanderplatz",
                    "surface": "artificial_turf",
                    "lit": "yes",
                    "access": "yes",
                    "addr:suburb": "Mitte"
                }
            }
        ]
        parsed = parse_osm_elements(sample_elements, city_name="Berlin")
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["surface"], "Kunstrasen")
        self.assertTrue(parsed[0]["lit"])
        self.assertEqual(parsed[0]["access"], "Öffentlich")

        berlin_pitches = fetch_osm_pitches((52.33, 13.08, 52.68, 13.76), city_name="Berlin", live=False)
        self.assertGreaterEqual(len(berlin_pitches), 3)

        multi = get_multi_city_pitches(live_osm=False)
        self.assertGreaterEqual(len(multi), 15)

    def test_fussball_de_scraper_and_gdpr(self):
        from scraper.fussball_de_scraper import parse_fussball_de_html, sanitize_match_record, scrape_all_cities_matches
        dirty = {
            "date": "2026-10-18",
            "time": "14:00",
            "minute_start": 840,
            "home": "Berliner AK 07",
            "away": "Türkiyemspor",
            "league": "Berlin-Liga",
            "venue_name": "Poststadion",
            "venue_addr": "Lehrter Str. 59",
            "player_names": ["Max Mustermann"],
            "referee_phone": "+49170123456"
        }
        clean = sanitize_match_record(dirty)
        self.assertNotIn("player_names", clean)
        self.assertNotIn("referee_phone", clean)
        self.assertEqual(clean["home"], "Berliner AK 07")

        sample_html = """
        <table>
          <tr class="club-match-row" data-date="2026-10-18" data-time="15:00">
            <td class="team-name">Altona 93</td>
            <td class="team-name">ETV Hamburg</td>
            <td class="league-name">Oberliga Hamburg</td>
            <td class="venue-name">Adolf-Jäger-Kampfbahn</td>
            <td class="venue-address">Griegstraße 62, Hamburg</td>
          </tr>
        </table>
        """
        matches = parse_fussball_de_html(sample_html, default_city="Hamburg", association="HFV")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["minute_start"], 900)
        self.assertEqual(matches[0]["home"], "Altona 93")

        all_regional = scrape_all_cities_matches(live=False)
        self.assertGreaterEqual(len(all_regional), 6)

    def test_scheduler_nightly_ingestion(self):
        from scraper.scheduler import run_nightly_ingestion
        report = run_nightly_ingestion(live_network=False, output_dir="data", update_js=False)
        self.assertEqual(report["status"], "success")
        self.assertEqual(report["munich_pitches"], 132)
        self.assertGreaterEqual(report["total_pitches"], 380)
        self.assertGreaterEqual(report["multi_city_pitches"], 250)
        self.assertGreaterEqual(report["clubs_processed"], 250)
        self.assertGreaterEqual(report["matched_occupations"], 70)

    def test_multi_city_parity_and_associations(self):
        from scraper.osm_importer import CURATED_MULTI_CITY_PITCHES
        from scraper.fussball_de_scraper import discover_city_clubs, scrape_city_matches, parse_fussball_de_html

        for city_key in ["nuremberg", "berlin", "hamburg", "cologne", "frankfurt"]:
            pitches = CURATED_MULTI_CITY_PITCHES.get(city_key, [])
            self.assertGreaterEqual(len(pitches), 45, f"Too few pitches in {city_key}")
            official = [p for p in pitches if p.get("access") != "Öffentlich"]
            public = [p for p in pitches if p.get("access") == "Öffentlich"]
            self.assertGreaterEqual(len(official), 20, f"Too few official pitches in {city_key}")
            self.assertGreaterEqual(len(public), 20, f"Too few public pitches in {city_key}")
            self.assertTrue(all(p.get("club") for p in official), f"Official pitch missing home club in {city_key}")

            clubs = discover_city_clubs(city_key, live=False)
            self.assertGreaterEqual(len(clubs), 40, f"Too few clubs in {city_key}")

            matches = scrape_city_matches(city_key, live=False)
            self.assertGreaterEqual(len(matches), 15, f"Too few matches in {city_key}")

        # Verify live 3-row Fussball.de HTML parser
        live_html = """
        <table>
          <tr class="row-headline visible-small">
            <td colspan="6">Sonntag, 25.10.2026 - 14:15 Uhr | Herren | Berlin-Liga</td>
          </tr>
          <tr class="odd row-competition hidden-small">
            <td class="column-date">14:15</td>
          </tr>
          <tr class="odd">
            <td class="column-club"><div class="club-name">Türkiyemspor Berlin</div></td>
            <td class="column-club"><div class="club-name">Berliner AK 07</div></td>
          </tr>
        </table>
        """
        parsed_3row = parse_fussball_de_html(live_html, default_city="Berlin", association="BFV_BERLIN")
        self.assertEqual(len(parsed_3row), 1)
        self.assertEqual(parsed_3row[0]["home"], "Türkiyemspor Berlin")
        self.assertEqual(parsed_3row[0]["away"], "Berliner AK 07")
        self.assertEqual(parsed_3row[0]["minute_start"], 855)


if __name__ == "__main__":
    unittest.main()

