#!/usr/bin/env python3
"""Export the generation ledger to a single HTML usage report.

Reads <store>/ledger.jsonl and writes <store>/usage-report.html (store defaults
to ~/.image-gen, override with IMAGE_GEN_HOME). Images are linked by relative
path, so the report must stay inside the store folder to show thumbnails.

Usage:
  export_usage_html.py            # write the report and print its path
  export_usage_html.py --open     # also open it in the default browser
"""

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pricing import PRICES, PRICES_CHECKED_ON  # noqa: E402  (fallback for runs logged before rates were stored)
import report_model_catalog_html as catalog  # noqa: E402
import report_daily_chart_html as daily_chart  # noqa: E402
from report_styles import CSS  # noqa: E402

TOKEN_COLUMNS = [("input_text", "Text in"), ("input_image", "Image in"), ("output_image", "Image out"),
                 ("output_text", "Other out"), ("thinking", "Thinking")]
TAG_ICON = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true"><path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 '
            '8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/></svg>')


def load_ledger(store):
    ledger = store / "ledger.jsonl"
    if not ledger.exists():
        raise SystemExit(f"No ledger at {ledger}. Generate an image first.")
    return [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]


def fmt_usd(value):
    return "—" if value is None else f"${value:,.4f}"


def fmt_usd_fine(value):
    """Per-token-type cost: enough decimals that sub-cent amounts don't round to $0.0000."""
    if value is None:
        return "—"
    if value == 0:
        return "$0"
    return f"${value:.4f}" if value >= 0.001 else f"${value:.6f}"


def fmt_vnd(value):
    return "—" if value is None else f"{value:,.0f} ₫"


def fmt_tokens(value):
    return "n/r" if value is None else f"{value:,}"


def settings_label(st):
    if st.get("provider") == "gemini":
        return f"{st.get('aspect')} · {st.get('resolution')} · thinking {st.get('thinking')}"
    return f"{st.get('size', '').replace('x', '×')} · {st.get('quality')}"


def rel(store, path):
    try:
        return escape(str(Path(path).relative_to(store)))
    except ValueError:
        return escape(Path(path).as_uri())


def pricing_template(r):
    """Hidden per-run pricing breakdown, shown by the Pricing button: tokens × rate = cost."""
    st = r.get("settings", {})
    model = st.get("model", "")
    rates = r.get("rates_usd_per_1m")
    rates_note = f"Rates stored with this run · prices checked {r.get('prices_checked_on', '?')}"
    if not rates:
        rates = PRICES.get(model, {})
        rates_note = f"Current rates (checked {PRICES_CHECKED_ON}); this run predates stored rates"
    tokens = r.get("tokens") or {}
    breakdown = r.get("cost_breakdown_usd") or {}
    rows = "".join(
        f"<tr><td>{label}</td><td class=num>{fmt_tokens(tokens.get(k))}</td>"
        f"<td class=num>${rates.get(k, 0):,.2f}</td><td class=num>{fmt_usd_fine(breakdown.get(k))}</td></tr>"
        for k, label in TOKEN_COLUMNS)
    fx = r.get("fx") or {}
    fx_line = f"× {fx['rate']:,.0f} ₫ per USD ({escape(fx.get('source', ''))})" if fx.get("rate") else "No exchange rate recorded"
    return f"""<template><h3>{catalog.model_name_html(model, st.get("provider"))}</h3><div class="pnote">{escape(r['id'])}</div>
<table class="ptable"><thead><tr><th>Token type</th><th class=num>Tokens</th><th class=num>USD / 1M</th><th class=num>Cost</th></tr></thead>
<tbody>{rows}</tbody><tfoot><tr><td colspan=3>Total</td><td class=num>{fmt_usd_fine(r.get('cost_usd'))}</td></tr>
<tr><td colspan=3>{fx_line}</td><td class=num>{fmt_vnd(r.get('cost_vnd'))}</td></tr></tfoot></table>
<div class="pnote">Standard tier · {escape(rates_note)}</div></template>"""


