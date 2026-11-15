// Draws one picture for each of the five shop concepts (for the owner's tier-list card).
// Run: node "Claude outputs/shop/tier/make_cards.js"   (needs the pre-installed Playwright and Chromium)
// Source of every word and number: Claude outputs/shop/SHOP-concepts.md, section 5. The sketches are not designs.
const path = require('path');
const { chromium } = require('playwright');

const GOLD = '#c9a44a', LIT = '#ffb35a', INK = '#e9e6df', DIM = '#8d8a84';

const defs = `<defs>
<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="1320" height="470"><feGaussianBlur stdDeviation="7" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<radialGradient id="knob" cx="35%" cy="30%"><stop offset="0" stop-color="#5c5d63"/><stop offset="1" stop-color="#1b1b1e"/></radialGradient>
</defs>`;
const board = (x, y, w, h) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="16" fill="#0a0a0b" stroke="${GOLD}" stroke-width="3"/>`;
const tube = (x, y, w, h, ch) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${w * 0.28}" fill="#1a110a" stroke="#6b5a48" stroke-width="2.5"/>
<text x="${x + w / 2}" y="${y + h * 0.72}" font-size="${h * 0.62}" text-anchor="middle" fill="#ffd2a0" filter="url(#glow)" font-weight="300">${ch}</text>`;
const lit = (d, w = 9, c = LIT) => `<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round" filter="url(#glow)"/>`;
const gold = (d, w = 3) => `<path d="${d}" fill="none" stroke="${GOLD}" stroke-width="${w}" stroke-linecap="round"/>`;
const label = (x, y, t, s = 22, c = DIM, a = 'middle') => `<text x="${x}" y="${y}" font-size="${s}" text-anchor="${a}" fill="${c}" letter-spacing="1.5">${t}</text>`;
const node = (x, y, on) => `<circle cx="${x}" cy="${y}" r="11" fill="${on ? LIT : '#0a0a0b'}" stroke="${on ? LIT : GOLD}" stroke-width="3" ${on ? 'filter="url(#glow)"' : ''}/>`;
const knob = (x, y, r) => `<circle cx="${x}" cy="${y}" r="${r + 7}" fill="#050505"/><circle cx="${x}" cy="${y}" r="${r}" fill="url(#knob)"/>`;

