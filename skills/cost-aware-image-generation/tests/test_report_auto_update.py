"""The usage report is rebuilt after every logged run, never opened, and can be turned off."""

import os
import unittest
from unittest import mock

from helpers import IsolatedStoreTest, generate_image, openai_response
import export_usage_html  # noqa: E402  (helpers puts scripts/ on sys.path)


class ReportAutoUpdateTest(IsolatedStoreTest):
    def setUp(self):
        super().setUp()
        self.api_returns(openai_response())
        self.report = self.store / "usage-report.html"

    def test_report_rebuilt_after_generation_and_path_returned(self):
        code, text, data = self.run_script("--prompt", "x", "--label", "first")
        self.assertEqual(code, 0, text)
        self.assertEqual(data["report"], str(self.report))
        self.assertIn(data["id"], self.report.read_text())

    def test_existing_stale_report_is_replaced_with_latest_runs_and_time(self):
        self.report.write_text("<html>Updated</dt><dd>Nov 4, 2026 · 22:37</dd> old report</html>")
        _, _, first = self.run_script("--prompt", "x", "--label", "first")
        _, _, second = self.run_script("--prompt", "x", "--label", "second")
        html = self.report.read_text()
        self.assertNotIn("old report", html)
        self.assertIn(first["id"], html)
        self.assertIn(second["id"], html)
        now = generate_image.datetime.now().strftime("%b %-d, %Y · %H:%M")
        self.assertIn(f"Updated</dt><dd>{now}", html)

    def test_report_is_never_opened(self):
        with mock.patch.object(export_usage_html.subprocess, "run") as opener:
            self.run_script("--prompt", "x")
        opener.assert_not_called()
        self.assertTrue(self.report.exists())

    def test_turned_off_by_false_like_values(self):
        for value in ("false", "False", "0", "no", "off"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"AUTO_UPDATE_REPORT": value}):
                _, _, data = self.run_script("--prompt", "x")
                self.assertIn("auto-update off", data["report"])
                self.assertFalse(self.report.exists())

    def test_turned_off_from_the_skill_env_file(self):
        (self.tmp / ".env").write_text("AUTO_UPDATE_REPORT=false\n")  # tests point SKILL_DIR at self.tmp
        _, _, data = self.run_script("--prompt", "x")
        self.assertIn("auto-update off", data["report"])

    def test_report_failure_never_fails_the_generation(self):
        with mock.patch.object(export_usage_html, "write_report", side_effect=OSError("disk full")):
            code, text, data = self.run_script("--prompt", "x")
        self.assertEqual(code, 0, text)
        self.assertEqual(data["report"], "not updated: disk full")
        self.assertEqual(self.ledger_lines()[-1]["status"], "ok")

    def test_failed_generation_also_refreshes_the_report(self):
        failing = mock.patch.object(generate_image.providers, "_post_json", side_effect=RuntimeError("HTTP 500 boom"))
        failing.start()
        self.addCleanup(failing.stop)
        self.run_script("--prompt", "x")
        self.assertIn("HTTP 500 boom", self.report.read_text())

    def test_dry_run_and_blocked_runs_do_not_touch_the_report(self):
        self.run_script("--prompt", "x", "--dry-run")
        self.run_script("--prompt", "x", "--quality", "high")  # blocked: needs --reason
        self.assertFalse(self.report.exists())

    def test_report_status_is_not_saved_in_the_ledger(self):
        self.run_script("--prompt", "x")
        self.assertNotIn("report", self.ledger_lines()[-1])


if __name__ == "__main__":
    unittest.main()
