"""Daily usage chart for the report: cost per day as bars, images per day as a line (last 30 days).

The user asked for one combined chart, so it has two y-scales: cost on the left,
image count on the right. To keep it readable, both scales share the same four
gridlines, a legend names each series and its axis, and the tooltip lists both
values for the hovered day. Colors: blue bars + orange line, validated with the
dataviz palette checks (CVD ΔE 24.7, all pass on a light surface). Every value
is also in the "View as table" list.
"""

import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from html import escape

DAYS = 30
BAR, LINE = "#2a78d6", "#eb6834"
W, H = 1000, 240                      # SVG viewBox; scales to the container width
LEFT, RIGHT, TOP, BOTTOM = 56, 40, 16, 28

CSS = """
  .chart { margin:0 0 12px; }
  .chart-head { display:flex; align-items:baseline; justify-content:space-between; gap:16px; margin-bottom:10px; }
  .chart h3 { margin:0; font-size:14px; font-weight:600; }
  .chart .csub { color:var(--muted); font-size:12.5px; margin-top:2px; }
  .legend { display:flex; gap:16px; color:var(--muted); font-size:12.5px; }
  .legend span { display:inline-flex; align-items:center; gap:6px; }
  .legend .k-bar { width:10px; height:10px; border-radius:2px; background:""" + BAR + """; }
  .legend .k-line { width:14px; height:2px; border-radius:1px; background:""" + LINE + """; }
  .chart svg { width:100%; height:auto; display:block; overflow:visible; }
  .chart .grid { stroke:#ebebea; stroke-width:1; }
  .chart .axis { fill:var(--muted); font-size:11px; font-variant-numeric:tabular-nums; }
  .chart .bar { fill:""" + BAR + """; pointer-events:none; }
  .chart .line { fill:none; stroke:""" + LINE + """; stroke-width:2; stroke-linejoin:round; stroke-linecap:round; pointer-events:none; }
  .chart .dot { fill:""" + LINE + """; stroke:#fff; stroke-width:2; pointer-events:none; }
  .chart .hit { fill:transparent; outline:none; }
  .chart .hit:hover, .chart .hit:focus { fill:rgba(55,53,47,.05); }
  .chart-tip { position:fixed; pointer-events:none; z-index:20; background:#fff; color:var(--ink); border-radius:6px; padding:7px 10px;
    box-shadow:var(--shadow); font-size:12.5px; line-height:1.5; display:none; white-space:nowrap; }
  .chart-tip .tday { color:var(--muted); margin-bottom:2px; }
  .chart-tip .trow { display:flex; align-items:center; gap:8px; }
  .chart-tip .trow b { font-variant-numeric:tabular-nums; }
  .chart-tip .trow i { width:12px; height:2px; border-radius:1px; display:inline-block; }
  details.chart-table { margin:0 0 40px; font-size:13px; color:var(--muted); }
  details.chart-table summary { cursor:pointer; width:max-content; }
  details.chart-table table { border-collapse:collapse; margin-top:8px; color:var(--ink); }
  details.chart-table th, details.chart-table td { padding:4px 14px 4px 0; border-bottom:1px solid var(--line); text-align:right; font-variant-numeric:tabular-nums; }
  details.chart-table th:first-child, details.chart-table td:first-child { text-align:left; }
  details.chart-table th { font-weight:500; color:var(--muted); }
"""

# One tooltip lists both series for the hovered day; text is set with textContent.
JS = """
  const tip = document.createElement('div'); tip.className = 'chart-tip'; document.body.append(tip);
  function tipRow(color, value, label) {
    const row = document.createElement('div'); row.className = 'trow';
    const key = document.createElement('i'); key.style.background = color;
    const b = document.createElement('b'); b.textContent = value;
    const s = document.createElement('span'); s.textContent = label;
    row.append(key, b, s); return row;
  }
  function showTip(el, x, y) {
    const day = document.createElement('div'); day.className = 'tday'; day.textContent = el.dataset.day;
    tip.replaceChildren(day, tipRow('""" + BAR + """', el.dataset.cost, 'cost'), tipRow('""" + LINE + """', el.dataset.images, 'images'));
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    tip.style.left = Math.min(x + 14, innerWidth - r.width - 8) + 'px'; tip.style.top = Math.max(8, y - r.height - 12) + 'px';
  }
  document.querySelectorAll('.chart .hit').forEach(el => {
    el.addEventListener('pointermove', e => showTip(el, e.clientX, e.clientY));
    el.addEventListener('pointerleave', () => { tip.style.display = 'none'; });
    el.addEventListener('focus', () => { const b = el.getBoundingClientRect(); showTip(el, b.left + b.width / 2, b.top + 40); });
    el.addEventListener('blur', () => { tip.style.display = 'none'; });
  });
"""


def _daily(records):
    """[(date, images, usd)] for successful runs in the last DAYS days, empty days included."""
    today = date.today()
    days = [today - timedelta(days=i) for i in range(DAYS - 1, -1, -1)]
    totals = defaultdict(lambda: [0, 0.0])
    for r in records:
        if r.get("status") != "ok":
            continue
        d = datetime.fromisoformat(r["created_at"]).date()
        totals[d][0] += len(r.get("outputs") or []) or 1
        totals[d][1] += r.get("cost_usd") or 0
    return [(d, totals[d][0], totals[d][1]) for d in days]


