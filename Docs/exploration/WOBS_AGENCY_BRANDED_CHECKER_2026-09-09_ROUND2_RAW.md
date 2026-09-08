# WOBS Appendix B — Round-2 raw role outputs (2026-09-09)

Verbatim transcript of the eight role reports from Round 2 of the wide-open brainstorm — the re-run against the owner's corrected thesis (Part 1.5 of the main doc): OPEN checker for ANY itinerary (self / LLM-generated / vendor package) → source-keyed corpus → routing to a marketplace of Waypoint's B2B customers. Roles were cross-pollinated with a digest of Round-1 conclusions and told to state where Round-1 conclusions survive, invert, or die. Outputs reproduced as returned, unedited. Lead verification notes by the auditor follow Role 8.

---

## ROLE 1 — STRATEGIST (+ Methodologist)

Repo grounding confirmed before writing: checker engine is real and live-probed (`/Users/pranay/Projects/travel_agency_agent/src/public_checker/live_checks.py`, kill-switch + live-check tests exist); launch is NO-GO (`/Users/pranay/Projects/travel_agency_agent/Docs/LAUNCH_STATUS.md`); the April wedge was retrospectively falsified — 822 synthetic events, north-star `action_packet_shared` fired twice, and the "tenant of one" claim contradicted by three live competitors (`/Users/pranay/Projects/travel_agency_agent/Docs/review/GTM_ANGLE_ASSESSMENT_2026-09-01.md`); marketplace supply today is literally one seeded canonical agency row (`/Users/pranay/Projects/travel_agency_agent/scripts/bootstrap_public_checker_agency.py`); and grep finds **no source-keyed corpus / attribution schema anywhere in `src/public_checker/`** — layers 1–3 of the corrected thesis are all unbuilt.

**ROUND-1 LEDGER — survives / inverts / dies**

- **"Briefs that become quotes" → survives, generalizes**: now the brief arrives at a *stranger* agency; the unit becomes the **routed brief with a status** (sent → accepted → fixed → paid). Round 1's status line survives verbatim, just one hop longer.
- **Kill-the-score-dial page → survives, sharpened**: a stranger's score is *more* insulting than an outsider's; the hero stays "your plan, 3 pins, here's who'll fix them."
- **Tenant-of-One → dies**. Three competitors already ship the check; the checker is not the moat. The moat candidate moves to the source-keyed corpus + acceptance loop.
- **Hand-Carried Pilot → inverts**: Ravi is not a distributor handing links to his clients; he is **receiver #1** proving routed briefs get accepted and fixed inside an SLA.
- **Poisoned-Pipe-Firewall → survives, promoted to Gate 0**: attribution (self/AI/vendor) *is* the corpus schema; client-fed events would poison it, so server-seal precedes everything.
- **Executioner kill ("clients phone in with no itinerary") → dies for layers 1–2** (open traffic doesn't depend on any agency's client list), **partially survives for layer 3** (agency-branded portals face the same empty room).

**NORTH STAR**: Not corpus size (an asset, maybe never monetized) and not the category (positioning, not metric). It is **routed-lead acceptance: % of reports whose 3 pins a vetted agency accepts and fixes**. Corpus growth and "verify any plan" are the leading indicator and the flag, not the scoreboard.

**What each gets wrong**: Consumer checkers score-and-dump — a number, no accountable closer. Agency tools assume a brief exists and never receive demand from the open internet. LLMs generate plans they can never be accountable for and cannot credibly audit themselves.

**The one insight**: the checker is an intake valve for accountability demand LLMs just created at scale — millions of AI itineraries nobody signs. Waypoint sells the signature, and only a corpus of source-keyed failures plus vetted humans can deliver it.

**METHODOLOGIST — gates and sequencing**
- **Gate 0 (pre-launch)**: server-sealed events only; retire client-fed KPIs. Nothing counts before this.
- **Gate A — corpus compounds (60d real traffic)**: ≥200 human-verified checks; ≥85% extraction; ≥60% yield ≥1 attributed pin; ≥30% of pins dedupe into existing failure-mode clusters (compounding, not one-offs).
- **Gate B — lead accepted (the never-built leg)**: ≥10 routed briefs, ≥30% accepted within SLA, ≥1 paid fix. Build routing to Ravi *before* any acquisition spend.
- **Kill**: pinned-finding rate <20% on real plans (checks are noise), or >70% brief rejection by pilots → you have an analytics toy, not a wedge.
- **Sequencing**: server-seal + attribution field → report close ("hand these 3 to an agency") routed to one pilot → proven acceptance before open traffic → agency-branded portals only for agencies who arrived via routed leads.

