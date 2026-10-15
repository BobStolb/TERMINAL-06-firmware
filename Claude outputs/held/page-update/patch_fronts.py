import sys, os
src = sys.argv[1]          # recovered/viewer2/src


def patch(fn, pairs):
    p = os.path.join(src, fn)
    s = open(p, encoding="utf8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (fn, a[:90])
        s = s.replace(a, b)
    open(p, "w", encoding="utf8").write(s)
    print("patched", fn)


CSS = '''/* ---------- Fronts view */
.frontgrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-items: start; }
.disprow { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr); gap: 16px; align-items: start; }
@media (max-width: 900px) { .disprow { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 760px) { .frontgrid { grid-template-columns: minmax(0, 1fr); } }
.front { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; box-shadow: var(--shadow); min-width: 0; }
.front .pic { display: block; width: 100%; padding: 0; margin: 0; border: 0; background: #0f1113; cursor: zoom-in; }
.front .pic:focus-visible { outline: 2px solid var(--accent); outline-offset: -2px; }
.front .pic img { display: block; width: 100%; height: auto; }
.front figcaption { padding: 12px 14px 14px; font-size: 14px; }
.front figcaption p { margin: 0 0 6px; max-width: 78ch; }
.front h3 { font: 600 16px/1.3 var(--f-body); margin: 0 0 6px; display: flex; gap: 6px 10px; flex-wrap: wrap; align-items: baseline; }
.front h3 .fid { font: 500 12px var(--f-mono); color: var(--muted); }
.front .lights { font-size: 13px; color: var(--muted); }
.front .lights b { color: var(--text); font-weight: 600; }
.front .src { font: 11.5px var(--f-mono); color: var(--muted); overflow-wrap: anywhere; margin: 0; }
.front .owner { margin: 8px 0; padding: 6px 12px; border-left: 3px solid var(--accent); background: var(--surface-2); border-radius: 0 6px 6px 0; font-size: 14px; }
.front .owner q { font-style: italic; }
.front .owner span { display: block; font: 12px var(--f-mono); color: var(--muted); margin-top: 2px; }
.inreview { font-size: 14px; color: var(--muted); margin: 14px 0 0; }
#frontdlg { width: min(96vw, 1600px); max-width: none; max-height: 94vh; padding: 0; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); color: var(--text); overflow: hidden; }
#frontdlg::backdrop { background: rgba(0, 0, 0, .72); }
#frontdlg .dlghead { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 8px 12px; border-bottom: 1px solid var(--line); font: 500 13.5px var(--f-body); }
#frontdlg .dlgimg { overflow: auto; max-height: calc(94vh - 50px); background: #0f1113; }
#frontdlg .dlgimg img { display: block; width: 100%; height: auto; }
/* ---------- Order view */'''

patch("index.html", [
    ('/* ---------- Order view */', CSS),
    ('''    <button class="doctab" role="tab" id="dt-fascia" data-doc="fascia" aria-selected="false">Fascia variants</button>''',
     '''    <button class="doctab" role="tab" id="dt-fascia" data-doc="fascia" aria-selected="false">Fascia variants</button>
    <button class="doctab" role="tab" id="dt-fronts" data-doc="fronts" aria-selected="false">Fronts</button>'''),
    ('''  <section class="docpanel" id="doc-order" role="tabpanel" aria-labelledby="dt-order" hidden>''',
     '''  <section class="docpanel" id="doc-fronts" role="tabpanel" aria-labelledby="dt-fronts" hidden>
    <div id="frontsbody"><p class="lead">Loading the fronts…</p></div>
    <dialog id="frontdlg" aria-labelledby="frontdlg-title">
      <div class="dlghead"><span id="frontdlg-title"></span><button type="button" class="btn" id="frontdlg-close">Close</button></div>
      <div class="dlgimg"><img id="frontdlg-img" alt=""></div>
    </dialog>
  </section>

  <section class="docpanel" id="doc-order" role="tabpanel" aria-labelledby="dt-order" hidden>'''),
])

JS = r'''// ------------------------------------------------------------------------------------------ fronts
// One back, many fronts: the owner's shortlist from front round 3, as pictures (data/fronts.json, written by tools/fronts.py from
// tools/fronts.json; the pictures are web copies of the PNGs in PCB/art, made at build time). A "final candidate" is on the owner's
// shortlist, a face the owner is willing to approve; "approved" is approved (K4W411). The fronts are drawings: no board carries them yet.
let FRONTS = null;
const frontPill = s => `<span class="pill ${s === 'approved' ? 'ok' : 'acc'}">${esc(s)}</span>`;
function frontFig(e, kind) {
  const title = kind === 'colours' ? 'Colour settings on disp-3-4' : (e.name && e.name !== e.id ? `${e.id} · ${e.name}` : e.id);
  const head = kind === 'colours' ? `<h3>Colour settings <span class="fid">disp-3-4</span></h3>`
    : `<h3>${esc(e.name && e.name !== e.id ? e.name : e.id)} ${e.name && e.name !== e.id ? `<span class="fid">${esc(e.id)}</span>` : ''}${e.theme ? `<span class="fid">${esc(e.theme)}</span>` : ''} ${frontPill(e.status)}</h3>`;
  const owner = e.owner ? `<blockquote class="owner" id="fronts-owner"><q>${esc(e.owner.text)}</q><span>the owner, ${esc(e.owner.when)}</span></blockquote>` : '';
  const lights = e.lights ? `<p class="lights"><b>Lights.</b> ${esc(e.lights)}</p>` : '';
  return `<figure class="front${kind ? ' ' + kind : ''}" data-front="${esc(e.id)}"${e.status ? ` data-status="${esc(e.status)}"` : ''}>
    <button type="button" class="pic" data-full="${esc(e.src)}" data-title="${esc(title)}" aria-label="${esc(title)}: open the picture full size">
      <img src="${esc(e.card)}" width="${e.card_w}" height="${e.card_h}" alt="${esc(title)}, the drawing" loading="lazy" decoding="async"></button>
    <figcaption>${head}<p class="cap">${esc(e.caption)}</p>${owner}${lights}<p class="src">${esc(e.from)}${e.writeup ? ' · ' + esc(e.writeup) : ''}</p></figcaption></figure>`;
}
function renderFronts() {
  const el = $('#frontsbody');
  if (!el) return;
  if (!FRONTS) { el.innerHTML = '<div class="card"><p>The fronts were not built (<code>data/fronts.json</code>).</p></div>'; return; }
  const R = FRONTS, d = R.display, nApp = R.fascias.filter(e => e.status === 'approved').map(e => e.id);
  const rev = R.in_review || [];
  el.innerHTML = `
    <p class="lead"><b>One back, many fronts.</b> The boards behind the face stay the same; the faces change. These are the owner’s final candidates from ${esc(R.round)}: the display and six fascias. A final candidate is on the owner’s shortlist, a face the owner is willing to approve.${nApp.length ? ` Approved: <b>${nApp.map(esc).join(', ')}</b>.` : ''}</p>
    <div class="caution" id="fronts-drawings"><b>Drawings, not boards.</b> ${esc(R.drawings)}${R.grill ? ` The K4W411 grill, <code>${esc(R.grill)}</code>, lists what that face needs.` : ''}</div>
    <h2 class="osec">The display</h2>
    <div class="disprow" id="fronts-display">${frontFig(d, 'display')}${d.colours ? frontFig(d.colours, 'colours') : ''}</div>
    <h2 class="osec">The fascias</h2>
    <div class="frontgrid" id="fronts-fascias">${R.fascias.map(e => frontFig(e, '')).join('')}</div>
    ${rev.length ? `<p class="inreview" id="fronts-review">Still in review, and not shown here: ${rev.map(esc).join(', ')}. The earlier faces that were not chosen are not shown either.</p>` : ''}
    <p class="sm" style="margin-top:10px">The pictures are web copies (WebP, 2400 px at most) of the drawings in <code>PCB/art</code>, made when this page was built; select one to see it full size. Source: <code>${esc(R.source)}</code>.</p>`;
}
function openFront(b) {
  const dlg = $('#frontdlg'), img = $('#frontdlg-img');
  img.src = b.dataset.full; img.alt = b.dataset.title + ', full size';
  $('#frontdlg-title').textContent = b.dataset.title;
  if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
  V.frontFrom = b;
}
function closeFront() {
  const dlg = $('#frontdlg');
  if (dlg.open) { if (dlg.close) dlg.close(); else dlg.removeAttribute('open'); }
}

// ------------------------------------------------------------------------------------------ order'''

patch("app.js", [
    ("// ------------------------------------------------------------------------------------------ order", JS),
    ("const DOCS = ['sections', 'panel', 'fascia', 'order', 'test', 'kicad', 'notes'];",
     "const DOCS = ['sections', 'panel', 'fascia', 'fronts', 'order', 'test', 'kicad', 'notes'];"),
    ("    ORDER = await getJSON('data/order.json').catch(() => null);",
     "    ORDER = await getJSON('data/order.json').catch(() => null);\n    FRONTS = await getJSON('data/fronts.json').catch(() => null);        // the Fronts view (tools/fronts.py)"),
    ("  renderOrder();\n  const h = location.hash.slice(1);", "  renderOrder();\n  renderFronts();\n  const h = location.hash.slice(1);"),
    ("  window.addEventListener('hashchange', () => { const h = location.hash.slice(1); if (DOCS.includes(h)) setDoc(h, false); });",
     "  window.addEventListener('hashchange', () => { const h = location.hash.slice(1); if (DOCS.includes(h)) setDoc(h, false); });\n"
     "  $('#frontsbody').addEventListener('click', e => { const b = e.target.closest('button.pic'); if (b) openFront(b); });\n"
     "  $('#frontdlg-close').addEventListener('click', closeFront);\n"
     "  $('#frontdlg').addEventListener('click', e => { if (e.target === e.currentTarget) closeFront(); });   // a click on the backdrop\n"
     "  $('#frontdlg').addEventListener('close', () => { if (V.frontFrom) V.frontFrom.focus(); });"),
])