def stat_tiles(records):
    ok = [r for r in records if r.get("status") == "ok"]
    usd = sum(r.get("cost_usd") or 0 for r in ok)
    vnd = sum(r.get("cost_vnd") or 0 for r in ok)
    failed = len(records) - len(ok)
    by_model = defaultdict(lambda: [0, 0.0])
    for r in ok:
        by_model[r["settings"]["model"]][0] += 1
        by_model[r["settings"]["model"]][1] += r.get("cost_usd") or 0
    tiles = [("Total spend", fmt_usd(usd), fmt_vnd(vnd)),
             ("Images", f"{len(ok)}", f"{failed} failed" if failed else "all succeeded"),
             ("Average per image", fmt_usd(usd / len(ok)) if ok else "—", fmt_vnd(vnd / len(ok)) if ok else "")]
    tiles = [(escape(a), b, c) for a, b, c in tiles]
    for model, (n, m_usd) in sorted(by_model.items()):
        tiles.append((catalog.model_name_html(model, use_label=True), fmt_usd(m_usd), f"{n} image{'s' * (n != 1)} · avg {fmt_usd(m_usd / n)}"))
    return "".join(f'<div class="stat"><div class="label">{a}</div><div class="value">{escape(b)}</div><div class="sub">{escape(c)}</div></div>'
                   for a, b, c in tiles)


def token_cell(count, usd):
    """Token count with its USD cost below; zeros fade to a dash so real costs stand out."""
    if count == 0:
        return '<td class="num tok"><span class="zero">—</span></td>'
    return f'<td class="num tok">{fmt_tokens(count)}<div class="usd">{fmt_usd_fine(usd)}</div></td>'


def row_html(store, r):
    st = r.get("settings", {})
    tokens = r.get("tokens") or {}
    breakdown = r.get("cost_breakdown_usd") or {}
    outputs = r.get("outputs") or []
    prompt = r.get("prompt") or ""
    # Images carry data-zoom so the page script opens them in the in-page viewer.
    caption = escape(r["id"])
    thumb = (f'<img data-zoom data-caption="{caption} · output" src="{rel(store, outputs[0])}" loading="lazy" alt="Generated image">'
             if outputs else '<div class="noimg">no image</div>')
    inputs = "".join(f'<img data-zoom data-caption="{caption} · input {n}" src="{rel(store, i["saved"])}" alt="Input image {n}">'
                     for n, i in enumerate(r.get("inputs") or [], 1))
    created = datetime.fromisoformat(r["created_at"]).strftime("%b %-d · %H:%M")
    reason = (f'<div class="reason">Above standard ({escape(", ".join(st["overridden"]))}): {escape(st.get("reason") or "")}</div>'
              if st.get("overridden") else "")
    error = f'<div class="error">{escape(r.get("error", ""))}</div>' if r.get("status") != "ok" else ""
    tokens_html = "".join(token_cell(tokens.get(k), breakdown.get(k)) for k, _ in TOKEN_COLUMNS)
    return f"""<tr data-provider="{escape(st.get('provider', ''))}" data-search="{escape(prompt.lower())}">
  <td class="c-img">{thumb}</td>
  <td class="c-run"><div class="when">{created}</div>
    <div class="chips"><span class="chip">{catalog.model_name_html(st.get('model', ''), st.get('provider'))}</span><button type="button" class="ghost price-btn">Pricing</button>{pricing_template(r)}</div>
    <div class="meta-line">{escape(settings_label(st))}</div>
    <div class="meta-line">{escape(Path(r.get('project') or '').name)} · {r.get('duration_s', '—')}s</div></td>
  <td class="c-prompt"><details class="prompt"><summary><span class="clamp">{escape(prompt)}</span><span class="less">Show less</span></summary>
    <div class="codeblock"><div class="cb-bar"><span>Prompt · {len(prompt):,} chars</span><button type="button" class="ghost" data-copy>Copy</button></div>
      <pre><code>{escape(prompt)}</code></pre></div><div class="runid">{escape(r['id'])}</div></details>{reason}{error}
    {f'<div class="inputs">Inputs {inputs}</div>' if inputs else ''}</td>
  {tokens_html}
  <td class="num cost">{fmt_usd(r.get('cost_usd'))}<div class="vnd">{fmt_vnd(r.get('cost_vnd'))}</div></td>
</tr>"""


