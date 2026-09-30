import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import path from 'node:path';
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const server = spawn('python3', [path.join(ROOT, 'test/serve.py'), '8767'], { cwd: path.join(ROOT, 'site'), stdio: 'ignore' });
await new Promise(r => setTimeout(r, 700));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
page.on('console', m => { if (m.type() === 'error') console.log('console', m.type(), m.text()); });
await page.route('https://cdn.jsdelivr.net/npm/three@0.186.1/**', r => r.fulfill({ path: path.join(ROOT, 'work/three', r.request().url().split('three@0.186.1/')[1]), contentType: 'application/javascript' }));
await page.route('https://fonts.googleapis.com/**', r => r.fulfill({ body: '', contentType: 'text/css' }));
await page.goto('http://127.0.0.1:8767/index.html');
await page.waitForFunction(() => document.body.dataset.ready === '1', null, { timeout: 240000 });
await page.evaluate(() => { const V = window.TS06; V.renders = 0; const r = V.renderer.render.bind(V.renderer); V.renderer.render = (a, b) => { V.renders++; V.lastDirty = V.dirty; return r(a, b); }; });
for (let i = 0; i < 6; i++) {
  await page.waitForTimeout(5000);
  console.log('t', (i + 1) * 5, 's renders', await page.evaluate(() => [window.TS06.renders, window.TS06.dirty, !!window.TS06.tween]));
}
let t0 = Date.now();
await page.screenshot({ path: '/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/viewer2/work/perf.png' });
console.log('screenshot', Date.now() - t0, 'ms');
await page.evaluate(() => { window.TS06.animScale = 0; });
await page.click('#deck [data-view="front"]');
await page.waitForTimeout(500);
t0 = Date.now();
await page.screenshot({ path: '/tmp/claude-0/-home-user-TERMINAL-06-firmware/c1b2f23b-2f88-537c-b39a-4eee239c41d3/scratchpad/viewer2/work/perf2.png' });
console.log('screenshot after a move', Date.now() - t0, 'ms', await page.evaluate(() => window.TS06.renders));
await browser.close(); server.kill();
