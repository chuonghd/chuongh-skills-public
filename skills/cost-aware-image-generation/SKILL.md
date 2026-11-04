---
name: cost-aware-image-generation
description: "Generate or edit images with a Gemini or OpenAI API key at a predictable, deliberately chosen cost. Enforces a standard tier of medium quality and ~1024px on the short edge (any shape: square, portrait or landscape), requires a stated reason for any larger or higher-quality setting, and logs every generation (prompt, inputs, outputs, full token counts, cost in USD and VND) to a local ledger. Use when the user asks to generate, create, render, or edit an image via the Gemini (Nano Banana) or OpenAI (GPT Image) API, or asks how much their image generations cost."
---

# Cost-Aware Image Generation

Generate images through the Gemini or OpenAI image APIs so that every call has a deliberate size and quality, a known cost, and a full audit trail.

All API work goes through `scripts/generate_image.py` (Python 3 standard library only, nothing to install). Never call the image APIs any other way from this skill: the script enforces the defaults and writes the ledger.

## Providers and the standard tier

The standard tier is **medium quality with ~1024px on the short edge, in whatever shape the use needs**: square, portrait or landscape. Shape is a free choice; it is not an override.

| Provider | Model | Standard tier (no reason needed) | Used when nothing is given |
|---|---|---|---|
| `gemini` (needs `GEMINI_API_KEY`) | `gemini-nano-banana-2.1` | `--resolution 1K --thinking medium`, any `--aspect` (e.g. 1:1 = 1024x1024, 3:2 = 1264x848, 2:3 = 848x1264) | `--aspect 2:3` |
| `openai` (needs `OPENAI_API_KEY`) | `gpt-image-2.5-sunburst` | `--quality medium`, any `--size` with short edge ≤ 1024 (e.g. 1024x1024, 1536x1024, 1024x1536) | `--size 1024x1536` |

Keys are read from the shell environment first, then from `.env` in this skill folder (gitignored; template: `.env.example`).

## API keys never enter the conversation

The script loads keys itself; the agent never needs to see them.

- **Never read, open, cat, grep, print or summarize `.env`**, and never echo `$GEMINI_API_KEY` / `$OPENAI_API_KEY` or run `env`/`printenv`. `.env.example` (no real values) is fine to read.
- To check setup, run only `python3 <skill-dir>/scripts/generate_image.py --check-keys`. It prints `set` / `NOT set`, never values.
- Never pass a key as a command-line argument or write it into any other file.
- Never ask the user to paste a key into chat. If a key is missing, tell them to copy `.env.example` to `.env` in this skill folder and fill it in themselves.
- If the user pastes a key into chat anyway, don't repeat it; advise them to rotate it, since it is now in the conversation history.

If only one key is set, use that provider. If both are set and the user has no preference, ask once which to use.

## The cost rule

**Stay in the standard tier for nearly every task.** Medium quality at ~1024px on the short edge is enough for social posts, blog and web images, product mockups, slides, concepts and drafts. Pick the shape the use needs (square avatar, landscape banner, portrait poster) without asking.

Go above the standard tier only for a concrete requirement it cannot meet, for example:
- Print or large-display output that genuinely needs more pixels (short edge above 1024, or Gemini 2K/4K).
- Fine detail or small legible text that failed at medium on a previous attempt.

These count as above-standard and need a reason: OpenAI short edge > 1024 or quality other than `medium`; Gemini resolution 2K/4K or thinking other than `medium`; a model other than the default.

Before any above-standard run:
1. Tell the user in one sentence what you want to change and why.
2. Run with `--dry-run` and show the estimate.
3. Get the user's go-ahead, then pass the same reason via `--reason "..."`.

The script refuses above-standard settings without `--reason`, refuses `auto` size/quality, and always generates exactly one image (`n=1`, no partial previews, Standard tier — never Batch). Do not work around these limits; generate again instead of asking for several images per call.

Lower-cost options worth suggesting when they fit: `--quality low` (OpenAI) or `--thinking minimal` (Gemini) for rough drafts.

## Workflow

