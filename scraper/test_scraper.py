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

    def test_known_club_home_ground_mapping(self):
        from scraper.matcher import KNOWN_CLUB_HOME_GROUNDS
        self.assertIn("TSV Grünwald", KNOWN_CLUB_HOME_GROUNDS)
        self.assertIn("SV Heimstetten", KNOWN_CLUB_HOME_GROUNDS)
        self.assertIn("FC Ismaning", KNOWN_CLUB_HOME_GROUNDS)


if __name__ == "__main__":
    unittest.main()
