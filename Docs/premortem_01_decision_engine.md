# PRE-MORTEM: Waypoint OS Decision Engine Integrity

**Date**: 2026-05-05
**Assumed Outcome**: Launch has failed.
**Focus**: Decision pipeline — suitability scoring, override logic, confidence scoring, context rules, hardcoded destination logic.
**Role**: Saboteur (cold glee — finding the seam that tears)

---

## FINDING 1: Confidence Score Is a Flat Average That Lies in Both Directions

1. **WHAT GOES WRONG**: `compute_confidence()` treats all field confidences as equally important, producing a score that understates danger on risky trips and overstates danger on safe ones.
2. **CHAIN OF EVENTS**: `scoring.py` line 216-222 builds `field_confidence` dict: `intensity: 0.95`, `age_bounds: 0.6`, `tags: 0.0` (no tags), `duration: 0.0` (no duration), `weight_bounds: 0.5`. `confidence.py` line 25-26 computes `sum(values) / len(values)` = (0.95+0.6+0.0+0.0+0.5)/5 = 0.41. A high-intensity scuba dive with full age data gets 0.41 confidence. A low-risk temple visit with no tags and no duration also gets ~0.41. The confidence number is decorrelated from actual decision quality.
3. **USER EXPERIENCE**: Agency operator sees "confidence: 0.41" on a critical elderly exclusion and also on a trivial advisory. They learn to ignore the number entirely. When a genuinely uncertain result appears (new destination, incomplete data), the low confidence carries no weight because everything is low.
4. **EMOTIONAL IMPACT**: Helplessness — the gauge is broken so you stop looking at the dashboard.
5. **WHY TEAM MISSES IT**: Unit tests verify the arithmetic (mean of values) not the semantics (should missing `tags` on a museum visit penalize confidence as much as missing `intensity` on a bungee jump?). No weighted confidence exists in the test corpus.
6. **LIKELIHOOD x IMPACT**: H x major
7. **TRUST DAMAGE**: M
8. **RECOVERABILITY**: moderate — requires per-field importance weights and a migration
9. **EARLIEST SIGNAL**: Beta agencies ask "what does confidence mean?" or ignore it consistently in UX sessions.
10. **VERIFY BY**: Run scoring on 20 real trip packets from beta agencies; check correlation between confidence and operator override rate. Near-zero correlation confirms the failure.

---

## FINDING 2: Destination Aliases Map Paris/London to "Europe" — A Key That Doesn't Exist

1. **WHAT GOES WRONG**: The `_DESTINATION_ALIASES` dict at decision.py:799-808 maps "Paris" → "Europe" and "London" → "Europe", but `BUDGET_BUCKET_RANGES` has no "Europe" entry, causing these cities to silently fall through to the generic `__default_international__` cost table.
2. **CHAIN OF EVENTS**: Client requests Paris trip with ₹2,50,000 budget. `_resolve_bucket_table("Paris", packet)` hits the alias → looks up "Europe" in `BUDGET_BUCKET_RANGES` → fails → falls back to `__default_international__` (flights: ₹25-50K). Paris flights are actually ₹40-80K and hotels ₹30-55K (the Paris-specific entry that EXISTS in the ranges table is never reached). Budget decomposition says "realistic" when it should say "borderline". The Maldives resort-premium check on line 1078 correctly catches Maldives-specific risk, but Paris gets no equivalent because its data is orphaned.
3. **USER EXPERIENCE**: Agency quotes a Paris trip at the system's estimated low end. Margin evaporates when actual hotel and flight costs come in 40-60% above the default international table. Client gets sticker shock atrevision time. Agency loses trust in the budget tool.
4. **EMOTIONAL IMPACT**: Betrayal — the system said it could handle Europe.
5. **WHY TEAM MISSES IT**: The alias map and the ranges table are 400 lines apart in the same file. No integration test exercises the alias → lookup → fallback path with an assertion on which table was actually used. The Paris and London entries in `BUDGET_BUCKET_RANGES` (lines 737-756) exist but are unreachable dead code.
6. **LIKELIHOOD x IMPACT**: H x catastrophic (Paris and London are top-5 Indian outbound destinations)
7. **TRUST DAMAGE**: H
8. **RECOVERABILITY**: easy — fix the alias map or remove it; but undetected financial damage from wrong quotes in beta is hard
9. **EARLIEST SIGNAL**: Any Paris/London quote comes back with flights at ₹25,000-50,000 instead of ₹40,000-80,000.
10. **VERIFY BY**: `python -c "from src.intake.decision import _resolve_bucket_table, BUDGET_BUCKET_RANGES; print(_resolve_bucket_table('Paris', type('P',(object,),{'derived_signals':{}})()))"` — if the result is `__default_international__` instead of the Paris entry, the alias is broken.

