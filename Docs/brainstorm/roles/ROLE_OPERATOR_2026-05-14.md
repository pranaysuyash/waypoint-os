# Brainstorm Role: Operator
**Date:** 2026-05-14  
**Topic:** Workbench / Trip Workspace architecture split — ground-level workflow  
**Agent:** general-purpose subagent (code-aware)

---

## Operator Workflow: Inquiry to Booking Confirmed

### Step-by-Step Map

**Step 1 — Inquiry lands**  
Operator sees: WhatsApp message, email, or voicemail. Raw intent, often vague ("we want 10 days in Japan, 4 people, sometime in March").  
Operator does: Extracts names, dates, budget hints, special requests. Pastes or types into Workbench.  
Currently lives: Wherever the inquiry came in. Manual copy-paste into the system.  
Friction: Zero structure. The operator is the parser. A missed detail here echoes through every downstream step.

**Step 2 — Spine AI run**  
Operator sees: Processing indicator, then structured packet — destinations, traveler count, date windows, preference signals.  
Operator does: Reviews the packet, corrects Spine misreads, fills gaps Spine couldn't infer.  
Currently lives: Workbench.  
Friction: Low at this step — this is where Workbench earns its keep.

**Step 3 — Options + Quote**  
Operator sees: Supplier options, pricing blocks, availability windows.  
Operator does: Curates options, applies markup, assesses risk (seasonality, availability tightness, payment deadlines).  
Currently lives: Workbench (options) + Trip Workspace (risk review).  
Friction: First surface split. The operator has to mentally hold quote numbers in their head while flipping to risk context.

**Step 4 — Proposal output sent**  
Operator sees: Generated proposal document.  
Operator does: Reviews, edits, sends to client.  
Currently lives: Workbench output panel.  
Friction: Low. Clean handoff — but the moment the client says "yes," the operator is about to fall into a hole.

**Step 5 — Client confirms, booking execution begins** ← THE CRITICAL BREAK  
Operator sees: Needs to know which traveler is paying which leg, what data is still missing, which supplier needs to be booked first, what the payment schedule is.  
Operator does: Collects traveler booking data (passports, DOBs, frequent flyer numbers), sends collection links, starts booking tasks supplier by supplier.  
Currently lives: Back in Workbench (OpsPanel).  
Friction: **Critical break.** The operator just left the Trip Workspace after client confirmation and has to navigate back to Workbench. The Trip Workspace has no Ops tab, so the durable per-trip record is incomplete — the booking execution context lives in a different surface entirely.

**Step 6 — Document collection + payment tracking**  
Operator sees: Who has submitted docs, who hasn't, which payments have cleared.  
Operator does: Chases missing docs, reconciles payments against supplier deadlines, uploads and reviews airline tickets and hotel vouchers.  
Currently lives: Workbench OpsPanel.  
Friction: The operator is running a live trip-coordination task inside a tool designed for AI creation. The Workbench UI metaphor is wrong — creation tools feel provisional; ops needs permanence and status clarity.

**Step 7 — Confirmation tracking**  
Operator sees: Per-booking confirmation status — PNR numbers, hotel refs, transfer vouchers.  
Operator does: Verifies each confirmation against the original booking, flags gaps, sends client confirmation summary.  
Currently lives: Workbench.  
Friction: No single view that ties timeline (Trip Workspace) to confirmation status (Workbench). The operator is stitching two surfaces together in their head.

---

## The 5 Micro-Decisions Waypoint Must Make Easier

1. **"What's still missing before I can book?"** — Traveler data gaps, unsigned docs, unpaid deposits. Today this requires scanning multiple panels.
2. **"Which supplier do I book first, and when is their deadline?"** — Sequencing errors cost money. There's no priority-ordered booking queue.
3. **"Has this payment cleared, and does it match the supplier requirement?"** — Payment reconciliation is manual cross-referencing today.
4. **"Is this trip safe to book?"** — Risk signals (availability, seasonality, supplier reliability) live separately from the booking action. They need to be co-located.
5. **"What does the client still need to sign off on?"** — Approval gates before each booking action are implicit today, not enforced by the UI.

---

## What Gets Worse vs. Better

**Gets worse if Ops moves to Trip Workspace:**
- Workbench loses its natural exit — need a clear transition trigger
- Trip Workspace tabs multiply — risk of tab overload if added naively

**Gets better:**
- The per-trip record becomes complete — every material fact in one place
- Context isn't rebuilt at every surface switch
- Confirmation and risk become adjacent — can review them in the same session

---

## Three Strongest Insights

1. **The current model treats Ops as a creation activity — it isn't.** Ops is record-keeping and coordination. It belongs in the durable record, not the scratch pad.
2. **The trip lifecycle has one natural home: the Trip Workspace.** Workbench is a runway, not a destination. Once a trip leaves Spine, it should live entirely in Trip Workspace.
3. **The hardest moment in the operator's day is Step 5.** Client says yes, execution begins, and the tool sends you backward. That backward navigation is where trips go wrong.

---

**The thing most people miss about this:** The operator's anxiety isn't about features — it's about not knowing what they forgot. The product's real job isn't to organize information, it's to surface the one thing the operator would have missed at 6pm on a Friday.
