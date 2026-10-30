# Council — Open-Item Adjudication (2026-10-30)

**Mandate:** the owner directed that items previously parked as "owner-gated" be put through a persona council: anything decidable under delegated authority (reversible design decisions, per TRV-DP-05) gets decided + documented; the rest stay deferred with the unblock condition named.

**Seats:** Strategist (vision/moat) · Operator (agency workflows / day-1 usability) · Skeptic (attacks each idea) · Security & Compliance (licensing, regulatory, PII) · Champion (owner-proxy priorities).

**Verdict scale:** DECIDED (delegated; decision record + revisit trigger) / DEFERRED (owner-only; named unblock).

## Adjudications

| Item | Verdict | Rationale (seat consensus) | Revisit trigger / unblock |
|---|---|---|---|
| **R2-A** agency-facing agent/MCP API | **DECIDED — direction ratified, build post-pilot** | Strategist: validated twice in one week (Widgety/AirnodeHub agent-data layer; Odessia booking loop) — no competitor serves it; Skeptic: an API is a public contract, but pre-launch nothing breaks and RLS already scopes everything; Security: responses must be provenance-gated (BD framework's `license_tier`/`as_of` contract) — never serve Timatic-tier data through it | First 5 pilot agencies live, or a corporate client asks |
| **R2-B** commission-reconciliation ingest breadth | **DECIDED — adopt the Travefy Sep-2026 bar as acceptance spec** | Operator: #1 practitioner pain at review scale; Skeptic: our `commission_reconciliation.py` existing ≠ matching the bar — the spec is image/CSV/email ingest + fuzzy supplier match + manual-link fallback | Next commission-reconciliation tranche (verify-then-extend) |
| **R2-C** India compliance pack (TCS + GST 2.0) | **DECIDED — architecture: one jurisdiction-aware compliance layer on the quote/booking object; TCS+GST 2.0 = first config set** | Compliance: TCS (5%/20% over ₹7L, PAN-gated) + GST 2.0 effective-dated tax matrix are launch-market obligations; Skeptic: per-country hacks would rot — build-once/config-per-country is the first-principles shape; Security: display/calculation only — payment mandates stay human-approved, no money-movement change | First India pilot agency onboarded; then the quote-engine tranche implements |
| **R2-D** constraint-gate paper protocol ideas | **DONE already** (fed into `CONSTRAINT_DSL_GATE_CORE_PAPER_DESIGN_2026-10-26.md` addendum) | — | Publication decision = owner when paper matures |
| **R2-E** multi-traveler constraint benchmark lane | **DECIDED — publication lane ratified, no build now** | Strategist: the open gap is real (AI Tour Meeting validates no constraints); Skeptic: building a benchmark without a consensus eval corpus is premature | When the group-consensus eval corpus exists |
| **R2-F** agent-resolved-share KPI | **DECIDED — track when inbox analytics ships** | Operator: Navan discloses Ava ≈50% as a margin story; the metric is a trivially cheap addition to the planned inbox analytics tranche | Inbox analytics tranche |
| **R2-G** WhatsApp-group conversational agent | **DEFERRED (recommended, not decided)** | Champion: the giants' admitted blind spot and our consensus moat make it the most exciting lane; Operator+Skeptic: it adds a NEW conversational surface (UX risk + Meta policy surface) while B1 direct channel isn't even flipped live yet — sequencing, not rejection | DP-04b flips live, then pilot-agency demand signal |
| **R2-H** watcher-framework generalization (IRROPS/weather triggers) | **DECIDED — extend the fare-drop trigger taxonomy after the IRROPS expedition lands** | Operator: same decision-desk shape, more triggers; Skeptic: don't generalize before the IRROPS semantics doc exists or the taxonomy inherits its gaps | Next `TicketPriceWatchAgent` tranche, post-IRROPS doc |
| **R2-I** traveler-facing continuous monitoring | **DECIDED — operator-first stays; traveler-visible watching post-pilot only** | Skeptic: Odessia proves consumers reward visible monitoring, but exposing watching to travelers without operator control recreates the Hopper fee-trap class; Operator: agency-branded transparency (advisor recommends) is the defensible form | First 10 pilot-agency trips complete |
| **DP-04a** producer vendor | **DEFERRED — owner** | Money/vendor contract (delegated-authority boundary) | Owner names vendor + budget |
| **DP-04b** WhatsApp direct channel flip | **DEFERRED — owner** | Meta business-account verification credentials | Owner completes Meta verification |
| **51c** bounded-contexts ADR | **DEFERRED — owner** (drafts exist: A=6 contexts vs B=3) | Doctrine posture: ADRs are owner-ratified; council can pre-digest, not decide | Owner picks a draft → unblocks FND-0387 |
| **Facebook authenticated session** | **DEFERRED — owner** | Credentials + ToS posture of the account used | Owner supplies a session or declines |
| **Disk recovery menu** | **DEFERRED — owner** (protected paths per AGENTS.md) | 79G+41G experiment repos, venvs, Downloads are owner data | Owner names targets → unblocks deep Mimosa scan |
| **IDEA-141 GST resurrection** | **RECOMMENDATION recorded, pad untouched** | Compliance: GST 2.0 genuinely re-opens a mispricing wedge, but the pad is the owner's capture surface — the tool protocol puts additions at the pad owner's discretion | Owner adds via `idea_pad_tool.py` or waves it off |

## Net effect

Owner-only residual after this council: **DP-04a, DP-04b, 51c ADR, Facebook session, disk menu, IDEA-141 (pad), R2-G sequencing** — seven items, each with a named unblock. Everything else in the register is now a recorded decision with a trigger, or already executed.

**Evidence base:** round-2 sweep (`EXTERNAL_IDEAS_SWEEP_ROUND2_RESULTS_2026-10-27.md` + TinyFish deep-dive), regulatory digest (§Source 9), delegated-authority ruling (TRV-DP-05), BD governance framework (2026-10-30).
