# EXPLORE #6 — Group Proxy Negotiation: Scope & Design Sketch

**Date:** 2026-10-26
**Status:** SCOPE DOC — pattern evaluated against existing machinery; implementation gated on group-travel demand signal.
**Origin:** Exploration topic 48 next-step #6 (NTT ai-tour-meeting pattern, AACL-IJCNLP 2026); lineage to Sim #2 Family Summit.

---

## TL;DR

The NTT ai-tour-meeting pattern (multiple LLM persona-agents negotiate a group itinerary) maps onto machinery Waypoint **already has**: per-traveler facts with authority levels, `GroupConsensusOptimizer` (Pareto scoring with the zero-out rule), and the T1 ask-traveler loop. The product form is **not** "multiple chatbots argue" — it's **proxy agents drafting per-traveler preference positions that feed the existing consensus scorer**, with the advisor seeing the trade-off map instead of reading four chat logs. Recommendation: DEFER until a real group-travel demand signal arrives (the optimizer is live but no agency flow exercises it yet), and land it as an *enrichment of GroupConsensusOptimizer inputs*, not a new agent framework.

## The pattern, translated to Waypoint's vocabulary

| NTT ai-tour-meeting | Waypoint equivalent | Status |
|---|---|---|
| Persona-agent per group member | Per-traveler fact profile (`TravelerPreferenceProfile`) | **exists** — `group_consensus.py` |
| Agents argue → converge on itinerary | `GroupConsensusOptimizer.evaluate_group_consensus` (Pareto + zero-out) | **exists**, consensus-scored |
| Members who "can't participate" get proxies | T1 ask-traveler loop answers absent travelers' questions asynchronously | **exists** (token-gated) |
| Negotiation transcript | Advisor-visible compromises list (`compromises_made`) | **exists** in the score |
| LLM-generated proposals | `ItineraryOptionProposal` candidates — today hand/assembler-built | **gap: candidate generation from per-traveler facts** |

## The genuine gap (one, not five)

Everything downstream of "we have N travelers with different budgets/paces" exists and is scored honestly (zero-out rule live). What's missing is the **candidate generator**: turning per-traveler profiles into 3–5 concrete option proposals (budget-tiered, pace-mixed) that the optimizer can score. The E15 tiered-option exploration (2026-09-18) rejected this exact framing *when demand was absent* — its reopen condition was "operator demand once options are operator-visible."

## Scope if triggered (small, additive)

1. `generate_candidate_options(traveler_profiles, trip_facts)` — deterministic templating (budget tiers × pacing mixes), LLM optional for activity selection. ~1 service function + tests.
2. Feed results to the existing optimizer; advisor sees ranked options + compromises.
3. NO new agent framework, NO multi-agent chat — the "negotiation" is the scorer's arithmetic plus the advisor's judgment, matching the concierge doctrine (system proposes, human decides).

## Explicitly out of scope

- Autonomous multi-agent debate loops (token cost, determinism loss, no operator value over scored candidates).
- Direct-to-traveler negotiation UI (the advisor owns client communication — E1 channel doctrine).

## Trigger to reopen

Any of: (a) an agency runs a 4+ traveler group through the workbench; (b) the group-consensus endpoint sees production traffic; (c) the owner requests multi-party planning as a feature. Until then the optimizer + zero-out are the shippable slice, already live.

## Sources

- NTT ai-tour-meeting (AACL-IJCNLP 2026), arXiv:2607.18806 — topic 48 sweep record
- `src/decision/group_consensus.py` (live, zero-out adopted 2026-10-22)
- `Docs/exploration/E15_TIERED_OPTION_GENERATOR_DEMAND_2026-09-18.md` (reopen condition)
- Sim #2 Family Summit per-traveler attribution fixes (memory record)
