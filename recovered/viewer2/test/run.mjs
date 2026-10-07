// Playwright checks for the TS06 board viewer v2.
//   node test/run.mjs            (from viewer2/; serves site/ on :8766, CDN routed to the vendored three)
//   SITE=DIR THREE=DIR SHOTS=DIR node test/run.mjs     the built site, three.js and the screenshots elsewhere
//                                (build.sh OUT=DIR puts the site in DIR/site, outside the checkout)
//   ONLY_NEW=1 node test/run.mjs       only the checks of the populated boards and the Order view (about 5 minutes)
// three.js: the CDN requests are answered from THREE, by default 3d/populated/stack/vendor/three of this repository
// (r186, MIT: the same files the page loads from the CDN). The repository root is REPO (two folders up).
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '..');
const REPO = path.resolve(ROOT, '..', '..');
const SITE = process.env.SITE ? path.resolve(process.env.SITE) : path.join(ROOT, 'site');
const THREE = process.env.THREE ? path.resolve(process.env.THREE) : path.join(REPO, '3d', 'populated', 'stack', 'vendor', 'three');
const SHOTS = process.env.SHOTS ? path.resolve(process.env.SHOTS) : path.join(ROOT, 'shots');
const ONLY_WIRING = process.env.ONLY_WIRING === '1';       // just the wiring checks (the lead, the hand wiring, the Wiring switch, the fascia selector)
const ONLY_NEW = process.env.ONLY_NEW === '1' || ONLY_WIRING;
fs.mkdirSync(SHOTS, { recursive: true });
const PORT = 8766;
const server = spawn('python3', [path.join(HERE, 'serve.py'), String(PORT)], { cwd: SITE, stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));
process.on('exit', () => { try { server.kill(); } catch (e) { /* already gone */ } });
{   // a server left over from an earlier run on this port would answer with another build: check it serves SITE
  const served = await fetch(`http://127.0.0.1:${PORT}/index.html`).then(r => r.text()).catch(() => null);
  if (served !== fs.readFileSync(path.join(SITE, 'index.html'), 'utf8')) {
    console.error(`port ${PORT} does not serve ${SITE}: a server from an earlier run is probably still up (pkill -f "serve.py ${PORT}")`);
    server.kill(); process.exit(2);
  }
}

const results = [];
const ok = (name, pass, detail = '') => { results.push({ name, pass, detail }); console.log((pass ? 'PASS ' : 'FAIL ') + name + (detail ? '  ' + detail : '')); };

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const cdnHits = new Set();
async function newPage({ w, h, scheme = 'light', touch = false, mobile = false }) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: scheme, deviceScaleFactor: 1, hasTouch: touch, isMobile: mobile });
  const page = await ctx.newPage();
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('requestfailed', r => { if (!r.url().startsWith('data:')) errs.push('requestfailed: ' + r.url() + ' ' + (r.failure() || {}).errorText); });
  await page.route('https://cdn.jsdelivr.net/npm/three@0.186.1/**', r => {
    const rel = r.request().url().split('three@0.186.1/')[1].split('?')[0];
    cdnHits.add(rel);
    const f = path.join(THREE, rel);
    if (!fs.existsSync(f)) return r.fulfill({ status: 404, body: 'missing ' + rel });
    r.fulfill({ path: f, contentType: 'application/javascript' });
  });
  await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '/* fonts stubbed in test */', contentType: 'text/css' }));
  await page.route('https://fonts.gstatic.com/**', r => r.fulfill({ status: 404, body: '' }));
  await page.route(u => !u.href.startsWith('http://127.0.0.1') && !u.href.startsWith('https://cdn.jsdelivr.net/') && !u.href.startsWith('https://fonts.') && !u.href.startsWith('data:') && !u.href.startsWith('blob:'), r => { errs.push('unexpected external request ' + r.request().url()); r.abort(); });
  return { ctx, page, errs };
}
async function load(page, hash = '', instant = true) {
  await page.goto(`http://127.0.0.1:${PORT}/index.html${hash}`);
  await page.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 240000 });
  await page.waitForTimeout(1200);
  if (instant) await page.evaluate(() => { window.TS06.animScale = 0; });
}
const cam = page => page.evaluate(() => {
  const V = window.TS06, p = V.camera.position, t = V.controls.target;
  return { p: [p.x, p.y, p.z], t: [t.x, t.y, t.z] };
});
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const dirOf = c => { const d = [c.p[0] - c.t[0], c.p[1] - c.t[1], c.p[2] - c.t[2]]; const L = Math.hypot(...d); return d.map(x => x / L); };
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
// a move has finished and its frame is drawn (labels are placed in the DOM when a frame renders)
const settle = async page => {
  await page.waitForFunction(() => !window.TS06.tween && (window.TS06.dirty <= 0 || !window.TS06.onscreen), null, { timeout: 180000 });
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  await page.waitForTimeout(200);
};
const shot = async (page, name, full = false) => {
  // software GL: let the pending frames finish before the compositor is asked for one
  await page.waitForFunction(() => !window.TS06 || ((window.TS06.dirty <= 0 || !window.TS06.onscreen) && !window.TS06.tween), null, { timeout: 180000 });
  await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  await page.screenshot({ path: path.join(SHOTS, name + '.png'), fullPage: full, timeout: 180000 });
};

