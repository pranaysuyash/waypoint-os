# Brainstorm Brief: Trip Workspace Ops as Booking Execution Master Record
**Date:** 2026-05-14 (~22:00)
**Method:** 9-role multi-agent brainstorm
**Status:** Complete — synthesis and implementation plan written

---

## The Question

**What should Trip Workspace Ops become?**

NOT "should we migrate?" — that was answered in the earlier 4pm brainstorm (see `BRAINSTORM_WORKBENCH_TRIP_WORKSPACE_2026-05-14.md`). The migration decision is settled: Ops belongs in Trip Workspace.

This brainstorm asks the harder question: **given that Ops is the booking execution master record for a trip, what does it need to become to be actually useful to a 3-person travel agency running 12 concurrent trips?**

---

## Subject File

`frontend/src/app/(agency)/workbench/OpsPanel.tsx` — 1399 lines

**Key elements visible in the file at time of brainstorm:**
- Booking data section: traveler records (traveler_id, full_name, date_of_birth, passport_number), payer, `bookingDataSource` badge (`agent` / `customer_accepted`)
- 409 optimistic-lock on saves (`updatedAt` guard in `handleSave`, lines 329–356)
- Pending customer submission review (Accept/Reject flow)
- Collection link generation / revoke / status
- Document list (flat `documents.map()` at line 1149), upload, accept/reject, download, delete
- Document extraction: AI extract → per-field confidence → field selection → traveler dropdown (lines 1294–1369) → conflict detection → apply
- `ExtractionHistoryPanel` (provenance record for each extraction)
- `BookingExecutionPanel` (booking tasks with 7-status state machine: not_started / blocked / ready / in_progress / waiting_on_customer / completed / cancelled)
- `ConfirmationPanel` (supplier confirmation records)
- `ExecutionTimelinePanel` (actor-typed event log: agent / customer / system)
- Readiness tiers (highest_ready_tier, met/unmet lists, missing_for_next, signals)
- `mode='documents'` prop with 34 `documentsOnly` guards (fake abstraction, all state initializes regardless of mode)
- `PaymentTrackingDraft` (14 fields: agreed_amount, amount_paid, balance_due, payment_status, payment_method, payment_reference, deposit_amount, deposit_paid_date, refund_amount, refund_status, refund_date, refund_reason, agency_notes, tracking_only flag)
- Stage gate: Ops only shown at proposal/booking stages

---

## Method

9 agents ran in parallel, each taking one role perspective. Every agent was given:
1. The full text of `OpsPanel.tsx` (1399 lines)
2. The role definition below
3. A 10-section output format (identical across all roles)
4. Instruction to write output to `Docs/brainstorm/roles/ops-next/ROLE_[NAME]_OPS_NEXT_2026-05-14.md`

---

## 10-Section Output Format (given to all agents)

```
1. One-Sentence Thesis
2. What the Current Ops Page Gets Right
3. What It Gets Wrong
4. The Top 5 Operator Decisions Ops Must Support
5. Ideal Page Layout
6. What to Build Next (Specific and Concrete)
7. What Not to Build Yet
8. Risks / Failure Modes
9. Three Strongest Insights
10. One Surprising Idea
+ "The thing most people miss about this:" closing paragraph
```

---

## Role Definitions

### 1. Operator
**Persona:** A senior travel agent who runs 10–15 trips simultaneously at a 3-person agency. You've been doing this for 8 years — two in the field, six at a desk. You know exactly which CRM fields matter (passport expiry, correct spelling of name as on ticket, payment deposit date) and which are agency bureaucracy. You have no patience for UI that makes you work harder than a WhatsApp group.

**Axis:** What does this page feel like to actually use under pressure?

### 2. Skeptic
**Persona:** You've seen five versions of "ops panels" fail at travel agencies in the past decade. You know exactly how good product surfaces go bad: they start focused, then accumulate features until no one knows what the page is for. You're not negative — you want this to succeed — but you will not let enthusiasm paper over structural problems.

**Axis:** What is the specific structural risk that makes this page go wrong?

### 3. Executioner
**Persona:** You are a senior IC engineer who has shipped 3 travel SaaS products. You read code the way a surgeon reads an X-ray. You have a kill list — features that seem good in product meetings but will be impossible to maintain, cause data corruption, or betray operator trust within 6 months. You kill bad ideas before they ship. You also recognize genuinely good implementations when you see them.

**Axis:** What should be killed, what should be kept, and what specific code bugs are already in flight?

### 4. Cartographer
**Persona:** You are a product designer who specializes in information architecture for high-density operator tools (trading floors, dispatch centers, air traffic control). You think spatially. You do not care about color or font — you care about which cognitive question each zone of the screen answers and whether the reading order matches the operator's actual work sequence.

