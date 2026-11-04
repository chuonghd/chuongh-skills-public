#!/usr/bin/env python3
"""Cost-aware image generation for Gemini and OpenAI (stdlib only).

Generates exactly one image per call with explicit size/quality, saves every
input and output artifact, and appends a ledger line with full token counts
and cost in USD and VND.

Store layout (default ~/.image-gen, override with IMAGE_GEN_HOME):
  ledger.jsonl                    one JSON line per generation
  fx-cache.json                   today's USD->VND rate
  daily-spend-ack.json            today's acknowledged daily spend alert ($10 steps)
  runs/<timestamp>_<slug>/
    prompt.txt  request.json  response-meta.json  run.json
    inputs/     outputs/

Examples:
  generate_image.py --prompt "A lighthouse at dusk"                  # OpenAI GPT Image 2.5 Sunburst (default)
  generate_image.py --provider gemini --prompt "A lighthouse at dusk"
  generate_image.py --provider openai --prompt-file p.txt --input ref.png --out ./hero.png
  generate_image.py --provider openai --size 1536x1024 --reason "landscape web hero" --prompt "..."
  generate_image.py --provider openai --prompt "..." --dry-run
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent  # resolves through install symlinks to the real folder
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pricing import MODELS, PRICES, PRICES_CHECKED_ON, compute_cost_usd, get_usd_vnd_rate  # noqa: E402
import providers  # noqa: E402
import daily_spend_guard  # noqa: E402

# Standard tier: medium quality, short edge ~1024px in any shape (square, portrait, landscape).
# Shape is free; only a bigger short edge, a higher resolution tier, or non-medium quality needs --reason.
# The size/aspect values below are just what's used when none is given.
STANDARD_MAX_SHORT_EDGE = 1024
DEFAULTS = {
    "gemini": {"model": "gemini-nano-banana-2.1", "aspect": "2:3", "resolution": "1K", "thinking": "medium"},
    "openai": {"model": "gpt-image-2.5-sunburst", "size": "1024x1536", "quality": "medium"},
}
GEMINI_ASPECTS = {"1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"}
GEMINI_THINKING = {"minimal", "medium", "high"}


def store_dir():
    path = Path(os.environ.get("IMAGE_GEN_HOME", Path.home() / ".image-gen")).expanduser()
    (path / "runs").mkdir(parents=True, exist_ok=True)
    return path


def load_env_file(path):
    """Load KEY=VALUE lines from the skill folder's gitignored .env; shell variables win."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


def validate_openai_size(size):
    match = re.fullmatch(r"(\d+)x(\d+)", size or "")
    if not match:
        raise SystemExit(f"--size must be WIDTHxHEIGHT (got '{size}'); 'auto' is not allowed.")
    w, h = int(match[1]), int(match[2])
    problems = []
    if w % 16 or h % 16:
        problems.append("width and height must be multiples of 16")
    if max(w, h) > 3840:
        problems.append("no edge may exceed 3840px")
    if not (1 / 3 <= w / h <= 3):
        problems.append("aspect ratio must be between 1:3 and 3:1")
    if not (655_360 <= w * h <= 8_294_400):
        problems.append("total pixels must be between 655,360 and 8,294,400")
    if problems:
        raise SystemExit(f"Invalid --size {size}: " + "; ".join(problems))


def resolve_settings(args):
    """Fill defaults, validate, and enforce --reason for any non-default choice."""
    d = DEFAULTS[args.provider]
    s = {"provider": args.provider, "model": args.model or d["model"]}
    info = MODELS.get(s["model"])
    if not info or info["provider"] != args.provider:
        usable = [m for m, i in MODELS.items() if i["provider"] == args.provider and i["generate"]]
        raise SystemExit(f"Unknown {args.provider} model '{s['model']}'. Usable: {', '.join(usable)}")
    if not info["generate"]:
        raise SystemExit(f"'{s['model']}' is listed for pricing reference only; this skill can't generate with it yet.")
    if args.provider == "gemini":
        s.update(aspect=args.aspect or d["aspect"], resolution=args.resolution or d["resolution"],
                 thinking=args.thinking or d["thinking"])
        if s["aspect"] not in GEMINI_ASPECTS:
            raise SystemExit(f"--aspect must be one of {sorted(GEMINI_ASPECTS)}")
        if s["resolution"] not in info["image_tokens"]:
            raise SystemExit(f"--resolution must be one of {list(info['image_tokens'])} for {s['model']}")
        if s["thinking"] not in GEMINI_THINKING:
            raise SystemExit(f"--thinking must be one of {sorted(GEMINI_THINKING)}")
        # Any aspect ratio at 1K stays in the standard ~1024px tier.
        overridden = [k for k in ("model", "resolution", "thinking") if s[k] != d[k]]
    else:
        s.update(size=args.size or d["size"], quality=args.quality or d["quality"])
        validate_openai_size(s["size"])
        if s["quality"] not in info["qualities"]:
            raise SystemExit(f"--quality must be one of {info['qualities']} for {s['model']}; 'auto' is not allowed.")
        overridden = [k for k in ("model", "quality") if s[k] != d[k]]
        # Any shape is fine as long as the short edge stays at ~1024px or below.
        if min(map(int, s["size"].split("x"))) > STANDARD_MAX_SHORT_EDGE:
            overridden.insert(1, "size")

    if overridden and not args.reason:
        raise SystemExit(
            f"Above-standard {', '.join(overridden)} requested. Medium quality with a ~1024px short edge "
            "(any shape) is the cost-optimal choice for most work; pass --reason \"<why this task needs it>\" to proceed."
        )
    s["overridden"] = overridden
    s["reason"] = args.reason
    return s


