# WOBS Appendix A — Round-1 raw role outputs (2026-09-09)

Verbatim transcript of the eight role reports from Round 1 of the wide-open brainstorm (agency-branded framing, later corrected by the owner — see Part 1.5). Mode: single-agent (no external LLM CLIs); all roles = read-only subagents over the repo. Prompts followed the `wide-open-brainstorm` skill template. Outputs are reproduced as returned, unedited.

---

## ROLE 1 — STRATEGIST (+ Methodologist)

Grounded in the repo evidence (Wedge-Fate pack, EX-07 gap register, GTM assessment §5, Ravi demo plan, pricing copy), here is the memo.

**1. True north star.** Not traveler score, not `action_packet_shared` (fired twice, both fixtures). The north star is **briefs that become quotes**: an agency-sent branded check that produces a brief the agency actually works. Leading metric: *checks sent per active agency per week*. Lagging metric: *% of checker-sourced briefs that reach a quote conversation*. The checker's job is no longer to be right about trips in the abstract (Spotinga/Fortrip already do that, free); it is to be the fastest structured brief an agency has ever received.

**2. What the alternatives get wrong.**
- Consumer checkers (Spotinga, Fortrip): paste-text, single-player, and structurally adversarial to agents — they score trips nobody is accountable for. They also have your exact distribution problem: zero funnel, zero retention. You would be joining a contested graveyard.
- Agency tools (Travefy, Tern): their client-facing surface is decorative — brochures, not truth instruments. They produce no structured intake; the agent still re-types the trip.
- Your own past framing: a critique of agencies delivered under the *Waypoint* logo. The GTM assessment's inversion is right — the logo must be the agency's; Waypoint lends the honesty, not the brand.

