import sys
p = sys.argv[1]
s = open(p, encoding="utf8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)


rep("""const ONLY_WIRING = process.env.ONLY_WIRING === '1';       // just the wiring checks (the lead, the hand wiring, the Wiring switch, the fascia selector)
const ONLY_NEW = process.env.ONLY_NEW === '1' || ONLY_WIRING;""",
    """const ONLY_WIRING = process.env.ONLY_WIRING === '1';       // just the wiring checks (the lead, the hand wiring, the Wiring switch, the fascia selector)
const ONLY_FRONTS = process.env.ONLY_FRONTS === '1';       // just the Fronts view's checks (about a minute)
const ONLY_NEW = process.env.ONLY_NEW === '1' || ONLY_WIRING || ONLY_FRONTS;""")
rep("""//   ONLY_NEW=1 node test/run.mjs       only the checks of the populated boards and the Order view (about 5 minutes)""",
    """//   ONLY_NEW=1 node test/run.mjs       only the checks of the populated boards, the Order view, the Fronts view and the wiring
//   ONLY_FRONTS=1 node test/run.mjs    only the Fronts view's checks""")
rep("""import { spawn } from 'node:child_process';""", """import { spawn, execFileSync } from 'node:child_process';""")
rep("""// ================================================================ populated boards and the Order view""",
    """// ================================================================ populated boards and the Order view (not with ONLY_FRONTS)""")
rep("""if (!ONLY_WIRING) {
  const rd = f => JSON.parse(fs.readFileSync(path.join(SITE, 'data', f), 'utf8'));
  const pop = rd('populated.json'), order = rd('order.json');""",
    """if (!ONLY_WIRING && !ONLY_FRONTS) {
  const rd = f => JSON.parse(fs.readFileSync(path.join(SITE, 'data', f), 'utf8'));
  const pop = rd('populated.json'), order = rd('order.json');""")
rep("""    ok('publish limits: every file 15 MB or less, the version under 256 MB', files.every(f => f.n <= 15 * 1048576) && total < 256 * 1048576 && files.length < 511,""",
    """    ok('publish limits: every file 15 MB or less, the version under 256 MB; one publish under 64 MB and 255 files', files.every(f => f.n <= 15 * 1048576) && total < 64 * 1048576 && files.length <= 255,""")

FRONTS = r"""// ================================================================ the Fronts view: one back, many fronts
// The owner's shortlist from front round 3 as pictures: the display disp-3-4 and six fascias, each a "final candidate" except K4W411, the one
// "approved". The pictures are web copies of PCB/art's PNGs made by the build (tools/fronts.py); nothing is written under PCB/art.
if (!ONLY_WIRING) {
  const FR = JSON.parse(fs.readFileSync(path.join(SITE, 'data', 'fronts.json'), 'utf8'));
  const SEVEN = ['disp-3-4', 'organic-2-1', 'organic-2-2', 'science-2-3', 'celestial-3', 'K4W411', 'BLUPRNT'];
  const STATUS = { 'disp-3-4': 'final candidate', 'organic-2-1': 'final candidate', 'organic-2-2': 'final candidate', 'science-2-3': 'final candidate', 'celestial-3': 'final candidate', K4W411: 'approved', BLUPRNT: 'final candidate' };
  // the web copies: WebP, 2400 px at most, a few hundred kB, one per picture plus its card; the sources are the repository's PNGs, unchanged
  {
    const pics = [FR.display, FR.display.colours, ...FR.fascias];
    const sizes = pics.map(q => ({ id: q.id, w: q.w, h: q.h, kb: Math.round(q.bytes / 1024), ck: Math.round(q.card_bytes / 1024), on: fs.existsSync(path.join(SITE, q.src)) && fs.existsSync(path.join(SITE, q.card)), webp: /\.webp$/.test(q.src) && /\.webp$/.test(q.card), from: fs.existsSync(path.join(REPO, q.from)) && /^PCB\/art\/.*\.png$/.test(q.from) }));
    const art = execFileSync('git', ['-C', REPO, 'status', '--porcelain', '--', 'PCB/art'], { encoding: 'utf8' }).trim();
    ok('Fronts: web copies of the seven faces and the colour settings, WebP, the longest side 2400 px or less, under 500 kB each (cards under 200 kB), made from the PNGs of PCB/art; nothing new under PCB/art',
      sizes.length === 8 && sizes.every(q => q.on && q.webp && q.from && Math.max(q.w, q.h) <= 2400 && q.kb < 500 && q.ck < 200) && art === '' && [FR.display.id, ...FR.fascias.map(e => e.id)].join() === SEVEN.join(),
      sizes.map(q => `${q.id} ${q.w}x${q.h} ${q.kb}/${q.ck} kB`).join('; ') + (art ? ' | PCB/art changed: ' + art : ''));
  }
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900 });
  await load(page, '#fronts', true);
  // the pictures are lazy: bring each into view, then wait for it
  const figs = await page.$$('#doc-fronts figure.front');
  for (const f of figs) { await f.scrollIntoViewIfNeeded(); }
  await page.waitForFunction(() => [...document.querySelectorAll('#doc-fronts figure.front img')].every(i => i.complete && i.naturalWidth > 0), null, { timeout: 60000 }).catch(() => {});
  const F7 = await page.evaluate(() => {
    const t = e => (e ? e.textContent.replace(/\s+/g, ' ').trim() : '');
    return {
      open: !document.querySelector('#doc-fronts').hidden && document.querySelector('#dt-fronts').getAttribute('aria-selected') === 'true',
      tabs: [...document.querySelectorAll('.doctab')].map(b => b.dataset.doc).join(),
      figs: [...document.querySelectorAll('#doc-fronts figure.front')].map(f => ({ id: f.dataset.front, status: f.dataset.status || '', pill: t(f.querySelector('h3 .pill')), cap: t(f.querySelector('.cap')), lights: t(f.querySelector('.lights')), links: f.querySelectorAll('figcaption a').length,
        img: (() => { const i = f.querySelector('img'); return { ok: i.complete && i.naturalWidth > 0, nw: i.naturalWidth, src: i.getAttribute('src') }; })() })),
      owner: t(document.querySelector('#fronts-owner')), review: t(document.querySelector('#fronts-review')), drawings: t(document.querySelector('#fronts-drawings')),
      lead: t(document.querySelector('#doc-fronts .lead')), all: t(document.querySelector('#doc-fronts')),
      srcs: [...document.querySelectorAll('#doc-fronts img')].map(i => i.getAttribute('src') || '').join(' '),
      sw: document.documentElement.scrollWidth,
    };
  });
  await page.locator('#doc-fronts').scrollIntoViewIfNeeded();
  await shot(page, 'd1280-light-fronts', true);
  const faces = F7.figs.filter(f => f.status);
  ok('Fronts: the tab opens from #fronts and sits after Fascia variants', F7.open && /fascia,fronts,order/.test(F7.tabs), F7.tabs);
  ok('Fronts: the seven pictures load (the display disp-3-4 and the six fascias), and the colour settings of disp-3-4',
    faces.map(f => f.id).join() === SEVEN.join() && F7.figs.length === 8 && F7.figs.every(f => f.img.ok && f.img.nw >= 1000) && F7.figs.some(f => f.id === 'disp-3-4-colours'),
    F7.figs.map(f => `${f.id} ${f.img.ok ? f.img.nw + 'px' : 'NOT LOADED'}`).join(', '));
  ok('Fronts: K4W411 alone is approved; disp-3-4, organic-2-1, organic-2-2, science-2-3, celestial-3 and BLUPRNT are final candidates (the page says "approved" of nothing else)',
    faces.every(f => f.status === STATUS[f.id] && f.pill === STATUS[f.id]) && faces.filter(f => f.pill === 'approved').map(f => f.id).join() === 'K4W411'
    && (F7.all.match(/approved/gi) || []).length === 2 && /Approved: K4W411\./.test(F7.lead) && /final candidates/.test(F7.lead),
    faces.map(f => `${f.id}: ${f.pill}`).join(', ') + ` | "approved" ${(F7.all.match(/approved/gi) || []).length}x`);
  ok('Fronts: each face has its caption, each fascia its light colours, with no links in them; the display carries the owner’s words on the glyph colours',
    faces.every(f => f.cap.length > 60) && faces.filter(f => f.id !== 'disp-3-4').every(f => /^Lights\. .{20,}/.test(f.lights) && /warm|white|pink|blue|green/.test(f.lights)) && F7.figs.every(f => f.links === 0)
    && /color of the paricular glyphs might change/.test(F7.owner) && /the owner, 2026-10-14/.test(F7.owner),
    faces.map(f => `${f.id}: ${f.cap.slice(0, 30)}… ${f.lights.slice(0, 40)}`).join(' | ').slice(0, 400));
  ok('Fronts: one line names the themes still in review (steampunk, radio, celestial-2, VAPORWAVE), with no picture of them or of an earlier face',
    ['steampunk', 'radio', 'celestial-2', 'VAPORWAVE'].every(w => F7.review.includes(w)) && !/steampunk|radio|celestial-2|vaporwave|celestial-1|orrery|astrolabe|science-2-1|science-2-2|organic-2-3|disp-3-[123]-|kawaii|info-2/i.test(F7.srcs),
    F7.review.slice(0, 160));
  ok('Fronts: a plain note says the fronts are drawings, and the board-change run comes after the owner’s approved list is complete (the K4W411 grill lists what it needs)',
    /Drawings, not boards/.test(F7.drawings) && /board-change run/.test(F7.drawings) && /approved fronts is complete/.test(F7.drawings) && F7.drawings.includes('PCB/art/TS06-FASCIA-K4W411-grill.md') && fs.existsSync(path.join(REPO, 'PCB', 'art', 'TS06-FASCIA-K4W411-grill.md')),
    F7.drawings.slice(0, 160));
  // a picture opens full size, and Escape closes it
  await page.click('#doc-fronts figure[data-front="K4W411"] button.pic');
  await page.waitForFunction(() => { const i = document.querySelector('#frontdlg-img'); return document.querySelector('#frontdlg').open && i.complete && i.naturalWidth > 0; }, null, { timeout: 30000 }).catch(() => {});
  const dl = await page.evaluate(() => ({ open: document.querySelector('#frontdlg').open, nw: document.querySelector('#frontdlg-img').naturalWidth, title: document.querySelector('#frontdlg-title').textContent }));
  await page.keyboard.press('Escape'); await page.waitForTimeout(200);
  const closed = await page.evaluate(() => !document.querySelector('#frontdlg').open && document.activeElement && document.activeElement.closest('figure[data-front="K4W411"]') !== null);
  ok('Fronts: a picture opens full size (2400 px) in a dialog, Escape closes it and gives the focus back', dl.open && dl.nw === FR.fascias.find(e => e.id === 'K4W411').w && dl.nw === 2400 && /K4W411/.test(dl.title) && closed, JSON.stringify(dl) + ' closed ' + closed);
  ok('Fronts desktop: no horizontal scroll, no console errors', F7.sw <= 1280 && errs.length === 0, `scrollWidth ${F7.sw} ` + errs.slice(0, 3).join(' || '));
  await ctx.close();
  // the phone, light and dark: 16 px gutters, no sideways scroll, the faces stacked one above another
  for (const scheme of ['light', 'dark']) {
    const { ctx: c2, page: p2, errs: e2 } = await newPage({ w: 390, h: 844, scheme, touch: true, mobile: true });
    await load(p2, '#fronts', true);
    for (const f of await p2.$$('#doc-fronts figure.front')) await f.scrollIntoViewIfNeeded();
    await p2.waitForFunction(() => [...document.querySelectorAll('#doc-fronts figure.front img')].every(i => i.complete && i.naturalWidth > 0), null, { timeout: 60000 }).catch(() => {});
    const r = await p2.evaluate(() => {
      const fs_ = [...document.querySelectorAll('#doc-fronts figure.front')].map(f => f.getBoundingClientRect());
      return { sw: document.documentElement.scrollWidth, left: Math.min(...fs_.map(b => b.left)), right: Math.max(...fs_.map(b => b.right)), n: fs_.length,
        stacked: fs_.every((b, i) => i === 0 || b.top >= fs_[i - 1].bottom - 1), loaded: [...document.querySelectorAll('#doc-fronts figure.front img')].every(i => i.complete && i.naturalWidth > 0),
        bg: getComputedStyle(document.body).backgroundColor, fig: getComputedStyle(document.querySelector('#doc-fronts figure.front')).backgroundColor };
    });
    await p2.locator('#fronts-fascias figure[data-front="K4W411"]').scrollIntoViewIfNeeded();
    await p2.waitForTimeout(300); await shot(p2, `p390-${scheme}-fronts`);
    const dark = scheme === 'dark', lum = c => { const m = c.match(/\d+/g).map(Number); return (m[0] + m[1] + m[2]) / 3; };
    ok(`Fronts phone ${scheme}: fits 390 with 16 px gutters, no sideways scroll, the eight pictures stacked and loaded, the ${scheme} theme, no console errors`,
      r.sw <= 390 && Math.abs(r.left - 16) < 0.5 && Math.abs(r.right - (390 - 16)) < 0.5 && r.n === 8 && r.stacked && r.loaded && (dark ? lum(r.bg) < 80 && lum(r.fig) < 80 : lum(r.bg) > 180 && lum(r.fig) > 180) && e2.length === 0,
      `scrollWidth ${r.sw}, figures ${r.left.toFixed(1)}..${r.right.toFixed(1)}, bg ${r.bg}, card ${r.fig} ` + e2.slice(0, 3).join(' || '));
    await c2.close();
  }
}


// ================================================================ the wiring: the lead, the hand wiring, the Wiring switch, the fascia selector"""
rep("""// ================================================================ the wiring: the lead, the hand wiring, the Wiring switch, the fascia selector""", FRONTS)
# the wiring block does not run with ONLY_FRONTS
i = s.index("// ================================================================ the wiring: the lead, the hand wiring, the Wiring switch, the fascia selector")
j = s.index("\n{\n", i)
s = s[:j] + "\nif (!ONLY_FRONTS) {\n" + s[j + 3:]
open(p, "w", encoding="utf8").write(s)
print("patched", p)