// ================================================================ desktop, light
if (!ONLY_NEW) {
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900 });
  const t0 = Date.now();
  await load(page, '', false);
  ok('desktop loads, models built', true, `${((Date.now() - t0) / 1000).toFixed(1)} s`);
  await shot(page, 'd1280-light-overview');

  // ---- mouse drag on the canvas
  const box = await page.locator('#gl canvas').boundingBox();
  const c0 = await cam(page);
  const cx = box.x + box.width / 2, cy = box.y + box.height / 2;
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  for (let i = 1; i <= 12; i++) await page.mouse.move(cx + i * 18, cy + i * 4);
  await page.mouse.up();
  await page.waitForTimeout(900);
  const c1 = await cam(page);
  const ang = Math.acos(Math.min(1, dot(dirOf(c0), dirOf(c1)))) * 180 / Math.PI;
  ok('mouse drag orbits the camera', ang > 10, `camera turned ${ang.toFixed(1)}°, moved ${dist(c0.p, c1.p).toFixed(1)} mm`);

  // ---- right-drag pans
  const t0p = (await cam(page)).t;
  await page.mouse.move(cx, cy); await page.mouse.down({ button: 'right' });
  for (let i = 1; i <= 8; i++) await page.mouse.move(cx - i * 15, cy);
  await page.mouse.up({ button: 'right' }); await page.waitForTimeout(700);
  const t1p = (await cam(page)).t;
  ok('right-drag pans', dist(t0p, t1p) > 5, `target moved ${dist(t0p, t1p).toFixed(1)} mm`);

  // ---- wheel zooms
  const d0 = dist((await cam(page)).p, (await cam(page)).t);
  await page.mouse.move(cx, cy); await page.mouse.wheel(0, -600); await page.waitForTimeout(900);
  const cw = await cam(page);
  ok('wheel zooms', dist(cw.p, cw.t) < d0 * 0.95, `${d0.toFixed(0)} -> ${dist(cw.p, cw.t).toFixed(0)} mm`);

  // swiftshader draws the assembly at ~4 s a frame: after the drag tests, stop the damping tail
  // (dozens of frames) so the remaining checks and screenshots do not queue behind it
  await page.evaluate(() => { window.TS06.controls.enableDamping = false; });
  await page.waitForTimeout(500);
  // ---- one animated camera move (software GL draws a frame every few seconds, so only one)
  {
    const t0 = Date.now();
    await page.click('#deck [data-view="isoR"]');
    const moving = await page.evaluate(() => !!window.TS06.tween);
    await settle(page);
    const d = dot(dirOf(await cam(page)), [1 / Math.hypot(1, 0.72, 1.3), 0.72 / Math.hypot(1, 0.72, 1.3), 1.3 / Math.hypot(1, 0.72, 1.3)]);
    ok('animated view move (Iso R)', moving && d > 0.995, `tween started: ${moving}, alignment ${d.toFixed(4)}, ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  }
  await page.evaluate(() => { window.TS06.animScale = 0; });
  // ---- camera buttons
  const expect = { front: [0, 0, 1], back: [0, 0, -1], top: [0, 1, 0], bottom: [0, -1, 0], left: [-1, 0, 0], right: [1, 0, 0], isoL: [-1, 0.72, 1.3], isoR: [1, 0.72, 1.3] };
  for (const [v, e] of Object.entries(expect)) {
    await page.click(`#deck [data-view="${v}"]`);
    await settle(page);
    const L = Math.hypot(...e), d = dot(dirOf(await cam(page)), e.map(x => x / L));
    ok(`button ${v}`, d > 0.995, `alignment ${d.toFixed(4)}`);
  }
  await page.click('#deck [data-view="front"]'); await settle(page);
  if (true) {
    const a = await cam(page), da = dist(a.p, a.t);
    await page.click('#deck [data-zoom="in"]'); await settle(page);
    const b = await cam(page), db = dist(b.p, b.t);
    await page.click('#deck [data-zoom="out"]'); await page.click('#deck [data-zoom="out"]'); await settle(page);
    const c = await cam(page), dc = dist(c.p, c.t);
    ok('zoom + and −', db < da * 0.8 && dc > db * 1.5, `${da.toFixed(0)} → ${db.toFixed(0)} → ${dc.toFixed(0)} mm`);
  }
  await page.click('#deck [data-view="fit"]'); await settle(page);
  // keyboard: Tab to a view button, Enter; and keys on the focused stage
  await page.focus('#deck [data-view="top"]'); await page.keyboard.press('Enter'); await settle(page);
  ok('view button works from the keyboard (Enter)', dot(dirOf(await cam(page)), [0, 1, 0]) > 0.995);
  await page.focus('#gl'); await page.keyboard.press('1'); await settle(page);
  ok('stage key 1 = front', dot(dirOf(await cam(page)), [0, 0, 1]) > 0.995);
  await page.keyboard.press('ArrowLeft'); await settle(page);
  ok('stage arrow key orbits', dot(dirOf(await cam(page)), [0, 0, 1]) < 0.99);
  await page.click('#deck [data-view="isoL"]'); await settle(page);
  await shot(page, 'd1280-light-isoL');

  // ---- explode, case toggles
  await page.fill('#explode', '100'); await page.dispatchEvent('#explode', 'input');
  await page.click('#deck [data-view="fit"]'); await settle(page);
  const ex = await page.evaluate(() => window.TS06.explode);
  ok('explode slider', ex === 1, `explode ${ex}`);
  await shot(page, 'd1280-light-exploded');
  await page.fill('#explode', '0'); await page.dispatchEvent('#explode', 'input');
  await page.click('label[for="caseghost"]');
  await page.waitForTimeout(300);
  await shot(page, 'd1280-light-case-solid');
  await page.click('label[for="caseghost"]');

  // ---- steps
  await page.click('#stepnext'); await settle(page);
  let st = await page.evaluate(() => ({ step: window.TS06.step, chip: document.querySelector('#stepchip').textContent, labels: [...document.querySelectorAll('.lbl')].map(l => l.textContent) }));
  ok('Next starts step 1', st.step === 0 && /Build the driver board/.test(st.chip), JSON.stringify(st).slice(0, 160));
  await shot(page, 'd1280-light-step01');
  const vis = await page.evaluate(() => { const A = window.TS06.roots.asm; const shown = id => (A.items.get(id) || []).some(o => o.visible); return { drv: shown('drv'), strips: shown('drv.strips'), disp: shown('disp'), chip: shown('chip:U11'), cheek: shown('cheek_l') }; });
  ok('step 1 shows only the bare driver board', vis.drv && !vis.strips && !vis.disp && !vis.chip && !vis.cheek, JSON.stringify(vis));
  await page.click('#stepnext'); await settle(page);
  await page.click('#stepnext'); await settle(page);
  await shot(page, 'd1280-light-step03');
  await page.click('#stepprev'); await settle(page);
  st = await page.evaluate(() => window.TS06.step);
  ok('Prev goes back', st === 1, 'step index ' + st);
  // jump from the list: S3, S5, 9
  const idx = await page.evaluate(() => [...document.querySelectorAll('#steplist button')].map(b => b.textContent));
  const find = re => idx.findIndex(t => re.test(t)) - 1;
  for (const [re, name, want] of [[/U12 first/, 'S3', /U12 first/], [/U11 out/, 'S5', /U11 out/], [/Fit the fascia/, 'step09', /PH lead/], [/rear panel/, 'step10', /rear panel/]]) {
    const i = find(re);
    await page.click(`#steplist button[data-step="${i}"]`); await settle(page);
    await page.waitForTimeout(300);
    const labs = await page.evaluate(() => [...document.querySelectorAll('.lbl')].map(l => l.textContent));
    ok(`step ${name} highlights its parts`, labs.some(l => want.test(l)), labs.slice(0, 8).join(' | '));
    await shot(page, 'd1280-light-' + name);
  }
  // every step: the list button, the chip over the stage, what is shown against the step's own list, highlights
  const nsteps = await page.evaluate(() => window.TS06.getSteps().length);
  let stepFails = [];
  for (let i = 0; i < nsteps; i++) {
    await page.click(`#steplist button[data-step="${i}"]`); await settle(page);
    const r = await page.evaluate(i => {
      const V = window.TS06, s = V.getSteps()[i], A = V.roots.asm, vis = new Set(s.vis);
      const bad = [];
      for (const [id, objs] of A.items) {
        let want = vis.has(id);
        if (['cheek_l', 'cheek_r', 'brow', 'top', 'trench', 'base', 'rear', 'fascia_frame'].includes(id)) want = want && V.caseOn;
        if (id === 'lead') want = want && V.wiring && V.explode < 0.05;
        if (id === 'handwire') want = vis.has('fascia') && V.wiring;       // the hand wires go with the fascia
        const shown = objs.some(o => o.visible);
        if (shown !== want) bad.push(id + (want ? ' missing' : ' extra'));
      }
      const chip = document.querySelector('#stepchip').textContent;
      const labels = document.querySelectorAll('.lbl').length;
      return { step: V.step, title: s.title, chipOk: chip.includes(s.title), bad, labels, hl: V.hlList.length, explode: V.explode, want: s.explode || 0 };
    }, i);
    const good = r.step === i && r.chipOk && !r.bad.length && Math.abs(r.explode - r.want) < 1e-6 && (r.hl === 0 || r.labels > 0);
    if (!good) stepFails.push(JSON.stringify(r));
    ok(`step ${i + 1}/${nsteps}: ${r.title}`, good, `${r.labels} labels, ${r.hl} highlights, explode ${r.explode}` + (r.bad.length ? ' visibility: ' + r.bad.join(',') : ''));
    if ([0, 1, 2, 3, 5, 6, 7, 9, 11, 12, 13, 15, 16, 17].includes(i)) {
      await page.evaluate(() => window.scrollTo(0, document.querySelector('#viewer').getBoundingClientRect().top + scrollY - 8));
      await shot(page, `d1280-light-step-${String(i + 1).padStart(2, '0')}`);
    }
  }
  // a part chip focuses one part
  await page.click(`#steplist button[data-step="${find(/U12 first/)}"]`); await settle(page);
  await page.click('#stepcard .chip[data-key="DRV:RP1"]'); await settle(page);
  const one = await page.evaluate(() => window.TS06.hlList.map(h => h.key));
  ok('a part chip highlights that part alone', one.length === 1 && one[0] === 'DRV:RP1', one.join(','));
  await shot(page, 'd1280-light-chip-RP1');

  // ---- fascia variants
  for (const v of ['F', 'R']) {
    await page.click(`#fvseg button[data-fv="${v}"]`); await page.waitForTimeout(300);
    const s = await page.evaluate(() => { const V = window.TS06; let shown = []; V.roots.asm.group.traverse(o => { if (o.userData.fv && o.visible) shown.push(o.userData.fv); }); return { fv: V.fv, shown: [...new Set(shown)] }; });
    ok(`fascia variant ${v} swaps the board`, s.fv === v && s.shown.length === 1 && s.shown[0] === v, JSON.stringify(s));
    if (v === 'R' || v === 'F') { await page.click('#deck [data-view="front"]'); await settle(page); await shot(page, `d1280-light-fascia-${v}-front`); }
  }

  // ---- board scenes
  for (const s of ['DRV', 'DISP', 'FASCIA']) {
    await page.click(`#sc-${s}`); await settle(page);
    await shot(page, `d1280-light-${s}`);
  }
  await page.click('#sc-FASCIA'); await page.click('#fvseg button[data-fv="R"]'); await settle(page);
  await page.click('#deck [data-view="front"]'); await settle(page);
  await shot(page, 'd1280-light-FASCIA-R');
  await page.click('#imgbtn'); await page.waitForTimeout(600);
  await shot(page, 'd1280-light-FASCIA-R-render');
  await page.click('#sc-DRV'); await page.waitForTimeout(600);
  await shot(page, 'd1280-light-DRV-render');
  await page.click('#modeseg button[data-mode="3d"]');
  await page.click('#sc-asm'); await settle(page);

  // ---- sections tab
  await page.click('#dt-sections');
  const nsec = await page.locator('#seclist .secbtn').count();
  await page.locator('#seclist .secbtn').nth(1).click();
  await page.waitForTimeout(500);
  const pz = page.locator('#secdetail .pz').first();
  await pz.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  const pb = await pz.boundingBox();
  const tr0 = await pz.locator('img').evaluate(i => i.style.transform);
  await page.mouse.move(pb.x + pb.width / 2, pb.y + pb.height / 2); await page.mouse.wheel(0, -400); await page.waitForTimeout(200);
  await page.mouse.down(); await page.mouse.move(pb.x + pb.width / 2 + 60, pb.y + pb.height / 2 + 30, { steps: 5 }); await page.mouse.up();
  const tr1 = await pz.locator('img').evaluate(i => i.style.transform);
  ok('sections: list and schematic pan/zoom', nsec > 0 && tr0 !== tr1, `${nsec} sections; ${tr0} -> ${tr1}`);
  await page.locator('#secdetail').scrollIntoViewIfNeeded();
  await shot(page, 'd1280-light-sections', false);
  await page.click('#sec3d'); await settle(page); await page.waitForTimeout(500);
  const sh = await page.evaluate(() => ({ n: window.TS06.hlList.length, labels: document.querySelectorAll('.lbl').length, scene: window.TS06.current }));
  ok('sections: Show in 3D highlights the parts', sh.n > 0 && sh.labels > 0, JSON.stringify(sh));
  await shot(page, 'd1280-light-section-in-3d');
  for (let i = 0; i < nsec; i++) {
    await page.locator('#seclist .secbtn').nth(i).click();
    await page.waitForFunction(() => [...document.querySelectorAll('#secdetail .pz img')].every(im => im.complete), null, { timeout: 30000 });
    const imgs = await page.evaluate(() => [...document.querySelectorAll('#secdetail .pz img')].map(im => im.naturalWidth > 0));
    await page.click('#sec3d');
    await page.waitForFunction(() => window.TS06.onscreen, null, { timeout: 30000 });
    await settle(page);
    const r = await page.evaluate(() => ({ title: document.querySelector('#secdetail h2').textContent, n: window.TS06.hlList.length, labels: document.querySelectorAll('.lbl').length, scene: window.TS06.current }));
    ok(`section ${i + 1}/${nsec}: ${r.title}`, imgs.length >= 2 && imgs.every(Boolean) && r.labels > 0, `${imgs.length} images loaded; ${r.labels} labels in ${r.scene}`);
    if (i === 2 || i === 6 || i === 11) await shot(page, `d1280-light-section-${i + 1}-3d`);
  }
  // test tab and variants tab
  await page.click('#dt-test'); await page.locator('#doc-test').scrollIntoViewIfNeeded(); await shot(page, 'd1280-light-test-tab');
  await page.click('#dt-fascia'); await page.locator('#doc-fascia').scrollIntoViewIfNeeded(); await page.waitForTimeout(500); await shot(page, 'd1280-light-fascia-tab');
  const npic = await page.locator('#fvpic option').count();
  let picsOk = 0;
  for (let i = 0; i < npic; i++) {
    await page.selectOption('#fvpic', String(i));
    await page.waitForFunction(() => document.querySelector('#fvimg').complete, null, { timeout: 30000 });
    if (await page.evaluate(() => document.querySelector('#fvimg').naturalWidth > 0)) picsOk++;
  }
  const cols = await page.evaluate(() => [...document.querySelectorAll('#fvtable thead th')].map(t => t.textContent.trim()).filter(Boolean));
  ok('fascia variants: table and composites', npic > 0 && picsOk === npic && cols.length === 4, `${cols.join(' | ')}; ${picsOk}/${npic} pictures`);
  await page.selectOption('#fvpic', '6').catch(() => {}); await page.waitForTimeout(300);
  await page.locator('#fvpane').scrollIntoViewIfNeeded(); await shot(page, 'd1280-light-fascia-tab-F');
  await shot(page, 'd1280-light-full', true);
  const sw = await page.evaluate(() => document.documentElement.scrollWidth);
  ok('desktop: no horizontal scroll', sw <= 1280, 'scrollWidth ' + sw);
  ok('desktop light: no console errors', errs.length === 0, errs.slice(0, 5).join(' || '));
  await ctx.close();
}

// ================================================================ desktop, dark
if (!ONLY_NEW) {
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900, scheme: 'dark' });
  await load(page);
  await shot(page, 'd1280-dark-overview');
  await page.click('#steplist button[data-step="5"]'); await settle(page);
  await shot(page, 'd1280-dark-step06');
  await page.click('#sc-DRV'); await settle(page);
  await page.click('#deck [data-view="isoR"]'); await settle(page);
  await shot(page, 'd1280-dark-DRV');
  await shot(page, 'd1280-dark-full', true);
  ok('desktop dark: no console errors', errs.length === 0, errs.slice(0, 5).join(' || '));
  await ctx.close();
}

