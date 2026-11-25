# Waypoint responsive audit evidence

The [worklog](../../worklogs/2026-11-25-responsive-app-audit.md) records the workflow states, changes, and test limits for each comparison. Read paired images from left to right.

| Original report | Matched visual evidence | Behavior verified |
| --- | --- | --- |
| Overview queue squeezed beside its actions | [854px comparison](../overview-responsive-2026-11-25/comparison-854.png), [390px comparison](../overview-responsive-2026-11-25/comparison-390.png) | Both queue entries and both destination links survive resize |
| Blocked Workbench inquiry | [Phone tab comparison](comparison-workbench-tabs-320.png) | Blocked recovery and editable Trip Details remain reachable |
| Overnight train and missing intake questions | [Matched desktop](../workbench-rail-unslop-2026-11-24/matched-desktop.png), [matched phone](../workbench-rail-unslop-2026-11-24/matched-mobile.png) | All five intake questions appear in order with the feasibility prompt |
| Shared mobile navigation | [More comparison](comparison-mobile-modules-320.png), [New active state](comparison-mobile-new-390.png) | Enabled destinations, separate call capture, and focus behavior |

## Regression evidence

- [Chrome browser suite](playwright-chrome-reviewed.log) and [WebKit browser suite](playwright-webkit-reviewed.log) each passed 32 cases before the later focused additions. The worklog records the focused checks run after those changes.
- [Frontend unit suite](vitest-reviewed.log) passed 1,560 tests across 213 files.
- [Route geometry](agency-current-verified.jsonl), [alias rerun](agency-fast-intake-current.jsonl), and [public geometry](public-current.jsonl) record sampled rendered states at 15 widths. Populated workflows have separate browser evidence.
- [Chromium zoom measurements](browser-zoom-rail.jsonl) and [400% Risk Review capture](zoom/blocked-risk-zoom-400.png) cover the populated Overview queue, fresh intake, and the blocked rail inquiry.
- [WebKit touch emulation](playwright-touch-navigation.log) verifies a trusted touch event and portrait-to-landscape viewport changes. The native Safari attempt and its storage limitation are in the worklog.

The worklog records the broader set of comparisons and the fictional ChatGPT critique. Independent source review and physical-device verification remain open.
