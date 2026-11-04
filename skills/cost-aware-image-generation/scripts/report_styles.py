"""CSS for the usage report: a calm, Notion-like page (centered column, quiet grays, thin dividers)."""

CSS = """
  :root {
    --ink:#37352f; --muted:#787774; --faint:#b4b4b0; --line:#ebebea; --hover:#f7f7f5; --tile:#f7f6f3;
    --accent:#2f6f5e; --shadow:0 0 0 1px rgba(15,15,15,.05), 0 3px 6px rgba(15,15,15,.1), 0 9px 24px rgba(15,15,15,.2);
  }
  * { box-sizing:border-box; }
  body { margin:0; background:#fff; color:var(--ink); -webkit-font-smoothing:antialiased;
    font:14px/1.5 ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
  .page { max-width:1800px; margin:0 auto; padding:72px 56px 96px; }

  /* Page header */
  .title-row { display:flex; align-items:flex-end; justify-content:space-between; gap:16px; }
  h1 { margin:0; font-size:38px; line-height:1.2; font-weight:700; letter-spacing:-.02em; }
  .props { display:grid; grid-template-columns:120px 1fr; gap:6px 12px; margin:18px 0 28px; font-size:14px; }
  .props dt { color:var(--muted); }
  .props dd { margin:0; }
  .props code { font:12.5px ui-monospace, SFMono-Regular, Menlo, monospace; color:#eb5757; background:rgba(135,131,120,.15); padding:1px 5px; border-radius:4px; }

  /* Ghost buttons, like Notion's toolbar */
  .ghost { display:inline-flex; align-items:center; gap:6px; font:inherit; font-size:14px; color:var(--muted); background:none;
    border:0; border-radius:6px; padding:4px 8px; cursor:pointer; }
  .ghost:hover { background:rgba(55,53,47,.08); color:var(--ink); }

  /* Stat tiles */
  .stats { display:grid; grid-template-columns:repeat(auto-fill, minmax(190px, 1fr)); gap:10px; margin-bottom:44px; }
  .stat { background:var(--tile); border-radius:8px; padding:14px 16px; }
  .stat .label { color:var(--muted); font-size:12.5px; display:flex; align-items:center; }
  .stat .value { font-size:24px; font-weight:600; letter-spacing:-.01em; margin-top:4px; font-variant-numeric:tabular-nums; }
  .stat .sub { color:var(--muted); font-size:12.5px; font-variant-numeric:tabular-nums; }

  /* Section title + toolbar */
  .section { display:flex; align-items:center; justify-content:space-between; gap:12px; padding-bottom:8px; border-bottom:1px solid var(--line); }
  h2 { margin:0; font-size:20px; font-weight:600; letter-spacing:-.01em; }
  .toolbar { display:flex; align-items:center; gap:4px; }
  .toolbar input, .toolbar select { font:inherit; font-size:14px; color:var(--ink); border:0; background:none; border-radius:6px; padding:5px 8px; outline:none; }
  .toolbar input { width:220px; }
  .toolbar input:hover, .toolbar select:hover, .toolbar input:focus { background:rgba(55,53,47,.06); }

  /* Runs table */
  .wrap { overflow-x:auto; }
  table.runs { width:100%; border-collapse:collapse; }
  .runs th { text-align:left; font-size:12.5px; font-weight:500; color:var(--muted); padding:8px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }
  .runs td { padding:14px 10px; border-bottom:1px solid var(--line); vertical-align:top; }
  .runs tbody tr:hover { background:var(--hover); }
  .num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
  .c-img { width:84px; }
  .c-img img { width:72px; border-radius:6px; display:block; box-shadow:0 0 0 1px rgba(15,15,15,.06); }
  .noimg { width:72px; height:96px; border-radius:6px; background:var(--tile); color:var(--muted); font-size:12px; display:grid; place-items:center; }
  .c-run { min-width:230px; }
  .when { font-weight:600; }
  .chips { display:flex; align-items:center; gap:4px; margin:6px 0 4px; white-space:nowrap; }
  .chip { display:inline-flex; align-items:center; font-size:12.5px; background:rgba(227,226,224,.6); border-radius:4px; padding:1px 7px; white-space:nowrap; }
  .chip .logo { width:12px; height:12px; margin-right:5px; }
  .price-btn { font-size:12.5px; padding:1px 6px; }
  .meta-line { color:var(--muted); font-size:12.5px; }
  .c-prompt { min-width:420px; width:100%; cursor:pointer; }
  .c-prompt img, .c-prompt button { cursor:auto; }
  .c-prompt img[data-zoom] { cursor:zoom-in; }
  .c-prompt button { cursor:pointer; }
  details.prompt summary { list-style:none; cursor:pointer; }
  details.prompt summary::-webkit-details-marker { display:none; }
  details.prompt .clamp { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  details.prompt .less { display:none; color:var(--muted); font-size:12.5px; }
  details.prompt[open] .clamp { display:none; }
  details.prompt[open] .less { display:inline; }
  /* Prompt as a code block: monospace, kept line breaks, wraps instead of scrolling sideways. */
  .codeblock { background:#efeeeb; box-shadow:inset 0 0 0 1px rgba(55,53,47,.06); border-radius:6px; margin-top:4px; max-width:1200px; }
  .cb-bar { display:flex; align-items:center; justify-content:space-between; padding:6px 8px 0 14px; color:var(--muted); font-size:12px; }
  .cb-bar .ghost { font-size:12px; padding:2px 8px; }
  .codeblock pre { margin:0; padding:8px 14px 14px; white-space:pre-wrap; word-break:break-word; }
  .codeblock code { font:12px/1.6 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; color:var(--ink); }
  .runid { color:var(--faint); font-size:12px; margin-top:6px; font-family:ui-monospace, monospace; }
  .inputs { display:flex; align-items:center; gap:6px; margin-top:10px; color:var(--muted); font-size:12px; }
  .inputs img { width:30px; height:30px; object-fit:cover; border-radius:4px; box-shadow:0 0 0 1px rgba(15,15,15,.06); }
  .reason { margin-top:8px; font-size:12.5px; color:#9f6b00; }
  .error { margin-top:8px; font-size:12.5px; color:#d44c47; }
  .tok .usd { color:var(--muted); font-size:12px; margin-top:2px; }
  .tok .zero { color:var(--faint); }
  .cost { font-weight:600; }
  .cost .vnd { font-weight:400; color:var(--muted); font-size:12px; margin-top:2px; }
  img[data-zoom] { cursor:zoom-in; }

  /* Dialogs share one look */
  dialog.sheet { border:0; border-radius:12px; box-shadow:var(--shadow); padding:24px 26px; color:var(--ink); }
  dialog.sheet::backdrop { background:rgba(15,15,15,.45); }
  dialog.sheet .close { float:right; margin:-4px -6px 0 12px; }
  .title-actions { display:flex; gap:2px; }
  .howto-box { width:min(640px, 92vw); }
  .howto-box h2 { font-size:20px; margin-bottom:10px; }
  .howto-box p { margin:0 0 10px; }
  .howto-box .step { color:var(--muted); margin-top:16px; }
  .howto-box .step em { color:var(--ink); font-style:normal; }
  .cmd { display:flex; align-items:flex-start; gap:8px; background:var(--tile); border-radius:6px; padding:10px 10px 10px 14px; }
  .cmd code { flex:1; font:13px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; word-break:break-all; }
  .howto-props { grid-template-columns:90px 1fr; margin:20px 0 0; padding-top:16px; border-top:1px solid var(--line); font-size:13px; }
  .pricing-box { width:min(520px, 92vw); }
  .pricing-box h3 { margin:0; font-size:16px; font-weight:600; display:flex; align-items:center; }
  .pnote { color:var(--muted); font-size:12.5px; margin-top:4px; }
  .ptable { width:100%; border-collapse:collapse; margin:16px 0 10px; font-size:13.5px; }
  .ptable th { text-align:left; font-weight:500; color:var(--muted); font-size:12.5px; padding:6px 8px; border-bottom:1px solid var(--line); }
  .ptable td { padding:7px 8px; border-bottom:1px solid var(--line); }
  .ptable tfoot td { border-bottom:0; font-weight:600; }
  .ptable tfoot tr + tr td { font-weight:400; color:var(--muted); font-size:12.5px; }

  /* Image viewer: fits the window by default; "100%" shows actual pixels and scrolls. */
  dialog.viewer { border:0; padding:0; width:100vw; height:100vh; max-width:none; max-height:none; background:rgba(15,15,15,.92); color:#fff; }
  dialog.viewer::backdrop { background:rgba(0,0,0,.6); }
  .viewer .bar { position:fixed; top:0; left:0; right:0; display:flex; align-items:center; gap:8px; padding:10px 16px; z-index:2; }
  .viewer .cap { flex:1; font-size:13px; color:rgba(255,255,255,.75); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .viewer button { font:inherit; font-size:13px; color:#fff; background:rgba(255,255,255,.1); border:0; border-radius:6px; padding:6px 12px; cursor:pointer; }
  .viewer button:hover { background:rgba(255,255,255,.2); }
  .viewer .stage { position:absolute; inset:52px 0 0 0; overflow:auto; display:flex; }
  .viewer .stage img { margin:auto; display:block; border-radius:4px; }
  .viewer.fit .stage img { max-width:calc(100vw - 32px); max-height:calc(100vh - 72px); cursor:zoom-in; }
  .viewer:not(.fit) .stage img { max-width:none; max-height:none; cursor:zoom-out; }
"""
