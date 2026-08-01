/**
 * pii-worker.js — Client-side PII pre-scrubber Web Worker.
 *
 * Runs in an isolated worker context. Receives text from popup.js,
 * scans it with regex patterns optimized for Indian travel inquiry PII,
 * and returns structured findings with severity.
 *
 * Severity levels:
 *   'red'   — hard PII: Aadhaar, PAN, passport, credit card, full phone
 *   'amber' — soft PII: partial phone, email, generic ID-like patterns
 *   'clear' — no findings
 *
 * Redaction: returned `redacted` field masks the matched value (e.g. ****1234)
 * so the banner can show the user what was found without exposing the full value.
 *
 * Design decisions:
 *   - Pure regex: no ML, no external calls, works fully offline
 *   - India-specific patterns: Aadhaar (12 digits), PAN (ABCDE1234F),
 *     Indian passport (A1234567), +91 prefix phones
 *   - Intentionally conservative on 'amber' to prefer false positives over
 *     false negatives in a PII context (travel inquiry text is sensitive)
 *   - Does NOT send any data externally. Runs in isolated Worker thread.
 *
 * For server-side NLP-enhanced PII detection, see src/security/privacy_guard.py
 *
 * Reference: Evaluated models considered for local inference (documented in
 * Docs/ADR_PII_GUARD_SPACY_LAYER2_2026-07-29.md):
 *   - SpaCy en_core_web_sm (12MB) → server-side (Layer 2)
 *   - Regex + NLTK tokenizer → eliminated (Python-only)
 *   - Gemma2-2B-IT (client-side ONNX) → deferred (4GB, not mobile-viable)
 *   - Transformers.js (HF) → deferred (requires bundle > 50MB for NER)
 *   - Maziyar/mdeberta-v3-base-pii → server eval pending (800MB baseline)
 *   Conclusion: regex is the right client-side layer; server-side SpaCy is Layer 2.
 */

'use strict';

// ===========================================================================
// Pattern definitions
// ===========================================================================

const RED_PATTERNS = [
  {
    label: 'Aadhaar number',
    pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
    severity: 'red',
  },
  {
    label: 'PAN card',
    pattern: /\b[A-Z]{5}[0-9]{4}[A-Z]\b/g,
    severity: 'red',
  },
  {
    label: 'Indian passport number',
    pattern: /\b[A-PR-WY][1-9]\d{6}\b/g,
    severity: 'red',
  },
  {
    label: 'Credit/debit card number',
    pattern: /\b(?:\d{4}[\s-]?){3}\d{4}\b/g,
    severity: 'red',
  },
  {
    label: 'Indian mobile number',
    pattern: /(?:\+91[-\s]?|0)?[6-9]\d{9}\b/g,
    severity: 'red',
  },
  {
    label: 'Email address',
    pattern: /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g,
    severity: 'red',
  },
];

const AMBER_PATTERNS = [
  {
    label: 'Partial phone / number sequence',
    pattern: /\b\d{8,9}\b/g,
    severity: 'amber',
  },
  {
    label: 'Date of birth pattern',
    pattern: /\b(?:0?[1-9]|[12]\d|3[01])[\/-](?:0?[1-9]|1[0-2])[\/-](?:19|20)\d{2}\b/g,
    severity: 'amber',
  },
];

// ===========================================================================
// Scan function
// ===========================================================================

function scan(text) {
  const findings = [];

  for (const { label, pattern, severity } of [...RED_PATTERNS, ...AMBER_PATTERNS]) {
    // Reset stateful regex
    pattern.lastIndex = 0;
    const matches = [...text.matchAll(pattern)];

    for (const match of matches) {
      const value = match[0];
      const redacted = redact(value);
      findings.push({ label, redacted, severity, offset: match.index });
    }
  }

  // Deduplicate overlapping matches (prefer red over amber at same offset)
  const deduped = deduplicateFindings(findings);

  const severity =
    deduped.some((f) => f.severity === 'red')
      ? 'red'
      : deduped.length > 0
      ? 'amber'
      : 'clear';

  return { findings: deduped, severity };
}

// ===========================================================================
// Helpers
// ===========================================================================

function redact(value) {
  const clean = value.replace(/[\s\-]/g, '');
  if (clean.length <= 4) return '****';
  const visible = clean.slice(-4);
  const masked = '*'.repeat(clean.length - 4);
  return `${masked}${visible}`;
}

function deduplicateFindings(findings) {
  // Remove amber findings that overlap with red findings (red takes priority)
  const red = findings.filter((f) => f.severity === 'red');
  const amber = findings.filter((f) => f.severity === 'amber');

  const redOffsets = new Set(red.map((f) => f.offset));
  const filteredAmber = amber.filter((f) => {
    // Remove amber if within 2 chars of a red match offset (likely same match)
    return ![...redOffsets].some((ro) => Math.abs(ro - f.offset) <= 2);
  });

  return [...red, ...filteredAmber].slice(0, 10); // Cap at 10 findings for UI
}

// ===========================================================================
// Worker message handler
// ===========================================================================

self.onmessage = (event) => {
  const { type, text } = event.data;

  if (type === 'SCAN') {
    if (!text || typeof text !== 'string') {
      self.postMessage({ findings: [], severity: 'clear' });
      return;
    }
    const result = scan(text);
    self.postMessage(result);
  }
};