**Horizons**: 6mo — sealed corpus + routing, Gates A/B passed; 12mo — open launch, 10+ receiving agencies, portals for converts; 24mo — Failure-Mode Atlas as category reference, LLM vendors knocking. **Leapfrog**: an LLM vendor shipping self-audit + human handoff kills the middle; hedge is the corpus and the vetted network.

**Three strongest ideas**: **Second Opinion Engine** (neutral audit of any plan — paste a ChatGPT plan, vendor quote, or your own sheet); **Acceptance Ledger** (a corpus entry is complete only when a professional signs — acceptance as unit of truth); **Failure-Mode Atlas** (published, source-attributed failure rates by plan origin — the dataset that makes the category real).

*The thing most people miss about this*: the April wedge wasn't wrong, it was built back-to-front — the scarce thing was never the checker or the traffic, it's a professional willing to say "I'll fix this," and every one of the 822 synthetic events ran with zero such professionals on the other end.

---

## ROLE 2 — CHAMPION

The repo confirms the corrected frame: Waypoint OS already ingests messy artifacts and emits traveler-safe structured truth (README: "ingests messy inbound travel notes, structures them into canonical trip packets... produces traveler-safe outputs"). The corpus engine and report surface exist; the routing leg doesn't. That makes the owner's thesis a completion, not a pivot.

**The first-principles case.** AI trip planning just industrialized hallucination. Millions of ChatGPT/Gemini itineraries contain fabricated restaurants, closed venues, impossible transit connections, and stale prices — and nobody verifies them. Every generation of AI creates a verification market (fact-checkers, Webflow validators, spam filters). "Verify any plan" is the checker-position in travel. The corpus is the moat: every verified claim (fact + source + attribution) compounds into the only travel-truth dataset built from artifacts people actually bring, not scraped SEO. And the marketplace closes the loop: a verified plan is a *qualified lead with a diagnostic attached*. The report that says "3 findings, 2 fixable by an agency" is the highest-intent travel lead ever generated. Demand flows to agencies; agencies adopt your portal to catch it. Two-sidedness becomes an expansion motion, not an acquisition cost.

**Why this isn't the bet Round 1 killed.** The Executioner kill hinged on a proprietor client with NO written itinerary — the agency-branded tool demanded artifacts the channel didn't produce. The open consumer tool inverts the input: users arrive carrying artifacts (AI plans, OTA drafts, package quotes). The artifact shortage wasn't a market truth; it was a channel artifact. Round 1 was right that trust flows toward the person, not the brand — and that's *why* this works: the checker verifies the plan (brand territory), then hands the human to a trusted agency (trust territory). Round 1's trust-polarity flip is the thesis's engine, not its objection.

**What "improve the page" means.** The hero user is the person holding a 9-day Gemini itinerary at T-minus-3-weeks who suspects it's wrong and has no one to ask. The page becomes a *triage desk*: paste the plan, get findings with sources, then a single honest close — "an agency could fix all three of these." No score dial (Round 1 was right to kill it; a number hides the findings). The page's job is converting doubt into a handoff, and the brief-arrives-with-status artifact ("verified brief, findings attached") becomes what the agency receives.

**What makes this RIGHT even if unconventional.** If verification demand from AI-plan users is real and growing (search "is this itinerary real/safe/feasible"), if findings-to-lead conversion clears single digits, and if agencies will pay per qualified brief — then the checker is a demand engine agencies fund, not a consumer SaaS you subsidize.

**Preserve Round 1's discipline.** Pilot-first still binds: route leads to ONE waypoint agency manually before building the marketplace. Poisoned-pipe metrics still bind: "reports generated" is vanity; the only metric is *briefs accepted by an agency*. The page design discipline (findings over dials) carries over intact.

**Honest concessions.** Distribution still binds — a free checker needs cold-start traffic, and "verify my plan" search is unproven demand. Trust still binds — the corpus's authority rests on sourcing quality; one wrong "this restaurant closed" erodes everything. Abuse binds hardest — scrapers, competitor poisoning, people gaming findings to steer leads. And the April wedge's sin (shipping the easy leg, deferring the revenue leg) is a live risk: if lead-routing isn't piloted within weeks, this becomes checker-v2 with the same unfinished second leg.

