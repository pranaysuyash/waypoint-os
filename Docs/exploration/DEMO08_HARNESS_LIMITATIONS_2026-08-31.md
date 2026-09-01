# DEMO-08 / DEMO-15 — Computer-Use Demo Harness Limitations

*Date: 2026-08-31*
*Source session: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` (§2 flow log, §4 "Environment caveats").*
*Purpose: document the automation-harness quirks observed during the simulated demo so future sessions do not misattribute harness noise to product bugs.*
*Method: documentation only; the one code claim below (typing/sanitizing) was verified against the codebase with `rg` (read-only).*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## 1. Why this doc exists

The demo ran a macOS computer-use harness (Chrome driven via a DevTools-protocol client) against the local app. Several anomalies observed during the session are **harness-suspect, not product bugs**. Recording them here gives future demo/QA sessions a baseline: check this list before filing a finding, and run the code-check step below before escalating anything input-related.

## 2. Observed harness behaviors

### (a) Synthetic typing drops LETTER keystrokes; digits/punctuation pass — VERIFIED harness-suspect (code-checked)

- **Observed:** typing `"hello world 123"` into the workbench intake textarea landed as `"123"` — every letter (and spaces) dropped, digits intact. An earlier attempt landed as `"33.5++10-12"`.
- **Code verification (the one code claim, confirmed):** `frontend/src/app/(agency)/workbench/IntakeTab.tsx` (292 lines) contains **no `onKeyDown` handlers and no input sanitizers**. `rg "onKeyDown|onBeforeInput|onInput|sanitize|replace\(|filter\("` over the file returns exactly one match — `router.replace(...)` for navigation at `IntakeTab.tsx:65` — which cannot filter characters. The two textareas (`IntakeTab.tsx:174`, `IntakeTab.tsx:198`) are plain controlled components.
- **Conclusion:** the app has no mechanism that could strip letters. The keystroke loss happened between the harness's synthetic key dispatch and the OS/browser event pipeline. **Treat as harness-suspect, not an app bug.** (It was also reproduced once with the window active, so "window not focused" does not fully explain it.)

### (b) macOS Space drift → `window_offscreen` → keyboard/type refusals

- **Observed:** the Chrome window repeatedly reported `window_offscreen` — live bounds still onscreen but `live_on_screen` false (a CGWindow/Space state drift on macOS) — causing keyboard dispatch and `type` to be refused until the window was re-activated.
- **Impact:** mid-flow stalls and retry loops that look like app unresponsiveness if you only read the harness log.
- **Mitigation used in session:** re-activate the window (click/focus) before continuing; keyboard then worked.

### (c) AX tree capture timeouts on heavy pages

- **Observed:** accessibility-tree captures timed out at the 8s wall clock (failure phases: `tree_traversal`, `menu_traversal`) on heavy pages — e.g., 566+ AX nodes on the workbench packet tab.
- **Impact:** capture failures can be misread as "page frozen" or "content missing" when the page is merely large. This also contributed to the `/inbox` renderer-crash window (see `Docs/exploration/DEMO05_INBOX_CRASH_INVESTIGATION_2026-08-31.md` — sustained AX polling is a memory amplifier under dev mode).

### (d) AX `set_value` on a controlled React textarea — inconsistent registration (unverified cause)

- **Observed:** on the **signup form**, AX `set_value` on a controlled input registered with React state (the password strength meter reacted — so React saw the change). On the **workbench textarea**, one Chrome instance showed `set_value` apparently NOT registering with React state.
- **Status:** inconsistent, one instance, cause unverified (candidates: different React controlled-component wiring, IME/composition path, element identity churn after HMR or re-render). Do not treat the workbench instance as a product-bug signal on its own.

### (e) Stale AX/screenshot after client-side navigation

- **Observed:** after an in-app (client-side) navigation, the tab **title** updated (e.g., "Waypoint OS — Lead Inbox") before the page-content capture refreshed, so a screenshot/AX read taken immediately could describe the previous page's content under the new title.
- **Impact:** risk of "page shows X" claims that are actually one-navigation-stale. Always re-capture after navigation settles.

## 3. Isolated-profile Chrome launch command used

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --user-data-dir=/tmp/waypoint-demo-profile \
  --window-position=80,40 \
  <... additional window/flags as used that session>
```

The load-bearing parts are the scratch `--user-data-dir` (isolates the demo profile, cookies, and first-run UX from the operator's daily browser) and an explicit `--window-position` (keeps bounds deterministic for the harness). Recreate with a fresh `--user-data-dir` per session for clean signup/tenant state.

## 4. Guidance for future demo sessions

1. **Prefer `set_value` on fields known to register React state** (verified in this session on the signup form). If a field type is unproven, do one probe set_value and verify before relying on it.
2. **Confirm React state via derived UI, never via the input's displayed value alone** — e.g., password strength meter reacting, "Process Inquiry" button enabling, autosave chip firing. Derived-UI confirmation is the only trustworthy read that state landed.
3. **Re-activate the target window before keyboard dispatch** and verify `live_on_screen` is true; after any Space/desktop change, assume the window needs re-activation (see §2b).
4. **Expect AX-capture timeouts on heavy pages** (566+ nodes); treat capture failure as "retry after settle", not as page-broken. Consider capturing scoped subtrees where the harness supports it.
5. **After client-side navigation, wait and re-capture** title AND content together before asserting what the page shows (see §2e).
6. **Never file harness noise as a product bug without a code check.** Minimum code check for input anomalies: `rg "onKeyDown|onBeforeInput|onInput|sanitize" <component>` — if the component has no key handlers/sanitizers, the app cannot be filtering the input; escalate to harness triage instead.
7. **Distrust first-visit dev-mode timing** as a product signal: first navigation to a route in `next dev` triggers an on-demand compile (172.3s for `/inbox` during the demo — `/tmp/waypoint_frontend.log:368-369`). Pre-warm routes or demo against a production build when timing/robustness claims matter.

## 5. Product bugs confirmed during the session DESPITE the harness

These findings are based on rendered UI state (screenshots + AX tree), independent of the input-mechanics quirks above, and stand:

| Finding | ID | Evidence |
|---|---|---|
| **Lead Inbox promise broken** — blocked draft never appears in `/inbox` ("0 leads total") despite the workbench banner promising "incomplete leads appear in Lead Inbox" | DEMO-01 (P0) | Rendered empty state vs banner copy; workbench explainer strip at `frontend/src/app/(agency)/workbench/PageClient.tsx:964` |
| **Colloquial extraction misses** — "do japan" / "tokyo + kyoto + osaka" → Destination `-`; flexible dates missing; "me and 3 friends" → Party 1 | DEMO-02/DEMO-03 (P1) | Trip Details packet table (rendered output of the pipeline run `draft_22c74baae1d8`) |
| **Sample-profile panel on fresh tenant** — "Alex Morgan — Repeat Client (3 Bookings)" renders pre-processing on a 0-trip account | DEMO-04 (P1) | Overview "Captured Details" panel on a brand-new workspace |

Full details and severity rationale: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` §4 (findings 1–4) and the briefs in `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` (EX-DEMO-01…04). The `/inbox` renderer crash (finding 5) is intentionally NOT in this table — it is under separate investigation with verdict "dev-environment noise (likely)" pending human repro (`Docs/exploration/DEMO05_INBOX_CRASH_INVESTIGATION_2026-08-31.md`).
