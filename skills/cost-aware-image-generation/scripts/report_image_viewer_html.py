"""Full-screen image viewer for the usage report: the image on the left, that run's details on the right.

Clicking any image in the runs table opens it here. The right-hand panel copies
the row's hidden <template class="vinfo-t"> (built by export_usage_html), so it
shows the same prompt, settings, tokens and cost as the table. Left/Right arrow
keys (or the Previous/Next buttons) step through the runs that are currently
shown in the table, in table order. It stops at the first and last run instead
of wrapping around.
"""

DIALOG = """<dialog id="viewer" class="viewer fit"><div class="bar">
  <button type="button" data-act="prev" aria-label="Previous generation">← Previous</button>
  <button type="button" data-act="next" aria-label="Next generation">Next →</button>
  <div class="cap"></div>
  <button type="button" data-act="zoom">Zoom to 100%</button><button type="button" data-close aria-label="Close">✕</button></div>
  <div class="vbody"><div class="stage"><img alt="Full-size image"><div class="vnoimg" hidden>No image for this run</div></div>
  <aside class="vinfo"></aside></div></dialog>"""

CSS = """
  /* Image viewer: image fits its pane by default; "100%" shows actual pixels and scrolls. */
  dialog.viewer { border:0; padding:0; width:100vw; height:100vh; max-width:none; max-height:none; background:#191918; color:#fff; }
  dialog.viewer::backdrop { background:rgba(0,0,0,.6); }
  .viewer .bar { position:fixed; top:0; left:0; right:0; height:52px; display:flex; align-items:center; gap:8px; padding:10px 16px; z-index:2; }
  .viewer .cap { flex:1; font-size:13px; color:rgba(255,255,255,.75); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .viewer .bar button { font:inherit; font-size:13px; color:#fff; background:rgba(255,255,255,.1); border:0; border-radius:6px; padding:6px 12px; cursor:pointer; }
  .viewer .bar button:hover:not(:disabled) { background:rgba(255,255,255,.2); }
  .viewer .bar button:disabled { opacity:.35; cursor:default; }
  .viewer .vbody { position:absolute; inset:52px 0 0 0; display:grid; grid-template-columns:minmax(0, 1fr) 420px; }
  .viewer .stage { overflow:auto; display:flex; }
  .viewer .stage img { margin:auto; display:block; border-radius:4px; }
  .viewer .stage img[hidden] { display:none; }
  .viewer.fit .stage img { max-width:calc(100% - 32px); max-height:calc(100vh - 84px); cursor:zoom-in; }
  .viewer:not(.fit) .stage img { max-width:none; max-height:none; cursor:zoom-out; }
  .viewer .vnoimg { margin:auto; color:rgba(255,255,255,.5); }

  /* Right-hand details panel */
  .vinfo { overflow-y:auto; padding:8px 22px 28px; background:#222221; border-left:1px solid rgba(255,255,255,.08); font-size:13.5px; }
  .vinfo .logo { color:#fff; }
  .vinfo .vi-when { font-size:17px; font-weight:600; margin-top:10px; }
  .vinfo .vi-model { margin-top:6px; color:rgba(255,255,255,.85); }
  .vinfo h4 { margin:20px 0 8px; font-size:12px; font-weight:500; color:rgba(255,255,255,.5); text-transform:uppercase; letter-spacing:.04em; }
  .vinfo .vi-props { display:grid; grid-template-columns:90px 1fr; gap:6px 12px; margin:16px 0 0; }
  .vinfo .vi-props dt { color:rgba(255,255,255,.5); }
  .vinfo .vi-props dd { margin:0; font-variant-numeric:tabular-nums; word-break:break-word; }
  .vinfo .vi-imgs { display:flex; flex-wrap:wrap; gap:8px; }
  .vinfo .vi-imgs figure { margin:0; text-align:center; font-size:11.5px; color:rgba(255,255,255,.5); }
  .vinfo .vi-imgs img { width:56px; height:56px; object-fit:cover; border-radius:5px; cursor:pointer; display:block; margin-bottom:3px;
    box-shadow:0 0 0 1px rgba(255,255,255,.12); }
  .vinfo .vi-imgs img.on { box-shadow:0 0 0 2px #fff; }
  .vinfo .vi-tokens { width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }
  .vinfo .vi-tokens td { padding:4px 0; border-bottom:1px solid rgba(255,255,255,.08); }
  .vinfo .vi-tokens td + td { text-align:right; padding-left:12px; }
  .vinfo .vi-tokens .zero { color:rgba(255,255,255,.3); }
  .vinfo .reason { color:#f0c060; }
  .vinfo .error { color:#ff8a80; }
  .vinfo .codeblock { background:rgba(255,255,255,.06); box-shadow:none; margin:0; }
  .vinfo .codeblock code { color:#ececea; }
  .vinfo .cb-bar { color:rgba(255,255,255,.5); }
  .vinfo .ghost { color:rgba(255,255,255,.6); }
  .vinfo .ghost:hover { background:rgba(255,255,255,.1); color:#fff; }
  .vinfo .runid { color:rgba(255,255,255,.35); }

  /* Narrow screens: details go under the image and the whole viewer scrolls. */
  @media (max-width: 860px) {
    .viewer .vbody { display:block; overflow-y:auto; }
    .viewer .stage { height:60vh; }
    .viewer.fit .stage img { max-height:calc(60vh - 24px); }
    .vinfo { border-left:0; border-top:1px solid rgba(255,255,255,.08); overflow:visible; }
  }
"""

