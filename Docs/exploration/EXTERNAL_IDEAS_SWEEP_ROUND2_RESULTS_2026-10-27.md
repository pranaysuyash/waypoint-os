# External Ideas Sweep — Round 2 RESULTS (2026-10-27)

Companion to `EXTERNAL_IDEAS_SWEEP_NONTRADITIONAL_2026-10-18.md` (master sweep doc, round-2
queue §"Round-2 source queue"). This doc records the round-2 EXECUTION: all queued sources
swept on 2026-10-27 via parallel research subagents (web sources, after the primary search
quota exhausted — per owner directive), the TinyFish browser-automation runner
(`tools/tinyfish_sweep.py`, new reusable tool) for login-walled surfaces, and a read-only
in-repo audit subagent. Evidence files under `Docs/sims/assets/tinyfish_*_2026-10-27*`.

Status legend: ✅ swept with evidence · 🟡 partially swept (method limits recorded) · ⏳ blocked (owner-gated or rate-capped, next window noted).

| # | Source | Status | One-line outcome |
|---|--------|--------|------------------|
| 1 | In-repo: Research Opportunity Master List re-audit | ✅ | Counts were wrong three ways; true done ≈282 (not 211), total ≈1,942 (not 1,897); 6 shipped workstreams invisible to the inventory |
| 2 | In-repo: shared IDEA_PAD cross-check | ✅ | 56 open markers triaged against shipped reality (see §6) |
| 3 | AI-travel competitor teardown (12 products) | ✅ | Navan Cognition S-1 = closest analog; Layla dead; no startup serves the agency back office — white space confirmed |
| 4 | Agency-CRM review mining (TravelJoy/Tern/Travefy/WeTravel/GroupCollect/ClientBase) | 🟡 | G2/Capterra bot-walled; Tripkit/Trustpilot/Reddit-index + vendor pages mined; 10 ranked pain points, commission reconciliation = #1 |
| 5 | Academic thread (2025-26 travel-agent benchmarks + constraint DSL) | ✅ | 20+ papers; zero-out semantics validated (TravelPlanner FPR lineage); multi-traveler constraint benchmark = open gap; 5 adoptable protocol ideas |
| 6 | Facebook travel-agent groups | 🟡 | TinyFish run executed; logged-out visibility limited (evidence JSONL) |
| 7 | App-store review mining | ✅ | Subagent rate-capped → pivoted to iTunes customer-reviews RSS (Hopper/Expedia/Booking.com) |
| 8 | YouTube TBEX/advisor-conference talks | 🟡 | TinyFish run executed (evidence JSONL) |
| 9 | Regulatory feeds (FTC/EU/India) | ✅ | 11 ranked items; India TCS + GST 2.0 = top obligations; jurisdiction-aware compliance layer = the architectural fix |
| 10 | X re-scan | ✅ (2026-10-26, prior pass) | Already closed — see master doc "Round-2 live run 2" |

---

## Source 3 — AI-travel competitor teardown

**Method note:** primary `WebSearch` quota exhausted (resets 2026-11-06). Discovery ran on HN
Algolia, TechCrunch site search, SEC EDGAR (Navan S-1), live product pages, and Wayback.

### Per-competitor