**Three strongest ideas:**
1. **Corpus-of-Record** — every check feeds a source-keyed public fact ledger; the dataset becomes licensable and the brand becomes "the place that knows if your trip is real."
2. **Diagnostic-Attached Lead** — the handoff artifact is the verified brief plus findings; agencies pay for diagnosis, not clicks.
3. **Findings-Triage Close** — the report ends with exactly one action, routing to the fixer, mirroring the brief-with-status discipline.

*The thing most people miss about this:* the open checker doesn't compete with AI trip planners — it *monetizes their failure rate*.

---

## ROLE 3 — OPERATOR

OPERATOR MAP — corrected thesis, grounded in the code.

**What actually exists today (anchors)**
- Surface: `/Users/pranay/Projects/travel_agency_agent/frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx` — paste/upload/screenshot, client-side pdf.js parse, posts `/api/public-checker/run`, exports JSON, delete, share = clipboard text + raw Report ID (no URL).
- Engine/persistence: `/Users/pranay/Projects/travel_agency_agent/spine_api/services/public_checker_service.py` — synchronous run, saves trip with `source="public_checker"`, `agency_id=PUBLIC_CHECKER_AGENCY_ID` env or literal `"__UNSET__"` (the dead pseudo-agency), `user_id=None` (fully anonymous), `retention_consent` flag stored.
- Events: `ProductBEventStore` logs funnel events (`intake_started`, `first_credible_finding_shown`, `action_packet_shared`) — but NOT finding content. No corpus row today.
- Live checks: `/Users/pranay/Projects/travel_agency_agent/src/public_checker/live_checks.py` — regex destination/date extraction, weather/safety. No hotel/entity existence verification anywhere.
- No marketplace/lead/routing code exists at all; `agencies` are only multi-tenancy (`TripStore.get_trip_for_agency`, `AgencySettingsStore`). Rate limiter + payload caps exist; no identity, no acceptance handshake.

**Side 1 — checker user (three personas)**
- Self-planner: writes the paste themselves; gets a "did I miss anything" audit; routing = "a human finishes this" — pays via agency, user is the lead.
- AI-planner: pastes ChatGPT output; wants hallucination caught. Routing is strongest here: the plan is unbookable-by-construction if a hotel is invented. Nobody pays today; the fix cost is the agency's pitch.
- OTA-package buyer: uploads a MakeMyTrip PDF; wants "is this package a rip-off / will it rain / is the area safe." Routing means *switching* vendors — highest friction, lowest conversion; keep it a soft CTA.
- Fine-report case: routing is dead for them. Residual value = (a) a shareable "verified plan" badge (word-of-mouth), (b) scheduled re-check near travel dates (weather/safety are live checks already), (c) they become the corpus's clean-control rows. Do NOT force a CTA; the no-findings path is your trust engine.

**Side 2 — agency (Ravi, supply=1)**
A routed lead must arrive as: findings list + full plan + one reply channel + intent signal (user opted in). Not worth his time if it's spam or a grade-school "look at my score" toy run. The difference: a checkbox the user ticks ("send my plan to an agency") — consent IS the qualification.

**Side 3 — platform**
- Plan-source attribution: today only `input_mode` (paste/upload/mixed). Three signals available: a declared radio at paste time, PDF-producer fingerprints on OTA uploads, and a cheap text-style classifier. Declare-first, classify-second is enough.
- Routing mechanics: missing entirely — no lead table, no marketplace listing, no acceptance. But `PublicCheckerArtifactStore` + trip rows mean routing can be an *artifact annotation*, not new plumbing.

**Five micro-decisions to make easier**
1. Who declared the plan's source (radio vs silent classifier) and whether the report changes tone by source.
2. What ends the report: score, or one conditioned next action (fix-yourself vs hand-off).
3. What identity a lead carries (anonymous runs make routing impossible — one optional email/phone step).
4. What a clean report does (badge + recall date, not a CTA).
5. What the corpus row is: findings keyed by (destination, severity, plan-source) gated on `retention_consent` — the flag already exists.