1. **Understand the use.** Where will the image be shown and at what size? If unclear, assume the standard tier fits and say so; choose the shape from the use.
2. **Write the prompt.** For long prompts, save to a file and use `--prompt-file`.
3. **Pick settings.** Standard tier in the right shape, unless the cost rule above justifies more.
4. **Generate:**
   ```bash
   python3 <skill-dir>/scripts/generate_image.py --provider openai \
     --prompt "..." [--input ref.png ...] [--label short-name] [--out ./path/in/project.png]
   ```
   - `--input` (repeatable) sends reference images; OpenAI then uses its edits endpoint.
   - `--out` copies the final image into the user's project; the original stays in the store.
   - Calls can take up to ~2 minutes.
5. **Report back** from the script's JSON output, always including:
   - Output image path(s).
   - Token counts: input text, input image, output image, output text, thinking. Write "not reported" for any `null`.
   - Cost in USD and VND, plus the exchange rate and its source.
   - If `cost_usd` is `null`, say the provider did not return usage, so cost is unknown for this run.

## Where everything is stored

One global store for all projects: `~/.image-gen/` (override with `IMAGE_GEN_HOME`).

```
~/.image-gen/
  ledger.jsonl          one JSON line per generation (successes and failures)
  fx-cache.json         today's USD->VND rate
  runs/<YYYY-MM-DD_HHMMSS>_<slug>/
    prompt.txt          exact prompt sent
    request.json        request body (base64 image data stripped)
    response-meta.json  API response (base64 image data stripped)
    run.json            same record as the ledger line
    inputs/             copies of reference images
    outputs/            generated image(s)
```

Each ledger line contains: `id`, `created_at`, `project` (working directory), `settings` (model, size or aspect/resolution, quality or thinking, `overridden`, `reason`), `prompt`, `inputs`, `outputs`, `tokens`, `cost_breakdown_usd`, `cost_usd`, `fx` (`rate`, `source`, `date`), `cost_vnd`, `duration_s`, `status`. This is the source for any later usage or cost report.

To answer "how much have I spent?", read `ledger.jsonl` and sum `cost_usd` / `cost_vnd`.

To show usage visually, run `python3 <skill-dir>/scripts/export_usage_html.py --open`. It writes `~/.image-gen/usage-report.html`: total and per-model spend, then one row per generation with thumbnail, settings, full prompt, every token count, and cost in USD and VND. Search and provider filtering are built in. Images open in a zoomable popup; each run's **Pricing** button shows tokens × rate = cost; the header's **Models & pricing** button compares every catalog model (rates in USD and VND, estimated cost per image at the standard tier, and the user's measured average). Re-run it after new generations; the file must stay in the store folder for thumbnails to load.

## Pricing facts (Standard tier, checked 2026-11-04)

- **Gemini Nano Banana 2.1:** image output $30 per 1M tokens, billed at a fixed count per image — 1K = 1,120 tokens ($0.0336), 2K = 1,680 ($0.0504), 4K = 3,780 ($0.113), whatever the aspect ratio. Input (text, image or video) $1.50 per 1M. Text and thinking output $7.50 per 1M. Thinking is billed on top of the image: a measured default run (1K, 2:3, thinking `medium`) used 1,087 thinking + 351 non-image output tokens, so it cost about **$0.044**, not $0.034. `--thinking minimal` is the cheaper choice for simple prompts.
- **OpenAI GPT Image 2.5 Sunburst:** image output $30 per 1M, image input $8 per 1M, text input $5 per 1M. OpenAI publishes no per-image price; token use depends on size and quality, so the exact cost is known only after the call. The pre-call estimate reuses the last ledger run with the same model, size and quality. A measured default run (medium, 1024x1536) used 343 image output tokens: about **$0.0105**.
- USD->VND: Vietcombank USD sell rate (what a Vietnamese card is roughly charged), falling back to the open.er-api.com market rate; fetched once per day.

Other models (catalog in `scripts/pricing.py` → `MODELS`; shown in the report's Models & pricing table):
- **GPT Image 2.5 Flare** (`--model gpt-image-2.5-flare`) and **GPT Image 2** (`--model gpt-image-2`, quality up to `high`): same token rates as Sunburst, usable with `--provider openai`. A non-default model counts as above-standard, so it needs `--reason`.
- **Nano Banana 2** (`gemini-3.1-flash-image`, $60/1M image output, ~$0.067 per 1K image) and **Nano Banana Pro** (`gemini-3-pro-image`, $120/1M, ~$0.134 per 1K image): pricing reference only; the script refuses to generate with them.

When prices change, update `MODELS` and `PRICES_CHECKED_ON` in `scripts/pricing.py`, and this section.
