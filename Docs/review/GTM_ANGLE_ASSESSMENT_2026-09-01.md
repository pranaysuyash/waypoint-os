# GTM Angle — Full Assessment & Decision Brief

**Date**: 2026-09-01
**Scope**: What the GTM angle is, what is documented, what is actually shipped, what is real externally, and what is missing.
**Method**: Repo sweep (2,038 docs in `Docs/`), executed code verification, telemetry analysis of live event data, and external market research (8 research questions, sourced).
**Status**: Complete — pending Pranay's discussion. No code changed. No git mutations.

---

## 0. Executive summary — the five things that matter

1. **You have ~80 GTM documents and no GTM.** The thinking is rich but the canon is stale (April–May 2026), self-contradictory, and was written before a single customer conversation. Nothing has been retired.

2. **The wedge is contested, not open.** Three companies already ship "upload/paste an itinerary, get it stress-tested" — two of them free with no signup. The core strategic claim in `STRATEGIST_MEMO_TWO_PRODUCT_QUESTION_2026-05-06.md` ("No CRM builds a free traveler audit tool… Waypoint can build it precisely because it owns neither side yet") is **falsified by live products**.

3. **The wedge has never had a real user.** 822 events exist in the funnel. 613 of 614 intakes have `has_destination: false` and `has_dates: false`. That is synthetic test traffic. The north-star event (`action_packet_shared` — forwardability) has fired **twice**, never from a verified human.

4. **You cannot run GTM today because the core loop dead-ends.** The live persona demo from *yesterday* (`SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md`) shows a realistic messy note → destination "Japan" never extracted, party size 1 instead of 4, and the resulting lead **never reaching Lead Inbox**. Verdict: "Gorgeous cockpit, honest gauges — but my flight never took off."

5. **There are fabricated proof points on public surfaces right now.** Three named testimonials on `/itinerary-checker` and three hard numbers on `/`. There are zero customers. This is a legal and trust blocker, not a copy nit.

**The honest one-liner:** the GTM problem is not a marketing problem. It is that the product cannot yet complete the one loop it promises, and no one outside the repo has been asked whether they want it.

---

## 1. What exists — the documented GTM canon

Sweep of `Docs/` (2,038 markdown files) found **80+ GTM-relevant documents**. Concentrated in a burst between 2026-04-13 and 2026-05-18, then a second, corrective burst 2026-07-28 → 2026-08-04.

### 1.1 The nine dimensions

| Dimension | Strongest artifact | The strongest claim in it |
|---|---|---|
| **Wedge** | `STRATEGIST_MEMO_TWO_PRODUCT_QUESTION_2026-05-06.md` | "Product B is not a product — it is a customer acquisition channel that produces data… the channel builds the product." |
| **ICP** | `exploration/MESSAGING_BY_ICP_PERSONA_2026-05-18.md` | "A travel agency is not one ICP. It is at least 5–7 distinct ICPs." |
| **Positioning** | `CHATGPT_LAUNCH_AUDIT_2026-08-03.md` | "AI operating system for travel" is too broad; the credible line is "Turn messy travel enquiries into quote-ready briefs." |
| **Pricing** | `LAUNCH_AUDIT_DD6_MONETIZATION_2026-08-01.md` | "Do not publish numbers until ≥6 discovery calls include a pricing question." |
| **Channels** | `SALES_MARKETING_FIT.md` | "Zero ad spend until 50 paying customers." (Still true — there are zero.) |
| **Competition** | `PRODUCT_STRATEGY_PERSONAS_MARKET_2026.md` | Best-structured map: Travefy/Tern/TravelJoy (passive), Navan/TravelPerk/Spotnana (corporate), Mindtrip/Layla (B2C wrappers). |
| **Funnel** | `NEXT_STEPS_PRODUCTB_WEDGE_EXECUTION_2026-05-07.md` | "Forwardability, not engagement, is the success metric — travelers negotiate rather than switch." |
| **Partners** | `PRICING_AND_CUSTOMER_ACQUISITION.md` | "One conversation with Tirketi → 1,000+ agents → 2% convert = 20 customers." (Pure arithmetic; no relationship exists.) |
| **Brand** | `FRONTEND_LANDING_REDESIGN_2026-06-28.md` | "Remove the public checker distraction from the homepage so `/` does one job well." |

### 1.2 Three competing wedge theses — none retired