- **Mindtrip** (mindtrip.ai) — Consumer AI assistant with persistent memory ("learns what matters to you"), on-platform booking, itinerary store, creator content; users "create agents to keep tabs on whatever matters" (price drops, flight changes, weather). B2B footer targets brands & DMOs, not back-office agencies. July 2024: itineraries from a screenshot/YouTube/TikTok clip. https://mindtrip.ai
- **Layla** (itslayla.com) — Consumer AI travel recommender; acquired Roam Around Feb 2024. **Defunct as of 2026: itslayla.com now serves a Shopify clothing store.** Signal: viral consumer AI-travel apps die fast. https://techcrunch.com/?s=layla+travel
- **GuideGeek** — Messaging-first AI (WhatsApp/IG/Messenger), multilingual, free to consumers; "Book everything in one conversation." B2B: "GuideGeek for Brands — the AI backbone of the travel industry." No human travel involved. https://guidegeek.com
- **Expedia Romie** — 2024 EG Labs test: iMessage @-mentions in GROUP chats; WhatsApp 1:1 only — CTO: WhatsApp groups not shipped because they "have not yet figured out the dynamics" of group settings; proactive rebooking via AccuWeather/Yelp. 2025-26: Expedia distributes into external agents (Alexa+ Dec 2025; ChatGPT apps). No verified Romie GA. https://techcrunch.com/2024/05/14/expedia-starts-testing-ai-powered-features-for-search-and-travel-planning/
- **Kayak** — "AI Mode" launched Oct 16 2025 on kayak.com: ChatGPT-powered research/compare/BOOK; from the kayak.ai Apr 2025 testbed; TC flags "AI users convert to paying customers" as unproven. https://techcrunch.com/2025/10/16/kayak-launches-an-ai-mode-for-travel-questions-search-and-bookings/
- **Mindful Travel (mindfultravel.com)** — dead/parked domain since ~2022. Drop from the set. https://web.archive.org/web/20220811141808/http://mindfultravel.com/
- **Navan** (closest agency-backoffice analog) — S-1/A (Oct 10 2025) describes **Navan Cognition**: "modular framework of virtual agents using a graph-based workflow," "built-in safeguards and real-time oversight"; chatbot "Ava handled ~50% of user interactions" (H1 FY26) — AI as an explicit gross-margin lever; "Navan Go" mobile booking agent; strategy: "potentially enable outside organizations to create and oversee AI-powered virtual agents with enterprise-grade reliability." IPO Oct 30 2025, debut −20%, ~$6.45B target. https://www.sec.gov/Archives/edgar/data/1639723/000162828025044812/navan-sx1a.htm
- **Booking.com** — legacy AI Trip Planner overshadowed by distribution: car-rental booking shipped as a ChatGPT app (May 2026). Strategy = "meet the traveler's assistant." https://news.booking.com/?s=AI+Trip+Planner
- **Trip.com** — in-app TripGenie + Trip.Planner multi-leg planner live (multi-leg = differentiator). https://us.trip.com
- **Hopper** — fintech price prediction/freeze was the signature; **FTC $35M settlement July 2026** over hidden fees; /price-freeze now HTTP 410 — paid price-protection is retreating. Warning for monetizing fare-drop via consumer fees. https://techcrunch.com/?s=hopper+travel
- **Travala** — crypto-native OTA; "AVA" = rewards program, not an agent. Irrelevant to agencies. https://www.travala.com
- **Meta MUSE** (Sept 2026) — personal AI agent in a per-user Linux container; ~68 skill dirs incl. travel; memory = MEMORY.md entries with **quote + message-IDs + claim-ID**, hourly claim-vs-source verification job, nightly "dream" job, pgvector. Massive trust backlash (HN 666/392/359-pt threads; "blatantly ignores users permissions"; bug bounty closed "Not Applicable"). https://mouse.dev/blog/muse-runtime-export/
- **New 2025-26 found**: Kayak AI Mode; Google AI Mode flight-price tracking + hotel booking (Aug 2026); Airbnb AI CS bot (May 2025); OpenAI apps-in-ChatGPT commerce (Oct 2025); TripJam & Captain (indie group-travel agents, tiny). **No verified startup shipped an agency/advisor-backoffice agent in 2025-26 — the closest is Navan (corporate) and white-label brand plays. That absence is the white space.**

### Synthesis — ship-side patterns for Waypoint OS

