"""HTML usage report: survives real-world ledger contents, escapes prompts, and charts the right days."""

import math
import re
import unittest
from datetime import date, timedelta

from helpers import IsolatedStoreTest, ledger_record
import export_usage_html as report  # noqa: E402  (helpers puts scripts/ on sys.path)
import report_daily_chart_html as daily_chart  # noqa: E402
import report_model_catalog_html as catalog  # noqa: E402


class ReportBuildTest(IsolatedStoreTest):
    def build(self, *records):
        self.seed(*records)
        return report.build_html(self.store, report.load_ledger(self.store))

    def test_prompt_html_is_escaped(self):
        html = self.build(ledger_record(0.01, prompt='<script>alert("x")</script> & <b>bold</b>'))
        self.assertNotIn('<script>alert("x")', html)
        self.assertIn("&lt;script&gt;", html)

    def test_mixed_ledger_renders(self):
        # Failed run, run logged before rates were stored, unknown legacy model, Gemini run, run with no fx.
        legacy = ledger_record(0.02)
        legacy["settings"]["model"] = "gpt-image-1"
        gemini = ledger_record(0.044, tokens={"input_text": 27, "output_image": 1120, "thinking": 1087},
                               cost_breakdown_usd={"output_image": 0.0336})
        gemini["settings"] = {"provider": "gemini", "model": "gemini-nano-banana-2.1", "aspect": "2:3", "resolution": "1K",
                              "thinking": "medium", "overridden": [], "reason": None}
        html = self.build(ledger_record(None, status="error", error="HTTP 500"), legacy, gemini,
                          ledger_record(0.0104, rates_usd_per_1m={"input_text": 5, "input_image": 8, "output_image": 30,
                                                                  "output_text": 0, "thinking": 0}, prices_checked_on="2026-11-04"))
        self.assertIn("HTTP 500", html)
        self.assertIn("gpt-image-1", html)
        self.assertIn("this run predates stored rates", html)       # fallback note for old runs
        self.assertIn("Rates stored with this run", html)

    def test_images_link_relative_to_the_store(self):
        out = self.store / "runs" / "r1" / "outputs" / "image-1.png"
        html = self.build(ledger_record(0.01, outputs=[str(out)]))
        self.assertIn('src="runs/r1/outputs/image-1.png"', html)

    def test_empty_store_explains_instead_of_crashing(self):
        with self.assertRaises(SystemExit) as ctx:
            report.load_ledger(self.store)
        self.assertIn("Generate an image first", str(ctx.exception))

    def test_failed_runs_are_not_counted_in_spend(self):
        html = self.build(ledger_record(1.0), ledger_record(5.0, status="error"))
        self.assertIn("$1.0000", html)
        self.assertNotIn("$6.0000", html)


class DailyChartTest(unittest.TestCase):
    def test_last_30_days_only_with_empty_days_filled(self):
        daily = daily_chart._daily([ledger_record(1.0), ledger_record(2.0, days_ago=29), ledger_record(4.0, days_ago=30)])
        self.assertEqual(len(daily), 30)
        self.assertEqual((daily[0][0], daily[-1][0]), (date.today() - timedelta(days=29), date.today()))
        self.assertEqual(sum(c for _, _, c in daily), 3.0)             # 30 days ago is out of range
        self.assertEqual(sum(1 for _, n, _ in daily if n == 0), 28)

    def test_image_axis_steps_are_whole_numbers(self):
        for peak in (0, 1, 3, 7, 13, 250):
            step = daily_chart._nice_step(peak, integer=True)
            self.assertEqual(step, int(step), peak)
            self.assertGreaterEqual(step * 4, peak)

    def test_cost_axis_covers_the_peak_with_a_clean_step(self):
        for peak in (0, 0.0104, 0.0932, 1.37, 42.0):
            step = daily_chart._nice_step(peak, integer=False)
            self.assertGreaterEqual(step * 4, peak)
            mantissa = step / 10 ** math.floor(math.log10(step))
            self.assertIn(round(mantissa, 6), (1, 2, 2.5, 5, 10))

    def test_chart_has_one_hover_target_per_day(self):
        html = daily_chart.daily_charts_html([ledger_record(0.5)])
        self.assertEqual(len(re.findall(r'class="hit"', html)), 30)


class ModelCatalogTest(unittest.TestCase):
    def test_measured_average_uses_only_comparable_runs(self):
        std = ledger_record(0.010)
        with_refs = ledger_record(0.040, inputs=[{"saved": "x"}])       # reference images inflate cost
        big = ledger_record(0.200)
        big["settings"]["size"] = "1536x1536"
        avg, n = catalog._measured_average("gpt-image-2.5-sunburst", [std, with_refs, big])
        self.assertEqual((avg, n), (0.010, 1))

    def test_dialog_lists_every_model(self):
        html = catalog.models_dialog_html([], {"rate": 25910, "source": "vietcombank-sell", "date": "2026-11-04"})
        for model_id in catalog.MODELS:
            self.assertIn(model_id, html)


if __name__ == "__main__":
    unittest.main()