| Thesis | Source | Mechanism |
|---|---|---|
| **A. Empowerment** | `ARCHITECTURE_DECISION_D2_FREE_ENGINE_PERSONA_2026-04-18.md` | Traveler gets a non-adversarial audit → "things worth discussing with your planner." |
| **B. B2B2C pressure** | `STRATEGIST_MEMO…2026-05-06.md` + `NEXT_STEPS…2026-05-07.md` | Traveler takes the audit back to their *existing* agent; the agency adopts Waypoint to meet the new standard. |
| **C. Creator funnel** | `ADR_SOCIAL_INBOUND_ADAPTER_AND_TEASER_FUNNEL_2026-08-03.md` | `/c/[creatorId]/plan` link-in-bio → teaser with masked supplier names → $25–50 refundable deposit unmask gate. |

Thesis C is the most recent and the least grounded: `/c/[creatorId]` **does not exist in the codebase** (verified). Its ADR claims "approved & implemented" and names deciders ("Engineering & Product Lead, Creator Operations Lead") for roles that do not exist in a one-founder company with no customers. It also cites `motto_v4.md`, which does not exist.

### 1.3 Four ICP theses, four pricing schemes, two currencies

| Date | ICP | Pricing |
|---|---|---|
| 2026-04-29/30 | Boutique 2–5 staff, India metros | ₹999 / ₹6,000 / ₹12,000 |
| 2026-05-18 | 8 ICPs incl. TMC, DMC, MICE, cruise | (not addressed) |
| 2026-07-28 | **Mid-Market Outbound, 3–15 seats** (explicitly rejects the boutique-luxury launch ICP as wrong) | **$49 Solo / $199 Agency** |
| 2026-08-04 | **Solo Luxury Advisor, Host Agency, UHNW traveler** (pivots back) | (deferred) |
| 2026-08-01 | (open) | Free / Pro ₹2,000–3,500 — flagged as hypothesis |