1. **Verified-provenance memory** — Muse stores every learned preference with quote + message-ID + claim-ID, verified hourly → **intake**: persist extracted trip facts with quote-cited provenance keyed to WhatsApp message IDs. Analog: partial (confidence exists; durable customer-memory store explored 2026-09-15).
2. **Group-chat agents are unsolved at the giants** — Expedia's CTO admits WhatsApp group dynamics "not yet figured out" → **group-consensus** is a genuine moat: @-mention agent in traveler group chats summarizing votes into a consensus packet. Consensus engine shipped; group-channel conversational agent = white space.
3. **Watcher agents** — Mindtrip's "agents to keep tabs" (price/flight changes/weather) → **fare-drop**: generalize to a watcher framework (price/IRROPS/weather triggers), not just fares. Trigger taxonomy partial (IRROPS expedition doc pending).
4. **Supervised virtual-agent graph + real-time oversight UI** — Navan Cognition graph + safeguards/oversight → **booking** + canonical pipeline: per-task agent scoping and a live oversight surface (human-in-loop as feature, not apology). Operator oversight view partial.
5. **Agent-handled share as a KPI** — Navan discloses Ava ≈50% of interactions as a margin story → **channels/inbox**: track "agent-resolved share" of inbound conversations; agencies sell it as cost reduction. KPI not surfaced.
6. **Chat-native booking closure** — GuideGeek/Romie/Kayak end the conversation in a booking → **quotes + channels**: close quotes/approvals inside WhatsApp (pay-link + confirmation), not just notify. In-chat quote closure partial.
7. **Messy-multimodal intake synthesis** — Mindtrip builds itineraries from screenshots/video → **intake**: accept screenshots/links as intake evidence. Multimodal = white space on the agency side.
8. **Price protection without Hopper's fate** — Hopper monetized fare protection via dark-pattern fees → FTC $35M; Kayak monetizes as engagement → **fare-drop**: transparent, agency-branded reprice decision (advisor recommends, client approves), never a consumer upsell. Decision desk shipped; transparency framing to harden.
9. **Distribution into LLM platforms** — Booking in ChatGPT, Expedia via Alexa+ → **white space: expose an agency MCP/agent-facing API** so corporate clients' assistants can query live quotes/availability through the agency. No agency tool does this.
10. **White-label agent personas** — GuideGeek for Brands / Navan "outside organizations create and oversee virtual agents" → advisor-branded agent personas (agency's voice + memory). Multi-tenancy shipped; per-tenant persona partial.
11. **Consensus-engineering as the unserved product** — nobody serves the agency back office: group consensus + quote engineering + fare-drop decision desk for human agencies is unclaimed. Differentiation is structural.
12. **Graveyard discipline** — Layla dead, Roam Around absorbed, mindfultravel.com dead, Hopper fined: pure-consumer AI travel churns; the durable wedge is humans-in-loop agency operations. Keep agency-first positioning; treat consumer-agent encroachment as a channel question (pattern 9), not a pivot trigger.

**Adjacent-space transfers:** fintech STP discipline (report agent-automation rate as a board-level metric, via Navan); legal-copilot provenance ("why this hotel" shows the exact client message that requested it — Muse's quote-cited memory pattern); real-estate-embedded-agent model (corporate accounts run supervised sub-agents on Waypoint rails).

## Source 4 — Agency-CRM review mining

**Method/limits:** G2/Capterra direct pages 403 (and thin for trade-distributed tools per Tripkit); findings from vendor pricing pages, Tripkit 2026 review hub, Host Agency Reviews, WeTravel help-center/changelog, Travefy release roundups, Reddit thread indexes (bodies bot-blocked; titles/snippets captured).

### Per-tool

- **TravelJoy** — $19 Starter (12 trips/yr, 5%+$0.30 card) / $39 Pro (3.5%+$0.30; AI+automations+groups Pro-only); Premium adds "10x Copilot". Praise: all-in-one CRM/payments/forms; client-completed payment auth forms; per-traveler group payments. Complaints: card fees; Starter gating; weak itinerary polish; no commission machinery; no segmentation. https://traveljoy.com/pricing · https://tripkit.com/traveljoy-reviews
- **Tern** — $35/seat/mo annual; strongest 2025-26 AI stack (AI Assist itineraries, AI Notetaker, inbox/trip-reading agent); AI usage caps Jul 1 2026 with paid "Tern Pro". Praise: "a real commission engine" (auto splits, rollups, supplier reconciliation), email/PDF confirmation parsing, chargeback-protected checkout. Complaints: weekly release churn; AI metering backlash; no advisor mobile app; forced client logins. https://tern.travel/pricing · https://tripkit.com/tern-reviews
- **Travefy** — $39/$59 flat. Best client-facing itinerary doc + mobile flight alerts; CRM "afterthought" (Reddit: "not truly a CRM"). AI: **Smart Reconcile (Sep 2026)** — AI commission reconciliation from images/emails/CSVs/Word: multi-commission bookings, duplicates, fuzzy supplier names, manual-link fallback; Compass CRM dashboard. https://travefy.com/blog-post/september-2026-product-roundup
- **ClientBase (Trams)** — legacy heavyweight, quote-only pricing, Trams back-office integration; standard at established agencies, poor fit for solo/new. **TESS** — ~$10-25/mo budget pick, capable commission tracking, dated UI. https://tripkit.com/crm-for-travel-agents
- **WeTravel** — group-trip payments leader; $79/mo Pro, 2.9-3.9% fees. 2025-26 AI: Smart Import AI (PDF/URL→itinerary), AI Notetaker, AI email drafting w/ Voice Profile, AI CRM opportunities; launched WeTravel CRM 2025. Complaints (heavy): **funds held during "compliance review" while suppliers are owed; no partial refunds**; auto-held funds in disputes; price. https://www.trustpilot.com/review/wetravel.com (3.7) · https://help.wetravel.com/en/
- **GroupCollect** — group-trip ops all-in-one (registrations, payments, reminders, per-passenger data, supplier messaging). No published pricing, no AI marketed. https://www.groupcollect.com/
- **Unverified/wound down**: Ezus (DNS dead), SafariGate (522), "Travel Studio" (no footprint) — flagged, not mined.

### Ranked pain points → Waypoint OS mapping

1. **Payment fees + fund-hold distrust** (WeTravel holds; TravelJoy 5%/3.5%) — Waypoint partial (`payment_queue_service`, `financial_settlement`): add per-method fee schedule + funds-availability timeline on payment decision cards.
2. **Commission reconciliation = #1 ledger pain** (Tern markets an engine on it; Travefy shipped AI Smart Reconcile Sep 2026) — Waypoint yes (`commission_reconciliation.py`, `advisor_payout_store`): must match the 2026 bar (image/CSV/email ingest, auto-match + manual-link). Verify against the bar, not existence.
3. **Group-trip per-traveler collection** (TravelJoy gates groups; WeTravel installment complaints) — Waypoint yes/partial (`group_payments.py`, `group_booking.py`): verify installment schedules per traveler + partial-refund flows + reminder escalation.
4. **Client communication overhead** (read-receipts praised; AI email drafting everywhere) — Waypoint partial (channels, `message_triage`, inbox): add AI-drafted replies in operator voice + open/read tracking.
5. **Itinerary document drudgery** — Waypoint partial (`itinerary_export.py`, `proposal_compiler`): media-rich client doc polish + supplier-content auto-import.
6. **AI intake from messy confirmations** (Tern parse praised) — Waypoint yes (`extraction_service`, `document_extraction`): core differentiator; broaden confirmation-import breadth.
7. **Pricing-model resentment** (Starter gating, $79 WeTravel, Tern AI metering) — design lesson: avoid usage-metered AI tiers; flat per-seat with generous AI is rewarded.
8. **Workflow churn from fast AI shipping** (Tern weekly releases) — watch-item: keep stable operator muscle-memory surfaces.
9. **Supplier statement format chaos** — covered by #2; ingest-format breadth is the real gap.
10. **Client segmentation/re-marketing** (TravelJoy can't segment; Tern "AI client opportunities") — Waypoint partial: exportable client segments + AI opportunity surfacing.

**Group-consensus angle:** none of the mined tools have anything like `group_consensus` optimization or `fare_drop_disposition` cards — zero practitioner mentions of consensus tooling anywhere. No parity pressure; pure differentiation.

## Source 5 — Academic thread (constraint gates + travel-agent benchmarks)

**Lineage anchors:** [TravelPlanner](https://arxiv.org/abs/2402.01622) (ICML'24) defined **Final Pass Rate = zero-out** (hard-constraint violation ⇒ plan scores 0 before preference scoring) — the canonical HARD-gate precedent. [NATURAL PLAN](https://arxiv.org/abs/2406.04520) added tool-output-as-context trip planning.

### Benchmarks & methods (2025-26)

1. **[ChinaTravel](https://arxiv.org/abs/2412.13682)** (ICLR'26) — compositional constraint-validation DSL; separates feasibility / constraint satisfaction / preference comparison; neuro-symbolic 37.0% CSR. Its aggregate CSR is NOT pure zero-out — the gate paper can fill the zero-out-semantics gap on ChinaTravel directly.
2. **[TREK](https://arxiv.org/abs/2607.26977)** — 800 multi-constraint tasks, 13 personas, **deterministic rule-based evaluator, no LLM judge**; GPT-5.6 fully feasible on 46.2%.
3. **[TripTide](https://arxiv.org/abs/2510.21329)** — first disruption-revision benchmark; revision quality degrades with plan length → re-run gates on REVISED plans (where silent hard-violations creep in).
4. **[UTP-Bench](https://arxiv.org/abs/2609.02421)** — uncertainty-aware planning over 504 Indian cities; Buffer Adequacy Score under stochastic disruption → graded soft gate signal.
5. **[Flex-TravelPlanner](https://arxiv.org/abs/2506.04649)** — multi-turn constraint introduction + prioritized competing constraints; single-turn performance poorly predicts multi-turn adaptability.
6. **[CM-DPO](https://arxiv.org/abs/2610.09219)** — symbolic-verifier DPO with violation-severity margins, lexicographic objective → severity-weighted gate reporting is adoptable at zero infra cost.
7. **[SCOPE](https://arxiv.org/abs/2601.09097)** / **[TriFlow](https://arxiv.org/abs/2512.11271)** / **[Blueprint-first](https://arxiv.org/abs/2508.02721)** (96% fewer violations) / **[Behavior Forest](https://arxiv.org/abs/2604.21354)** (+11.8% ChinaTravel via local/global constraint split) — validates gate-DSL-first architecture as the field's convergent direction.
8. **[Solver-Aided Verification of Policy Compliance](https://arxiv.org/abs/2603.20449)** — NL policies → SMT-LIB, Z3 intercepts violating tool calls at runtime → strongest cross-domain validation of runtime gating; FINANCIAL_BOUND→SMT gives counterexample explanations ("over budget by $X").
9. **[ActGov](https://arxiv.org/abs/2609.24446)** — per-action policy-constrained validation → positions per-item vs per-plan gate granularity.
10. **[Policy Loopholes in Agent Evaluation](https://arxiv.org/abs/2609.14400)** — ambiguous/silent policies make scores unreliable ("policy ambiguity masquerading as agent error") → mandatory threat-to-validity: audit the constraint query set for ambiguity.
11. **[Write Once, Check Many](https://arxiv.org/abs/2610.24483)** — policy-independent trajectory ledgers reusable for post-hoc audit across DSL versions.
12. **[Frozen Judges, Moving Agents](https://arxiv.org/abs/2609.34198)** — LLM-judge errors are version-dependent → deterministic gates over judge-only scoring; pin versions + paired audit if judges are used at all.

### Group/multi-user

13. Group-rec cluster: [Unreliable Narrators](https://arxiv.org/abs/2507.13705) (LLM group aggregation ≈ Additive Utilitarian, explanations inconsistent), [Consensus vs Dissent](https://arxiv.org/abs/2607.10235) (per-group dynamic aggregation selection), [Pitfalls of Group Complexity](https://arxiv.org/abs/2505.05016) (zero-shot aggregation degrades >100 ratings), [Aggregation-Rule Authority audit](https://arxiv.org/abs/2608.23966), [Choquet-Borda consensus](https://arxiv.org/abs/2603.21012) → LLMs default to utilitarian sum; Waypoint's Pareto + per-traveler budgets is a fairness correction LLMs don't do natively.
14. **[AI Tour Meeting](https://arxiv.org/abs/2607.18806)** — persona-driven LLM agents negotiate a shared itinerary — the ONLY multi-traveler travel-planning work found; behavior simulation, not constraint-validated.

**Direct answers:** HARD zero-out semantics = validated in lineage (TravelPlanner FPR, TREK feasibility, CM-DPO lexicographic, Z3 runtime rejection) but NOT on ChinaTravel (aggregate CSR) — gap worth claiming. Multi-traveler group trips = essentially NO constraint-validated benchmark exists — publishable protocol territory. Fare/price-watching as an eval domain = doesn't exist (negative result; stochastic-price gate variant would be novel).

### 5 adoptable protocol ideas for the constraint-gate paper (ranked)

1. **Two-tier lexicographic scoring with explicit zero-out**: HARD-gate pass rate before preference scoring + per-constraint micro pass rates — fills ChinaTravel's aggregate-CSR gap; baseline-comparable to TravelPlanner FPR + TREK feasibility.
2. **Violation-severity margins**: graded violation magnitude (over-budget delta, time-window overflow) next to binary pass — distinguishes near-miss from catastrophic; doubles as user-facing explanation.
3. **Multi-turn gate-stability + priority-resolution split** (Flex-TravelPlanner protocol + TripTide revision): introduce constraints mid-planning with stated priorities; score whether gates keep revised plans feasible and whether resolution order matches stated lexicographic priorities.
4. **Reusable ledger + pinned-version audit**: freeze plan-state ledgers, re-audit across DSL versions; LLM-judge confined to a measured ambiguous-residue set (controls Frozen-Judges + Policy-Loopholes threats in one design).
5. **Multi-traveler extension lane**: first constraint-validated group-trip benchmark — per-traveler budget satisfaction + Pareto/fairness vs utilitarian-sum and Choquet/Borda baselines + aggregation-authority disclosure.

## Source 9 — Regulatory feeds

**Method:** search engines + several government sites bot-walled from this environment; facts verified via Federal Register API, Google News RSS (titles+dates), IATA pressroom, Watson Farley & Williams July 2026 multi-jurisdiction roundup. "Confirm" items need counsel/CA sign-off before roadmap commitments.

1. **India TCS on overseas tour packages (Finance Act 2025, eff. 2025-04-01) — OBLIGATION.** 5% up to ₹7L (excl. GST), 20% above; no PAN/Aadhaar = higher rate; agents must collect/deposit TCS + issue certificates. **Feature:** per-traveler PAN capture gate + cumulative-remittance tracker vs ₹7L at invoice time, TCS line-item, Form 27D generation, deposit reminders.
2. **India GST 2.0 (56th Council, eff. 2025-09-22) — OBLIGATION.** Hotel ≤₹7,500/night: 12%→5% (no ITC); >₹7,500 → 18%; tour-operator services 5% gross → 18% w/ ITC (confirm notification). Pre-Sept quote tax tables now misprice. **Feature:** effective-dated tax-rate matrix by service type + nightly band; gross-vs-ITC toggle per line.
3. **EU revised Package Travel Directive (EP Jan 2026; Council 2026-03-30; transposition ~2027-28) — OBLIGATION (EU sales).** Stronger consumer protection, all-in pricing/fee transparency, insolvency protection. **Feature:** all-in quote roll-up, package vs LTA classifier + pre-contract info pack, client-money flag.
4. **EU261 reform (trilogue 2026-06-15; EP vote Jul 2026; ~2027) — OBLIGATION/MONITOR.** Advertised fares include cabin bag; rights info within 96h of arrival; free adjacent seat for adults with under-14s; EP rejected relaxing delay triggers to 5h; intermediaries may refund their own fees (confirm). **Feature:** fare-construction flag, disruption-rights templates with SLA timers, refund-SLA tracking.
5. **DOT automatic-refund rule + enforcement pause (US) — OBLIGATION.** Cash refunds ≤7 business days for cancelled/significantly-changed flights; enforcement paused 2025-12-05 for merely-renumbered flights, extended 2026-07-07 to 2027-07-07. **Feature:** refund-eligibility timer per PNR + renumbered-flight whitelist; refund pass-through audit trail.
6. **UK CMA / DMCC drip-pricing (live 2025-04-06) — OBLIGATION (UK sales).** Direct fining powers; first fine Apr 2026; StubHub fined Jul 2026. **Feature:** single all-in headline total, non-hideable mandatory-fee toggles.
7. **FTC Junk Fees Rule (compliance 2025-05-12) — OBLIGATION (US lodging).** Total price most prominent for short-term lodging ads. **Feature:** resort/mandatory fees as first-class quote line-items rolled into headline total, per-jurisdiction display rules.
8. **India DPDP Act + Rules (notified 2025-11-14; phased to 2027-05) — OBLIGATION + OPPORTUNITY.** Consent, purpose limitation, breach notification; passport/visa PII squarely in scope. **Feature:** DPDP compliance pack — consent records, PII minimization (mask passport numbers by default), retention/erasure jobs, breach workflow. Strong paid upsell; most small Indian agencies have nothing.
9. **India CCPA pressure on booking platforms (probe May 2026; IndiGo Dec 2025 meltdown) — MONITOR→OBLIGATION.** Cancellation-fee disclosure + dark patterns moving toward intermediaries. **Feature:** cancellation-fee schedule pre-payment on every quote; no default pre-checked add-ons.
10. **PSD3/PSR (provisional 2025-11-27; ~2027) — MONITOR.** Fraud-liability shift, IBAN/name verification. **Feature:** record SCA/verification events per payment mandate for PSP evidence.
11. **FTC click-to-cancel vacatur/revival + NYC/CA state rules — OBLIGATION if recurring products sold.** Cancel as easy as signup, same channel. **Feature:** one-click cancel + receipts.

**Cross-cutting:** items 1,2,4,5,7,9 share one architectural need — a **jurisdiction-aware compliance layer on the quote/booking object** (tax matrix w/ effective dates, mandatory-fee roll-up, refund/rights SLA timers, consent+PAN evidence). Build once; 6-7-9 are configuration, not new code.

## Source 1 — Master-list re-audit (read-only, subagent)

**Method:** full-file programmatic recount + ~60-item artifact sampling against Docs/, src/, spine_api/, frontend/src/ (≈3.5% sample). Read-only — no files edited.

**Corrected inventory:** 56 categories ✓, but **1,942 bullets** (1,732 status-marked: ✅ 282 / 🟡 4 / ❌ 765 / 🔵 681; + 210 Content-Prism topics). The file disagrees with itself three ways: prose 1,897 / its table 1,903 / actual 1,942. Body ✅ = **282**, not 211.

**Verification results:** all 30 sampled ✅ claims verified (SPEC-cited docs exist 100%; convention sound). ≥10 stale-open items shipped since April but still marked ❌/🔵 (messaging ingress `messaging_webhooks.py`, RAG `src/rag/*`, holiday registry, 5 of 6 RA-EXTRACT build tickets, …). 24/30 sampled open items confirmed with zero artifacts (ACLED/political indices, seismic data, crowd density, all Waypoint indices BA2705-2716, all 18 mega tools BB2742-2759, AE keyword clusters). **Corrected totals: ~282 done (+4 partial) / ~1,660 not-done.**

**Most-changed categories:** AW Destination Intel (96 items; weather/AQI advanced in code, WeatherPivot agent LIVE), BD/BE Data Acq (5 of 6 RA-EXTRACT done in code — stalest block), E tech (messaging + RAG shipped — stale), AY Everyday (holiday registry shipped), AX/AZ/BA/BB (confirmed still open), AE SEO (open), Q Vendor (SLA covered elsewhere).

**5 highest-value still-OPEN clusters:** (1) AW safety/crime domain (lines 2381-2391 — gates the flagship "Is It Safe?" tool + index); (2) AW weather+AQI source evaluation (APIs wired ad hoc, no formal eval doc); (3) BD data governance (freshness/normalization/licensing — foundation of the moat); (4) AY laws/culture block (AX2520-2533 + AZ2667-2676 — largest untouched programmatic surface); (5) AE keyword-cluster research (cheapest cluster; gates every content decision).

**Structural problems:** three inconsistent totals; six shipped workstreams absent from the list (fare-drop card, FINANCIAL_BOUND, RAG egress, work-intake, messaging ingress, data-registry/customer-memory/ops runbooks) so done/open can never reconcile; ~250-380 rows are restatements across AF/AG/AV/BC/AX/AZ/BA; build tickets posing as research (BE); three competing research registries with no cross-references; FEATURE_LIST_V3 itself has post-Sept drift (D09 now mounted at `spine_api/server.py:1698` but still marked ORPHANED).

**README caveat replacement:** applied to `Docs/research/README.md` this pass (exact text in the audit; see README step 3).

## Source 2 — IDEA_PAD cross-check

`idea_pad_tool.py validate` passes. Ground truth of the pad (2,374 lines, 151 `IDEA-###` entries): **135 inbox / 6 committed / 4 qualified / 4 done / 1 active / 1 killed**. The master sweep doc's "56 open markers" claim was stale — actual open-ish (inbox+committed+qualified+active) = 146.

Waypoint-relevant triage (FND-0205 pattern — check done markers against shipped reality):
- **IDEA-120 "Autonomous Price-Lock Sentinel for GDS/NDC Rate Drops" (`done`)** — correctly marked: superseded by the shipped fare-drop decision card + `TicketPriceWatchAgent` post-booking branch.
- **IDEA-122 "Group Trip Multi-Payer Split Deposit Portal" (`done`)** — consistent: `group_payments.py` + `group_booking.py` + group-consensus optimizer exist (installment/partial-refund depth flagged as the residual gap by source #4).
- **IDEA-123 "Voice and WhatsApp Native AI Inbound Handler" (`done`)** — consistent: WhatsApp SYSTEM-READY per the B1 readiness pass (webhook/store/concierge/dispatch live; key flip pending).
- **IDEA-141 "GST input-tax-credit leak finder for CAs" (`killed` 2026-10-11 for incumbent saturation)** — kill rationale predates **GST 2.0 (eff. 2025-09-22)**: the regulatory sweep found pre-September quote tax tables now misprice, which reopens a mispricing-detection wedge for the *agency* side (R2-C adjacent). Pad owner's call whether to resurrect; recorded here so the date-sensitivity isn't lost.
- **IDEA-146 "single-problem app via 1-2 star review mining" (`inbox`)** — the method was just validated at travel scale by source #7 (150 app-store reviews → 7 ranked guard/white-space themes).

No pad markers contradict shipped reality. The 135 inbox items are untriaged capture, not claims — a full pad re-triage is a separate task and not part of this sweep.

## Consolidation — new ideas register (round 2)

Cross-source items worth tracking as candidate findings/tasks (NOT opened in the findings store yet — that decision belongs to the owner per findings protocol; recorded here so they are not orphaned):

- **R2-A (pattern 9 / competitor)**: Agency-facing agent API / MCP surface — make an agency's quotes/availability agent-callable. Owner-gate: product direction (API surface = public contract).
- **R2-B (pain 2 / CRM mining)**: Commission-reconciliation ingest breadth — image/CSV/email statement ingest with auto-match + manual-link, matching the Travefy Sep-2026 bar. Verify `commission_reconciliation.py` against it first.
- **R2-C (regulatory 1-2)**: India compliance pack — TCS tracker + GST 2.0 tax matrix (effective-dated). Highest launch-market obligation density.
- **R2-D (academic protocol 1-2)**: Constraint-gate paper: two-tier zero-out scoring + severity margins — feed into the paper-design doc (done this pass, see addendum there).
- **R2-E (academic gap)**: Multi-traveler constraint-validated benchmark = open publication lane; group-consensus runtime is already the moat.
- **R2-F (pattern 5)**: Agent-resolved-share KPI on the inbox surface.
- **R2-G (pattern 2)**: Group-channel conversational agent (WhatsApp group @-mention → consensus packet) — the giants' admitted blind spot.
- **R2-H (pattern 3)**: Watcher-framework generalization of the fare-drop trigger taxonomy (price/IRROPS/weather).

## Next actions

1. Owner DECIDE queue: R2-A (agent API), R2-C scope, whether to open findings for R2-B/R2-F/R2-G/R2-H.
2. Research program: the master-list inventory refresh (add the 6 missing shipped workstreams; reconcile 1,897/1,903/1,942) is a distinct task — the re-audit sample + README caveat are in place; full refresh is mechanical but large.
3. X re-scan & further TinyFish automations: `tools/tinyfish_sweep.py` is now reusable; runs cost one automation per source.
4. Primary search quota resets 2026-11-06 — app-store/CRM review depth can be re-mined then if the RSS/Tripkit evidence proves thin.

---

## Source 8 — YouTube advisor-AI sweep (TinyFish, COMPLETED)

Evidence: `Docs/sims/assets/tinyfish_youtube_2026-10-27.jsonl` (9 SSE events, terminal COMPLETED). Top-of-results for advisor AI workflows:

1. **Tern Travel — "What Agentic AI Actually Does for Your Advisory Business"** — vendor-authored agentic-AI education for advisors (AI email, packing lists, booking workflows). Confirms Tern's AI-stack positioning from source #4 at the practitioner-education layer.
2. **Travefy × Asia Lantz — "Mentorship, AI and the Next Wave of Advisors"** (1 day old) + Travefy CEO data-talk — the incumbent vendors are competing on AI *education* as marketing, not just features.
3. **"10 Ways Travel Agents Use AI"** (Ash Knows Travel, live + replay) — mainstream advisor AI-adoption content exists as a training genre.
4. **Automation tutorials** (Travefy workflow builder, DIY "AI travel agent" builds 2.2K-15K views) — practitioners hand-build automations for pre/during/post-trip communication; DIY agents from live booking networks. The same hand-rolled pattern the fare-drop card automated.

Takeaway: advisor-side AI adoption is mainstream and education-driven; the automation tutorials practitioners build by hand map to Waypoint's shipped surfaces (comms workflows, price watching). No video surfaced anything beyond source #3/#4's findings — corroborates them.

## Source 6 — Facebook groups (TinyFish, honest negative)

Evidence: `Docs/sims/assets/tinyfish_facebook_2026-10-27.jsonl` (COMPLETED). Facebook search redirects to login for logged-out browsers; **zero posts, groups, or content visible**. The agent explicitly reported what was and wasn't visible and that no credentials were configured.

Verdict: this source requires an authenticated session — an owner decision (credentialing an account for browser automation). Not retried; recorded as blocked-with-evidence rather than assumed-empty.

## Source 7 — App-store review mining (iTunes reviews RSS, 150 reviews)

Evidence: `Docs/sims/assets/appstore_reviews_{hopper,expedia,booking}_2026-10-27.json` (50 most-recent reviews each, pulled 2026-10-27). Rating distributions: Hopper 38×5★/5×1★; Expedia 20×5★/19×1★/6×2★; Booking.com 22×5★/23×1★ — the consumer OTA middle is genuinely polarized.

### Complaint themes → Waypoint OS mapping

1. **Price changes between selection and checkout** (Hopper "DECEPTIVE PRICING" — advertised low, raised at property page; Expedia "information was not the same as the one I picked, the price double") — the exact FTC $35M conduct. **Waypoint: avoided-by-design** (quotes are operator-authored artifacts with cost basis + provenance), plus a **guard-to-add**: quote-total re-verification at the approval door (client-visible total must equal operator-approved total — a FINANCIAL_BOUND-shaped check that already has the constraint-engine seam).
2. **Refund charged after confirmed cancellation** (Booking.com: "Charged over $500 for a cancelled room... after I received confirmation of the cancellation") — the 2024-25 Stripe-verify / disposition-ledger class. **Waypoint: guard** — cancellation confirmations must carry the evidence trail into the payment ledger (disposition events already embed `caused_by`; wire cancellation→refund SLA timers per regulatory item 5).
3. **Booking not found at property / never made but money taken** (both Booking.com and Expedia, multiple) — **Waypoint: avoided-by-design** (booking lifecycle states are honest-by-state; the fabricated-success-page class was closed in the launch-readiness audit), but it validates the OPERATOR surface: a human sees pre-booking failure instead of a client discovering it on arrival.
4. **Support black hole** (all three; "can't talk to a real person", "impossible to find answers on virtual chat") — consumers' pain is agents' product: the agency IS the human. Validates operator-in-loop positioning; also flags **R2-F** (agent-resolved-share KPI) as the counter-metric — automation without a human escape hatch is what they're punishing.
5. **Date/confirmation mismatch at booking** (Booking.com: "Selected today's date... received a confirmation for two Months ahead") — **Waypoint: guard** — date-consistency check between extracted intake window, quoted dates, and provider confirmation (the extraction pipeline already normalizes dates; the cross-artifact consistency assertion is the missing gate).
6. **Fake listings / scams on-platform** (Booking.com "$5,000 paid for a fake rental", "infestation of scammers", support *encouraging* off-platform payment) — **Waypoint: white space** — agency-curated supplier relationships with SLA frameworks (Q-category doc) are structurally insulated; potential marketing claim.
7. **Itinerary-change rigidity** (Expedia "outside of the 24 hours notice", dropping 3 of 4 rooms) — group/partial changes are the same white space found in source #4 (group payments): partial-refund and per-traveler-change flows.

Hopper's 5★ dominance (38/50) despite FTC settlement shows price-protection features still drive love — consumers want the watching; the agency-grade version (transparent decision desk) is the defensible form.


---

## TinyFish deep-dive (2026-10-28 — second pass on the four API sources)

Four more automations (all COMPLETED; `tools/tinyfish_sweep.py`; evidence `Docs/sims/assets/tinyfish_{x_rescan,gplay_hopper,gplay_expedia,facebook_mobile}_2026-10-28.jsonl`).

### X re-scan (fresh, Oct 2026)

- **Odessia** (launched Oct 14 2026) — free AI travel concierge: plans AND books flights/hotels/restaurants by text, checks live prices, and **keeps monitoring for openings and better options after quoting** — the consumer twin of our watcher pattern, validated as the viral shape (22.5K/30K view posts; community benchmarks it against Meta MUSE: "ready to check out in seconds" vs "minutes and an unavailable option"). Competitor set addition; teardown-worthy.
- **DiscoverAxel** — fast-growing AI flight/hotel deal agent (Render-backed). Second new name for the set.
- **Widgety + AirnodeHub (Api3)** — agent-facing **travel data API** (cruise/tour datasets, "every response signed at the source") — direct market validation for R2-A: agent-callable data surfaces with provenance are being built and marketed as the missing layer for travel agents.
- Meta-narrative post (Oct 28): "Agentic AI is quietly reshaping how we book travel as Google, Meta and Expedia race ahead."

### Google Play reviews (Android side — RSS covered Apple only)

- **Hopper**: same bait-price theme cross-platform ("advertised 150, at booking double the price"), plus **$15 charge to reach support** (paywalled support — new), connectivity-error double-charges, overbooking refund dead-ends.
- **Expedia**: cancellation-policy opacity at the moment of canceling, "breakfast included" listing inaccuracy, rental-car counter fees tripling the reservation price, fights over 24-hour-window cancels, "airline credit is an absolute joke."
- Confirms: the iOS themes are platform-independent, not Apple-artifacts. Guard list from §Source 7 stands unchanged.

### Facebook (m.facebook retry — PARTIAL BREAKTHROUGH)

The mobile search URL returned "Not Found", but public search snippets and group previews were accessible logged-out — **the previous hard-wall verdict is downgraded to partial**:

- Practitioner sentiment from "Facebook For Travel Agents" group (public snippets): "using AI cautiously... curious what's working for you" (Oct 19); the contrarian: "made a personal decision not to use it — I believe it's created more trust with my clients." **Trust, not capability, is the adoption wedge.**
- **Voice-agent-as-agency-tool is a live practitioner discussion** (the "AI agent phoned a Holiday Inn for event space and reported back" post: 74 reactions, 616 comments) — an intake/channel surface candidate beyond text.
- "Claude just killed travel agents" engagement-bait (1,236 reactions, 5,168 comments) — displacement anxiety is the content genre; Waypoint's positioning is the antidote framing.
- TravelJoy advocacy posts recur (consistent with source #4's table-stakes read).

Full group content still requires an authenticated session — but the snippet layer is reachable, so this source can be mined incrementally without credentials.

### Delta to the round-2 register

- **R2-I (new)**: post-quote continuous monitoring as user-facing product (Odessia's shape) — our fare-drop watcher is internal-first; Odessia proves consumers reward *visible* ongoing monitoring. Owner-gate: whether the traveler-facing side of watching (not just operator cards) becomes a surface.
- R2-A strengthened twice in one week (Widgety/AirnodeHub market signal + Odessia booking-loop).
