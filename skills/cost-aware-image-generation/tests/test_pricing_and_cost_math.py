"""Cost math, price catalog consistency, and the USD->VND rate (cache and fallbacks)."""

import json
import unittest
from datetime import date, timedelta
from unittest import mock

from helpers import IsolatedStoreTest, pricing


class CostMathTest(unittest.TestCase):
    """Expected totals are the real runs from 2026-11-04, so this pins the math to actual bills."""

    def test_openai_with_reference_images(self):
        tokens = {"input_text": 946, "input_image": 2912, "input_total": 3858, "output_image": 343, "output_text": 0, "thinking": 0}
        breakdown, total = pricing.compute_cost_usd("gpt-image-2.5-sunburst", tokens)
        self.assertAlmostEqual(total, 0.038316, places=6)
        self.assertAlmostEqual(breakdown["input_image"], 2912 * 8 / 1e6, places=9)

    def test_gemini_bills_thinking_and_other_output_at_text_rate(self):
        tokens = {"input_text": 27, "input_image": 0, "input_total": 27, "output_image": 1120, "output_text": 351, "thinking": 1087}
        _, total = pricing.compute_cost_usd("gemini-nano-banana-2.1", tokens)
        self.assertAlmostEqual(total, 0.044426, places=6)

    def test_gemini_unknown_input_split_still_exact(self):
        # Text and image input share one Gemini rate, so the total input is enough.
        tokens = {"input_text": None, "input_image": None, "input_total": 1400, "output_image": 1120, "output_text": 0, "thinking": 0}
        breakdown, total = pricing.compute_cost_usd("gemini-nano-banana-2.1", tokens)
        self.assertAlmostEqual(total, (1400 * 1.5 + 1120 * 30) / 1e6, places=9)
        self.assertEqual(breakdown["input_image"], 0)

    def test_openai_unknown_input_split_is_not_guessed(self):
        # Text and image input have different OpenAI rates: refuse to invent a split.
        tokens = {"input_text": None, "input_image": None, "input_total": 1000, "output_image": 343, "output_text": 0, "thinking": 0}
        self.assertEqual(pricing.compute_cost_usd("gpt-image-2.5-sunburst", tokens), ({}, None))

    def test_missing_usage_gives_unknown_cost(self):
        tokens = {k: None for k in ("input_text", "input_image", "input_total", "output_image", "output_text", "thinking")}
        self.assertEqual(pricing.compute_cost_usd("gpt-image-2.5-sunburst", tokens), ({}, None))

    def test_unknown_model_is_an_error_not_zero_cost(self):
        with self.assertRaises(SystemExit):
            pricing.compute_cost_usd("gpt-image-9", {"output_image": 1})


class CatalogTest(unittest.TestCase):
    def test_every_model_is_complete(self):
        for model_id, info in pricing.MODELS.items():
            with self.subTest(model_id):
                self.assertEqual(set(info["rates"]), set(pricing.TOKEN_FIELDS))
                self.assertIn(info["provider"], ("openai", "gemini"))
                if info["provider"] == "gemini":
                    self.assertIn("1K", info["image_tokens"])
                elif info["generate"]:
                    self.assertIn("medium", info["qualities"])

    def test_exactly_one_default_and_it_is_sunburst(self):
        self.assertEqual([m for m, i in pricing.MODELS.items() if i.get("default")], ["gpt-image-2.5-sunburst"])

    def test_script_defaults_point_at_generatable_models(self):
        import generate_image
        for provider, d in generate_image.DEFAULTS.items():
            self.assertTrue(pricing.MODELS[d["model"]]["generate"], provider)

    def test_standard_estimates_match_published_prices(self):
        # Google publishes $0.0336 / $0.067 / $0.134 per 1K image; OpenAI's table lists $0.041 for gpt-image-2.
        expected = {"gemini-nano-banana-2.1": 0.0336, "gemini-3.1-flash-image": 0.0672, "gemini-3-pro-image": 0.1344,
                    "gpt-image-2": 0.041, "gpt-image-2.5-sunburst": 0.01029}
        for model_id, usd in expected.items():
            self.assertAlmostEqual(pricing.standard_image_estimate(model_id)[0], usd, places=4, msg=model_id)
        self.assertIsNone(pricing.standard_image_estimate("gpt-image-2.5-flare")[0])


class ExchangeRateTest(IsolatedStoreTest):
    VCB = '<Exrate CurrencyCode="USD" CurrencyName="US DOLLAR" Buy="25,500.00" Transfer="25,530.00" Sell="25,910.00" />'

    def test_uses_vietcombank_sell_rate_and_caches_it(self):
        with mock.patch.object(pricing, "_http_get", return_value=self.VCB) as get:
            fx = pricing.get_usd_vnd_rate(self.store)
            self.assertEqual((fx["rate"], fx["source"]), (25910.0, "vietcombank-sell"))
            pricing.get_usd_vnd_rate(self.store)  # same day: served from cache
            self.assertEqual(get.call_count, 1)

    def test_falls_back_to_market_rate_when_vietcombank_fails(self):
        def fake(url, timeout=10):
            if "vietcombank" in url:
                raise OSError("down")
            return json.dumps({"rates": {"VND": 25769.07}})
        with mock.patch.object(pricing, "_http_get", side_effect=fake):
            fx = pricing.get_usd_vnd_rate(self.store)
        self.assertEqual((fx["rate"], fx["source"]), (25769.07, "open.er-api-mid"))

    def test_vietcombank_feed_without_usd_falls_back(self):
        responses = iter(['<Exrate CurrencyCode="EUR" Sell="30,000" />', json.dumps({"rates": {"VND": 25800}})])
        with mock.patch.object(pricing, "_http_get", side_effect=lambda *a, **k: next(responses)):
            self.assertEqual(pricing.get_usd_vnd_rate(self.store)["source"], "open.er-api-mid")

    def test_offline_uses_yesterdays_cache_and_says_so(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        (self.store / "fx-cache.json").write_text(json.dumps({"rate": 25900.0, "source": "vietcombank-sell", "date": yesterday}))
        with mock.patch.object(pricing, "_http_get", side_effect=OSError("offline")):
            fx = pricing.get_usd_vnd_rate(self.store)
        self.assertEqual(fx["rate"], 25900.0)
        self.assertIn("stale cache", fx["source"])

    def test_offline_with_no_cache_stops(self):
        with mock.patch.object(pricing, "_http_get", side_effect=OSError("offline")), self.assertRaises(SystemExit):
            pricing.get_usd_vnd_rate(self.store)


if __name__ == "__main__":
    unittest.main()