// ================================================================ phone, light and dark, with a real touch drag
for (const scheme of ONLY_NEW ? [] : ['light', 'dark']) {
  const { ctx, page, errs } = await newPage({ w: 390, h: 844, scheme, touch: true, mobile: true });
  await load(page);
  await shot(page, `p390-${scheme}-top`);
  const sw = await page.evaluate(() => document.documentElement.scrollWidth);
  ok(`phone ${scheme}: no horizontal scroll at 390`, sw <= 390, 'scrollWidth ' + sw);
  if (scheme === 'light') {
    // touch drag through CDP: real touch events, so Chromium makes pointerType "touch"
    const box = await page.locator('#gl canvas').boundingBox();
    const c0 = await cam(page);
    const sy0 = await page.evaluate(() => scrollY);
    const cdp = await ctx.newCDPSession(page);
    const x = box.x + box.width / 2, y = box.y + box.height / 2;
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y, id: 1 }] });
    for (let i = 1; i <= 12; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + i * 12, y: y + i * 6, id: 1 }] }); await page.waitForTimeout(16); }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await page.waitForTimeout(900);
    const c1 = await cam(page);
    const sy1 = await page.evaluate(() => scrollY);
    const ang = Math.acos(Math.min(1, dot(dirOf(c0), dirOf(c1)))) * 180 / Math.PI;
    await page.evaluate(() => { window.TS06.controls.enableDamping = false; });   // no damping tail in software GL
    ok('touch drag orbits the camera (phone)', ang > 10, `camera turned ${ang.toFixed(1)}°; page scroll ${sy0} -> ${sy1}`);
    // a touch drag outside the canvas still scrolls the page
    const hb = await page.locator('.lede').boundingBox();
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 200, y: hb.y + 20, id: 2 }] });
    for (let i = 1; i <= 10; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 200, y: hb.y + 20 - i * 30, id: 2 }] }); await page.waitForTimeout(16); }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await page.waitForTimeout(600);
    const sy2 = await page.evaluate(() => scrollY);
    ok('touch drag outside the canvas scrolls the page', sy2 > sy1 + 50, `scrollY ${sy1} -> ${sy2}`);
    await page.evaluate(() => scrollTo(0, 0));
    // pinch? two-finger dolly
    const d0 = dist(c1.p, c1.t);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x - 30, y, id: 3 }, { x: x + 30, y, id: 4 }] });
    for (let i = 1; i <= 10; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x - 30 - i * 8, y, id: 3 }, { x: x + 30 + i * 8, y, id: 4 }] }); await page.waitForTimeout(16); }
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await page.waitForTimeout(900);
    const c2 = await cam(page);
    ok('pinch zooms (phone)', dist(c2.p, c2.t) < d0 * 0.9, `${d0.toFixed(0)} -> ${dist(c2.p, c2.t).toFixed(0)} mm`);
    await page.tap('#deck [data-view="front"]'); await settle(page);
    ok('tap on a view button (phone)', dot(dirOf(await cam(page)), [0, 0, 1]) > 0.995);
    await shot(page, 'p390-light-front');
    await page.tap('#stepnext'); await settle(page);
    await shot(page, 'p390-light-step01');
  } else {
    await page.tap('#steplist button[data-step="9"]');
    await page.waitForFunction(() => window.TS06.onscreen, null, { timeout: 30000 }); await settle(page);
    await shot(page, 'p390-dark-stepS3-model');
    await page.locator('#stepcard').scrollIntoViewIfNeeded();
    await shot(page, 'p390-dark-stepS3');
  }
  await page.locator('#stepcard').scrollIntoViewIfNeeded();
  await shot(page, `p390-${scheme}-stepcard`);
  await page.locator('#doc-sections').scrollIntoViewIfNeeded();
  await shot(page, `p390-${scheme}-sections`);
  await shot(page, `p390-${scheme}-full`, true);
  const sw2 = await page.evaluate(() => document.documentElement.scrollWidth);
  ok(`phone ${scheme}: still no horizontal scroll after use`, sw2 <= 390, 'scrollWidth ' + sw2);
  ok(`phone ${scheme}: no console errors`, errs.length === 0, errs.slice(0, 5).join(' || '));
  await ctx.close();
}

