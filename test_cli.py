"""CLI tests: scripted runs against a temp data file."""

import io
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest import mock

from funnel import cli, store

TMP = "/tmp/test_funnel_cli.csv"


class CliCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TMP):
            os.remove(TMP)
        patcher = mock.patch.dict(os.environ, {"FUNNEL_FILE": TMP})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: os.path.exists(TMP) and os.remove(TMP))

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class TestBasics(CliCase):
    def test_help(self):
        code, out, _ = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("stats", out)

    def test_unknown_command(self):
        code, _, err = self.run_cli("frobnicate")
        self.assertEqual(code, 2)

    def test_list_empty(self):
        code, out, _ = self.run_cli("list")
        self.assertIn("nothing here yet", out)


class TestFlow(CliCase):
    def test_add_move_note_due(self):
        code, out, _ = self.run_cli("add", "Acme", "SWE Intern",
                                    "--followup", "2026-11-20")
        self.assertIn("added #1", out)
        code, out, _ = self.run_cli("move", "1", "oa")
        self.assertIn("#1 Acme -> oa", out)
        code, out, _ = self.run_cli("note", "1", "recruiter is Mia")
        self.assertIn("noted", out)
        code, out, _ = self.run_cli("due")
        self.assertIn("Acme", out)
        rows = store.load(TMP)
        self.assertEqual(rows[0]["stage"], "oa")
        self.assertIn("Mia", rows[0]["notes"])

    def test_add_bad_stage_exits(self):
        with self.assertRaises(SystemExit):
            self.run_cli("add", "Acme", "x", "--stage", "hired")

    def test_move_missing_id_exits(self):
        with self.assertRaises(SystemExit):
            self.run_cli("move", "99", "oa")

    def test_followup_validates_date(self):
        self.run_cli("add", "Acme", "x")
        with self.assertRaises(SystemExit):
            self.run_cli("followup", "1", "next friday")

    def test_stats_no_benchmarks_language(self):
        self.run_cli("add", "Acme", "x")
        self.run_cli("add", "Beta", "y")
        code, out, _ = self.run_cli("stats")
        self.assertIn("YOUR file only", out)
        self.assertIn("no benchmark", out)


class TestSample(CliCase):
    def test_sample_loads_and_refuses_overwrite(self):
        code, out, _ = self.run_cli("sample")
        self.assertIn("FICTIONAL", out)
        rows = store.load(TMP)
        self.assertEqual(len(rows), 14)
        code, out, _ = self.run_cli("stats")
        self.assertIn("14 applications", out)
        with self.assertRaises(SystemExit):
            self.run_cli("sample")  # refuses to overwrite real rows


if __name__ == "__main__":
    unittest.main()
