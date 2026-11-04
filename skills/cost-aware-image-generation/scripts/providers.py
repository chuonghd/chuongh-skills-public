"""HTTP calls to Gemini and OpenAI image APIs (stdlib only), plus token normalization.

Each provider function returns:
  images:   list of (bytes, ext)
  tokens:   normalized dict with keys input_text, input_image, output_image,
            output_text, thinking (ints, or None when the API doesn't report it)
  raw_meta: the API response with base64 image data stripped, for auditing
"""

import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path

from pricing import MODELS

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
GEMINI_API_REVISION = "2026-05-20"
OPENAI_BASE = "https://api.openai.com/v1/images"
TIMEOUT_S = 300  # complex prompts can take up to ~2 minutes


def _require_key(name):
    key = os.environ.get(name)
    if not key:
        raise SystemExit(f"{name} is not set. Copy .env.example to .env in the skill folder and fill it in.")
    return key


def redact_keys(text):
    """Replace any API key value (full or a long fragment) so keys never reach logs or the agent."""
    for name in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
        key = os.environ.get(name)
        if key:
            text = text.replace(key, f"[{name} REDACTED]")
            if len(key) > 16:  # providers sometimes echo a partial key, e.g. "sk-abc...wxyz"
                text = text.replace(key[:8], "[REDACTED]").replace(key[-6:], "[REDACTED]")
    return text


def _post_json(url, headers, body):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(redact_keys(f"HTTP {err.code} from {url}: {detail}")) from None
    except urllib.error.URLError as err:
        raise RuntimeError(redact_keys(f"Network error calling {url}: {err.reason}")) from None


def _read_image(path):
    data = Path(path).read_bytes()
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    return data, mime


def strip_base64(obj):
    """Recursively replace long base64 payloads so metadata files stay small."""
    if isinstance(obj, dict):
        return {
            k: (f"<{len(v)} chars stripped>" if k in ("data", "b64_json") and isinstance(v, str) else strip_base64(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [strip_base64(v) for v in obj]
    return obj


def _by_modality(entries):
    """Turn [{"modality": "image", "tokens": 1120}, ...] into {"image": 1120, ...}."""
    result = {}
    for entry in entries or []:
        key = str(entry.get("modality", "")).lower()
        result[key] = result.get(key, 0) + (entry.get("tokens") or 0)
    return result


def _ext_for_mime(mime):
    return {"image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "png")


# ---------------------------------------------------------------------------
# Gemini (Interactions API)
# ---------------------------------------------------------------------------

def build_gemini_request(model, prompt, input_paths, aspect_ratio, resolution, thinking_level):
    parts = [{"type": "text", "text": prompt}]
    for path in input_paths:
        data, mime = _read_image(path)
        parts.append({"type": "image", "mime_type": mime, "data": base64.b64encode(data).decode()})
    return {
        "model": model,
        "input": parts,
        "response_format": {"type": "image", "aspect_ratio": aspect_ratio, "image_size": resolution},
        "generation_config": {"thinking_level": thinking_level},
    }


def call_gemini(request_body, resolution, has_input_images):
    key = _require_key("GEMINI_API_KEY")
    resp = _post_json(GEMINI_URL, {"x-goog-api-key": key, "Api-Revision": GEMINI_API_REVISION}, request_body)

    images = []
    for step in resp.get("steps", []):
        if step.get("type") != "model_output":
            continue
        for block in step.get("content", []):
            if block.get("type") == "image" and block.get("data"):
                images.append((base64.b64decode(block["data"]), _ext_for_mime(block.get("mime_type"))))

    usage = resp.get("usage", {}) or {}
    total_in = usage.get("total_input_tokens") or 0
    total_out = usage.get("total_output_tokens") or 0
    in_by = _by_modality(usage.get("input_tokens_by_modality"))
    out_by = _by_modality(usage.get("output_tokens_by_modality"))
    # Prefer the API's per-modality counts. Fallback: Gemini bills a fixed
    # image-token count per resolution. Output tokens that are not image tokens
    # are billed at the text rate. Thinking is reported separately from output.
    out_image = out_by.get("image", MODELS[request_body["model"]]["image_tokens"][resolution] * len(images))
    in_image = sum(v for k, v in in_by.items() if k != "text") if in_by else (None if has_input_images else 0)
    tokens = {
        "input_text": in_by.get("text", 0) if in_by else (None if has_input_images else total_in),
        "input_image": in_image,
        "input_total": total_in,
        "output_image": out_image,
        "output_text": max(total_out - out_image, 0),
        "thinking": usage.get("total_thought_tokens") or 0,
    }
    return images, tokens, strip_base64(resp)


# ---------------------------------------------------------------------------
# OpenAI (Image API: generations, or edits when input images are given)
# ---------------------------------------------------------------------------

def build_openai_request(model, prompt, input_paths, size, quality):
    body = {"model": model, "prompt": prompt, "size": size, "quality": quality, "n": 1, "output_format": "png"}
    if input_paths:
        body["images"] = []
        for path in input_paths:
            data, mime = _read_image(path)
            body["images"].append({"image_url": f"data:{mime};base64,{base64.b64encode(data).decode()}"})
    return body


def call_openai(request_body):
    key = _require_key("OPENAI_API_KEY")
    endpoint = "edits" if request_body.get("images") else "generations"
    resp = _post_json(f"{OPENAI_BASE}/{endpoint}", {"Authorization": f"Bearer {key}"}, request_body)

    images = [(base64.b64decode(d["b64_json"]), "png") for d in resp.get("data", []) if d.get("b64_json")]

    usage = resp.get("usage") or {}
    in_details = usage.get("input_tokens_details") or {}
    out_details = usage.get("output_tokens_details") or {}
    has_usage = bool(usage)
    tokens = {
        "input_text": in_details.get("text_tokens") if has_usage else None,
        "input_image": in_details.get("image_tokens") if has_usage else None,
        "input_total": usage.get("input_tokens") if has_usage else None,
        # When no breakdown is given, all output tokens are image tokens.
        "output_image": out_details.get("image_tokens", usage.get("output_tokens")) if has_usage else None,
        "output_text": out_details.get("text_tokens", 0) if has_usage else None,
        "thinking": 0 if has_usage else None,
    }
    return images, tokens, strip_base64(resp)
