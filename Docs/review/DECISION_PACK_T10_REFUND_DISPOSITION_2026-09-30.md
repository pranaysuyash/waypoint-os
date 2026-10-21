# Decision Pack — T10: Refund/Compensation Disposition (FND-0233)

**Date:** 2026-09-30
**Status:** ⚖️ DECIDE — research complete, recommendation made, **owner gate open**
**Decision owner:** Pranay (operator gate per council protocol — this doc does not self-execute)
**Canonical finding:** FND-0233 (open-noted; scope revised 2026-09-29 by launch council)
**Related:** T9 (confirmation defect grading — shipped; designed to link re-shop credits here)

---

## 1. Background (how this decision arose)

The 2026-08-30 findings register flagged FND-0233: "Refund/compensation
pipeline dead-ends (`passenger_rights_claims.py` + payment refund constants);
no disposition grading or re-shop credit path."

The 2026-09-29 launch-readiness council **revised the scope on live code**: this
is *not* a dead-end. What actually exists today (verified in-tree):

- `spine_api/routers/passenger_rights.py` — mounted (`server.py:1593`), auth-gated.
- `POST /evaluate` — statutory compensation evaluation under **EU261 /
  UK261 / US-DOT** (distance-tiered amounts; EU261 €250–€600 bands).
- `POST /{trip_id}/generate-claim` — formal airline claim-letter generation.
- Backed by `spine_api/services/passenger_rights_claims.py`
  (`evaluate_statutory_compensation`).

**The genuine gap:** no disposition ledger. After a claim letter is generated,
nothing tracks submitted → airline accepted/rejected/partial → paid →
re-shop credit. `PAYMENT_REFUND_TRACKING_STATUS_2026-05-12.md` deliberately
placed money-movement tracking out of scope by design. The council therefore
queued T10 as an owner gate: **wire disposition grading vs archive the lane
honestly** (wire-or-archive ADR protocol; ambiguous drift is the rejected
outcome).

## 2. Market research (2026-09-30)

**Evidence class note:** the web-search quota was exhausted until 2026-10-06 at
research time. What follows is stable regulation (citable law) plus
well-established industry structure (labeled as such). Live-source re-citation
is queued for the 10-06 quota reset — falsifier below.

### 2.1 The stable legal layer (citable regulation)

- **EU261 (Regulation EC 261/2004):** the *operating airline* — not the
  agency — owes passengers €250–€600 in compensation for cancellations/long
  delays within its scope, independent of ticket price. The agency's lane is
  assistance, not liability.
- **EU Package Travel Directive (2015/2302), Arts. 13–14:** for **package**
  bookings, the organizer/retailer that sold the package is *itself* on the
  hook for disruption remedies — rerouting or refund **within 14 days**,
  repatriation, cost coverage. For packages, tracking "what did we owe this
  customer and did they get it" is **compliance, not goodwill**.

### 2.2 The market layer (industry structure; re-cite live on 10-06)

- **A claim-farming industry exists precisely because travelers won't chase
  airlines.** AirHelp, Flightright, EUclaim, Skycop, Compensation2Go do one
  thing: pursue compensation claims for a cut — typically **25–35% of the
  payout** (of a €600 award, ~€180–210 goes to the middleman). AirHelp alone
  reports checking tens of millions of flights. Willingness to hand over a
  third of the money is the strongest possible demand signal.
- **OTAs run it in-house.** eDreams/Opodo and Kiwi.com operate claim handling
  for bookings made through them — a service differentiator, since the airline
  is the payer.
- **Human travel advisors live on it.** "We fight the airline for you" is a
  core selling point of full-service agents; it became publicly famous during
  COVID, when advisors spent months recovering billions in refunds/credits
  while airlines went silent (widely reported via ASTA and press).
- **Corporate travel managers industrialized it.** Amex GBT / CWT / BCD run
  refund-and-credit tracking as standard back-office service with SLAs — the
  corporate segment explicitly treats "track it to the end" as part of the job.
- **Partner model exists:** claim agencies offer referral/partner programs, so
  an agency can also monetize by routing — but an agency that recovers the
  full amount *free as part of service* undercuts both airlines and the
  25–35% middlemen as a trust position.

### 2.3 Implication

The market has already voted: travelers ask for this, pay heavily for it when
agencies don't provide it, and for package bookings the agency is legally
obligated to remedy disruptions regardless. An evaluation-and-letter boundary
(Option B) puts the product on the wrong side of customer expectation and,
for packages, of the Directive's remedy duties.

## 3. Options

### Option A — Wire a minimal disposition ledger (RECOMMENDED)

Claim disposition state machine (drafted → submitted → accepted/rejected/
partial → paid → re-shop credit) + operator-visible tracking surface + T9
re-shop-credit linkage. **Does not move money** — it is the scorecard, not the
bank; payment processing stays with the payment stack per the 2026-05-12 scope
doc.

- Value: completes the loop on the already-built statutory engine; closes the
  "pipeline ends where the operator's work begins" failure class; T9 linkage
  becomes real; compliance evidence for package remedies.
- Cost: M tranche (states + persistence + 2 endpoints + small operator surface
  + tests). Built on an already-mounted, already-authenticated router.

### Option B — Archive the lane honestly (evaluation-only boundary)

ADR recording: statutory evaluation + claim-letter generation is the product
boundary; follow-up is the agency's job outside the system. Annotate/remove the
refund-tracking vocabulary so nothing implies a ledger exists.

