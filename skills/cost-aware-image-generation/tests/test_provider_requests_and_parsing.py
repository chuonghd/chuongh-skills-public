"""What we send to each API and how we read its reply (shapes taken from real 2026-11-04 responses)."""

import os
import unittest
import urllib.error
from io import BytesIO
from unittest import mock

from helpers import REAL_POST_JSON, IsolatedStoreTest, PNG_B64, gemini_response, openai_response, providers


class OpenAIRequestTest(IsolatedStoreTest):
    def test_text_only_uses_generations_and_one_image(self):
        api = self.api_returns(openai_response())
        body = providers.build_openai_request("gpt-image-2.5-sunburst", "a mug", [], "1024x1536", "medium")
        providers.call_openai(body)
        url, headers, sent = api.call_args.args
        self.assertTrue(url.endswith("/images/generations"))
        self.assertEqual(sent["n"], 1)
        self.assertNotIn("partial_images", sent)  # partial previews cost extra tokens
        self.assertTrue(headers["Authorization"].startswith("Bearer sk-test"))

    def test_reference_images_use_edits_as_data_urls(self):
        ref = self.tmp / "ref.png"
        ref.write_bytes(b"\x89PNG fake")
        api = self.api_returns(openai_response(image_in=500))
        providers.call_openai(providers.build_openai_request("gpt-image-2.5-sunburst", "x", [str(ref)], "1536x1024", "medium"))
        url, _, sent = api.call_args.args
        self.assertTrue(url.endswith("/images/edits"))
        self.assertTrue(sent["images"][0]["image_url"].startswith("data:image/png;base64,"))


class OpenAIParsingTest(IsolatedStoreTest):
    def test_full_usage_is_split_by_type(self):
        self.api_returns(openai_response(text_in=946, image_in=2912, image_out=343))
        images, tokens, meta = providers.call_openai({"model": "gpt-image-2.5-sunburst"})
        self.assertEqual(len(images), 1)
        self.assertEqual((tokens["input_text"], tokens["input_image"], tokens["output_image"]), (946, 2912, 343))
        self.assertNotIn(PNG_B64, str(meta))  # image bytes never stored in metadata files

    def test_missing_usage_reports_unknown_not_zero(self):
        self.api_returns(openai_response(usage=False))
        _, tokens, _ = providers.call_openai({"model": "gpt-image-2.5-sunburst"})
        self.assertIsNone(tokens["output_image"])

    def test_no_image_returned(self):
        resp = openai_response()
        resp["data"] = []
        self.api_returns(resp)
        images, _, _ = providers.call_openai({"model": "gpt-image-2.5-sunburst"})
        self.assertEqual(images, [])


class GeminiTest(IsolatedStoreTest):
    def test_request_sets_size_ratio_and_thinking(self):
        body = providers.build_gemini_request("gemini-nano-banana-2.1", "x", [], "16:9", "1K", "medium")
        self.assertEqual(body["response_format"], {"type": "image", "aspect_ratio": "16:9", "image_size": "1K"})
        self.assertEqual(body["generation_config"], {"thinking_level": "medium"})

    def test_reads_image_from_model_output_step_and_modality_counts(self):
        self.api_returns(gemini_response())
        body = providers.build_gemini_request("gemini-nano-banana-2.1", "x", [], "2:3", "1K", "medium")
        images, tokens, _ = providers.call_gemini(body, "1K", has_input_images=False)
        self.assertEqual(images[0][1], "jpg")
        self.assertEqual(tokens, {"input_text": 27, "input_image": 0, "input_total": 27, "output_image": 1120,
                                  "output_text": 351, "thinking": 1087})

    def test_reference_images_split_from_modality_counts(self):
        self.api_returns(gemini_response(text_in=40, image_in=1200))
        body = providers.build_gemini_request("gemini-nano-banana-2.1", "x", [], "2:3", "1K", "medium")
        _, tokens, _ = providers.call_gemini(body, "1K", has_input_images=True)
        self.assertEqual((tokens["input_text"], tokens["input_image"]), (40, 1200))

    def test_without_modality_counts_falls_back_to_fixed_image_tokens(self):
        self.api_returns(gemini_response(by_modality=False, image_out=1680, other_out=0))
        body = providers.build_gemini_request("gemini-nano-banana-2.1", "x", [], "2:3", "2K", "medium")
        _, tokens, _ = providers.call_gemini(body, "2K", has_input_images=True)
        self.assertEqual(tokens["output_image"], 1680)              # 2K fixed count from the pricing page
        self.assertEqual((tokens["input_text"], tokens["input_image"]), (None, None))  # split unknown, not guessed


class KeySafetyTest(IsolatedStoreTest):
    def test_missing_key_message_points_to_env_example(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": ""}), self.assertRaises(SystemExit) as ctx:
            providers.require_key("OPENAI_API_KEY")
        self.assertIn(".env.example", str(ctx.exception))

    def test_full_and_partial_key_echoes_are_redacted(self):
        key = os.environ["OPENAI_API_KEY"]
        text = providers.redact_keys(f"Incorrect API key provided: {key}. Also {key[:8]}***{key[-6:]}")
        self.assertNotIn(key, text)
        self.assertNotIn(key[:8], text)
        self.assertNotIn(key[-6:], text)

    def test_http_error_body_is_redacted(self):
        key = os.environ["OPENAI_API_KEY"]
        err = urllib.error.HTTPError("https://api.openai.com/v1/images/generations", 401, "Unauthorized", {},
                                     BytesIO(f'{{"error": "Incorrect API key provided: {key}"}}'.encode()))
        self.addCleanup(err.close)
        with mock.patch("urllib.request.urlopen", side_effect=err), self.assertRaises(RuntimeError) as ctx:
            REAL_POST_JSON("https://api.openai.com/v1/images/generations", {}, {})
        self.assertIn("HTTP 401", str(ctx.exception))
        self.assertNotIn(key, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
