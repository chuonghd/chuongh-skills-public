"""HTML pieces for the usage report: provider logos and the "Models & pricing" table.

Logos are the Google "G" and OpenAI marks used on Belovedfolio's NYX admin.
The table lists every model in pricing.MODELS with list rates per 1M tokens
(USD, VND below), an estimated cost per image at the standard tier, and the
user's own measured average when the ledger has comparable runs.
"""

from html import escape

from pricing import MODELS, PRICE_SOURCES, PRICES_CHECKED_ON, standard_image_estimate

_GOOGLE_G = (
    '<svg viewBox="0 0 24 24" class="logo" role="img" aria-label="Google">'
    '<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>'
    '<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>'
    '<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>'
    '<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>'
)
_OPENAI = (
    '<svg viewBox="0 0 24 24" class="logo" role="img" aria-label="OpenAI"><path fill="currentColor" d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/></svg>'
)

_RATE_COLUMNS = [("input_text", "Text in"), ("input_image", "Image in"),
                 ("output_text", "Text out"), ("output_image", "Image out")]

CSS = """
  .logo { width:14px; height:14px; flex:none; display:inline-block; vertical-align:-2px; margin-right:6px; color:#111; }
  .mname { display:inline-flex; align-items:center; }
  .models-box { width:max-content; max-width:calc(100vw - 32px); padding:28px 30px; }
  .models-box h2 { font-size:22px; }
  .models-box .lede { color:var(--muted); font-size:13.5px; margin:4px 0 18px; }
  .mtable { border-collapse:collapse; font-size:14px; }
  .mtable th { text-align:left; font-size:12.5px; font-weight:500; color:var(--muted); padding:8px 14px; border-bottom:1px solid var(--line); white-space:nowrap; }
  .mtable td { padding:12px 14px; border-bottom:1px solid var(--line); vertical-align:middle; }
  .mtable tbody tr:hover { background:var(--hover); }
  .mtable tbody tr:last-child td { border-bottom:0; }
  .mtable .mcol { white-space:nowrap; }
  .mtable .mid { display:block; font:12px ui-monospace, SFMono-Regular, Menlo, monospace; color:var(--faint); margin-top:2px; }
  .mtable .rate { min-width:76px; }
  .mtable .est { font-weight:600; white-space:nowrap; }
  .mtable .sub { display:block; font-size:12px; color:var(--muted); font-weight:400; white-space:nowrap; }
  .mtable .na { color:var(--faint); font-weight:400; }
  .mtable .note { color:var(--muted); font-size:13px; white-space:nowrap; }
  .badges { display:inline-flex; gap:4px; margin-left:8px; vertical-align:1px; }
  .badge { border-radius:4px; padding:0 6px; font-size:12px; line-height:20px; white-space:nowrap; }
  .b-default { background:#dbeddb; color:#1c3829; }
  .b-latest { background:#d3e5ef; color:#183347; }
  .b-ref { background:rgba(227,226,224,.6); color:#5a5853; }
  .models-box .foot { color:var(--muted); font-size:12.5px; margin-top:14px; }
  .models-box .foot a { color:inherit; }
"""


def logo(provider):
    return _GOOGLE_G if provider == "gemini" else _OPENAI


def model_name_html(model_id, provider=None, use_label=False):
    """Provider logo followed by the model id (or its friendly label)."""
    info = MODELS.get(model_id, {})
    provider = provider or info.get("provider", "openai")
    text = info.get("label", model_id) if use_label else model_id
    return f'<span class="mname">{logo(provider)}{escape(text)}</span>'


def _fmt_usd(value):
    return f"${value:.4f}" if value < 1 else f"${value:,.2f}"


def _fmt_vnd(value):
    return f"{value:,.0f} ₫"


def _measured_average(model_id, records):
    """Average total cost of the user's text-only runs at this model's standard settings."""
    std = MODELS[model_id]["standard"]["settings"]
    costs = [r["cost_usd"] for r in records
             if r.get("status") == "ok" and r.get("cost_usd") is not None and not r.get("inputs")
             and r.get("settings", {}).get("model") == model_id
             and all(r["settings"].get(k) == v for k, v in std.items())]
    return (sum(costs) / len(costs), len(costs)) if costs else (None, 0)


def models_dialog_html(records, fx):
    """The "Models & pricing" dialog: every catalog model, rates, per-image estimate, notes."""
    rate = fx.get("rate") if fx else None
    vnd_note = f"1 USD = {rate:,.0f} ₫." if rate else ""
    rows = []
    for model_id, info in MODELS.items():
        badges = "".join([
            '<span class="badge b-default">Default</span>' if info.get("default") else "",
            '<span class="badge b-latest">Latest</span>' if info.get("latest") else "",
            '<span class="badge b-ref">Pricing only</span>' if not info["generate"] else "",
        ])
        rate_cells = "".join(
            f'<td class="num rate">${info["rates"][k]:g}</td>' if info["rates"][k] else '<td class="num rate"><span class="na">—</span></td>'
            for k, _ in _RATE_COLUMNS)
        usd, _basis, source = standard_image_estimate(model_id)
        measured, n = _measured_average(model_id, records)
        if usd is None:
            est = '<span class="na">not measured</span>'
        else:
            est = f'<span class="est" title="{escape(source)}">~{_fmt_usd(usd)}</span>' + (f'<span class="sub">{_fmt_vnd(usd * rate)}</span>' if rate else "")
        if measured is not None:
            est += f'<span class="sub" title="Average of {n} of your runs, incl. input and thinking">yours {_fmt_usd(measured)}</span>'
        rows.append(
            f'<tr><td class="mcol"><span class="mname" style="font-weight:600">{logo(info["provider"])}{escape(info["label"])}</span>'
            f'<span class="badges">{badges}</span><span class="mid">{escape(model_id)}</span></td>'
            f'{rate_cells}<td class="num">{est}</td>'
            f'<td class="note">{escape(info["sizes"])}</td><td class="note">{escape(info["note"])}</td></tr>')
    heads = "".join(f"<th class=num>{label}</th>" for _, label in _RATE_COLUMNS)
    sources = ", ".join(f'<a href="{escape(url)}" target="_blank" rel="noreferrer">{escape(label)}</a>' for label, url in PRICE_SOURCES)
    return f"""<dialog id="models" class="sheet models-box"><button type="button" class="ghost close" data-close>Close</button>
<h2>Models &amp; pricing</h2>
<div class="lede">USD per 1M tokens, Standard tier, checked {PRICES_CHECKED_ON}. {vnd_note}</div>
<div style="overflow-x:auto"><table class="mtable"><thead><tr><th>Model</th>{heads}<th class=num title="Gemini 1K · OpenAI 1024x1536 medium">Per image</th><th>Sizes</th><th>Notes</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<div class="foot">Per image: Gemini 1K, OpenAI 1024x1536 medium, image output only. Text out includes thinking. Sources: {sources}.</div>
</dialog>"""