**Edge cases**
- LLM-invented hotels: extraction finds the name, nothing verifies it exists. This is the killer feature — "reality check" every named entity. It's the one test OTA PDFs never fail and LLM plans routinely fail.
- Arguing with the report: no challenge path; add "dispute this finding" — disputes are the highest-value corpus rows.
- Bot poisoning: caps exist, identity doesn't; consent + reply-channel verification is the spam gate.
- Unaccepted leads: needs TTL + expiry state; with supply=1, an unaccepted lead is just Ravi's inbox noise — fine for now.

**Three strongest named ideas**
1. **Ghost Hotel Test** — entity-existence gate before scoring; fabricated names = hard blocker, headline finding.
2. **Fix-it Brief** — the export artifact doubles as the agency-facing brief with consented contact; routing = attaching a lead, no new pipeline.
3. **Second-Opinion Escrow** — structured dispute of findings; disagreements become corpus gold and public proof the checker is honest.

*The thing most people miss about this:* the checker's output isn't the product — the *consent moment* is. A user who pastes a hallucinated plan and opts in has performed the highest-intent agency-sales action in travel, and today that moment evaporates into a clipboard string and an `__UNSET__` agency row.

---

## ROLE 4 — CUSTOMER WHISPERER (+ Outsider)

Grounded in the repo (Waypoint OS: agency ops co-pilot pivoting to open consumer checker; source envelope + canonical packet specs already exist). Findings below.

**1. THE AI PLANNER — "my plan" vs "the AI's plan"**
After 3 evenings of coaxing, the ChatGPT itinerary is no longer ChatGPT's — it's theirs. They edited it, reordered it, chose the ryokan. So a hole in the plan is a hole in their taste, and the first instinct is defense: they will Google "is Fushimi Inari really closed" to disprove finding #3. This persona becomes empowered (not condescended to) under three conditions: (a) findings are source-keyed so disputes resolve in the tool's favor by evidence, not authority; (b) each finding has a "Disagree / it's fine" button — contesting converts ego threat into engagement, and re-scoring after their fix gives v2-beats-v1 dopamine; (c) the report leads with what's sound. "4 holes" framing loses to "your routing is right; the 4 things it missed." Score is acceptable here — this persona iterates and re-checks — but as a delta, not a verdict.

**2. THE VENDOR-PACKAGE BUYER — anger with nowhere to go**
Deposit paid, findings arrive: dread, then vindication, then powerlessness — they cannot edit the itinerary, the OTA owns it. They don't want a report, they want leverage. Anger seeks a target: badly built, they blame the checker ("why didn't you exist before I booked?"). The emotional unlock is splitting findings into *fixable* (vendor can swap the hotel) vs *recoverable* (deposit terms) vs *irrelevant*, and handing them a weapon: a polite, sourced escalation letter they forward to the vendor. Here the agency handoff lands as "someone in my corner," not a sales call — the buyer is the one persona who already wants a human to fight for them.

**3. THE MARKETPLACE MOMENT — trust is earned in the agency's first message**
An unknown agency earning a stranger's trust requires: the agency's opening message quoting the user's specific finding ("noticed your Day 3 is an 11-hour transfer — here's a fixed version, free"), consent + choice (user picks 1 of 3 matched agencies, no phone number required, agency replies in-product), and a visible "no pitch, no retainer" promise. Lead-gen-trap signal: any request for a call. Help signal: value delivered before any ask.

**OUTSIDER LENS — what the builder assumes that users won't share**
- People don't want their plan judged; they want it *confirmed*. The clean bill of health is a product, not an absence of one — and paradoxically it's what makes later criticism credible.
- "Source: KDDI outage dataset" reads like homework. A named human ("Pooja, Kyoto-based guide, on record saying…") transfers trust; a database doesn't.
- "Travel agency" means different things globally: nostalgic-scam to Americans, high-touch-trusted to Indians, alien to DIYers who used AI *specifically to avoid* one. The pitch must be "a fixer for the parts your plan can't cover," not "an agent."
- "Upload your itinerary" — real itineraries are WhatsApp threads, screenshots, PDFs with 40 pages. Ingestion friction, not scoring, is the cliff.

**Delight lives in:** the dispute-won moment (user contests, tool shows the receipt, user feels armed not judged), the v2-improvement delta, the free fixed-Day-3 from the agency.

**3 strongest named ideas:**
1. **Second Opinion** — medical framing, not grading: sound-things-first, per-finding Disagree button, version deltas.
2. **Ammunition Mode** — vendor-package buyers get a sourced escalation letter (fixable vs refundable), with the agency positioned as representative.
3. **The Cold Open** — matched agency's first message must contain a free partial fix of a flagged day, in-product, pre-consent; no calls.

