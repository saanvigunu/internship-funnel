"""Storage tests: add/move/get, validation, CSV round-trip."""

import os
import unittest

from funnel import store

TMP = "/tmp/test_funnel_store.csv"


class StoreCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TMP):
            os.remove(TMP)

    def tearDown(self):
        if os.path.exists(TMP):
            os.remove(TMP)


class TestAdd(StoreCase):
    def test_add_assigns_ids_and_today(self):
        rows = []
        a = store.add(rows, "Acme", "SWE Intern", today="2026-11-27")
        b = store.add(rows, "Beta", "ML Intern", today="2026-11-27")
        self.assertEqual((a["id"], b["id"]), ("1", "2"))
        self.assertEqual(a["applied"], "2026-11-27")
        self.assertEqual(a["last_touch"], "2026-11-27")

    def test_bad_stage_rejected(self):
        with self.assertRaises(ValueError):
            store.add([], "Acme", "x", stage="hired")
        with self.assertRaises(ValueError):
            store.add([], "Acme", "x", stage="Applied")  # case matters

    def test_bad_dates_rejected(self):
        with self.assertRaises(ValueError):
            store.add([], "Acme", "x", applied="nov 3")
        with self.assertRaises(ValueError):
            store.add([], "Acme", "x", followup="2026-13-01"[:10] + "x")
        # empty dates are fine
        store.add([], "Acme", "x", applied="", followup="")


class TestMoveGet(StoreCase):
    def test_move_updates_stage_and_touch(self):
        rows = [store.add([], "Acme", "x", today="2026-11-01")]
        row = store.move(rows, 1, "oa", today="2026-11-27")
        self.assertEqual(row["stage"], "oa")
        self.assertEqual(row["last_touch"], "2026-11-27")

    def test_move_rejects_bad_stage(self):
        rows = [store.add([], "Acme", "x", today="2026-11-01")]
        with self.assertRaises(ValueError):
            store.move(rows, 1, "maybe")

    def test_get_missing_raises(self):
        with self.assertRaises(KeyError):
            store.get([], "99")


class TestRoundTrip(StoreCase):
    def test_save_load_preserves_rows(self):
        rows = []
        store.add(rows, "Acme, Inc.", "SWE \"Intern\"", today="2026-11-27",
                  notes="comma, and \"quotes\"")
        store.add(rows, "Beta", "ML", today="2026-11-27")
        store.save(rows, path=TMP)
        loaded = store.load(path=TMP)
        self.assertEqual(loaded, rows)

    def test_empty_file_loads_empty(self):
        self.assertEqual(store.load(path=TMP), [])


if __name__ == "__main__":
    unittest.main()
