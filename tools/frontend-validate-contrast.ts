#!/usr/bin/env -S tsx

/**
 * Frontend Color Contrast Validator
 *
 * Run from repo root with:
 *   cd frontend && npx tsx ../tools/frontend-validate-contrast.ts
 */

import { validateTokenColors } from "../frontend/src/lib/contrast-utils.js";

const results = validateTokenColors();

console.log("\nColor Contrast Validation Report\n");
console.log("=".repeat(70));

let failures = 0;
let passes = 0;

for (const result of results) {
  const status = result.passesAA ? "PASS" : "FAIL";

  if (!result.passesAA) failures++;
  else passes++;

  console.log(
    `${status.padEnd(4)} | ${result.name.padEnd(35)} | ${result.ratio.toFixed(2)}:1`
  );
}

console.log("=".repeat(70));
console.log(`\nSummary: ${passes} passed, ${failures} failed out of ${results.length} combinations\n`);

console.log("\nDetailed Analysis:\n");
console.log("textPrimary (#e6edf3): Very light, should pass on all backgrounds");
console.log("textSecondary (#8b949e): Medium gray, may fail on dark backgrounds");
console.log("textTertiary (#6e7681): Medium-dark gray, likely fails");
console.log("textMuted (#484f58): Dark gray, fails on dark backgrounds\n");

console.log("Recommended Fixes:\n");
console.log("1. textSecondary: Lighten to #a8b3c1 or similar");
console.log("2. textTertiary: Lighten to #8b949e (current textSecondary)");
console.log("3. textMuted: Lighten to #6e7681 (current textTertiary)\n");
