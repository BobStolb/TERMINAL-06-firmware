// Playwright checks for the TS06 board viewer v2.
//   node test/run.mjs            (from viewer2/; serves site/ on :8766, CDN routed to the npm-packed three)
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT = path.resolve(HERE, '..');
const SITE = path.join(ROOT, 'site');
const THREE = path.join(ROOT, 'work', 'three');
const SHOTS = path.join(ROOT, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });
const PORT = 8766;
const server = spawn('python3', [path.join(HERE, 'serve.py'), String(PORT)], { cwd: SITE, stdio: 'ignore' });
await new Promise(r => setTimeout(r, 800));

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
{
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
  for (const [re, name, want] of [[/U12 first/, 'S3', /U12 first/], [/U11 out/, 'S5', /U11 out/], [/Fit the fascia/, 'step09', /lead path/], [/rear panel/, 'step10', /rear panel/]]) {
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
        if (id === 'lead') want = want && V.explode < 0.05;
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
  for (const v of ['W', 'R', 'F', 'A']) {
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
{
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
for (const scheme of ['light', 'dark']) {
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
{
  const { ctx, page, errs } = await newPage({ w: 1280, h: 900 });
  await openPanel(page);
  const facts = JSON.parse(fs.readFileSync(path.join(SITE, 'data', 'facts.json'), 'utf8')).boards;
  const sz = b => `${facts[b].size[0]} × ${facts[b].size[1]}`;
  ok('front panel: the tab opens (#panel)', await page.evaluate(() => !document.querySelector('#doc-panel').hidden && document.querySelector('#dt-panel').getAttribute('aria-selected') === 'true'));
  // today's board, from the build
  {
    const res = [];
    for (const [v, b] of [['A', 'TS06-FASCIA'], ['W', 'TS06-FASCIA-wide'], ['R', 'TS06-FASCIA-rhythm']]) {
      await page.click(`#fp-fvseg button[data-fp="${v}"]`);
      await page.waitForFunction(() => ['#fp-front', '#fp-back'].every(s => document.querySelector(s).complete), null, { timeout: 30000 });
      const r = await page.evaluate(() => ({ imgs: ['#fp-front', '#fp-back'].map(s => document.querySelector(s).naturalWidth > 0), dl: document.querySelector('#fp-todayfacts').textContent }));
      res.push(r.imgs.every(Boolean) && r.dl.includes(sz(b)) && r.dl.includes(b));
    }
    await page.click('#fp-fvseg button[data-fp="A"]');
    ok('front panel: today’s boards A, W, R shown from the build (renders + facts)', res.every(Boolean), res.join(','));
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
    ok('old drawings labelled: superseded by today’s fascia, the choice still open', h.startsWith(`History: superseded by today’s TS06-FASCIA, ${sz('TS06-FASCIA')} mm`) && h.includes('still the owner’s open choice') && h.includes(sz('TS06-FASCIA-wide')), h.slice(0, 160));
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
{
  const bad = [];
  const walk = d => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, f.name); if (f.isDirectory()) walk(p); else if (/\.svg$/i.test(f.name) && /<!DOCTYPE/i.test(fs.readFileSync(p, 'utf8'))) bad.push(path.relative(SITE, p)); } };
  walk(SITE);
  ok('site SVGs carry no <!DOCTYPE', bad.length === 0, bad.join(', '));
}
for (const scheme of ['light', 'dark']) {
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

await browser.close();
server.kill();
const failed = results.filter(r => !r.pass);
console.log(`\n${results.length - failed.length} PASS, ${failed.length} FAIL; CDN files served locally: ${cdnHits.size}`);
fs.writeFileSync(path.join(SHOTS, 'results.json'), JSON.stringify({ results, cdn: [...cdnHits] }, null, 1));
process.exit(failed.length ? 1 : 0);