const sketch = {
  G: () => board(60, 20, 1200, 430)
    + tube(190, 50, 112, 170, '0') + tube(316, 50, 112, 170, '3') + label(309, 252, 'AHEAD')
    + tube(520, 50, 112, 170, '0') + tube(646, 50, 112, 170, '1') + label(639, 252, 'BEHIND')
    + tube(900, 66, 92, 140, '+') + label(946, 252, 'PAGE')
    + lit('M120 405 H1200') + label(1195, 385, 'main', 20, DIM, 'end')
    + lit('M330 405 C 400 405, 400 320, 480 320 H 760')
    + gold('M760 320 H 900 C 980 320, 980 405, 1050 405', 4).replace('stroke-linecap', 'stroke-dasharray="4 12" stroke-linecap')
    + node(330, 405, true) + node(480, 320, true) + node(620, 320, true) + node(760, 320, true) + node(1050, 405, false)
    + label(620, 296, 'feature: lit while work is not merged', 20),
  A: () => board(60, 20, 1200, 430)
    + tube(250, 50, 112, 170, '0') + tube(376, 50, 112, 170, '0') + tube(502, 50, 112, 170, '1') + tube(628, 50, 112, 170, '7')
    + label(495, 252, 'PASSES TODAY') + tube(860, 66, 92, 140, 'M') + label(906, 252, 'PAGE')
    + gold('M120 400 H1010', 2) + gold('M120 290 V400', 2)
    + lit('M130 305 C 420 305, 480 310, 565 348 S 720 392, 1000 392')
    + node(565, 348, true) + label(600, 338, 'closest point', 20, DIM, 'start')
    + label(130, 432, 'the pitch of the sound falls as the aircraft passes', 20, DIM, 'start')
    + node(1080, 318, true) + label(1104, 325, 'NAMED', 20, INK, 'start')
    + node(1080, 372, false) + label(1104, 379, 'NOT NAMED', 20, DIM, 'start'),
  P: () => `<path d="M330 452 L370 400 H470 L510 452 Z M810 452 L850 400 H950 L990 452 Z" fill="#1c1c1f" stroke="#3a3a40" stroke-width="2"/>`
    + board(60, 40, 1200, 370)
    + lit('M170 110 A 150 150 0 0 0 170 340') + `<circle cx="270" cy="225" r="78" fill="none" stroke="${GOLD}" stroke-width="4"/>`
    + gold('M270 147 V120 M348 225 H375 M270 303 V330 M325 170 L344 151 M325 280 L344 299', 4)
    + `<circle cx="540" cy="225" r="62" fill="none" stroke="${GOLD}" stroke-width="4"/><circle cx="720" cy="225" r="62" fill="none" stroke="${GOLD}" stroke-width="4"/>`
    + gold('M602 225 H658', 4) + lit('M480 120 H600') + lit('M660 120 H780') + lit('M480 330 H600') + lit('M660 330 H780')
    + lit('M930 205 A 95 95 0 0 1 1010 130', 8) + lit('M1090 130 A 95 95 0 0 1 1170 205', 8)
    + lit('M930 245 A 95 95 0 0 0 1010 320', 8) + lit('M1090 320 A 95 95 0 0 0 1170 245', 8)
    + `<circle cx="1050" cy="225" r="44" fill="none" stroke="${GOLD}" stroke-width="4"/>` + gold('M1030 225 H1070 M1050 205 V245', 4)
    + Array.from({ length: 7 }, (_, i) => `<circle cx="${838}" cy="${135 + i * 30}" r="5" fill="${GOLD}"/>`).join('')
    + label(660, 388, 'no tubes  ·  no high voltage  ·  5 V from USB', 20),
  T: () => board(60, 20, 1200, 430)
    + `<rect x="150" y="60" width="210" height="318" rx="14" fill="none" stroke="${GOLD}" stroke-width="3" stroke-dasharray="3 9"/>`
    + tube(185, 90, 140, 215, '8') + label(255, 348, 'TUBE UNDER TEST', 20) + label(255, 414, 'plug-in card for each tube type', 20)
    + tube(470, 70, 84, 130, '1') + tube(564, 70, 84, 130, '7') + tube(658, 70, 84, 130, '2') + label(606, 232, 'STRIKE VOLTAGE')
    + ['A', 'B', 'C', 'X'].map((g, i) => node(488 + i * 78, 300, i === 0) + label(488 + i * 78, 345, g, 22, i === 0 ? INK : DIM)).join('')
    + label(606, 395, 'GRADE', 22)
    + `<rect x="860" y="80" width="330" height="270" rx="10" fill="#141416" stroke="#4a4a50" stroke-width="2"/>`
    + [0, 1, 2, 3].map(i => tube(884 + i * 74, 120, 60, 96, '8')).join('')
    + [0, 1, 2, 3].map(i => `<rect x="${884 + i * 74}" y="238" width="60" height="96" rx="17" fill="#141009" stroke="#4d4136" stroke-width="2"/>`).join('')
    + label(1025, 395, 'A MATCHED SET', 22),
  F: () => board(60, 20, 1200, 430)
    + `<circle cx="230" cy="250" r="62" fill="#141416" stroke="${GOLD}" stroke-width="4"/><path d="M230 250 L290 96" stroke="#b9bbc2" stroke-width="16" stroke-linecap="round"/>`
    + `<circle cx="292" cy="90" r="24" fill="url(#knob)" stroke="#9a9ca4" stroke-width="2"/>`
    + lit('M150 170 A 115 115 0 0 0 150 330', 8) + label(230, 370, 'PULL: 25 MIN', 22, INK) + label(230, 402, 'BACK: A BREAK', 20)
    + tube(440, 80, 124, 190, '2') + tube(578, 80, 124, 190, '5')
    + `<circle cx="735" cy="205" r="10" fill="${LIT}" filter="url(#glow)"/>`
    + tube(768, 80, 124, 190, '0') + tube(906, 80, 124, 190, '0')
    + label(735, 318, 'MINUTES  ·  SECONDS', 22) + label(735, 400, 'no app  ·  no computer  ·  no sensor  ·  also a clock', 20)
    + knob(1130, 150, 34) + knob(1130, 290, 34),
};

