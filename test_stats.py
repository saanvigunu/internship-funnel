"""Funnel math tests pinned to the committed sample file.

The expected numbers are the real contents of data/sample.csv; if the
sample changes, these move with it.
"""

import os
import unittest
from datetime import date

from funnel import stats, store

SAMPLE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "data", "sample.csv")
TODAY = date(2026, 11, 27)


class SampleCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = store.load(path=SAMPLE)


class TestCounts(SampleCase):
    def test_total_and_stages(self):
        counts = stats.stage_counts(self.rows)
        self.assertEqual(len(self.rows), 14)
        self.assertEqual(counts["applied"], 4)
        self.assertEqual(counts["offer"], 1)
        self.assertEqual(counts["rejected"], 2)
        self.assertEqual(counts["watching"], 1)

    def test_summary(self):
        s = stats.summary(self.rows, today=TODAY)
        self.assertEqual(s["total"], 14)
        self.assertEqual(s["active"], 9)
        self.assertEqual(s["offers"], 1)
        self.assertEqual(s["due"], 5)


class TestConversions(SampleCase):
    def test_pinned_rates(self):
        steps, unknown = stats.conversions(self.rows)
        table = {(p, s): (pn, n) for p, s, pn, n, _ in steps}
        self.assertEqual(table[(None, "applied")], (None, 10))
        self.assertEqual(table[("applied", "oa")], (10, 6))
        self.assertEqual(table[("oa", "interview")], (6, 4))
        self.assertEqual(table[("interview", "onsite")], (4, 2))
        self.assertEqual(table[("onsite", "offer")], (2, 1))
        # 2 rejected + 1 ghosted excluded; the watching row is NOT "unknown"
        self.assertEqual(unknown, 3)

    def test_rates_computed_correctly(self):
        steps, _ = stats.conversions(self.rows)
        rates = {(p, s): r for p, s, _, _, r in steps if r is not None}
        self.assertAlmostEqual(rates[("applied", "oa")], 0.6)
        self.assertAlmostEqual(rates[("onsite", "offer")], 0.5)

    def test_empty_rows(self):
        steps, unknown = stats.conversions([])
        self.assertEqual(unknown, 0)
        self.assertTrue(all(n == 0 for _, _, _, n, _ in steps))


class TestFollowups(SampleCase):
    def test_due_order_and_filter(self):
        due = stats.due_followups(self.rows, today=TODAY)
        # rows 4 and 5 share 2026-11-26; row 2 lands exactly on today
        self.assertEqual([r["id"] for r in due], ["6", "7", "4", "5", "2"])
        # the watching row's followup (2026-12-15) is in the future
        self.assertNotIn("14", [r["id"] for r in due])

    def test_terminal_rows_never_due(self):
        rows = [{"id": "1", "company": "X", "role": "y", "stage": "offer",
                 "applied": "2026-01-01", "last_touch": "2026-01-01",
                 "followup": "2026-01-02", "link": "", "notes": ""}]
        self.assertEqual(stats.due_followups(rows, today="2026-11-27"), [])


class TestStale(SampleCase):
    def test_stale_14d(self):
        cold = stats.stale(self.rows, days=14, today=TODAY)
        ids = [r["id"] for r, _ in cold]
        self.assertEqual(ids, ["6", "8", "9", "4", "7", "10", "3"])
        ages = {r["id"]: age for r, age in cold}
        self.assertEqual(ages["6"], 25)   # last touch 2026-11-02

    def test_watching_and_terminal_not_stale(self):
        cold = stats.stale(self.rows, days=1, today=TODAY)
        ids = {r["id"] for r, _ in cold}
        self.assertNotIn("14", ids)   # watching
        self.assertNotIn("1", ids)    # offer
        self.assertNotIn("11", ids)   # rejected


if __name__ == "__main__":
    unittest.main()