JS = """
  // Image viewer: picture on the left, the run's details on the right, arrow keys step through runs.
  const viewer = document.getElementById('viewer'), big = viewer.querySelector('.stage img');
  const noImg = viewer.querySelector('.vnoimg'), info = viewer.querySelector('.vinfo'), cap = viewer.querySelector('.cap');
  const zoomBtn = viewer.querySelector('[data-act=zoom]');
  const prevBtn = viewer.querySelector('[data-act=prev]'), nextBtn = viewer.querySelector('[data-act=next]');
  let runs = [], at = -1;

  function setFit(fit) { viewer.classList.toggle('fit', fit); zoomBtn.textContent = fit ? 'Zoom to 100%' : 'Fit to window'; }

  function showImage(src) {
    big.hidden = !src; noImg.hidden = !!src; zoomBtn.disabled = !src;
    if (src) big.src = src; else big.removeAttribute('src');
    info.querySelectorAll('.vi-imgs img').forEach(t => t.classList.toggle('on', t.dataset.src === src));
    const dims = info.querySelector('.vi-dims');
    if (dims) dims.textContent = '…';
  }

  // Show run number i of the rows currently visible in the table; src picks an input image instead of the output.
  function showRun(i, src) {
    at = Math.max(0, Math.min(runs.length - 1, i));
    const row = runs[at];
    info.replaceChildren(row.querySelector('template.vinfo-t').content.cloneNode(true));
    info.scrollTop = 0;
    const out = row.querySelector('td.c-img img');
    setFit(true);
    showImage(src || (out && out.getAttribute('src')));
    cap.textContent = `Generation ${at + 1} of ${runs.length}`;
    prevBtn.disabled = at === 0; nextBtn.disabled = at === runs.length - 1;
  }

  document.addEventListener('click', e => {
    const t = e.target.closest('img[data-zoom]');
    if (!t || viewer.contains(t)) return;
    runs = [...document.querySelectorAll('table.runs tbody tr')].filter(tr => !tr.hidden);
    showRun(runs.indexOf(t.closest('tr')), t.getAttribute('src'));
    viewer.showModal();
  });
  // Thumbnails in the details panel swap the big image without leaving the run.
  info.addEventListener('click', e => { const t = e.target.closest('.vi-imgs img'); if (t) { setFit(true); showImage(t.dataset.src); } });
  big.addEventListener('load', () => {
    const dims = info.querySelector('.vi-dims');
    if (dims) dims.textContent = `${big.naturalWidth} × ${big.naturalHeight} px`;
  });
  prevBtn.addEventListener('click', () => { if (at > 0) showRun(at - 1); });
  nextBtn.addEventListener('click', () => { if (at < runs.length - 1) showRun(at + 1); });
  viewer.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();  // no wrap-around: the first and last runs are hard stops
      if (e.key === 'ArrowLeft' && at > 0) showRun(at - 1);
      if (e.key === 'ArrowRight' && at < runs.length - 1) showRun(at + 1);
    }
  });
  zoomBtn.addEventListener('click', () => setFit(!viewer.classList.contains('fit')));
  big.addEventListener('click', () => setFit(!viewer.classList.contains('fit')));
  viewer.querySelector('.stage').addEventListener('click', e => { if (e.target === e.currentTarget) viewer.close(); });
"""
