# Council Decision — Sim #2: the next product simulation (2026-09-12)

Orchestrated via `$council-orchestrator`. Question: *which simulation should
follow the Tool-Taster single-persona demo (verdict: Postpone) to maximize
real-world product learning — including new personas, new ideas, and a
multi-persona customer delegation?*

## Council Manifest

**Lead:** PER-0442 Travel Operating Systems Architect (continuity: led the
previous Waypoint council; owns system-level simulation decisions).

| Seat | Source | Type | Mission |
|---|---|---|---|
| Possibility-Space Explorer | PER-0465 (canonical, read) | Persona | Generate candidate sims beyond delegation |
| Why-Doesn't-This-Exist Analyst | PER-0478 (canonical, read) | Persona | Is "multi-person delegation intake" absent from real products for a structural reason? |
| Capability Gap Analyst | PER-0477 (canonical, read) | Persona | What Waypoint can/can't measure today (feasibility of a graded sim) |
| Consumer UX Designer | PER-1141 (canonical) | Persona | How real group travel planning actually behaves |
| Failure Mode Architect | PER-0924 (canonical) | Persona (skeptic) | Falsify the delegation-sim value case |
| Simulation Designer | bounded speciality (grounded in the Tool-Taster precedent + computer-use harness docs) | Specialist | Convert the decision into a runnable script |

**Coverage:** decision ownership (Lead), domain (travel personas), user/stakeholder
(PER-1141 + sim constructs), implementation (PER-0477 + repo facts), risk
(PER-0924), methods (Simulation Designer + harness docs), counterposition
(PER-0924). **Rejected candidates:** PER-0443/0444 architects (build-side,
duplicate the Lead's lens); PER-0369 Customer Success (post-sale, wrong
workflow); PER-0398 Enterprise Buyer (B2B, not the intake lane).

**Evidence boundary:** canonical persona docs are lenses, not evidence. Repo
facts cited below were verified by search (`rg`) at decision time. Customer
personas are bounded simulation constructs (Tool-Taster precedent) — the
canonical repository intentionally contains no consumer travelers, and none
were invented as canonical.

## Seat findings (condensed)

**PER-0465 (candidate space):** five candidate sims — (a) customer
delegation/multi-persona negotiation, (b) agency-operator day (one agent, 10
messy leads, workbench throughput), (c) repeat-traveler return (memory-loop
verification), (d) corporate booker + policy constraints, (e) crisis replan
(mid-trip disruption). Ranked (a) first: it is the only candidate exercising
multi-actor dynamics no single persona can reach.

**PER-0478 (absence diagnosis):** mainstream AI travel products are
single-user by construction. The absence of multi-traveler delegation is
partly structural — identity, consent, and preference conflict are genuinely
hard — which makes it a *moat-shaped opportunity*: if Waypoint's pipeline
degrades gracefully under group negotiation, that is a differentiator no
chat-assistant competitor currently offers. The sim tests exactly this.

