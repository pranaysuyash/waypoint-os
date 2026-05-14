# Brainstorm Role: Skeptic
**Date:** 2026-05-14  
**Topic:** Workbench / Trip Workspace architecture split — restraint and noise  
**Agent:** Two independent Skeptic agents ran. Both reached consistent conclusions. Composite documented here.

---

## 3 Most Likely Ways This Refactor Creates New Problems for Operators

**1. The "View Trip" navigation lands on `/intake`, not `/ops` — and you're about to add an Ops tab.**

After Spine completes, the operator clicks "View Trip" and lands on `/trips/[id]/intake`. After this refactor, the operator now needs to *know* to click the Ops tab. There is no navigation that says "you just processed a trip, here is the Ops work." Every operator who learned "Workbench has an Ops panel that appears after I run Spine" now has a two-step hunt. The architectural elegance is real. The UX regression is also real and it is not addressed in the original plan.

**2. DecisionTab.tsx is 446 lines. StrategyTab.tsx is 106 lines. These are not stubs.**

DecisionTab has a full `STATE_BADGE_CLASS` lookup table, suitability flag acknowledgment, budget breakdown rendering, and follow-up question handling. That is not a file someone wrote and forgot to wire up — that is a file someone built and then *removed from the tab list without deleting*. The reasons matter: was it A/B tested and removed? Was it moved partially to another tab? Was it intentionally pulled back? Deleting those files based on "they're not imported in the render path" will lose 552 lines of non-trivial logic. "Zero risk" is the wrong characterization — correct characterization is "zero render risk, unknown logic risk."

**3. OpsPanel's `result_validation` carries BLOCKED/ESCALATED semantics that `trip.stage` alone cannot reproduce.**

`result_validation` carries `.is_valid`, `.status === "ESCALATED"`, `.status === "BLOCKED"`, and `.reasons[]`. The stage field on `trip` tells you *where* the trip is in the lifecycle. The `result_validation` tells you *why it is blocked* and what the reasons are. These are not the same signal. If you replace the gate with `trip.stage`, operators lose the inline blocked/escalated warning banner. That banner exists because sometimes a trip is at `proposal` stage but Spine returned `BLOCKED`.

*(Note: Executioner #1 subsequently verified that `trip?.validation` already contains this full signal via API response — the fallback already works. Skeptic concern #3 is therefore addressed by the existing fallback.)*

---

## Strongest Argument for Keeping Ops in Workbench

**Ops is the only part of the product where the AI context (what Spine just recommended) is directly adjacent to the execution action (book this, document this, pay for this).** The operator just ran Spine, saw the decision output, and wants to act on it immediately. The Workbench AI context is all in working memory and on screen. Moving to Trip Workspace means navigating away from that context before acting. For the most consequential action in the product (committing to a booking), context proximity is not a UX nicety — it is a guard against errors.

---

## What Operators Will Notice vs. Not Notice

**Will notice:**
- "The Ops section is gone from Workbench." Even users who never complained about it being there will notice when it is gone.
- If "View Trip" still lands on `/intake`, they will not see an Ops tab immediately and will assume the functionality is missing.
- If "Last processed" date shows wrong value (because `trip.updated_at` ≠ last Spine run), they will notice on any trip that was edited but not recently re-run.

**Will not notice:**
- The cross-boundary store read fix in layout.tsx. Invisible.
- The `WorkspaceStage` type extension. Invisible.
- Dead import removal. Invisible.
- The architectural cleanliness of "one mental model."

---

## What Should Be Cut from the Implementation Plan

**Cut or defer Step 7 (remove Ops from Workbench) by at least one release cycle.** Ship Steps 1–6 first: add Ops to Trip Workspace without removing it from Workbench. Observe. Then remove it when you have evidence that operators have migrated.

*(Note: Executioner #2 argued the opposite — if you don't commit to deprecation now, you get permanent parallelism. Resolution: scope Step 7 to the same or next release, but with a migration signal first.)*

**Cut the "zero risk" characterization for Step 1.** Reclassify as "hidden product intent risk." Keep DecisionTab.tsx and StrategyTab.tsx with a `// DEFERRED: see [issue]` comment. Do not delete 552 lines of business logic because they are not currently rendered.

---

## 3 Strongest Skeptical Insights

1. **The real coupling problem is not `result_run_ts` in the layout — it is that `result_validation` carries semantics that `trip.stage` cannot reproduce.** *(Addressed by existing fallback, but the semantic point stands for the warning banner.)*

2. **The plan protects the Spine run flow from changes but does not protect the operator flow that depends on it.** The `completedTripId` handoff navigates to `/intake`. After this refactor, the correct destination is arguably `/ops`. Deferring the redirect is technically valid. Calling the refactor "complete" without it is not.

3. **The 1404-line OpsPanel is doing too many jobs and decoupling it from the workbench store will surface that problem, not solve it.** Step 5 will either be done incompletely (swap the store, leave the tangle) or will balloon into unreviewable scope mid-implementation. The plan does not scope a component split.

---

**The thing most people miss about this:** The operators who will be most confused by this refactor are not the ones who use the product casually — they are the *power users* who have built muscle memory around the Workbench-to-Ops flow, and they are also the ones most likely to be doing bookings for high-value clients where a moment of disorientation causes a real mistake. Architectural reorganization hurts experts more than novices because experts have automated the old pattern. The plan has no migration signal for power users.

*(Architectural cleanliness is not a user benefit. "One mental model, one durable record" is a pitch to engineers. Operators have a different mental model that already works. You are not clarifying their mental model — you are replacing it with yours. Be honest about which problem is actually being solved.)*