def estimate(settings, ledger_path):
    """Pre-call estimate: exact image-output cost for Gemini, last observed cost for OpenAI."""
    if settings["provider"] == "gemini":
        tokens = MODELS[settings["model"]]["image_tokens"][settings["resolution"]]
        usd = tokens * PRICES[settings["model"]]["output_image"] / 1_000_000
        return {"output_image_usd": round(usd, 4), "note": "exact image output; input and thinking add a little"}
    if ledger_path.exists():
        for line in reversed(ledger_path.read_text().splitlines()):
            rec = json.loads(line)
            st = rec.get("settings", {})
            if (rec.get("status") == "ok" and rec.get("cost_usd") is not None and st.get("model") == settings["model"]
                    and st.get("size") == settings["size"] and st.get("quality") == settings["quality"]):
                return {"last_observed_usd": rec["cost_usd"], "from_run": rec["id"]}
    return {"note": "no previous run with this model/size/quality; cost known after the call"}


def slugify(text, limit=40):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit] or "image"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--check-keys", action="store_true",
                   help="report which API keys are set (never their values) and exit")
    p.add_argument("--provider", choices=["gemini", "openai"], default="openai",
                   help="openai (default: GPT Image 2.5 Sunburst) or gemini (Nano Banana 2.1)")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--prompt")
    src.add_argument("--prompt-file")
    p.add_argument("--input", action="append", default=[], help="reference image path (repeatable)")
    p.add_argument("--model")
    p.add_argument("--size", help="OpenAI WIDTHxHEIGHT, any shape; short edge >1024 needs --reason (default 1024x1536)")
    p.add_argument("--quality", help="OpenAI low|medium|high|xhigh|max (default medium)")
    p.add_argument("--aspect", help="Gemini aspect ratio, any supported (default 2:3)")
    p.add_argument("--resolution", help="Gemini 1K|2K|4K (default 1K)")
    p.add_argument("--thinking", help="Gemini minimal|medium|high (default medium)")
    p.add_argument("--reason", help="required when any setting differs from the defaults")
    p.add_argument("--label", help="short name for the run folder")
    p.add_argument("--out", help="also copy the final image to this path")
    p.add_argument("--dry-run", action="store_true", help="validate and estimate only; no API call")
    p.add_argument("--ack-daily-spend", type=int, metavar="USD",
                   help="acknowledge today's daily spend alert (10, 20, …) after the user agreed to continue")
    args = p.parse_args()

    load_env_file(SKILL_DIR / ".env")
    if args.check_keys:
        # Lets the agent confirm setup without ever reading the .env file or key values.
        for name in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
            print(f"{name}: {'set' if os.environ.get(name) else 'NOT set'}")
        return
    if args.prompt is None and args.prompt_file is None:
        p.error("one of --prompt / --prompt-file is required")

    prompt = args.prompt if args.prompt is not None else Path(args.prompt_file).read_text()
    for path in args.input:
        if not Path(path).is_file():
            raise SystemExit(f"Input image not found: {path}")
    settings = resolve_settings(args)
    store = store_dir()
    ledger = store / "ledger.jsonl"
    est = estimate(settings, ledger)

    if args.dry_run:
        print(json.dumps({"dry_run": True, "settings": settings, "estimate": est,
                          "daily_spend": daily_spend_guard.status(store, ledger)}, indent=2))
        return

    # Fail before creating any files if this provider's key is missing (dry runs don't need a key).
    providers.require_key("OPENAI_API_KEY" if settings["provider"] == "openai" else "GEMINI_API_KEY")
    # Stop before any API call when today's spend has crossed an unacknowledged $10 step.
    daily_spend_guard.check(store, ledger, args.ack_daily_spend)

    base_id = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{slugify(args.label or prompt)}"
    run_id, n = base_id, 2
    while (store / "runs" / run_id).exists():  # two runs in the same second with the same label
        run_id, n = f"{base_id}-{n}", n + 1
    run_dir = store / "runs" / run_id
    (run_dir / "inputs").mkdir(parents=True)
    (run_dir / "outputs").mkdir()
    (run_dir / "prompt.txt").write_text(prompt)
    saved_inputs = []
    for i, path in enumerate(args.input, 1):
        dest = run_dir / "inputs" / f"input-{i}{Path(path).suffix.lower()}"
        shutil.copy2(path, dest)
        saved_inputs.append({"source": str(Path(path).resolve()), "saved": str(dest)})

    if settings["provider"] == "gemini":
        body = providers.build_gemini_request(settings["model"], prompt, args.input, settings["aspect"],
                                              settings["resolution"], settings["thinking"])
    else:
        body = providers.build_openai_request(settings["model"], prompt, args.input, settings["size"],
                                              settings["quality"])
    (run_dir / "request.json").write_text(json.dumps(providers.strip_base64(body), indent=2))

    record = {"id": run_id, "created_at": datetime.now().astimezone().isoformat(), "project": os.getcwd(),
              "settings": settings, "prompt": prompt, "inputs": saved_inputs, "estimate": est,
              "run_dir": str(run_dir)}
    started = time.time()
    try:
        if settings["provider"] == "gemini":
            images, tokens, meta = providers.call_gemini(body, settings["resolution"], bool(args.input))
        else:
            images, tokens, meta = providers.call_openai(body)
    except Exception as err:  # noqa: BLE001 - log the failure, then exit non-zero
        record.update(status="error", error=str(err), duration_s=round(time.time() - started, 1), cost_usd=None)
        _write_record(ledger, run_dir, record)
        raise SystemExit(f"Generation failed (logged as {run_id}): {err}")

    (run_dir / "response-meta.json").write_text(json.dumps(meta, indent=2))
    outputs = []
    for i, (data, ext) in enumerate(images, 1):
        dest = run_dir / "outputs" / f"image-{i}.{ext}"
        dest.write_bytes(data)
        outputs.append(str(dest))
    if args.out and outputs:
        Path(args.out).expanduser().parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(outputs[0], Path(args.out).expanduser())

    breakdown, usd = compute_cost_usd(settings["model"], tokens)
    fx = get_usd_vnd_rate(store)
    record.update(
        status="ok" if outputs else "no_image",
        duration_s=round(time.time() - started, 1),
        outputs=outputs,
        copied_to=str(Path(args.out).expanduser().resolve()) if args.out and outputs else None,
        tokens=tokens,
        cost_breakdown_usd=breakdown,
        # Rates used for this run, so old entries keep their real pricing if prices.py changes later.
        rates_usd_per_1m=PRICES[settings["model"]],
        prices_checked_on=PRICES_CHECKED_ON,
        cost_usd=usd,
        fx=fx,
        cost_vnd=round(usd * fx["rate"]) if usd is not None else None,
    )
    _write_record(ledger, run_dir, record)
    print(json.dumps({k: record[k] for k in ("id", "status", "outputs", "copied_to", "tokens", "cost_breakdown_usd",
                                             "cost_usd", "cost_vnd", "fx", "duration_s", "run_dir", "report")}, indent=2))


def _write_record(ledger, run_dir, record):
    (run_dir / "run.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    with ledger.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    record["report"] = refresh_report(ledger.parent)


def auto_update_enabled():
    """AUTO_UPDATE_REPORT in the shell or the skill's .env; on unless set to false/0/no/off."""
    return os.environ.get("AUTO_UPDATE_REPORT", "true").strip().lower() not in ("false", "0", "no", "off")


def refresh_report(store):
    """Rebuild the usage report after a run (never opens it). A report problem never fails the generation."""
    if not auto_update_enabled():
        return "auto-update off (AUTO_UPDATE_REPORT=false)"
    try:
        import export_usage_html  # imported here so a report bug can't break generation at startup
        return str(export_usage_html.write_report(store))
    except Exception as err:  # noqa: BLE001
        return f"not updated: {err}"


if __name__ == "__main__":
    main()
