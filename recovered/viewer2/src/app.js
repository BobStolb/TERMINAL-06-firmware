// TS06 board viewer v2: three.js scene, camera deck, assembly + explode, build and bring-up
// stepper, facts, circuit sections. Data comes from data/*.json, written by build.sh.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { ConvexGeometry } from 'three/addons/geometries/ConvexGeometry.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem('ts06v2:' + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem('ts06v2:' + k, JSON.stringify(v)); } catch (e) { /* storage blocked */ } },
};
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const BOARD = { DRV: 'TS06-DRV', DISP: 'TS06-DISP', FASCIA: 'TS06-FASCIA' };   // FASCIA follows the chosen variant
const FV = { A: 'TS06-FASCIA', W: 'TS06-FASCIA-wide', R: 'TS06-FASCIA-rhythm', F: 'TS06-FASCIA' };   // F: the 176 board stands in for the frame's 179 panel
const FV_NAME = { A: 'A · centred', W: 'W · full width', R: 'R · on the tube grid', F: 'F · in a printed frame' };
const HB = -0.045;          // KiCad's GLB: the board's back surface sits at this height (mm), the front at HB + thickness
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);

// ------------------------------------------------------------------------------------------ data
async function getJSON(u) {
  const r = await fetch(u);
  if (!r.ok) throw new Error(u + ' answered ' + r.status);
  return r.json();
}
let MODEL, PARTS, FACTS, SECTIONS;
let ORDER = null;                       // data/order.json: what is ready to order (tools/order.py)
let POP = { boards: {}, pictures: [] };   // data/populated.json: the boards drawn populated (tools/populated.py)
const isPop = b => !!(POP.boards || {})[b];
const hasStack = () => (POP.pictures || []).includes('img/stack-front.png');
const F = () => MODEL.frame;
const thick = k => PARTS[BOARD[k]].thickness;
const HTB = b => HB + PARTS[b].thickness;
const HT = k => HTB(BOARD[k]);
const fvData = v => (MODEL.fascia_variants || {})[v] || { X0: F().FASCIA_X0, bodies: MODEL.bodies, lead: MODEL.lead, lead_path: F().LEAD_PATH, checks: MODEL.checks, fascia_checks: [] };

// ------------------------------------------------------------------------------------------ theme
(function theme() {
  const root = document.documentElement;
  const set = t => { if (t) root.setAttribute('data-theme', t); else root.removeAttribute('data-theme'); store.set('theme', t || null); };
  const saved = store.get('theme', null);
  if (saved) root.setAttribute('data-theme', saved);
  $('#themebtn').addEventListener('click', () => {
    const cur = root.getAttribute('data-theme');
    const dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    set(dark ? 'light' : 'dark');
  });
})();

// ------------------------------------------------------------------------------------------ materials
const std = (color, o = {}) => new THREE.MeshStandardMaterial(Object.assign({ color, roughness: 0.6, metalness: 0 }, o));
const MAT = {
  glass: new THREE.MeshStandardMaterial({ color: 0xffc07a, roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.26, depthWrite: false, side: THREE.DoubleSide, emissive: 0x3a1600, emissiveIntensity: 0.4 }),
  chip: std(0x151515, { roughness: 0.5 }),
  dot: std(0xcfcfcf),
  pbs: std(0x1a1a1a, { roughness: 0.7 }),
  nano: std(0x1d5aa3, { roughness: 0.5 }),
  metal: std(0xc4c4c4, { metalness: 0.9, roughness: 0.3 }),
  rtc: std(0x1d5aa3, { roughness: 0.5 }),
  ptc: std(0xe3a31b, { roughness: 0.5 }),
  led: new THREE.MeshStandardMaterial({ color: 0xffb04a, roughness: 0.2, transparent: true, opacity: 0.8, emissive: 0x7a3a00, emissiveIntensity: 0.5 }),
  gold: std(0xd8b048, { metalness: 1, roughness: 0.3 }),
  wire: std(0xb8b8b8, { metalness: 0.9, roughness: 0.35 }),
  nylon: std(0xece5d6, { roughness: 0.75 }),
  screw: std(0x2b2b2b, { metalness: 0.5, roughness: 0.4 }),
  lead: std(0x8250df, { roughness: 0.55 }),
  white: std(0xf2f2f2, { roughness: 0.5 }),
  knob: std(0x2d333b, { roughness: 0.45 }),
  body: std(0x8c959f, { roughness: 0.5, metalness: 0.3 }),
  rot: std(0x6e7781, { roughness: 0.45, metalness: 0.4 }),
  orange: std(0xf28c28),
  lever: std(0xc9d1d9, { metalness: 0.8, roughness: 0.3 }),
  hl: new THREE.MeshStandardMaterial({ color: 0xff8a3d, emissive: 0xff5a00, emissiveIntensity: 0.55, roughness: 0.45 }),
  ghost: new THREE.MeshBasicMaterial({ color: 0xff8a3d, transparent: true, opacity: 0.22, depthWrite: false }),
};
const CASE_COL = { cheek_l: 0x3a3f45, cheek_r: 0x3a3f45, brow: 0xf28c28, top: 0x2b2f34, trench: 0x30363d, base: 0x30363d, rear: 0x15181b, fascia_frame: 0x30363d };

function glyphTexture(ch) {
  const c = document.createElement('canvas');
  c.width = 128; c.height = 192;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 128, 192);
  g.font = '300 170px "IBM Plex Mono", monospace';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.shadowColor = 'rgba(255,120,20,1)'; g.shadowBlur = 18;
  g.strokeStyle = 'rgba(255,170,90,1)'; g.lineWidth = 7;
  g.strokeText(ch, 64, 104);
  g.shadowBlur = 0; g.strokeStyle = 'rgba(255,225,170,1)'; g.lineWidth = 2.5;
  g.strokeText(ch, 64, 104);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const glyphMat = ch => new THREE.MeshBasicMaterial({ map: glyphTexture(ch), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide });

// ------------------------------------------------------------------------------------------ geometry helpers
function box(w, h, d, mat, x, y, z) {               // w along x, h along y, d along z; centre at x,y,z
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  return m;
}
function ycyl(r, y0, y1, mat, x, z, seg = 20, r2) {  // a cylinder standing along +y from y0 to y1
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r2 ?? r, r, y1 - y0, seg), mat);
  m.position.set(x, (y0 + y1) / 2, z);
  return m;
}
function zcylW(r, z0, z1, mat, x, y, seg = 20) {       // a cylinder along the three.js z axis
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, Math.abs(z1 - z0), seg), mat);
  m.rotation.x = Math.PI / 2;
  m.position.set(x, y, (z0 + z1) / 2);
  return m;
}
function hull(points, mat) {
  return new THREE.Mesh(new ConvexGeometry(points), mat);
}
function tag(obj, item, ref) {
  obj.traverse(o => { o.userData.item = item; if (ref) o.userData.ref = ref; });
  return obj;
}

// board-local ("native") frame of KiCad's GLB, in mm: x = board x, y = height above the back face,
// z = board y (down the page). Proxies for parts KiCad has no body for are built in it.
function nativeGroupFor(key, gltf, root, bname = BOARD[key], fv) {
  const g = new THREE.Group();
  g.name = key + ':native';
  g.userData.board = key;
  const items = {};
  const sub = id => { if (!items[id]) { items[id] = new THREE.Group(); items[id].name = id; g.add(items[id]); } return items[id]; };
  const scene = gltf.scene.clone(true);
  scene.scale.setScalar(1000);
  const mainItem = key === 'DRV' ? 'drv' : key === 'DISP' ? 'disp' : 'fascia';
  sub(mainItem).add(scene);
  // named nodes: KiCad names each part's node by its reference
  const refs = new Map();
  scene.traverse(o => {
    if (o !== scene && /^[A-Z]{1,3}\d{1,3}$/.test(o.name) && !refs.has(o.name)) refs.set(o.name, o);
  });
  for (const [ref, o] of refs) {
    const k = key + ':' + ref;
    root.addRef(k, o, g);
    if (/^X[SP]\d+$/.test(ref)) { o.userData.stripItem = mainItem + '.strips'; root.addItem(mainItem + '.strips', o); }
  }
  // KiCad exports every copper feature in the finish colour (gold, for ENIG) under a mask that is 83 %
  // opaque, so pours and tracks glow through it. On a real black board they barely show: the mask is
  // made opaque here, and the pads stay gold through its openings. The FR4 body becomes opaque too.
  const fixed = new Map();
  scene.traverse(o => {
    const m = o.isMesh && o.material;
    if (!m || !m.transparent) return;
    if (!fixed.has(m)) {
      const c = m.clone();
      // (GLTFLoader turns depth writes off for BLEND materials: an opaque copy must turn them back on)
      if (m.opacity > 0.95) { c.transparent = false; c.opacity = 1; c.depthWrite = true; }
      else if (m.color && m.color.r + m.color.g + m.color.b < 0.3) { c.transparent = false; c.opacity = 1; c.depthWrite = true; c.roughness = 0.5; }
      fixed.set(m, c);
    }
    o.material = fixed.get(m);
  });
  // the finish gold (ENIG pads, and the fascia's gold lines) is a fully metallic material in the GLB: under this scene's soft
  // light it mirrors a dim room and reads pale cream. Keep its colour, lean on the diffuse part so it reads as gold.
  const golds = new Map();
  scene.traverse(o => {
    const m = o.isMesh && o.material;
    if (!m || !m.color || m.transparent || m.metalness < 0.9 || !(m.color.r > 0.5 && m.color.g > 0.4 && m.color.b < 0.25)) return;
    if (!golds.has(m)) { const c = m.clone(); c.color.setRGB(0.9, 0.66, 0.08); c.metalness = 0.3; c.roughness = 0.38; c.emissive = new THREE.Color(0x2e1d00); golds.set(m, c); }
    o.material = golds.get(m);
  });
  g.updateMatrixWorld(true);
  const P = PARTS[bname].parts;
  const ht = HTB(bname);
  g.userData.bname = bname;
  if (isPop(bname)) populatedItems(key, g, root, refs);        // the GLB is 3d/populated's: every part is in it already
  else if (key === 'DISP') buildDispProxies(g, sub, root, P, ht);
  else if (key === 'DRV') buildDrvProxies(g, sub, root, P, ht, refs);
  else if (key === 'FASCIA') buildFasciaProxies(g, sub, root, P, ht, fv);
  for (const [id, grp] of Object.entries(items)) root.addItem(id, grp);
  g.userData.items = items;
  return g;
}

// A populated board's GLB (3d/populated) holds every part under a node named by its reference. The build and
// bring-up steps show and hide parts by item name (in12, leds, chip:U2, nano, rtc, fascia ...), as they did with the
// stand-in bodies; here the item is the part's own node, so the stepper works on the real bodies. A tube's socket
// contacts are part of its node, a chip's socket part of the chip's: they appear with it.
function populatedItems(key, g, root, refs) {
  const reg = (item, ref, alias) => {
    const o = refs.get(ref);
    if (!o) return;
    root.addItem(item, o);
    if (alias) root.addRef(alias, o, g);
  };
  if (key === 'DISP') {
    for (const t of MODEL.tubes) reg(({ IN12: 'in12', IN15: 'in15', IN17: 'in17', INS1: 'ins1' })[t.kind] || 'in12', t.ref);
    for (const l of MODEL.leds) reg('leds', l.ref);
  } else if (key === 'DRV') {
    for (const ref of CHIPS) reg('chip:' + ref, ref, 'DRV:' + ref + '#chip');
    reg('nano', 'U1', 'DRV:U1#sockets');
    reg('rtc', 'U13', 'DRV:U13#module');
  } else {
    for (const ref of ['SW1', 'SW2', 'SW3', 'SW4', 'SW5', 'J1']) reg('fascia', ref);
  }
}

function buildDispProxies(g, sub, root, P, ht) {
  const f = F();
  const TOP = f.DISP_TOP_Y;
  const digits = { V1: '1', V2: '2', V3: '3', V4: '4', V5: '5', V6: '6', V9: 'A', V10: 'M' };
  for (const t of MODEL.tubes) {
    const x = t.X, z = TOP - t.Y, key = 'DISP:' + t.ref;
    const grp = new THREE.Group();
    if (t.kind === 'IN12' || t.kind === 'IN15') {
      const y0 = ht + f.Z_DISP_F - f.IN12_D, y1 = ht + f.Z_DISP_F;
      const pts = [];
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) for (let i = 0; i < 10; i++) {
        const a = i / 10 * Math.PI * 2;
        const cx = x + sx * (f.IN12_W / 2 - 2) + 2 * Math.cos(a), cz = z + sz * (f.IN12_H / 2 - 2) + 2 * Math.sin(a);
        pts.push(V3(cx, y0, cz), V3(cx, y1, cz));
      }
      grp.add(hull(pts, MAT.glass));
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(12, 18), glyphMat(digits[t.ref] || '8'));
      pl.rotation.x = -Math.PI / 2; pl.position.set(x, (y0 + y1) / 2 + 3, z);
      pl.userData.noFit = true;
      grp.add(pl);
      tag(grp, t.kind === 'IN12' ? 'in12' : 'in15', key);
      // the 12 socket contacts (fitted in build step 2)
      const cg = new THREE.Group();
      for (const p of P[t.ref].pads || []) if (/^\d+$/.test(p[0])) cg.add(ycyl(0.75, ht, ht + f.IN12_SEAT, MAT.gold, p[1], p[2], 10));
      tag(cg, 'contacts', key + '#contacts');
      sub('contacts').add(cg);
      root.addRef(key + '#contacts', cg, g);
    } else if (t.kind === 'IN17') {
      const yF = ht + f.Z_DISP_F, yR = ht + f.Z_DISP_F - f.IN17_D;
      const pts = [];
      for (const sx of [-1, 1]) for (const sz of [-1, 1]) pts.push(V3(x + sx * f.IN17_FACE / 2, yF, z + sz * f.IN17_H / 2), V3(x + sx * f.IN17_FACE / 2, yF - 0.5, z + sz * f.IN17_H / 2));
      for (let i = 0; i < 28; i++) {
        const a = i / 28 * Math.PI * 2;
        pts.push(V3(x + f.IN17_STEM / 2 * Math.cos(a), yR, z + f.IN17_STEM / 2 * Math.sin(a)), V3(x + f.IN17_STEM / 2 * Math.cos(a), yR + 0.5, z + f.IN17_STEM / 2 * Math.sin(a)));
      }
      grp.add(hull(pts, MAT.glass));
      const pl = new THREE.Mesh(new THREE.PlaneGeometry(6.5, 9.5), glyphMat(digits[t.ref] || '8'));
      pl.rotation.x = -Math.PI / 2; pl.position.set(x, yF - 3, z); pl.userData.noFit = true;
      grp.add(pl);
      for (const p of P[t.ref].pads || []) grp.add(ycyl(0.3, ht, yR, MAT.wire, p[1], p[2], 6));
      tag(grp, 'in17', key);
    } else if (t.kind === 'INS1') {
      grp.add(ycyl(f.INS1_D / 2, ht + f.Z_DISP_F - 28 + 3, ht + f.Z_DISP_F - 2, MAT.glass, x, z, 24));
      const core = ycyl(0.9, ht + 8, ht + f.Z_DISP_F - 5, new THREE.MeshBasicMaterial({ color: 0xff7a1a, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false }), x, z, 8);
      core.userData.noFit = true; grp.add(core);
      for (const p of P[t.ref].pads || []) grp.add(ycyl(0.3, ht, ht + 4, MAT.wire, p[1], p[2], 6));
      tag(grp, 'ins1', key);
    }
    sub(grp.userData.item).add(grp);
    root.addRef(key, grp, g);
  }
  for (const l of MODEL.leds) {
    const p = P[l.ref];
    const x = p.at[0], z = p.at[1];
    const grp = new THREE.Group();
    grp.add(ycyl(f.LED_D / 2, ht, ht + f.LED_H - f.LED_D / 2, MAT.led, x, z, 16));
    const dome = new THREE.Mesh(new THREE.SphereGeometry(f.LED_D / 2, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), MAT.led);
    dome.position.set(x, ht + f.LED_H - f.LED_D / 2, z);
    grp.add(dome);
    grp.add(ycyl(1.9, ht, ht + 1, MAT.led, x, z, 16));
    tag(grp, 'leds', 'DISP:' + l.ref);
    sub('leds').add(grp);
    root.addRef('DISP:' + l.ref, grp, g);
  }
}

function padsBox(pads) {
  const xs = pads.map(p => p[1]), zs = pads.map(p => p[2]);
  return { x0: Math.min(...xs), x1: Math.max(...xs), z0: Math.min(...zs), z1: Math.max(...zs) };
}
function boxIn(obj, frame, out = new THREE.Box3()) {      // obj's bounding box in frame's coordinates
  out.makeEmpty();
  frame.updateMatrixWorld(true);
  const inv = frame.matrixWorld.clone().invert();
  obj.updateMatrixWorld(true);
  obj.traverse(o => {
    if (!o.isMesh || o.userData.noFit) return;
    if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
    const b = o.geometry.boundingBox.clone().applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld));
    out.union(b);
  });
  return out;
}

