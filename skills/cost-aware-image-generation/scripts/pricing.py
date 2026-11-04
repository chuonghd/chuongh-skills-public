"""Model catalog, price tables, per-generation cost math, and the USD->VND rate.

All prices are Standard (non-batch) tier, USD per 1M tokens, taken from the
official pages below. Update MODELS (and PRICES_CHECKED_ON) when they change.
"""

import json
import re
import time
import urllib.request
from datetime import date
from pathlib import Path

PRICES_CHECKED_ON = "2026-11-04"
PRICE_SOURCES = [
    ("Gemini pricing", "https://ai.google.dev/gemini-api/docs/pricing"),
    ("Gemini image guide", "https://ai.google.dev/gemini-api/docs/image-generation"),
    ("OpenAI pricing", "https://developers.openai.com/api/docs/pricing"),
    ("OpenAI image guide", "https://developers.openai.com/api/docs/guides/image-generation"),
]


def _rates(text_in, image_in, image_out, text_out=0.0):
    """USD per 1M tokens. Thinking is billed at the text output rate."""
    return {"input_text": text_in, "input_image": image_in, "output_image": image_out,
            "output_text": text_out, "thinking": text_out}


_GPT_IMAGE_RATES = _rates(5.00, 8.00, 30.00)  # GPT Image 2.5 Sunburst/Flare share GPT Image 2's token rates
_GPT_QUALITIES_2_5 = ["low", "medium", "high", "xhigh", "max"]

# Every model shown in the pricing table. `generate`: the script can call it.
# Gemini models bill a fixed number of output tokens per image by resolution
# (`image_tokens`, same for every aspect ratio), per the pricing page footnotes.
MODELS = {
    "gemini-nano-banana-2.1": {
        "label": "Nano Banana 2.1", "provider": "gemini", "latest": True, "generate": True,
        "rates": _rates(1.50, 1.50, 30.00, 7.50),
        "image_tokens": {"1K": 1120, "2K": 1680, "4K": 3780},
        "sizes": "1K–4K, 14 ratios",
        "note": "Thinking billed on top.",
        "standard": {"settings": {"resolution": "1K"}, "basis": "1K, image output only"},
    },
    "gemini-3.1-flash-image": {
        "label": "Nano Banana 2", "provider": "gemini", "generate": False,
        "rates": _rates(0.50, 0.50, 60.00, 3.00),
        "image_tokens": {"0.5K": 747, "1K": 1120, "2K": 1680, "4K": 2520},
        "sizes": "0.5K–4K, 14 ratios",
        "note": "Previous generation.",
        "standard": {"settings": {"resolution": "1K"}, "basis": "1K, image output only"},
    },
    "gemini-3-pro-image": {
        "label": "Nano Banana Pro", "provider": "gemini", "generate": False,
        "rates": _rates(2.00, 2.00, 120.00, 12.00),
        "image_tokens": {"1K": 1120, "2K": 1120, "4K": 2000},
        "sizes": "1K–4K, 10 ratios",
        "note": "Premium; always thinks.",
        "standard": {"settings": {"resolution": "1K"}, "basis": "1K, image output only"},
    },
    "gpt-image-2.5-sunburst": {
        "label": "GPT Image 2.5 Sunburst", "provider": "openai", "default": True, "latest": True, "generate": True,
        "rates": _GPT_IMAGE_RATES, "qualities": _GPT_QUALITIES_2_5,
        "sizes": "Any size, up to 3840px",
        "note": "Best for precise edits.",
        "standard": {"settings": {"size": "1024x1536", "quality": "medium"}, "basis": "1024x1536 medium, image output",
                     "output_tokens": 343, "source": "measured 2026-11-04"},
    },
    "gpt-image-2.5-flare": {
        "label": "GPT Image 2.5 Flare", "provider": "openai", "latest": True, "generate": True,
        "rates": _GPT_IMAGE_RATES, "qualities": _GPT_QUALITIES_2_5,
        "sizes": "Any size, up to 3840px",
        "note": "Faster everyday images.",
        "standard": {"settings": {"size": "1024x1536", "quality": "medium"}, "basis": "1024x1536 medium, image output",
                     "output_tokens": None, "source": "not published; measure with one run"},
    },
    "gpt-image-2": {
        "label": "GPT Image 2", "provider": "openai", "generate": True,
        "rates": _GPT_IMAGE_RATES, "qualities": ["low", "medium", "high"],
        "sizes": "Any size, up to 3840px",
        "note": "Previous generation; up to high quality.",
        "standard": {"settings": {"size": "1024x1536", "quality": "medium"}, "basis": "1024x1536 medium, image output",
                     "usd": 0.041, "source": "OpenAI image guide cost table"},
    },
}