// ================================================================ front panel view + the panel ladders
// Moved 30.09.26 from A1 (TS06-FASCIA Panel Drawing) and A2 (TS06-FASCIA Reference). One check per moved
// item, so nothing is lost without a FAIL. The expected words are copied from the old pages here, not
// read back from app.js. The 3D models are not waited for: this content renders before they load.
async function openPanel(page, hash = '#panel') {
  await page.goto(`http://127.0.0.1:${PORT}/index.html${hash}`);
  await page.waitForFunction(() => document.querySelectorAll('#fp-difflist li').length > 0 && document.querySelector('#lad-a6fig svg'), null, { timeout: 120000 });
}
const txt = (page, s) => page.evaluate(s => { const e = document.querySelector(s); return e ? e.textContent.replace(/\s+/g, ' ').trim() : ''; }, s);
if (!ONLY_NEW) {
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900 });
  await openPanel(page);
  const facts = JSON.parse(fs.readFileSync(path.join(SITE, 'data', 'facts.json'), 'utf8')).boards;
  const sz = b => `${facts[b].size[0]} × ${facts[b].size[1]}`;
  ok('front panel: the tab opens (#panel)', await page.evaluate(() => !document.querySelector('#doc-panel').hidden && document.querySelector('#dt-panel').getAttribute('aria-selected') === 'true'));
  // today's board, from the build
  {
    const res = [];
    for (const [v, b] of [['R', 'TS06-FASCIA-rhythm']]) {
      await page.click(`#fp-fvseg button[data-fp="${v}"]`);
      await page.waitForFunction(() => ['#fp-front', '#fp-back'].every(s => document.querySelector(s).complete), null, { timeout: 30000 });
      const r = await page.evaluate(() => ({ imgs: ['#fp-front', '#fp-back'].map(s => document.querySelector(s).naturalWidth > 0), dl: document.querySelector('#fp-todayfacts').textContent }));
      res.push(r.imgs.every(Boolean) && r.dl.includes(sz(b)) && r.dl.includes(b));
    }
    const picker = await page.evaluate(() => [...document.querySelectorAll('#fp-fvseg button')].map(b => b.dataset.fp));
    ok('front panel: the board picker offers R only (A and W are out); R shown from the build (renders + facts)', res.every(Boolean) && picker.join() === 'R', `${res.join(',')}; picker ${picker.join()}`);
  }
  await page.locator('#fp-today').screenshot({ path: path.join(SHOTS, 'd1280-light-panel-today.png') });
  // the disagreements
  {
    const d = await page.evaluate(() => [...document.querySelectorAll('#fp-difflist li')].map(li => ({ k: li.dataset.d, mk: !!li.querySelector('.mk') })));
    ok('front panel: disagreements with today listed and marked', d.length === 9 && d.every(x => x.mk) && ['outline', 'j1', 'back', 'dial', 'silk', 'firmware', 'drv', 'routing', 'cable'].every(k => d.some(x => x.k === k)), d.map(x => x.k).join(','));
  }
  // A1: what the controls do
  {
    const t = await txt(page, '#fp-controls');
    ok('migrated A1 “What the controls do”: intro and the SUB rule', t.includes('The rotary has six fixed names, so it letters itself.') && t.includes('SUB now has one rule, and it holds everywhere:') && t.includes('the lever itself, not a drawing of one, closes the gap.'));
    ok('A1 dial explainer flagged: rev B is not in the firmware yet', (await txt(page, '#fp-fwnote')).includes('does not read A7'));
    const want = [
      ['Normal', 'not read', 'not read', 'not read', 'A safe parking position.'],
      ['Set Time', 'Hour ↔ Minute', 'not read', 'Adjusts the selected field', 'costs you the time on the clock'],
      ['Display', 'Brightness ↔ Effects', 'Transition ↔ Glitch — read only while FIELD = Effects', 'Adjusts the selected setting. Glitch runs off at the bottom of its range', 'three settings on two levers'],
      ['Ambient', 'Colon ↔ Backlight', 'not read', "Cycles that item's styles", 'not digits'],
      ['Format / Date', 'Format ↔ Date', 'Day-Month ↔ Year — read only while FIELD = Date', "Format: flips 12h/24h. Date: adjusts SUB's selection", 'a binary toggle and a multi-field value'],
      ['Info', 'not read', 'not read', 'not read', 'it is now an end stop']];
    const bad = [];
    for (let i = 0; i < 6; i++) {
      await page.click(`#fp-poslist button[data-pos="${i}"]`);
      const r = await page.evaluate(() => ({ n: document.querySelector('#fp-posname').textContent, f: document.querySelector('#fp-c-field .v').textContent, s: document.querySelector('#fp-c-sub .v').textContent, b: document.querySelector('#fp-c-btn .v').textContent, l: document.querySelector('#fp-poslede').textContent, rot: document.querySelector('#fp-knob').getAttribute('transform'), pressed: [...document.querySelectorAll('#fp-poslist .posbtn')].findIndex(b => b.getAttribute('aria-pressed') === 'true') }));
      const w = want[i];
      if (!(r.n === w[0] && r.f === w[1] && r.s === w[2] && r.b === w[3] && r.l.includes(w[4]) && r.pressed === i && r.rot === `rotate(${15 + 30 * i} 30 26)`)) bad.push(i + 1 + ':' + JSON.stringify(r));
      if (i === 2) await page.locator('#fp-dial').screenshot({ path: path.join(SHOTS, 'd1280-light-panel-dial-display.png') });
    }
    ok('migrated A1 dial explainer: all six positions, as A1 wrote them', !bad.length, bad.join(' | ').slice(0, 300));
    await page.click('#fp-poslist button[data-pos="0"]');
    ok('migrated A1 note under the panel drawing (hand-wired landing pads)', t.includes('each control is hand-wired to its landing pads'));
  }
  // A1 hardware + control scheme
  {
    const hw = await page.evaluate(() => [...document.querySelectorAll('#fp-hardware tbody tr')].map(r => [...r.cells].map(c => c.textContent.trim()).join(' ')));
    ok('migrated A1 hardware table: 8 rows', hw.length === 8 && hw[0].includes('Ø8.62 → 8.80 hole') && hw[4].includes('30.00° × 6 = 150°') && hw[7].includes('КМД1 plunger'), hw.join(' / ').slice(0, 200));
    const sc = await page.evaluate(() => [...document.querySelectorAll('#fp-scheme tbody tr')].map(r => [...r.cells].map(c => c.textContent.trim()).join(' ')));
    ok('migrated A1 control scheme rev B: 6 rows and the two changes from rev A', sc.length === 6 && sc[2].includes('Trans ↔ Glitch') && sc[4].includes('D‑M ↔ Year') && (await txt(page, '#fp-scheme')).includes('INFO and FORMAT/DATE swap'), sc.join(' / ').slice(0, 200));
  }
  // A2 §03 nets, §04 J1, §05 routing
  {
    const nets = await page.evaluate(() => [...document.querySelectorAll('#fp-nets .netrow')].map(r => [r.dataset.net, r.querySelector('.np').textContent]));
    const want = { '+5V': 'SW1.6, R5.1, R6.1, J1.1', GND: 'SW1.1, SW4.1, SW5.1, R1.2, R7.2, R8.2, J1.2', A6: 'SW1.7, J1.3', 'TAP2–TAP5': 'SW1.2–.5, R1–R5 chain', A7: 'R6.2, SW2.2, SW3.2, R6–R8 junction, J1.4', 'LEVA / LEVB': 'SW2.1↔R7.1 · SW3.1↔R8.1', D7: 'SW4.2 (−), J1.5', D8: 'SW5.2 (+), J1.6' };
    ok('migrated A2 §03 net reference: 8 nets with their pads', nets.length === 8 && nets.every(([n, p]) => want[n] === p), JSON.stringify(nets).slice(0, 200));
    const nc = await txt(page, '#fp-netcheck');
    ok('A2 §03 checked: every part it names is on today’s board', nc.startsWith('seen Current.') && !nc.includes('changed since'), nc.slice(0, 120));
    const pins = await page.evaluate(() => [...document.querySelectorAll('#fp-pinout .pin')].map(p => [...p.children].map(c => c.textContent.trim()).join(' ')));
    ok('migrated A2 §04 J1 pinout: 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8', pins.join('|') === 'PIN 1 +5V|PIN 2 GND|PIN 3 A6|PIN 4 A7|PIN 5 D7|PIN 6 D8', pins.join('|'));
    ok('A1’s JST-XH J1 order marked history: superseded', (await txt(page, '#fp-j1 .hist')).includes('History: superseded by the order above.'));
    const rn = await page.evaluate(() => [...document.querySelectorAll('#fp-routing .rnote h4')].map(h => h.textContent));
    const rc = await txt(page, '#fp-routecheck');
    ok('migrated A2 §05 routing notes: 3 notes, checked per board', rn.length === 3 && rn[0].startsWith('64 signal tracks') && rn[1].startsWith('R6 was sitting') && rn[2].startsWith('Moving it') && rc.includes(`${facts['TS06-FASCIA'].tracks} tracks, ${facts['TS06-FASCIA'].vias} vias`) && rc.includes(`(${facts['TS06-FASCIA-rhythm'].tracks} tracks`), rc.slice(0, 160));
  }
  // A1 open before Gerbers
  {
    const q = await page.evaluate(() => [...document.querySelectorAll('#fp-open .q')].map(x => ({ h: x.querySelector('h4').textContent, today: !!x.querySelector('.today .mk') })));
    ok('migrated A1 “Open before Gerbers”: 5 items, each with today’s status', q.length === 5 && q.every(x => x.today) && q[0].h.includes('twelve detents') && q[1].h.includes('bushing clear the stack') && q[4].h.includes('26.94'), q.map(x => x.h.slice(0, 24)).join(' | '));
  }
  // then and now
  {
    const rows = await page.evaluate(() => [...document.querySelectorAll('#fp-tntable tbody tr')].map(r => [...r.cells].map(c => c.textContent.replace(/\s+/g, ' ').trim())));
    const out = rows.find(r => r[1] === 'Outline') || [];
    const itf = rows.find(r => r[1] === 'Interface') || [];
    ok('migrated A1 title block + A2 header: 15 rows, each with today and a status', rows.length === 15 && rows.every(r => r.length === 5 && r[3] && r[4]), rows.length + ' rows');
    ok('176 × 52 outline labelled “history: superseded by” today’s fascia', out[2] === '176.00 × 52.00 mm' && out[4].startsWith(`history: superseded by today’s TS06-FASCIA, ${sz('TS06-FASCIA')} mm`), out[4]);
    ok('A1’s JST-XH interface labelled “history: superseded by” JST PH', itf[2] === '1 × JST-XH, 6 way' && itf[4].startsWith('history: superseded by the JST PH J1'), itf[4]);
  }
  // the drawings as they were
  {
    const h = await txt(page, '#fp-histlabel');
    ok('old drawings labelled: superseded by today’s fascia, R picked and ordered by fab/ORDER.md', h.startsWith(`History: superseded by today’s TS06-FASCIA, ${sz('TS06-FASCIA')} mm`) && h.includes('The fascia built is R') && h.includes('fab/ORDER.md') && h.includes(sz('TS06-FASCIA-wide')), h.slice(0, 200));
    const f = await page.evaluate(() => { const s = document.querySelector('#fp-a1front svg'); return { t: s.textContent, n: s.querySelectorAll('*').length, w: s.getBoundingClientRect().width }; });
    ok('migrated A1 panel drawing, front: redrawn 176 × 52 by its own code', f.t.includes('176.00') && f.t.includes('52.00') && f.t.includes('FORMAT/DATE') && f.t.includes('FIELD') && f.n > 80 && f.w > 500, `${f.n} elements, ${f.w.toFixed(0)} px wide`);
    await page.locator('#fp-history').scrollIntoViewIfNeeded();
    await page.locator('#fp-history').screenshot({ path: path.join(SHOTS, 'd1280-light-panel-history.png') });
    await page.click('#fp-a1tabs button[data-side="back"]');
    const b = await page.evaluate(() => { const s = document.querySelector('#fp-a1back svg'); return { t: s.textContent, vis: !document.querySelector('#fp-a1back').hidden && document.querySelector('#fp-a1front').hidden }; });
    ok('migrated A1 panel drawing, back (x-ray): redrawn, J1 in its old order', b.vis && b.t.includes('J1  GND +5V A6 A7 D7 D8') && b.t.includes('BACK-SIDE PLACEMENT') && b.t.includes('R6 10k') && b.t.includes('∅25.00 BODY KEEPOUT'), b.t.slice(0, 80));
    await page.locator('#fp-history').screenshot({ path: path.join(SHOTS, 'd1280-light-panel-history-back.png') });
    await page.click('#fp-a1tabs button[data-side="front"]');
    const a2 = await page.evaluate(() => { const s = document.querySelector('#fp-a2front svg'); return s ? s.textContent : ''; });
    ok('migrated A2 §01 front-face drawing (176 × 52)', a2.includes('SW1 · SR25 rotary · A6') && a2.includes('SW4/SW5 · D7/D8') && a2.includes('— FORMAT/DATE'), a2.slice(0, 60));
    ok('migrated A2 §01 front-face words', (await txt(page, '#fp-today')).includes('Every control the customer touches, laid out to scale.') && (await txt(page, '#fp-history')).includes('Front — as the customer sees it, drawn to real scale.'));
    const links = await page.evaluate(() => [...document.querySelectorAll('#doc-panel a[href*="claude.ai/artifact/"]')].map(a => a.href));
    const pv = await txt(page, '#fp-prov');
    ok('provenance: both old pages linked, their footers kept', links.some(l => l.endsWith('TUhqHXAXRTEU7tNwfTPH3L')) && links.some(l => l.endsWith('PAMS1JbcoDL8A7hXQcQgwS')) && pv.includes('drawn 2026-09-08') && pv.includes('checkmatch.py'), links.length + ' links');
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.locator('#doc-panel').screenshot({ path: path.join(SHOTS, 'd1280-light-panel.png') });
  // Circuit sections: the ladders
  await page.click('#dt-sections');
  {
    const t = await txt(page, '#ladders');
    ok('migrated A2 §02 lede and A1’s “Every resistor on the back” in Circuit', t.includes('six rotary positions and two independent levers are each read through a single MCU analog input') && t.includes('TQFP‑32 ATmega328P are ADC inputs with no digital driver'));
    const a6 = await page.evaluate(() => ({ svg: document.querySelector('#lad-a6fig svg').textContent, rows: [...document.querySelectorAll('#lad-a6table tbody tr')].map(r => [...r.cells].map(c => c.textContent.trim()).join(' ')), t: document.querySelector('#lad-a6').textContent.replace(/\s+/g, ' ') }));
    ok('migrated A1 A6 divider (diagram, codes) + A2’s A6 table', ['1023', '818', '614', '409', '205', 'R5 4k7', 'wiper'].every(s => a6.svg.includes(s)) && a6.rows.length === 6 && a6.rows[0] === '1 T1 NORMAL GND' && a6.rows[5] === '6 T6 INFO +5V' && a6.t.includes('0, 205, 409, 614, 818, 1023') && a6.t.includes('5.64 kΩ'), a6.rows.join(' / '));
    const a7 = await page.evaluate(() => ({ svg: document.querySelector('#lad-a7fig svg').textContent, codes: [...document.querySelectorAll('#lad-a7codes tbody tr')].map(r => r.cells[3].textContent.trim()), paths: [...document.querySelectorAll('#lad-a7table tbody tr')].map(r => r.cells[2].textContent.trim()), t: document.querySelector('#lad-a7').textContent.replace(/\s+/g, ' ') }));
    ok('migrated A1 A7 lever ladder (diagram, ADC 1023/682/512/409) + A2’s A7 table', ['R6 10k', 'R7 20k', 'R8 10k', 'FIELD', 'SUB', 'A7'].every(s => a7.svg.includes(s)) && a7.codes.join('/') === '1023/682/512/409' && a7.paths.join('/') === 'none — A7 ≈ +5V/R6 || R7/R6 || R8/R6 || (R7||R8)' && a7.t.includes('Worst gap is 103 codes'), a7.codes.join('/'));
    ok('migrated A1 “The two resistors that are not here”', (await txt(page, '#lad-notthere')).includes('The two 100 nF filter caps are deliberately at the main board end') && (await txt(page, '#lad-drvnote')).includes('C5 and C6'));
    ok('migrated A1 “Why the ladder earns the board”', (await txt(page, '#lad-earns')).includes('six wires and zero real GPIO'));
    const lc = await txt(page, '#lad-check');
    ok('ladders checked against today’s resistor values (build data)', lc.startsWith('Checked against today: boards A, W, R carry R1–R5 4k7, R6 10k, R7 20k, R8 10k'), lc.slice(0, 120));
    await page.locator('#ladders').scrollIntoViewIfNeeded();
    await page.locator('#ladders').screenshot({ path: path.join(SHOTS, 'd1280-light-ladders.png') });
    const i = await page.evaluate(() => [...document.querySelectorAll('#seclist .secbtn')].findIndex(b => b.id === 'sec-fascia'));
    let linked = false;
    if (i >= 0) {
      await page.locator('#seclist .secbtn').nth(i).click();
      await page.waitForSelector('#sec-ladlink');
      await page.click('#sec-ladlink button[data-goto="ladders"]'); await page.waitForTimeout(800);
      linked = await page.evaluate(() => { const r = document.querySelector('#ladders').getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; });
    }
    ok('the Fascia link section points to the ladders', i >= 0 && linked, 'section index ' + i);
  }
  const sw = await page.evaluate(() => document.documentElement.scrollWidth);
  ok('front panel desktop: no horizontal scroll, no console errors', sw <= 1280 && errs.length === 0, 'scrollWidth ' + sw + ' ' + errs.slice(0, 3).join(' || '));
  await ctx.close();
}
// the site's SVGs: the host refuses XML with a DOCTYPE
if (!ONLY_NEW) {
  const bad = [];
  const walk = d => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, f.name); if (f.isDirectory()) walk(p); else if (/\.svg$/i.test(f.name) && /<!DOCTYPE/i.test(fs.readFileSync(p, 'utf8'))) bad.push(path.relative(SITE, p)); } };
  walk(SITE);
  ok('site SVGs carry no <!DOCTYPE', bad.length === 0, bad.join(', '));
}
for (const scheme of ONLY_NEW ? [] : ['light', 'dark']) {
  const { ctx, page, errs } = await newPage({ w: 390, h: 844, scheme, touch: true, mobile: true });
  await openPanel(page);
  await page.tap('#fp-poslist button[data-pos="4"]');
  const r = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, n: document.querySelector('#fp-posname').textContent, st: Math.max(...[...document.querySelectorAll('#fp-tntable tbody td:last-child')].map(td => td.getBoundingClientRect().right)) }));
  await page.locator('#fp-dial').scrollIntoViewIfNeeded();
  await page.waitForTimeout(300); await page.screenshot({ path: path.join(SHOTS, `p390-${scheme}-panel-dial.png`) });
  await page.locator('#fp-history').scrollIntoViewIfNeeded();
  await page.waitForTimeout(300); await page.screenshot({ path: path.join(SHOTS, `p390-${scheme}-panel-history.png`) });
  await page.tap('#dt-sections');
  await page.locator('#ladders').scrollIntoViewIfNeeded();
  await page.waitForTimeout(300); await page.screenshot({ path: path.join(SHOTS, `p390-${scheme}-ladders.png`) });
  const sw2 = await page.evaluate(() => document.documentElement.scrollWidth);
  ok(`phone ${scheme}: front panel and ladders fit 390, the dial taps`, r.sw <= 390 && sw2 <= 390 && r.st <= 390 && r.n === 'Format / Date' && errs.length === 0, `scrollWidth ${r.sw}/${sw2}, status column right edge ${r.st.toFixed(0)}, ${r.n}` + (errs.length ? ' ' + errs.slice(0, 3).join(' || ') : ''));
  await ctx.close();
}

