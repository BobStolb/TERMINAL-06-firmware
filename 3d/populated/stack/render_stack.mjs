// Render the assembled TS06 stack (three populated boards placed from case_pair.py) with headless Chromium + three.js.
//
//   node 3d/populated/stack/render_stack.mjs STACK.json GLBDIR OUTDIR [front,iso]
//
// STACK.json is written by tools/stack_frame.py; GLBDIR holds TS06-DISP-populated.glb, TS06-DRV-populated.glb and
// TS06-FASCIA-rhythm-populated.glb (tools/render_populated.py). Writes OUTDIR/TS06-stack-<view>.png, transparent,
// trimmed, at most 2400 px wide. No network: three.js is the copy in ./vendor, served from a local port, and
// Chromium is the one in $PLAYWRIGHT_BROWSERS_PATH (/opt/pw-browsers here; run no `playwright install`).
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const [stackPath, glbArg, outDir, viewsArg] = process.argv.slice(2);
const glbDir = glbArg ? path.resolve(glbArg) : glbArg;
if (!outDir) { console.error('usage: node render_stack.mjs STACK.json GLBDIR OUTDIR [front,iso]'); process.exit(2); }
const views = (viewsArg || 'front,iso').split(',');
const stack = JSON.parse(fs.readFileSync(stackPath, 'utf8'));
fs.mkdirSync(outDir, { recursive: true });

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  const f = u.startsWith('/glb/') ? path.join(glbDir, u.slice(5)) : path.join(HERE, u === '/' ? 'stack.html' : u.slice(1));
  if (!f.startsWith(HERE) && !f.startsWith(glbDir)) { res.writeHead(403); res.end(); return; }
  fs.readFile(f, (err, data) => {
    if (err) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(f)] || 'application/octet-stream' });
    res.end(data);
  });
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const files = {
  'TS06-DISP': '/glb/TS06-DISP-populated.glb',
  'TS06-DRV': '/glb/TS06-DRV-populated.glb',
  'fascia': '/glb/' + stack.fascia_board + '-populated.glb',
};
const W = { front: 2400, iso: 2400 }, H = { front: 1500, iso: 1500 };
for (const view of views) {
  const ctx = await browser.newContext({ viewport: { width: W[view] || 2400, height: H[view] || 1500 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await page.addInitScript(s => { window.SCENE = s; }, { w: W[view] || 2400, h: H[view] || 1500, view, files, stack, fov: view === 'front' ? 12 : 18 });
  await page.goto(`http://127.0.0.1:${port}/stack.html`);
  try { await page.waitForFunction('window.__done === true', null, { timeout: 180000 }); }
  catch (e) { console.error('render failed:', errs.join('\n')); process.exit(1); }
  const out = path.join(outDir, `TS06-stack-${view}.png`);
  await page.screenshot({ path: out, omitBackground: true });
  console.log('wrote', out, errs.length ? 'console errors: ' + errs.join(' | ') : '');
  await ctx.close();
}
await browser.close();
server.close();