---

## FINDING 3: Toddler Age Cutoff Contradiction Between Decision.py and Integration.py

1. **WHAT GOES WRONG**: `decision.py:1202` defines toddlers as age < 4, but `integration.py:125` defines toddlers as age < 5, creating a seam where 4-year-olds get suitability risk flags that the decision engine ignores.
2. **CHAIN OF EVENTS**: A family with a 4-year-old child enters intake. `integration.py:125` labels them "toddler" and generates `suitability_discourage_*` flags for cultural and water activities. These flags arrive in `generate_risk_flags()` at decision.py:1314-1324. Simultaneously, the old rule path at decision.py:1199-1208 checks `ages.value if a < 4` and finds zero toddlers, so it generates NO `toddler_pacing_risk` flag. The decision engine's blocker logic sees suitability flags as advisory (severity "high" not "critical") while missing the pacing risk entirely. The 4-year-old falls through the gap.
3. **USER EXPERIENCE**: Operator sees scattered suitability warnings for a 4-year-old but no coherent "toddler pacing risk" summary. The trip proceeds without the transfer-complexity and stamina flags a toddler classification would trigger. Family shows up at airport with a 4-year-old and a 6-transfer itinerary. Operator is blamed.
4. **EMOTIONAL IMPACT**: Guilt and anger — "the system knew something was wrong but didn't connect the dots."
5. **WHY TEAM MISSES IT**: The two age thresholds are in different modules maintained at different times. `integration.py` was written during the suitability implementation (2026-04-18) while `decision.py:1202` predates it. No cross-module test asserts that both use the same threshold.
6. **LIKELIHOOD x IMPACT**: H x major (4-year-olds are common in Indian family travel)
7. **TRUST DAMAGE**: H
8. **RECOVERABILITY**: easy code fix, hard to recover from a family that had a bad experience
9. **EARLIEST SIGNAL**: A 4-year-old appears in a beta trip and the risk summary shows suitability flags but no toddler_pacing_risk.
10. **VERIFY BY**: Create a test packet with `child_ages=[4]`, run both `extract_participants_from_packet()` and the decision.py toddler check; assert the same label/count.

---

## FINDING 4: Static Activity Catalog Has Zero Destination Scoping — Every Trip Gets Warned About Snorkeling

1. **WHAT GOES WRONG**: All 18 activities in `STATIC_ACTIVITIES` have `destination_keys=[]` (catalog.py), meaning suitability scoring runs water-based and mountain activity checks against desert-city trips and vice versa.
2. **CHAIN OF EVENTS**: Client plans a Dubai shopping and desert trip. `generate_suitability_risks()` at integration.py:210-211 (when no specific activity_ids) defaults to `STATIC_ACTIVITIES[:5]` = snorkeling, scuba_diving, white_water_rafting, hiking_easy, hiking_difficult. Every single one is water-based or hiking. Elderly travelers get flagged with `suitability_discourage_snorkeling`, `suitability_exclude_white_water_rafting`, `suitability_discourage_hiking_easy`. None of these activities are available in Dubai. The risk panel is 100% noise. The operator clicks through all of them. When a real risk appears (desert_safari for elderly in humid climate), it's not in the catalog at all.
3. **USER EXPERIENCE**: Risk panels become "the boy who cried wolf." Operators learn to dismiss all suitability flags. Critical warnings get the same mental treatment as irrelevant snorkeling warnings.
4. **EMOTIONAL IMPACT**: Annoyance → habituation → dismissal. The tool becomes furniture.
5. **WHY TEAM MISSES IT**: The catalog was designed as a "baseline" with the intent to add per-destination filtering later. But the integration layer already ships to beta with no destination filter. The `destination_keys` field on `ActivityDefinition` exists but is always empty. The team assumes the data gap will be filled before launch; it won't be.
6. **LIKELIHOOD x IMPACT**: H x major
7. **TRUST DAMAGE**: M (slow erosion, not a single catastrophic event)
8. **RECOVERABILITY**: moderate — requires populating destination_keys on all 18 activities and adding a filter in integration.py
9. **EARLIEST SIGNAL**: Beta operators say "why is it warning me about snorkeling for a Dubai trip?" or simply never click the suitability panel.
10. **VERIFY BY**: Run `generate_suitability_risks()` with a Dubai-destination packet; count how many of the 5 default activities are relevant to Dubai. If answer > 0, the catalog isn't scoped.