// ================================================================ populated boards and the Order view
// The boards are the GLBs and pictures of 3d/populated/ (the fascia R as ordered, with its Plates print and Divider gold),
// and the Order view reads fab/ORDER.md and the fit table. Each piece has its own check below.
if (!ONLY_WIRING) {
  const rd = f => JSON.parse(fs.readFileSync(path.join(SITE, 'data', f), 'utf8'));
  const pop = rd('populated.json'), order = rd('order.json');
  const BOARDS3 = ['TS06-DRV', 'TS06-DISP', 'TS06-FASCIA-rhythm'];

  // ---- the files the site would publish: the host's limits (15 MB a file, 256 MB a version), and the list
  {
    const files = [];
    const walk = (d, rel = '') => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { if (f.isDirectory()) walk(path.join(d, f.name), rel + f.name + '/'); else files.push({ p: rel + f.name, n: fs.statSync(path.join(d, f.name)).size }); } };
    walk(SITE);
    const total = files.reduce((a, f) => a + f.n, 0), big = files.slice().sort((a, b) => b.n - a.n)[0];
    ok('publish limits: every file 15 MB or less, the version under 256 MB', files.every(f => f.n <= 15 * 1048576) && total < 256 * 1048576 && files.length < 511,
      `${files.length} files, ${(total / 1048576).toFixed(1)} MB, largest ${big.p} ${(big.n / 1048576).toFixed(2)} MB`);
    const pf = path.join(path.dirname(SITE), 'publish-files.json');
    const list = fs.existsSync(pf) ? JSON.parse(fs.readFileSync(pf, 'utf8')) : {};
    const same = Object.keys(list).length === files.length && files.every(f => list[f.p] === f.p);
    ok('publish-files.json maps each of the site’s files to itself', same, `${Object.keys(list).length} entries`);
  }

  // ---- data written by the build
  ok('populated data: three boards, no footprint without a model, the Divider gold', BOARDS3.every(b => pop.boards[b] && pop.boards[b].footprints.missing === 0 && pop.boards[b].footprints.with_model > 10) && pop.gold === 'divider',
    BOARDS3.map(b => `${b.replace('TS06-', '')} ${pop.boards[b].footprints.with_model}+${pop.boards[b].footprints.allowlisted}`).join(', ') + ', gold ' + pop.gold);
  ok('populated GLBs published as glTF JSON, each under 15 MB', BOARDS3.every(b => { const f = path.join(SITE, pop.boards[b].published); return fs.existsSync(f) && fs.statSync(f).size === pop.boards[b].published_bytes && pop.boards[b].published_bytes <= 15 * 1048576; }),
    BOARDS3.map(b => `${b.replace('TS06-', '')} ${(pop.boards[b].glb_bytes / 1048576).toFixed(1)} MB GLB -> ${(pop.boards[b].published_bytes / 1048576).toFixed(2)} MB`).join(', '));

  const reqs = [];
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900 });
  page.on('request', r => reqs.push(r.url()));
  await load(page, '', true);

  // ---- the GLBs loaded, with the parts in them, and no stand-in bodies on top
  const g = await page.evaluate(() => {
    const V = window.TS06, out = { fv: V.fv, boards: {} };
    for (const [k, refs] of [['DRV', ['U1', 'U2', 'U13', 'L1', 'F1', 'XS11']], ['DISP', ['V1', 'V5', 'V7', 'HL1', 'XP11']], ['FR', ['SW1', 'SW2', 'SW4', 'J1', 'R1']]]) {
      const gl = V.gltf[k], js = gl.parser.json, names = new Set();
      let meshes = 0;
      gl.scene.traverse(o => { if (o.name) names.add(o.name); if (o.isMesh) meshes++; });
      const gold = (js.materials || []).filter(m => { const p = m.pbrMetallicRoughness || {}, c = p.baseColorFactor || [0, 0, 0]; return (p.metallicFactor === undefined || p.metallicFactor === 1) && (p.roughnessFactor || 1) <= 0.5 && c[0] > 0.6 && c[1] > 0.5 && c[2] < 0.2; }).length;
      out.boards[k] = { nodes: js.nodes.length, meshes, have: refs.filter(r => names.has(r)), want: refs, gold };
    }
    const A = V.roots.asm, items = id => (A.items.get(id) || []);
    const named = (id, re) => items(id).filter(o => re.test(o.name) && o.userData.item === undefined).length;
    out.items = { chipU2: items('chip:U2').map(o => o.name + ':' + (o.userData.item || '')), nano: items('nano').map(o => o.name), rtc: items('rtc').map(o => o.name),
      in12: named('in12', /^V\d+$/), in15: named('in15', /^V\d+$/), in17: named('in17', /^V\d+$/), ins1: named('ins1', /^V\d+$/), leds: named('leds', /^HL\d+$/),
      fascia: named('fascia', /^(SW\d|J1)$/), chipsReal: ['U2', 'U3', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10', 'U11', 'U12', 'U15', 'U16', 'U17'].filter(r => items('chip:' + r).length === 1 && items('chip:' + r)[0].name === r).length };
    return out;
  });
  ok('GLBs loaded: DRV, DISP and the fascia R carry their parts (nodes by reference)', Object.values(g.boards).every(b => b.have.length === b.want.length && b.meshes > 30),
    Object.entries(g.boards).map(([k, b]) => `${k} ${b.nodes} nodes, ${b.meshes} meshes, ${b.have.length}/${b.want.length} refs`).join('; '));
  ok('GLBs: the fascia R carries its gold as a metallic gold material', g.boards.FR.gold >= 1, `${g.boards.FR.gold} gold material(s) in the R GLB`);
  ok('populated boards draw no stand-in bodies: the stepper uses the parts’ own nodes', g.items.chipsReal === 13 && g.items.nano.join() === 'U1' && g.items.rtc.join() === 'U13' && g.items.in12 === 4 && g.items.in15 === 2 && g.items.in17 === 2 && g.items.ins1 === 2 && g.items.leds === 9 && g.items.fascia === 6,
    JSON.stringify(g.items).slice(0, 220));
  ok('the fascia shown first is R, the board that is ordered', g.fv === 'R', 'variant ' + g.fv);

  // ---- the pictures of the populated boards (the page's own picture mode, and every file)
  const pics = await page.evaluate(async list => {
    const res = [];
    for (const p of list) {
      const im = new Image();
      await new Promise(r => { im.onload = im.onerror = r; im.src = p; });
      res.push({ p, w: im.naturalWidth, h: im.naturalHeight });
    }
    return res;
  }, pop.pictures);
  const sizes = pop.pictures.map(p => fs.statSync(path.join(SITE, p)).size);
  ok('populated pictures: all ' + pop.pictures.length + ' load, at most 2400 px wide and under 3 MB', pics.length === 11 && pics.every(x => x.w >= 700 && x.w <= 2400) && sizes.every(n => n < 3 * 1048576),
    pics.map(x => `${x.p.replace('img/', '').replace('.png', '')} ${x.w}x${x.h}`).join(', ').slice(0, 300));
  const px = await page.evaluate(async src => {
    const im = new Image();
    await new Promise(r => { im.onload = im.onerror = r; im.src = src; });
    const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
    const x = c.getContext('2d'); x.drawImage(im, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    let gold = 0, white = 0, opaque = 0;
    for (let i = 0; i < d.length; i += 4) {
      if (d[i + 3] < 200) continue;
      opaque++;
      if (d[i] > 180 && d[i + 1] > 140 && d[i + 2] < 90 && d[i] - d[i + 2] > 100) gold++;
      else if (d[i] > 235 && d[i + 1] > 235 && d[i + 2] > 235) white++;
    }
    return { gold, white, opaque };
  }, 'img/TS06-FASCIA-rhythm-top.png');
  ok('the fascia picture shows the Divider gold and the Plates print', px.gold > 8000 && px.white > 6000, `${px.gold} gold pixels, ${px.white} white pixels of ${px.opaque}`);
  const mode = {};
  for (const [scene, key] of [['DRV', 'TS06-DRV'], ['DISP', 'TS06-DISP'], ['FASCIA', 'TS06-FASCIA-rhythm']]) {
    await page.click(`#scenes [data-scene="${scene}"]`);
    await page.click('#modeseg [data-mode="img"]');
    await page.waitForFunction(() => document.querySelector('#shotimg').complete && document.querySelector('#shotimg').naturalWidth > 0);
    mode[scene] = await page.evaluate(() => { const i = document.querySelector('#shotimg'); return { src: i.getAttribute('src'), alt: i.alt, w: i.naturalWidth, n: document.querySelectorAll('#shotnav button').length }; });
  }
  ok('picture mode shows the populated renders of each board', mode.DRV.src === 'img/TS06-DRV-iso.png' && mode.DISP.src === 'img/TS06-DISP-iso.png' && mode.FASCIA.src === 'img/TS06-FASCIA-rhythm-iso.png' && Object.values(mode).every(m => /populated/.test(m.alt) && m.w > 700 && m.n === 3),
    Object.entries(mode).map(([k, m]) => `${k}: ${m.src} (${m.w} px)`).join('; '));
  await page.click('#scenes [data-scene="asm"]');
  await page.click('#modeseg [data-mode="img"]');
  const asmShots = await page.evaluate(() => [...document.querySelectorAll('#shotnav button')].map(b => b.textContent));
  await page.click('#shotnav button:last-child');
  await page.waitForFunction(() => document.querySelector('#shotimg').complete && document.querySelector('#shotimg').naturalWidth > 0);
  const stk = await page.evaluate(() => ({ src: document.querySelector('#shotimg').getAttribute('src'), w: document.querySelector('#shotimg').naturalWidth }));
  ok('the case pictures include the populated stack, front and angled', asmShots.includes('Populated, front') && asmShots.includes('Populated, angled') && stk.src === 'img/stack-iso.png' && stk.w > 700, asmShots.join(' | ') + '; ' + stk.src);
  await page.click('#modeseg [data-mode="3d"]');

  // ---- the 3D view with the populated boards (screenshots; the gold in the fascia)
  await page.click('#scenes [data-scene="asm"]');
  await page.click('#deck [data-view="isoL"]'); await settle(page);
  await shot(page, 'd1280-light-populated-assembly');
  await page.click('#scenes [data-scene="DRV"]'); await page.click('#sidetabs [data-side="facts"]').catch(() => {});
  await page.click('#deck [data-view="isoL"]').catch(() => {}); await settle(page);
  await shot(page, 'd1280-light-populated-driver');
  await page.click('#scenes [data-scene="DISP"]'); await settle(page);
  await shot(page, 'd1280-light-populated-display');
  await page.click('#scenes [data-scene="FASCIA"]'); await settle(page);
  await page.click('#deck [data-view="front"]').catch(() => {}); await settle(page);
  await shot(page, 'd1280-light-populated-fascia-gold');
  const png = await page.locator('#gl canvas').screenshot();
  const gp = await page.evaluate(async b64 => {
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const bm = await createImageBitmap(new Blob([bin], { type: 'image/png' }));
    const c = document.createElement('canvas'); c.width = bm.width; c.height = bm.height;
    const x = c.getContext('2d'); x.drawImage(bm, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    let gold = 0, n = 0;
    for (let i = 0; i < d.length; i += 4) { n++; if (d[i] > 120 && d[i] - d[i + 2] > 60 && d[i + 1] > 90) gold++; }
    return { gold, n };
  }, png.toString('base64'));
  ok('the 3D view of the fascia R shows the gold', gp.gold > 2000, `${gp.gold} gold-coloured pixels of ${gp.n} in the canvas`);

  // ---- the glow switch. The numerals glowed in the stand-in tubes before the boards were drawn populated; they come back behind a
  // switch in the 3D view: off at load (the plain glass), on shows the glow, off hides it again. It is an illustration, and says so
  // in one line beside the switch. Checked on the desktop and on the phone, light and dark: the scene graph (the numeral planes, the
  // tubes' glass), the canvas (what changes on screen) and the layout.
  const glowState = pg => pg.evaluate(() => {
    const V = window.TS06, deep = o => { for (let n = o; n; n = n.parent) if (!n.visible) return false; return true; };
    const root = V.roots[V.current].group;
    let planes = 0, shown = 0, cores = 0, coresShown = 0, glass = 0, lit = 0;
    root.traverse(o => {
      if (o.userData.glowPlane) { planes++; if (deep(o)) shown++; }
      if (o.userData.glowCore) { cores++; if (deep(o)) coresShown++; }
      if (o.userData.glassPlain) { glass++; if (o.material !== o.userData.glassPlain) lit++; }
    });
    const row = document.querySelector('#glowdeck'), sw = document.querySelector('#glowon');
    return { planes, shown, cores, coresShown, glass, lit, checked: sw.checked, row: !row.hidden, glow: V.glow };
  });
  const canvasPng = async pg => (await pg.locator('#gl canvas').screenshot()).toString('base64');
  const pngDiff = (pg, a, b) => pg.evaluate(async ([a, b]) => {
    const px = async s => {
      const bm = await createImageBitmap(new Blob([Uint8Array.from(atob(s), c => c.charCodeAt(0))], { type: 'image/png' }));
      const c = document.createElement('canvas'); c.width = bm.width; c.height = bm.height;
      const x = c.getContext('2d'); x.drawImage(bm, 0, 0);
      return x.getImageData(0, 0, c.width, c.height).data;
    };
    const A = await px(a), B = await px(b);
    let changed = 0, warm = 0;
    for (let i = 0; i < A.length; i += 4) {
      const d = Math.abs(A[i] - B[i]) + Math.abs(A[i + 1] - B[i + 1]) + Math.abs(A[i + 2] - B[i + 2]);
      if (d > 45) { changed++; if (B[i] > B[i + 2] + 25 && B[i] >= B[i + 1]) warm++; }
    }
    return { changed, warm, total: A.length / 4 };
  }, [a, b]);
  for (const [label, w, h, phone] of [['d1280', 1280, 900, false], ['p390', 390, 844, true]]) for (const scheme of ['light', 'dark']) {
    const tag = `${label}-${scheme}`, human = `${phone ? 'phone 390' : 'desktop 1280'} ${scheme}`;
    const { ctx: cg, page: pg, errs: eg } = await newPage({ w, h, scheme, touch: phone, mobile: phone });
    await load(pg, '', true);
    // at load: the switch is there, off, with its line of text, and nothing glows
    const s0 = await glowState(pg);
    const note = await pg.evaluate(() => { const n = document.querySelector('#glownote'), sw = document.querySelector('#glowon'); return { text: n.textContent.trim(), described: sw.getAttribute('aria-describedby'), type: sw.type, label: document.querySelector('label[for="glowon"]').textContent.trim() }; });
    ok(`glow switch (${human}): there, off at load, one line says the glow is an illustration`, s0.row && !s0.checked && !s0.glow && s0.shown === 0 && s0.coresShown === 0 && s0.lit === 0 && note.type === 'checkbox' && note.described === 'glownote' && /illustration/i.test(note.text) && note.text.length < 140 && /glow/i.test(note.label),
      `row ${s0.row}, checked ${s0.checked}, ${s0.shown} numerals and ${s0.coresShown} lamp cores shown, ${s0.lit} glass meshes lit; "${note.text}"`);
    await pg.click('#scenes [data-scene="DISP"]'); await settle(pg);
    await pg.click(`#deck [data-view="${phone ? 'front' : 'isoL'}"]`); await settle(pg);
    await shot(pg, `${tag}-glow-off-display`);
    const off1 = await canvasPng(pg);
    const lay = async () => pg.evaluate(() => {
      const r = e => { const b = document.querySelector(e).getBoundingClientRect(); return { l: b.left, r: b.right, t: b.top, b: b.bottom }; };
      return { sw: document.documentElement.scrollWidth, tog: r('label[for="glowon"]'), note: r('#glownote'), vw: innerWidth };
    });
    // on
    await pg.click('label[for="glowon"]'); await settle(pg);
    const s1 = await glowState(pg), l1 = await lay();
    await shot(pg, `${tag}-glow-on-display`);
    const on = await canvasPng(pg);
    const dOn = await pngDiff(pg, off1, on);
    ok(`glow switch (${human}): on, the eight numerals and the two colon lamps show in the display and their glass is warm; the picture changes`, s1.checked && s1.glow && s1.planes === 8 && s1.shown === 8 && s1.cores === 2 && s1.coresShown === 2 && s1.glass >= 10 && s1.lit === s1.glass && dOn.changed > dOn.total * 0.01 && dOn.warm > 300,
      `${s1.shown} of ${s1.planes} numerals and ${s1.coresShown} of ${s1.cores} lamp cores shown, ${s1.lit} of ${s1.glass} glass meshes lit; ${dOn.changed} px changed (${(100 * dOn.changed / dOn.total).toFixed(1)} %), ${dOn.warm} warm`);
    if (phone) ok(`glow switch (${human}): the switch and its line fit the 390 px screen, no sideways scroll`, l1.sw <= 390 && l1.tog.l >= 0 && l1.tog.r <= 390 && l1.note.l >= 0 && l1.note.r <= 390 && l1.note.b > l1.note.t,
      `scrollWidth ${l1.sw}, switch ${l1.tog.l.toFixed(0)}-${l1.tog.r.toFixed(0)}, line ${l1.note.l.toFixed(0)}-${l1.note.r.toFixed(0)}`);
    // off again: the glow is gone and the picture is the plain one
    await pg.click('label[for="glowon"]'); await settle(pg);
    const s2 = await glowState(pg);
    const off2 = await canvasPng(pg);
    const dBack = await pngDiff(pg, off1, off2);
    ok(`glow switch (${human}): off again, the numerals and the lamp cores are hidden and the glass is plain as before`, !s2.checked && !s2.glow && s2.shown === 0 && s2.coresShown === 0 && s2.lit === 0 && dBack.changed < dBack.total * 0.002,
      `${s2.shown} numerals and ${s2.coresShown} lamp cores shown, ${s2.lit} lit; ${dBack.changed} px differ from the first off picture`);
    // the assembly shows the same glow; the boards without tubes do not offer the switch
    if (!phone) {
      await pg.click('#scenes [data-scene="asm"]'); await settle(pg);
      const a0 = await glowState(pg);
      await pg.click('label[for="glowon"]'); await settle(pg);
      const a1 = await glowState(pg);
      await pg.click('#scenes [data-scene="DRV"]'); await settle(pg);
      const rowDrv = (await glowState(pg)).row;
      await pg.click('#scenes [data-scene="FASCIA"]'); await settle(pg);
      const rowFas = (await glowState(pg)).row;
      await pg.click('#scenes [data-scene="DISP"]'); await settle(pg);
      const d1 = await glowState(pg);
      ok(`glow switch (${human}): offered with the tubes (assembly, display) and not on the driver or the fascia; one setting for all`, a0.row && a0.shown === 0 && a0.coresShown === 0 && a1.shown === 8 && a1.coresShown === 2 && a1.checked && !rowDrv && !rowFas && d1.row && d1.checked && d1.shown === 8,
        `assembly ${a0.shown} -> ${a1.shown} numerals, ${a1.coresShown} lamp cores; driver row ${rowDrv}, fascia row ${rowFas}; display ${d1.shown} numerals, checked ${d1.checked}`);
      await pg.click('#scenes [data-scene="asm"]'); await pg.click('#deck [data-view="front"]'); await settle(pg);
      await shot(pg, `${tag}-glow-on-assembly`);
    }
    ok(`glow switch (${human}): no console errors, nothing leaves the machine`, eg.length === 0, eg.slice(0, 3).join(' | '));
    await cg.close();
  }

  // ---- the Order view
  await page.goto(`http://127.0.0.1:${PORT}/index.html#order`);
  await page.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 240000 });
  await page.waitForTimeout(800);
  const o = await page.evaluate(() => {
    const t = s => [...document.querySelectorAll(s)];
    const cells = r => [...r.children].map(c => c.textContent.replace(/\s+/g, ' ').trim());
    return {
      open: !document.querySelector('#doc-order').hidden && document.querySelector('#dt-order').getAttribute('aria-selected') === 'true',
      boards: t('#order-boards .ob').map(b => { const m = {}; b.querySelectorAll('dt').forEach(dt => { m[dt.textContent] = dt.nextElementSibling.textContent.replace(/\s+/g, ' ').trim(); }); m.name = b.querySelector('h3').textContent; m.img = b.querySelector('img').getAttribute('src'); m.link = b.querySelector('dd a') && b.querySelector('dd a').getAttribute('href'); return m; }),
      dfmHead: cells(document.querySelector('#order-dfm-table thead tr')), dfm: t('#order-dfm-table tbody tr').map(cells),
      fit: t('#order-fit-table tbody tr').map(r => ({ st: r.children[0].textContent.trim(), where: r.children[1].textContent.replace(/\s+/g, ' ').trim(), plain: r.children[2].textContent.trim(), margin: r.children[3].textContent.trim() })),
      pills: t('#doc-order .olede .pill').map(p => p.textContent.trim()),
      open: t('#order-open li').map(l => l.textContent.replace(/\s+/g, ' ').trim()),
      proto: t('#order-proto li').length,
      zips: t('#order-zips tbody tr').map(r => ({ cells: cells(r), href: r.querySelector('a').getAttribute('href'), text: r.querySelector('a').textContent.trim() })),
      own: document.querySelector('#order-ownhand').textContent.replace(/\s+/g, ' '),
      embed: document.querySelectorAll('#doc-order iframe, #doc-order embed, #doc-order object, #doc-order a[download]').length,
      sw: document.documentElement.scrollWidth,
    };
  });
  await page.locator('#doc-order').scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await shot(page, 'd1280-light-order', true);
  ok('Order: the tab opens from #order', o.open);
  ok('Order: per board, size, layers, thickness, finish, colour and quantity 10', o.boards.length === 3 && o.boards.every(b => b.Quantity === '10' && b.Layers === '2' && b.Finish === 'ENIG' && /^\d+\.\d x \d+\.\d mm$/.test(b.Size) && /^mask black/.test(b.Colour) && /silk white/.test(b.Colour) && /all PASS/.test(b['DFM check']))
    && o.boards.map(b => b.Thickness.slice(0, 6)).join('|') === '1.6 mm|1.6 mm|2.0 mm' && o.boards.map(b => b.Size).join('|') === '191.4 x 44.0 mm|191.4 x 100.0 mm|191.4 x 40.0 mm',
    o.boards.map(b => `${b.name.split(' ')[0]} ${b.Size}, ${b.Thickness.slice(0, 6)}, qty ${b.Quantity}`).join('; '));
  ok('Order: each board shows its populated picture', o.boards.map(b => b.img).join() === 'img/TS06-DISP-top.png,img/TS06-DRV-top.png,img/TS06-FASCIA-rhythm-top.png', o.boards.map(b => b.img).join(', '));
  ok('Order: the DFM table, 9 rules by 3 boards, every cell filled', o.dfmHead.length === 4 && o.dfmHead.slice(1).join() === 'TS06-DISP,TS06-DRV,Fascia R' && o.dfm.length === 9 && o.dfm.every(r => r.length === 4 && r.every(Boolean)),
    o.dfm.map(r => r[0].replace(/ \(.*/, '')).join(', ').slice(0, 200));
  const failN = o.fit.filter(r => r.st === 'FAIL').length, tightN = o.fit.filter(r => r.st === 'TIGHT').length;
  ok('Order: the fit table lists every TIGHT and FAIL row, each in plain words', o.fit.length === order.fit.rows.length && failN === (order.fit.tally.FAIL || 0) && tightN === order.fit.tally.TIGHT && o.fit.every(r => r.plain.length > 60 && /\d/.test(r.margin) && r.where.length > 10)
    && o.pills.join(' ') === `${order.fit.tally.PASS} PASS ${order.fit.tally.TIGHT} TIGHT ${order.fit.tally.FAIL || 0} FAIL`,
    `${tightN} TIGHT, ${failN} FAIL; ` + o.pills.join(', '));
  // the ИН-17's measured length (19.72 mm, the owner's bench caliper, 2026-10-02) took the one FAIL out of the fit table: its front row is a PASS and the tube's open item is the pip
  const fitAll = JSON.parse(fs.readFileSync(path.join(REPO, '3d', 'populated', 'fit-table.json'), 'utf8')).rows;
  const front17 = fitAll.find(r => /^ИН-17 glass front/.test(r.part));
  ok('Order: no FAIL row left; the ИН-17 front row is a PASS since its length was measured (19.72 mm)', (order.fit.tally.FAIL || 0) === 0 && failN === 0 && !!front17 && front17.status === 'PASS' && /19\.72/.test(front17.note), front17 ? `${front17.status} ${front17.margin}` : 'no ИН-17 front row');
  ok('Order: the open items before ordering, and what the prototype closes', o.open.length === order.open.length && o.open.length === 6 && /Which fascia/.test(o.open[0]) && /Which gold/.test(o.open[1]) && o.proto === order.prototype.length && o.proto >= 5, `${o.open.length} items, ${o.proto} for the prototype`);
  // the fascia zip is the one with the control holes opened (fab/HOLES-VARIANT.md, picked 2026-10-02): one row in the open list, naming the zip and the margin, backed by the fit table and the file
  const hv = await page.evaluate(() => [...document.querySelectorAll('#order-open li[data-open="holes"]')].map(l => ({ text: l.textContent.replace(/\s+/g, ' ').trim(), pill: l.querySelector('.pill').textContent.trim(), idx: [...l.parentNode.children].indexOf(l) })));
  const fitJ = JSON.parse(fs.readFileSync(path.join(REPO, '3d', 'populated', 'fit-table.json'), 'utf8'));
  const hzip = 'fab/TS06-FASCIA-R-revA-divider-holes04-fab.zip';
  ok('Order: the open list has the fascia-holes row (picked), with the ordered zip and 0.29 mm a side',
    hv.length === 1 && hv[0].idx === 2 && hv[0].pill === 'does not hold the order' && hv[0].text.includes('Fascia holes: opened by 0.4 mm (picked).')
    && hv[0].text.includes(hzip) && hv[0].text.includes('0.29 mm a side') && order.open[2].id === 'holes'
    && fs.existsSync(path.join(REPO, hzip)) && fs.statSync(path.join(REPO, hzip)).size > 10000
    && fitJ.rows.filter(r => r.what === 'hole').length === 3 && fitJ.rows.filter(r => r.what === 'hole').every(r => r.margin === 0.29)
    && fitJ.holes_committed.rows.length === 3 && fitJ.holes_committed.rows.every(r => r.margin === 0.09)
    && order.boards.some(b => b.zip === hzip) && !order.boards.some(b => /notordered/.test(b.zip)),
    hv.length ? hv[0].text.slice(0, 150) : 'no row');
  const repoFab = f => fs.statSync(path.join(REPO, f)).size;
  ok('Order: the three fab zips are linked on GitHub under pcb/kicad-boards, by repo path, not embedded',
    o.zips.length === 3 && o.zips.every(z => z.href === 'https://github.com/BobStolb/TERMINAL-06-firmware/blob/pcb/kicad-boards/' + z.text && /^fab\/.*-fab\.zip$/.test(z.text) && fs.existsSync(path.join(REPO, z.text)))
    && o.zips.every(z => { const kb = Math.round(repoFab(z.text) / 1024); return z.cells[2] === kb + ' kB'; }) && o.embed === 0 && !reqs.some(u => /\.zip(\?|$)/.test(u)),
    o.zips.map(z => z.text + ' ' + z.cells[2]).join('; '));
  ok('Order: the line that placing the order is the owner’s own hand', /Placing the order is the owner’s own hand|Placing the order is the owner's own hand/.test(o.own), o.own.slice(0, 120));
  ok('Order desktop: no horizontal scroll, no console errors', o.sw <= 1280 && errs.length === 0, 'scrollWidth ' + o.sw + ' ' + errs.slice(0, 3).join(' || '));
  await ctx.close();

  for (const scheme of ['light', 'dark']) {
    const { ctx: c2, page: p2, errs: e2 } = await newPage({ w: 390, h: 844, scheme, touch: true, mobile: true });
    await load(p2, '#order', true);
    const r = await p2.evaluate(() => ({ sw: document.documentElement.scrollWidth, rows: document.querySelectorAll('#order-fit-table tbody tr').length, boards: document.querySelectorAll('#order-boards .ob').length,
      right: Math.max(...[...document.querySelectorAll('#order-boards .ob')].map(b => b.getBoundingClientRect().right)) }));
    await p2.locator('#order-boards').scrollIntoViewIfNeeded();
    await p2.waitForTimeout(300); await shot(p2, `p390-${scheme}-order`);
    ok(`Order phone ${scheme}: fits 390, three boards stacked, no console errors`, r.sw <= 390 && r.right <= 390 && r.boards === 3 && r.rows === order.fit.rows.length && e2.length === 0, `scrollWidth ${r.sw}, card right edge ${r.right.toFixed(0)} ` + e2.slice(0, 3).join(' || '));
    await c2.close();
  }
}


// ================================================================ the wiring: the lead, the hand wiring, the Wiring switch, the fascia selector
// The lead is six wires and a housing at each end; its length is counted from the drawn wires; no wire point may lie inside a board, a
// standoff or the case's walls (a ray cast from the point through the case's closed shells: an odd number of crossings is inside).
{
  const hw = JSON.parse(fs.readFileSync(path.join(SITE, 'data', 'handwire.json'), 'utf8'));
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900 });
  await load(page, '', true);
  const sel = await page.evaluate(() => ({ btns: [...document.querySelectorAll('#fvseg button')].map(b => b.dataset.fv + ':' + b.getAttribute('aria-pressed')), fv: window.TS06.fv, hidden: document.querySelector('#fvseg').hidden }));
  ok('fascia selector: exactly R and F, R the default and pressed', sel.btns.join() === 'R:true,F:false' && sel.fv === 'R' && !sel.hidden, sel.btns.join(' '));
  // the lead, for both fascias of the selector
  const L = await page.evaluate(() => {
    const V = window.TS06, out = {};
    for (const [v, l] of Object.entries(V.lead || {})) out[v] = { n: l.wires.length, housings: l.housings.map(h => h.end), len: l.length, wl: l.wires.map(w => w.length), nets: l.wires.map(w => w.net + ' ' + w.colour).join(', '), taut: l.taut, loop: l.loopDepth };
    return out;
  });
  const vs = Object.keys(L);
  ok('the lead exists for R and F only', vs.sort().join() === 'F,R', vs.join());
  for (const v of ['R', 'F']) {
    const l = L[v];
    ok(`lead ${v}: six wires, a housing at each end, pins 1-6 +5V GND A6 A7 D7 D8 in red black yellow green blue white`,
      l.n === 6 && l.housings.length === 2 && l.housings.join() === 'TS06-DRV J1,fascia J1' && l.nets === '+5V red, GND black, A6 yellow, A7 green, D7 blue, D8 white', l.nets + '; ' + l.housings.join(' + '));
    const lo = Math.min(...l.wl), hi = Math.max(...l.wl);
    ok(`lead ${v}: its length is within 180-200 mm (centre line ${l.len.toFixed(1)} mm, wires ${lo.toFixed(1)}-${hi.toFixed(1)} mm; the shortest way across is ${l.taut} mm)`, l.len >= 180 && l.len <= 200 && lo >= 180 && hi <= 200 && l.taut < lo,
      `centre ${l.len.toFixed(2)}, wires ${l.wl.map(x => x.toFixed(1)).join(' / ')}`);
  }
  // no wire point inside a board's box, a standoff or the case's walls
  for (const v of ['R', 'F']) {
    await page.click(`#fvseg button[data-fv="${v}"]`); await page.waitForTimeout(300);
    const r = await page.evaluate(v => {
      const V = window.TS06, f = V.frame(), T = V.THREE, M = V.model(), l = V.lead[v], fv = M.fascia_variants[v];
      V.scene.updateMatrixWorld(true);
      const margin = 0.45;                                   // a wire's own radius
      const boxes = [['TS06-DRV', 0, f.BOARD_W, f.DRV_BOT_Y, f.DRV_TOP_Y, -f.Z_DRV_B, -f.Z_DRV_F], ['TS06-DISP', 0, f.BOARD_W, f.DISP_BOT_Y, f.DISP_TOP_Y, -f.Z_DISP_B, -f.Z_DISP_F]];
      const inv = V.boardMatrix('FASCIA', v).clone().invert(), HB = -0.045;
      const res = { pts: 0, board: {}, fascia: 0, standoff: 0, wall: 0, ctl: null, minFloor: 9e9 };
      const A = V.roots.asm, rc = new T.Raycaster(), up = new T.Vector3(0, 1, 0);
      rc.far = 400;
      const inCase = p => { rc.set(p, up); return rc.intersectObjects(A.caseMeshes, false).length % 2 === 1; };
      res.ctl = [inCase(new T.Vector3(-3.5, 50, -20)), inCase(new T.Vector3(96, 50, -20))];      // a point in the left cheek, one in the air
      for (const w of l.wires) w.pts.forEach((q, i) => {
        const p = new T.Vector3(...q);
        res.pts++;
        res.minFloor = Math.min(res.minFloor, q[1] - f.Y_FLOOR);
        for (const b of boxes) if (q[0] > b[1] - margin && q[0] < b[2] + margin && q[1] > b[3] - margin && q[1] < b[4] + margin && q[2] > b[5] - margin && q[2] < b[6] + margin) res.board[b[0]] = (res.board[b[0]] || 0) + 1;
        const n = p.clone().applyMatrix4(inv);
        if (n.x > -margin && n.x < fv.W + margin && n.z > -margin && n.z < fv.H + margin && n.y > HB - margin && n.y < HB + 2.0 + margin) res.fascia++;
        for (const [X, Y] of M.standoffs) if (Math.hypot(q[0] - X, q[1] - Y) < 3.2 + margin && q[2] > -f.Z_DRV_F - margin && q[2] < -f.Z_DISP_F + margin) res.standoff++;
        if (i % 3 === 0 && inCase(p)) res.wall++;
      });
      return res;
    }, v);
    ok(`lead ${v}: no wire point inside TS06-DRV, TS06-DISP or the fascia board's box, or a standoff (a wire's radius kept clear)`, Object.keys(r.board).length === 0 && r.fascia === 0 && r.standoff === 0, `${r.pts} points; boards ${JSON.stringify(r.board)}, fascia ${r.fascia}, standoffs ${r.standoff}`);
    ok(`lead ${v}: no wire point inside the case's walls (the check itself: a cheek point reads ${r.ctl[0]}, a point in the air ${r.ctl[1]}); the wires keep above the floor`, r.ctl[0] === true && r.ctl[1] === false && r.wall === 0 && r.minFloor > 0, `${r.wall} points inside of ${Math.ceil(r.pts / 3)} tested; lowest wire centre ${r.minFloor.toFixed(2)} mm over the floor`);
  }
  await page.click('#fvseg button[data-fv="R"]'); await page.waitForTimeout(300);
  // the hand wiring: wires from lugs to pads; clearance data of the build
  {
    const R = hw.boards['TS06-FASCIA-rhythm'].controls, A = hw.boards['TS06-FASCIA'].controls;
    const nR = Object.values(R).reduce((a, c) => a + c.wires.length, 0);
    const clr = Object.values(R).map(c => c.clearance);
    ok('hand wiring R: 15 wires from the lugs of the control models (7 for the dial, 2 for each lever and button), none touching a body, a lug of another wire, or another wire',
      nR === 15 && Object.values(R).every(c => c.model === 'lugs') && R.SW1.lugs.length === 14 && ['SW2', 'SW3', 'SW4', 'SW5'].every(k => R[k].lugs.length === 3) && clr.every(c => c['wire-wire'] > 0 && c['wire-lug'] > 0 && c['wire-body'] > 0),
      `dial ${R.SW1.lugs.length} lugs, levers and buttons ${R.SW2.lugs.length} each; least gaps ${Math.min(...clr.map(c => c['wire-wire']))} / ${Math.min(...clr.map(c => c['wire-lug']))} / ${Math.min(...clr.map(c => c['wire-body']))} mm`);
    ok('hand wiring F (the stand-in A board): the models there have no lugs, so each wire starts on the body’s back face',
      Object.values(A).every(c => c.model === 'standin' && c.wires.length >= 2) && Object.values(A).reduce((a, c) => a + c.wires.length, 0) === 15, `${Object.values(A).map(c => c.model).join(',')}`);
    const ends = Object.entries(R).every(([ref, c]) => c.wires.every(w => { const pad = c.pads[w.pad]; const e = w.pts[w.pts.length - 1]; return pad && Math.hypot(e[0] - pad[0], e[1] - pad[1]) < 0.05 && pad[2] === w.net && e[2] < 0.6; }));
    ok('hand wiring R: every wire ends on its landing pad, and its net is the pad’s net in the board file', ends, 'checked against pad positions and nets');
    // the dressing: no two wires cross or touch (recomputed here from the points, exact segment to segment), one bend radius, wires land flat
    {
      const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], dotp = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
      const segSeg = (p1, q1, p2, q2) => {                     // closest distance of two 3D segments (Ericson)
        const d1 = sub(q1, p1), d2 = sub(q2, p2), r = sub(p1, p2), a = dotp(d1, d1), e = dotp(d2, d2), f = dotp(d2, r);
        let s, t;
        if (a < 1e-12 && e < 1e-12) { s = t = 0; }
        else if (a < 1e-12) { s = 0; t = Math.min(1, Math.max(0, f / e)); }
        else {
          const c = dotp(d1, r);
          if (e < 1e-12) { t = 0; s = Math.min(1, Math.max(0, -c / a)); }
          else {
            const b = dotp(d1, d2), den = a * e - b * b;
            s = den > 1e-12 ? Math.min(1, Math.max(0, (b * f - c * e) / den)) : 0;
            t = (b * s + f) / e;
            if (t < 0) { t = 0; s = Math.min(1, Math.max(0, -c / a)); } else if (t > 1) { t = 1; s = Math.min(1, Math.max(0, (b - c) / a)); }
          }
        }
        const c1 = [p1[0] + d1[0] * s, p1[1] + d1[1] * s, p1[2] + d1[2] * s], c2 = [p2[0] + d2[0] * t, p2[1] + d2[1] * t, p2[2] + d2[2] * t];
        return Math.hypot(...sub(c1, c2));
      };
      const polyDist = (A, B) => { let m = 9e9; for (let i = 0; i + 1 < A.length; i++) for (let j = 0; j + 1 < B.length; j++) m = Math.min(m, segSeg(A[i], A[i + 1], B[j], B[j + 1])); return m; };
      const planCross = (A, B) => {                            // transversal crossings (> 20 degrees) of two plan views
        for (let i = 0; i + 1 < A.length; i++) for (let j = 0; j + 1 < B.length; j++) {
          const d1 = [A[i + 1][0] - A[i][0], A[i + 1][1] - A[i][1]], d2 = [B[j + 1][0] - B[j][0], B[j + 1][1] - B[j][1]];
          const den = d1[0] * d2[1] - d1[1] * d2[0], l1 = Math.hypot(...d1), l2 = Math.hypot(...d2);
          if (l1 < 1e-9 || l2 < 1e-9 || Math.abs(den) / (l1 * l2) < Math.sin(20 * Math.PI / 180)) continue;
          const w = [B[j][0] - A[i][0], B[j][1] - A[i][1]], t = (w[0] * d2[1] - w[1] * d2[0]) / den, u = (w[0] * d1[1] - w[1] * d1[0]) / den;
          if (t > 0.02 && t < 0.98 && u > 0.02 && u < 0.98) return true;
        }
        return false;
      };
      const minRadius = P => {                                 // the circle through three points 4 apart, the smallest along the wire
        let m = 9e9;
        for (let i = 0; i + 8 < P.length; i++) {
          const a = P[i], b = P[i + 4], c = P[i + 8], ab = Math.hypot(...sub(b, a)), bc = Math.hypot(...sub(c, b)), ca = Math.hypot(...sub(a, c));
          const u = sub(b, a), v = sub(c, a), cr = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]], area2 = Math.hypot(...cr);
          if (area2 > 1e-9) m = Math.min(m, ab * bc * ca / (2 * area2));
        }
        return m;
      };
      const rw = hw.wire_r;
      for (const [bname, tag] of [['TS06-FASCIA-rhythm', 'R'], ['TS06-FASCIA', 'F']]) {
        const ctl = hw.boards[bname].controls;
        const W = [];
        for (const [ref, c] of Object.entries(ctl)) for (const w of c.wires) W.push({ ref, pad: w.pad, pts: w.pts });
        let gap = 9e9, who = '', cross = 0;
        for (let i = 0; i < W.length; i++) for (let j = i + 1; j < W.length; j++) {
          const g = polyDist(W[i].pts, W[j].pts) - 2 * rw;
          if (g < gap) { gap = g; who = `${W[i].ref}.${W[i].pad}/${W[j].ref}.${W[j].pad}`; }
          if (planCross(W[i].pts, W[j].pts)) cross++;
        }
        ok(`hand wiring ${tag}: no two of the ${W.length} wires cross or touch (least gap between wire surfaces ${gap.toFixed(2)} mm, ${who}), and none crosses another as seen from the back (${cross} crossings)`, W.length === 15 && gap >= 0.15 && cross === 0, `${gap.toFixed(3)} mm, ${cross} crossings`);
        const rmin = Math.min(...W.map(w => minRadius(w.pts)));
        ok(`hand wiring ${tag}: every bend of every wire has the one radius ${hw.bend_r} mm (the sharpest found in the points: ${rmin.toFixed(2)} mm), and the data says so`,
          rmin >= hw.bend_r - 0.05 && Object.values(ctl).every(c => Math.abs(c.bend_radius - hw.bend_r) < 0.05), `${rmin.toFixed(3)} mm`);
        const flat = W.every(w => { const e = w.pts[w.pts.length - 1]; let k = w.pts.length - 1, arc = 0; while (k > 0 && arc < 0.5) { arc += Math.hypot(...sub(w.pts[k], w.pts[k - 1])); k--; } return e[2] < rw + 0.01 && w.pts[k][2] < rw + 0.1; });
        ok(`hand wiring ${tag}: every wire lands flat on its pad (the last 0.5 mm lies within 0.1 mm of the board's surface)`, flat, '');
      }
      // the dial's group: the seven wires, one over another at a fixed pitch, each leaving its lug along the lug
      const d = R.SW1, lv = d.wires.map(w => w.level).sort((a, b) => a - b);
      const pitch = lv.slice(1).map((v, i) => v - lv[i]);
      ok('hand wiring R: the dial’s seven wires run as one group, one over another at a fixed pitch of 0.95 mm', lv.length === 7 && pitch.every(p => Math.abs(p - 0.95) < 0.01) && d.wires.every(w => ['left', 'right', 'straight on'].includes(w.turn)), `levels ${lv.map(v => v.toFixed(2)).join(' ')}`);
      const runAlong = w => { let k = 0; while (k + 1 < w.pts.length && Math.hypot(w.pts[k + 1][0] - w.pts[0][0], w.pts[k + 1][1] - w.pts[0][1]) < 0.02) k++; return w.pts[0][2] - w.pts[k][2]; };
      const alongs = d.wires.map(w => runAlong(w));
      ok('hand wiring R: each wire of the dial leaves its lug along the lug (straight toward the board beside it for at least 0.7 mm, the six taps for 4.5 mm, before its first bend)',
        alongs.every(a => a >= 0.7) && d.wires.every((w, i) => w.pts[0][2] < 19 || alongs[i] >= 4.5), alongs.map(a => a.toFixed(1)).join(' '));
    }
    const nHand = root => page.evaluate(root => {
      const V = window.TS06, shown = o => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
      let k = 0; V.roots[root].group.traverse(o => { if (o.isMesh && /^SW\d pad/.test(o.name) && shown(o)) k++; });
      return k;
    }, root);
    const cnt = { asm: await nHand('asm') };
    await page.click('#sc-FASCIA'); await settle(page);
    cnt.fascia = await nHand('FASCIA');
    await page.click('#sc-asm'); await settle(page);
    ok('hand wiring is drawn on the fascia: 15 wires in the assembly (the shown fascia), and in the fascia scene', cnt.asm === 15 && cnt.fascia === 15, JSON.stringify(cnt));
  }
  // the Wiring switch: on by default; off hides the lead, the hand wires and the pin labels; on shows them again
  {
    const count = () => page.evaluate(() => {
      const V = window.TS06, shown = o => { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; };
      let lead = 0, hand = 0;
      V.roots.asm.group.traverse(o => { if (o.isMesh && shown(o)) { if (/^wire \d/.test(o.name)) lead++; else if (/^SW\d pad/.test(o.name)) hand++; } });
      const labels = [...document.querySelectorAll('.pinlbl')].filter(e => e.isConnected && e.style.display !== 'none' && getComputedStyle(e).display !== 'none').length;
      return { lead, hand, labels, on: document.querySelector('#wiringon').checked, wv: V.wiring };
    });
    await page.click('#deck [data-view="isoL"]'); await settle(page);
    const on0 = await count();
    ok('Wiring switch: on at load (the lead’s 6 wires, 15 hand wires, six pin labels with Labels on)', on0.on && on0.wv && on0.lead === 6 && on0.hand === 15 && on0.labels === 6, JSON.stringify(on0));
    await page.click('label[for="wiringon"]'); await settle(page);
    const off = await count();
    ok('Wiring switch off: the lead, the hand wires and the pin labels are hidden', !off.on && off.lead === 0 && off.hand === 0 && off.labels === 0, JSON.stringify(off));
    await page.click('label[for="wiringon"]'); await settle(page);
    const on1 = await count();
    ok('Wiring switch back on: they show again', on1.on && on1.lead === 6 && on1.hand === 15 && on1.labels === 6, JSON.stringify(on1));
    await page.click('label[for="labelson"]'); await settle(page);
    const nl = await count();
    ok('Labels off hides the six pin labels and leaves the wires', nl.lead === 6 && nl.labels === 0, JSON.stringify(nl));
    await page.click('label[for="labelson"]'); await settle(page);
  }
  // a stored A or W from the old selector falls back to R
  await page.evaluate(() => localStorage.setItem('ts06v2:fascia', JSON.stringify('W')));
  await page.reload();
  await page.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 240000 });
  const fb = await page.evaluate(() => ({ fv: window.TS06.fv, btns: [...document.querySelectorAll('#fvseg button')].map(b => b.dataset.fv) }));
  ok('a stored fascia W (the old selector) falls back to R', fb.fv === 'R' && fb.btns.join() === 'R,F', JSON.stringify(fb));
  // the Fascia variants tab: one line at its top, R picked and ordered (fab/ORDER.md); the record stays
  await page.click('#dt-fascia');
  const fvt = await page.evaluate(() => { const e = document.querySelector('#doc-fascia > :first-child'); return { line: e.textContent.replace(/\s+/g, ' ').trim(), id: e.id, cols: [...document.querySelectorAll('#fvtable thead th')].map(t => t.textContent.trim()).filter(Boolean).length,
    btns: [...document.querySelectorAll('#fvtable button[data-fv3d]')].map(b => b.dataset.fv3d).join() }; });
  ok('Fascia variants tab: its first line says R was picked and is in the order (fab/ORDER.md); the four columns stay as the record; only R and F open in 3D', fvt.id === 'fv-picked' && /^R was picked/.test(fvt.line) && fvt.line.includes('fab/ORDER.md') && fvt.cols === 4 && fvt.btns === 'R,F', fvt.line.slice(0, 100) + ' | ' + fvt.btns);
  ok('wiring: no console errors', errs.length === 0, errs.slice(0, 3).join(' || '));
  await ctx.close();
  // the phone, light and dark: the Wiring switch and its legend fit 390 px, the selector offers R and F, the lead and its pin labels are there
  for (const scheme of ['light', 'dark']) {
    const { ctx: c2, page: p2, errs: e2 } = await newPage({ w: 390, h: 844, scheme, touch: true, mobile: true });
    await load(p2, '', true);
    await p2.evaluate(() => { const V = window.TS06; V.controls.target.set(96, -2, -25); V.camera.position.set(96, -110, -95); V.controls.update(); V.dirty = 3; });
    await p2.locator('.stagecard').scrollIntoViewIfNeeded();
    const r = await p2.evaluate(() => {
      const V = window.TS06, rect = s => document.querySelector(s).getBoundingClientRect();
      return { sw: document.documentElement.scrollWidth, noteRight: rect('#wirenote').right, noteH: rect('#wirenote').height, toggle: rect('label[for="wiringon"]'), fvs: [...document.querySelectorAll('#fvseg button')].map(b => b.dataset.fv).join(), lead: Object.keys(V.lead).join() };
    });
    await settle(p2);
    await shot(p2, `p390-${scheme}-wiring`);
    ok(`wiring phone ${scheme}: the Wiring switch and its legend fit 390 px, the selector offers R and F, no console errors`, r.sw <= 390 && r.noteRight <= 390 && r.toggle.width > 0 && r.toggle.right <= 390 && r.fvs === 'R,F' && r.lead === 'R,F' && e2.length === 0,
      `scrollWidth ${r.sw}, legend right edge ${r.noteRight.toFixed(0)}, toggle right edge ${r.toggle.right.toFixed(0)}, ${e2.slice(0, 2).join(' || ')}`);
    await c2.close();
  }
}

await browser.close();
server.kill();
const failed = results.filter(r => !r.pass);
console.log(`\n${results.length - failed.length} PASS, ${failed.length} FAIL; CDN files served locally: ${cdnHits.size}`);
fs.writeFileSync(path.join(SHOTS, 'results.json'), JSON.stringify({ results, cdn: [...cdnHits] }, null, 1));
process.exit(failed.length ? 1 : 0);