def _nice_step(peak, integer):
    """Clean tick step (1/2/2.5/5 × 10^n, whole numbers for counts) so 4 steps cover the peak."""
    raw = peak / 4 if peak > 0 else (0.25 if integer else 0.0025)
    exp = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * exp
        if step >= raw and (not integer or step >= 1 and step == int(step)):
            return step
    return 10 * exp


def _decimals(step):
    """Fewest decimals that show every tick of this step exactly (at least 2 for money)."""
    for d in range(2, 6):
        if abs(round(step, d) - step) < 1e-12:
            return d
    return 6


def _fmt_usd(v):
    return f"${v:,.4f}" if v else "$0"


def daily_charts_html(records):
    daily = _daily(records)
    cost_step = _nice_step(max(c for _, _, c in daily), integer=False)
    img_step = _nice_step(max(n for _, n, _ in daily), integer=True)
    cost_top, img_top = cost_step * 4, img_step * 4
    dec = _decimals(cost_step)
    plot_w, plot_h = W - LEFT - RIGHT, H - TOP - BOTTOM
    base = TOP + plot_h
    band = plot_w / len(daily)
    bar_w = min(24, band * 0.6)
    y_cost = lambda v: base - v / cost_top * plot_h  # noqa: E731
    y_img = lambda v: base - v / img_top * plot_h  # noqa: E731

    parts = []
    for i in range(5):  # shared gridlines: left = cost, right = images
        gy = base - plot_h * i / 4
        parts.append(f'<line class="grid" x1="{LEFT}" x2="{W - RIGHT}" y1="{gy:.1f}" y2="{gy:.1f}"/>')
        parts.append(f'<text class="axis" x="{LEFT - 8}" y="{gy + 3.5:.1f}" text-anchor="end">${cost_step * i:,.{dec}f}</text>')
        parts.append(f'<text class="axis" x="{W - RIGHT + 8}" y="{gy + 3.5:.1f}">{int(img_step * i):,}</text>')

    points = []
    for i, (d, n, c) in enumerate(daily):
        cx = LEFT + band * (i + 0.5)
        day = d.strftime("%a, %b %-d")
        images = f"{n:,} image{'s' * (n != 1)}"
        parts.append(f'<rect class="hit" x="{LEFT + band * i:.1f}" y="{TOP}" width="{band:.1f}" height="{plot_h}" tabindex="0" '
                     f'data-day="{escape(day)}" data-cost="{escape(_fmt_usd(c))}" data-images="{escape(images)}" '
                     f'aria-label="{escape(day)}: {escape(_fmt_usd(c))}, {escape(images)}"/>')
        h = c / cost_top * plot_h
        if h > 0:  # 4px rounded top, square at the baseline
            x0, y0, r = cx - bar_w / 2, y_cost(c), min(4, h, bar_w / 2)
            parts.append(f'<path class="bar" d="M{x0:.1f},{base:.1f} V{y0 + r:.1f} Q{x0:.1f},{y0:.1f} {x0 + r:.1f},{y0:.1f} '
                         f'H{x0 + bar_w - r:.1f} Q{x0 + bar_w:.1f},{y0:.1f} {x0 + bar_w:.1f},{y0 + r:.1f} V{base:.1f} Z"/>')
        points.append((cx, y_img(n), n))
        last = len(daily) - 1
        # Weekly date labels plus today; skip a weekly label that would crowd today's.
        if i == last or (i % 7 == 0 and last - i >= 4):
            parts.append(f'<text class="axis" x="{cx:.1f}" y="{H - 8}" text-anchor="middle">{escape(d.strftime("%b %-d"))}</text>')

    parts.append('<polyline class="line" points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points) + '"/>')
    parts.extend(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="4"/>' for x, y, n in points if n)  # markers only on active days

    total_images = sum(n for _, n, _ in daily)
    total_usd = sum(c for _, _, c in daily)
    chart = (f'<figure class="chart" style="margin:0 0 12px"><div class="chart-head"><div><h3>Daily usage</h3>'
             f'<div class="csub">Last {DAYS} days · {total_images:,} images · ${total_usd:,.4f}</div></div>'
             f'<div class="legend"><span><i class="k-bar"></i>Cost (USD, left axis)</span><span><i class="k-line"></i>Images (right axis)</span></div></div>'
             f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Daily cost and images, last {DAYS} days">{"".join(parts)}</svg></figure>')
    rows = "".join(f"<tr><td>{d.strftime('%a, %b %-d')}</td><td>{n:,}</td><td>${c:,.4f}</td></tr>" for d, n, c in reversed(daily) if n)
    table = (f'<details class="chart-table"><summary>View as table</summary><table><thead><tr><th>Day</th><th>Images</th><th>Cost (USD)</th></tr></thead>'
             f'<tbody>{rows or "<tr><td colspan=3>No generations in this period</td></tr>"}</tbody></table></details>')
    return chart + table
