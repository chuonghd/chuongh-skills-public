"""Shared test setup: an isolated store, no real keys, no network.

Every test that runs the script goes through `IsolatedStoreTest`, which:
  - points IMAGE_GEN_HOME at a temp folder (never the real ~/.image-gen),
  - stops the skill's real .env from loading and sets fake keys,
  - replaces the HTTP layer so any unexpected network call fails the test.
Responses below mirror the shapes the real APIs returned on 2026-11-04.
"""

import base64
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import daily_spend_guard  # noqa: E402,F401  (re-exported for tests)
import generate_image  # noqa: E402
import pricing  # noqa: E402
import providers  # noqa: E402

REAL_POST_JSON = providers._post_json  # the unpatched HTTP call, for tests that mock urlopen instead

# 1x1 PNG, enough for "an image was saved".
PNG_B64 = base64.b64encode(bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")).decode()


def openai_response(text_in=32, image_in=0, image_out=343, usage=True):
    """Image API response shape for gpt-image-2.5-sunburst."""
    resp = {"created": 0, "background": "opaque", "data": [{"b64_json": PNG_B64}], "output_format": "png",
            "quality": "medium", "size": "1024x1536"}
    if usage:
        resp["usage"] = {"input_tokens": text_in + image_in,
                         "input_tokens_details": {"image_tokens": image_in, "text_tokens": text_in},
                         "output_tokens": image_out, "output_tokens_details": {"image_tokens": image_out, "text_tokens": 0},
                         "total_tokens": text_in + image_in + image_out}
    return resp


def gemini_response(text_in=27, image_in=0, image_out=1120, other_out=351, thought=1087, by_modality=True):
    """Interactions API response shape for gemini-nano-banana-2.1."""
    usage = {"total_input_tokens": text_in + image_in, "total_output_tokens": image_out + other_out,
             "total_thought_tokens": thought, "total_tokens": text_in + image_in + image_out + other_out + thought}
    if by_modality:
        usage["input_tokens_by_modality"] = [{"modality": "text", "tokens": text_in}] + (
            [{"modality": "image", "tokens": image_in}] if image_in else [])
        usage["output_tokens_by_modality"] = [{"modality": "image", "tokens": image_out}]
    return {"id": "x", "status": "completed", "usage": usage, "steps": [
        {"type": "thought"},
        {"type": "model_output", "content": [{"type": "image", "mime_type": "image/jpeg", "data": PNG_B64}]}]}


def ledger_record(cost_usd, days_ago=0, status="ok", **extra):
    when = (datetime.now().astimezone() - timedelta(days=days_ago)).isoformat()
    return {"id": f"seed-{cost_usd}-{days_ago}-{status}", "created_at": when, "status": status, "cost_usd": cost_usd,
            "settings": {"provider": "openai", "model": "gpt-image-2.5-sunburst", "size": "1024x1536", "quality": "medium",
                         "overridden": [], "reason": None},
            "prompt": "seed", "inputs": [], "outputs": [], **extra}


class IsolatedStoreTest(unittest.TestCase):
    """Temp store + fake keys + mocked network for every test."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.store = self.tmp / "store"
        self.ledger = self.store / "ledger.jsonl"
        env = {"IMAGE_GEN_HOME": str(self.store), "OPENAI_API_KEY": "sk-test-openai-0123456789abcdef",
               "GEMINI_API_KEY": "AIza-test-gemini-0123456789abcdef"}
        patches = [
            mock.patch.dict(os.environ, env),
            mock.patch.object(generate_image, "SKILL_DIR", self.tmp),          # never load the real .env
            mock.patch.object(providers, "_post_json", side_effect=AssertionError("unexpected API call")),
            mock.patch.object(pricing, "_http_get", return_value='<Exrate CurrencyCode="USD" Sell="25,910.00" />'),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.store.mkdir(parents=True)
        os.environ.pop("AUTO_UPDATE_REPORT", None)  # a value in the real shell must not leak in (env patch restores it)

    def api_returns(self, response):
        """Make the next API calls return `response`; returns the mock to inspect calls."""
        patcher = mock.patch.object(providers, "_post_json", return_value=response)
        m = patcher.start()
        self.addCleanup(patcher.stop)
        return m

    def seed(self, *records):
        with self.ledger.open("a") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def run_script(self, *argv):
        """Run generate_image.main(); returns (exit_code, stdout, parsed JSON or None)."""
        out = io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", ["generate_image.py", *argv]), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(io.StringIO()):
            try:
                generate_image.main()
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
                if not isinstance(e.code, int) and e.code:
                    out.write(str(e.code))
        text = out.getvalue()
        data = None
        if text.lstrip().startswith("{"):
            data = json.loads(text)
        return code, text, data

    def ledger_lines(self):
        return [json.loads(line) for line in self.ledger.read_text().splitlines()] if self.ledger.exists() else []

    def run_dirs(self):
        runs = self.store / "runs"
        return sorted(p.name for p in runs.iterdir()) if runs.exists() else []
