#!/usr/bin/env node
/**
 * verify.mjs — gate for the v8 "Disciplined Dark" landing prototype.
 *
 *   node verify.mjs
 *
 * What it enforces, and why each rule exists (see ../PROD_FINDINGS.md):
 *   A. CONTRAST  — every ink/accent pairing against its ACTUAL composited
 *                  background (accent washes are alpha over a real surface).
 *   B. RETIREMENT — the measured 2020s patterns must be ABSENT: gradients,
 *                  backdrop-filter, glow shadows, infinite CSS animation, SMIL,
 *                  radii above 8px. The live landing carried 17 / 1 / 11 / 6 / 2
 *                  of these respectively; this file must carry zero.
 *   C. CONTINUITY — the palette must match the RUNNING app's :root, not
 *                  DESIGN.md §2 (which has drifted on all five bg tokens).
 *   D. BEHAVIOUR — jsdom: accordion, copy, one-shot reveal, reduced motion,
 *                  graceful degradation, pagehide teardown.
 *
 * Exit 0 = all pass. Never change a token to make this pass; change it because
 * the number is real.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const HTML_PATH = path.join(HERE, 'index.html');
const html = fs.readFileSync(HTML_PATH, 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));

let pass = 0, fail = 0;
const ok = (name, cond, detail = '') => {
  if (cond) { pass++; console.log('  ✓ ' + name); }
  else { fail++; console.log('  ✗ ' + name + (detail ? ' — ' + detail : '')); }
};

/* ══════════════════ A. CONTRAST ══════════════════ */
console.log('\n── A. CONTRAST (WCAG 2.1 AA, actual composited backgrounds) ──');

const lum = (h) => {
  const c = [1, 3, 5].map(i => parseInt(h.substr(i, 2), 16) / 255)
    .map(v => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
const ratio = (a, b) => {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return +((x + 0.05) / (y + 0.05)).toFixed(2);
};
const rgb = (h) => [1, 3, 5].map(i => parseInt(h.substr(i, 2), 16));
const over = (fg, alpha, bg) => {
  const F = rgb(fg), B = rgb(bg);
  return '#' + F.map((v, i) =>
    Math.round(v * alpha + B[i] * (1 - alpha)).toString(16).padStart(2, '0')).join('');
};

// Tokens parsed from the file — never duplicated here, so they cannot drift.
const tok = {};
for (const m of css.matchAll(/--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})/g)) tok[m[1]] = m[2];

const wash = (name, base) => {
  const m = css.match(new RegExp('--' + name + ':\\s*rgba\\((\\d+),\\s*(\\d+),\\s*(\\d+),\\s*([\\d.]+)\\)'));
  if (!m) throw new Error('missing wash token: ' + name);
  const fg = '#' + [m[1], m[2], m[3]].map(v => (+v).toString(16).padStart(2, '0')).join('');
  return over(fg, +m[4], base);
};

const CANVAS = tok.canvas, SURFACE = tok.surface, ELEV = tok.elevated;
const SURF = {
  canvas, surface, elevated,
  'wash-neutral/surface': wash('wash-neutral', SURFACE),
  'wash-blue/surface': wash('wash-blue', SURFACE),
  'wash-green/surface': wash('wash-green', SURFACE),
  'wash-amber/surface': wash('wash-amber', SURFACE),
  'wash-red/surface': wash('wash-red', SURFACE),
};
SURF.canvas = CANVAS; SURF.surface = SURFACE; SURF.elevated = ELEV;

// Where each token ACTUALLY sits. Move accent text onto a new surface and this
// suite fails you. That is the point — v7 shipped two contrast bugs that were
// only visible once alpha compositing was modelled.
const USAGE = [
  ['ink',       'body / headings',        ['canvas', 'surface', 'elevated'], 4.5],
  ['ink-2',     'body copy / lede',       ['canvas', 'surface', 'elevated'], 4.5],
  ['ink-3',     'meta / captions / nav',  ['canvas', 'surface', 'elevated', 'wash-neutral/surface'], 4.5],
  ['blue',      'links / step number',    ['surface', 'wash-blue/surface'], 4.5],
  ['green',     'success chip / copy ok', ['surface', 'wash-green/surface'], 4.5],
  ['amber',     'warning chip',           ['surface', 'wash-amber/surface'], 4.5],
  ['red',       'blocking chip',          ['surface', 'wash-red/surface'], 4.5],
  ['cyan',      'accent on canvas',       ['canvas'], 4.5],
];
for (const [t, where, surfaces, min] of USAGE) {
  const fg = tok[t];
  if (!fg) { ok(`token --${t} exists`, false); continue; }
  const rs = surfaces.map(s => [s, ratio(fg, SURF[s])]);
  const worst = Math.min(...rs.map(r => r[1]));
  ok(`--${t} ${fg} · ${where} · worst ${worst.toFixed(2)}`,
    worst >= min,
    rs.filter(r => r[1] < min).map(([n, v]) => `${n}=${v}`).join(', '));
}

