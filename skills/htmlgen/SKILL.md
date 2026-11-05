---
name: htmlgen
description: "Build one standalone, Notion-like HTML page that captures the topic being discussed (explainer, comparison/decision, investigation, design proposal, plan, review, status, results readout or cheat sheet), structured summary-first with inline SVG diagrams, and open it. Use when the user asks to put something in an HTML page, write it up as a page, make a one-pager, visualize or summarize a discussion as HTML, or invokes /htmlgen. No server, no upload, no external resources."
user-invocable: true
argument-hint: "[topic or question the page should answer]"
---

# /htmlgen

Build **one standalone HTML file** that captures the topic we are discussing, written and structured the way the user likes, and open it. No server, no upload, no external resources.

## 1. Decide what the page is for

Before writing, answer in one line each (don't show this to the user):

- **Question:** what question does this page answer for the user?
- **Type:** pick the closest shape — it drives the structure (section 3): `explainer` · `comparison / decision` · `investigation / root cause` · `design / proposal` · `plan` · `review / audit` · `status / summary` · `results / benchmark readout` · `cheat sheet / reference`.
- **Takeaway:** the one thing the user should remember after 30 seconds.

If the topic is ambiguous or too broad for one page, ask at most 3 short questions (who it's for, the one takeaway, what decision it should drive) instead of guessing.

## 2. Style rules (the user's preferences — these win)

### Writing

- Plain, easy-to-read language and short sentences. The reader is a senior engineer: technical terms are fine **only when they carry meaning** — don't stack jargon; it's cognitive load.
- **Focused and critical.** Every block must serve the question in section 1. Cut relevant-but-not-insightful content: generic background, restating the obvious, boilerplate caveats, exhaustive lists. If a section would be filler, drop it — sections are optional, insight is not.
- Have a point of view: say what you think, why, and what would change your mind. Flag weak spots — in the user's idea and in your own reasoning. Mark uncertainty honestly ("not verified", "assumption").
- Ground claims in evidence from the conversation (real names and numbers). **Never invent facts** — no made-up owners, dates or numbers; write `TBD` and tell the user. If sources disagree, use the primary one and flag the conflict on the page.
- **Outcomes, not the conversation.** The page shows where things landed, as if written fresh by someone who knows the final answer. Leave out the back-and-forth that got there: options tried and dropped, corrections, "we first thought…", and small tweaks along the way. Include a decision only if it changes what the reader does or believes; one big decision with its main reason beats ten small ones with theirs. A rejected option earns at most one line in a toggle, and only if someone is likely to propose it again.
- Lists and short paragraphs over walls of text.
- **Visual rhythm:** never more than 3 paragraphs in a row without an anchor (table, diagram, callout, short snippet).
- **Tables over prose** for anything compared across 2+ options or metrics: bold row leads, ✅ ⚠️ ❌ for status.
- **Headings say something.** Prefer short "action" headings (≤ 12 words, stating what the section shows: "Retries cause the 2 s stall") over vague topic labels; use topic labels only for reference pages. Avoid AI-sounding headings: fake tension ("It's not X. It's Y."), drama ("A game changer"), faux insight ("The hidden cost"), questions, colon punchlines, exclamation marks, emoji.
- Show links as short labels (`PR #123`, `ISSUE-456`, a doc title), never raw `https://…` text.

### Structure

- **Summary first.** The first screen must stand alone: title, a one-line "question / context", and a **TL;DR callout** with 2–4 bold-labeled bullets (e.g. **Problem / Approach / Impact**, or **What / Why / Trade-off / Ask**): one idea per bullet, one sentence (~25 words), plain language — no file paths, links or flag names in the TL;DR. If the user needs to decide or answer something, a **"Decisions needed"** callout comes right after it.
- Metadata (question, date, status, related issues/docs) lives in the properties block under the title — don't repeat it in prose.
- Pages with 4+ `h2` sections get a one-line contents row under the TL;DR.
- Code snippets ≤ 25 lines and only the lines that matter; longer code, logs, raw data and stack traces go into toggles.
- Secondary detail (long code, raw data, full lists, alternatives) goes into collapsible toggles at the end, not the main flow.

### Illustrations

- Use one when it explains faster than text: block diagram (components/flow), sequence diagram (who talks to whom, in order), mind map (options/factors), bar chart (a few numbers), before/after, timeline. Typically 1–2 per page, never decorative; a list beats a diagram that says the same thing.
- **Pick the visual by the question the section answers** (section 5 has the patterns):

  | Question | Visual |
  |---|---|
  | How is it built / what talks to what? | block diagram, layered stack |
  | What happens, in what order? | sequence diagram, timeline |
  | What are the options / factors? | mind map, comparison table |
  | How do a few numbers compare? | bar chart (paired bars for before/after) |
  | What share / how far along? | donut / progress ring, waffle ("7 in 100") |
  | Is it good or bad (one value vs a threshold)? | gauge, big number + status color |
  | Which way is it trending? | sparkline next to the number |
  | Where do things get filtered or diverted? | funnel, fork / router |
  | What changed? | before / after |

- One focal element per visual; the highlight color marks the single thing to look at. Color carries meaning only: green good, red bad, yellow caution, blue = look here.
- No "data slop": no decorative stats, icons that carry no information, or filler cards. If something feels empty, fix the layout — don't invent content.
- Draw them as **inline SVG / HTML+CSS** (patterns in section 5). No Mermaid, no CDNs, no chart libraries.

### Look

- Clean, light, Notion-like page — use the CSS in section 4 as is: no dark mode, no new colors, no heavy borders. No generic AI decoration: gradients, glassmorphism / blur, glows, thick colored side-stripes, pills used as decoration, a page icon or emoji above the title, emoji in headings (callout icons are fine).

### Links

- All links open in a new tab: `target="_blank" rel="noopener noreferrer"` (not for in-page `#anchors`).

### Self-contained

- All CSS/JS inline; images as inline SVG or `data:` URIs. No external scripts, stylesheets, fonts or `fetch()` — it must work offline from disk.
- No secrets, tokens or credentials.

## 3. Structure by type

Always: **title → properties (question/context, date) → TL;DR → Decisions needed (if any) → body → toggles**. Body by type:

| Type | Body (keep only what adds insight) |
|---|---|
| explainer | The idea in plain words → how it works (diagram) → what matters / gotchas |
| comparison / decision | Recommendation + why → comparison table (✅ ⚠️ ❌) → what would flip the decision |
| investigation / root cause | What happened → evidence (timeline or sequence) → root cause → fix / next steps → open questions |
| design / proposal | Problem → proposed design (block diagram) → key trade-offs → alternatives (toggle) |
| plan | Approach → numbered steps, each with "done when" → risks that matter |
| review / audit | Verdict → findings by severity (table) → suggested changes |
| status / summary | Where we are → what changed → blockers → next |
| results / benchmark readout | Headline numbers (table or big number) → why it matters → distribution / trend chart → caveats → next |
| cheat sheet / reference | Compact tables/snippets grouped by task; minimal prose |

## 4. Page template (copy, then fill)

```html
<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TITLE</title>
<style>
:root{--text:#37352f;--muted:#787774;--faint:#9b9a97;--line:#e9e9e7;--soft:#f7f6f3;--hover:#f1f1ef;
--blue-bg:#e7f3f8;--yellow-bg:#fbf3db;--green-bg:#edf3ec;--red:#d44c47;--red-bg:#fdebec;--purple-bg:#f6f3f9;--code:#eb5757}
*{box-sizing:border-box}body{margin:0;color:var(--text);background:#fff;font:16px/1.65 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
main{max-width:820px;margin:0 auto;padding:56px 32px 120px}
h1{font-size:38px;line-height:1.2;margin:0 0 12px;letter-spacing:-.01em}h2{font-size:23px;font-weight:650;margin:40px 0 8px}h3{font-size:18px;margin:24px 0 4px}
p{margin:6px 0}ul,ol{margin:4px 0;padding-left:24px}li{margin:3px 0}
a{color:inherit;text-decoration:underline;text-decoration-color:rgba(55,53,47,.4);text-underline-offset:2px}
.props{display:grid;grid-template-columns:130px 1fr;gap:4px 12px;font-size:14px;margin:4px 0 20px}.props .k{color:var(--muted)}
.callout{display:flex;gap:12px;padding:14px 16px;border-radius:6px;margin:12px 0;background:var(--soft)}.callout .ci{font-size:20px;line-height:1.5}.callout .cb{flex:1;min-width:0}
.callout b.t{display:block;margin-bottom:2px}.tldr{background:var(--blue-bg)}.decide{background:var(--yellow-bg)}.good{background:var(--green-bg)}.warn{background:var(--red-bg)}
code{font:85%/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--code);background:rgba(135,131,120,.15);padding:2px 5px;border-radius:4px}
pre{background:var(--soft);border-radius:6px;padding:16px 18px;overflow:auto}pre code{color:var(--text);background:none;padding:0;font-size:13.5px}
table{border-collapse:collapse;width:100%;font-size:15px;margin:10px 0}th,td{border:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}th{color:var(--muted);font-weight:500;background:var(--soft)}
details{margin:6px 0}summary{cursor:pointer;padding:3px 4px;border-radius:4px;font-weight:500}summary:hover{background:var(--hover)}details>div{padding:2px 0 6px 22px}
.steps{list-style:none;padding:0;counter-reset:s}.steps>li{counter-increment:s;position:relative;padding:2px 0 10px 36px}
.steps>li::before{content:counter(s);position:absolute;left:0;top:3px;width:24px;height:24px;border-radius:50%;background:var(--soft);color:var(--muted);font-size:13px;font-weight:600;display:flex;align-items:center;justify-content:center}
.done{color:var(--muted);font-size:14px}.tag{display:inline-block;font-size:12.5px;padding:0 7px;border-radius:4px;background:var(--hover);color:var(--muted)}
.tag.new{background:var(--green-bg);color:#448361}.tag.risk{background:var(--red-bg);color:var(--red)}
figure{margin:18px 0}figure svg{display:block;max-width:100%;height:auto;margin:0 auto}figcaption{text-align:center;color:var(--faint);font-size:13.5px;margin-top:6px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.cols{grid-template-columns:1fr}main{padding:32px 18px 80px}}
</style></head>
<body><main>
  <h1>TITLE</h1>
  <div class="props">
    <div class="k">Question</div><div>WHAT THIS PAGE ANSWERS</div>
    <div class="k">Updated</div><div>DATE</div>
  </div>
  <div class="callout tldr"><div class="ci">💡</div><div class="cb"><b class="t">TL;DR</b>
    <ul><li><b>Label:</b> …</li></ul></div></div>
  <!-- only if needed -->
  <div class="callout decide"><div class="ci">🤔</div><div class="cb"><b class="t">Decisions needed</b>
    <ol><li><b>…?</b> My recommendation: … because …</li></ol></div></div>

  <h2>…</h2>
  <p>…</p>
  <figure><!-- inline SVG --><figcaption>…</figcaption></figure>

  <h2>Details</h2>
  <details><summary>…</summary><div>…</div></details>
</main></body></html>
```

Components available: `.callout` (+ `tldr` / `decide` / `good` / `warn`), `.steps` with `.done`, `table`, `details`, `.tag` (`new` / `risk`), `.cols` (two columns, e.g. before/after), `figure`.

## 5. Inline-SVG diagram patterns

Palette only: text `#37352f`, muted `#787774`, lines `#d3d1cb`, box fill `#f7f6f3`, highlight fill `#e7f3f8` + stroke `#2383e2` (only for the part that matters/changes), warning fill `#fdebec`. System font, 13–14px. Always a `viewBox`, no fixed width, ≤ 760 units wide. Labels 1–3 words; widen boxes rather than shrink text.

Arrow marker (inside each `<svg>`):

```html
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#787774"/></marker></defs>
```

- **Block diagram:** `<rect rx="8">` boxes + `<line marker-end="url(#arr)">` arrows with small muted labels above them.
- **Sequence diagram:** participant boxes on top, dashed lifelines (`stroke-dasharray="4 4"`), solid arrows for calls, dashed for replies, labels above arrows, optional yellow note box.
- **Mind map:** pill in the center (highlight colors), curved `<path d="M… C…">` branches to boxes around it.
- **Bar chart:** horizontal bars, max value = 460 units, labels left, values right of each bar; highlight the bar that matters.
- **Before / after:** two small block diagrams in `.cols`.
- **Layered stack / funnel / fork:** 3–6 simple shapes, real text labels (≥ 13px) outside or on the shapes.
- **Donut / progress ring** (one percentage), r=54, circumference 339.3:

  ```html
  <svg viewBox="0 0 120 120" width="140" style="transform:rotate(-90deg)">
    <circle cx="60" cy="60" r="54" fill="none" stroke="#f1f1ef" stroke-width="12"/>
    <circle cx="60" cy="60" r="54" fill="none" stroke="#2383e2" stroke-width="12"
            stroke-linecap="round" stroke-dasharray="{3.393*v} 339.3"/></svg>
  ```

- **Gauge** (value vs threshold): half circle `M10 70 A60 60 0 0 1 130 70`, `stroke-dasharray="{1.885*v} 188.5"`; green / yellow / red by meaning.
- **Waffle:** 10×10 CSS grid of 22px rounded cells, highlighted cells first.
- **Sparkline:** a 120×36 `<path>` polyline with a dot on the last point, placed next to the number it explains.
- **Big number:** one large figure (≈ 56px, 700 weight) with a short label and a status color — for the one number people should remember.

## 6. Write, check, open

1. **Write** to `/tmp/htmlgen/<yyyy-mm-dd>-<slug>.html` (`mkdir -p`). Reusing the same slug in this conversation = an updated version:
   - **Rewrite affected sections in place** so the page reads as one current, final version. Don't append new sections or a running history of the discussion.
   - Add a "What changed" callout under the TL;DR only for **material** changes (a different recommendation, scope, number or risk), at most 3 bullets. Small wording, layout or detail tweaks don't go in it; if nothing material changed, leave the callout out.
   - Before saving, cut anything a reader who missed the conversation wouldn't need.
2. **Check** before opening:
   - no `src=`/`href=` to `http(s)://` except plain `<a>` links; no `fetch(`;
   - every `<a href="http…">` has `target="_blank" rel="noopener noreferrer"`;
   - first screen = title + properties + TL;DR (+ decisions);
   - no run of 4+ paragraphs without a table/diagram/callout; no invented numbers (`TBD` instead); headings aren't AI-sounding;
   - **look at it:** if Chrome is available, take a screenshot and check it (layout, text fitting in diagram boxes, nothing overflowing), e.g. `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --window-size=1100,1800 --screenshot=/tmp/htmlgen/shot.png file:///tmp/htmlgen/<file>.html` (on Linux: `google-chrome --headless=new …`); fix and re-check;
   - reads as the final state: no back-and-forth, dropped options or small decisions with their rationale;
   - re-read once as the user: delete anything that doesn't serve the question.
3. **Open:**
   - Mac (local session): `open /tmp/htmlgen/<file>.html`
   - Linux desktop: `xdg-open /tmp/htmlgen/<file>.html`
   - Remote or headless machine: copy it somewhere the user's computer can open (a synced folder, if they have one), or just give the user the path.
4. **Reply** in 1–3 lines: what the page covers, where it is, and the decisions needed (if any). Don't repeat the page in chat.
