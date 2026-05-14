# Brainstorm Role: Champion
**Date:** 2026-05-14  
**Topic:** Workbench / Trip Workspace architecture split  
**Agent:** general-purpose subagent (code-aware)  
**Note:** Two Champion agents ran independently and reached consistent conclusions. This is the composite.

---

## Why the Two-Surface Model Is Wrong

The split isn't a UX preference problem. It's a **cognitive jurisdiction problem**.

When an operator closes a booking, they need to see the client's original request, the itinerary they built, the supplier confirmations, the payment state, and the next pending action — simultaneously. All of that is trip-level context. None of it is transient. Splitting execution (Ops) from record (Trip Workspace) forces the operator to maintain a mental join table. That join table has a cost, and in a 2-person shop, that cost compounds every time they context-switch.

The two-surface model made architectural sense when Workbench was genuinely transient — you run Spine, you get results, you move on. The session ends. But Ops destroyed that assumption. Ops is not transient. Booking execution takes days. Document management takes weeks. Payments trail the whole lifecycle. The moment Ops moved into Workbench, Workbench stopped being a processing tool and became a half-baked trip manager that doesn't know it.

**The product's own code is trying to tell you this.** `Shell.tsx:141` hides the word "Workbench" from users entirely. The nav doc says `/workbench` is not a durable module name. The breadcrumb already calls it "New Inquiry." The product, in its small daily decisions, has been slowly renaming this surface to something more honest — but the architecture hasn't caught up.

---

## What Operator Behavior This Damages

**1. The return trip.** Operator completes a Spine run, sees "View Trip," goes to Trip Workspace. Does their review. Wants to create a booking. Has to navigate back to Workbench. This is not a UX annoyance — it's a signal that the mental model is broken. In a well-designed tool, you never navigate *away from the record* to *act on the record*. The record is home. Everything happens at home.

**2. The interrupted session.** Operator is in the middle of Ops work — booking a flight, tracking a deposit. They close the tab, open a fresh session. `result_run_ts` in the Trip Workspace layout reads from the in-memory Workbench store, which is now empty. The "last processed" timestamp is gone. This erodes operator trust in small, invisible ways.

**3. The handoff moment.** In a 3-person shop, the founder runs Spine, then hands off to an assistant for booking. The assistant gets a trip URL. They have no Ops access. They have to either know to navigate to Workbench (how?) or ask where to find it. The single durable home model fixes this because the trip URL is the whole story.

---

## What the Single Durable Home Model Unlocks

**Sharing and delegation become trivial.** A trip URL is a complete context. You can paste it in Slack. You can bookmark it. You can hand it to a new hire and they see everything — trip details, risk review, ops status, documents. The two-surface model makes none of this possible because "the trip" is split between two URLs.

**Trust in the record.** Operators who trust their tool make fewer mistakes. The moment the tool has one clear answer to "where is the status of this trip?" — the answer is always the trip URL — cognitive overhead drops and the tool becomes load-bearing infrastructure, not a reference to check and verify.

**Feature coherence going forward.** Every feature you build in Trip Workspace from this point forward can assume Ops data is present. Want to show booking status in the trip overview? It's there. Want a timeline that includes "booking confirmed" events alongside AI processing events? The data is in one place. The two-surface model would require stitching Workbench store state into Trip Workspace features forever, and that debt compounds.

---

## What Would Have to Be True for This Thesis to Be Definitively Correct

1. Operators actually go back to Workbench to do Ops work after completing a Spine run (not just in theory, but in actual session recordings or support tickets). Your design doc's navigation analysis confirms this: there is no entry point to `/trips/[tripId]/ops/` because that page doesn't exist. So they *must* go back to Workbench. The behavior is forced, not chosen.

2. Ops work is genuinely trip-scoped, not session-scoped. It is. Booking execution is tied to the trip record, not to the Spine run that produced it. A booking doesn't expire when the browser tab closes.

3. Trip Workspace is already the durable home in every other dimension. It is. Seven tabs covering intake through timeline. The only thing missing is Ops.

All three are true. The thesis is correct.

---

## The Two Things That Could Make It Wrong (And Why They Don't)

**Objection 1: Workbench is where the AI context lives. Moving Ops to Trip Workspace loses the connection between AI output and operational action.**

This sounds right but isn't. The AI context is already surfaced in Trip Workspace — that's what the packet, risk review, and output tabs are. The `result_validation` store coupling in OpsPanel is an implementation artifact, not a design requirement. You replace it with a trip-stage readiness signal and the coupling dissolves. The AI context follows the trip record, as it should.

**Objection 2: Some operators re-run Spine on existing trips, which requires Workbench.**

True, and this is why Option C (redirect all existing trips away from Workbench) is premature. But this objection doesn't defend the two-surface model for Ops — it only defends keeping Workbench alive as a "creation and AI re-processing" tool. Which is exactly what the thesis recommends. Workbench stays. It just stops pretending to own the full trip lifecycle.

---

## Three Strongest Arguments

1. **The product already voted.** The shell breadcrumb, the nav doc, the `completedTripId` push to Trip Workspace on run completion — these are design decisions made incrementally by developers who felt the friction. The architecture is lagging behind the product's own expressed intent.

2. **Ops is permanent state, not session state. It was never right to put it in Workbench.** Booking execution is a business record. The moment a booking is created, it belongs to the trip, not to the Spine session that justified it.

3. **One URL, one truth, one operator workflow.** You gain: shareability, delegation, bookmarking, feature coherence, reduced cognitive overhead, clean API for future features. You lose: nothing except the ability to say "Ops is in Workbench" — which was never a feature, just an accident.

---

**The thing most people miss about this:** The two-surface model isn't a design problem — it's a trust problem. When a tool doesn't have a single authoritative place for a record, operators don't trust any of its places. They keep their own spreadsheets. The tool becomes a convenience, not a system of record. Making Trip Workspace the single durable home is about making the tool load-bearing enough that operators stop hedging it with external workarounds. That's the actual product outcome.