console.log('\n  Button fills (needs ≥ 4.5):');
{
  const r = ratio(tok.canvas, tok.blue); // #0d1117 on blue fill
  ok(`  --canvas ${tok.canvas} on --blue ${tok.blue} = ${r}`, r >= 4.5);
}

console.log('\n  Non-text tiers (icons/rules need ≥ 3.0, must never be text):');
{
  const r = ratio(tok['ink-none'], SURFACE);
  ok(`  --ink-none ${tok['ink-none']} = ${r.toFixed(2)} on surface (icon only)`, r >= 3.0);
  // `color:` on an aria-hidden SVG wrapper just sets currentColor for the icon
  // stroke — legitimate. What must never happen is --ink-none colouring TEXT.
  // So: assert every rule that uses it targets a known icon selector.
  const ICON_SELECTORS = ['gap__chev'];
  const uses = [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)]
    .filter(m => /var\(--ink-none\)/.test(m[2]))
    .flatMap(m => m[1].split(',').map(s => s.trim().replace(/^[.#]/, '')))
    .filter(Boolean);
  ok('  --ink-none used only on icon selectors',
    uses.length > 0 && uses.every(s => ICON_SELECTORS.includes(s)),
    uses.join(' | ') || 'declared but unused');
}
{
  const r = ratio(tok['rule-hi'], SURFACE);
  ok(`  --rule-hi ${tok['rule-hi']} = ${r.toFixed(2)} on surface (rule only)`, r >= 3.0);
}

/* ══════════════════ B. RETIREMENT (the 2020s patterns) ══════════════════ */
console.log('\n── B. RETIREMENT — patterns measured on the live landing, must be 0 ──');
console.log('   (live landing: 17 gradients · 1 backdrop-filter · 11 glow shadows');
console.log('    6 infinite CSS animations · 2 SMIL · radii 999/30/24/20px)');

ok('zero gradients (background/mask/border-image)',
  !/gradient\s*\(/i.test(css));
ok('zero backdrop-filter / backdrop blur',
  !/backdrop-(filter|blur)/i.test(css));
ok('zero infinite CSS animations',
  !/\binfinite\b/i.test(css.replace(/\/\*[\s\S]*?\*\//g, '')));
ok('zero SMIL animation elements',
  !/<animate(Motion|Transform)?[\s/>]/i.test(html));
ok('zero @keyframes blocks',
  !/@keyframes/.test(css));

console.log('\n  Radius — Theme B rule, one value, no pills:');
{
  const radii = [...css.matchAll(/border-radius:\s*([^;}]+)/g)]
    .flatMap(m => m[1].split(/[\s\/]+/))
    .filter(v => v && v !== 'var(--r)')
    .map(v => parseFloat(v))
    .filter(v => !isNaN(v));
  const max = Math.max(0, ...radii);
  ok(`  no hard-coded radius above 8px (max ${max}px)`, max <= 8);
  ok('  --r is 8px', /--r:\s*8px/.test(css));
  ok('  no pill (999px / 50%)', !/(999|50%)/.test(
    [...css.matchAll(/border-radius:\s*([^;}]+)/g)].map(m => m[1]).join(' ')));
}

console.log('\n  Elevation — one subtle layer, no glow:');
{
  // Resolve var() first — otherwise the blur check is vacuous.
  const shadows = [...css.matchAll(/box-shadow:\s*([^;}]+)/g)]
    .map(m => m[1].replace(/var\(--([a-z0-9-]+)\)/g, (_, n) => {
      const d = css.match(new RegExp('--' + n + ':\\s*([^;}]+)'));
      return d ? d[1].trim() : '';
    }));
  ok(`  at most one box-shadow declaration (${shadows.length})`, shadows.length <= 1);
  const blurs = shadows.flatMap(s => [...s.matchAll(/(-?[\d.]+)px/g)]
    .map(m => Math.abs(parseFloat(m[1]))));
  const maxBlur = Math.max(0, ...blurs);
  ok(`  max shadow blur ${maxBlur}px ≤ 8 (a glow is 24px+)`, maxBlur <= 8,
    shadows.join(' / '));
}

console.log('\n  Typography — marketing scale, not the app’s 14px:');
{
  const fs = css.match(/body\{[\s\S]*?font-size:\s*(\d+)px/);
  ok(`  body font-size ${fs ? fs[1] : '?'}px ≥ 17`, fs && +fs[1] >= 17);
  const lh = css.match(/body\{[\s\S]*?line-height:\s*([\d.]+)/);
  ok(`  body line-height ${lh ? lh[1] : '?'} ≥ 1.6`, lh && +lh[1] >= 1.6);
}

/* ══════════════════ C. CONTINUITY with the running app ══════════════════ */
console.log('\n── C. CONTINUITY — palette must match the app, not DESIGN.md §2 ──');
// Measured 2026-08-31 via inspect-app-dna.py. DESIGN.md §2 differs on all five.
const LIVE = {
  canvas: '#0d1117', surface: '#161b22', elevated: '#1c2128',
  highlight: '#222833', input: '#0e1116',
  ink: '#e6edf3', 'ink-2': '#a8b3c1', 'ink-3': '#8b949e',
  blue: '#58a6ff', green: '#3fb950', amber: '#d29922', red: '#f85149',
  cyan: '#39d0d8', rule: '#30363d', 'rule-hi': '#8b949e', 'rule-active': '#58a6ff',
};
for (const [k, v] of Object.entries(LIVE)) {
  ok(`  --${k} = ${v} (matches running app)`, tok[k] === v,
    tok[k] ? `file has ${tok[k]}` : 'missing');
}
console.log('\n  Fonts — must match what the app actually loads:');
ok('  Sora loaded', /Sora/.test(html));
ok('  Rubik loaded', /Rubik/.test(html));
ok('  JetBrains Mono loaded', /JetBrains\+Mono/.test(html));
{
  // Scoped to real font sources — the file legitimately *discusses* IBM Plex in a
  // comment (it is §3's specified font and prod loads none of it).
  const fontSrc = [
    ...(html.match(/<link[^>]*fonts\.googleapis[^>]*>/g) || []),
    ...[...css.matchAll(/--(?:display|body|mono):([^;}]+)/g)].map(m => m[1]),
  ].join(' ');
  ok('  does not claim IBM Plex (§3 font, 0 elements in prod)',
    !/IBM\s*\+?\s*Plex/i.test(fontSrc));
}
ok('  no AI-cliche faces in the body stack',
  !/\b(Inter|Roboto|Fraunces|Space Grotesk|Arial|Helvetica)\b/.test(
    [...css.matchAll(/--body:([^;}]+)/g)].map(m => m[1]).join(' ')));

/* ══════════════════ D. BEHAVIOUR ══════════════════ */
console.log('\n── D. BEHAVIOUR (jsdom) ──');

let JSDOM;
try {
  ({ JSDOM } = await import('/Users/pranay/Projects/travel_agency_agent/frontend/node_modules/jsdom/lib/api.js'));
} catch {
  console.log('  (jsdom unavailable — behavioural suite skipped)');
  JSDOM = null;
}

if (JSDOM) {
  const make = ({ io = true, reduce = false } = {}) =>
    new JSDOM(html, {
      runScripts: 'dangerously',
      pretendToBeVisual: true,
      beforeParse(w) {
        w.matchMedia = q => ({
          matches: reduce && /reduced-motion/.test(q), media: q,
          addEventListener() {}, removeEventListener() {},
          addListener() {}, removeListener() {},
        });
        if (!io) { delete w.IntersectionObserver; return; }
        w.__ios = [];
        w.IntersectionObserver = class {
          constructor(cb) { this.cb = cb; this.els = []; w.__ios.push(this); }
          observe(el) { this.els.push(el); }
          unobserve(el) { this.els = this.els.filter(e => e !== el); }
          disconnect() { this.els = []; }
          trigger() { this.cb(this.els.map(t => ({ target: t, isIntersecting: true })), this); }
        };
        if (!w.navigator.clipboard) {
          Object.defineProperty(w.navigator, 'clipboard',
            { value: { writeText: () => Promise.resolve() }, configurable: true });
        }
      },
    });
  const tick = (d, ms) => new Promise(r => d.window.setTimeout(r, ms));

  let dom = make(); let w = dom.window; let doc = w.document; await tick(dom, 60);

  console.log('\n  Structure:');
  ok('single h1', doc.querySelectorAll('h1').length === 1);
  ok('skip link → #main', doc.querySelector('a.skip')?.getAttribute('href') === '#main');
  ok('heading order never skips a level', (() => {
    const ls = [...doc.querySelectorAll('h1,h2,h3,h4')].map(h => +h.tagName[1]);
    return ls.every((v, i) => i === 0 || v - ls[i - 1] <= 1);
  })());
  ok('every button has accessible text', [...doc.querySelectorAll('button')]
    .every(b => (b.textContent || '').trim() || b.getAttribute('aria-label')));
  ok('no inline onclick handlers', !/\son(click|keydown|mouseover)=/i.test(html));
  ok('live region present for copy feedback',
    !!doc.querySelector('[aria-live="polite"]'));
  ok('decorative hero art hidden from AT',
    doc.querySelector('.hero__art')?.getAttribute('aria-hidden') === 'true');
  ok('progress bar has an accessible label',
    !!doc.querySelector('[role="img"][aria-label]'));
  ok('progress fill width matches its label', (() => {
    const label = doc.querySelector('.prog__bar')?.getAttribute('aria-label') || '';
    const m = label.match(/(\d+) of (\d+)/);
    const got = parseFloat((css.match(/\.prog__fill\{[^}]*width:\s*([\d.]+)%/) || [])[1]);
    if (!m || isNaN(got)) return false;
    return Math.abs(Math.round((+m[1] / +m[2]) * 1000) / 10 - got) < 0.5;
  })());
  ok('--ink-none icons carry no text (icon-only tier)',
    [...doc.querySelectorAll('.gap__chev')].every(e => !(e.textContent || '').trim()));

  console.log('\n  Specimen accordion:');
  const btns = [...doc.querySelectorAll('.gap__btn')];
  ok('4 gap buttons', btns.length === 4, btns.length + ' found');
  ok('all start collapsed', btns.every(b => b.getAttribute('aria-expanded') === 'false'));
  ok('panels start hidden', [...doc.querySelectorAll('.gap__panel')].every(p => p.hidden));
  btns[2].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok('opens on click', btns[2].getAttribute('aria-expanded') === 'true');
  ok('panel unhidden', doc.getElementById('g3').hidden === false);
  btns[0].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok('one open at a time',
    btns[2].getAttribute('aria-expanded') === 'false' &&
    btns[0].getAttribute('aria-expanded') === 'true');
  ok('every button controls a real panel', btns.every(b =>
    !!doc.getElementById(b.getAttribute('aria-controls'))));

  console.log('\n  Grounding — copy must describe what the app actually renders:');
  const text = doc.body.textContent;
  ok('uses the product’s real string “Trip details incomplete”',
    /Trip details incomplete/.test(text));
  ok('uses the product’s real string “Missing customer details”',
    /Missing customer details/.test(text));
  ok('uses the product’s real string “Suggested Follow-up”',
    /Suggested follow-up/i.test(text));
  ok('cites real routes (Lead Inbox / Quote Review)',
    /Lead Inbox/.test(text) && /Quote Review/.test(text));
  ok('does NOT claim unbuilt epistemic tiers',
    !/\b(FACT|INFERRED|ASSUMED|UNKNOWN)\b/.test(text));
  ok('no invented metrics (no % or time claims)',
    !/\d+\s?%/.test(text.replace(/9 of \d+|\d+ of \d+/g, '')) && !/\d+m \d+s/.test(text));

  console.log('\n  Copy + reveal:');
  const copy = doc.querySelector('.copy');
  copy.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  await tick(dom, 40);
  ok('copy announces via aria-live',
    (doc.getElementById('live').textContent || '').length > 0);

  const rvs = [...doc.querySelectorAll('.reveal')];
  ok('hidden before intersect', rvs.every(e => !e.classList.contains('is-in')));
  w.__ios.forEach(o => o.trigger());
  ok('revealed on intersect', rvs.filter(e => e.classList.contains('is-in')).length > 0);
  ok('observer unobserves after firing (one-shot)',
    w.__ios.every(o => o.els.length === 0));
  dom.window.close();

  dom = make({ io: false }); w = dom.window; doc = w.document; await tick(dom, 60);
  console.log('\n  Graceful degradation (no IntersectionObserver):');
  ok('all content visible', [...doc.querySelectorAll('.reveal')]
    .every(e => e.classList.contains('is-in')));
  ok('accordion still works', (() => {
    const b = doc.querySelector('.gap__btn');
    b.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    return b.getAttribute('aria-expanded') === 'true';
  })());
  dom.window.close();

  dom = make({ reduce: true }); w = dom.window; doc = w.document; await tick(dom, 60);
  console.log('\n  prefers-reduced-motion:');
  ok('all revealed immediately', [...doc.querySelectorAll('.reveal')]
    .every(e => e.classList.contains('is-in')));
  ok('no observers created', w.__ios.length === 0, w.__ios.length + ' created');
  dom.window.close();

  console.log('\n  Lifecycle:');
  ok('teardown registered on pagehide',
    /pagehide/.test(html) && /teardown/.test(html));
  ok('teardown clears the observer list',
    /teardown\.length\s*=\s*0/.test(html));
}

console.log('\n════════════════════════════════════════');
console.log(`  ${pass} passed, ${fail} failed`);
console.log('════════════════════════════════════════\n');
process.exit(fail ? 1 : 0);