---

## FINDING 5: Hardcoded Elderly Risk Destination Set Misses the Most Dangerous Actual Destinations

1. **WHAT GOES WRONG**: `risky_dests = {"Maldives", "Andaman", "Andamans", "Bhutan", "Nepal"}` (decision.py:1192) omits the destinations that actually cause the most elderly medical emergencies: Switzerland (altitude sickness), Peru/Machu Picchu (altitude + limited medical), Thailand rural areas (humidity + dengue), and any cruise destination (norovirus + limited medical).
2. **CHAIN OF EVENTS**: An elderly couple books a Swiss Alps trip. The set doesn't include "Switzerland" or any Swiss city. No `elderly_mobility_risk` flag is generated. The trip proceeds to booking. At 2,500m altitude, one traveler develops acute mountain sickness with no pre-trip altitude advisory. Meanwhile, "Andaman" and "Andamans" are both in the set — a redundant entry suggesting the list was hand-typed from memory, not derived from incident data.
3. **USER EXPERIENCE**: Agency gets a medical emergency call on a Swiss trip with no pre-trip warning from the system. They trusted the system to flag elderly risks and it was silent on the #1 actual risk destination for Indian elderly travelers.
4. **EMOTIONAL IMPACT**: Fear — "what else doesn't the system know about?"
5. **WHY TEAM MISSES IT**: The set was created by the solo founder based on personal travel experience (island destinations feel risky) rather than medical incident data. The CORE_INSIGHT document (line 57-60) already flags this: "Why these 5? What makes Bhutan risky but not Switzerland?" But the insight was documented, not acted on. Hardcoded sets feel "good enough" until they catastrophically aren't.
6. **LIKELIHOOD x IMPACT**: M x catastrophic (first elderly medical emergency from an unflagged destination)
7. **TRUST DAMAGE**: H
8. **RECOVERABILITY**: hard — moving from a hardcoded set to a destination-attribute database requires schema, data sourcing, and migration
9. **EARLIEST SIGNAL**: First beta agency reports an elderly traveler issue at a destination not in the set.
10. **VERIFY BY**: Cross-reference the hardcoded set against actual travel insurance elderly claim rates by destination (available from ACKO/Star Health). If correlation < 0.3, the set is unreliable.

---

## FINDING 6: Intensity Upgrade/Downgrade Can Erase Tag-Based Safety Warnings