*The thing most people miss about this:* the checker's most valuable output isn't the holes it finds — it's the permission to stop planning. The "your plan holds" verdict is what makes people trust the tool enough to accept its critique, and what makes handing the remainder to a human feel like completion rather than defeat.

---

## ROLE 5 — TRICKSTER (+ Cartographer)

Repo context confirmed (Waypoint OS: grounding layer, booking confirmations, agency integrations already exist — the metaphors can lean on real primitives).

## TRICKSTER — what is an ANY-plan verifier like?

**1. The Pre-Purchase Car Inspection ("PPI").** You bring any used car — dealer lot, Facebook Marketplace, your uncle's driveway. The mechanic doesn't judge your taste; he lifts the hood. *Reveals:* the product isn't judging the plan, it's inspecting it BEFORE commitment. *Corpus:* the mechanic knows which seller sent the car — "this one came from a dealer, this one from Craigslist" is exactly the AI-vs-human-vs-vendor badge. A self-planned itinerary gets the gentlest findings; a vendor package gets "did they actually book this, or just describe it?" *Marketplace:* after a bad PPI you don't fix the car yourself — the report IS the negotiation weapon (your Ammunition Mode is literally this: the PPI report held up to the seller). *Dispute:* you contest a finding with the mechanic, not the seller — a second lift on the same hoist.

**2. Airport Customs, not Security.** Not "are you a threat" but "what are you DECLARING?" *Reveals:* the corpus is a customs ledger. "Plan origin: AI-generated — 3 items undeclared (ghost hotel, closed-day ferry, expired visa)." Non-declared = the finding itself. *Dispute:* the customs appeal is a separate office, paper trail, ruling precedent — versioned, citable, Wikipedia-shaped.

**3. Corked-Wine Sommelier.** Universal ritual, one binary act per bottle, zero insult to the host. *Reveals:* the clean-report path. Nobody's day is ruined by "this one's fine, drink it." The badge system should feel like the sommelier's nod, not a red flag at the checkpoint.

**4. Estoppel/title search in real estate.** *Reveals:* the Ghost Hotel Test is a LIEN — an entity that doesn't exist, attached to your plan. Title searches don't score houses; they list defects by origin (surveyor, previous owner, county).

## CARTOGRAPHER — the page

**Hero object:** not a score, the **plan-as-manifest** — a customs declaration card: "Itinerary: Singapore, 5 days. Origin detected: ChatGPT (87% confidence)." The ghost hotel is pinned ON the manifest, crossed out in the inspector's red pen, with a sticky note: "no such hotel — did you mean X?"

**Source badge placement:** not "AI-generated plan detected" (insulting) but the sommelier framing — a provenance stamp top-right: *Provenance: AI-assisted — verified against 214 live sources.* Judgment sits in the findings, never the badge. The badge is descriptive ("we know where this came from"), findings are evaluative ("3 things will break").

**Route-to-agency CTA:** lives INSIDE the first red-pinned finding, not the footer: "The mechanic calls the garage for you." For vendor plans, the CTA becomes the Ammunition letter itself — "send this" — with agency routing as the "or we'll send it" default. Clean reports get zero CTA, only the re-check date (trust engine).

**Anxious phone user nav:** one vertical spine — stamp, findings, then a fixed bottom thumb-zone bar that changes with scroll state: before findings "Read the 3 flags", after "Hand this to someone." Nothing else. No menu.

## 3 strongest named ideas

1. **The Manifest** — provenance-stamped customs declaration; Ghost Hotel as a lien.
2. **The Hoist** — car-inspection grammar: findings stay, users leave with the report, agency = the garage that gets handed it.
3. **The Corked Ritual** — binary, gentle, every-plan universal; clean path earns the sommelier's nod + re-check date.

*The thing most people miss about this:* the corpus isn't an asset you build — it's a *ledger you inherit*. Every routed lead ships a pre-attributed record (AI vs self vs vendor) to the receiving agency; the marketplace's moat is that no agency can reconstruct provenance the way the inspector who touched the plan first can.

---

## ROLE 6 — SKEPTIC (+ Data Steward)

