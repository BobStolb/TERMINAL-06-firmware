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

await browser.close();
server.kill();
const failed = results.filter(r => !r.pass);
console.log(`\n${results.length - failed.length} PASS, ${failed.length} FAIL; CDN files served locally: ${cdnHits.size}`);
fs.writeFileSync(path.join(SHOTS, 'results.json'), JSON.stringify({ results, cdn: [...cdnHits] }, null, 1));
process.exit(failed.length ? 1 : 0);
