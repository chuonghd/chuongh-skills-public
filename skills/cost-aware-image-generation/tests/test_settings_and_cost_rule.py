"""The cost rule: what counts as standard tier, what needs --reason, and what is never allowed.

All runs here are dry runs or rejected before any API call.
"""

import unittest

from helpers import IsolatedStoreTest


class StandardTierTest(IsolatedStoreTest):
    def settings(self, *argv):
        code, text, data = self.run_script("--prompt", "x", "--dry-run", *argv)
        self.assertEqual(code, 0, text)
        return data["settings"]

    def test_no_provider_defaults_to_sunburst_portrait_medium(self):
        s = self.settings()
        self.assertEqual((s["provider"], s["model"], s["size"], s["quality"]), ("openai", "gpt-image-2.5-sunburst", "1024x1536", "medium"))
        self.assertEqual(s["overridden"], [])

    def test_any_shape_with_short_edge_1024_or_less_is_standard(self):
        for size in ("1024x1024", "1536x1024", "1024x1536", "1792x1024", "1024x2048", "1280x720"):
            with self.subTest(size=size):
                self.assertEqual(self.settings("--size", size)["overridden"], [])

    def test_gemini_any_aspect_at_1k_is_standard(self):
        for aspect in ("1:1", "16:9", "9:16", "21:9", "4:1"):
            with self.subTest(aspect=aspect):
                s = self.settings("--provider", "gemini", "--aspect", aspect)
                self.assertEqual((s["model"], s["resolution"], s["overridden"]), ("gemini-nano-banana-2.1", "1K", []))


class AboveStandardNeedsReasonTest(IsolatedStoreTest):
    CASES = [
        ("short edge over 1024", ["--size", "1536x1536"], "size"),
        ("4K-ish size", ["--size", "3840x2160"], "size"),
        ("high quality", ["--quality", "high"], "quality"),
        ("low quality is still a deliberate change", ["--quality", "low"], "quality"),
        ("other OpenAI model", ["--model", "gpt-image-2.5-flare"], "model"),
        ("Gemini 2K", ["--provider", "gemini", "--resolution", "2K"], "resolution"),
        ("Gemini 4K", ["--provider", "gemini", "--resolution", "4K"], "resolution"),
        ("Gemini thinking high", ["--provider", "gemini", "--thinking", "high"], "thinking"),
    ]

    def test_blocked_without_reason_and_no_api_call(self):
        for label, args, _ in self.CASES:
            with self.subTest(label):
                code, text, _ = self.run_script("--prompt", "x", *args)  # real run, not dry: must stop before the API
                self.assertNotEqual(code, 0)
                self.assertIn("Above-standard", text)
        self.assertEqual(self.run_dirs(), [])
        self.assertEqual(self.ledger_lines(), [])

    def test_allowed_with_reason_and_flagged(self):
        for label, args, field in self.CASES:
            with self.subTest(label):
                code, text, data = self.run_script("--prompt", "x", "--dry-run", "--reason", "print poster", *args)
                self.assertEqual(code, 0, text)
                self.assertIn(field, data["settings"]["overridden"])
                self.assertEqual(data["settings"]["reason"], "print poster")


class NeverAllowedTest(IsolatedStoreTest):
    def rejected(self, *args):
        code, text, _ = self.run_script("--prompt", "x", "--dry-run", "--reason", "r", *args)
        self.assertNotEqual(code, 0, f"expected rejection for {args}")
        return text

    def test_auto_size_and_quality_rejected(self):
        self.assertIn("auto", self.rejected("--size", "auto"))
        self.assertIn("auto", self.rejected("--quality", "auto"))

    def test_sizes_the_api_would_reject(self):
        for size, why in [("1000x1500", "multiples of 16"), ("4096x2304", "3840"), ("3200x1024", "1:3 and 3:1"),
                          ("640x640", "655,360"), ("1536x1024px", "WIDTHxHEIGHT")]:
            with self.subTest(size=size):
                self.assertIn(why, self.rejected("--size", size))

    def test_quality_must_exist_for_the_model(self):
        self.assertIn("gpt-image-2", self.rejected("--model", "gpt-image-2", "--quality", "xhigh"))

    def test_gemini_options_validated(self):
        self.assertIn("--aspect", self.rejected("--provider", "gemini", "--aspect", "5:7"))
        self.assertIn("--thinking", self.rejected("--provider", "gemini", "--thinking", "max"))

    def test_model_must_match_provider_and_be_enabled(self):
        self.assertIn("Unknown gemini model", self.rejected("--provider", "gemini", "--model", "gpt-image-2.5-sunburst"))
        self.assertIn("pricing reference only", self.rejected("--provider", "gemini", "--model", "gemini-3-pro-image"))
        self.assertIn("Unknown openai model", self.rejected("--model", "dall-e-3"))

    def test_missing_input_image_rejected_before_anything(self):
        code, text, _ = self.run_script("--prompt", "x", "--input", str(self.tmp / "nope.png"))
        self.assertNotEqual(code, 0)
        self.assertIn("Input image not found", text)
        self.assertEqual(self.run_dirs(), [])

    def test_prompt_is_required(self):
        code, _, _ = self.run_script("--dry-run")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