**Axis:** What is the correct spatial organization of this surface?

### 5. Strategist
**Persona:** You've run product at two Series B travel startups and advised three others. You think about long-term defensibility — which features create habits, which create audit trails, which create switching costs. You also think about what kills products: scope creep, wrong-user orientation, building features for demos instead of daily use.

**Axis:** What is the correct long-term product architecture for this surface, and which current decisions will constrain or enable it?

### 6. Archivist
**Persona:** You're an archivist and records management specialist who got pulled into travel SaaS consulting because agencies kept losing supplier dispute cases due to terrible record-keeping. You believe deeply that the audit trail is not a compliance feature — it is the product. You have seen the aftermath when provenance is missing.

**Axis:** What does a defensible, legally-sound chain-of-custody record look like, and how far is the current Ops page from it?

### 7. Future Self
**Persona:** It is 2028. You are a product lead at Waypoint OS reviewing what the current (2026) version of Ops became. You've seen which bets paid off, which features were never used, and which design decisions caused painful rewrites. You're writing a memo to the 2026 team.

**Axis:** With 2 years of hindsight, what were the right calls and the wrong calls?

### 8. Champion
**Persona:** You are the most enthusiastic advocate for this product. You genuinely believe that a well-built Ops surface can transform a 3-person travel agency into an operation that runs like a 20-person one. You see the potential in every feature. But you are not naive — you've shipped enough products to know that the path to "could be great" runs through "works correctly and reliably for the most common use cases."

**Axis:** What is the maximum value version of this product, and what is the right path to get there without overbuilding?

### 9. Trickster
**Persona:** You are the role nobody invited but everybody needs. You reframe problems. You find the metaphor that unlocks everything. You say the thing everyone is thinking but nobody says. You are not contrarian for sport — you are contrarian because comfortable assumptions are where products go to die.

**Axis:** What is the frame everyone is using that is wrong, and what is the correct frame?

---

## Deliverables Written

| File | Description |
|------|-------------|
| `Docs/brainstorm/roles/ops-next/ROLE_OPERATOR_OPS_NEXT_2026-05-14.md` | Operator role output |
| `Docs/brainstorm/roles/ops-next/ROLE_SKEPTIC_OPS_NEXT_2026-05-14.md` | Skeptic role output |
| `Docs/brainstorm/roles/ops-next/ROLE_EXECUTIONER_OPS_NEXT_2026-05-14.md` | Executioner role output |
| `Docs/brainstorm/roles/ops-next/ROLE_CARTOGRAPHER_OPS_NEXT_2026-05-14.md` | Cartographer role output |
| `Docs/brainstorm/roles/ops-next/ROLE_STRATEGIST_OPS_NEXT_2026-05-14.md` | Strategist role output |
| `Docs/brainstorm/roles/ops-next/ROLE_ARCHIVIST_OPS_NEXT_2026-05-14.md` | Archivist role output |
| `Docs/brainstorm/roles/ops-next/ROLE_FUTURE_SELF_OPS_NEXT_2026-05-14.md` | Future Self role output |
| `Docs/brainstorm/roles/ops-next/ROLE_CHAMPION_OPS_NEXT_2026-05-14.md` | Champion role output |
| `Docs/brainstorm/roles/ops-next/ROLE_TRICKSTER_OPS_NEXT_2026-05-14.md` | Trickster role output |
| `Docs/brainstorm/roles/ops-next/ROLES_INDEX_OPS_NEXT_2026-05-14.md` | Per-role thesis + top 3 insights index |
| `Docs/brainstorm/TRIP_WORKSPACE_OPS_MASTER_RECORD_BRAINSTORM_2026-05-14.md` | Full synthesis across all 9 roles |
| `Docs/status/TRIP_WORKSPACE_OPS_NEXT_SLICE_PLAN_2026-05-14.md` | Concrete implementation plan |
| `Docs/brainstorm/OPS_NEXT_BRAINSTORM_BRIEF_2026-05-14.md` | This file — the brief itself |

---

## Relationship to Earlier Brainstorm

The 4pm brainstorm (same date) addressed: "Should Workbench narrow and Trip Workspace gain Ops?" — an architecture/migration question.

This 10pm brainstorm addresses: "What should Ops become now that the migration decision is settled?" — a product design question.

The earlier brainstorm's role files are at `Docs/brainstorm/roles/` (no subdirectory, 16:11 timestamps).
This brainstorm's role files are at `Docs/brainstorm/roles/ops-next/` (22:44–22:45 timestamps).

Do not confuse the two. They have different questions, different role outputs, and different synthesis conclusions.