INFO_ICON = ('<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>')


def howto_dialog_html(store):
    """Note on how this page is made and refreshed; the command path is the script's real location."""
    command = f"python3 {Path(__file__).resolve()} --open"
    return f"""<dialog id="howto" class="sheet howto-box"><button type="button" class="ghost close" data-close>Close</button>
<h2>How to update this page</h2>
<p>This page is a snapshot. It doesn't refresh itself, so run the export again after new generations.</p>
<p class="step">Run this in a terminal:</p>
<div class="cmd"><code>{escape(command)}</code><button type="button" class="ghost" data-copy>Copy</button></div>
<p class="step">Or ask your agent: <em>“Refresh my image generation usage report.”</em></p>
<dl class="props howto-props">
  <dt>Data</dt><dd><code>{escape(str(store / 'ledger.jsonl'))}</code> · one line per generation</dd>
  <dt>Images</dt><dd><code>{escape(str(store / 'runs'))}/</code></dd>
  <dt>This page</dt><dd><code>{escape(str(store / 'usage-report.html'))}</code> · keep it in this folder so images load</dd>
</dl></dialog>"""


SCRIPT = """
  const q = document.getElementById('q'), p = document.getElementById('p');
  function filter() {
    const term = q.value.toLowerCase(), prov = p.value;
    document.querySelectorAll('table.runs tbody tr').forEach(tr => {
      tr.hidden = (prov && tr.dataset.provider !== prov) || (term && !tr.dataset.search.includes(term));
    });
  }
  q.addEventListener('input', filter); p.addEventListener('change', filter);

  // Every dialog closes with Esc, its Close button, or a click on the backdrop.
  document.querySelectorAll('dialog').forEach(d => {
    d.addEventListener('click', e => { if (e.target === d) d.close(); });
    d.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => d.close()));
  });

  // Clicking anywhere in a prompt cell expands/collapses it, except on images, buttons, or while selecting text.
  document.addEventListener('click', e => {
    const cell = e.target.closest('td.c-prompt');
    if (!cell || e.target.closest('img, button, a') || getSelection().toString()) return;
    e.preventDefault();  // stop the <summary> default toggle so this is the only one
    const details = cell.querySelector('details.prompt');
    details.open = !details.open;
  });

  // Image viewer: click any image to open; toggle fit / 100%.
  const viewer = document.getElementById('viewer'), big = viewer.querySelector('.stage img');
  const zoomBtn = viewer.querySelector('[data-act=zoom]'), cap = viewer.querySelector('.cap');
  function setFit(fit) { viewer.classList.toggle('fit', fit); zoomBtn.textContent = fit ? 'Zoom to 100%' : 'Fit to window'; }
  document.addEventListener('click', e => {
    const t = e.target.closest('img[data-zoom]');
    if (!t) return;
    big.src = t.getAttribute('src'); cap.textContent = t.dataset.caption || ''; setFit(true); viewer.showModal();
  });
  big.addEventListener('load', () => { cap.textContent = cap.textContent.split(' · ').slice(0, 2).join(' · ') + ` · ${big.naturalWidth}×${big.naturalHeight}`; });
  zoomBtn.addEventListener('click', () => setFit(!viewer.classList.contains('fit')));
  big.addEventListener('click', () => setFit(!viewer.classList.contains('fit')));
  viewer.querySelector('.stage').addEventListener('click', e => { if (e.target === e.currentTarget) viewer.close(); });

  // Per-run pricing: copy the row's hidden <template> into the shared dialog.
  const pricing = document.getElementById('pricing'), pricingBody = pricing.querySelector('.body');
  document.addEventListener('click', e => {
    const btn = e.target.closest('.price-btn');
    if (!btn) return;
    pricingBody.replaceChildren(btn.nextElementSibling.content.cloneNode(true));
    pricing.showModal();
  });

  // Models & pricing table.
  const models = document.getElementById('models');
  document.getElementById('models-open').addEventListener('click', () => models.showModal());

  // How to update note. Copy buttons put text on the clipboard (or select it if that's blocked).
  const howto = document.getElementById('howto');
  document.getElementById('howto-open').addEventListener('click', () => howto.showModal());
  document.addEventListener('click', async e => {
    const btn = e.target.closest('[data-copy]');
    if (!btn) return;
    const code = btn.closest('.codeblock, .cmd').querySelector('code');
    try { await navigator.clipboard.writeText(code.textContent); btn.textContent = 'Copied'; }
    catch { getSelection().selectAllChildren(code); btn.textContent = 'Press ⌘C'; }
    setTimeout(() => { btn.textContent = 'Copy'; }, 1600);
  });
"""