const C = [
  { k: 'G', name: 'Git tracker', who: 'your idea', pitch: 'One repository’s working state on tubes; branches as lit gold lines.',
    f: ['Developers with a desk setup; gifts for them.',
        'Commits ahead and behind. Second page: open changes, days since the last merge.',
        'USB from the computer and a short script. No Wi-Fi.',
        'The profile on the old clock. Film a real merge.'],
    price: '179 USD', parts: '4 ИН-12, 1 ИН-15А', s: [3, 4, 3, 5],
    note: 'Hardest: the script on three systems, and its support.' },
  { k: 'A', name: 'Aircraft display', who: 'your idea, with sky1', pitch: 'A tube display for the aircraft that pass your window.',
    f: ['Plane spotters; radio hobbyists.',
        'Passes today. The last pass: speed and closest distance. A lit arc follows each pass.',
        'From sky1’s sensor, however it gets the data (your answer). The sensor is not part of this product.',
        'A week of counts on the old clock.'],
    price: '179 USD', parts: '4 ИН-12, 1 ИН-15А', s: [3, 2, 2, 5],
    note: 'Hardest: false counts; it waits on the sensor.' },
  { k: 'P', name: 'Lit plate', who: 'nixie’s idea', pitch: 'The fascia art as an object: warm LED filaments behind windows in a black and gold board.',
    f: ['People who like the look but not 185 V or the price; gifts.',
        'No numbers. A stand, a dimmer, a USB socket.',
        'None. 5 V only.',
        'The window coupon. Photograph it by day and by night.'],
    price: '39 USD', parts: 'no tubes', s: [3, 5, 3, 5],
    note: 'Hardest: light through bare laminate is not proven.' },
  { k: 'T', name: 'Tube tester and matcher', who: 'nixie’s idea', pitch: 'A bench tool: lights each cathode, measures it, runs a recovery cycle, grades tubes into matched sets.',
    f: ['Clock builders and tube traders. First, this shop: about 120 tubes to test for ten units.',
        'Strike and hold voltage for each cathode; a grade.',
        'Results over USB.',
        'Build the audit’s tube rig with measuring added. Publish the table.'],
    price: 'kit 79 USD', parts: 'uses up no tubes', s: [2, 4, 3, 5],
    note: 'Hardest: live leads on an open socket; recovery works only sometimes.' },
  { k: 'F', name: 'Focus timer', who: 'nixie’s idea', pitch: 'Pull a lever: 25 minutes count down on tubes. Return it: a break.',
    f: ['Desk-setup people, students, gifts.',
        'Minutes and seconds on four tubes; a running dot; a beep.',
        'None. No computer, no sensor: the easiest first sale of the four-tube core.',
        'Timer firmware on the old clock, with a film.'],
    price: '179 USD', parts: '4 ИН-12, 1 lever', s: [3, 4, 3, 4],
    note: 'Hardest: the price beside a 20 USD timer; levers are short.' },
];

const rows = ['For', 'Shows', 'Data', 'Test first'];
const scoreNames = ['Demand', 'Least work', 'Margin', 'Fits the stock'];
const html = c => `<!doctype html><meta charset="utf-8"><style>
*{box-sizing:border-box}body{margin:0;width:1400px;height:900px;background:#111216;color:${INK};font-family:"DejaVu Sans",sans-serif;position:relative;overflow:hidden}
.b{position:absolute;left:40px;top:28px;width:104px;height:104px;border-radius:18px;background:${GOLD};color:#111;font-size:76px;font-weight:700;display:flex;align-items:center;justify-content:center}
h1{position:absolute;left:170px;top:22px;margin:0;font-size:50px}h1 span{font-size:24px;color:${DIM};font-weight:400;margin-left:16px}
.p{position:absolute;left:172px;top:90px;font-size:25px;color:#d8d4cb;width:1190px}
svg{position:absolute;left:40px;top:150px}
.f{position:absolute;left:40px;top:632px;width:880px;font-size:20px;line-height:1.3}
.f div{display:flex;margin-bottom:9px}.f b{flex:0 0 118px;color:${GOLD};font-weight:400}
.s{position:absolute;left:960px;top:632px;width:400px;font-size:20px}
.s div{display:flex;align-items:center;margin-bottom:8px}.s span{flex:0 0 168px;color:${DIM}}
.s i{width:28px;height:16px;margin-right:6px;border:1.5px solid ${GOLD};border-radius:3px}.s i.on{background:${GOLD}}
.pr{margin:14px 0 0;font-size:21px}.pr b{color:${LIT}}
.n{position:absolute;left:40px;bottom:16px;right:40px;font-size:17px;color:${DIM};display:flex;justify-content:space-between}
</style><div class="b">${c.k}</div><h1>${c.name}<span>${c.who}</span></h1><div class="p">${c.pitch}</div>
<svg width="1320" height="470" viewBox="0 0 1320 470" font-family="DejaVu Sans, sans-serif">${defs}${sketch[c.k]()}</svg>
<div class="f">${rows.map((r, i) => `<div><b>${r}</b><span>${c.f[i]}</span></div>`).join('')}</div>
<div class="s">${scoreNames.map((n, i) => `<div><span>${n}</span>${[1, 2, 3, 4, 5].map(v => `<i class="${v <= c.s[i] ? 'on' : ''}"></i>`).join('')}</div>`).join('')}
<p class="pr">Price <b>${c.price}</b> (assumed)<br>${c.parts}</p></div>
<div class="n"><span>${c.note}</span><span>Scores 1 to 5 from the shop study; demand is not proven. A sketch, not a design.</span></div>`;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 2 });
  for (const c of C) {
    await page.setContent(html(c));
    const out = path.join(__dirname, `${c.k}-${c.name.toLowerCase().replace(/[^a-z]+/g, '-')}.jpg`);
    await page.screenshot({ path: out, type: 'jpeg', quality: 88 });
    console.log(out);
  }
  await browser.close();
})();
