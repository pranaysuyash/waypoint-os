# Blocked inquiry header and repair flow

24 November 2026 · Local Workbench · Uncommitted

## Why the earlier pass missed it

The [7 November unslop worklog](2026-11-07-unslop-and-design-spells-signup-handoff.md) names signup, login and the intake handoff. The [Goa workflow replay](2026-11-24-goa-feasibility-workbench-replay.md) checked advisory parity and a completed run with follow-up. Neither record establishes acceptance of a blocked run with its inherited title, actions and validation feedback. The operator screenshot shows the consequence. The original row put the title next to an action form that could claim nearly the entire content width once the inline error and run panel both appeared.

The current source also had overlapping ownership. The run hook surfaced a terminal blocked response as both structured state and a thrown error. The Workbench rendered both. The run panel then concatenated the structured reasons with backend prose synthesized from those same reasons. The persistent banner had two links to the identical repair URL.

## Changes and preservation

The unslop audit found a local spacing and hierarchy failure, duplicated copy and actions, and a warning border that rendered white. The existing Waypoint dark palette, outline icons and monospace identifiers fit the dispatch interface. The header now gives the title a full row and wraps action buttons independently. Below the toolbar, the run panel owns the blocked summary and repair action. The page retains unrelated error and save messages, and completion shows one run acknowledgement. The persistent banner retains the Review Missing Fields link to the existing repair route, including a supported field deep link, or the Trip Details tab for a draft. No state transition, API schema or backend write path changed.

A parallel change introduced the scoped feasibility action while this work was in progress. Its branch, question decoder and tab handler were preserved. Test inputs and their request routes were isolated from existing workspace records.

## Evidence

- [Desktop comparison](../evidence/workbench-blocked-unslop-2026-11-24/desktop-comparison.png) and [390px comparison](../evidence/workbench-blocked-unslop-2026-11-24/mobile-comparison.png) show before on the left and after on the right. Both sides use the same full-page Chrome fixture and viewport. The fixture does not seed risk findings, so its Risk Review content area is empty. The operator screenshot remains the evidence of the original extreme title compression. The controlled baseline reproduces duplicate warnings and the expanded toolbar, and the captures were inspected.
- Playwright at 1440 and 390 CSS pixels checks title width, a single warning and summary, page overflow, expanded run details and the repair tab. The exact summary assertion failed before and passed after at both widths (S2 for duplicate copy). Browser flow with synthetic responses is Tier 3, and rendered browser observations are Tier 4. The layout checks passed after the fix.
- Focused frontend verification passed 155 tests across the Workbench, blocking-copy and run hooks. The persisted-trip test now asserts one repair link and the same route. Focused Python verification passed 45 tests across feasibility and pipeline execution boundaries.
- Full frontend baseline recorded 1,523 passes and 13 failures across public marketing, two traveler visual suites, and the PacketPanel assumptions test. The first post-change full run also found the old two-link assertion and hit ENOSPC. Its logs are preserved. The repair test was updated to check the intended invariant and passed in the focused run. The complete rerun with `--pool=threads` reported 1,523 passes and the same 13 named failures. There were zero new failure identities.

- The [Goa before/after](../evidence/workbench-blocked-unslop-2026-11-24/goa-comparison.png) pairs the operator's original screenshot with a fresh [live local Chrome replay](../evidence/workbench-blocked-unslop-2026-11-24/live-goa-risk-review.png). They use distinct drafts. Signup returned 201, session verification 200 and run status 200 with `blocked / ESCALATED / STOP_NEEDS_REVIEW`. The Risk Review advisory rendered and Trip Details opened. These were real HTTP calls against isolated local test services. The standalone booking smoke could not start with its default Playwright browser because the bundled Chromium executable was missing.
- The final browser spec uses the canonical `/inquiries/new` entry and verifies the accessibility state of the run-details control. Both viewport cases passed. TypeScript and diff checks passed. Targeted ESLint reported zero errors and the existing process callback dependency warning.

## Review boundaries

The current browser viewport evidence is local. Hosted behavior, physical-device interaction and customer acceptance remain unverified. Backend health returned 200. The unauthenticated metrics probe returned 401. No Git mutations were performed. Existing unrelated changes in the Workbench and repository were preserved.