def build_html(store, records):
    records = sorted(records, key=lambda r: r["created_at"], reverse=True)
    token_heads = "".join(f"<th class=num>{label}</th>" for _, label in TOKEN_COLUMNS)
    rows = "\n".join(row_html(store, r) for r in records)
    generated = datetime.now().strftime("%b %-d, %Y · %H:%M")
    fx_cache = store / "fx-cache.json"
    fx = json.loads(fx_cache.read_text()) if fx_cache.exists() else next((r["fx"] for r in records if r.get("fx")), {})
    fx_text = f"1 USD = {fx['rate']:,.0f} ₫ · {escape(fx.get('source', ''))}" if fx.get("rate") else "—"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Image generation usage</title>
<style>{CSS}{catalog.CSS}{daily_chart.CSS}</style></head><body>
<main class="page">
  <div class="title-row"><h1>Image generation usage</h1>
    <div class="title-actions"><button type="button" class="ghost" id="howto-open">{INFO_ICON}How to update</button>
      <button type="button" class="ghost" id="models-open">{TAG_ICON}Models &amp; pricing</button></div></div>
  <dl class="props">
    <dt>Updated</dt><dd>{generated}</dd>
    <dt>Exchange rate</dt><dd>{fx_text}</dd>
  </dl>
  <div class="stats">{stat_tiles(records)}</div>
  {daily_chart.daily_charts_html(records)}
  <div class="section"><h2>Generations</h2>
    <div class="toolbar"><input id="q" placeholder="Search prompts…" aria-label="Search prompts">
      <select id="p" aria-label="Provider"><option value="">All providers</option><option value="gemini">Gemini</option><option value="openai">OpenAI</option></select></div></div>
  <div class="wrap"><table class="runs"><thead><tr><th></th><th>Run</th><th>Prompt</th>{token_heads}<th class=num>Cost</th></tr></thead>
  <tbody>
{rows}
  </tbody></table></div>
</main>
<dialog id="viewer" class="viewer fit"><div class="bar"><div class="cap"></div>
  <button type="button" data-act="zoom">Zoom to 100%</button><button type="button" data-close aria-label="Close">✕</button></div>
  <div class="stage"><img alt="Full-size image"></div></dialog>
{howto_dialog_html(store)}
<dialog id="pricing" class="sheet pricing-box"><button type="button" class="ghost close" data-close>Close</button><div class="body"></div></dialog>
{catalog.models_dialog_html(records, fx)}
<script>{SCRIPT}{daily_chart.JS}</script>
</body></html>"""


def write_report(store):
    """Rebuild <store>/usage-report.html from the ledger and return its path."""
    out = store / "usage-report.html"
    out.write_text(build_html(store, load_ledger(store)))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--open", action="store_true", help="open the report in the default browser")
    args = parser.parse_args()
    store = Path(os.environ.get("IMAGE_GEN_HOME", Path.home() / ".image-gen")).expanduser()
    out = write_report(store)
    print(out)
    if args.open:
        subprocess.run(["open", str(out)], check=False)


if __name__ == "__main__":
    main()