1. **WHAT GOES WRONG**: The intensity-based tier adjustment in `scoring.py:207-212` can upgrade a "discourage" tier to "neutral" when the intensity score is high, silently erasing a tag-based safety warning.
2. **CHAIN OF EVENTS**: An elderly participant encounters a "cultural" activity tagged `physical_intense`. TAG_RULES fires `(physical_intense, elderly) → "discourage"`. `fired_tiers = ["discourage"]`. `_pick_most_conservative_tier` returns "discourage". Then intensity scoring: activity intensity is "moderate" → `base_intensity_score = 0.7`, elderly modifier = 0.8 → `intensity_score = 0.56`. Wait — that's not > 0.8. Let's find the real case: activity is "light" intensity (spa with physical_moderate tag?), elderly modifier for light = 1.0, base = 0.9 → intensity_score = 0.9 > 0.8 → `_upgrade_tier("discourage")` returns "neutral". The "physical intensity may create strain for elderly travelers" warning was generated but the tier got promoted past it. The `warnings` list still has the reason text, but `tier = "neutral"` and `score = 0.5`. The operator sees "neutral" with a buried warning.
3. **USER EXPERIENCE**: Operator scans the tier column (neutral, green checkmark) and moves on. The warning text is in a collapsed details section. The activity appears safe when it's not.
4. **EMOTIONAL IMPACT**: False security — the green light on a yellow activity.
5. **WHY TEAM MISSES IT**: The upgrade logic was added to reward low-intensity activities without considering that tag-based rules (which encode domain expertise like "physical_intense + elderly = bad") should be authoritative over generic intensity scores. Tests check individual rules fire correctly but don't test the tier-adjustment interaction.
6. **LIKELIHOOD x IMPACT**: M x major
7. **TRUST DAMAGE**: M
8. **RECOVERABILITY**: easy — tag-based exclusions/discourages should be tier-floor, not overridable by intensity scoring
9. **EARLIEST SIGNAL**: A beta operator books a "neutral" activity for an elderly traveler that the operator's own experience says is unsuitable.
10. **VERIFY BY**: Construct an activity with tags that fire "discourage" + intensity "light" with elderly modifier; assert final tier ≤ "discourage" (not upgraded).

---

## FINDING 7: Context Rule Penalties Compound Without Bound — Three Correlated Warnings = Exclusion