- Value: near-zero cost; honest boundary.
- Cost: IRROPS money-loop stays manual forever; product sits opposite market
  expectation; for packages, remedy tracking happens outside the system that
  evaluated the entitlement — the exact silent-failure class the audit
  doctrine targets.

### Rejected third state

Leave as-is (built, mounted, ambiguous). The council's wire-or-archive
protocol rejects this: a lane that looks like a pipeline but dead-ends is
worse than an absent one.

## 4. Discussion record

| Question raised | Finding |
|---|---|
| Do people ask agencies to do this? | Yes — the claim-farm industry's 25–35% take rate is the demand proof; advisors/TMCs treat it as core service |
| Do agencies track it? | TMCs industrialized it with SLAs; OTAs run in-house handling; package-sellers must (Directive arts. 13–14) |
| Is the agency legally liable? | Under EU261, no (airline is payer); under the Package Travel Directive for packages, yes for remedies |
| Does wiring imply payment processing? | No — ledger tracks/reminds; money movement stays out of scope (2026-05-12 doc) |
| Why not leave it ambiguous? | Council protocol rejects unbuilt-but-implied capability; silent gaps are the audited failure class |

## 5. Recommendation

**Option A**, scoped as above. The expensive half (statutory engine + claim
generation) is built, mounted, and authenticated; the ledger is the cheap half
that makes it valuable and completes the designed T9→T10 credit linkage.

## 6. Decision block

- Decision: ☑ **A (wire)** — with owner hard constraint: **the system never
  initiates, holds, or receives money.** No payment processing, no gateways,
  no payment instruments, no balances. The ledger records outcomes of money
  that moved *elsewhere* (airline → traveler, directly). Enforced by an
  always-on invariant test.
- Decided by / date: Pranay, 2026-09-30 ("do it then" after the no-money
  constraint was stated).
- Tranche scope: disposition state machine (pure module + tests), disposition
  riding the existing `passenger_claim` trip record, GET/PATCH on the existing
  mounted router (no new route file), generate-claim auto-creates the
  disposition, claim-letter wording corrected (airline pays passengers
  directly — removed "agency trust ledger" language), minimal operator surface.
- Invariant guard: `tests/test_claim_disposition.py::test_no_payment_code_paths`.

## 7. Falsifier / revisit trigger

- **Research falsifier:** if live-source checks (quota reset 2026-10-06) show
  the claim-agency commission model or OTA in-house handling claims are
  materially wrong, revisit §2 before deciding.
- **Decision revisit:** Option A's ledger should be revisited if the payment
  stack later absorbs disposition tracking natively (then this becomes a
  display integration, not a ledger).

## 8. Provenance

- Finding: FND-0233 (imported 2026-09-10 as F-16 alias; council scope note
  2026-09-29 event 565).
- Council rows: `Docs/review/LAUNCH_READINESS_TASK_INVENTORY_2026-09-29.md`
  lines 31, 77–78, 125 (T10 REVISED scope).
- Market research session: 2026-09-30 (this document); live re-citation queued
  2026-10-06.

---

## 9. Implementation record (2026-09-30, same session — tranche shipped)

**Built (Option A under the no-money constraint):**
- `spine_api/services/claim_disposition.py` — pure 8-state machine
  (DRAFTED → SUBMITTED → AIRLINE_{ACCEPTED,PARTIAL,REJECTED} / ESCALATED →
  TRAVELER_PAID → CLOSED), terminal-freeze, illegal-transition rejection,
  30-day airline-response overdue nudge (read-time computation, no jobs).
- `spine_api/routers/passenger_rights.py` — extended (no new route file):
  generate-claim auto-creates the disposition (state SUBMITTED);
  `GET /{trip_id}/claims/{claim_id}/disposition` (overdue computed);
  `PATCH` (operator records reality; 409 on illegal/terminal transitions;
  audited). Claim letter corrected: **airline remits directly to passengers**
  — the previous "agency trust ledger" wording violated the owner constraint
  and was removed.
- `spine_api/contract.py` — `TripResponse.passenger_claim` added (closes the
  silent-strip that would have made the ledger operator-invisible; same
  failure class as the branch_options serving gap).
- FE: `ClaimDispositionCard` (parcel-tracking model) mounted on the trip
  decision page; Trip type extended; 4 component tests.

**The invariant, in code:** `tests/test_claim_disposition.py::
test_no_payment_code_paths` scans the entire lane for payment vendors and
funds-movement patterns and fails the build if any appear — the scorecard can
never quietly become a bank. State vocabulary itself is guarded against
custody-implying names.

**Evidence:** disposition suite 11/11 (wiring guard S2: failed RED before
router wiring, GREEN after); endpoint integration 5/5 (real generate→get→patch
flow, terminal-freeze 409, illegal-transition 409, 404s, TripResponse
carriage); FE key suites 22/22 + typecheck clean; ruff clean. RETRACTED baseline framing (owner-called, 2026-09-30): the original text
recorded `test_passenger_rights_api_endpoint` as "pre-existing baseline,
not this tranche" — a mine/theirs dodge that violates the blast-radius
doctrine (the test lives in the edited file, exercising the edited
router). Fixed in the same pass: the test had been coupled to the
DB-provisioning `session_client` although `/evaluate` needs no database;
it now uses the file's hermetic client with all assertions unchanged.
File is 9/9 green with a clean exit (the failed DB provisioning was also
the cause of the 5-minute pytest exit hang).

**FND-0233:** closed with this evidence. Remaining linkage (T9 re-shop credit
→ disposition) is future work when T9's credit path lands.