**Geography is also unresolved**: April–May canon is India-first (INR, Indian Facebook groups, Singapore as #1 Indian outbound); the 05-06 strategist memo addendum says **"Day-1 Global, Not India-First."** Never reconciled. DD-6 still lists an open "INR vs USD" decision.

### 1.4 A direct self-contradiction on the moat

`GTM_AND_DATA_NETWORK_EFFECTS.md` (2026-04-13) is emphatic:

> "Network effects are overrated. Tool value is underrated."
> "Agencies don't want recommendations from OTHER agencies."
> Data Strategy Recommendation, Phase 1: "No Data Sharing… **No network effects**. Focus on tool value, not data value."

The entire moat of `STRATEGIST_MEMO…2026-05-06.md` and `PRODUCT_STRATEGY_PERSONAS_MARKET_2026.md` is a **cross-agency data flywheel** (10,000+ audited itineraries, a "Global B2B Trust Ledger"). These positions are mutually exclusive. Both documents are live and un-retired.

---

## 2. What is actually shipped (executed evidence, not doc claims)

| Claim | Verified reality | Evidence |
|---|---|---|
| Itinerary checker is live | **Yes** — real route, real backend | `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx` (110 KB); `POST /api/public-checker/run` at `spine_api/server.py:1770` |
| Checker has its own light pipeline | **No** — still runs the full B2B agency spine | `spine_api/services/public_checker_service.py:19` imports `run_spine_once` from `src.intake.orchestration`. Flagged 2026-05-01 as the thing to fix; **still unfixed 4 months later** |
| Checker is the top-of-funnel | **No** — not linked from the live homepage | `landing-v5.tsx` has exactly one "itinerary" mention (body copy, line 30). Zero links. Only `/pricing` and dead generations (`v2`, `landing-experiments`) link to it |
| Share/forward the report | **No route exists** | `proxy.ts:34` declares `/itinerary-checker/shared/` public; **no such page**. The north-star metric has no implementation |
| Consent + export/delete | **Yes** — real | `/api/public-checker/{id}` GET/export/DELETE + consent gate |
| Funnel instrumentation | **Yes** — well designed | `spine_api/product_b_events.py`: 8 events, strict envelope, required properties |
| Pricing published | **No** — deliberately | `pricing-page.tsx`: "Free" / "Start self-serve" / "Add support when needed". FAQ admits numbers don't exist |
| SEO foundation | **None** | `frontend/src/app`: **0 sitemap.xml, 0 robots.txt, 0 openGraph across every page**. `proxy.ts` lists both files as public; neither exists |
| `Docs/LAUNCH_STATUS.md` | **Not created** (recommended 2026-08-01, DD-8 item 3) | `ls` → no such file |
| Customer discovery | **Still open** | `TODO.md:8-14` — all boxes unchecked. `AGENCY_OWNER_INTERVIEW_GUIDE_2026-04-27.md` exists; no completed interviews. Only external voice on record is `CALL_NOTES_AYSE_2026-04-30.md` — a GTM advisor, not a customer |

### 2.1 The funnel has never seen a real user

`data/product_b_events/events_normalized.jsonl` — 822 events, 618 sessions, 2026-05-07 → 2026-08-30.

```
intake_started                   619     has_destination: true   →   1
first_credible_finding_shown     198     has_destination: false  → 613
action_packet_shared               2     input_mode: freeform_text → 614 (all)
agency_revision_reported           2     finding_category: suitability → 197 (all)
product_a_interest_signal          1     workspace: d1e3b2b6…  → 811 of 822
```

613 of 614 intakes have **no destination and no dates**. Every finding is the same `suitability` category. This is a repeated smoke fixture, not traveler traffic.

The two events the entire strategy depends on — `action_packet_shared` (2) and `agency_revision_reported` (2) — occurred in the `waypoint-hq` and `public-checker` workspaces, i.e. test fixtures, not the public checker agency.

**Conclusion: forwardability has never been observed in a real user.** Every downstream GTM number built on it is unanchored.

### 2.2 Fabricated proof on public surfaces

`/itinerary-checker` renders three named testimonials from a hardcoded array (`PageClient.tsx:1027-1045`):

- "Found a 52-minute connection I completely missed." — Sarah K., Solo traveler, Japan trip 2025
- "I'm a 20-year travel veteran and it still caught a visa issue my agent didn't flag." — Marcus T.
- "Shared the report with my advisor. She said it was the most useful pre-trip brief she'd seen." — Priya N., Family trip, Italy 2025

`/` renders `operatorProof` (`landing-v5.tsx:22-26`): **"2m 14s"** from inquiry to usable brief, **"3"** questions before quote, **"18%"** owner reviews routed.

There are zero customers and zero completed discovery calls. These are presented as measured results on public marketing pages. `CHATGPT_LAUNCH_AUDIT_2026-08-03.md` flagged the homepage numbers on 2026-08-03; they are **still live on 2026-09-01**.

This is the single hardest blocker in this document. Fabricated testimonials and unsubstantiated performance claims are a consumer-protection exposure (FTC in the US, CPA 2019 in India), and they are the exact failure mode the 2026-08-01 audit named as the company's core disease.

### 2.3 ADR 18 builds on components the launch audit called simulated

`ADR_SOCIAL_INBOUND_ADAPTER_AND_TEASER_FUNNEL_2026-08-03.md` states "Initial ADR 18 approved & implemented" for a Ghost Concierge, Yield Arbitrage Engine, and Karpathy AutoResearch Loop. `LAUNCH_AUDIT_DD5_SIMULATION_BOUNDARY_2026-08-01.md` (two days earlier) found these fabricated.

**Nuance, verified:** the routers do exist and are now honestly tiered `DATA_DEPENDENT` (`spine_api/routers/concierge.py:10`, `yield_arbitrage.py:9`) — meaning real code awaiting data that isn't connected. That is better than "fabricated," but it means **they cannot be marketed as working**, and ADR 18's GTM plan assumes they are.

---

## 3. External reality (researched 2026-09-01)

Labels: **[F]** verified with source · **[E]** estimate/vendor claim · **[I]** inference · **[NF]** not found.

### 3.1 The wedge is occupied — and free

| Competitor | What it does | Price |
|---|---|---|
| **SuperTravel** — [suptravel.ai/itinerary-check](https://suptravel.ai/itinerary-check) | Paste itinerary (50k chars) → issues, **severity ratings**, suggestions. 10–30s. | **Free, 5 checks, no signup** |
| **Spotinga** — [spotinga.com/tools/itinerary-checker](https://www.spotinga.com/tools/itinerary-checker) | Paste plan → "feasibility report": conflicts, overloaded days, **fatigue scoring**, real map travel times | Free (5k char limit) |
| **Fortrip** — [fortrip.ai/itinerary-validator](https://fortrip.ai/itinerary-validator) | "**Stress-test your itinerary before you book it.**" Parallel AI agents check connections, transit, pacing, routing. Auto-re-validation. | Not published |

Fortrip's headline is a near-verbatim restatement of Waypoint's wedge positioning ("Find what your travel plan missed" / "Upload. Analyze. Travel confident.").

**Gaps neither has closed [I]:**
- **All three are paste-text only. No PDF / email / screenshot upload.** Waypoint's PDF + OCR ingestion is genuinely unoccupied — and it is already built.
- **No forwardable score artifact** designed for handing to an agent. The load-bearing part of Waypoint's loop is still open.
- No agency-facing motion or marketplace on any of them.

### 3.2 SEO is a dead end for this wedge [F]

Exact-match SERP check (2026-09-01):

- `itinerary checker` → #1 CheckMyTrip, #2 Expedia login utility page, **#4 SuperTravel**, **#6 Spotinga**. SERP is polluted by big-brand utility pages and generic planners. No clean commercial lane.
- `check my travel itinerary` → **zero exact-match organic results**
- `itinerary stress test` / `is my itinerary realistic` → **zero results**
- `travel itinerary review` → a Tripadvisor paid ad only; no organic service pages

**Caveat:** no Ahrefs/Semrush/GSC access, so this is SERP-structural, not volume data. Zero exact-match results is a strong but indirect signal. **Spend $50 on real volumes before killing the channel** — but do not plan a GTM on it. If the checker works, it works as a **sales asset**, not as an SEO funnel.

### 3.3 The real competitive threat is not who the docs say it is

- **Fora** — [F] $60M Series D at **$1B valuation**, July 16 2026 ([TechCrunch](https://techcrunch.com/2026/07/16/ai-powered-travel-agency-fora-hits-unicorn-status-raises-60m/)). $138.5M raised; agents booked **$3B+**; its AI agent **Via** is described as "the AI operating layer across our entire platform."
- **Tern** — [F] $13M Series A; **already ships a trip audit** ("review an itinerary for missing hotel nights, absent confirmation numbers or other inconsistencies"). $49/seat/mo monthly, $35 annual.

**Both are already "the AI OS for travel agencies." Both are funded.** Waypoint cannot differentiate on "AI for agencies."

Published price band [F]: **TravelJoy $19–39 · JourneyFuse $25 · Tern $35–49 · Travefy $39–59** (+$20/extra seat). The $19 tier is a decoy (capped at 12 trips/yr, no AI, no team seats).

### 3.4 Adoption has inflected — the concept is no longer novel [F]

[PhocusWire, 2026-07-14](https://www.phocuswire.com/news/technology/ai-pushing-travelers-toward-next-evolution), citing Phocuswright + Travel Weekly:

- **59%** of advisors have used gen AI, **up from 41%** a year earlier. 56% "cautiously optimistic."
- Tern usage data (6,900 advisors / 90 days): monthly active AI users nearly **tripled YoY**; typical advisor now uses AI **50×/month vs 12** a year ago.
- Advisors accept **~9 in 10 routine AI suggestions**.

You are no longer selling the concept. You are selling a specific better outcome.

### 3.5 India validates half the thesis and threatens the price [F/E]

- **32.71M Indian outbound departures in 2025, +5.9% YoY — a record** (Ministry of Tourism). Inbound fell 9.4%. Government is actively campaigning *against* outbound — a mild policy headwind.
- **WhatsApp Business is "the operational backbone most agents use — not email, not calls."** [E] This directly validates the messy-WhatsApp-parsing wedge.
- Indian agency structure [E]: home-based agents (fastest growing), sub-agents under consolidators (60–70/30–40 split), registered independents at **₹2–8 lakh/month revenue**.
- India-specific players [F]: **Itiner.in**, **ChinarCRM**, **Zotrai**, **ZentrumHub**, **flyo.ai** (free tier). None publishes pricing.
- **[NF]** No WTP data for India. [I] An agency billing ₹2–8 lakh/month cannot absorb $39/seat the way a US agency can. **India-first likely means INR pricing well below $30/seat.**

### 3.6 Distribution: consortia are the leverage, but the evidence is thin [F]

[AltexSoft, 2026-02-06](https://www.altexsoft.com/blog/travel-consortia-virtuoso-ensemble-signature-travel-leaders/), citing Travel Weekly's 2025 survey: **55%** of advisors belong to ≥1 consortium; **49%** work with a host agency.

| Consortium | Advisors | Annual sales | Tech posture |
|---|---|---|---|
| Travel Leaders Network | 100,000+ | $17B+ | In-house, **moving CRM-agnostic** — a door |
| **Virtuoso** | 22,000+ | **$35B** | **Partners — direct Travefy integration (2025)** — a door |
| Signature | 15,000+ | $11B | In-house + adding AI |
| Ensemble | "Tens of thousands" | — | Proprietary ADX; $500k minimum — **closed** |

**[NF] No publicly documented conversion rates** for cold outreach, Facebook/WhatsApp communities, or trade shows into small travel agencies. **Do not let anyone quote a rate for these channels — the public evidence base does not exist.**

### 3.7 The free-consumer-tool-as-B2B-wedge pattern: no evidence it works [NF]

Four searches returned only generic PLG listicles (Slack, Dropbox, Zoom, Calendly). **None is a free consumer tool wedging into a B2B market. None is in travel.**

[I] This absence is informative. The free-tool wedge works when the free user **is** the buyer's employee (Slack/Dropbox — bottom-up inside one company). The checker's user is the agency's **customer**, which means:
- you are asking a consumer to do unpaid sales work for their supplier, and
- you are asking the agency to accept a lead that arrives **pre-armed with a critique of their own work**.

**"Your itinerary has problems — send this to your agent" is adversarial to the exact person who has to pay you.**

---

## 4. Gaps

### P0 — blocks any GTM motion

1. **The core loop dead-ends.** Lead Inbox never receives the blocked lead (`SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md`, finding 1). You cannot acquire users into a funnel that drops them.
2. **Extraction fails on realistic input.** "japan" + "tokyo + kyoto + osaka" → destination `-`; "me and 3 friends" → party of 1. This is the product's entire promise. The 0.9524 golden-set F1 does not cover colloquial phrasing — the eval and reality have diverged.
3. **Fabricated proof on public surfaces.** 3 testimonials + 3 homepage numbers, zero customers.
4. **Zero customer discovery.** No agency owner has been asked anything. Every ICP, price, and positioning claim in the canon is unanchored.
5. **A stranger's PII renders on a new tenant** ("Alex Morgan — Delta Diamond Medallion" + SkyMiles number). Reads as a cross-tenant leak to any privacy-aware buyer.

### P1 — blocks the wedge specifically

6. **The wedge has no distribution.** Not linked from `/`, no sitemap, no robots, no OG cards, no share route. It is an orphan.
7. **SEO cannot be the channel.** 3 of 5 target phrases have zero exact-match demand.
8. **The wedge runs the wrong pipeline.** It still calls the full B2B spine, which degrades realistic PDFs to `incomplete_intake` — the exact failure the 2026-05-01 audit told you to fix.
9. **The creator wedge's entry point doesn't exist.** `/c/[creatorId]/plan` is missing.

### P2 — strategic incoherence

10. **Three wedge theses, four ICPs, four price points, two currencies, two geographies, and a self-contradicting moat** — all live, none retired. This is the known systemic defect (start canonical paths, never retire old ones) applied to GTM.
11. **No canonical GTM document.** `Docs/INDEX.md` indexes 8 separate GTM docs with no stated precedence. `LAUNCH_STATUS.md` was recommended 2026-08-01 and never created.
12. **Two data gaps worth money:** Host Agency Reviews 2026 advisor survey (WTP — results unpublished) and real keyword volumes (~$50 on Ahrefs).

---

## 5. Options

### Option 1 — Invert the wedge: agency-branded checker (recommended)

Stop selling a consumer scorecard. Let the **agency** brand and send the checker to **its own clients**. Waypoint becomes the agency's client-facing tool, not a consumer critique of the agency.

- Converts B2C→B2B (hard, no evidence it works) into **B2B→B2B2C** (proven — this is how Travefy and Tern sell).
- Removes the adversarial framing that makes agencies resist.
- Still uses everything already built: PDF/OCR ingestion, extraction, suitability scoring.
- The agency is the buyer, so the ICP question collapses from eight to one.
- **Cost**: reframing + agency-side send/branding. No new pipeline.

### Option 2 — Sell the extraction, not the audit

The research found the genuinely unoccupied ground is **messy-input ingestion** — PDF/email/WhatsApp/OCR. All three checker competitors are paste-text only. No one owns "the note arrived as a WhatsApp screenshot in Hinglish."

- The defensibility is the eval set on real messy inputs, which compounds.
- Does not require winning a consumer audience.
- **Risk**: narrower story; harder to demo in 30 seconds.

### Option 3 — Narrow to India, WhatsApp-first, INR

Pick the one place where the incumbents are weakest: Tern, Travefy, and Fora are all US-centric, English, email-shaped products.

- WhatsApp is the operational backbone of Indian agencies [E] — the wedge is validated by how they already work.
- Goes straight at the geography the docs keep flirting with and never committing to.
- **Cost**: INR pricing at a fraction of $39/seat. Revenue per customer drops materially; volume must compensate.

### Option 4 — Stop GTM entirely until discovery is done

The 2026-08-01 audit said it: *"Discovery is the real P0."* Close the P0 loop defects, run 7–10 agency calls with a pricing question in each, then choose.

- Highest information value per unit of effort.
- **Cost**: another month with no distribution. Acceptable only if you believe the current canon is wrong — which the evidence suggests it is.

**My read:** Option 1 or 3, with Option 4's discovery running in parallel regardless. Option 1 because it fixes the adversarial-framing flaw that the research independently surfaced; Option 3 because it targets the one geography where the funded incumbents are weakest. They are not mutually exclusive — agency-branded checker, India-first, is a coherent single sentence. Option 2 is the fallback if the audit mechanic turns out to be too contested to matter.

---

## 6. Decisions needed from you

| # | Question | Why it blocks |
|---|---|---|
| **D1** | Do we keep the consumer-facing itinerary checker at all? | Three competitors already give it away free. Every week on it is a week not spent on ingestion. |
| **D2** | If we keep it — consumer-branded or agency-branded? | Determines whether the funnel is B2C→B2B (no evidence) or B2B→B2B2C (proven). |
| **D3** | India-first or global? | Sets currency, price band, and which competitors we actually face. Unresolved since May. |
| **D4** | One ICP. Which one? | Eight is not a strategy. The Aug-4 doc (Solo Luxury / Host Agency / UHNW) is the most recent and best-structured. |
| **D5** | Do we delete the fabricated testimonials and homepage numbers today? | Nothing else in GTM is credible while these are live. |
| **D6** | Is the network-effects moat in or out? | Two live documents assert opposite answers. |
| **D7** | Do we fix the P0 loop (Lead Inbox) before any outbound? | Acquiring users into a dead-ending funnel is worse than not acquiring. |
| **D8** | Do we kill the creator wedge (ADR 18)? | Its entry point doesn't exist and it's built on `DATA_DEPENDENT` components. |

---

## 7. Research handoff — topics for the separate research agent

Per your standing preference, these are handed off rather than done inline:

1. **Willingness-to-pay for agency software, India specifically.** Host Agency Reviews 2026 advisor survey results (unpublished as of now) is the best available source. Everything pricing-related in this repo is guesswork until this exists.
2. **Real keyword volumes.** $50 on Ahrefs for the five wedge phrases. SERP structure says dead end; confirm with numbers before killing it.
3. **Colloquial/multilingual extraction eval set.** "do japan", "me and 3 friends", relative date windows, Hinglish. The golden-set F1 of 0.9524 does not predict real-world performance — this is the highest-value research target in the whole list.
4. **Consortia and host agency gatekeeping.** Who signs a tech partnership at Virtuoso / TLN / Indian host agencies, what the commercial terms look like, and whether a pre-revenue vendor can get in the door at all.
5. **Fora and Tern teardown.** What Via and Tern's trip audit actually do end-to-end, from a trial account. They are the real competitive set.
6. **Adoption blockers.** The PhocusWire data shows adoption inflecting but I found **no quantified blocker data**. Do not assume we know why an agency says no.
7. **India regulatory surface for traveler data.** Consent, retention, and cross-border transfer for a tool that stores passport/visa data on Indian travelers.

---

## 8. Evidence tiers

- **Verified from code** (executed, this session): §2, §2.1, §2.2, §2.3.
- **Verified from live telemetry**: §2.1 (822 events parsed).
- **Verified externally with sources**: §3.1–§3.7 (URLs and dates inline).
- **Documented but unevidenced**: §1 in its entirety — the April–May canon has no customer input behind any of it.
- **Not found**: WTP data for India, keyword volumes, channel conversion rates, free-tool-wedge case studies. Marked [NF] rather than filled with plausible content.

## 9. Standing caveat

This repo is edited concurrently by parallel agents — `git status --short` showed **120 files changed** at the time of writing. Re-verify file:line references before acting on them. No files were modified and no git operations were performed in producing this assessment.