Repo check done. Two facts anchor this memo: `data/public_checker` exists and contains exactly zero bytes (manifests/uploads only — no corpus has ever accumulated), and the May 6 skeptic doc (`Docs/brainstorm_skeptic_2026-05-06.md`) already flagged "conversion is the job... build for the click." Nothing since has tested the click.

## Skeptic verdict — restraint for this thesis

**Yes, this is two products.** A universal verifier (consumer trust tool, B2C, viral-friendly) and a routed-lead marketplace (B2B2C, revenue). They share a report and nothing else. Building both at once repeats the April sin in mirror image: last time you shipped the easy leg (checker surface) and deferred the revenue leg (agency demand capture). The thesis repeats that — the checker is again the "easy" leg because it's code; the marketplace leg is the hard one because it's *negotiation*, not code.

**Which leg is risky? Routing, not checking.** Checking is a solved-ish engineering problem (entity-existence verification is well-defined and demoable). Routing is unproven end to end: zero corpus exists, supply is one agency, demand is unverified, organic acquisition already failed once. The Ghost Hotel Test proves checking *can* work; it proves nothing about whether a stranger with a broken itinerary will ever arrive, or whether Ravi will take the lead. Risk lives entirely in the funnel's two ends: inbound traffic and lead acceptance.

## Concrete cuts (do NOT build)

1. **Cut the open/universal surface.** "ANY itinerary, self/AI/vendor" triples parsers and edge cases for an audience of zero. Verifier v1 accepts ONE format (ChatGPT-style pasted itinerary). Vendors and PDFs wait.
2. **Cut Ammunition Mode.** Escalation letters serve OTA buyers who already paid — the narrowest segment of the narrowest funnel. It's a support-cost generator, not a wedge.
3. **Cut the marketplace UI entirely.** No vetted-agency grid, no profiles, no roster. Ravi gets a hotline (one routed handoff). You can't build supply-side product before supply-side agreement #2 exists.
4. **Cut the corpus as a feature.** Source-keyed corpus with consent/PII liabilities is a data liability with no consumer payoff in v1. Server-seal the minimum events for the experiment (below); store nothing else. The corpus becomes a product later, if the funnel works.
5. **Cut attribution radio/classify-fallback to one field.** Declare-radio only. Fallback classification is precision theater when traffic is near zero — you'll read tea leaves.

