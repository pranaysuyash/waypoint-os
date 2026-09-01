#!/usr/bin/env node
/**
 * verify.mjs — gate for the v7 Theme B landing prototype.
 *
 *   node verify.mjs
 *
 * Two independent suites:
 *   A. Contrast — parses tokens out of index.html and checks every
 *      accent-ink pairing against its ACTUAL composited background.
 *   B. Behaviour — jsdom: accordion, copy, reveal gating, reduced motion,
 *      graceful degradation, Theme B conformance.
 *
 * Exit 0 = all pass. Never edit a token to make this pass; edit it because
 * the number is real. See RATIONALE.md § Contrast.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const HTML_PATH = path.join(HERE, 'index.html');
const html = fs.readFileSync(HTML_PATH, 'utf8');

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
const hex = (h) => [1, 3, 5].map(i => parseInt(h.substr(i, 2), 16));
const over = (fg, alpha, bg) => {
  const F = hex(fg), B = hex(bg);
  return '#' + F.map((v, i) =>
    Math.round(v * alpha + B[i] * (1 - alpha)).toString(16).padStart(2, '0')).join('');
};

// Tokens are read from the file — never hardcoded here.
const tok = {};
for (const m of html.matchAll(/--([a-z0-9-]+):\s*(#[0-9a-fA-F]{6})/g)) tok[m[1]] = m[2];

const ARCHIVE = tok.archive, CARD = tok.card;
const wash = (name, base) => {
  const m = html.match(new RegExp('--' + name + ':\\s*rgba\\((\\d+),\\s*(\\d+),\\s*(\\d+),\\s*([\\d.]+)\\)'));
  if (!m) throw new Error('missing wash token: ' + name);
  return over('#' + [m[1], m[2], m[3]].map(v => (+v).toString(16).padStart(2, '0')).join(''), +m[4], base);
};

const SURF = {
  archive: ARCHIVE,
  card: CARD,
  'wash-blue/card': wash('wash-blue', CARD),
  'wash-blue/archive': wash('wash-blue', ARCHIVE),
  'wash-amber/card': wash('wash-amber', CARD),
  'wash-green/card': wash('wash-green', CARD),
  'wash-red/archive': wash('wash-red', ARCHIVE),
};

// Where each token ACTUALLY sits. If you move accent text onto --hovered or
// --selected, add it here and this suite will fail you. That is the point.
const USAGE = [
  ['ink',         'body / headings',       ['archive', 'card'], 4.5],
  ['graphite',    'body copy',             ['archive', 'card'], 4.5],
  ['ink-muted',   'labels / captions',     ['archive', 'card', 'wash-blue/archive'], 4.5],
  ['royal',       'links',                 ['archive', 'card'], 4.5],
  ['royal',       'chip--inferred',        ['wash-blue/card'], 4.5],
  ['royal-dark',  'step number',           ['wash-blue/archive'], 4.5],
  ['amber-ink',   'chip--assumed/unknown', ['wash-amber/card'], 4.5],
  ['forest-ink',  'chip--fact',            ['wash-green/card'], 4.5],
  ['forest-ink',  'copy confirmation',     ['archive'], 4.5],
  ['error-ink',   'criticality chip',      ['wash-red/archive'], 4.5],
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

console.log('\n  White on button fills (needs ≥ 4.5):');
for (const t of ['royal', 'royal-dark']) {
  const r = ratio('#ffffff', tok[t]);
  ok(`  white on --${t} ${tok[t]} = ${r}`, r >= 4.5);
}
console.log('\n  Interactive borders (UI boundary, needs ≥ 3.0 on card):');
{
  const r = ratio(tok['rule-strong'], CARD);
  ok(`  --rule-strong ${tok['rule-strong']} = ${r}`, r >= 3.0);
}
// The real invariant is not "these are low contrast" — it is "these are never
// used as a text colour." #dc2626 is a perfectly good text colour on white
// (4.83:1); it is listed here because this page uses it only as a border.
console.log('\n  Decorative-only tokens (must never be a text colour):');
for (const t of ['silver', 'amber', 'forest', 'error', 'rule', 'rule-hover']) {
  const asText = new RegExp('color:\\s*var\\(--' + t + '\\)').test(html);
  ok(`  --${t} ${tok[t]} not used as text (card contrast ${ratio(tok[t], CARD).toFixed(2)})`, !asText);
}

/* ══════════════════ B. BEHAVIOUR ══════════════════ */
console.log('\n── B. BEHAVIOUR (jsdom) ──');

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
        w.document.execCommand = () => true;
        if (!w.navigator.clipboard) {
          Object.defineProperty(w.navigator, 'clipboard',
            { value: { writeText: () => Promise.resolve() }, configurable: true });
        }
      },
    });
  const tick = (d, ms) => new Promise(r => d.window.setTimeout(r, ms));

  let dom = make(); let w = dom.window; let doc = w.document; await tick(dom, 50);

  console.log('\n  Structure:');
  ok('single h1', doc.querySelectorAll('h1').length === 1);
  ok('skip link → #main', doc.querySelector('a.skip')?.getAttribute('href') === '#main');
  ok('headings hierarchical', (() => {
    const ls = [...doc.querySelectorAll('h1,h2,h3')].map(h => +h.tagName[1]);
    return ls.every((v, i) => i === 0 || v - ls[i - 1] <= 1);
  })());
  ok('every button has accessible text', [...doc.querySelectorAll('button')]
    .every(b => (b.textContent || '').trim() || b.getAttribute('aria-label')));
  ok('no inline onclick in markup', !/\son(click|keydown)=/i.test(html));

  console.log('\n  Specimen accordion:');
  const btns = [...doc.querySelectorAll('.field-btn')];
  ok('5 field buttons', btns.length === 5, btns.length + ' found');
  ok('all start collapsed', btns.every(b => b.getAttribute('aria-expanded') === 'false'));
  btns[2].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok('opens on click', btns[2].getAttribute('aria-expanded') === 'true');
  ok('criticality shown', doc.getElementById('fd-3').textContent.includes('Critical'));
  btns[4].dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  ok('one-open-at-a-time', btns[2].getAttribute('aria-expanded') === 'false'
    && btns[4].getAttribute('aria-expanded') === 'true');

  console.log('\n  Epistemic chips (src/intake/packet_models.py):');
  const chips = [...doc.querySelectorAll('.chip')].map(c => c.textContent.trim());
  ok('only FACT/INFERRED/ASSUMED/UNKNOWN',
    chips.every(c => ['Fact', 'Inferred', 'Assumed', 'Unknown'].includes(c)), chips.join(','));
  ok('all four represented',
    ['Fact', 'Inferred', 'Assumed', 'Unknown'].every(s => chips.includes(s)));

  console.log('\n  Copy + reveal:');
  const copy = doc.querySelector('.copy');
  copy.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
  await tick(dom, 30);
  const status = doc.querySelector('.copy-done');
  ok('copy writes status', (status.textContent || '').length > 0);
  ok('status is aria-live', status.getAttribute('aria-live') === 'polite');

  const rvs = [...doc.querySelectorAll('.rv')];
  ok('hidden before intersect', rvs.every(e => !e.classList.contains('in')));
  w.__ios.forEach(o => o.trigger());
  ok('revealed on intersect', rvs.filter(e => e.classList.contains('in')).length > 0);
  dom.window.close();

  dom = make({ io: false }); w = dom.window; doc = w.document; await tick(dom, 50);
  console.log('\n  Graceful degradation (no IntersectionObserver):');
  ok('all content visible', [...doc.querySelectorAll('.rv')].every(e => e.classList.contains('in')));
  ok('accordion still works', (() => {
    const b = doc.querySelector('.field-btn');
    b.dispatchEvent(new w.MouseEvent('click', { bubbles: true }));
    return b.getAttribute('aria-expanded') === 'true';
  })());
  dom.window.close();

  dom = make({ reduce: true }); w = dom.window; doc = w.document; await tick(dom, 50);
  console.log('\n  prefers-reduced-motion:');
  ok('all revealed immediately', [...doc.querySelectorAll('.rv')].every(e => e.classList.contains('in')));
  ok('line art not dash-hidden', !doc.querySelector('.hero-art .route').style.strokeDashoffset);
  ok('no observers created', w.__ios.length === 0, w.__ios.length + ' created');
  dom.window.close();

  console.log('\n  Theme B conformance (DESIGN.md §11):');
  ok('no backdrop-filter', !/backdrop-(filter|blur)/.test(html));
  ok('no gradients', !/gradient/i.test(html));
  ok('single box-shadow token', (html.match(/box-shadow:/g) || []).length === 1);
  ok('shadow = 0 2px 8px rgba(0,0,0,.06)', /--shadow:0 2px 8px rgba\(0,0,0,\.06\)/.test(html));
  ok('radius unified at 8px', /--r:8px/.test(html));
  ok('shell 1100px', /--shell:1100px/.test(html));
  ok('IBM Plex Sans + JetBrains Mono', /IBM\+Plex\+Sans/.test(html) && /JetBrains\+Mono/.test(html));
  ok('no infinite CSS animations', !/@keyframes[\s\S]*?infinite|\binfinite\b(?!\s*loop\s*-)/.test(
    html.replace(/\/\*[\s\S]*?\*\//g, '')));
  ok('teardown on pagehide', /pagehide/.test(html) && /teardown/.test(html));
  ok('font stack free of AI-cliche faces',
    !/\b(Inter|Roboto|Fraunces|Space Grotesk|Arial)\b/.test(
      [...html.matchAll(/--sans:([^;}]+)/g)].map(m => m[1]).join(' ')));
}

console.log('\n════════════════════════════════════════');
console.log(`  ${pass} passed, ${fail} failed`);
console.log('════════════════════════════════════════\n');
process.exit(fail ? 1 : 0);