**PER-0477 (feasibility, repo-verified):** `party_composition` is first-class
(`src/intake/extractors.py:1997`); dietary/vegetarian/allergy/mobility tokens
have extraction coverage (9 mobility, 4 vegetarian, 1 allergy hits);
per-person-vs-total budget scope exists (budget fixtures). NOT modeled:
per-traveler preference attribution ("Meera is vegetarian" ≠ "we are
vegetarian"), intra-group conflict representation, delegation/approval
workflow. Conclusion: the sim is feasible AND will surface real gaps — which
is the learning objective, not a blocker.

**PER-1141 (UX reality):** real group trips are negotiated in WhatsApp
threads and one overworked organizer — not clean briefs. The sim must feed
multi-voice, contradictory, asynchronous notes; a polished single brief would
measure nothing.

**PER-0924 (skeptic):** two failure modes — (1) the sim measures extraction
theater rather than product value → mitigate by tying pass/fail to business
surfaces (quote correctness, blocked-lead follow-up, conflict surfacing), not
field cosmetics; (2) cheaper alternative = synthetic fixtures → rejected:
group phrasings are already fixture-covered; the untested learning target is
multi-actor dynamics, which fixtures cannot produce. Skeptic accepts the sim
WITH the business-surface criteria.

## Recommendation

**Sim #2 — "The Family Summit": a real customer delegation.** Four personas
(bounded sim constructs) planning one Japan trip through conflicting needs,
run live via computer-use against the real intake flow, exactly like the
Tool-Taster demo (same verification standard: servers on :8000/:3005, real
sessions, screenshots verified before claims).

### The delegation (sim constructs, clearly non-canonical)

| Persona | Voice | Conflicts they carry |
|---|---|---|
| **Priya** (organizer/booker) | channel-of-record; practical, budget-capped | holds the total budget (₹3.5L hard cap); wants one decision |
| **Arjun** (adventure friend) | enthusiastic, price-insensitive pushes | scuba + nightlife; mocks the "boring" options |
| **Meera** (anniversary couple w/ Dev) | sensitive to occasion + diet | Jain food, no heights/cable cars (callback to demo note), quiet lodging |
| **Dev** (Meera's partner) | peacemaker, date-flexible | will trade dates for price; contradicts Arjun on pace |

### Flow (asynchronous multi-voice, per PER-1141)

1. Priya's opening note (destination Japan, flexible dates, "budget we'll
   figure out").
2. Arjun's contradicting voice-note (add Osaka nightlife + scuba; "spring is
   overrated, go in December").
3. Meera's constraints note (Jain meals, no heights, anniversary dinner,
   quiet ryokan not party hostel).
4. Dev's compromise note (dates ±1 week for ₹40k savings; split 2 rooms).
5. The **group-chat dump** — all four voices interleaved in one messy paste.
6. Priya's follow-up: "so what's the plan and what does each of us owe?"

### Pass/fail criteria (business surfaces, per the skeptic)

- **Identity & party resolution:** party = 4 adults + composition drift
  detected across notes (2 couples).
- **Constraint retention:** Meera's Jain + no-heights + anniversary survive
  to the packet/quote surface with attribution (per-traveler, not group-wide
  — expected FAIL: per-traveler attribution is not modeled; the finding is
  the point).
- **Conflict surfacing:** December-vs-spring and party-hostel-vs-ryokan
  contradictions surface as follow-up questions or advisor-visible flags —
  not silently resolved by last-writer-wins.
- **Budget integrity:** per-person vs ₹3.5L total not double-counted
  (regression guard from the X-05 fix).
- **Follow-up quality:** blocked/escalated lead asks the questions a real
  agent would ask (which rooms, who decides, occasion date).
- **No crashes / no fabricated values** (demo P0 regression guard).

### Recording

Full-fidelity doc per the demo standard: flow, per-criteria verdicts,
findings register rows, harness limitations, buy/postpone verdict for the
*delegation capability* (not the whole product).

## Runner-up candidates (ranked for later sims)

2. **Agency Operator Day** (Sim #3 candidate) — exercises workbench
   throughput, priority/triage, quote workflow; complements delegation's
   intake focus. 3. Repeat-Traveler Return — verifies the memory loop
   end-to-end. 4. Crisis Replan — mid-trip disruption; needs lifecycle
   features that are PREVIEW_ONLY today (defer). 5. Corporate booker +
   policy — deferred until corporate policy lane exists.

## Material dissent

PER-0924 argued the delegation sim's extraction findings will overlap the
existing colloquial fixture coverage (~50% of the pass/fail criteria touch
already-gated phrasings). Resolution adopted: the sim's NEW learning target
is formally scoped to multi-actor dynamics (attribution, conflict, delegation
flow), with phrasing-level findings recorded but not counted as new.

## Next action

Owner go/no-go on Sim #2 script → then execute live (computer-use, ~60–90
min, same verification standard as Tool-Taster). Falsifier for this
recommendation: if the live run produces zero findings beyond existing
fixture coverage AND zero delegation-workflow gaps, the multi-persona sim
premise was wrong and Sim #3 (Operator Day) takes priority.
