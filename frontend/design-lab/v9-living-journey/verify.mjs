#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(here, 'index.html'), 'utf8');
const css = html.slice(html.indexOf('<style>'), html.indexOf('</style>'));
let pass = 0;
let fail = 0;
const ok = (name, condition, detail = '') => {
  if (condition) { pass += 1; console.log(`  ✓ ${name}`); }
  else { fail += 1; console.log(`  ✗ ${name}${detail ? ` — ${detail}` : ''}`); }
};

console.log('\n-- STRUCTURE --');
ok('single journey canvas exists', /id="journey-map"/.test(html));
ok('four journey states are represented', ['intake', 'decision', 'conflict', 'update'].every((s) => html.includes(`data-stage="${s}"`)));
ok('journey map has accessible label', /canvas[^>]+aria-label="Animated map/.test(html));
ok('state tabs use tab semantics', /role="tablist"/.test(html) && (html.match(/role="tab"/g) || []).length === 4);
ok('reduced-motion media query exists', /prefers-reduced-motion: reduce/.test(css));
ok('reduced motion branch exists', /stateIsReduced\(\)/.test(html));
ok('map loop starts only when motion is allowed', /if \(stateIsReduced\(\) \|\| !playing \|\| running\) return/.test(html));
ok('map loop cancels on pause/offscreen', /cancelAnimationFrame\(raf\)/.test(html) && /new IntersectionObserver/.test(html));
ok('reveal observers disconnect after entry', /obs\.disconnect\(\)/.test(html));
ok('no generic transition: all', !/transition\s*:\s*all/.test(css));
ok('no WebGL dependency', !/WebGL|three\.js|three\/build/i.test(html));
ok('no autoplay video/audio', !/<(?:video|audio)[^>]+autoplay/i.test(html));

console.log('\n-- DESIGN TOKENS --');
const token = (name) => css.match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`))?.[1];
const ratio = (a, b) => {
  const lum = (hex) => {
    const rgb = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
    return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
  };
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + .05) / (lo + .05);
};
for (const name of ['ink', 'muted', 'faint', 'canvas', 'surface', 'surface-2', 'route', 'coral', 'amber']) ok(`--${name} exists`, Boolean(token(name)) || css.includes(`--${name}:`));
ok('body copy contrast on canvas >= 4.5', ratio(token('muted'), token('canvas')) >= 4.5, `${ratio(token('muted'), token('canvas')).toFixed(2)}:1`);
ok('route accent contrast on canvas >= 3', ratio(token('route'), token('canvas')) >= 3, `${ratio(token('route'), token('canvas')).toFixed(2)}:1`);
ok('no purple gradient aesthetic', !/gradient\(/i.test(css));
ok('no backdrop-filter glass', !/backdrop-filter/i.test(css));

console.log(`\n${pass} passed, ${fail} failed`);
process.exitCode = fail ? 1 : 0;