const CHIPS = ['U2', 'U3', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10', 'U11', 'U12', 'U15', 'U16', 'U17'];
function buildDrvProxies(g, sub, root, P, ht, refs) {
  const f = F();
  // DIP bodies on their sockets. The chips are fitted stage by stage in bring-up; RN1 (a resistor
  // network) goes in when the board is built.
  for (const ref of CHIPS.concat(['RN1'])) {
    const p = P[ref];
    if (!p || !p.pads) continue;
    const b = padsBox(p.pads);
    const alongX = (b.x1 - b.x0) >= (b.z1 - b.z0);
    const len = (alongX ? b.x1 - b.x0 : b.z1 - b.z0) + 2.0;
    const wid = (alongX ? b.z1 - b.z0 : b.x1 - b.x0) - 1.27;
    const node = refs.get(ref);
    let top = ht + 4.2;
    if (node) { const bb = boxIn(node, g); if (!bb.isEmpty()) top = bb.max.y; }
    const cx = (b.x0 + b.x1) / 2, cz = (b.z0 + b.z1) / 2;
    const grp = new THREE.Group();
    grp.add(box(alongX ? len : wid, 3.3, alongX ? wid : len, MAT.chip, cx, top + 1.35, cz));
    const p1 = p.pads.find(q => q[0] === '1');
    if (p1) {
      const dx = cx - p1[1], dz = cz - p1[2], L = Math.hypot(dx, dz) || 1;
      const dot = ycyl(0.55, top + 2.99, top + 3.03, MAT.dot, p1[1] + dx / L * 2.2, p1[2] + dz / L * 2.2, 12);
      grp.add(dot);
    }
    const item = ref === 'RN1' ? 'drv' : 'chip:' + ref;
    tag(grp, item, 'DRV:' + ref + (ref === 'RN1' ? '' : '#chip'));
    sub(item).add(grp);
    if (ref !== 'RN1') root.addRef('DRV:' + ref + '#chip', grp, g);
  }
  // the Nano: two PBS-15 strips (built with the board), and the module on them (bring-up stage 3)
  const u1 = P.U1;
  if (u1 && u1.pads) {
    const rows = {};
    for (const q of u1.pads) (rows[q[2].toFixed(1)] = rows[q[2].toFixed(1)] || []).push(q);
    const socks = new THREE.Group();
    for (const r of Object.values(rows)) {
      const b = padsBox(r);
      socks.add(box(b.x1 - b.x0 + 2.54, f.PBS_H, 2.54, MAT.pbs, (b.x0 + b.x1) / 2, ht + f.PBS_H / 2, b.z0));
    }
    tag(socks, 'drv', 'DRV:U1#sockets');
    sub('drv').add(socks);
    const cy = u1.box, y0 = ht + f.PBS_H + f.PLS_BODY;
    const nano = new THREE.Group();
    const bx0 = cy[0], bx1 = Math.min(cy[1], f.BOARD_W - 0.4);
    nano.add(box(bx1 - bx0, 1.6, cy[3] - cy[2] - 0.6, MAT.nano, (bx0 + bx1) / 2, y0 + 0.8, (cy[2] + cy[3]) / 2));
    const zc = f.DRV_TOP_Y - f.USB_Y;
    nano.add(box(9.2, 4, 7.7, MAT.metal, cy[1] - 4.6, y0 + 1.6 + 2, zc));
    nano.add(box(7, 1.2, 7, MAT.chip, (bx0 + bx1) / 2 - 4, y0 + 2.2, (cy[2] + cy[3]) / 2));
    for (const r of Object.values(rows)) { const b = padsBox(r); nano.add(box(b.x1 - b.x0 + 2.54, f.PLS_BODY, 2.54, MAT.pbs, (b.x0 + b.x1) / 2, ht + f.PBS_H + f.PLS_BODY / 2, b.z0)); }
    tag(nano, 'nano', 'DRV:U1');
    sub('nano').add(nano);
    root.addRef('DRV:U1', nano, g);
  }
  // the DS3231 mini standing in U13's 5-way strip (bring-up stage 4)
  const u13 = P.U13;
  if (u13 && u13.pads) {
    const b = padsBox(u13.pads);
    const m = new THREE.Group();
    m.add(box(b.x1 - b.x0 + 5, 22 - f.PBS_H, 1.6, MAT.rtc, (b.x0 + b.x1) / 2, ht + f.PBS_H + (22 - f.PBS_H) / 2, b.z0 - 1.2));
    m.add(box(5, 5, 1.2, MAT.chip, (b.x0 + b.x1) / 2, ht + 16, b.z0 - 2.6));
    tag(m, 'rtc', 'DRV:U13#module');
    sub('rtc').add(m);
    root.addRef('DRV:U13#module', m, g);
  }
  // F1: KiCad's library has no MF-RG1100 body; the BOM now asks for a 1.1 A radial PTC (MF-R110)
  const f1 = P.F1;
  if (f1 && f1.pads) {
    const [a, c] = f1.pads;
    const m = box(Math.hypot(c[1] - a[1], c[2] - a[2]) + 3, 11, 3.2, MAT.ptc, (a[1] + c[1]) / 2, ht + 3 + 5.5, (a[2] + c[2]) / 2);
    m.rotation.y = -Math.atan2(c[2] - a[2], c[1] - a[1]);
    tag(m, 'drv', 'DRV:F1');
    sub('drv').add(m);
    root.addRef('DRV:F1', m, g);
  }
}

function buildFasciaProxies(g, sub, root, P, ht, fv) {
  const d = fvData(fv);
  const back = HB;              // the controls hang behind the fascia (its B face)
  for (const [ref, X, t, a, b, dep] of d.bodies) {
    const x = X - d.X0, z = t;
    const grp = new THREE.Group();
    if (ref === 'SW1') {
      grp.add(ycyl(a / 2, back - dep, back, MAT.rot, x, z, 32));
      grp.add(ycyl(10, ht, ht + 14, MAT.knob, x, z, 32));
      grp.add(box(1.2, 0.4, 6, MAT.orange, x, ht + 14.2, z - 6));
    } else if (ref === 'SW2' || ref === 'SW3') {
      grp.add(box(a, dep, b, MAT.body, x, back - dep / 2, z));
      const lv = ycyl(1.25, 0, 16, MAT.lever, 0, 0, 12, 2.0);
      const piv = new THREE.Group(); piv.add(lv); piv.position.set(x, ht, z); piv.rotation.x = -20 * Math.PI / 180;
      grp.add(piv);
    } else {
      grp.add(box(a, dep, b, MAT.body, x, back - dep / 2, z));
      grp.add(ycyl(5.5, ht, ht + 6, MAT.knob, x, z, 24));
    }
    tag(grp, 'fascia', 'FASCIA:' + ref);
    sub('fascia').add(grp);
    root.addRef('FASCIA:' + ref, grp, g);
  }
  const j1 = P.J1 && P.J1.box;
  if (j1) {
    const grp = new THREE.Group();
    grp.add(box(j1[1] - j1[0] - 2, 4.8, j1[3] - j1[2], MAT.white, (j1[0] + j1[1]) / 2, back - 2.4, (j1[2] + j1[3]) / 2));
    tag(grp, 'fascia', 'FASCIA:J1');
    sub('fascia').add(grp);
    root.addRef('FASCIA:J1', grp, g);
  }
}

// ------------------------------------------------------------------------------------------ roots
class Root {
  constructor(name) {
    this.name = name;
    this.group = new THREE.Group();
    this.group.name = name;
    this.items = new Map();       // item id -> [Object3D]
    this.refs = new Map();        // 'DRV:U11' -> { objs: [], frames: [one per object], frame: the first }
    this.natives = {};            // board key -> native group
    this.hl = [];                 // highlight decorations to remove
  }
  addItem(id, o) { if (!this.items.has(id)) this.items.set(id, []); this.items.get(id).push(o); }
  addRef(k, o, frame) { if (!this.refs.has(k)) this.refs.set(k, { objs: [], frames: [], frame }); const e = this.refs.get(k); e.objs.push(o); e.frames.push(frame); }
  setItem(id, on) { for (const o of this.items.get(id) || []) o.visible = on; }
}

function boardMatrix(key, fv) {      // native -> three.js world, as the case model places the board
  const f = F(), m = new THREE.Matrix4(), ht = key === 'FASCIA' ? HTB(FV[fv]) : HT(key);
  if (key === 'DISP') m.set(1, 0, 0, 0, 0, 0, -1, f.DISP_TOP_Y, 0, 1, 0, -(ht + f.Z_DISP_F), 0, 0, 0, 1);
  if (key === 'DRV') m.set(-1, 0, 0, f.BOARD_W, 0, 0, -1, f.DRV_TOP_Y, 0, -1, 0, HB - f.Z_DRV_F, 0, 0, 0, 1);
  if (key === 'FASCIA') {
    const r = f.FASCIA_RAKE * Math.PI / 180, s = Math.sin(r), c = Math.cos(r);
    m.set(1, 0, 0, fvData(fv).X0, 0, s, -c, f.SILL_TOP_Y - ht * s, 0, c, s, -f.Z_FACE - ht * c, 0, 0, 0, 1);
  }
  return m;
}
function standMatrix(bname) {        // native -> upright, centred: the front face towards +z
  const e = PARTS[bname].edge;
  const W = e[1] - e[0], H = e[3] - e[2];
  return new THREE.Matrix4().set(1, 0, 0, -(e[0] + W / 2), 0, 0, -1, e[2] + H / 2, 0, 1, 0, -(HB + HTB(bname)) / 2, 0, 0, 0, 1);
}
const variantsAvail = () => Object.keys(FV).filter(v => V.gltf['F' + v] && PARTS[FV[v]] && (v !== 'F' || (MODEL.fascia_variants || {}).F));
function holder(matrix) {
  const h = new THREE.Group();
  h.matrixAutoUpdate = false;
  h.matrix.copy(matrix);
  return h;
}
function exploder(root, dir) {
  const e = new THREE.Group();
  e.userData.explode = V3(...dir);
  root.explo.push(e);
  return e;
}

// ------------------------------------------------------------------------------------------ viewer
const V = {
  scene: new THREE.Scene(),
  roots: {}, gltf: {}, current: 'asm', ready: false, explode: 0,
  caseOn: true, caseGhost: true, showLabels: true, hlList: [], step: -1, dirty: 2, animScale: 1,
};
const invalidate = (n = 2) => { V.dirty = Math.max(V.dirty, n); };   // render on demand: only when something changed
function initViewer() {
  const host = $('#gl');
  // logarithmic depth: the mask sits 0.015 mm over the copper, which a linear depth buffer cannot separate at 400 mm
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance', logarithmicDepthBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.setClearColor(0x000000, 0);
  host.appendChild(renderer.domElement);
  const labelR = new CSS2DRenderer();
  labelR.domElement.className = 'labels';
  host.appendChild(labelR.domElement);
  const camera = new THREE.PerspectiveCamera(28, 1.6, 1, 6000);
  camera.position.set(-260, 180, 380);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.12;
  controls.screenSpacePanning = true;
  controls.zoomToCursor = true;
  controls.minDistance = 15;
  controls.maxDistance = 2500;
  controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
  const pmrem = new THREE.PMREMGenerator(renderer);
  V.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  V.scene.environmentIntensity = 0.85;
  const key = new THREE.DirectionalLight(0xffffff, 1.4); key.position.set(-1, 1.6, 1.2);
  const fill = new THREE.DirectionalLight(0xffffff, 0.5); fill.position.set(1.2, -0.4, -1);
  V.scene.add(key, fill, new THREE.HemisphereLight(0xffffff, 0x404040, 0.35));
  Object.assign(V, { renderer, labelR, camera, controls, host });
  const resize = () => {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    labelR.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    invalidate();
  };
  new ResizeObserver(resize).observe(host);
  resize();
  V.onscreen = true;
  new IntersectionObserver(es => { V.onscreen = es[0].isIntersecting; }).observe(host);
  controls.addEventListener('start', () => { V.tween = null; });
  controls.addEventListener('change', () => invalidate());
  new IntersectionObserver(es => { if (es[0].isIntersecting) invalidate(); }).observe(host);
  renderer.setAnimationLoop(t => {
    if (!V.onscreen || document.hidden) {       // off screen: draw nothing; a pending move just lands
      if (V.tween) { V.controls.target.copy(V.tween.t1); V.camera.position.copy(V.tween.t1).add(V.tween.b); V.tween = null; }
      return;
    }
    if (V.tween) { stepTween(t); invalidate(); }
    controls.update();                     // fires 'change' while damping settles
    if (V.dirty <= 0) return;
    V.dirty--;
    renderer.render(V.scene, camera);
    labelR.render(V.scene, camera);
  });
  // keyboard on the focused stage
  host.addEventListener('keydown', e => {
    const k = e.key;
    const map = { '1': 'front', '2': 'back', '3': 'top', '4': 'bottom', '5': 'left', '6': 'right', '7': 'isoL', '8': 'isoR', f: 'fit', F: 'fit', '0': 'fit' };
    if (map[k]) { view(map[k]); e.preventDefault(); return; }
    if (k === '+' || k === '=') { zoom(0.75); e.preventDefault(); return; }
    if (k === '-' || k === '_') { zoom(1 / 0.75); e.preventDefault(); return; }
    const a = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[k];
    if (a) { orbitBy(a[0] * 15, a[1] * 10); e.preventDefault(); }
  });
}

function orbitBy(dAz, dPol) {
  const off = V.camera.position.clone().sub(V.controls.target);
  const s = new THREE.Spherical().setFromVector3(off);
  s.theta += dAz * Math.PI / 180;
  s.phi = THREE.MathUtils.clamp(s.phi + dPol * Math.PI / 180, 0.01, Math.PI - 0.01);
  tweenTo(V.controls.target.clone(), V3(0, 0, 0).setFromSpherical(s).add(V.controls.target), 350);
}

// ---- camera moves
const DIRS = {
  front: [0, 0, 1], back: [0, 0, -1], top: [0, 1, 0.0001], bottom: [0, -1, 0.0001], left: [-1, 0, 0], right: [1, 0, 0],
  isoL: [-1, 0.72, 1.3], isoR: [1, 0.72, 1.3], isoBL: [-1, 0.6, -1.25], isoBR: [1, 0.6, -1.25], lowL: [-1, 0.25, 1.1], lowR: [1, 0.3, 1.1], underL: [-0.75, -0.55, 0.45],
};
function visibleBox(obj) {
  const b = new THREE.Box3(), t = new THREE.Box3();
  obj.updateMatrixWorld(true);
  obj.traverseVisible(o => {
    if (!o.isMesh || o.userData.noFit || o.userData.hlDeco) return;
    if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
    t.copy(o.geometry.boundingBox).applyMatrix4(o.matrixWorld);
    b.union(t);
  });
  return b;
}
function fitDistance(radius) {
  const vfov = V.camera.fov * Math.PI / 180;
  const hfov = 2 * Math.atan(Math.tan(vfov / 2) * V.camera.aspect);
  return radius / Math.sin(Math.min(vfov, hfov) / 2) * 1.02;
}
function frameBox(b, dirName, pad = 1, ms = 700) {
  if (b.isEmpty()) return;
  const c = b.getCenter(V3()), r = b.getBoundingSphere(new THREE.Sphere()).radius * pad;
  const d = V3(...(DIRS[dirName] || DIRS.isoL)).normalize();
  let dist = fitDistance(r);
  // A long thin board (the fascia, the display) fills little of the frame when a sphere is fitted round it: when its box, seen from
  // this side, is more than 2.5 times wider than tall, fit the projected box instead (the sphere stays for every other shape).
  const right = V3(0, 1, 0).cross(d); if (right.lengthSq() < 1e-6) right.set(1, 0, 0); right.normalize();
  const up = d.clone().cross(right).normalize();
  let hw = 0, hh = 0, hd = 0;
  for (const x of [b.min.x, b.max.x]) for (const y of [b.min.y, b.max.y]) for (const z of [b.min.z, b.max.z]) {
    const q = V3(x, y, z).sub(c);
    hw = Math.max(hw, Math.abs(q.dot(right))); hh = Math.max(hh, Math.abs(q.dot(up))); hd = Math.max(hd, Math.abs(q.dot(d)));
  }
  if (hw > 2.5 * hh && hh > 0) {
    const t = Math.tan(V.camera.fov * Math.PI / 360);
    dist = Math.min(dist, (Math.max(hh / t, hw / (t * V.camera.aspect)) * 1.08 + hd) * pad);
  }
  tweenTo(c, c.clone().add(d.multiplyScalar(dist)), ms);
}
function currentDir() {
  const d = V.camera.position.clone().sub(V.controls.target).normalize();
  let best = 'isoL', bd = -2;
  for (const [k, v] of Object.entries(DIRS)) { const x = V3(...v).normalize().dot(d); if (x > bd) { bd = x; best = k; } }
  return best;
}
function view(name) {
  const root = V.roots[V.current];
  if (!root) return;
  const b = visibleBox(root.group);
  frameBox(b, name === 'fit' ? (V.current === 'asm' ? 'isoL' : 'front') : name);       // frameBox: the sphere, or the box of a long thin board
}
function zoom(f) {
  const t = V.controls.target, off = V.camera.position.clone().sub(t);
  const L = THREE.MathUtils.clamp(off.length() * f, V.controls.minDistance, V.controls.maxDistance);
  tweenTo(t.clone(), t.clone().add(off.setLength(L)), 300);
}
const ease = x => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
function tweenTo(target, pos, ms = 700) {
  const t0 = V.controls.target.clone(), p0 = V.camera.position.clone();
  ms *= V.animScale;                  // 1; the tests set 0 once the animated moves are checked
  if (REDUCED || ms === 0) { V.controls.target.copy(target); V.camera.position.copy(pos); V.controls.update(); return; }
  const a = p0.clone().sub(t0), b = pos.clone().sub(target);
  V.tween = { start: null, ms, t0, t1: target, a, b, q: new THREE.Quaternion().setFromUnitVectors(a.clone().normalize(), b.clone().normalize()) };
}
function stepTween(now) {
  const w = V.tween;
  if (w.start === null) w.start = now;
  const k = Math.min(1, (now - w.start) / w.ms), e = ease(k);
  const dir = w.a.clone().normalize().applyQuaternion(new THREE.Quaternion().slerp(w.q, e));
  const len = THREE.MathUtils.lerp(w.a.length(), w.b.length(), e);
  V.controls.target.lerpVectors(w.t0, w.t1, e);
  V.camera.position.copy(V.controls.target).add(dir.multiplyScalar(len));
  if (k >= 1) V.tween = null;
}

// ---- the four scenes
function buildRoots() {
  // assembly, in the case model's world (three.js: X, Y, -Z)
  const A = new Root('asm');
  A.explo = [];
  const f = F();
  const dispEx = exploder(A, [0, 0, 26]), drvEx = exploder(A, [0, 0, -30]), fasEx = exploder(A, [0, -6, 60]);
  for (const [k, ex] of [['DISP', dispEx], ['DRV', drvEx]]) {
    const h = holder(boardMatrix(k));
    ex.add(h);
    const n = nativeGroupFor(k, V.gltf[k], A);
    h.add(n);
    A.natives[k] = n;
    A.group.add(ex);
  }
  A.fnatives = {};
  for (const v of variantsAvail()) {            // the fascia variants, each at its own case position
    const h = holder(boardMatrix('FASCIA', v));
    h.userData.fv = v;
    const n = nativeGroupFor('FASCIA', V.gltf['F' + v], A, FV[v], v);
    h.add(n);
    fasEx.add(h);
    A.fnatives[v] = n;
  }
  A.group.add(fasEx);
  // standoffs (nylon, M3 × 11) and their screws, and the four module screws into the cheeks
  const so = new THREE.Group();
  for (const [X, Y] of MODEL.standoffs) {
    so.add(zcylW(6.35 / 2, -f.Z_DISP_B, -f.Z_DRV_F, MAT.nylon, X, Y, 6));
    so.add(zcylW(f.SCREW_HEAD_D / 2, -f.Z_DISP_F, -f.Z_DISP_F + f.SCREW_HEAD, MAT.screw, X, Y, 16));
    so.add(zcylW(f.SCREW_HEAD_D / 2, -f.Z_DRV_B, -f.Z_DRV_B - f.SCREW_HEAD, MAT.screw, X, Y, 16));
  }
  tag(so, 'standoffs', '@standoffs'); A.addItem('standoffs', so); A.addRef('@standoffs', so, drvEx);
  drvEx.add(so);
  const cs = new THREE.Group();
  for (const [, X, Y] of MODEL.case_screws) cs.add(zcylW(f.SCREW_HEAD_D / 2, -f.Z_DRV_B, -f.Z_DRV_B - f.SCREW_HEAD, MAT.screw, X, Y, 16));
  tag(cs, 'case_screws', '@case_screws'); A.addItem('case_screws', cs); A.addRef('@case_screws', cs, drvEx);
  drvEx.add(cs);
  // the fascia lead: DRV J1 -> floor -> the fascia's J1 (case model's centre line)
  for (const v of variantsAvail()) {
    const path = new THREE.CurvePath();
    const pts = fvData(v).lead.map(p => V3(p[0], p[1], -p[2]));
    for (let i = 0; i < pts.length - 1; i++) path.add(new THREE.LineCurve3(pts[i], pts[i + 1]));
    const lead = new THREE.Mesh(new THREE.TubeGeometry(path, 96, f.CABLE_HALF + 0.35, 8, false), MAT.lead);
    const w = new THREE.Group(); w.userData.fv = v; w.add(lead);
    tag(lead, 'lead', '@lead'); A.addItem('lead', lead); A.addRef('@lead', lead, w);
    A.group.add(w);
  }
  // the case
  // explode vectors: case.scad's ex([dX, dY, dZ]) in world, as (dX, dY, -dZ) here
  const EX = { cheek_l: [-40, 0, 0], cheek_r: [40, 0, 0], brow: [0, 36, 12], top: [0, 62, 0], trench: [0, 0, 30], base: [0, -30, 0], rear: [0, 0, -50], fascia_frame: [0, -8, 42] };
  A.caseMats = [];
  V.gltf.CASE.scene.traverse(o => {
    if (!o.isMesh) return;
    const name = o.name || (o.parent && o.parent.name);
    if (!CASE_COL[name]) return;
    const m = new THREE.Mesh(o.geometry, new THREE.MeshStandardMaterial({ color: CASE_COL[name], roughness: 0.75, metalness: 0.05, flatShading: true, transparent: true, opacity: 0.22, depthWrite: false, side: THREE.DoubleSide }));
    m.applyMatrix4(o.matrixWorld);
    A.caseMats.push(m.material);
    const ex = exploder(A, EX[name] || [0, 0, 0]);
    const w = new THREE.Group();
    if (name === 'fascia_frame') w.userData.fv = 'F';       // variant D: shown only with F
    ex.add(w); w.add(m);
    tag(m, name, '@' + name);
    A.addItem(name, ex); A.addRef('@' + name, m, ex);
    A.group.add(ex);
  });
  V.roots.asm = A;
  V.scene.add(A.group);
  // one board at a time, standing up, front face towards you
  for (const k of ['DRV', 'DISP', 'FASCIA']) {
    const R = new Root(k);
    if (k === 'FASCIA') {
      R.fnatives = {};
      for (const v of variantsAvail()) {
        const h = holder(standMatrix(FV[v]));
        h.userData.fv = v;
        const n = nativeGroupFor(k, V.gltf['F' + v], R, FV[v], v);
        h.add(n);
        R.fnatives[v] = n;
        R.group.add(h);
      }
    } else {
      const h = holder(standMatrix(BOARD[k]));
      const n = nativeGroupFor(k, V.gltf[k], R);
      h.add(n);
      R.natives[k] = n;
      R.group.add(h);
    }
    R.group.visible = false;
    V.roots[k] = R;
    V.scene.add(R.group);
  }
}

function setFascia(v, opts = {}) {
  if (!FV[v] || (V.ready && !variantsAvail().includes(v))) v = 'A';
  V.fv = v; store.set('fascia', v);
  BOARD.FASCIA = FV[v];
  $$('#fvseg button').forEach(b => b.setAttribute('aria-pressed', b.dataset.fv === v));
  for (const r of Object.values(V.roots)) {
    r.group.traverse(o => { if (o.userData.fv) o.visible = o.userData.fv === v; });
    if (r.fnatives) r.natives.FASCIA = r.fnatives[v];
  }
  if (MODEL) {
    STEPS = steps();
    renderStepCard(); renderTestStages();
    if (V.step >= 0) $('#stepchip').innerHTML = stepChipHTML(STEPS[V.step]);
    renderFacts();
    if (UI.scene === 'FASCIA') { UI.shot = Math.min(UI.shot, IMGS.FASCIA().length - 1); renderShots(); setDims(); }
  }
  if (V.ready) highlight(V.hlList);
}
function setExplode(e) {
  V.explode = e;
  const A = V.roots.asm;
  if (A) for (const g of A.explo) g.position.copy(g.userData.explode).multiplyScalar(e);
  applyVisibility();
  $('#explode').value = Math.round(e * 100);
  $('#explodeout').textContent = Math.round(e * 100) + '%';
}
function setCaseLook() {
  const A = V.roots.asm;
  if (!A) return;
  for (const m of A.caseMats) { m.opacity = V.caseGhost ? 0.22 : 1; m.transparent = V.caseGhost; m.depthWrite = !V.caseGhost; m.needsUpdate = true; }
  applyVisibility();
}
const CASE_PARTS = ['cheek_l', 'cheek_r', 'brow', 'top', 'trench', 'base', 'rear', 'fascia_frame'];
const SHELL = ['cheek_l', 'cheek_r', 'brow', 'top', 'trench', 'base'];
const ALL_ITEMS = ['drv', 'drv.strips', 'disp', 'disp.strips', 'nano', 'rtc', 'contacts', 'leds', 'in12', 'in15', 'in17', 'ins1',
  'standoffs', 'case_screws', 'fascia', 'lead', ...CHIPS.map(c => 'chip:' + c), ...CASE_PARTS];
function applyVisibility() {
  const A = V.roots.asm;
  invalidate();
  if (!A) return;
  const vis = A.stepVis || new Set(ALL_ITEMS);
  for (const id of A.items.keys()) {
    let on = vis.has(id);
    if (CASE_PARTS.includes(id)) on = on && V.caseOn;
    if (id === 'lead') on = on && V.explode < 0.05;
    A.setItem(id, on);
  }
}

// ---- highlight
function clearHighlight(root) {
  for (const d of root.hl) {
    if (d.restore) d.restore();
    else if (d.parent) d.parent.remove(d);
  }
  root.hl = [];
}
function highlight(list) {          // list: [{ key: 'DRV:U11', note: 'out' | undefined, label }]
  V.hlList = list || [];
  invalidate();
  const root = V.roots[V.current];
  if (!root) return;
  for (const r of Object.values(V.roots)) clearHighlight(r);
  let n = 0;
  for (const h of V.hlList) {
    const ent = resolveRef(root, h.key);
    if (!ent) continue;
    const { objs, frame } = ent;
    const out = h.note === 'out';
    if (!out) for (const o of objs) o.traverse(m => {
      if (m.isMesh && !m.userData.noFit && !m.userData.hlDeco && m.material !== MAT.hl) {
        const orig = m.material;
        m.material = MAT.hl;
        root.hl.push({ restore: () => { m.material = orig; } });
      }
    });
    let b = new THREE.Box3();
    for (const o of objs) b.union(boxIn(o, frame));
    if (b.isEmpty()) continue;
    b.expandByScalar(0.6);
    const helper = new THREE.Box3Helper(b, out ? 0x9a9a9a : 0xff8a3d);
    helper.userData.hlDeco = true;
    helper.userData.noFit = true;
    frame.add(helper);
    root.hl.push(helper);
    if (!h.nolabel && n < 24) {
      const el = document.createElement('div');
      el.className = 'lbl' + (out ? ' out' : '') + (h.label && !out ? ' note' : '');
      el.textContent = h.label || (refName(h.key) + (out ? ' out' : ''));
      const lo = new CSS2DObject(el);
      lo.userData.hlDeco = true;
      const c = b.getCenter(V3());
      c.y = b.max.y;
      lo.position.copy(c);
      frame.add(lo);
      root.hl.push(lo);
      n++;
    }
  }
}
function refName(key) {
  return key.startsWith('@') ? key.slice(1).replace('_', ' ') : (key.split(':')[1] || key).replace(/#.*/, '');
}
function resolveRef(root, key) {
  let e = root.refs.get(key);
  if (e) {
    // a ref the three fascia variants share (FASCIA:J1, @lead) holds one object per variant, each in its own frame: the highlight
    // and its label go in the frame of the one that is shown (the first variant's frame is hidden while R or W is on)
    const keep = e.objs.map((o, i) => i).filter(i => isShown(e.objs[i]));
    return keep.length ? { objs: keep.map(i => e.objs[i]), frame: e.frames[keep[0]] } : (key.startsWith('@') ? null : courtyardRef(root, key));
  }
  return courtyardRef(root, key);
}
function isShown(o) { for (let p = o; p; p = p.parent) if (!p.visible) return false; return true; }
function courtyardRef(root, key) {      // a part with no body: a thin box on its courtyard
  const [bk, refRaw] = key.split(':');
  const ref = (refRaw || '').replace(/#.*/, '');
  const n = root.natives[bk];
  const p = n && PARTS[BOARD[bk]].parts[ref];
  if (!p || !p.box || !isShown(n)) return null;
  const [x0, x1, z0, z1] = p.box;
  const back = p.side === 'B', ht = HT(bk);
  const m = box(x1 - x0, 1.2, z1 - z0, MAT.ghost, (x0 + x1) / 2, back ? HB - 0.6 : ht + 0.6, (z0 + z1) / 2);
  m.userData.hlDeco = true;
  n.add(m);
  root.hl.push(m);
  return { objs: [m], frame: n };
}
function hlBox() {
  const root = V.roots[V.current], b = new THREE.Box3();
  for (const d of root.hl) if (d.isBox3Helper) { d.updateMatrixWorld(true); b.union(new THREE.Box3().copy(d.box).applyMatrix4(d.parent.matrixWorld)); }
  return b;
}

// ------------------------------------------------------------------------------------------ scenes, modes
const IMGS = {
  asm: () => [['case-iso', 'Case, angled'], ['case-front', 'Front'], ['case-exploded', 'Exploded'], ['case-iso_rear', 'Rear'], ['case-module', 'Module'],
    ...(hasStack() ? [['stack-front', 'Populated, front'], ['stack-iso', 'Populated, angled']] : [])],
  DRV: [['TS06-DRV-iso', 'Angled'], ['TS06-DRV-top', 'Top (parts)'], ['TS06-DRV-bottom', 'Bottom (strips)']],
  DISP: [['TS06-DISP-iso', 'Angled'], ['TS06-DISP-top', 'Top (tubes)'], ['TS06-DISP-bottom', 'Bottom (strips)']],
  FASCIA: () => [[BOARD.FASCIA + '-iso', 'Angled'], [BOARD.FASCIA + '-top', 'Face'], [BOARD.FASCIA + '-bottom', 'Back']],
};
const imgList = s => typeof IMGS[s] === 'function' ? IMGS[s]() : IMGS[s];
function setDims() {
  const s = UI.scene;
  $('#dims').textContent = s === 'asm' ? `case ${F().OUT_W} × ${F().OUT_H} × ${F().OUT_D.toFixed(1)} mm`
    : (() => { const e = PARTS[BOARD[s]].edge; return `${BOARD[s]} · ${+(e[1] - e[0]).toFixed(2)} × ${+(e[3] - e[2]).toFixed(2)} × ${thick(s)} mm`; })();
}
const UI = { scene: store.get('scene', 'asm'), mode: 'img', shot: 0, side: 'steps', doc: 'sections' };
function setScene(s, opts = {}) {
  if (!['asm', 'DRV', 'DISP', 'FASCIA'].includes(s)) s = 'asm';
  UI.scene = s; V.current = s; store.set('scene', s);
  $$('#scenes .tab').forEach(t => { const on = t.dataset.scene === s; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; });
  for (const [k, r] of Object.entries(V.roots)) r.group.visible = k === s;
  invalidate();
  $('#asmdeck').hidden = s !== 'asm';
  $('#imgbtn').textContent = s === 'asm' ? 'Case pictures' : 'KiCad renders';
  setDims();
  $('#fvseg').hidden = !(s === 'asm' || s === 'FASCIA');
  UI.shot = 0;
  renderShots();
  renderFacts();
  $('#stepchip').hidden = !(s === 'asm' && V.step >= 0);
  if (V.ready) {
    highlight(V.hlList);
    if (!opts.keepCamera) view('fit');
  }
}
function setMode(m) {
  UI.mode = m;
  invalidate();
  $('#stage').dataset.mode = m;
  $$('#modeseg button').forEach(b => b.setAttribute('aria-pressed', b.dataset.mode === m));
}
function renderShots() {
  const list = imgList(UI.scene);
  $('#shotnav').innerHTML = list.map((s, i) => `<button type="button" data-i="${i}" aria-pressed="${i === UI.shot}">${esc(s[1])}</button>`).join('');
  const img = $('#shotimg');
  img.src = 'img/' + list[UI.shot][0] + '.png';
  img.alt = (UI.scene === 'asm' ? (/^stack/.test(list[UI.shot][0]) ? 'The three boards in their case positions, ' : 'Case model, ')
    : BOARD[UI.scene] + (isPop(BOARD[UI.scene]) ? ', populated, KiCad render, ' : ', KiCad render, ')) + list[UI.shot][1];
  $('#shotview').classList.remove('zoom');
}

// ------------------------------------------------------------------------------------------ steps
const on = (...a) => new Set(a.flat());
const BOARD_ITEMS = ['drv', 'drv.strips', 'disp', 'disp.strips', 'rtc', 'nano', 'contacts', 'leds'];
const allChips = CHIPS.map(c => 'chip:' + c);
const chipsOf = (...refs) => refs.map(r => 'chip:' + r);
const TUBES_ALL = ['in12', 'in15', 'in17', 'ins1'];
const MODULE = ['drv', 'drv.strips', 'disp', 'disp.strips', 'contacts', 'leds', 'standoffs'];
const hlRefs = (b, ...refs) => refs.flat().map(r => ({ key: b + ':' + r }));
const rng = (p, a, b) => Array.from({ length: b - a + 1 }, (_, i) => p + (a + i));
const XS = ['XS11', 'XS12', 'XS21', 'XS22', 'XS23', 'XS24', 'XS25'], XP = XS.map(s => s.replace('XS', 'XP'));

function steps() {
  const f = F();
  const fd = fvData(V.fv || 'A'), lead = fd.lead_path, gap = f.STACK_GAP;
  const r5 = (fd.fascia_checks || []).find(r => /R5/.test(r.what));
  const fname = FV_NAME[V.fv || 'A'];
  return [
    { g: 'build', n: '1', title: 'Build the driver board', vis: on('drv'), explode: 0, cam: 'isoBL', fit: 'all',
      hl: hlRefs('DRV', 'U14', 'L1', 'C7', 'VT21', 'RP1', 'XS1'),
      body: `<p>Solder every part of TS06-DRV onto its component face, the one that will face the rear panel. The ICs go into sockets and stay <b>empty</b> until bring-up; the Nano sits on two PBS-15 strips. RN1, the 8 × 220 Ω network, goes into its socket now.</p>
      <ul><li><b>Leave the seven socket strips XS11–XS25 off.</b> They are soldered in step 4, with the display plugged on.</li>
      <li>Check every socket's notch against the silkscreen: the board uses three orientations.</li>
      <li>U13 takes the DS3231 mini, whose own header is female: fit a <b>male</b> strip. Pad 1 (square) is GND and the module's + goes to pad 5, so square-to-square reverses it.</li>
      <li>F1 is a 1.1 A radial PTC (MF-R110 class) on 5.1 mm leads. The 0.5 W 350 V resistors must be DIN0309 size with leads of 0.6 mm or less.</li></ul>` },
    { g: 'build', n: '2', title: 'Fit the display’s LEDs and socket contacts', vis: on('disp', 'contacts', 'leds'), explode: 0, cam: 'isoL', fit: 'all',
      hl: [{ key: '@contactsAll', group: 'contacts' }, ...hlRefs('DISP', rng('HL', 1, 9))],
      body: `<p>On TS06-DISP's front face: the <b>72 socket contacts</b> for the six socketed tubes (four ИН-12 and two ИН-15, 12 each) and the <b>nine 3 mm LEDs</b>, HL1–HL8 under the tubes and HL9, the "m", between the ИН-15s.</p>
      <ul><li>The ИН-17s and the ИНС-1 lamps are wire-ended and wait until step 6, after the strips.</li>
      <li>Leave the pin strips XP11–XP25 on the back off for now.</li></ul>` },
    { g: 'build', n: '3', title: 'Mate the boards on their standoffs', vis: on(MODULE), explode: 0, cam: 'lowL', fit: 'all',
      hl: [{ key: '@standoffs' }],
      body: `<p>Push the XP pin strips into the XS socket strips, loose, and put the strips between the boards: XP on the display's back, XS on the driver's back. Then join the boards with <b>four M3 × 11 mm nylon standoffs</b> and eight M3 × 6 screws.</p>
      <ul><li>${gap} mm = 8.5 mm PBS + 2.5 mm PLS body. Measure the strips you bought before trusting it.</li>
      <li>Nylon, or brass with nylon washers at both ends: tracks pass 2.2–2.4 mm from DRV H2/H3 and DISP H3, inside a metal standoff's 2.75–3.2 mm.</li></ul>` },
    { g: 'build', n: '4', title: 'Solder the strips on both boards, mated', vis: on(MODULE), explode: 0, cam: 'underL', fit: 'all',
      hl: hlRefs('DRV', XS).concat(hlRefs('DISP', XP)),
      body: `<p>With the boards screwed together, solder <b>XS11–XS25 on TS06-DRV and XP11–XP25 on TS06-DISP</b>. Soldered in place, all 63 strip pins line up; soldered loose, the 31-pin strips will not.</p>
      <div class="caution">Under a loupe afterwards: on XS21/23/24/25 and XP21/23/24/25 a 5 V LED line sits 0.84 mm from a 185 V anode pad. A bridge there puts 185 V into the MCP23017.</div>` },
    { g: 'build', n: '5', title: 'Separate the boards', vis: on(MODULE), explode: 0.65, cam: 'isoL', fit: 'all', hl: [],
      body: `<p>Unscrew the display and pull it straight off. The strips are now soldered to their own boards and will always meet again the same way.</p>` },
    { g: 'build', n: '6', title: 'Fit the ИНС-1 lamps and the ИН-17s', vis: on(MODULE, 'ins1', 'in17'), explode: 0.65, cam: 'isoR', fit: 'hl',
      hl: hlRefs('DISP', 'V5', 'V6', 'V7', 'V8'),
      body: `<p>Solder the two ИНС-1 colon lamps (V7, V8) and the two wire-ended ИН-17 seconds tubes (V5, V6) on their spacers, glass faces level with the ИН-12 fronts: ${f.IN17_STANDOFF} mm of lead above the board.</p>
      <ul><li><b>Confirm the ИН-17 lead order on a rig first</b> (gate 3). A wrong one cannot be undone.</li>
      <li>Measure the ИН-17 pip and the Ø20 stem (gate 5): the seconds pair stands 20.5 mm apart for it.</li></ul>` },
    { g: 'build', n: '7', title: 'Plug the boards together again', vis: on(MODULE, TUBES_ALL), explode: 0, cam: 'isoL', fit: 'all',
      hl: [{ key: '@standoffs' }],
      body: `<p>Plug TS06-DISP back onto the strips and screw the four standoffs. The ИН-12s and ИН-15s plug into their socket contacts; bench stage 6 fits them one at a time.</p>
      <p>Before closing anything up, bring the module up on the bench: the <b>Bring-up</b> steps below. The display comes off again for stages 1–5.</p>` },
    // --------------------------------------------------------------- bench bring-up
    { g: 'bench', n: 'S1', title: 'Bare boards: continuity and isolation', vis: on('drv', 'drv.strips', 'disp', 'disp.strips', 'contacts', 'leds', 'in17', 'ins1', 'standoffs'), explode: 0.65, cam: 'isoL', fit: 'all',
      hl: hlRefs('DRV', 'XS21', 'XS23', 'XS24', 'XS25', 'RP1', 'VT21'),
      body: `<p>No power. Every socket empty, the Nano and RTC out, the display unplugged.</p>
      <ul><li>Loupe: the strip rows XS/XP 21, 23, 24, 25 (0.84 mm HV gaps), VT21's pads and the empty bleeds R33–R44.</li>
      <li>Every pair in the guide's table 1b reads <b>open</b> on the highest range.</li>
      <li><b>Set RP1 for the lowest voltage, with the power off:</b> its maximum resistance, <b>5.0 kΩ between pins 1 and 2</b> (pin 1 to GND). That is the 165 V set-point.</li>
      <li>C7+ to C7−: 550–600 kΩ. C7+ to U12 pin 2: 560–615 kΩ; 963 kΩ means R62 or R63 is open: then do not power the converter.</li></ul>
      <div class="pass">Pass: <b>OL</b> on every isolation pair, R27–R30 6.8 kΩ, R31–R32 12 kΩ, R56–R57 18 kΩ in place, <b>RP1 = 5.0 kΩ</b>.</div>` },
    { g: 'bench', n: 'S2', title: 'Power only: no chips, no modules', vis: on('drv', 'drv.strips'), explode: 0, cam: 'isoBL', fit: 'all',
      hl: hlRefs('DRV', 'XS1', 'U14', 'C8', 'C7', 'VD2'),
      body: `<p>12.0 V with a <b>100 mA</b> limit into the barrel jack (centre positive). Nothing in any socket.</p>
      <ul><li>Supply current ≈ 1.7 mA (under 5 mA). +12 V at C8: 11.5–12.0 V. +5 V at U14 pin 3: 4.75–5.25 V.</li>
      <li>VREF at U12 pin 3: 2.46–2.52 V. HV185 at C7+: ≈ 11.4 V (the input through L1 and VD1).</li>
      <li>Every socket's supply pins before a chip sees them. The К155ИД1 is <b>+5 V on pin 5, GND on pin 12</b>, not the corners.</li></ul>
      <div class="pass">Pass: <b>&lt; 5 mA</b>, +5 V within ±5 %, the rail at the input voltage.</div>` },
    { g: 'bench', n: 'S3', title: 'The converter: U12 first, then U11', hv: true, vis: on('drv', 'drv.strips', 'nano', chipsOf('U11', 'U12')), explode: 0, cam: 'isoBR', fit: 'hl',
      hl: [{ key: 'DRV:U12#chip', label: 'U12 first · pin 1' }, { key: 'DRV:U11#chip', label: 'U11 second' }, ...hlRefs('DRV', 'RP1', 'C7', 'VT21', 'L1', 'VD1')],
      body: `<p>Flash the Nano with <code>firmware/ts06_bringup</code>. With the power off, fit <b>U12 (LM393) first and check its pin 1</b> against the silkscreen notch. Only then fit <b>U11 (TC4420)</b> and the Nano. The display stays unplugged.</p>
      <div class="danger"><b>Until rev B there is no independent over-voltage clamp.</b> U12 is the only thing that stops the converter. With U11 in and U12 missing or turned round, the rail runs away.</div>
      <ul><li>Meter on 600 V DC clipped across C7 before power. 12.0 V, <b>500 mA</b> limit.</li>
      <li>Power on: 8–25 mA with the converter off. Type <code>H</code>: the rail rises to the RP1 = 5 kΩ set-point, ≈ 165 V. If it passes 200 V or keeps climbing, <code>h</code> or switch off at once.</li>
      <li>Set 185 V with a plastic tool: RP1 ≈ 2.55 kΩ, about 1.8 V per turn.</li>
      <li>Supply off, time C7 down: under 10 V in 6–11 s. From now on: <b>wait 15 s and check under 10 V</b>.</li></ul>
      <div class="pass">Pass: <b>185 ± 1 V</b>, <code>H</code> adds 3–15 mA, ripple ≤ 1.5 V p-p, C7 under 10 V within 11 s.</div>` },
    { g: 'bench', n: 'S4', title: 'Logic: the Nano, U3 and the RTC', hv: true, vis: on('drv', 'drv.strips', 'nano', 'rtc', chipsOf('U11', 'U12', 'U3')), explode: 0, cam: 'isoBR', fit: 'all',
      hl: [{ key: 'DRV:U1' }, { key: 'DRV:U3#chip' }, { key: 'DRV:U13#module', label: 'U13 RTC' }],
      body: `<p>Power off, fit <b>U3</b> (MCP23017; check the notch) and the <b>DS3231 module in U13</b>: GND, NC, SCL, SDA, +5 V from pin 1.</p>
      <div class="caution"><b>Connect USB only while 12 V is applied.</b> With 12 V off, USB power back-feeds the R-78E's output through the Nano's diode, which can damage it (rev B adds a 1N5819 across U14).</div>
      <ul><li>Type <code>i</code>: an I²C scan with the converter off.</li>
      <li>Decoder inputs at the empty sockets: <code>0</code> puts code 1 on U2 pin 3, and so on (guide 4.4).</li>
      <li>The clock firmware (BOARD_TYPE 4) <b>starts the converter at boot</b>: clip the meter on C7 first.</li></ul>
      <div class="pass">Pass: the scan finds <b>0x20</b> (MCP23017) and <b>0x68</b> (DS3231); SDA and SCL idle high.</div>` },
    { g: 'bench', n: 'S5', title: 'Decoders and optos, U11 out', vis: on('drv', 'drv.strips', 'nano', 'rtc', chipsOf('U2', 'U3', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10', 'U12', 'U15', 'U16', 'U17')), explode: 0, cam: 'isoBR', fit: 'all',
      hl: [{ key: 'DRV:U11', note: 'out' }, ...['U2', 'U15', 'U16', 'U17', 'U5', 'U6', 'U7', 'U8', 'U9', 'U10'].map(r => ({ key: 'DRV:' + r + '#chip' }))],
      body: `<p>Power off and discharge. <b>Pull U11</b>: R68 then holds VT21's gate low and nothing can start the converter, so the rail sits at ≈ 11.4 V. Fit the four К155ИД1 (U2, U15, U16, U17) and the six TLP627 (U5–U10).</p>
      <ul><li>12 V, 200 mA limit: 30–70 mA in all.</li>
      <li>LED probe from +5 V (U14 pin 3): only the strip pins the sketch names light it.</li>
      <li><code>t</code> then <code>s</code>: the selected tube's anode pin reads ≈ 10.7 V, the other five under 1 V.</li>
      <li>Colon with the stand-in lamp: off &gt; 10 V, <code>k</code> on &lt; 0.3 V. Each LED line lights only in its own step.</li></ul>` },
    { g: 'bench', n: 'S6', title: 'Display mated, tubes one at a time', hv: true, vis: on(MODULE, TUBES_ALL, 'nano', 'rtc', allChips), explode: 0, cam: 'isoL', fit: 'all',
      hl: [{ key: 'DISP:V1', label: 'V1 (H10) first' }, { key: 'DRV:R27', label: 'meter across R27' }],
      body: `<p>Power off, discharge, <b>refit U11</b>, plug the display on and screw the standoffs. Fit the socketed tubes one at a time; the sketch lights one anode at a time.</p>
      <ul><li>Meter (floating, never a scope) across the tube's anode resistor; <code>H</code>, pick the tube with <code>t</code>, a digit, then <code>s</code> for a 5 s steady burst.</li>
      <li>ИН-12 across R27–R30 (6k8): <b>33–53 V</b> steady. ИН-17 across R31–R32 (12k): <b>66–90 V</b>.</li>
      <li>ИН-15 across R56/R57 (18k): 34–54 V. Colon across R58/R59: 115–130 V, the two within 3 V.</li>
      <li>Then the clock, BOARD_TYPE 4, all six tubes: right order and digits, no ghosting, no flicker.</li></ul>` },
    { g: 'bench', n: 'S7', title: 'The fascia', hv: true, vis: on(MODULE, TUBES_ALL, 'nano', 'rtc', allChips, 'fascia', 'lead'), explode: 0, cam: 'lowL', fit: 'all',
      hl: [...hlRefs('FASCIA', 'SW1', 'SW2', 'SW3', 'SW4', 'SW5', 'J1'), { key: 'DRV:J1' }, { key: '@lead', label: 'PH lead, 1:1' }],
      body: `<p>Power off. Check the PH lead is one-to-one, pin 1 to pin 1, and plug it into J1 (+5 V, GND, A6, A7, D7, D8). Type <code>r</code>.</p>
      <ul><li>A6, the MODE rotary: 0, 205, 409, 614, 818, 1023 (±7 codes) for positions 1–6.</li>
      <li>A7, the levers: 1023 open, 682 FIELD, 512 SUB, 409 both.</li>
      <li>"−" and "+" read DOWN. Always bring a pair up with the panel connected: with it unplugged A6 floats.</li></ul>` },
    { g: 'bench', n: 'S8', title: 'Full-system soak', hv: true, vis: on(MODULE, TUBES_ALL, 'nano', 'rtc', allChips, 'fascia', 'lead'), explode: 0, cam: 'isoBL', fit: 'all',
      hl: hlRefs('DRV', 'VT21', 'U14', 'C7', 'L1'),
      body: `<p>The clock firmware, all tubes, display mated, fascia on; 12 V with a 1 A limit or the adapter you will ship; meter on C7.</p>
      <ul><li>Input current 150–280 mA (≈ 200 mA, 2.4 W).</li>
      <li>After an hour: HV 185 ± 8 V; VT21 under 45 °C; regulator and decoders warm, not hot.</li>
      <li>24 hours: no flicker or ghosting, the colon dots match, RTC drift under 2 s. Afterwards C7 reaches 10 V in ≈ 8 s again.</li></ul>` },
    // --------------------------------------------------------------- into the case
    { g: 'case', n: '8', title: 'Fit the module into the case', vis: on(MODULE, TUBES_ALL, 'nano', 'rtc', allChips, 'case_screws', SHELL), explode: 0.35, cam: 'isoBL', fit: 'all', caseOn: true,
      hl: [{ key: '@case_screws', label: 'H5–H8 to the cheeks' }],
      body: `<p>Put the cheeks and the crossmembers (base, trench, brow, top plate) together <b>loosely</b>. Slide the module in from the back and screw TS06-DRV's <b>H5–H8</b> to the cheek bosses first, M3 × 8 with nylon washers: the driver board sets the cheeks' spacing. Then tighten the crossmember screws.</p>
      <ul><li>Print the crossmembers +0.4 % in X (PETG shrinks about 0.77 mm over the 192.4 mm between the cheeks), or what a 150 mm test bar says.</li>
      <li>The tube glass sits 1 mm behind the face plane, so a knock lands on the case. The module lifts out backwards as one piece.</li>
      <li>The USB slot in the left cheek is open to the rear edge; the 12 V jack passes the right cheek through a Ø9 hole with a Ø14 counterbore from outside.</li></ul>` },
    { g: 'case', n: '9', title: 'Fit the fascia and its lead', vis: on(MODULE, TUBES_ALL, 'nano', 'rtc', allChips, 'case_screws', SHELL, 'fascia_frame', 'fascia', 'lead'), explode: 0, cam: 'lowL', fit: 'all', caseOn: true,
      hl: [{ key: 'FASCIA:J1' }, { key: 'DRV:J1' }, { key: '@lead', label: `lead path ${lead} mm` }],
      body: `<p>${V.fv === 'F' ? `F: the printed frame screws to the cheeks (2 × M3 × 8) and the panel drops into its rabbet (4 × M2.5 × 6, plus 2 countersunk ties down through the sill). The 176 board stands in for the frame's 179 panel at X ${fd.X0}.` : `The fascia (${esc(fname)}, ${esc(BOARD.FASCIA)}) screws to four M2.5 bosses on the cheeks (M2.5 × 6) at FASCIA_X0 ${fd.X0} mm`}, raked back ${f.FASCIA_RAKE}°. Switch the variant with the <b>Fascia</b> buttons above the model.</p>
      <ul><li>The 6-way JST PH lead runs from DRV J1 down to the floor, across it, and up into the fascia's side-entry J1: a ${lead} mm path for a ${f.LEAD_LEN} mm lead (the BOM: 180–200 mm).</li>
      <li>Beep it out one-to-one before plugging it in.</li></ul>
      ${r5 && r5.status !== 'OK' ? `<div class="caution">Case model, ${esc(r5.status)}: ${esc(r5.what)}: ${esc(r5.result)}.</div>` : ''}
      <p style="font-size:13px;color:var(--muted)">The case parts drawn are the committed case model's, made for A: its bosses and sill notch do not move with the variant.</p>` },
    { g: 'case', n: '10', title: 'Fit the rear panel', vis: on(MODULE, TUBES_ALL, 'nano', 'rtc', allChips, 'case_screws', CASE_PARTS, 'fascia', 'lead'), explode: 0, cam: 'isoBR', fit: 'all', caseOn: true,
      hl: [{ key: '@rear', label: 'rear panel' }],
      body: `<p>Last, the rear panel: a 1.6 mm FR4 blank on six M2.5 × 6, three into the base's rear lip and three into the top plate's, its holes slotted ±0.6 mm in X. The vent slots sit over the Nano, away from every 185 V part, and it carries the label: 12 V DC centre +, 185 V inside, unplug and wait 15 s.</p>
      <ul><li>Service: rear panel off (4 screws), module screws out (4), draw it back, unplug DRV J1 from below, lift it out.</li></ul>` },
  ];
}
const GROUPS = { build: 'Build the module', bench: 'Bring it up on the bench', case: 'Close the case' };
let STEPS = [];

function goStep(i, opts = {}) {
  const A = V.roots.asm;
  V.step = i;
  store.set('step', i);
  if (i < 0) {
    if (A) A.stepVis = null;
    V.caseOn = true; $('#caseon').checked = true;
    setExplode(0);
    applyVisibility();
    highlight([]);
    renderStepCard();
    $('#stepchip').hidden = true;
    if (V.ready && !opts.noCamera) frameBox(visibleBox(A.group), 'isoL', 1, opts.ms);
    return;
  }
  const s = STEPS[i];
  if (UI.scene !== 'asm') setScene('asm', { keepCamera: true });
  if (UI.mode !== '3d') setMode('3d');
  if (A) A.stepVis = new Set(s.vis);
  V.caseOn = true;
  $('#caseon').checked = true;
  setExplode(s.explode || 0);
  applyVisibility();
  const hl = [];
  for (const h of s.hl) {
    if (h.group === 'contacts') {
      for (const t of MODEL.tubes) if (t.kind === 'IN12' || t.kind === 'IN15') hl.push({ key: 'DISP:' + t.ref + '#contacts', label: t.ref === 'V1' ? '72 contacts' : '' });
    } else hl.push(h);
  }
  highlight(hl.map(h => h.label === '' ? { key: h.key, nolabel: true } : h));
  renderStepCard();
  const chip = $('#stepchip');
  chip.innerHTML = stepChipHTML(s);
  chip.hidden = false;
  if (V.ready && !opts.noCamera) stepCamera(s, opts.ms);
}
const stepChipHTML = s => `<b>${esc(s.n)}</b>${esc(s.title)}${s.hv ? '<span class="hvflag">185 V</span>' : ''}`;
function stepCamera(s, ms) {
  const A = V.roots.asm;
  const hb = hlBox();
  const b = s.fit === 'hl' && !hb.isEmpty() ? hb : visibleBox(A.group);
  frameBox(b, s.cam, s.fit === 'hl' ? 1.25 : 1, ms);
}
function renderStepList() {
  let h = '', g = '';
  STEPS.forEach((s, i) => {
    if (s.g !== g) { g = s.g; h += `<li class="gh" role="presentation">${esc(GROUPS[g])}</li>`; }
    h += `<li><button type="button" data-step="${i}"${V.step === i ? ' aria-current="step"' : ''}><span>${esc(s.n)}</span><span>${esc(s.title)}${s.hv ? ' <span class="hvflag">185 V</span>' : ''}</span></button></li>`;
  });
  $('#steplist').innerHTML = `<li><button type="button" data-step="-1"${V.step < 0 ? ' aria-current="step"' : ''}><span>—</span><span>Overview: the finished clock</span></button></li>` + h;
}
function renderStepCard() {
  const i = V.step, card = $('#stepcard');
  if (i !== V.cardStep) { V.cardStep = i; const p = $('#panel-steps'); if (p.scrollTop > 0) p.scrollTop = 0; }
  if (i < 0) {
    card.innerHTML = `<div class="stephead"><span class="stepgroup">Overview</span><span class="stepnum">${STEPS.length} steps</span></div>
      <h2 class="steptitle">The finished clock</h2>
      <div class="stepbody"><p>TS06-DISP carries the tubes; TS06-DRV sits ${F().STACK_GAP} mm behind it on four nylon standoffs, its parts facing the rear panel; the fascia is raked ${F().FASCIA_RAKE}° under the tubes. The case is see-through: switch it off, or pull everything apart with <b>Explode</b>.</p>
      <p>Step through the build, the bench bring-up and the case with <b>Next</b>. Each step shows what is fitted and lights the parts it is about.</p></div>
      <div class="stepnav"><button class="btn primary" type="button" id="stepnext">Start: step 1</button></div>`;
  } else {
    const s = STEPS[i];
    const chips = s.hl.filter(h => !h.group).map(h => {
      const k = h.key;
      const txt = k.startsWith('@') ? k.slice(1).replace('_', ' ') : k.replace(/#.*/, '').replace(':', ' ');
      return `<button type="button" class="chip" data-key="${esc(k)}">${esc(txt)}${h.note === 'out' ? ' out' : ''}</button>`;
    }).join('');
    card.innerHTML = `<div class="stephead"><span class="stepgroup">${esc(GROUPS[s.g])}</span><span class="stepnum">${i + 1} / ${STEPS.length}</span></div>
      <h2 class="steptitle">${s.g === 'bench' ? 'Stage ' + esc(s.n.slice(1)) : 'Step ' + esc(s.n)} · ${esc(s.title)}${s.hv ? ' <span class="pill bad">185 V</span>' : ''}</h2>
      <div class="stepbody">${s.body}</div>
      ${chips ? `<div class="chips" aria-label="Parts in this step">${chips}</div>` : ''}
      <div class="stepnav"><button class="btn" type="button" id="stepprev">Prev</button><button class="btn primary" type="button" id="stepnext"${i >= STEPS.length - 1 ? ' disabled' : ''}>Next</button></div>`;
  }
  $$('#steplist button').forEach(b => { if (+b.dataset.step === i) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current'); });
}

// ------------------------------------------------------------------------------------------ facts
function pillDRC(d, expect) {
  if (!d) return '<span class="pill warn">not run</span>';
  const same = d.errors === expect[0] && d.warnings === expect[1] && d.unconnected === expect[2];
  const cls = d.unconnected ? 'bad' : same ? 'ok' : 'warn';
  return `<span class="pill ${d.errors ? (same ? 'warn' : 'bad') : 'ok'}">${d.errors} errors</span> <span class="pill ${d.warnings ? 'warn' : 'ok'}">${d.warnings} warnings</span> <span class="pill ${cls}">${d.unconnected} unconnected</span>${same ? '' : ' <span class="pill bad">changed since this page was written</span>'}`;
}
function popBodies(bname) {         // the facts row for a populated board
  const f = (POP.boards[bname] || {}).footprints || {};
  const tot = (f.with_model || 0) + (f.allowlisted || 0) + (f.missing || 0);
  return ['3D bodies', `<span class="num">${f.with_model}</span> of <span class="num">${tot}</span> footprints carry a model; the other ${f.allowlisted} are ${bname === 'TS06-DRV' ? 'mounting holes and the DNP bleed resistors the bench leaves empty' : 'bare mounting holes'}. <span class="pill ${f.missing ? 'bad' : 'ok'}">${f.missing} missing</span>`];
}
function renderFacts() {
  const s = UI.scene, el = $('#panel-facts'), f = F();
  const B = k => FACTS.boards[BOARD[k]];
  const n = x => `<span class="num">${x}</span>`;
  const size = k => { const b = B(k); return `${n(b.size[0] + ' × ' + b.size[1] + ' mm')}, ${n(b.thickness + ' mm')} FR4, 2 layers`; };
  let name, sub, rows, note;
  if (s === 'DRV') {
    const b = B('DRV');
    name = 'TS06-DRV · driver board'; sub = 'The Nano, the 185 V converter, four К155ИД1, the MCP23017, six optocouplers and the RTC. Its parts face the rear panel; its seven socket strips face the display.';
    rows = [['Size', size('DRV')], ['Finish', 'black soldermask, white silkscreen, ENIG (board stackup)'],
      ['Parts', `${n(b.parts)} fitted + ${n(b.dnp)} DNP (the bleed pairs R33–R44), all through-hole`],
      ['Tracks', `${n(b.tracks)}: 369 laid by hand, the rest by negotiated routing (0 unrouted)`],
      ['Vias', `<span class="pill ${b.vias ? 'bad' : 'ok'}">${b.vias}</span>`],
      ['Copper', `${n('6663 mm')}, ${n('1.32×')} its floor`],
      ['KiCad DRC', pillDRC(b.drc, [0, 2, 0]) + '<br><span style="color:var(--muted);font-size:12.5px">2 accepted: the Nano’s silk past the edge with its USB. (The VT21 and XS1 library mismatches this note once listed are no longer reported.)</span>'],
      ['Mate check', '<span class="pill ok">[]</span> 63 strip pins (59 carry a net) land on their pins with the same net; all 4 standoffs have holes'],
      ['185 V gaps', '<span class="pill ok">clean</span> at 0.6 mm (HV net class)'],
      isPop('TS06-DRV') ? popBodies('TS06-DRV') : ['3D bodies', `${n(b.bodies)} of ${n(b.parts + b.dnp)} from KiCad's library; ${b.no_body.map(esc).join(', ') || 'none'} drawn as proxies`]];
    note = isPop('TS06-DRV') ? 'Drawn populated, as the bench builds it: the DIP chips in their sockets, the Nano on its strips, the RTC module on its header, L1, the МЛТ resistors and the fuse. The bring-up steps fit each part stage by stage. Sizes marked inferred in 3d/populated/README.md are not measured.'
      : 'Grey DIP sockets are empty in KiCad’s export: the chips drawn on them here are proxies, and the bring-up steps fit them stage by stage.';
  } else if (s === 'DISP') {
    const b = B('DISP');
    name = 'TS06-DISP · display board'; sub = 'Four ИН-12, two ИН-17 for the seconds, two ИН-15, two ИНС-1 colon lamps and nine addressable LEDs. Nothing but the tubes and their wiring; seven pin strips on the back.';
    rows = [['Size', size('DISP')], ['Finish', 'black soldermask, white silkscreen, ENIG (board stackup)'],
      ['Parts', `${n(b.parts)} fitted, all through-hole`], ['Tracks', `${n(b.tracks)}, all drawn by hand`],
      ['Vias', `<span class="pill ${b.vias ? 'bad' : 'ok'}">${b.vias}</span>`], ['Copper', `${n('2108 mm')}, ${n('1.14×')} its floor`],
      ['Tube pitch', `the Gyver pitch; the seconds pair ${n('20.5 mm')} apart for their Ø20 stems`],
      ['KiCad DRC', pillDRC(b.drc, [2, 0, 0]) + '<br><span style="color:var(--muted);font-size:12.5px">0 unconnected; 2 errors, accepted (colon lamp courtyards overlap M10 by 0.135 mm; a test fit settles it)</span>'],
      ['185 V gaps', '<span class="pill ok">clean</span> at 0.6 mm'],
      isPop('TS06-DISP') ? popBodies('TS06-DISP') : ['3D bodies', `${n(b.bodies)} of ${n(b.parts)} (the strips). Tubes, lamps, LEDs and socket contacts are proxies from the case model’s envelopes`]];
    note = (isPop('TS06-DISP') ? 'Drawn populated: six ИН-12/15 on their socket contacts, two ИН-17 on wire leads, two ИНС-1, nine LEDs. The glass is the repo’s STEP files; the ИН-17 glass is the 19.72 mm the owner measured on a bench tube (the STEP scaled to it), with a pip of about 2.28 mm under it (a reading, not measured), seated level with the ИН-12 faces. ' : '') + 'The LED return BL_K exists only as a ground pour: refill the zones (B) before judging or plotting the board.';
  } else if (s === 'FASCIA') {
    const b = B('FASCIA'), v = V.fv, d = fvData(v), row = VARIANT_ROWS[v] || {};
    const bad = (d.fascia_checks || []).filter(r => r.status !== 'OK' && r.status !== 'NOTE');
    name = `${BOARD.FASCIA} · fascia ${FV_NAME[v]}`;
    sub = 'The printed product face under the tubes: the MODE rotary, two levers and two buttons. Surface-mount on the back, so no solder shows from the front. It joins TS06-DRV J1 on a 6-way JST PH lead.';
    rows = [['Variant', `${esc(FV_NAME[v])}${v === 'R' ? ' <span class="pill acc">recommended</span>' : ''} · the owner chooses (see <b>Fascia variants</b> below)`],
      ['Size', size('FASCIA')], ['Finish', v === 'R' && isPop(BOARD.FASCIA) ? 'black soldermask, white silkscreen, ENIG, 2.0 mm (the board’s own stack-up). The gold is copper under openings in the mask' : 'black soldermask, white silkscreen, ENIG (PCB/README.md). The board file has no stackup of its own; this build adds one for the renders'],
      ['Tracks', `${n(b.tracks)}`], ['Vias', `<span class="pill ${b.vias ? 'bad' : 'ok'}">${b.vias}</span>`],
      ['Position', `${n('FASCIA_X0 = ' + d.X0)}, raked ${n(f.FASCIA_RAKE + '°')}`],
      ['Controls vs tubes', esc(row.controls || '')],
      ['KiCad DRC', pillDRC(b.drc, [0, 0, 0])],
      ['Case checks', bad.length ? bad.map(r => `<span class="pill ${r.status === 'FAIL' ? 'bad' : 'warn'}">${esc(r.status)}</span> ${esc(r.what)}`).join('<br>') : '<span class="pill ok">no fascia row TIGHT or FAIL</span>'],
      ['Lead path', n(d.lead_path + ' mm')], ['Area, cost', esc(row.cost || '')], ['Reach', esc(row.reach || '')]];
    const dep = r => ((d.bodies || []).find(b => b[0] === r) || [])[5];
    if (isPop(BOARD.FASCIA)) rows.splice(2, 0, ['As ordered', `drawn with the Plates print (white names and nameplates) and the <b>${esc((POP.gold || 'divider').replace(/^./, c => c.toUpperCase()))} gold</b>, the board <code>fab/TS06-FASCIA-R-revA-divider-fab.zip</code> is made from; ${popBodies(BOARD.FASCIA)[1]}`]);
    note = isPop(BOARD.FASCIA) ? 'The dial, the two МТ1 levers and the two КМД1 buttons are drawn with their bodies behind the panel and their bushings in the holes; the eight 1206 resistors and the JST header are on the back. The gold shows as yellow in KiCad’s pictures and in the 3D view as a metallic gold.' :
      `Control bodies behind the panel are proxies with the case model’s depths: rotary Ø${((d.bodies || [])[0] || [])[3]} × ${dep('SW1')} mm, МТ1 ${dep('SW2')} mm, КМД1 ${dep('SW4')} mm.` + (v === 'F' ? ' F: the 176 board stands in for the 179 panel the frame needs; that board is not drawn yet.' : '');
    if (!isPop(BOARD.FASCIA) && Object.keys(POP.boards || {}).length) note += ' Only the fascia R is drawn populated, with its gold; A and W are the bare boards.';
  } else {
    const c = MODEL.checks || {};
    name = 'Assembly · 3d/case-pair'; sub = 'Both boards, the fascia and the case, placed where the case model puts them. Z runs from the ИН-12 glass front backwards.';
    rows = [['Outside', n(`${f.OUT_W} × ${f.OUT_H} × ${f.OUT_D.toFixed(1)} mm`)],
      ['Stack', `glass front Z 0 → TS06-DISP ${n('Z ' + f.Z_DISP_F)} → ${n(f.STACK_GAP + ' mm')} gap → TS06-DRV ${n('Z ' + f.Z_DRV_F + '–' + f.Z_DRV_B)}, parts towards the rear panel at ${n('Z ' + f.Z_REAR_IN)}`],
      ['Driver', `mirrored: DRV x = ${f.BOARD_W} − DISP x; its top edge ${n(f.DRV_Y0 + ' mm')} above the display's`],
      ['Fascia', `${esc(FV_NAME[V.fv])} (${esc(BOARD.FASCIA)}) at ${n('FASCIA_X0 ' + fvData(V.fv).X0)}, raked ${n(f.FASCIA_RAKE + '°')}, top edge on the sill at ${n('Y ' + f.SILL_TOP_Y)}`],
      ['Fascia lead', `path ${n(fvData(V.fv).lead_path + ' mm')} for a ${n(f.LEAD_LEN + ' mm')} lead (BOM 180–200 mm)`],
      ['Case checks', Object.entries(fvData(V.fv).checks || c).map(([k, v]) => `<span class="pill ${k === 'OK' ? 'ok' : k === 'FAIL' ? 'bad' : k === 'TIGHT' ? 'warn' : 'acc'}">${v} ${esc(k)}</span>`).join(' ') + '<br><span style="color:var(--muted);font-size:12.5px">Two FAILs are the rejected jack openings, kept on record' + (V.fv === 'A' ? '; one is open: the fascia boss on R5' : '') + '.</span>']];
    note = isPop('TS06-DRV') ? 'The boards are drawn populated (3d/populated): every part has its body, and the fascia R carries its gold. The tubes are the repo’s STEP files; the case parts are the case model’s.'
      : 'The tubes are drawn from the case model’s envelopes (ИН-12/ИН-15 19.47 × 28.86 × 25.5, ИН-17 face 14 × 20 on a Ø20 stem, ИНС-1 Ø6.97), in warm glass.';
  }
  el.innerHTML = `<h2>${esc(name)}</h2><div class="sub">${esc(sub)}</div><dl>${rows.map(r => `<dt>${r[0]}</dt><dd>${r[1]}</dd>`).join('')}</dl><div class="note">${esc(note)}</div>`;
}

// ------------------------------------------------------------------------------------------ sections
function panZoom(host, img) {
  const st = { s: 1, x: 0, y: 0 }, ptr = new Map();
  let base = null;
  const apply = () => { img.style.transform = `translate(${st.x}px, ${st.y}px) scale(${st.s})`; };
  const fit = () => {
    const W = host.clientWidth, H = host.clientHeight, w = img.naturalWidth || 800, h = img.naturalHeight || 600;
    img.style.width = w + 'px'; img.style.height = h + 'px';
    st.s = Math.min(W / w, H / h) * 0.96; st.x = (W - w * st.s) / 2; st.y = (H - h * st.s) / 2; apply();
  };
  const zoomAt = (f, cx, cy) => {
    const ns = THREE.MathUtils.clamp(st.s * f, 0.05, 40);
    st.x = cx - (cx - st.x) * ns / st.s; st.y = cy - (cy - st.y) * ns / st.s; st.s = ns; apply();
  };
  host.addEventListener('wheel', e => { e.preventDefault(); const r = host.getBoundingClientRect(); zoomAt(Math.exp(-e.deltaY * 0.0015), e.clientX - r.left, e.clientY - r.top); }, { passive: false });
  host.addEventListener('pointerdown', e => { host.setPointerCapture(e.pointerId); ptr.set(e.pointerId, [e.clientX, e.clientY]); base = null; });
  host.addEventListener('pointermove', e => {
    if (!ptr.has(e.pointerId)) return;
    const prev = ptr.get(e.pointerId);
    ptr.set(e.pointerId, [e.clientX, e.clientY]);
    if (ptr.size === 1) { st.x += e.clientX - prev[0]; st.y += e.clientY - prev[1]; apply(); }
    else if (ptr.size === 2) {
      const [a, b] = [...ptr.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
      const r = host.getBoundingClientRect(), cx = (a[0] + b[0]) / 2 - r.left, cy = (a[1] + b[1]) / 2 - r.top;
      if (base) zoomAt(d / base, cx, cy);
      base = d;
    }
  });
  const up = e => { ptr.delete(e.pointerId); base = null; };
  host.addEventListener('pointerup', up); host.addEventListener('pointercancel', up);
  host.addEventListener('dblclick', e => { const r = host.getBoundingClientRect(); zoomAt(2, e.clientX - r.left, e.clientY - r.top); });
  host.addEventListener('keydown', e => {
    const W = host.clientWidth / 2, H = host.clientHeight / 2;
    if (e.key === '+' || e.key === '=') zoomAt(1.25, W, H); else if (e.key === '-') zoomAt(0.8, W, H); else if (e.key === '0') fit();
    else if (e.key.startsWith('Arrow')) { const d = { ArrowLeft: [40, 0], ArrowRight: [-40, 0], ArrowUp: [0, 40], ArrowDown: [0, -40] }[e.key]; st.x += d[0]; st.y += d[1]; apply(); }
    else return;
    e.preventDefault();
  });
  img.addEventListener('load', fit);
  if (img.complete && img.naturalWidth) fit();
  return { fit, zoomIn: () => zoomAt(1.4, host.clientWidth / 2, host.clientHeight / 2), zoomOut: () => zoomAt(1 / 1.4, host.clientWidth / 2, host.clientHeight / 2), st };
}
let SEC = 0;
function renderSections() {
  const list = SECTIONS.sections || [];
  $('#secnote').innerHTML = SECTIONS.source === 'stub'
    ? `<div class="caution stubnote"><b>Stub.</b> The schematic sections are still being drawn. Until <code>sch/out/sections.json</code> exists, this tab shows ${list.length} sections generated from the netlist (<code>tools/ts06pair.py</code>): a parts list in place of the schematic sheet, and a generated layout map. The next build picks up the real ones.</div>` : '';
  if (!list.length) { $('#seclist').innerHTML = '<p>No sections yet.</p>'; return; }
  SEC = Math.min(SEC, list.length - 1);
  $('#seclist').innerHTML = list.map((s, i) => `<button type="button" class="secbtn" role="tab" id="sec-${esc(s.id)}" data-i="${i}" aria-selected="${i === SEC}">${esc(s.title)}<small>${esc((s.boards || []).join(' + '))} · ${(s.parts || []).length} parts</small></button>`).join('');
  const s = list[SEC];
  const pane = (kind, files, cls) => files && files.length ? `<div class="pane"><div class="panehead"><span>${kind}${files.length > 1 ? ` <select data-pz="${kind}" aria-label="${kind} page">${files.map((f, i) => `<option value="${i}">${esc(f.split('/').pop())}</option>`).join('')}</select>` : ''}</span>
      <span class="pztools"><button type="button" data-act="out" aria-label="Zoom out">−</button><button type="button" data-act="in" aria-label="Zoom in">+</button><button type="button" data-act="fit">Fit</button></span></div>
      <div class="pz ${cls}" tabindex="0" aria-label="${kind}: drag to pan, scroll or pinch to zoom"><img alt="${esc(s.title)}, ${kind.toLowerCase()}" src="${esc(files[0])}" draggable="false"></div></div>` : '';
  const boardsOf = (s.boards || []).map(b => Object.keys(BOARD).find(k => BOARD[k] === b)).filter(Boolean);
  $('#secdetail').innerHTML = `<h2>${esc(s.title)}</h2><p style="max-width:78ch">${esc(s.summary || '')}</p>
    <div class="stepnav"><button type="button" class="btn primary" id="sec3d">Show in 3D</button></div>
    <div class="chips" aria-label="Parts">${(s.parts || []).map(r => `<button type="button" class="chip" data-ref="${esc(r)}">${esc(r)}</button>`).join('')}</div>
    <div class="chips" aria-label="Nets">${(s.nets || []).map(n => `<span class="chip net">${esc(n)}</span>`).join('')}</div>
    ${(s.nets || []).includes('A6') ? '<p style="font-size:13.5px" id="sec-ladlink">The panel end of this link, the two resistor ladders on A6 and A7, is <button type="button" class="linkbtn" data-goto="ladders">below this list</button>; the panel itself is in <button type="button" class="linkbtn" data-goto="panel">Front panel</button>.</p>' : ''}
    <div class="secpanes">${pane('Schematic', s.schematic, '')}${pane('Layout', s.layout, 'dark')}</div>`;
  $$('#secdetail .pane').forEach(p => {
    const pz = panZoom($('.pz', p), $('img', p));
    $$('.pztools button', p).forEach(b => b.addEventListener('click', () => ({ in: pz.zoomIn, out: pz.zoomOut, fit: pz.fit })[b.dataset.act]()));
    const sel = $('select', p);
    if (sel) sel.addEventListener('change', () => { const kind = sel.dataset.pz; $('img', p).src = (kind === 'Schematic' ? s.schematic : s.layout)[+sel.value]; });
  });
  $('#sec3d').addEventListener('click', () => showSection(s, boardsOf));
  $$('#secdetail .chip[data-ref]').forEach(c => c.addEventListener('click', () => showSection(Object.assign({}, s, { parts: [c.dataset.ref] }), boardsOf, true)));
}
function sectionKeys(s, boards) {
  const keys = [];
  for (const r of s.parts || []) {
    const qual = r.includes(':') ? [r] : boards.filter(k => PARTS[BOARD[k]].parts[r]).map(k => k + ':' + r);
    for (const q of (qual.length ? qual : [])) {
      const [k, ref] = q.split(':');
      const root = V.roots.asm;
      if (root && root.refs.has(k + ':' + ref + '#chip')) keys.push({ key: k + ':' + ref + '#chip', label: ref });
      else if (root && root.refs.has(k + ':' + ref + '#module')) keys.push({ key: k + ':' + ref + '#module', label: ref });
      else keys.push({ key: q });
    }
  }
  return keys;
}
function showSection(s, boards, single) {
  const keys = sectionKeys(s, boards);
  const scene = boards.length === 1 ? boards[0] : 'asm';
  goStep(-1, { noCamera: true });
  if (scene === 'asm') setExplode(0.65);
  setScene(scene, { keepCamera: true });
  setMode('3d');
  V.caseOn = false; $('#caseon').checked = false; applyVisibility();
  highlight(keys);
  $('#viewer').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
  const b = hlBox();
  const allBack = keys.length && keys.every(k => { const [bk, r] = k.key.split(':'); const p = PARTS[BOARD[bk]] && PARTS[BOARD[bk]].parts[(r || '').replace(/#.*/, '')]; return p && p.side === 'B'; });
  const dir = scene === 'asm' ? (keys.some(k => k.key.startsWith('DRV')) ? 'isoBL' : 'isoL') : (allBack ? 'back' : 'front');
  frameBox(b.isEmpty() || !single ? visibleBox(V.roots[scene].group) : b, dir, single ? 3 : 1);
}

// ------------------------------------------------------------------------------------------ fascia variants
// Key rows of PCB/TS06-FASCIA-variants.md (measured there, 30.09.26)
const VARIANT_ROWS = {
  A: { board: 'PCB/TS06-FASCIA', size: '176 × 40', where: 'X 4.3–180.3, on the middle of H10 and ИН-15А', controls: 'SW1 −2.3 (H1) · SW2 −9.3 (S10) · SW3 −6.8 (S1) · SW4 −0.1 (ИН-15Б) · SW5 −3.1 (ИН-15А)',
       r5: ['bad', 'FAIL −1.2 mm: the boss lands on R5'], sw5: ['warn', 'TIGHT 1.2 / 2.6 mm'], sill: ['warn', 'TIGHT, the sill needs a notch'], slots: '4.8 mm left, 11.6 mm right: TS06-DRV shows', lead: '139 mm', cost: '7040 mm²', reach: 'one hand' },
  W: { board: 'PCB/TS06-FASCIA-wide', size: '191.4 × 40', where: 'X 0–191.4, cheek to cheek', controls: '+1.1 · −5.9 · −3.4 · +3.3 · +0.3 (same layout, translated)',
       r5: ['ok', 'OK 6.5 mm'], sw5: ['ok', 'OK 8.4 / 7.2 mm'], sill: ['warn', 'TIGHT (notch)'], slots: 'none', lead: '142 mm', cost: '7656 mm², +8.75 %, about +70–90 ₽', reach: 'one hand' },
  R: { board: 'PCB/TS06-FASCIA-rhythm', size: '191.4 × 40', where: 'X 0–191.4, cheek to cheek', controls: '0 for all five: dial under the hours pair, FIELD/SUB under M10/M1, − / + under the ИН-15s',
       r5: ['ok', 'OK 1.7 mm'], sw5: ['ok', 'OK 9.2 / 8.4 mm'], sill: ['ok', 'OK, no notch'], slots: 'none', lead: '138 mm', cost: '7656 mm², +8.75 %, about +60–90 ₽', reach: 'two hands: 86 mm from FIELD to −' },
  F: { board: 'case model only (FASCIA_FRAME=1); renders in 3d/case-pair/variant-D', size: 'a 179 × 40 panel in a printed frame', where: 'X 3.0–182.0, the trench window', controls: 'as A',
       r5: ['ok', 'OK 1.86 mm (the frame’s fixing)'], sw5: ['ok', 'no fixing there; 1.0 / 2.6 mm to the top rail'], sill: ['warn', 'as A (notch)'], slots: 'none: 1.3 / 1.7 mm round the stand-in; a 179 panel fits with 0.02 mm a side (TIGHT: draw it 178.6)', lead: 'as A', cost: 'a printed frame, and a new 178.6–179 board with its top holes over the ribs', reach: 'one hand' },
};
let VARIANTS = { pictures: [], frame: 'in progress' };
function renderVariants() {
  const keys = ['A', 'W', 'R', 'F'];
  const head = k => `<th>${esc(FV_NAME[k])}${k === 'R' ? ' <span class="pill acc">recommended</span>' : ''}${k === 'F' ? ` <span class="pill ${VARIANTS.frame === 'rendered' ? 'acc' : 'warn'}">${VARIANTS.frame === 'rendered' ? 'case model only' : esc(VARIANTS.frame)}</span>` : ''}</th>`;
  const cell = v => Array.isArray(v) ? `<span class="pill ${v[0]}">${esc(v[1])}</span>` : esc(v);
  const rows = [['Board', 'board'], ['Size (mm)', 'size'], ['Where', 'where'], ['Controls vs the tube above (mm)', 'controls'], ['Fascia boss vs R5', 'r5'],
    ['SW5 vs the top-right boss', 'sw5'], ['Rotary vs the sill', 'sill'], ['Open slots where TS06-DRV shows', 'slots'], ['Lead path', 'lead'], ['Area, cost', 'cost'], ['Reach', 'reach']];
  const pics = VARIANTS.pictures || [];
  $('#fvouter').textContent = `${F().OUT_W} × ${F().OUT_H} × ${F().OUT_D.toFixed(1)} mm`;
  $('#fvtable').innerHTML = `<thead><tr><th></th>${keys.map(head).join('')}</tr></thead><tbody>${rows.map(([l, k]) => `<tr><th>${esc(l)}</th>${keys.map(v => `<td>${cell(VARIANT_ROWS[v][k])}</td>`).join('')}</tr>`).join('')}
    <tr><th>In 3D</th>${keys.map(v => `<td><button type="button" class="linkbtn" data-fv3d="${v}"${PARTS[FV[v]] ? '' : ' disabled'}>Show ${v} in the case</button></td>`).join('')}</tr></tbody>`;
  const sel = $('#fvpic');
  if (!pics.length) { $('#fvpics').hidden = true; return; }
  sel.innerHTML = pics.map((p, i) => `<option value="${i}">${esc(p.label)}</option>`).join('');
  const img = $('#fvimg');
  img.src = pics[0].src; img.alt = pics[0].label;
  $('#fvfrom').textContent = pics[0].from;
  if (!V.fvpz) {
    V.fvpz = panZoom($('#fvpz'), img);
    $$('#fvpane .pztools button').forEach(b => b.addEventListener('click', () => ({ in: V.fvpz.zoomIn, out: V.fvpz.zoomOut, fit: V.fvpz.fit })[b.dataset.act]()));
    sel.addEventListener('change', () => { const p = pics[+sel.value]; img.src = p.src; img.alt = p.label; $('#fvfrom').textContent = p.from; });
  }
}

// ------------------------------------------------------------------------------------------ test tab, notes
function renderTestStages() {
  const bench = STEPS.map((s, i) => [s, i]).filter(([s]) => s.g === 'bench');
  $('#stagelist').innerHTML = bench.map(([s, i]) => `<li><div><h3>${esc(s.title)}${s.hv ? ' <span class="pill bad">185 V</span>' : ''}</h3>${s.body}<button type="button" class="linkbtn" data-step="${i}">Show this stage in 3D</button></div></li>`).join('');
}
function renderNotes() {
  const d = FACTS.boards;
  const pop = Object.keys(POP.boards || {}).length > 0;
  const mb = b => ((POP.boards[b] || {}).published_bytes / 1048576).toFixed(1);
  const rows = [
    ...(pop ? [['The boards drawn populated', `TS06-DRV, TS06-DISP and the fascia R are the GLBs of <code>3d/populated/</code>, with every component: the DIP chips in their sockets, the Nano on its strips, the six ИН-12/15, the two ИН-17, the colon lamps and LEDs, the dial, levers and buttons. They are quantised (gltfpack, 16-bit positions) and embedded in glTF JSON because the host serves no .glb: ${['TS06-DRV', 'TS06-DISP', 'TS06-FASCIA-rhythm'].filter(isPop).map(b => `${b.replace('TS06-', '')} ${mb(b)} MB`).join(', ')} as published. No copper tracks are in them (they lie under the black mask). The fascia R is drawn <b>as ordered</b>: the Plates print and the Divider gold.`]] : []),
    ['Black boards with white silkscreen', 'Each board’s own stackup: the GLB export and <code>kicad-cli pcb render --use-board-stackup-colors</code>. TS06-DRV and TS06-DISP carry black mask and white silk; TS06-FASCIA’s file has no stackup, so the build adds the one PCB/README.md orders (2.0 mm, black, white, ENIG) to a scratch copy.'],
    ['Tracks faintly under the mask, gold pads', 'KiCad’s copper, pads and zones, exported after the pours were refilled (the committed files store no fill).'],
    ['Parts with KiCad bodies', `TS06-DRV ${d['TS06-DRV'].bodies}, TS06-DISP ${d['TS06-DISP'].bodies}, TS06-FASCIA ${d['TS06-FASCIA'].bodies}. Their glTF nodes are named by reference (U11, XS21, …), which is how a step or a section finds them.`],
    ...(pop ? [['Stand-in bodies', 'Only on the boards that are not populated, the fascia variants A and W: control bodies from the case model’s depths. The populated boards need none, so the build and bring-up steps show and hide the parts’ own bodies.']] : []),
    ['Every other part', 'Found by its footprint in the <code>.kicad_pcb</code>: position, pads and courtyard, read by the build (<code>data/parts.json</code>). A part with no body gets a proxy (below) or, when highlighted, a thin box on its courtyard.'],
    ...(pop ? [] : [['Warm glass tubes', 'Proxies from the case model’s envelopes: ИН-12/ИН-15 19.47 × 28.86 × 25.5 mm on a 4.5 mm socket seat, ИН-17 face 14 × 20 on a Ø20 stem, 19.72 mm of glass (measured) on a 10.28 mm seat, ИНС-1 Ø6.97. The glowing numerals are decoration.']]),
    ...(pop ? [] : [['Chips, the Nano, the RTC module, F1', 'Proxies. KiCad draws empty DIP sockets; the chip bodies on them are placed from the pads and the socket’s height so the bring-up steps can fit them. The Nano and the MF-RG1100 fuse have no model in the library used here.'],
    ['Socket contacts and LEDs', 'Proxies at the footprints’ pads: 12 contacts under each socketed tube, 3 mm LEDs 5.3 mm tall.']]),
    ['Standoffs, screws, the fascia lead', 'From the case model: nylon M3 × 11 mm at the display’s four holes, the module screws at TS06-DRV H5–H8, the lead along its centre line.'],
    ['The case', 'The printable parts from <code>3d/case-pair/out/*.stl</code> (cheeks, brow, top plate, trench, base, rear panel, and the fascia frame for F), where the case model places them. The cheeks are the default build, with the fascia bosses A, W and R use.'],
    ['Fascia A, W, R and F', 'A, W and R are their own boards, exported like the others and placed at the case model’s X0 for each (4.305, 0, 0). F is the case model’s printed frame with A’s 176 board standing in for the 179 panel it needs.'],
  ];
  $('#notesbody').innerHTML = rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('');
}

// ------------------------------------------------------------------------------------------ order
// What is ready to order, from data/order.json (tools/order.py: fab/ORDER.md, the zips on disk, the fit table).
// Placing the order is the owner's own hand: nothing here contacts a fab; the zips are links, not embedded.
const kB = b => b >= 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.round(b / 1024) + ' kB';
function renderOrder() {
  const el = $('#orderbody');
  if (!el) return;
  if (!ORDER) { el.innerHTML = '<div class="card"><p>The order data was not built (<code>data/order.json</code>).</p></div>'; return; }
  const O = ORDER, t = O.fit.tally;
  const gold = (O.fit.gold || 'none').replace(/^./, c => c.toUpperCase());
  const boards = O.boards.map(b => `<article class="card ob" data-board="${esc(b.short)}">
      <div class="tag">${esc(b.short)}</div>
      <h3>${esc(b.name)}</h3>
      <img src="img/${esc(b.picture)}.png" alt="${esc(b.short)}, populated, seen from the front" loading="lazy">
      <dl class="obrows">
        <dt>Size</dt><dd>${esc(b.size)}</dd>
        <dt>Layers</dt><dd>${b.layers}</dd>
        <dt>Thickness</dt><dd>${esc(b.thickness)}${/2\.0/.test(b.thickness) ? ' <span class="pill acc">not 1.6: say so on the quote</span>' : ''}</dd>
        <dt>Finish</dt><dd>${esc(b.finish)}</dd>
        <dt>Colour</dt><dd>mask ${esc(b.mask)}; silk ${esc(b.silk)}</dd>
        <dt>Holes</dt><dd>${esc(b.holes.plated)} plated, ${esc(b.holes.non_plated)} non-plated</dd>
        <dt>Quantity</dt><dd><b>${b.qty}</b></dd>
        <dt>DFM check</dt><dd><span class="pill ok">${esc(b.dfm)}</span></dd>
        <dt>Zip</dt><dd><a href="${esc(b.url)}" target="_blank" rel="noopener"><code>${esc(b.zip)}</code></a> · ${kB(b.zip_bytes)}</dd>
      </dl></article>`).join('');
  const dfm = `<table id="order-dfm-table"><thead><tr>${O.dfm.cols.map((c, i) => `<th${i ? ' class="n"' : ''}>${esc(c || 'Rule (limit)')}</th>`).join('')}</tr></thead><tbody>${
    O.dfm.rows.map(r => `<tr>${r.map((c, i) => `<td${i ? ' class="n"' : ''}>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  const fit = `<table id="order-fit-table"><thead><tr><th>Reading</th><th>Where</th><th>What it says, in plain words</th><th class="n">Margin</th></tr></thead><tbody>${
    O.fit.rows.map(r => `<tr class="fit-${r.status.toLowerCase()}"><td><span class="pill ${r.status === 'FAIL' ? 'bad' : 'warn'}">${esc(r.status)}</span></td>
      <td>${esc(r.board)}, ${esc(r.side)}<br><span class="sm">${esc(r.part)}</span></td><td>${esc(r.plain)}</td><td class="n">${r.margin > 0 ? '+' : ''}${r.margin.toFixed(2)} mm</td></tr>`).join('')}</tbody></table>`;
  const open = O.open.map(o => `<li data-open="${esc(o.id)}"><span class="pill ${o.blocking ? 'warn' : 'acc'}">${o.blocking ? 'before you order' : 'does not hold the order'}</span> <b>${esc(o.title)}.</b> ${esc(o.body)}</li>`).join('');
  const zips = O.boards.map(b => `<tr><td>${esc(b.short)}</td><td><a href="${esc(b.url)}" target="_blank" rel="noopener"><code>${esc(b.zip)}</code></a></td><td class="n">${kB(b.zip_bytes)}</td><td>${esc(b.layers)} layers, ${esc(b.thickness)}, ${esc(b.finish)}</td></tr>`).join('');
  el.innerHTML = `
    <p class="lead">${esc(O.status)} Quantity <b>${O.quantity} of each board</b>, a prototype run. The fascia is shown as ordered: the Plates print and the <b>${esc(gold)} gold</b>.</p>
    <div class="card ownhand" id="order-ownhand"><div class="tag">Whose hand</div><p><b>${esc(O.own_hand)}</b></p></div>
    <h2 class="osec">What is ready, board by board</h2>
    <div class="grid3" id="order-boards">${boards}</div>
    <h2 class="osec">Design-for-manufacture check</h2>
    <p class="olede">The worst value the check found on each board, against the limit in brackets. ${esc(O.dfm_note)}</p>
    <div class="tablewrap card" style="padding:0 4px" id="order-dfm">${dfm}</div>
    <h2 class="osec">Fit table</h2>
    <p class="olede">How tall each part is, as drawn, against the room the case gives it (<code>3d/populated/fit-table.md</code>). <span class="pill ok">${t.PASS || 0} PASS</span> has a millimetre or more to spare.
      <span class="pill warn">${t.TIGHT || 0} TIGHT</span> fits as drawn with less than a millimetre. <span class="pill bad">${t.FAIL || 0} FAIL</span> is more than 0.25 mm over: the drawing says it would not fit. Only the rows that are not PASS are listed.</p>
    <div class="tablewrap card" style="padding:0 4px" id="order-fit">${fit}</div>
    <h2 class="osec">Open before ordering</h2>
    <ul class="openlist" id="order-open">${open}</ul>
    <details class="card" id="order-proto"><summary>What only the prototype run can close (${O.prototype.length})</summary><ul>${O.prototype.map(x => `<li>${esc(x)}</li>`).join('')}</ul></details>
    <h2 class="osec">Where the fab zips are</h2>
    <p class="olede">One zip per board, on GitHub, branch <code>${esc(O.branch)}</code>. They are links, not part of this page: download them there and upload one zip to the board house for each board.</p>
    <div class="tablewrap card" style="padding:0 4px" id="order-zips"><table><thead><tr><th>Board</th><th>File in the repository</th><th class="n">Size</th><th>Holds</th></tr></thead><tbody>${zips}</tbody></table></div>
    <p class="sm" style="margin-top:10px">Source: <code>${esc(O.source)}</code>, read when this page was built.</p>`;
}

// ------------------------------------------------------------------------------------------ front panel
// Moved 30.09.26 from two older pages, kept as they were: A1 = TS06-FASCIA Panel Drawing (rev A,
// 08.09.26), A2 = TS06-FASCIA Reference (09.09.26). The old text is in index.html (#doc-panel, #ladders);
// here are A1's script-built parts (the dial explainer, the panel drawing, the two ladder diagrams), ported
// with their geometry unchanged, and the checks against today's board, read from data/facts.json and
// data/parts.json so they follow the board files when the fascia changes. Marks: seen / computed / inferred.
const FPB = { A: 'TS06-FASCIA', W: 'TS06-FASCIA-wide', R: 'TS06-FASCIA-rhythm' };
const MK = { seen: 'seen', comp: 'computed', inf: 'inferred' };
const mk = k => `<span class="mk ${k}">${MK[k]}</span>`;
const SVGNS = 'http://www.w3.org/2000/svg';
const svgEl = (t, a) => { const e = document.createElementNS(SVGNS, t); for (const k in a) e.setAttribute(k, a[k]); return e; };
// A1's dial: six positions 30° apart, the arc opening right, position 1 at 75° (its CX, CY, SPAN, START)
const A1D = { CX: 30, CY: 26, SPAN: 30, START: 75 };
const a1ang = i => (A1D.START - A1D.SPAN * i) * Math.PI / 180;
const a1px = (r, i) => A1D.CX + r * Math.cos(a1ang(i));
const a1py = (r, i) => A1D.CY - r * Math.sin(a1ang(i));
const A1POS = [   // A1's POS, word for word
  { n: 'Normal', lede: 'A safe parking position. Nothing is read, so a knock does nothing. The ИН-15 pair idle-cycles its symbol set here.', field: null, sub: null, btn: null },
  { n: 'Set Time', lede: 'The only screen where a wrong input costs you the time on the clock.', field: 'Hour ↔ Minute', sub: null, btn: 'Adjusts the selected field' },
  { n: 'Display', lede: 'Digit brightness, the transitions between digits, and how often the glitch fires — three settings on two levers.', field: 'Brightness ↔ Effects', sub: 'Transition ↔ Glitch', subnote: 'read only while FIELD = Effects', btn: 'Adjusts the selected setting. Glitch runs off at the bottom of its range' },
  { n: 'Ambient', lede: 'The two light sources that are not digits.', field: 'Colon ↔ Backlight', sub: null, btn: "Cycles that item's styles" },
  { n: 'Format / Date', lede: 'Two different kinds of setting on one screen — a binary toggle and a multi-field value.', field: 'Format ↔ Date', sub: 'Day-Month ↔ Year', subnote: 'read only while FIELD = Date', btn: "Format: flips 12h/24h. Date: adjusts SUB's selection" },
  { n: 'Info', lede: 'Read-only glance screen. Every input is ignored on purpose — and it is now an end stop, so the knob cannot be knocked past it into anything live.', field: null, sub: null, btn: null },
];
const A1LABEL = ['NORMAL', 'SET TIME', 'DISPLAY', 'AMBIENT', 'FORMAT/DATE', 'INFO'];
const A2NETS = [   // A2 §03, word for word
  ['Power & ground', [
    ['+5V', 'SW1.6, R5.1, R6.1, J1.1', 'Rail for both resistor ladders and the connector. Pin 1 on J1 — first on the cable, on purpose.'],
    ['GND', 'SW1.1, SW4.1, SW5.1, R1.2, R7.2, R8.2, J1.2', "Poured across the whole back face rather than traced — seven pads scattered edge to edge is exactly what a plane is for. See §05 for why that almost didn't work."]]],
  ['Position sensing (analog)', [
    ['A6', 'SW1.7, J1.3', 'MODE rotary wiper. Off-board on J1 pin 3.'],
    ['TAP2–TAP5', 'SW1.2–.5, R1–R5 chain', 'Internal ladder nodes only — never leave the board. They exist purely to give the rotary something to land on between GND and +5V.'],
    ['A7', 'R6.2, SW2.2, SW3.2, R6–R8 junction, J1.4', 'Shared read for both levers. Off-board on J1 pin 4.'],
    ['LEVA / LEVB', 'SW2.1↔R7.1 · SW3.1↔R8.1', 'Internal-only names for each lever-to-resistor junction — a routing label, not a signal the MCU sees separately from A7.']]],
  ['Buttons (digital)', [
    ['D7', 'SW4.2 (−), J1.5', 'Normally open, shorts to GND on press. MCU-side pull-up (GyverButton, INPUT_PULLUP) — nothing extra needed here.'],
    ['D8', 'SW5.2 (+), J1.6', 'Same as D7, other button.']]],
];
// A1's back-side placement ("x-ray"), as its script drew it: parts, landing pads, J1 box
const A1BACK = { R: [['R1', 58, 10], ['R2', 58, 18], ['R3', 58, 26], ['R4', 58, 34], ['R5', 58, 42], ['R7', 95, 44], ['R8', 118, 44], ['R6', 106.5, 10]], J1: [147, 10] };

const fpBoard = v => FACTS.boards[FPB[v]];
const fpSize = v => { const b = fpBoard(v); return b ? `${+b.size[0]} × ${+b.size[1]}` : 'not built'; };
const ohms = v => { const m = /^([\d.]+)([kKM]?)(\d*)$/.exec(String(v).trim()); if (!m) return NaN; const mul = { '': 1, k: 1e3, K: 1e3, M: 1e6 }[m[2]]; return parseFloat(m[1] + (m[3] ? '.' + m[3] : '')) * mul; };
function fpLadderCodes(b) {        // the codes today's resistor values give (computed), or null if a part is missing
  const P = (PARTS[b] || {}).parts || {}, r = k => ohms((P[k] || {}).v);
  const R = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8'].map(r);
  if (R.some(x => !(x > 0))) return null;
  const tot = R.slice(0, 5).reduce((a, x) => a + x, 0);
  let below = 0; const a6 = [0];
  for (let i = 0; i < 5; i++) { below += R[i]; a6.push(Math.round(1023 * below / tot)); }   // R1 is the GND end
  const par = (x, y) => x * y / (x + y), dv = g => Math.round(1023 * g / (g + R[5]));
  return { raw: ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8'].map(k => P[k].v), a6, a7: [1023, dv(R[6]), dv(R[7]), dv(par(R[6], R[7]))] };
}
function fpTodayFacts(v) {
  const b = fpBoard(v), P = (PARTS[FPB[v]] || {}).parts || {}, n = x => `<span class="num">${x}</span>`;
  if (!b) return '<dt>Board</dt><dd>not in this build</dd>';
  const j = P.J1 || {};
  return [['Board', `<code>PCB/${esc(FPB[v])}</code>${v === 'A' ? ' <span class="pill acc">committed</span>' : ''}`],
    ['Outline', n(fpSize(v) + ' mm') + `, ${n((+b.thickness).toFixed(1) + ' mm')} FR4`],
    ['Copper', `${n(b.tracks)} tracks, all on B.Cu; ${n(b.vias)} vias`],
    ['Parts', `${n(b.parts)}: R1–R8, SW1–SW5, J1`],
    ['J1', `${esc(j.fp || '?').replace('TS06_', '')} on the ${j.side === 'B' ? 'back' : 'front'}, at ${n((j.at || []).slice(0, 2).join(', '))}`],
    ['Finish', '2.0 mm FR4, black mask, white silk, ENIG (PCB/README.md)']]
    .map(r => `<dt>${r[0]}</dt><dd>${r[1]}</dd>`).join('') + `<dt>Checked</dt><dd>${mk('seen')} this page’s build, from the board file</dd>`;
}
let FPV = 'A';
function fpShowToday(v) {
  FPV = FACTS.boards[FPB[v]] ? v : 'A';
  $$('#fp-fvseg button').forEach(b => b.setAttribute('aria-pressed', b.dataset.fp === FPV));
  const f = $('#fp-front'), k = $('#fp-back');
  f.src = `img/${FPB[FPV]}-top.png`; f.alt = `${FPB[FPV]}, front, KiCad render`;
  k.src = `img/${FPB[FPV]}-bottom.png`; k.alt = `${FPB[FPV]}, back, KiCad render`;
  $('#fp-todayfacts').innerHTML = fpTodayFacts(FPV);
}
const fpTodayName = () => `today’s TS06-FASCIA, ${fpSize('A')} mm (board A, the committed one; its height was compressed from 52 to 40 mm in 2026-09)`;
const fpOpenChoice = () => `Which fascia is built is still the owner’s open choice: A, W or R (${fpSize('W')} mm), or F, a 179 × 40 panel in a printed frame (PCB/TS06-FASCIA-variants.md).`;

// ---- the dial explainer (A1's "What the controls do")
function fpDialSVG() {
  const s = svgEl('svg', { viewBox: '10 5 70 43', role: 'img', 'aria-label': 'The MODE dial' });
  s.innerHTML = `<defs><linearGradient id="dxgold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFC46B"/><stop offset=".5" stop-color="#FF9E36"/><stop offset="1" stop-color="#C87515"/></linearGradient>
    <linearGradient id="dxknob" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A3F44"/><stop offset="1" stop-color="#191C1F"/></linearGradient></defs>`;
  const tg = svgEl('g', {}), ng = svgEl('g', {}), wg = svgEl('g', {});
  tg.appendChild(svgEl('path', { d: `M ${a1px(13.9, 0)} ${a1py(13.9, 0)} A 13.9 13.9 0 0 1 ${a1px(13.9, 5)} ${a1py(13.9, 5)}`, fill: 'none', stroke: '#4A5057', 'stroke-width': '.25' }));
  for (let i = 0; i < 6; i++) {
    tg.appendChild(svgEl('line', { x1: a1px(11.6, i), y1: a1py(11.6, i), x2: a1px(13.9, i), y2: a1py(13.9, i), stroke: '#DCD8D0', 'stroke-width': '.55', 'stroke-linecap': 'round' }));
    const nt = svgEl('text', { x: a1px(16.4, i), y: a1py(16.4, i) + 1.05, 'font-family': 'IBM Plex Mono, monospace', 'font-size': '3', fill: 'url(#dxgold)', 'text-anchor': 'middle' });
    nt.textContent = String(i + 1); ng.appendChild(nt);
    const wt = svgEl('text', { x: 52, y: a1py(16.4, i) + 1.0, 'font-family': 'Saira Condensed, Arial Narrow, sans-serif', 'font-size': '3.4', 'letter-spacing': '.28', fill: '#DCD8D0', 'data-w': i });
    wt.textContent = A1LABEL[i]; wg.appendChild(wt);
    wg.appendChild(svgEl('line', { x1: a1px(18.3, i), y1: a1py(16.4, i), x2: 50.6, y2: a1py(16.4, i), stroke: '#4A5057', 'stroke-width': '.22' }));
  }
  s.append(tg, ng, wg);
  s.appendChild(svgEl('circle', { cx: 30, cy: 26, r: 4.4, fill: '#000' }));
  const knob = svgEl('g', { id: 'fp-knob' });
  knob.appendChild(svgEl('circle', { cx: 30, cy: 26, r: 9.2, fill: 'url(#dxknob)', stroke: '#4A5057', 'stroke-width': '.35' }));
  knob.appendChild(svgEl('path', { d: 'M30 18.4 L31.15 21.2 L28.85 21.2 Z', fill: '#F25610' }));
  knob.appendChild(svgEl('rect', { x: 29.55, y: 21.4, width: .9, height: 3.2, fill: '#F25610', opacity: '.75' }));
  s.appendChild(knob);
  s.appendChild(svgEl('circle', { cx: 30, cy: 26, r: 1.5, fill: '#0C0D0E', stroke: '#4A5057', 'stroke-width': '.3' }));
  return s;
}
let FPPOS = 0;
function fpSelect(i) {
  FPPOS = i; const p = A1POS[i];
  $$('#fp-poslist .posbtn').forEach((b, k) => b.setAttribute('aria-pressed', k === i));
  $('#fp-posname').textContent = p.n;
  $('#fp-poslede').textContent = p.lede;
  const fill = (id, val, note) => {
    const box = $(id), v = $('.v', box);
    box.classList.toggle('off', !val); box.classList.toggle('live', !!val);
    v.textContent = val ? val + (note ? ' — ' + note : '') : 'not read';
  };
  fill('#fp-c-field', p.field); fill('#fp-c-sub', p.sub, p.subnote); fill('#fp-c-btn', p.btn);
  const rot = 90 - (A1D.START - A1D.SPAN * i);                 // the pointer art starts pointing up
  const k = $('#fp-knob'); if (k) k.setAttribute('transform', `rotate(${rot} 30 26)`);
  $$('#fp-dialpic [data-w]').forEach(w => { const on = +w.dataset.w === i; w.setAttribute('fill', on ? '#FFFFFF' : '#DCD8D0'); w.setAttribute('opacity', on ? '1' : '.62'); });
}

// ---- A1's panel drawing, front and back, by its own drawing code (ids prefixed a1)
function fpA1Front() {
  const s = svgEl('svg', { viewBox: '-10 -10 196 76', role: 'img', 'aria-label': 'TS06-FASCIA front face, 176 by 52 millimetres (A1, rev A, history)' });
  s.innerHTML = `<defs>
    <linearGradient id="a1mask" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#141618"/><stop offset="1" stop-color="#08090A"/></linearGradient>
    <linearGradient id="a1gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFC46B"/><stop offset=".5" stop-color="#FF9E36"/><stop offset="1" stop-color="#C87515"/></linearGradient>
    <linearGradient id="a1knobg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3A3F44"/><stop offset="1" stop-color="#191C1F"/></linearGradient></defs>
    <rect x="0" y="0" width="176" height="52" rx="1.5" fill="url(#a1mask)" stroke="#33383D" stroke-width=".3"/>
    <g fill="#000" stroke="#3A4045" stroke-width=".25"><circle cx="4.5" cy="4.5" r="1.35"/><circle cx="171.5" cy="4.5" r="1.35"/><circle cx="4.5" cy="47.5" r="1.35"/><circle cx="171.5" cy="47.5" r="1.35"/></g>
    <g><g class="a1ticks"></g><g class="a1nums"></g><g class="a1words"></g>
      <circle cx="30" cy="26" r="4.4" fill="#000"/>
      <g transform="rotate(15 30 26)"><circle cx="30" cy="26" r="9.2" fill="url(#a1knobg)" stroke="#4A5057" stroke-width=".35"/>
        <path d="M30 18.4 L31.15 21.2 L28.85 21.2 Z" fill="#F25610"/><rect x="29.55" y="21.4" width=".9" height="3.2" fill="#F25610" opacity=".75"/></g>
      <circle cx="30" cy="26" r="1.5" fill="#0C0D0E" stroke="#4A5057" stroke-width=".3"/></g>
    <g class="a1levers"></g><g class="a1buttons"></g>
    <text x="6.5" y="6.4" font-family="Saira Condensed, Arial Narrow, sans-serif" font-size="2.5" letter-spacing=".55" fill="#8C8880">MODE</text>
    <g stroke="#4A5057" stroke-width=".22" fill="none"><path d="M0 58 L176 58"/><path d="M0 55.6 L0 60.4"/><path d="M176 55.6 L176 60.4"/><path d="M181 0 L181 52"/><path d="M178.6 0 L183.4 0"/><path d="M178.6 52 L183.4 52"/></g>
    <rect x="79" y="55.6" width="18" height="4.8" fill="#0f1113"/>
    <text x="88" y="59.4" font-family="IBM Plex Mono, monospace" font-size="3.1" fill="#8C8880" text-anchor="middle">176.00</text>
    <text x="181" y="26" font-family="IBM Plex Mono, monospace" font-size="3.1" fill="#8C8880" text-anchor="middle" transform="rotate(-90 181 26)">52.00</text>`;
  const tg = $('.a1ticks', s), ng = $('.a1nums', s), wg = $('.a1words', s);
  for (let i = 0; i < 6; i++) {
    tg.appendChild(svgEl('line', { x1: a1px(11.6, i), y1: a1py(11.6, i), x2: a1px(13.9, i), y2: a1py(13.9, i), stroke: '#DCD8D0', 'stroke-width': '.55', 'stroke-linecap': 'round' }));
    const nt = svgEl('text', { x: a1px(16.4, i), y: a1py(16.4, i) + 1.05, 'font-family': 'IBM Plex Mono, monospace', 'font-size': '3', fill: 'url(#a1gold)', 'text-anchor': 'middle' });
    nt.textContent = String(i + 1); ng.appendChild(nt);
    const wt = svgEl('text', { x: 52, y: a1py(16.4, i) + 1.0, 'font-family': 'Saira Condensed, Arial Narrow, sans-serif', 'font-size': '3.4', 'letter-spacing': '.28', fill: i === 0 ? '#FFFFFF' : '#DCD8D0', opacity: i === 0 ? '1' : '.62' });
    wt.textContent = A1LABEL[i]; wg.appendChild(wt);
    wg.appendChild(svgEl('line', { x1: a1px(18.3, i), y1: a1py(16.4, i), x2: 50.6, y2: a1py(16.4, i), stroke: '#4A5057', 'stroke-width': '.22' }));
  }
  tg.insertBefore(svgEl('path', { d: `M ${a1px(13.9, 0)} ${a1py(13.9, 0)} A 13.9 13.9 0 0 1 ${a1px(13.9, 5)} ${a1py(13.9, 5)}`, fill: 'none', stroke: '#4A5057', 'stroke-width': '.25' }), tg.firstChild);
  const lg = $('.a1levers', s);
  [[95, 'FIELD'], [118, 'SUB']].forEach(([x, name]) => {
    lg.appendChild(svgEl('circle', { cx: x, cy: 26, r: 4, fill: '#000' }));
    lg.appendChild(svgEl('circle', { cx: x, cy: 26, r: 6.6, fill: 'none', stroke: '#4A5057', 'stroke-width': '.3' }));
    lg.appendChild(svgEl('path', { d: `M ${x - 1.4} 24.6 L ${x + 1.4} 19.4 L ${x + 3.1} 20.6 L ${x + 0.5} 25.6 Z`, fill: '#2E3338', stroke: '#565C63', 'stroke-width': '.3' }));
    const t = svgEl('text', { x, y: 38.4, 'font-family': 'Saira Condensed, Arial Narrow, sans-serif', 'font-size': '3.6', 'letter-spacing': '.4', fill: '#DCD8D0', 'text-anchor': 'middle', 'font-weight': '600' });
    t.textContent = name; lg.appendChild(t);
  });
  // the gold traces from the SUB box to positions 3 and 5, and the enable stub under FIELD (A1's code)
  const g2 = svgEl('g', {}), ytx = i => a1py(16.4, i) + 1.0, y3 = ytx(2), y5 = ytx(4), BX = 108, BR = 128, BT = 17, BB = 41;
  const gold = { fill: 'none', stroke: 'url(#a1gold)', 'stroke-width': '.45', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' };
  g2.appendChild(svgEl('path', Object.assign({ d: `M ${BX} 34.2 L 95 34.2 L 95 32.6` }, gold)));
  g2.appendChild(svgEl('circle', { cx: 95, cy: 32.6, r: '.85', fill: 'url(#a1gold)' }));
  g2.appendChild(svgEl('rect', { x: BX, y: BT, width: BR - BX, height: BB - BT, rx: '2.2', fill: 'none', stroke: 'url(#a1gold)', 'stroke-width': '.45' }));
  g2.appendChild(svgEl('path', Object.assign({ d: `M 118 ${BT} L 118 11 L ${65 + (11 - y3) * -1} 11 L 65 ${y3}` }, gold)));
  g2.appendChild(svgEl('path', Object.assign({ d: `M 118 ${BB} L 118 45 L ${71 + (45 - y5)} 45 L 71 ${y5}` }, gold)));
  g2.appendChild(svgEl('circle', { cx: 65, cy: y3, r: '.85', fill: 'url(#a1gold)' }));
  g2.appendChild(svgEl('circle', { cx: 71, cy: y5, r: '.85', fill: 'url(#a1gold)' }));
  lg.insertBefore(g2, lg.firstChild);
  const bg = $('.a1buttons', s);
  [[146, '−'], [164, '+']].forEach(([x, ch]) => {
    bg.appendChild(svgEl('circle', { cx: x, cy: 26, r: 4, fill: '#000' }));
    bg.appendChild(svgEl('circle', { cx: x, cy: 26, r: 6.6, fill: 'none', stroke: '#4A5057', 'stroke-width': '.3' }));
    bg.appendChild(svgEl('circle', { cx: x, cy: 26, r: 3, fill: '#22262A', stroke: '#565C63', 'stroke-width': '.3' }));
    const t = svgEl('text', { x, y: 39.2, 'font-family': 'Saira Condensed, Arial Narrow, sans-serif', 'font-size': '6.4', fill: 'url(#a1gold)', 'text-anchor': 'middle', 'font-weight': '700' });
    t.textContent = ch; bg.appendChild(t);
  });
  return s;
}
function fpA1Back() {
  const s = svgEl('svg', { viewBox: '-10 -10 196 76', role: 'img', 'aria-label': 'TS06-FASCIA back side placement, drawn as seen from the front (A1, rev A, history)' });
  s.innerHTML = `<rect x="0" y="0" width="176" height="52" rx="1.5" fill="#0E1012" stroke="#33383D" stroke-width=".3"/>
    <g fill="#000" stroke="#3A4045" stroke-width=".25"><circle cx="4.5" cy="4.5" r="1.35"/><circle cx="171.5" cy="4.5" r="1.35"/><circle cx="4.5" cy="47.5" r="1.35"/><circle cx="171.5" cy="47.5" r="1.35"/></g>
    <circle cx="30" cy="26" r="12.5" fill="none" stroke="#F25610" stroke-width=".3" stroke-dasharray="1.6 1.2" opacity=".8"/>
    <text x="30" y="41.6" font-family="IBM Plex Mono, monospace" font-size="2.3" fill="#B4562A" text-anchor="middle">∅25.00 BODY KEEPOUT</text>
    <circle cx="30" cy="26" r="4.4" fill="#000" stroke="#3A4045" stroke-width=".25"/>
    <g class="bh"></g><g class="bp"></g><g class="bpad"></g>
    <text x="88" y="6.2" font-family="Saira Condensed, Arial Narrow, sans-serif" font-size="3" letter-spacing=".4" fill="#6C6F72" text-anchor="middle">BACK-SIDE PLACEMENT, DRAWN AS SEEN FROM THE FRONT (X-RAY)</text>`;
  const bh = $('.bh', s), bp = $('.bp', s), bpad = $('.bpad', s), mono = 'IBM Plex Mono, monospace';
  [95, 118, 146, 164].forEach(x => bh.appendChild(svgEl('circle', { cx: x, cy: 26, r: 4, fill: '#000', stroke: '#3A4045', 'stroke-width': '.25' })));
  const part = (x, y, label, w = 9) => {
    bp.appendChild(svgEl('rect', { x: x - w / 2, y: y - 1.6, width: w, height: 3.2, fill: '#1E2225', stroke: '#5E646A', 'stroke-width': '.28', rx: '.3' }));
    bp.appendChild(svgEl('circle', { cx: x - w / 2, cy: y, r: .75, fill: '#B9932F' }));
    bp.appendChild(svgEl('circle', { cx: x + w / 2, cy: y, r: .75, fill: '#B9932F' }));
    const t = svgEl('text', { x, y: y - 2.9, 'font-family': mono, 'font-size': '2.2', fill: '#9C9890', 'text-anchor': 'middle' }); t.textContent = label; bp.appendChild(t);
  };
  ['R1 4k7', 'R2 4k7', 'R3 4k7', 'R4 4k7', 'R5 4k7'].forEach((l, i) => part(58, 10 + i * 8, l));
  part(95, 44, 'R7 20k'); part(118, 44, 'R8 10k'); part(106.5, 10, 'R6 10k');
  const pads = (x, y, n, lbl) => {
    for (let i = 0; i < n; i++) bpad.appendChild(svgEl('circle', { cx: x + (i - (n - 1) / 2) * 2.6, cy: y, r: 1.05, fill: '#0B0C0D', stroke: '#B9932F', 'stroke-width': '.4' }));
    const t = svgEl('text', { x, y: y + 3.9, 'font-family': mono, 'font-size': '2.1', fill: '#9C9890', 'text-anchor': 'middle' }); t.textContent = lbl; bpad.appendChild(t);
  };
  pads(30, 44.5, 7, 'SW1 COM + T1..T6');
  pads(95, 33.5, 2, 'SW2'); pads(118, 33.5, 2, 'SW3'); pads(146, 33.5, 2, 'SW4'); pads(164, 33.5, 2, 'SW5');
  bpad.appendChild(svgEl('rect', { x: 139, y: 7, width: 16, height: 6, fill: '#1E2225', stroke: '#5E646A', 'stroke-width': '.3', rx: '.4' }));
  for (let j = 0; j < 6; j++) bpad.appendChild(svgEl('circle', { cx: 141.5 + j * 2.5, cy: 10, r: .8, fill: '#0B0C0D', stroke: '#B9932F', 'stroke-width': '.35' }));
  const jt = svgEl('text', { x: 147, y: 5.4, 'font-family': mono, 'font-size': '2.2', fill: '#9C9890', 'text-anchor': 'middle' });
  jt.textContent = 'J1  GND +5V A6 A7 D7 D8'; bpad.appendChild(jt);
  return s;
}
// A2 §01, its one static drawing, word for word (its colours are A2's own tokens, see .a2fig)
const A2FRONT = `<svg viewBox="-6 -6 188 64" style="width:100%; height:auto; display:block;" role="img" aria-label="TS06-FASCIA front panel diagram (A2, history)">
  <rect x="0" y="0" width="176" height="52" rx="2.5" fill="var(--mask)" stroke="var(--panel-line)" stroke-width="0.6"/>
  <circle cx="4.5" cy="4.5" r="1.35" fill="none" stroke="var(--silk-dim)" stroke-width="0.4"/><circle cx="171.5" cy="4.5" r="1.35" fill="none" stroke="var(--silk-dim)" stroke-width="0.4"/>
  <circle cx="4.5" cy="47.5" r="1.35" fill="none" stroke="var(--silk-dim)" stroke-width="0.4"/><circle cx="171.5" cy="47.5" r="1.35" fill="none" stroke="var(--silk-dim)" stroke-width="0.4"/>
  <circle cx="30" cy="26" r="17" fill="none" stroke="var(--silk-dim)" stroke-width="0.35"/><circle cx="30" cy="26" r="8" fill="var(--panel-line)"/>
  <path d="M 33.6 12.57 A 13.9 13.9 0 0 1 33.6 39.43" fill="none" stroke="var(--gold)" stroke-width="1"/>
  <text x="20" y="8" font-size="3.6" fill="var(--silk)" font-weight="600">MODE</text>
  <g font-size="3.1" fill="var(--silk)">
    <text x="34.5" y="13.4">1</text><text x="40" y="13.4">— NORMAL</text><text x="37.5" y="18.5">2</text><text x="43" y="18.5">— SET TIME</text>
    <text x="39" y="24.8">3</text><text x="44.5" y="24.8">— DISPLAY</text><text x="39" y="30.2">4</text><text x="44.5" y="30.2">— AMBIENT</text>
    <text x="37.5" y="35.8">5</text><text x="43" y="35.8">— FORMAT/DATE</text><text x="34.5" y="40.6">6</text><text x="40" y="40.6">— INFO</text></g>
  <circle cx="95" cy="26" r="4.2" fill="var(--panel-line)"/><rect x="88.6" y="19.6" width="12.8" height="18.8" rx="3" fill="none" stroke="var(--gold)" stroke-width="0.7"/>
  <circle cx="118" cy="26" r="4.2" fill="var(--panel-line)"/><rect x="111.6" y="19.6" width="12.8" height="18.8" rx="3" fill="none" stroke="var(--gold)" stroke-width="0.7"/>
  <text x="95" y="43.5" font-size="3" fill="var(--silk)" text-anchor="middle">FIELD</text><text x="118" y="43.5" font-size="3" fill="var(--silk)" text-anchor="middle">SUB</text>
  <path d="M 89.5 20.5 L 78.5 11.5" stroke="var(--gold)" stroke-width="0.5" fill="none"/><path d="M 91 32.5 L 78.5 32.5" stroke="var(--gold)" stroke-width="0.5" fill="none"/>
  <path d="M 100.5 32.5 L 113.5 32.5" stroke="var(--gold)" stroke-width="0.5" fill="none"/><path d="M 101 20.5 L 111.5 12" stroke="var(--gold)" stroke-width="0.5" fill="none"/>
  <circle cx="146" cy="26" r="4.2" fill="var(--panel-line)"/><circle cx="164" cy="26" r="4.2" fill="var(--panel-line)"/>
  <text x="146" y="43.5" font-size="4" fill="var(--gold)" text-anchor="middle">−</text><text x="164" y="43.5" font-size="4" fill="var(--gold)" text-anchor="middle">+</text>
  <g font-size="2.6" fill="var(--silk-dim)">
    <text x="30" y="50.5" text-anchor="middle">SW1 · SR25 rotary · A6</text><text x="95" y="6" text-anchor="middle">SW2 · LEVER A</text>
    <text x="118" y="6" text-anchor="middle">SW3 · LEVER B</text><text x="155" y="6" text-anchor="middle">SW4/SW5 · D7/D8</text></g></svg>`;

// ---- A1's two ladder diagrams (for Circuit sections), by its own drawing code
function fpLadderA6() {
  const s = svgEl('svg', { viewBox: '0 0 330 206', role: 'img', 'aria-label': 'Five 4.7k resistors in series from plus 5 volts to ground, with six taps' }), mono = 'IBM Plex Mono, monospace';
  s.innerHTML = `<g stroke="#4A5057" stroke-width="1.4" fill="none"><path d="M110 20 L110 170"/><path d="M110 20 L96 20 M96 14 L96 26"/></g>
    <text x="88" y="24" fill="#DCD8D0" font-family="${mono}" font-size="11" text-anchor="end">+5V</text>
    <g stroke="#4A5057" stroke-width="1.4" fill="none"><path d="M100 176 L120 176 M104 181 L116 181 M108 186 L112 186"/><path d="M110 170 L110 176"/></g>
    <g class="a6r"></g><g class="a6taps"></g>
    <path d="M243 95 L176 110" stroke="#F25610" stroke-width="1.6" fill="none"/><circle cx="243" cy="95" r="3.4" fill="#F25610"/>
    <path d="M176 110 L184 105 L184 116 Z" fill="#F25610"/>
    <path d="M232 42 A 62 62 0 0 1 232 148" stroke="#F25610" stroke-width="1" fill="none" stroke-dasharray="3 4" opacity=".55"/>
    <text x="250" y="99" fill="#F25610" font-family="${mono}" font-size="11">wiper</text>
    <text x="250" y="112" fill="#7C7972" font-family="${mono}" font-size="10">→ A6</text>`;
  const a6r = $('.a6r', s), a6t = $('.a6taps', s), NODEY = [20, 50, 80, 110, 140, 170];   // node 0 = +5V end, node 5 = GND end
  for (let r = 0; r < 5; r++) {
    const cy = (NODEY[r] + NODEY[r + 1]) / 2;
    a6r.appendChild(svgEl('rect', { x: 99, y: cy - 11, width: 22, height: 22, fill: '#1A1E21', stroke: '#5E646A', 'stroke-width': '1.3' }));
    const rl = svgEl('text', { x: 92, y: cy + 4, fill: '#DCD8D0', 'font-family': mono, 'font-size': '10', 'text-anchor': 'end' }); rl.textContent = 'R' + (5 - r) + ' 4k7'; a6r.appendChild(rl);
  }
  for (let t = 0; t < 6; t++) {
    const y = NODEY[t], posn = 6 - t, volts = (5 - t).toFixed(2), code = [1023, 818, 614, 409, 205, 0][t];
    a6t.appendChild(svgEl('path', { d: 'M110 ' + y + ' L168 ' + y, stroke: '#4A5057', 'stroke-width': '1.2', fill: 'none' }));
    a6t.appendChild(svgEl('circle', { cx: 110, cy: y, r: '2.6', fill: '#B9932F' }));
    const pl = svgEl('text', { x: 176, y: y + 4, 'font-family': mono, 'font-size': '10.5', fill: '#DCD8D0' });
    pl.textContent = posn + '   ' + volts + ' V   ' + code; a6t.appendChild(pl);
  }
  return s;
}
function fpLadderA7() {
  const s = svgEl('svg', { viewBox: '0 0 330 206', role: 'img', 'aria-label': 'A 10k pull-up on A7, with 20k and 10k switched to ground by the two levers' }), mono = 'IBM Plex Mono, monospace';
  s.innerHTML = `<g stroke="#4A5057" stroke-width="1.4" fill="none"><path d="M150 16 L150 34"/><path d="M150 16 L136 16 M136 10 L136 22"/>
      <path d="M150 66 L150 96"/><path d="M78 96 L232 96"/><path d="M78 96 L78 116"/><path d="M232 96 L232 116"/>
      <path d="M78 146 L78 156"/><path d="M232 146 L232 156"/><path d="M78 188 L78 196"/><path d="M232 188 L232 196"/></g>
    <text x="128" y="20" fill="#DCD8D0" font-family="${mono}" font-size="11" text-anchor="end">+5V</text>
    <rect x="139" y="34" width="22" height="32" fill="#1A1E21" stroke="#5E646A" stroke-width="1.3"/>
    <text x="168" y="54" fill="#DCD8D0" font-family="${mono}" font-size="11">R6 10k</text>
    <circle cx="150" cy="96" r="3.4" fill="#FF9E36"/>
    <text x="150" y="86" fill="#FF9E36" font-family="${mono}" font-size="11" text-anchor="middle">A7</text>
    <g class="a7sw"></g>
    <rect x="67" y="156" width="22" height="32" fill="#1A1E21" stroke="#5E646A" stroke-width="1.3"/>
    <text x="55" y="176" fill="#DCD8D0" font-family="${mono}" font-size="11" text-anchor="end">R7 20k</text>
    <rect x="221" y="156" width="22" height="32" fill="#1A1E21" stroke="#5E646A" stroke-width="1.3"/>
    <text x="255" y="176" fill="#DCD8D0" font-family="${mono}" font-size="11">R8 10k</text>
    <g stroke="#4A5057" stroke-width="1.4" fill="none"><path d="M68 196 L88 196 M72 200 L84 200"/><path d="M222 196 L242 196 M226 200 L238 200"/></g>`;
  const a7 = $('.a7sw', s);
  [[78, 'FIELD'], [232, 'SUB']].forEach(([x, name]) => {
    a7.appendChild(svgEl('circle', { cx: x, cy: 116, r: '3', fill: '#0E1012', stroke: '#5E646A', 'stroke-width': '1.3' }));
    a7.appendChild(svgEl('circle', { cx: x, cy: 146, r: '3', fill: '#0E1012', stroke: '#5E646A', 'stroke-width': '1.3' }));
    a7.appendChild(svgEl('path', { d: `M ${x + 2} 118 L ${x + 13} 143`, stroke: '#5E646A', 'stroke-width': '1.4', fill: 'none', 'stroke-linecap': 'round' }));
    const t = svgEl('text', { x, y: 108, 'font-family': 'Saira Condensed, Arial Narrow, sans-serif', 'font-size': '11', 'letter-spacing': '1', fill: '#7C7972', 'text-anchor': 'middle' });
    t.textContent = name; a7.appendChild(t);
  });
  return s;
}

// ---- where the old pages disagree with today, and the then-and-now table
function fpDiffs() {
  const P = (PARTS[FPB.A] || {}).parts || {}, at = r => P[r] ? `${+P[r].at[0]}, ${+P[r].at[1]}` : '?';
  const rows = [...'12345'].map(i => P['R' + i]).filter(Boolean), ys = [...new Set(rows.map(p => +p.at[1]))], xs = rows.map(p => +p.at[0]);
  const r15 = ys.length === 1 ? `in a row at y ${ys[0]}, x ${Math.min(...xs)}–${Math.max(...xs)}` : 'at ' + [...'12345'].map(i => 'R' + i + ' ' + at('R' + i)).join('; ');
  return [
    ['outline', `<b>Outline.</b> Both old pages draw the board 176 × 52 mm. Today’s board A is ${fpSize('A')} mm: its height was compressed in 2026-09 by moving the parts, tracks, pour and legend up 12 mm, with no re-route. W and R are ${fpSize('W')} and ${fpSize('R')} mm, and the choice between them is still open. ${mk('seen')}`],
    ['j1', `<b>Connector.</b> A1 says “1 × JST-XH, 6 way” and letters J1 “GND +5V A6 A7 D7 D8”. A2 and today say JST PH, pin 1 +5V, 2 GND, 3 A6, 4 A7, 5 D7, 6 D8 (PCB/README.md fixes the order for both builds). Here the two old pages disagree with each other, and A2 is the one that still holds. ${mk('seen')}`],
    ['back', `<b>Back-side placement.</b> A1’s x-ray drawing puts R1–R5 in a column at x 58, R6 at 106.5, 10, R7 and R8 at y 44 and J1 top right. On today’s board A they sit ${r15}; R6 at ${at('R6')}, R7 at ${at('R7')}, R8 at ${at('R8')}, J1 at ${at('J1')} (board mm). ${mk('seen')}`],
    ['dial', `<b>Dial lettering.</b> The old drawings letter the dial for the 52 mm board. Today’s lettering was scaled by 0.789 in the compression and MODE moved to the left of the shaft; the angles did not change (positions at 75° down to −75°, 30° apart). ${mk('seen')} ${mk('comp')}`],
    ['silk', `<b>Silkscreen.</b> A1 says white silk “front only”. Today the back silkscreen carries J1’s pin legend. ${mk('seen')}`],
    ['firmware', `<b>The controls, in the firmware.</b> A1’s dial explainer is control scheme rev B, the spec. The firmware does not do it yet: <code>ts06pair.ino</code> reads SET TIME as PROGRAM and the other five positions as RUN, does not read A7, and keeps the ИН-15 pair dark, so NORMAL’s idle cycle is not written. ${mk('seen')}`],
    ['drv', `<b>The driver-board end.</b> A1 names two 100 nF caps there; they are still there (C5, C6 on TS06-DRV). Rev B added R72, 1 M from A6 to ground, and 1 k with 10 nF on D7 and D8, so J1’s pins 5 and 6 are D7_J and D8_J on that board. With R72 the middle taps read up to 3.4 codes low; the firmware rounds with ±102 codes to spare. ${mk('seen')} ${mk('comp')}`],
    ['routing', `<b>Routing notes.</b> A2’s 64 tracks and the R6 story are board A’s, and W’s, which is A’s tracks moved. R was placed and routed anew: ${fpBoard('R') ? fpBoard('R').tracks : '?'} tracks, ${fpBoard('R') ? fpBoard('R').vias : '?'} vias. ${mk('seen')}`],
    ['cable', `<b>Cable length.</b> A1 argues from “a metre of cable”. Today’s lead is 180–200 mm (TS06-DRV bom.md). ${mk('seen')} The argument for switching to ground holds all the same. ${mk('inf')}`],
  ];
}
function fpThenNow() {
  const A = fpBoard('A') || {}, pill = (c, t) => `<span class="pill ${c}">${t}</span>`;
  const cur = pill('ok', 'current'), chg = pill('warn', 'changed since'), hist = pill('bad', 'history: superseded'), unk = pill('acc', 'not checked');
  const J = ((PARTS[FPB.A] || {}).parts || {}).J1 || {};
  return [
    ['A1, A2', 'Outline', '176.00 × 52.00 mm', `${fpSize('A')} mm (A); W and R ${fpSize('W')} mm ${mk('seen')}`, hist + ` by ${fpTodayName()}`],
    ['A1', 'Stack', '2.0 mm FR4, 2 layer', `${(+A.thickness).toFixed(1)} mm FR4, 2 layers ${mk('seen')}`, cur],
    ['A2', 'Stack', '2.0mm FR4, 2-layer, ENIG', 'the same, ENIG (PCB/README.md) ' + mk('seen'), cur],
    ['A1', 'Mask', 'Matte black', 'black (PCB/README.md; “matte” is not written there) ' + mk('seen'), cur],
    ['A1', 'Silk', 'White, front only', 'white; the back silk carries J1’s pin legend ' + mk('seen'), chg],
    ['A2', 'Finish', 'Black mask · white silk', 'the same ' + mk('seen'), cur],
    ['A1', 'Finish', 'ENIG — gold accents', 'ENIG; the gold artwork is F.Cu under opened mask ' + mk('seen'), cur],
    ['A2', 'Signal routing', 'B.Cu only, 0 vias', `A: ${A.tracks} tracks on B.Cu, ${A.vias} vias ${mk('seen')}`, cur],
    ['A1', 'Interface', '1 × JST-XH, 6 way', `JST PH: ${esc((J.fp || '').replace('TS06_JST_PH_', '').replace('_Back', ''))} on the back ${mk('seen')}`, hist + ' by the JST PH J1'],
    ['A2', 'Off-board', '6-pin JST-PH to main board', 'a 6-way JST PH lead, 180–200 mm, to TS06-DRV’s J1; the main board is now the pair’s driver board ' + mk('seen'), cur],
    ['A1', 'Parts', '8 R · 5 SW · 1 J', `${A.parts} parts: R1–R8, SW1–SW5, J1 ${mk('seen')}`, cur],
    ['A1', 'Rev', 'A · 2026-09-08', 'compressed to 40 mm in 2026-09; two leftovers fixed 30.09.26 (PCB/README.md) ' + mk('seen'), hist + ` by ${fpTodayName()}`],
    ['A1', 'Order', 'Rezonit order, 15 off', 'PCB/README.md: the fascia goes to Rezonit with the electronics; the count is not in the repository', unk],
    ['A2', 'Build', 'for the surface-mount build', 'TS06-FASCIA is the surface-mount build chosen for fabrication; TS06-FASCIA-THT (176 × 52) stays as the alternative ' + mk('seen'), cur],
    ['A2', 'Full render', 'PCB/TS06-FASCIA/preview.svg', 'still made there by tools/render.py; this page shows KiCad renders of the board file instead (above) ' + mk('seen'), cur],
  ];
}
function renderPanel() {
  // today's board
  const v0 = V.fv in FPB ? V.fv : 'A';
  fpShowToday(v0);
  // disagreements
  $('#fp-difflist').innerHTML = fpDiffs().map(([k, t]) => `<li data-d="${k}">${t}</li>`).join('');
  // dial explainer
  $('#fp-poslist').innerHTML = A1LABEL.map((l, i) => `<button type="button" class="posbtn" data-pos="${i}" aria-pressed="${i === 0}"><span class="n">${i + 1}</span><span>${esc(l)}</span></button>`).join('');
  $('#fp-dialpic').replaceChildren(fpDialSVG());
  fpSelect(FPPOS);
  // hardware check
  $('#fp-hwcheck').innerHTML = `${mk('seen')} Today’s board drills the rotary 8.8 mm and the МТ1 and КМД1 8.0 mm, and its body ring reads “BODY 25.00”. The bushing length, shaft and plunger are not in the board file ${mk('inf')}.`;
  // nets, with a live check that every part named still exists on board A
  const P = (PARTS[FPB.A] || {}).parts || {};
  $('#fp-netbody').innerHTML = A2NETS.map(([g, rows]) => `<div class="netgroup"><h3>${esc(g)}</h3>${rows.map(([n, p, w]) => `<div class="netrow" data-net="${esc(n)}"><div class="nn">${esc(n)}</div><div class="np">${esc(p)}</div><div class="nw">${esc(w)}</div></div>`).join('')}</div>`).join('');
  const named = [...new Set(A2NETS.flatMap(g => g[1].map(r => r[1])).join(' ').match(/\b(SW\d|R\d|J\d)\b/g))];
  const missing = named.filter(r => !P[r]);
  $('#fp-netcheck').innerHTML = (missing.length ? `<span class="pill bad">changed since</span> not on today’s board A: ${missing.map(esc).join(', ')}. ` : `${mk('seen')} Current. Every pad above, read pad by pad from today’s board A (30.09.26), carries the net named, and no other pad does; the ${named.length} parts named are all on the board in this build. `)
    + `The firmware’s buttons are GButton HIGH_PULL, which is INPUT_PULLUP ${mk('seen')}. Since A2, TS06-DRV rev B puts 1 k in series and 10 nF to ground on D7 and D8 at its end (R73, R74, C18, C19), and 1 M from A6 to ground (R72) ${mk('seen')}.`;
  // routing
  const b = k => fpBoard(k) || {};
  $('#fp-routecheck').innerHTML = `${mk('seen')} Current for board A: ${b('A').tracks} tracks, ${b('A').vias} vias, all signal copper on B.Cu, one GND pour on B.Cu; PCB/README.md tells the same R6 story. W is A’s ${b('W').tracks} tracks moved across. R was placed and routed anew (${b('R').tracks} tracks, ${b('R').vias} vias), so the corridor story is not R’s.`;
  // then and now
  $('#fp-tntable').innerHTML = '<thead><tr><th>From</th><th>Item</th><th>The old page says</th><th>Today</th><th>Status</th></tr></thead><tbody>'
    + fpThenNow().map(r => `<tr><td class="n" data-l="From">${r[0]}</td><td data-l="Item">${r[1]}</td><td data-l="The old page says">${esc(r[2])}</td><td data-l="Today">${r[3]}</td><td data-l="Status">${r[4]}</td></tr>`).join('') + '</tbody>';
  // history
  $('#fp-histlabel').innerHTML = `<b>History:</b> superseded by ${fpTodayName()}. ${fpOpenChoice()} These drawings show the 176 × 52 board of 08–09.09.26: its outline, the old dial lettering, A1’s JST-XH J1 “GND +5V A6 A7 D7 D8” and A1’s back-side placement no longer hold. The controls and their order still do.`;
  $('#fp-a1front').replaceChildren(fpA1Front());
  $('#fp-a1back').replaceChildren(fpA1Back());
  $('#fp-a2front').innerHTML = A2FRONT;
}
function renderLadders() {
  $('#lad-a6fig').replaceChildren(fpLadderA6());
  $('#lad-a7fig').replaceChildren(fpLadderA7());
  const want = { a6: [0, 205, 409, 614, 818, 1023], a7: [1023, 682, 512, 409] };
  const res = Object.keys(FPB).map(v => [v, fpLadderCodes(FPB[v])]).filter(r => r[1]);
  const same = c => c.a6.join() === want.a6.join() && c.a7.join() === want.a7.join();
  const bad = res.filter(r => !same(r[1]));
  const vals = res.length ? res[0][1].raw : [];
  $('#lad-check').innerHTML = (bad.length
    ? `<b>Changed since:</b> on ${bad.map(r => r[0]).join(', ')} today’s resistor values give A6 ${bad[0][1].a6.join('/')} and A7 ${bad[0][1].a7.join('/')} ${mk('comp')}, not the codes below. `
    : `<b>Checked against today:</b> boards ${res.map(r => r[0]).join(', ')} carry R1–R5 ${esc(vals[0])}, R6 ${esc(vals[5])}, R7 ${esc(vals[6])}, R8 ${esc(vals[7])} ${mk('seen')}, which give exactly the codes below ${mk('comp')}; the firmware uses the same numbers (<code>ts06pair.ino</code>) ${mk('seen')}. `)
    + `The 213 µA, 5.64 kΩ, 564 µs, 300 µA and the 103-code gap are recomputed here and agree ${mk('comp')}.`;
  $('#lad-drvnote').innerHTML = `${mk('seen')} Still so on TS06-DRV: C5 and C6, 100 nF from A6 and A7 to ground (<code>tools/ts06pair.py</code>); the firmware’s rotary filter wants five identical readings about 10 ms apart, and its buttons use the ATmega’s pull-ups. Since A1, rev B added R72, 1 M from A6 to ground, so an unplugged panel reads 0 instead of noise; with the panel on, the middle taps read up to 3.4 codes low ${mk('comp')}, inside the firmware’s ±102.`;
}
function gotoDoc(d) {
  if (d === 'ladders') { setDoc('sections', true); $('#ladders').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' }); return; }
  if (!DOCS.includes(d)) return;
  setDoc(d, true);
  $('#doc-' + d).scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
}

// ------------------------------------------------------------------------------------------ wiring
function wire() {
  $$('#scenes .tab').forEach(t => {
    t.addEventListener('click', () => { setScene(t.dataset.scene); if (t.dataset.scene !== 'asm') setSide('facts'); });
    t.addEventListener('keydown', e => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      const tabs = $$('#scenes .tab'), i = tabs.indexOf(t) + (e.key === 'ArrowRight' ? 1 : -1), n = tabs[(i + tabs.length) % tabs.length];
      setScene(n.dataset.scene); n.focus();
    });
  });
  $$('#modeseg button').forEach(b => b.addEventListener('click', () => setMode(b.dataset.mode)));
  $('#shotnav').addEventListener('click', e => { const b = e.target.closest('button'); if (b) { UI.shot = +b.dataset.i; renderShots(); } });
  $('#shotview').addEventListener('click', e => {
    const sv = $('#shotview');
    if (!sv.classList.contains('zoom')) {
      const r = sv.getBoundingClientRect(), fx = (e.clientX - r.left) / r.width, fy = (e.clientY - r.top) / r.height;
      sv.classList.add('zoom');
      requestAnimationFrame(() => { sv.scrollLeft = fx * sv.scrollWidth - r.width / 2; sv.scrollTop = fy * sv.scrollHeight - r.height / 2; });
    } else sv.classList.remove('zoom');
  });
  $$('#deck [data-view]').forEach(b => b.addEventListener('click', () => { if (UI.mode !== '3d') setMode('3d'); view(b.dataset.view); }));
  $$('#deck [data-zoom]').forEach(b => b.addEventListener('click', () => { if (UI.mode !== '3d') setMode('3d'); zoom(b.dataset.zoom === 'in' ? 0.75 : 1 / 0.75); }));
  $('#explode').addEventListener('input', e => setExplode(e.target.value / 100));
  $('#caseon').addEventListener('change', e => { V.caseOn = e.target.checked; applyVisibility(); });
  $('#caseghost').addEventListener('change', e => { V.caseGhost = e.target.checked; setCaseLook(); });
  $('#labelson').addEventListener('change', e => { V.showLabels = e.target.checked; V.labelR.domElement.style.display = V.showLabels ? '' : 'none'; invalidate(); });
  $('#sidetabs').addEventListener('click', e => { const b = e.target.closest('button'); if (b) setSide(b.dataset.side); });
  $('#steplist').addEventListener('click', e => {
    const b = e.target.closest('button[data-step]');
    if (!b) return;
    goStep(+b.dataset.step);
    // one column (phones, narrow windows): the list sits below the model, so bring the model back into view
    if (matchMedia('(max-width: 1000px)').matches) $('#viewer').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
  });
  $('#stepcard').addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.id === 'stepnext') goStep(Math.min(STEPS.length - 1, V.step + 1));
    else if (b.id === 'stepprev') goStep(Math.max(-1, V.step - 1));
    else if (b.dataset.key) {
      const pressed = b.getAttribute('aria-pressed') === 'true';
      $$('#stepcard .chip').forEach(c => c.setAttribute('aria-pressed', 'false'));
      if (pressed) { goStep(V.step); return; }
      b.setAttribute('aria-pressed', 'true');
      const h = STEPS[V.step].hl.find(x => x.key === b.dataset.key);
      highlight([h]);
      requestAnimationFrame(() => { const bb = hlBox(); if (!bb.isEmpty()) frameBox(bb, currentDir(), 3); });
    }
  });
  $$('.doctab').forEach(t => t.addEventListener('click', () => setDoc(t.dataset.doc, true)));
  $('.doctabs').addEventListener('keydown', e => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const tabs = $$('.doctab'), i = tabs.findIndex(t => t.getAttribute('aria-selected') === 'true') + (e.key === 'ArrowRight' ? 1 : -1);
    const n = tabs[(i + tabs.length) % tabs.length]; setDoc(n.dataset.doc, true); n.focus();
  });
  $$('#fvseg button').forEach(b => b.addEventListener('click', () => setFascia(b.dataset.fv)));
  $('#fvtable').addEventListener('click', e => {
    const b = e.target.closest('button[data-fv3d]');
    if (!b) return;
    setFascia(b.dataset.fv3d);
    goStep(-1, { noCamera: true });
    setScene('asm', { keepCamera: true }); setMode('3d');
    $('#viewer').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' });
    if (V.ready) frameBox(visibleBox(V.roots.asm.group), 'front');
  });
  $('#seclist').addEventListener('click', e => { const b = e.target.closest('button'); if (b) { SEC = +b.dataset.i; renderSections(); } });
  $('#stagelist').addEventListener('click', e => {
    const b = e.target.closest('button[data-step]');
    if (b) { goStep(+b.dataset.step); setSide('steps'); $('#viewer').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' }); }
  });
  window.addEventListener('hashchange', () => { const h = location.hash.slice(1); if (DOCS.includes(h)) setDoc(h, false); });
  // front panel view (and its ladders in Circuit sections)
  document.addEventListener('click', e => { const b = e.target.closest('[data-goto]'); if (b) gotoDoc(b.dataset.goto); });
  $('#fp-fvseg').addEventListener('click', e => { const b = e.target.closest('button[data-fp]'); if (b) fpShowToday(b.dataset.fp); });
  $('#fp-poslist').addEventListener('click', e => { const b = e.target.closest('button[data-pos]'); if (b) fpSelect(+b.dataset.pos); });
  $('#fp-a1tabs').addEventListener('click', e => {
    const b = e.target.closest('button[data-side]');
    if (!b) return;
    $$('#fp-a1tabs button').forEach(x => x.setAttribute('aria-pressed', x === b));
    $('#fp-a1front').hidden = b.dataset.side !== 'front';
    $('#fp-a1back').hidden = b.dataset.side !== 'back';
  });
}
const DOCS = ['sections', 'panel', 'fascia', 'order', 'test', 'kicad', 'notes'];
function setSide(s) {
  UI.side = s;
  $$('#sidetabs button').forEach(b => { const on = b.dataset.side === s; b.setAttribute('aria-selected', on); b.setAttribute('aria-pressed', on); });
  $('#panel-steps').hidden = s !== 'steps';
  $('#panel-facts').hidden = s !== 'facts';
}
function setDoc(d, push) {
  UI.doc = d;
  $$('.doctab').forEach(t => { const on = t.dataset.doc === d; t.setAttribute('aria-selected', on); t.tabIndex = on ? 0 : -1; });
  $$('.docpanel').forEach(p => { p.hidden = p.id !== 'doc-' + d; });
  if (push) { try { history.replaceState(null, '', '#' + d); } catch (e) { /* sandboxed */ } }
}

// ------------------------------------------------------------------------------------------ loading
// The models are glTF JSON with the buffer embedded as base64 (the host serves no .glb). They are
// fetched as text and repacked into a GLB in memory, so nothing depends on fetching a data: URI.
async function fetchText(url, onProgress) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ' answered ' + r.status);
  const total = +r.headers.get('content-length') || 0;
  if (!r.body || !total) return r.text();
  const rd = r.body.getReader(), parts = [];
  let got = 0;
  for (;;) {
    const { done, value } = await rd.read();
    if (done) break;
    parts.push(value); got += value.length;
    onProgress(got / total);
  }
  const all = new Uint8Array(got);
  let o = 0;
  for (const p of parts) { all.set(p, o); o += p.length; }
  return new TextDecoder().decode(all);
}
function toGLB(json) {
  const j = JSON.parse(json);
  let bin = new Uint8Array(0);
  const b = j.buffers && j.buffers[0];
  if (b && typeof b.uri === 'string' && b.uri.startsWith('data:')) {
    const s = atob(b.uri.slice(b.uri.indexOf(',') + 1));
    bin = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) bin[i] = s.charCodeAt(i);
    delete b.uri;
  }
  const enc = new TextEncoder().encode(JSON.stringify(j));
  const jl = (enc.length + 3) & ~3, bl = (bin.length + 3) & ~3;
  const out = new Uint8Array(12 + 8 + jl + (bl ? 8 + bl : 0));
  const dv = new DataView(out.buffer);
  dv.setUint32(0, 0x46546C67, true); dv.setUint32(4, 2, true); dv.setUint32(8, out.length, true);
  dv.setUint32(12, jl, true); dv.setUint32(16, 0x4E4F534A, true);
  out.fill(0x20, 20, 20 + jl); out.set(enc, 20);
  if (bl) { dv.setUint32(20 + jl, bl, true); dv.setUint32(24 + jl, 0x004E4942, true); out.set(bin, 28 + jl); }
  return out.buffer;
}
async function loadGLTF(key, url, label) {
  const row = document.createElement('div');
  row.className = 'row';
  row.innerHTML = `<span>${esc(label)}</span><span class="bar2"><i></i></span><span class="pct">0%</span>`;
  $('#loading').appendChild(row);
  try {
    const txt = await fetchText(url, f => { const p = Math.round(f * 100); $('i', row).style.width = p + '%'; $('.pct', row).textContent = p + '%'; });
    const g = await new Promise((res, rej) => new GLTFLoader().parse(toGLB(txt), '', res, rej));
    row.remove();
    V.gltf[key] = g;
    return g;
  } catch (err) {
    row.innerHTML = `<span>${esc(label)}: could not load (${esc(err && err.message || err)})</span>`;
    throw err;
  }
}

async function main() {
  initViewer();
  try {
    [MODEL, PARTS, FACTS, SECTIONS] = await Promise.all(['model', 'parts', 'facts', 'sections'].map(n => getJSON('data/' + n + '.json')));
    VARIANTS = await getJSON('data/variants.json').catch(() => VARIANTS);
    ORDER = await getJSON('data/order.json').catch(() => null);
    POP = await getJSON('data/populated.json').catch(() => POP);
  } catch (e) {
    $('#loading').innerHTML = `<div class="row">The page data did not load: ${esc(e.message)}</div>`;
    throw e;
  }
  V.fv = store.get('fascia', isPop('TS06-FASCIA-rhythm') ? 'R' : 'A');       // R is the board that is ordered
  BOARD.FASCIA = FV[V.fv] && PARTS[FV[V.fv]] ? FV[V.fv] : (V.fv = 'A', FV.A);
  STEPS = steps();
  wire();
  renderVariants();
  renderStepList();
  renderSections();
  renderTestStages();
  renderNotes();
  renderPanel();
  renderLadders();
  renderOrder();
  const h = location.hash.slice(1);
  setDoc(DOCS.includes(h) ? h : 'sections', false);
  setMode('img');                       // the pictures show while the models load
  setScene(UI.scene, { keepCamera: true });
  let step = store.get('step', -1);
  if (!(Number.isInteger(step) && step >= -1 && step < STEPS.length) || UI.scene !== 'asm') step = -1;
  V.step = step;
  renderStepCard();
  try {
    await Promise.all([
      loadGLTF('DRV', '3d/TS06-DRV.gltf.json', 'TS06-DRV'),
      loadGLTF('DISP', '3d/TS06-DISP.gltf.json', 'TS06-DISP'),
      ...Object.entries(FV).filter(([v, b]) => PARTS[b] && v !== 'F').map(([v, b]) => loadGLTF('F' + v, `3d/${b}.gltf.json`, b)),
      loadGLTF('CASE', '3d/case.gltf.json', 'case'),
    ]);
  } catch (e) { console.warn('model load failed', e); return; }
  if (V.gltf.FA) V.gltf.FF = V.gltf.FA;       // F shows A's board as the stand-in for its 179 panel
  buildRoots();
  V.ready = true;
  setFascia(V.fv);
  setMode('3d');
  setCaseLook();
  setScene(UI.scene, { keepCamera: true });
  if (UI.scene === 'asm') goStep(step, { ms: 0 });
  else frameBox(visibleBox(V.roots[UI.scene].group), 'front', 1, 0);
  document.body.dataset.ready = '1';
}
window.TS06 = V;                      // for the tests: camera, controls, state
V.getSteps = () => STEPS;
main();
