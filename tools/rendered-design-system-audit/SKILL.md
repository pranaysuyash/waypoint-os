---
name: rendered-design-system-audit
description: |
  Systematic visual audit of a rendered frontend by extracting the actual design
  system from the browser DOM and comparing it against DESIGN.md.
category: frontend
---

# Rendered Design System Audit

Trigger when asked to audit frontend visual design, check styling consistency,
or reconcile the rendered site against DESIGN.md.

## Usage

```bash
# Default: launch headless browser + audit all pages
node tools/rendered-design-system-audit/index.mjs --serve

# Connect to your signed-in Chrome (for app page access):
# First, launch Chrome with remote debugging:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Then run the audit using CDP:
node tools/rendered-design-system-audit/index.mjs --cdp http://localhost:9222

# Custom pages and faster wait strategy:
node tools/rendered-design-system-audit/index.mjs \
  --pages /,/login,/inbox,/settings \
  --wait domcontentloaded

# Output in custom location:
node tools/rendered-design-system-audit/index.mjs \
  --out /tmp/audit-output
```

### Options

| Flag | Description |
|------|-------------|
| `--url` | Base URL (default: http://localhost:3000) |
| `--out` | Output directory |
| `--pages` | Comma-separated page paths |
| `--serve` | Start dev server first |
| `--cdp` | Connect to Chrome via CDP (use your signed-in profile) |
| `--wait` | Wait strategy: `load`, `domcontentloaded`, `networkidle` |

## Audit Workflow

### Phase 1: Capture Baseline
- Screenshot every page (full-page, 2x DPI)
- Capture performance metrics (TTFB, load time)
- Save to `audit-output/screenshots/`

### Phase 2: Extract True Design System
- Extract all CSS custom properties from `:root`
- Extract computed styles from every element (colors, typography, spacing)
- Capture component-level tokens (cards, buttons, inputs, badges)
- Identify touch target violations (< 44px)

### Phase 3: Compare Against DESIGN.md
- Background colors vs `--bg-*` tokens
- Text colors vs `--text-*` tokens
- Accent colors vs `--accent-*` tokens
- Geographic colors vs `--geo-*` tokens
- Border colors vs `--border-*` tokens
- Spacing scale vs `--space-*` tokens

### Phase 4: Report
- CSS Token compliance score
- Per-page visual audit tables
- Discrepancies & issues list
- Prioritized recommendations

## Known Pitfalls

| Pitfall | Workaround |
|---------|------------|
| App pages redirect to login | Use `--cdp` with your signed-in Chrome |
| `networkidle` timeout | Use `--wait domcontentloaded` |
| Playwright browsers not installed | `npx playwright install chromium` from tools/ |

## File Reference

| File | Purpose |
|------|---------|
| `index.mjs` | Main audit script (Playwright-based) |
| `SKILL.md` | This file — skill instructions |
| `audit-output/DESIGN_AUDIT_REPORT.md` | Generated audit report |
| `audit-output/screenshots/` | Page screenshots |

## Hermes Skill Origin

This tool was built from the skill at `~/.hermes/skills/frontend/rendered-design-system-audit/SKILL.md`
and extended with full Playwright automation for DOM extraction + DESIGN.md comparison.