1. **WHAT GOES WRONG**: `context_rules.py:154-157` applies `_downgrade_tier()` for EACH new risk, independently of whether the risks are correlated, causing three observations of the same underlying issue to push an activity from "recommend" to "exclude."
2. **CHAIN OF EVENTS**: An elderly traveler has a day with two moderate activities + one walking-heavy activity. Tier 2 fires: (1) `cumulative_fatigue_risk` (day intensity > threshold) → downgrade from "recommend" to "neutral"; (2) `back_to_back_strain` (2 high activities) → downgrade from "neutral" to "discourage"; (3) `day_duration_overload` (total > 8h) → downgrade from "discourage" to "exclude". All three risks are describing the SAME problem: too much activity for elderly in one day. But the system treats them as three independent votes of no-confidence. An activity that should be "discourage" with a strong warning becomes "exclude" — a hard stop that triggers `STOP_NEEDS_REVIEW`. The operator sees an exclusion and overrides it (because it's too aggressive), losing respect for the "exclude" tier entirely.
3. **USER EXPERIENCE**: Operator sees "EXCLUDED" for an activity that's merely suboptimal, overrides it immediately, and starts ignoring the exclusion system. The override culture propagates.
4. **EMOTIONAL IMPACT**: Frustration — "the system overreacts to everything."
5. **WHY TEAM MISSES IT**: Each risk rule is independently correct and well-tested. The compounding effect only appears when multiple rules fire simultaneously, which requires specific multi-activity, multi-concern combinations. No test asserts "tier should not drop more than 2 levels from base" or "correlated risks should not compound."
6. **LIKELIHOOD x IMPACT**: M x major
7. **TRUST DAMAGE**: H (override culture is self-reinforcing and nearly impossible to reverse)
8. **RECOVERABILITY**: moderate — need tier-change caps or risk-deduplication before penalty application
9. **EARLIEST SIGNAL**: Override rate on exclude-tier suitability flags exceeds 30% in first month.
10. **VERIFY BY**: Run `apply_tour_context_rules` on a day with 3+ activities for elderly; check if tier drops more than 2 levels from base. If yes, compounding is uncontrolled.

---

## FINDING 8: Budget Feasibility Returns "unknown" for Multi-Destination Trips, Deferring All Budget Risk

1. **WHAT GOES WRONG**: `check_budget_feasibility()` returns `{"status": "unknown"}` whenever `len(dests) > 1` (decision.py:874-876), which means multi-destination trips — the most expensive and complex itineraries — skip the feasibility check entirely during the critical early stages.
2. **CHAIN OF EVENTS**: A client wants Singapore + Bali. Two destinations → feasibility returns "unknown" → no `margin_risk` flag generated at the feasibility stage. `decompose_budget()` still runs and uses `primary_dest = dests[0]` (Singapore) for the entire cost breakdown, ignoring Bali entirely. Neither function handles the multi-destination cost correctly. The `_MULTI_COUNTRY_PENALTY = 1.10` is a 10% flat bump on flights/transport/buffer only. Actual multi-destination costs (inter-island flights, additional visa fees, resort price differential) can be 30-50% higher. The system underestimates by 20-40% and never flags it because feasibility said "unknown" (which the downstream code treats as "not infeasible").
3. **USER EXPERIENCE**: Operator confidently quotes a Singapore+Bali trip at the system's budget only to discover at the proposal stage that inter-destination flights, Bali resort premiums, and double visa fees blow the budget. They scramble to revise. The client feels misled.
4. **EMOTIONAL IMPACT**: Panic at proposal time; shame in front of the client.
5. **WHY TEAM MISSES IT**: The "unknown" return was intentionally conservative ("don't guess from the first candidate") but its downstream effect is the opposite: by NOT flagging risk, it makes the system less conservative. The team reviewed the intent (don't guess) but not the effect (no flag = no warning = blind spot). Multi-destination trips are common in the target market (Singapore+Bali, Thailand+Maldives) so this fires frequently.
6. **LIKELIHOOD x IMPACT**: H x major
7. **TRUST DAMAGE**: M (felt as individual mistakes, not systemic — until the pattern repeats)
8. **RECOVERABILITY**: moderate — need multi-destination cost aggregation logic and a "feasibility_uncertain" flag that triggers human review instead of silent pass-through
9. **EARLIEST SIGNAL**: Budget revision rate on multi-destination trips exceeds single-destination revision rate by >2x in beta.
10. **VERIFY BY**: Pull all multi-destination packets from a test corpus; check that `check_budget_feasibility` returns "unknown" for all of them and no margin_risk flag is generated.

---

## The failure nobody wants to talk about:

The decision engine's most dangerous property is not that it's wrong — it's that it's *selectively* wrong in a way that feels right. When it underestimates Paris costs, the error is invisible because the numbers look plausible (₹25K flights to Paris from India sound reasonable until you actually try to book). When it over-warns about snorkeling for Dubai trips, the error is visible but harmless (operators dismiss it). When it silently excludes a moderate activity because three correlated risks compounded, the error feels like appropriate caution. The system will not fail with a bang. It will fail with a slow accumulation of "probably fine" judgments that are each just wrong enough to erode margin, trust, and safety — and because the confidence score is a meaningless average and the risk flags are mostly noise, nobody will have a working gauge to notice the drift until a real family has a real problem on a trip the system said was fine.

---

## Addendum: Finding 3 — Age Threshold Discussion (2026-05-06)

**Context:** The report flagged a contradiction between `decision.py:1202` (toddlers <4) and `integration.py:125` (toddlers <5) as a bug.

**Correction after review:** Different age thresholds for different risks is correct design. A 2-year-old is free on a flight but needs a car seat in Dubai. A 4-year-old can handle a safari but not a 7-transfer day. There is no single universal "toddler" definition.

**The real problem is structural, not numeric:**

1. **No discoverable registry of age thresholds.** One constant lives in `decision.py:1202`, another in `integration.py:125`. If a new rule is added (e.g., "Dubai car seat mandate for <5" or "safari minimum age 5"), there is no single place to see all thresholds. No operator or future agent can discover what age-sensitive rules exist without reading every module.

2. **Suitability and decision systems don't cross-reference.** Integration.py fires suitability warnings using <5, decision.py evaluates toddler_pacing_risk using <4. A 4-year-old gets partial warnings from both systems but no coherent picture from either.

**Proposed fix — not unification, but structure:**

- Create a shared config (e.g., `data/age_thresholds.json`) listing each age-sensitive rule, its threshold, its source, and which pipeline stage owns it.
- Or at minimum, a shared constant module that both systems import from, making the relationship between thresholds explicit even when they differ.
- The goal: when a 4-year-old arrives, both systems produce output like "adult for toddler_pacing_risk (threshold <4), child for safari suitability (threshold <5), full-fare for flights (threshold <2)" — and the operator sees all of it in one place instead of scattered warnings from disconnected modules.