Keep: Ghost Hotel Test, clean-report page, consent-moment-as-product (it's the only mechanism that makes server-sealed consent unpoisonable), Poisoned-Pipe Gate 0.

## Data Steward — the minimal unpoisonable experiment

Server-sealed events only (Gate 0). Three numbers, 30 days:

1. **Raw visits → completed check submissions** (server-counted, client-fed inputs logged but untrusted). Proves demand exists at all.
2. **Clean reports → "route me" clicks.** Proves the trust engine converts to demand. Threshold: ≥5% of completed checks.
3. **Routed leads → Ravi accepts and responds within 48h.** Proves supply. Hand-tabulated, no pipeline needed.

Go/stop: fewer than ~100 completed checks in 30 days with free distribution attempted (one Reddit/one forum post, no spend) = **demand is dead; stop**. 100+ checks but <5% route-click = **fix the report, not the funnel**. Route-clicks ≥5% but Ravi accepts <50% = **supply is the bottleneck — recruit agency #2 before building anything**.

**Cold-start is NOT testable without spend as specified** — but one $200 targeted ad test (people who just booked an AI itinerary) is cheaper than any feature and directly answers the unproven demand question. That spend is the experiment, not the marketing.

## Three strongest restraint ideas

1. **"Click Before Corpus"** — nothing gets built (corpus, attribution, marketplace UI) until the third number exists at least once.
2. **"One Agency Stress Test"** — run the entire funnel with Ravi manually before a line of routing code; his acceptance rate *is* the north star.
3. **"Spend Is the Instrument"** — $200 of traffic is a measurement device, not growth. It buys the only answer organic never gave you.

*The thing most people miss about this:* the checker and the marketplace fail at different ends of the funnel — a great verifier with no traffic looks identical to a great marketplace with no supply, and this repo's zero-byte public_checker directory proves you've already built the middle of a funnel whose two ends were never tested.

---

## ROLE 7 — FUTURE SELF

**FUTURE SELF — EARLY 2028**

**(1) What all good versions share.** A canonical plan object: any itinerary (pasted, exported, agent-produced) decomposed into verifiable atoms — entities, dates, prices, sequences. Entity-existence checks (Ghost Hotel Test generalized to every claim: restaurants, visa rules, ferry schedules). Timestamped verdicts with a TTL, because plans are perishable. Honest partial verification ("verified 72%, here's what's unverifiable"). And one artifact that is simultaneously human-readable and machine-callable: a URL you can paste into a chat, an API response an agent can consume.

**(2) Leapfrog.** The destination site is the wrong default. By 2028 the winning form is **invisible infrastructure**: an MCP tool that Claude/ChatGPT call to self-verify *before* the plan reaches the user — distribution rides on the agent platforms themselves. The extension is the hedge (annotates surfaces that won't integrate you). WhatsApp-native is the non-US wedge. **What bypasses the destination roadmap entirely:** tool integration — you stop acquiring users and start being invoked. **What keeps the door open TODAY:** build the checker as a headless API with a content-addressed report artifact (hash of the canonical plan); tokenized briefs so any surface can submit a plan. **What bricks it:** a wizard-only web app, proprietary plan formats, ingestion that requires your UI.

**(3) The marketplace question.** "Route to a human agency" as *trip planning* is a bridge-to-nowhere. But reframed, it's the last durable moat: when agents book end-to-end, the binding constraint shifts from discovery to **liability**. The Acceptance Ledger becomes the underwriting layer — a professional's signature is the warranty. The agency becomes the insurer/recourse point when the ghost hotel is real, not the planner. Vendors self-auditing + handing off doesn't kill the middle, because nobody trusts the airline to grade its own safety. The Failure-Mode Atlas is what makes third-party verification *regulator-grade*.

**(4) Source attribution.** Yes — by 2028 plan-origin is the dominant trust axis, like organic vs. paid. "Human-verified itinerary" is a label people screenshot. What Waypoint does NOW so its corpus is *the* corpus: (a) publish the finding schema as an open standard and name the category — vocabulary wins precede product wins; (b) log failure events from every verification attempt regardless of whether the user returns (the Atlas is the moat, the checker is the funnel); (c) get LLM vendors calling your verification so you become the verifier of record; (d) time-stamp everything so the corpus has temporal depth, not just volume.

**Horizon pass**
- **6 mo** — Predictable: everyone ships a "verify my trip" button. Compounding: canonical plan schema + content-addressed URL reports + corpus enriching on every run. Weird-brave: publish the first source-attributed Failure-Mode Atlas — a PR nuke that names the category before anyone else can.
- **12 mo** — Predictable: extension annotating ChatGPT/Claude outputs. Compounding: Acceptance Ledger beta; agencies as signatories not leads. Weird-brave: continuous re-verification — a plan you "subscribe" to until travel date.
- **24 mo** — Predictable: verification as default infrastructure inside planning flows. Compounding: Atlas as the ratings agency of plan provenance. Weird-brave: the accountability marketplace — humans as insurers of AI-booked travel.

**Three strongest named ideas**
1. **Verify-as-API** — the checker is an endpoint with a content-addressed report object, not a destination.
2. **The Failure-Mode Atlas as Moody's for itineraries** — source-attributed, published, regulator-grade.
3. **The Warranty Layer** — the Acceptance Ledger inverts "route to a human" into humans-as-recourse for autonomous booking.

*The thing most people miss about this:* a verified plan isn't a one-shot artifact — it's perishable. Prices move, hotels close, visas change between planning and departure. Continuous re-verification until the trip ends turns a free tool into a subscription, and it's also what gives the corpus its temporal depth: failure rates over time are what make the Atlas credible, and credibility is the only thing underwriters will pay for.

Sources: none used (no web search; analysis grounded in the repo, e.g. `Docs/ADR_RAG_GROUNDING_AND_CITATION_PROVENANCE_2026-07-29.md` and `ADR_HIGH_VALUE_SIGNOFF_GATE_2026-07-29.md` echo the provenance and signoff motifs already present in the codebase).

---

## ROLE 8 — EXECUTIONER (+ Devil's Advocate)

**Kill review — Round 2: OPEN checker + corpus + marketplace**

**(b) SAME FAILED BET — HOLDS, decisively.** First commit 2026-04-09; the repo's own white-hat line: "0 real users/5 months" (`Docs/exploration/WOBS_AGENCY_BRANDED_CHECKER_2026-09-09.md`). Worse than zero users: the surface never even went live — `Docs/LAUNCH_STATUS.md` (2026-09-04) is "Public or paid launch: NO-GO," deployment target unprovisioned, `LAUNCH_AUDIT_BASELINE` notes `/v2`–`/v5` pages reachable with no robots.txt. No `/blog`, no sitemap in `frontend/src/app/`; the April blog/SEO plan (`Docs/CONTENT_SEO_STRATEGY.md`) was never built. The correction changes the hook, not the channel. A funnel whose top has never opened doesn't get fixed by re-labeling the door.
Watch-item: B9 competitor refresh (quota-blocked until 2026-10-06) showing existing verifier sites already capture this traffic.

**(e) CATEGORY ABSENCE — HOLDS, and the repo self-gates on it.** The owner's own document declares the load-bearing research ("AI itinerary verifier landscape, 'check your ChatGPT plan' demand") is unresearchable until the 2026-10-06 quota reset and is "a real gate before committing build effort." Documented SEO keywords are all B2B. Demand creation requires spend; `Docs/SALES_MARKETING_FIT.md` sets "zero ad spend until 50 paying customers." The repo literally cannot validate the demand before asking you to commit.

**(d) CORPUS LIABILITY — HOLDS hard.** The shipped UI and tests already promise the opposite of a corpus: "Not stored · Not shared · Session only" (`frontend/src/app/itinerary-checker/page.tsx`, asserted in `public_marketing_pages.test.tsx`). A corpus breaks a shipped trust contract. Independent repo evidence: DD-4 found "no consent/DPA gate" with PII flowing to LLMs by default; LAUNCH_STATUS blocker 6 requires human sign-off on PII/consent/retention before any public exposure; the public checker had 4 verified cross-tenant IDORs; and `Docs/exploration/RDA_EX04_...2026-09-08.md` shows the GDPR-style erasure path is currently dead code and any agency can read any checker trip. Vendor-scoring precedent: the trust scorecard was already blocked for "unsubstantiated claims" (`LAUNCH_AUDIT_SYNTHESIS`).

**(c) MARKETPLACE ILLUSION — HOLDS.** "The clearinghouse flip" (clients carry dossiers, agencies pay for intake) sits in the repo's own **dream column, 24-month leapfrog** — not a validated lane. Discovery is open (synthesis §4), monetization unbuilt (DD-6), supply = one proprietor agency whose only recorded behavior shows clients phone in without artifacts. The room's own highest-signal conclusion: "the distribution step IS the hypothesis; automating it converts a cheap honest no into an expensive delayed no."

**(a) NOVELTY NOT HABIT — inference, not repo-proof.** No usage data exists to prove one-time curiosity. Supporting only: "no account needed," session-only design, once-per-trip cadence. This one alone does not kill; it is a plausible corollary of (b).

**Verdict: the idea does not survive.** (b) kills it outright; (d) and (e) are independent, repo-verified compounders. The single riskiest assumption: that anyone organically seeks itinerary verification — untestable until Oct 6.

*The thing most people miss about this:* the corpus thesis contradicts the product's already-shipped privacy promise — the "data moat" requires breaking the exact trust contract the UI tests currently enforce.

---

## Auditor's post-script on Round 2 (verification notes, 2026-09-09)

- Role 8's kill (b) citation verified: no sitemap/robots in `frontend/src/app` or `frontend/public`, `Docs/CONTENT_SEO_STRATEGY.md` never executed — but the owner subsequently ruled (Part 3 of the main doc) that "never launched" cannot count as "demand falsified." Kill (b) is therefore a *sequencing input* (open the door deliberately), not a demand verdict.
- Role 8's kill (d) sharpest citation **FAILED verification**: no "Not stored · Not shared · Session only" copy or asserting test exists anywhere in `frontend/src` (rg across all tsx). What ships is the consent toggle ("Store my typed input… uncheck for a one-time analysis"). Kill (d) was downgraded in synthesis to: consent copy does not cover marketplace secondary use + vendor-scoring legal exposure — a redesign task, not a broken promise.
- Role 6's `data/public_checker` = zero bytes and `Docs/brainstorm_skeptic_2026-05-06.md` existence: both verified TRUE.
- The owner's final ruling (Part 3): build properly → open the checker's own door (scoped exposure decision, separate from the platform NO-GO) → market properly; B9/spend move from preconditions to post-exposure measurement.
