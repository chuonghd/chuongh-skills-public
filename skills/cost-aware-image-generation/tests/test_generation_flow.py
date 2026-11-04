"""End-to-end runs of generate_image.py with the API mocked: files, ledger, failures, keys."""

import json
import os
import unittest
from unittest import mock

from helpers import IsolatedStoreTest, generate_image, openai_response, gemini_response


class SuccessfulRunTest(IsolatedStoreTest):
    def test_writes_run_folder_and_ledger_with_cost(self):
        self.api_returns(openai_response(text_in=22, image_out=343))
        code, text, data = self.run_script("--prompt", "a mug", "--label", "mug")
        self.assertEqual(code, 0, text)
        run_dir = self.store / "runs" / data["id"]
        for name in ("prompt.txt", "request.json", "response-meta.json", "run.json", "outputs/image-1.png"):
            self.assertTrue((run_dir / name).exists(), name)
        rec = self.ledger_lines()[-1]
        self.assertEqual(rec["status"], "ok")
        self.assertAlmostEqual(rec["cost_usd"], (22 * 5 + 343 * 30) / 1e6, places=6)
        self.assertEqual(rec["cost_vnd"], round(rec["cost_usd"] * 25910))
        self.assertEqual(rec["rates_usd_per_1m"]["output_image"], 30.0)  # rates kept with the run
        self.assertEqual(rec["project"], os.getcwd())

    def test_out_copies_final_image_into_project(self):
        self.api_returns(openai_response())
        target = self.tmp / "project" / "assets" / "hero.png"
        code, text, data = self.run_script("--prompt", "x", "--out", str(target))
        self.assertEqual(code, 0, text)
        self.assertTrue(target.exists())
        self.assertEqual(data["copied_to"], str(target.resolve()))

    def test_reference_images_are_copied_into_the_run(self):
        ref = self.tmp / "Cat Photo.JPG"
        ref.write_bytes(b"jpeg")
        self.api_returns(openai_response(image_in=500))
        _, _, data = self.run_script("--prompt", "x", "--input", str(ref))
        self.assertTrue((self.store / "runs" / data["id"] / "inputs" / "input-1.jpg").exists())

    def test_request_file_has_no_image_bytes(self):
        ref = self.tmp / "ref.png"
        ref.write_bytes(b"x" * 5000)
        self.api_returns(openai_response())
        _, _, data = self.run_script("--prompt", "x", "--input", str(ref))
        request = (self.store / "runs" / data["id"] / "request.json").read_text()
        self.assertLess(len(request), 2000)

    def test_gemini_run_end_to_end(self):
        self.api_returns(gemini_response())
        code, text, data = self.run_script("--provider", "gemini", "--prompt", "x")
        self.assertEqual(code, 0, text)
        self.assertAlmostEqual(data["cost_usd"], 0.044426, places=6)
        self.assertTrue(data["outputs"][0].endswith(".jpg"))

    def test_same_label_in_the_same_second_gets_its_own_folder(self):
        self.api_returns(openai_response())
        fixed = generate_image.datetime(2026, 11, 4, 22, 0, 0).astimezone()
        with mock.patch.object(generate_image, "datetime", wraps=generate_image.datetime) as dt:
            dt.now.return_value = fixed
            ids = [self.run_script("--prompt", "same", "--label", "same")[2]["id"] for _ in range(3)]
        self.assertEqual(ids, ["2026-11-04_220000_same", "2026-11-04_220000_same-2", "2026-11-04_220000_same-3"])


class FailedRunTest(IsolatedStoreTest):
    def test_api_error_is_logged_without_cost(self):
        failing = mock.patch.object(generate_image.providers, "_post_json", side_effect=RuntimeError("HTTP 500 from api"))
        failing.start()
        self.addCleanup(failing.stop)
        code, text, _ = self.run_script("--prompt", "x")
        self.assertNotEqual(code, 0)
        self.assertIn("logged as", text)
        rec = self.ledger_lines()[-1]
        self.assertEqual((rec["status"], rec["cost_usd"]), ("error", None))
        self.assertIn("HTTP 500", rec["error"])

    def test_missing_key_stops_before_any_file_is_written(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            code, text, _ = self.run_script("--prompt", "x")
        self.assertNotEqual(code, 0)
        self.assertIn("OPENAI_API_KEY is not set", text)
        self.assertEqual((self.run_dirs(), self.ledger_lines()), ([], []))

    def test_only_openai_key_is_enough_for_the_default(self):
        self.api_returns(openai_response())
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            code, text, _ = self.run_script("--prompt", "x")
        self.assertEqual(code, 0, text)

    def test_dry_run_needs_no_key_and_touches_nothing(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": ""}):
            code, text, data = self.run_script("--prompt", "x", "--dry-run")
        self.assertEqual(code, 0, text)
        self.assertTrue(data["dry_run"])
        self.assertEqual((self.run_dirs(), self.ledger_lines()), ([], []))


class EstimateTest(IsolatedStoreTest):
    def test_openai_estimate_reuses_last_matching_run_only(self):
        self.seed({**self._rec(0.0104, "1024x1536", "medium")}, {**self._rec(0.5, "1536x1536", "high")})
        _, _, same = self.run_script("--prompt", "x", "--dry-run")
        _, _, other = self.run_script("--prompt", "x", "--dry-run", "--size", "1024x1024")
        self.assertEqual(same["estimate"]["last_observed_usd"], 0.0104)
        self.assertNotIn("last_observed_usd", other["estimate"])

    def test_gemini_estimate_is_the_fixed_image_cost(self):
        _, _, data = self.run_script("--provider", "gemini", "--prompt", "x", "--dry-run")
        self.assertEqual(data["estimate"]["output_image_usd"], 0.0336)

    @staticmethod
    def _rec(cost, size, quality):
        from helpers import ledger_record
        r = ledger_record(cost)
        r["settings"].update(size=size, quality=quality)
        return r


class EnvFileTest(IsolatedStoreTest):
    def test_env_file_fills_missing_keys_but_shell_wins(self):
        (self.tmp / ".env").write_text('# comment\nexport OPENAI_API_KEY="from-file"\nGEMINI_API_KEY=\nOTHER=\'quoted\'\n')
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "", "GEMINI_API_KEY": "from-shell"}, clear=False):
            os.environ.pop("OPENAI_API_KEY")
            generate_image.load_env_file(self.tmp / ".env")
            self.assertEqual(os.environ["OPENAI_API_KEY"], "from-file")
            self.assertEqual(os.environ["GEMINI_API_KEY"], "from-shell")   # shell value kept
            self.assertEqual(os.environ["OTHER"], "quoted")

    def test_check_keys_never_prints_values(self):
        code, text, _ = self.run_script("--check-keys")
        self.assertEqual(code, 0)
        self.assertIn("OPENAI_API_KEY: set", text)
        self.assertNotIn(os.environ["OPENAI_API_KEY"], text)


if __name__ == "__main__":
    unittest.main()