# Model id -> rates, used by the cost math.
PRICES = {model_id: info["rates"] for model_id, info in MODELS.items()}


def standard_image_estimate(model_id):
    """(usd or None, basis, source) for one image at the standard tier (Gemini 1K; OpenAI 1024x1536 medium)."""
    info = MODELS[model_id]
    std = info["standard"]
    if info["provider"] == "gemini":
        tokens = info["image_tokens"]["1K"]
        return tokens * info["rates"]["output_image"] / 1_000_000, std["basis"], f"{tokens:,} tokens, Gemini pricing page"
    if std.get("usd") is not None:
        return std["usd"], std["basis"], std["source"]
    if std.get("output_tokens"):
        usd = std["output_tokens"] * info["rates"]["output_image"] / 1_000_000
        return usd, std["basis"], f"{std['output_tokens']:,} tokens, {std['source']}"
    return None, std["basis"], std["source"]

TOKEN_FIELDS = ("input_text", "input_image", "output_image", "output_text", "thinking")


def compute_cost_usd(model, tokens):
    """Return (per-bucket USD dict, total USD or None if usage was not reported).

    When the text/image input split is unknown but both share one rate (Gemini),
    the input total is billed under input_text so the total stays exact.
    """
    rates = PRICES.get(model)
    if rates is None:
        raise SystemExit(f"No price table for model '{model}'. Add it to pricing.py first.")
    if tokens.get("output_image") is None:
        return {}, None  # provider returned no usage; cost cannot be computed

    counts = dict(tokens)
    if counts.get("input_text") is None or counts.get("input_image") is None:
        if rates["input_text"] != rates["input_image"]:
            return {}, None
        counts["input_text"], counts["input_image"] = counts.get("input_total") or 0, 0

    breakdown = {f: round((counts.get(f) or 0) * rates[f] / 1_000_000, 6) for f in TOKEN_FIELDS}
    return breakdown, round(sum(breakdown.values()), 6)


# ---------------------------------------------------------------------------
# USD -> VND rate: fetched live, cached once per day in the store.
# Primary: Vietcombank USD sell rate (what a Vietnamese card is roughly charged).
# Fallback: open.er-api.com mid-market rate.
# ---------------------------------------------------------------------------

VCB_URL = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"
ER_API_URL = "https://open.er-api.com/v6/latest/USD"


def _http_get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "cost-aware-image-generation"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _fetch_vietcombank():
    match = re.search(r'CurrencyCode="USD"[^>]*Sell="([\d,\.]+)"', _http_get(VCB_URL))
    if not match:
        raise ValueError("USD sell rate not found in Vietcombank feed")
    return float(match.group(1).replace(",", "")), "vietcombank-sell"


def _fetch_er_api():
    data = json.loads(_http_get(ER_API_URL))
    return float(data["rates"]["VND"]), "open.er-api-mid"


def get_usd_vnd_rate(store_dir):
    """Return {rate, source, date}. Uses today's cache, else fetches, else last cache."""
    cache_file = Path(store_dir) / "fx-cache.json"
    today = date.today().isoformat()
    cached = json.loads(cache_file.read_text()) if cache_file.exists() else None
    if cached and cached.get("date") == today:
        return cached

    for fetch in (_fetch_vietcombank, _fetch_er_api):
        try:
            rate, source = fetch()
            fx = {"rate": rate, "source": source, "date": today, "fetched_at": int(time.time())}
            cache_file.write_text(json.dumps(fx, indent=2))
            return fx
        except Exception:  # noqa: BLE001 - try the next source
            continue

    if cached:
        return {**cached, "source": cached["source"] + " (stale cache, offline)"}
    raise SystemExit("Could not fetch USD->VND rate and no cached rate exists.")