**3. The one insight — and it is already sitting in EX-07.** The gap register proves the checker is strong exactly where input is *structured or verifiable* (live weather/safety, declared composition) and weak where it needs parsed itinerary structure (connections, transfers, check-in buffers — internal endpoints exist, unwired, because freeform text can't support them). Everyone treats this as the public tool's deficiency. Inverted, it's the product: **the agency's involvement is what makes the input structured.** A client pasting text alone gets the honest shallow check; a client responding to *their agent's* link, who then reviews and files the report, closes the loop that makes deeper checks safe to enable. Distribution fixes the data problem, not just the traffic problem. The check is the intake — not a marketing gadget bolted onto it.

**4. Three strongest ideas, named.**
1. **Audit-as-Intake** — the branded pre-quote check emits the trip brief directly into the agency workspace via capability token. One artifact serves both audiences: the client gets "my agent is on top of this," the agency gets quote-ready fields. Pricing-page copy already tells this story ("Produces a cleaner brief for the agency") — ship the mechanics behind it.
2. **Borrowed Trust** — the report footer is a co-branded moment: Ravi's logo up top, Waypoint's honesty architecture underneath ("abstains instead of inventing"). Every sent check is a distribution event you don't pay for, and the abstention screen — your demo's strongest beat — becomes a differentiator clients remember.
3. **The Messy-Ingest Moat** — GTM assessment Option 2 is the compounding asset: the eval set built on real inputs (WhatsApp screenshots, Hinglish, scanned PDFs) no paste-text competitor touches. Capability-gated file upload is the unlock that eventually wires `connection-risk` and `timed-entry-audit` as advisory checks — exactly the EX-07 recommendation.

**5. Altitudes and horizons.**
- *Ground (6mo):* parameterize checker tenancy off `PUBLIC_CHECKER_AGENCY_ID`; build the send-link + capability-token share (design exists unbuilt); ship the EX-07 fast path (let users declare "already booked" so `visa_not_applied` fires); run Ravi as pilot zero.
- *1,000ft (12mo):* multi-tenant agency gallery replaces homepage checker decision; file upload with advisory logistics checks; branded domain.
- *10,000ft (24mo):* the extraction eval set is licensable — sell ingestion into any travel CRM. *Leapfrog:* a de-facto standard of co-branded abstaining reports; done honestly, this is the "trust ledger" the canon wanted, without network-effect fantasy.

**6. Methodologist: acceptance boundaries.** Gate 1 (Ravi, ~2 wks): does he send one real client check *unprompted*? Gate 2 (60d): 3 agencies × ≥5 real checks; brief extraction fidelity ≥ pre-check baseline; time-to-quote measurably down. Gate 3 (90d): agencies still sending in week 12; at least one asks about price. **Premise proven:** agencies send without chasing, clients complete, briefs get worked. **Premise falsified (→ Option C):** checks run but never become briefs (the check is a toy), or agencies demo it once and vanish (vanity tool), or real-file extraction fidelity collapses. Pre-commit the kill criteria now so Option C is a decision, not a drift.

*The thing most people miss about this:* the checker's honest shallowness isn't a bug to fix before launch — it's the reason the agency must be in the loop, and the agency in the loop is the whole business model.

---

## ROLE 2 — CHAMPION

**The case for full Option B, plus the page**

1. **Causal logic.** The consumer wedge did not die of product quality — the engine is built, honest, kill-switched, throttled, 90 tests green. It died of distribution: a cold web surface with zero traffic, paid launch NO-GO, and a homepage delink since June. Inversion doesn't change the engine; it changes who vouches for it. Same artifact, attached to a channel that actually exists: agency → client, warm, repeated, per booking.

2. **Trust physics.** A stranger's 0–100 score on your trip reads as attack ("who are you to judge"). The identical score from *your own agent* ("I ran your itinerary through my pre-trip check before quoting") reads as competence. Inversion is not a rebrand; it reverses the polarity of the entire report.

3. **The strongest objection dissolves.** The May 6 skeptic wrote: "pre-qualified is doing a lot of work — they might take the audit back to their original agent." Under inversion the agency running the check *is* the agent they'd book with. The leak in the funnel becomes the funnel.

4. **Architecture says yes.** The May 6 cartographer already named it: "The audit IS the intake" — TripBrief is entry-point-agnostic, so a client-completed check lands in the Ravi workspace as a pre-qualified brief with no translation and no re-keying. EX-04's capability token is ~2 units of work, reuses the hardened proposal-token machinery, fixes the live anonymous-401 defect, and delivers the share-handoff in the same stroke. Marginal cost is near zero; Option C destroys an honest, working surface to save nothing.

5. **Leapfrog.** Spotinga/Fortrip can copy a consumer checker; they cannot copy the channel. Travefy/Tern sell itinerary-building; nobody sells client-facing pre-quote diligence. The competitive moat is not the score — it's who is permitted to issue it.

6. **What makes this view RIGHT** (kill conditions): pilot agencies send links unprompted on repeat bookings; clients complete them without chasing; briefs land and get quoted. If agencies treat it as a one-time campaign gimmick, revert to Option A as holding pattern — that's the honest fallback, already sanctioned by the decision pack.

**Three named ideas**

1. **The Two-Minute Diligence.** Reframe the checker as the agency's standard first response to any inquiry: "Send me a TripCheck link." The report *is* the intake form. The page's strongest form: client opens an agency-co-branded moment — agency name up top, "Powered by Waypoint" small, report framed as *your agent's* diligence, CTA "send to your agent." Not a marketing surface; a client-facing professional artifact.
2. **Gallery, not Billboard.** Resolve the homepage-relink decision by replacing the consumer link with a gallery of real branded check pages from pilot agencies. The failed consumer page becomes social proof that sells the workspace — the checker graduates from lead magnet to demo asset.
3. **Token as Handoff.** Build EX-04 not as a checker patch but as Waypoint's universal exchange primitive: one signed, hashed, revocable token pattern governing every public↔workspace boundary — check results now, proposals (already exists), briefs next. That's the 24-month leverage: the capability token becomes the contract that lets Waypoint's public surfaces interoperate with its tenanted core.

**Horizon.** 6 months: 3–5 proprietor agencies piloting, per-tenant checker, token shipped, pricing tier-1 copy rewritten to describe what actually ships. 12 months: check links are routine agency workflow and the top source of pre-qualified briefs. 24 months: "running a pre-trip check" is the mark of a serious agency; Waypoint owns the client-facing diligence layer — the credit-bureau position from May 6, finally with the right brand-bearer.

*The thing most people miss about this:* the checker was never failing as a product, it was failing as a *vouching structure* — inversion adds no users, it adds a voucher, and that single change converts the same 0–100 number from insult into service.

---

## ROLE 3 — OPERATOR

Workflow mapped end-to-end against the code. Findings below.

## What works today vs. what's missing

**The engine (real):** `POST /api/public-checker/run` (`spine_api/routers/public_checker.py`, `spine_api/services/public_checker_service.py`) runs synchronously: payload caps (32k chars, JSON depth 10, 2,000 nodes) → full spine pipeline → live Open-Meteo climate/current-weather/regional-advisory enrichment (`src/public_checker/live_checks.py`, penalty capped at 35) → 0–100 validation score → trip persisted with `source="public_checker"` and `trip_status` of only `new`/`incomplete`/`blocked`. Kill switch (`PUBLIC_CHECKER_ENABLED=0`) 503s every route; frontend renders the maintenance notice.

**The tenancy hole (the whole product):** every run is saved under `PUBLIC_CHECKER_AGENCY_ID` — a *dedicated non-operating agency* asserted at boot (`spine_api/server.py:1112-1174`). Ravi's workspace never sees it. The agency trips page has no source filter to bridge, because tenancy blocks it upstream. There is no notification of any kind — `intake_started` and `first_credible_finding_shown` go to the ProductB analytics event store only.

**The client side (mostly real):** upload accepts .pdf/.jpg/.png/.txt/.webp; extraction is client-side (pdf.js text; images are *labeled* `ocr` but pdf.js returns nothing for image-only PDFs → thrown error); garbage guard is a 10-character minimum. Report renders with score, blockers, follow-ups. **Share-back is fake:** `handleShareReport` copies *summary text plus a report ID* to clipboard/`navigator.share` — no link exists (the `/shared/` routes are dead 401s per EX-04; the honesty-sweep test asserts their absence). Export/DELETE are 401 for the anonymous client today.

## The five micro-decisions

1. **What does Ravi send?** A per-client invite, not the public URL. Mechanism: extend EX-04's token issuance — workspace button issues a signed invite token (`/itinerary-checker?invite=tok`) plus a prefilled WhatsApp message. Branding (name/logo) resolves server-side from the agency row.
2. **Where does the brief land?** Invert tenancy: stamp `agency_id` from the invite token at `save_processed_trip` (the parameter already exists) instead of the env-fixed checker agency. Checker agency stays fallback for the unbranded page.
3. **How does Ravi know it arrived?** Reuse `first_credible_finding_shown` — on event with the new workspace_id, fire an inbox badge + optional WhatsApp Business webhook. No new schema.
4. **How does the client hand it back?** Replace clipboard text with EX-04's `share_token` (revocable, read-only `/itinerary-checker/shared/[token]` page). "Send to my agent" produces the link; Ravi claims it.
5. **What does Ravi quote from?** The trip row already holds packet/validation/decision. Needs a "Brief → Quote" action prefilling the quotes flow, and a status lifecycle beyond `new` (awaiting_review / quoted / archived).

## Operational edge cases

- **Abandonment** is pre-run (link opened, never uploaded) — the run is atomic, there is no half-state. Invites need expiry + one reminder; the EX-02 90-day TTL would delete briefs Ravi still needs — EX-02's own open question 2.
- **Garbage upload:** "aaaaaaaaaa" passes; image-only PDFs hard-fail client-side with a raw error. Needs a server-side quality gate and a human-sounding retry.
- **Two clients, one trip:** every run creates a new trip; no dedupe. Key on (agency, destination, date-window) or scope re-audits to the invite (the `re_audit_started` event already exists).
- **Public forwarding:** rate limit is per-IP only; an un-gated invite means stranger briefs land in Ravi's pipeline and his brand leaks. Invites must be single-use and revocable (EX-04 machinery).
- **Staleness:** current-weather signals are a point-in-time snapshot with no age marker. The client's re-audit path exists in the UI; nothing server-side versions reports or flags "checked 6 weeks ago."

## Three strongest operational ideas

1. **The Runner** — one workspace button: invite token + WhatsApp template. The entire "send" step is a single tap.
2. **The Brief Drop** — inverted tenancy: client's report materializes as a pre-qualified inquiry card in Ravi's trips/inbox with a real status lifecycle, not a dead row in a non-operating agency.
3. **The Handshake** — capability-token share-back: client taps "Send to my agent," Ravi claims the brief; claim converts invite → inquiry and revokes the token.

*The thing most people miss about this:* the engine already manufactures the agency's most expensive artifact — a structured, evidence-backed pre-quote brief — but the code delivers it to a non-operating agency and notifies nobody. The product isn't the analysis; it's "lands in Ravi's workspace with a status."

---

## ROLE 4 — CUSTOMER WHISPERER (+ Outsider)

Grounded in the repo: the checker lives in `src/public_checker/live_checks.py` — a penalty-deduction model (score_penalty, capped deductions for climate/current/safety) feeding a findings list and scorecards (see `Docs/research/ITINERARY_CHECKER_PARALLEL_BETA_IMPLEMENTATION_PLAN_2026-05-01.md`).

**The client's arc.** A 55-year-old gets a WhatsApp link from Ravi. First feeling: suspicion ("my bank says don't click links"). Trust is built or broken in the first two seconds — before any functionality. The fix is the URL itself showing the agency's name and the page opening with the person's own context: "Ravi asked us to check your Kerala trip." Generic branding = spam. Branded = Ravi's office.

**The upload is a shame moment.** Their itinerary is a photo of a screenshot of an email with a typo. "Is my messy plan going to be laughed at?" The product must treat garbage input as normal, even affectionate — "Got it, 4 screenshots stitched together. We can work with this." A rejection or parse-failure here isn't a UX error; it's a humiliation.

**The score is the cruelest object in the product.** A penalty-deduction system tuned by engineers reads as a verdict. A 43 to an anxious, pre-payment person says "my trip is ruined" — and worse, "Ravi sold me a ruined trip." The number must never be the headline for clients. Reframe from a grade to a gap list: not "your plan scored 43," but "3 things Ravi can fix before you pay." The score exists for the agency; the client should see findings as an action list, each finding pre-drafted as a WhatsApp message to Ravi. The best finding is invisible to the client and loud to Ravi.

**The agency's pride problem.** The report will catch what Ravi's quote missed. If the client sees "your agency missed a monsoon-window conflict," Ravi loses authority at the moment of maximum leverage (pre-payment, one-time, anxious). The inversion that saves it: the tool never claims credit — every finding is framed as "Flagged for Ravi's review," and Ravi gets a private, fuller report first, so he can call the client before they finish reading. The tool should make the agent the hero, the agent's software the back office. Ravi's actual fear: it exposes his thin margins and rushed quotes. His actual desire: a way to look like he employs an analyst.

**Outsider lens — unshared assumptions.** Builders assume "upload your itinerary" is clear (clients wonder: which document? the PDF or the hotel email?). Assume a health score is wanted (nobody asked to be graded). Assume agency-visibility is a feature (to the client it can read as surveillance: "will Ravi see I shopped around?"). Assume English, assume literacy in "findings," assume a desktop. And assume the tool is used once — the client's memory of it is a feeling, not a feature.

**Delight lives** in specificity and speed: naming the client's actual hotel, the actual weather that day, the actual 90-minute gap between landing and check-in. One concrete "we noticed your 6:40am arrival has no transfer" does more trust-building than the whole scorecard.

**Three ideas:**

1. **Ravi's Second Eyes** — every report ends with one branded line: "Reviewed with Ravi's travel desk. He'll follow up on the 3 items marked for him." The client's takeaway: my agent has a team.
2. **The Pre-Trip Seal** — after Ravi resolves findings, the client receives a shareable, dated "Checked & Cleared" seal for their family WhatsApp group. Turns anxiety into status; the seal is the viral object, not the report.
3. **Confession Mode** — a "what should I ask Ravi?" page that generates the client's questions for the agent, in their language, so the client never feels stupid and Ravi gets warmer, better-informed leads.

*The thing most people miss about this:* the checker isn't a trust-builder for the client — it's a trust *transferer*. The client doesn't learn to trust the software; they learn the software trusts Ravi, and that belief is what closes the payment.

---

## ROLE 5 — TRICKSTER (+ Cartographer)

Grounded in `frontend/src/app/(traveler)/itinerary-checker/PageClient.tsx`: hero + orb decorations, an UploadCard that says "Score My Itinerary," severity badges (Critical/Warning/Info), a "Score preview." The score is the current religion. Now the trickery.

**1. The Detective's Evidence Board (Corkboard & Red String).** Current framing hides that findings are *correlated*, not independent — a typhoon season warning connects to the flight buffer, which connects to the missed connection. An evidence board puts pins on a map of the itinerary with red string between findings: "this warning CAUSED this exposure." Reveals: today's report is a flat list of verdicts; the real product is a causal story. The hero becomes the itinerary itself, not a number.

**2. The Pre-Purchase Inspection Report.** Used-car buyers accept a mechanic's honest list: "brakes fine, CV joint worn, budget $600." Nobody asks for a score. Reveals: the agency's client doesn't want a verdict on their dream — they want to know what the *mechanic* (agency) would fix first, and what it costs. That reframes the check as a **pre-quote repair estimate**: "This itinerary is drivable. The Monsoon Gap will cost you ~$340 to fix. Want us to fix it?" The report IS the quote, wearing a coverall.

**3. The Visa Officer's Eyebrow.** The scariest, most useful metaphor. A visa officer doesn't score you; they raise an eyebrow at exactly one thing per application. Reveals: the funnel converts best when it surfaces the ONE finding the client can't un-see — a single annotated sentence on their own itinerary, circled in red marker by the agency, not a dashboard. Fear of the eyebrow, relief of the stamp.

**4. The Tailor's Fitting Session.** The itinerary is a garment; the agency is the tailor with pins in hand. No pass/fail — just "let's take this in here, let this out there." Reveals: findings should be *adjustments with a body*, not defects. The client leaves with their own itinerary, pinned, not graded.

**Cartographer — the improved page:**
- **Client sees first:** their own itinerary, rendered back at them (proof of reading), with 1–3 pins. The eyebrow. Everything else is background.
- **Zoom levels:** Pin (single finding: what, why, so-what) → Day (findings grouped by itinerary date) → Trip (the summary strip). One axis of navigation: *time*. An anxious phone user is always oriented because they know what day it is.
- **Agency view vs client view:** same pins, different overlay. Client sees plain language + "the agency can fix this"; agency sees cost-to-fix, supplier exposure, and quote hooks. Same object, two lenses — the capability token is literally "lens rental."
- **The score dial:** kill it as hero. A number invites negotiation ("can't I get an 85?") and conceals narrative. Demote it to a small "Fitting verdict" chip. The hero should be the **pinned itinerary** — the client's own document, touched by a professional hand. Trust comes from seeing your thing handled, not from being graded.
- **Navigation metaphor:** a bound **flight-crew checklist flipped into a scrapbook** — sequential, one screen per leg, progress dots along the timeline, no hamburger menu, nothing that requires backtracking.

**Three strongest, with sticky names:**
1. **The Red String** — findings as a causal evidence board over the itinerary timeline.
2. **The Worn CV Joint** — every critical finding priced as a repair estimate; the report ends in a quote, not a score.
3. **The Eyebrow** — one circled finding per check, promoted to hero; everything else filed beneath the fold.

*The thing most people miss about this:* the client doesn't fear a bad score — they fear discovering it *after paying*. The funnel's real magic is that it moves the moment of doubt *before* the quote, and the agency should charge for the pins, not apologize for them.

---

## ROLE 6 — SKEPTIC (+ Data Steward)

**The skeptic's cut of full-B.** Five months and 1,098 synthetic events bought you zero users. Full-B responds to that with infrastructure for a distribution channel that has never produced a single real click. That is the classic error: building multi-tenancy before one tenant exists, because tenancy is architecture-shaped (feels like progress) while distribution is rejection-shaped (feels like work). Full-B optimizes the demoable, not the usable. Cut it down to this:

1. **Cut per-agency tenancy.** One hardcoded agency config (Ravi's, if he says yes) is enough. Tenancy abstraction is a bet on scale you have no evidence for.
2. **Cut capability-token share.** Security polish for a surface nobody has visited. If a pilot needs "sharing," a plain link with an expiring nonce is fine.
3. **Cut branded invite-link infrastructure.** The premise being tested is not "can we generate pretty links," it is "will an agency ever send one." A human sending a URL manually tests the premise at full fidelity.
4. **Cut the workspace intake pipeline.** Reports landing in an agency workspace implies a second user (the agency employee) who also does not exist yet. Email the report to the owner. Humans are the MVP message bus.
5. **Improve the page only as a pilot artifact.** One page, one agency's name on it, tuned by watching Ravi's actual clients use it — not by speculating.

**Data Steward scope.** Instrumentation is currently poison: client-fed events, no trust model (per `Docs/exploration/RDA_EX03_KPI_TRUST_MODEL_2026-09-08.md`). Do not repair the funnel dashboard. Replace the question with a two-number experiment that is unpoisonable by design. Do not measure 1,098 events; measure two:

- **Number 1 — Sent.** Did the agency hand the link to real clients? Counted by the owner's own calendar/notes, not by telemetry. This is the entire premise. Three agencies × 10 clients, sent manually over two weeks.
- **Number 2 — Completed.** Server-side completion of a real itinerary check (server validates input, server logs completion against a per-link nonce). Ignore every client-emitted event; they are untrusted by construction until a trust model exists.

**Go:** at least one agency sends to ≥5 real clients unprompted, and ≥50% server-verified completion. **Stop:** agencies agree enthusiastically but never send ("yes" without "sent" is the universal fake-signal of B2B pilots), or senders complete <20%. One dead pilot costs a week. Full-B costs the Wave A P0/P1s — which are real work — and another five months of synthetic confidence.

**Three restraint ideas:**

1. **"Tenant of One.** Build for exactly one named agency. No tenancy, no branding engine, no admin panel. The abstraction is earned by the second tenant, not the first.
2. **Hand-Carried Pilot.** The agency sends links personally; reports return by email. Deliberately un-automated, because the distribution step is the hypothesis — automating it would let a fake premise succeed at scale.
3. **Poisoned-Pipe Firewall.** Server-sealed events only (nonce-bound, server-validated). Everything client-emitted is quarantined as untrusted until a trust model exists. Cheap, and it ends the "is this number real" argument permanently.

*The thing most people miss about this:* the consumer version failing does not mean the product failed — it means nobody was ever asked to send it. The scarcest resource is not engineering time for full-B; it is the courage to put a real link in front of a real agency's real client and find out. Ship the pilot, not the platform. The platform is what you build after the pilot refuses to die.

(The thing most people miss about this, stated twice by the role): automating distribution converts an honest, cheap "no" from agencies into an expensive, delayed "no" hidden inside infrastructure.

---

## ROLE 7 — FUTURE SELF

Grounded in the repo: `public_checker`, `intake`, `suitability`, `proposals`, `telephony`, `governance` modules already exist — so the 2028 answer builds on that skeleton.

**1. What all good versions share by early 2028**

Every winner is no longer a "checker" — it's a **trust machine**. Common DNA: (a) diligence findings are signed, versioned, and reusable across trips (a finding on an operator survives the deal that died); (b) the report is the *brief* — client-side artifact and agency intake are the same object with two renderings; (c) capability tokens have become standard inter-agency rail, so "we verified this leg, hand it off" is a protocol, not a PDF; (d) every check run feeds a per-agency memory: which clients say yes, which findings changed their mind, which suppliers burned them. By 2028 the moat isn't the diligence logic — everyone has that — it's the longitudinal record of what diligence predicted versus what happened.

**2. The leapfrog**

The check stops being a link. Three converging forms: the **WhatsApp-native flow** (the "check" is a conversation the client already started; your agent joins the trip group chat as a quiet participant), the **forwarded-anything parser** (client forwards the cousin's itinerary email/screenshot/PDF and the diligence happens on that artifact), and the **agent-side agent** — an MCP-capable counterparty that WhatsApp's own client assistant calls to pull a signed risk report. The strongest leapfrog: make the *check callable*. Waypoint's diligence becomes an MCP tool other agents invoke; every invocation spreads your finding schema and branding. You stop fishing for links and become infrastructure inside other people's conversations.

**3. Optionality vs local maxima today**

- Web page check: fine as the harness, but **local maximum as the surface**. Keep it as a fallback render; invest in the WhatsApp Cloud API flow now — per-tenant branding over WhatsApp Business is your real moat, white-label domains are a distraction (proprietor agencies don't own domains).
- **Score: local maximum. Findings: compounding.** A score compresses and gets argued with; signed findings with evidence chain aggregate into the trust ledger. Store findings as structured objects now even if the UI shows a number.
- Per-tenant branding: keep (it's the way agencies feel ownership), but design the brand token as a portable signed asset, not a CSS theme — that's what makes handoffs work later.
- Keep `public_checker` and `intake` reading from one canonical trip-packet schema (already true in the repo) — that seam is where the leapfrog attaches.

**4. What stops mattering**

The accuracy of any single finding. Model lifts compress everything to "good enough"; the scarce assets become provenance, memory, and the handoff network. Also stops mattering: the agency's website, the demo onboarding, per-check pricing.

**Time horizons.** 6mo: predictable — WhatsApp flow, findings ledger v1, branded links. 12mo: compounding — per-agency memory of diligence-vs-outcome, supplier track records across tenants (network effect begins), first capability-token handoff between two Waypoint agencies. 24mo: the weird brave move — flip the direction: clients carry their Waypoint dossier to any agency, and agencies *pay* to receive pre-qualified intake. Waypoint becomes the clearinghouse.

**Three sticky names:**

1. **Tarmac** — the pre-flight diligence layer: every trip cleared before takeoff, findings that never rot.
2. **Hawala Ledger** — trust that transfers between parties like the money network it's named for: signed findings + capability tokens moving between agencies.
3. **Ghost Companion** — the agent-side agent sitting in the family WhatsApp group, silent until asked, diligent always.

*The thing most people miss about this:* the check isn't the product — the check is the *excuse* to start a signed, structured conversation. Whoever owns that first structured artifact owns intake, proposals, booking, and money downstream; diligence is just the honest way in the door.

---

## ROLE 8 — EXECUTIONER (+ Devil's Advocate)

**The kill case holds.** Four attempted kills, one lands decisively, and the rest collapse into it.

1. **The strongest kill: Ravi's own recorded call proves the workflow full-B presupposes does not exist.** The repo's closest reality contact with the target user is `Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md`: Pranay calls Ravi in late November about a Singapore family trip, Ravi suggests Universal Studios and nature parks verbally, and says he will "return with a draft in one or two days." No document. No pre-quote itinerary to upload. The itinerary appears only after the agent does unpaid work. Full-B inverts an orphaned checker into the entry point of a funnel whose first step — "upload your quote for review" — never happens at proprietor scale. The repo's own capture UI already knows this: that scenario runs in `discovery`/`normal_intake` as freeform call capture, not document checking. Building per-agency branding, invite links, and capability-token handoffs on top of a step zero proprietor agents perform is building a door to an empty room.

2. **The thing being inverted is itself a mock.** `Docs/LANDING_PAGE_ITINERARY_CHECKER_AUDIT_2026-04-28.md` found "no actual upload or analysis backend wiring" — the checker is "a marketing-first surface." Five months and zero real users later, full-B would put agency logos on a funnel with no working core.

3. **The demo-theater kill and the Wave-A kill reinforce it.** `Docs/LAUNCH_STATUS.md` (2026-09-04) says NO-GO, and its own evidence table names the missing proofs full-B does nothing to supply: RLS hosted proof, encryption, durability, semantic ownership — the exact Wave-A P0s. A one-stakeholder demo does not need multi-tenant branding infrastructure; it needs the pilot gates the status doc already defines.

**What evidence would make each kill hold (watch for these):**

- Kill 1 holds unless Ravi — unprompted — produces written client-supplied itineraries/quotes *before* quoting in a real pipeline. One honest week of his inbox settles it.
- Kill 2 fails to hold only if a public checker run end-to-end (real upload, real findings, real report) already works in production; the April audit says it does not.
- Kill 3 fails only if Ravi commits to a paid pilot *before* full-B exists, i.e., the demo converts on the current product.
- Kill 4 fails only if Wave-A items (RLS hosted proof, encryption, disruption intake) are demonstrably not required for the invite-only pilot the status doc already conditionally approves — the status doc's own gate table says they are.

**Verdict:** Abandon full-B. Do the Ravi demo on what exists, and let his pilot gate requirements — not a funneled checker — determine whether agency distribution is real.

*The thing most people miss about this:* the funnel is downstream of trust, and proprietor agencies run on trust built in phone calls — so the product's true wedge is what Ravi said he'd deliver in "one or two days" (the draft), not what the client sends him first.

---

## Auditor's post-script on Round 1 (verification notes, 2026-09-09)

- Role 8's citation #1 verified in-repo (`DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md:6,42`) — it became the Round-1 kill grenade and reshaped the synthesis.
- Role 8's citation #2 verified real (`LANDING_PAGE_ITINERARY_CHECKER_AUDIT_2026-04-28.md`) but **stale**: the checker backend is now live-probed real (run works end-to-end, score produced, live checks fire, 189 tests green 2026-09-08). Kill 2 was therefore rejected in synthesis.
- Role 6's Tenant-of-One / Hand-Carried-Pilot / Poisoned-Pipe-Firewall cut list converged with Role 8's discipline independently — adopted as the synthesis spine.
- The Round-1 framing itself was later corrected by the owner (Part 1.5 of the main WOBS doc); several Round-1 conclusions were re-tested in Round 2 (Appendix B).
