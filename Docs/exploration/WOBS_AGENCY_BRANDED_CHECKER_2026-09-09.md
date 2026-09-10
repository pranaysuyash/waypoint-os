# Wide-Open Brainstorm — Agency-Branded Checker (Full-B) (2026-09-09)

## PART 0 — Discussion & decision trail (what was said, in order)

Full-fidelity record of how this brainstorm came to be, with the owner's words preserved. Raw role outputs: **Appendix A (Round 1)** and **Appendix B (Round 2)** — `WOBS_AGENCY_BRANDED_CHECKER_2026-09-09_ROUND1_RAW.md` / `_ROUND2_RAW.md`.

1. **2026-09-08 — Random doc audit.** Pranay's reusable "Random Repo Document Audit" prompt drew `Docs/context/ITINERARY_CHECKER_GTM_WEDGE_2026-04-14.md` (2,225-doc population, SystemRandom). Four parallel agents + live probes. Verdict: wedge implemented divergently, quietly demoted, never closed; honesty defects (fabricated testimonials, fake email gate, anonymous 401s, KPI-poisonable events). Report + register delivered.
2. **2026-09-08 — "do all following the doctrines".** Register Buckets A (EXPLORE) + B (IMPLEMENT) executed same session (testimonials/email-gate removed, kill switch, event rotation, throttles, XFF rate key, agency guard, dead-share cleanup, supersession banners, 8 explore docs, wedge-fate decision pack). 189 backend + 22 frontend green.
3. **2026-09-09 — Pranay challenged the AUD-07 "false positive" framing:** *"why should the pricing/marketing link to itinerary checker? isnt that the gtm wedge?"* → Verified: links work, but they ARE the wedge in copy (pricing tier 1 = "Traveler checker… pre-qualifying a trip before it reaches the agency"; PublicHeader default nav). Reframed: FT-03 moot as a broken-link fix; FT-G7 (marketing-link disposition) added to Bucket C, D-01-gated.
4. **2026-09-09 — "keep this open as a task for later"** (on the quota-blocked competitor refresh) → Open Work Roadmap rows **B9** (retry 2026-10-06, queries recorded) and **C7** (wedge decisions).
5. **2026-09-09 — "whats left?"** → Decisions D-01..D-05, Bucket C, full-suite debt, uncommitted tree.
6. **2026-09-09 — "lets discuss, explain"** (D-01 selected) → Three options argued: kill steelmanned (surface = liability tax), keep called a trap (unowned surfaces decay — the testimonials/email-gate proved it), invert argued on five grounds (distribution dissolves, trust flips to the agent, pricing copy already inverted, feeds the core loop, ~full engine reuse); recommendation narrowed to "B pending one Ravi discovery answer, C-lite if it fails."
7. **2026-09-09 — Pranay decided:** *"i think i will improve the page and do full B plus more if needed… you should call wide open brainstorm or the council orchestrator or personas that may help with this… even online research if needed"* → Skill-tool invocation timed out; SKILL.md read and followed manually. No external LLM CLIs → single-agent mode, 8 roles. Round 1 ran (Appendix A). Search quota exhausted (→ B9 debt made load-bearing).
8. **2026-09-09 — Pranay's counter-frame (Part 1.5):** *"you took it such that the b2b side itself is asking clients to check their own provided itineraries while i had the gtm wedge inverted, people get to check any itinerary whether their own, an llms or any other vendor, we build a data corpus, and we also maybe make that a funnel to a marketplace of our own b2b customers… have you considered exploring?"* → Conceded the frame miss; compared B vs B′; proposed stack (B′ acquisition layer, B expansion layer); re-aimed pilot metrics; flagged B9 as now load-bearing.
9. **2026-09-09 — Pranay: "document the whole brainstorm… then what we discussed and then run it again against the brainstorm"** → Part 1.5 written; Round 2 dispatched with cross-pollination digest (Appendix B); Part 2 synthesis: corrected kill ledger — (b) channel and (e) demand-research gate hold, (d) corpus-liability downgraded after its citation failed verification, verdict "conditional survive" with build conditions (proceed / gated / pause-cuts).
10. **2026-09-09 — Pranay's epistemics ruling (Part 3):** *"why before launch you keep breaking your head… if you build properly, we start marketing properly"* → kill (b) ruled circular (the channel was never opened; zero organic usage cannot falsify demand); gates inverted: build properly → the checker earns its own scoped exposure decision (separate from platform NO-GO) → market properly, with B9/spend as post-exposure measurement, not preconditions.

> **PART 1.5 — THE OWNER'S COUNTER-FRAME (Pranay, 2026-09-09, same day).** Round 1 anchored on the Sept-1 assessment's reading of "invert" (agency-branded private tool). Pranay corrected the frame: **the inverted wedge is an OPEN checker that verifies ANY itinerary — the user's own, an LLM-generated plan, or another vendor's package — builds a source-keyed data corpus, and funnels users to a marketplace of Waypoint's own B2B customers** ("3 things wrong with this plan → hand it to a vetted agency who'll fix them"). Key properties: agencies are demand *receivers*, not distributors; the funnel does not depend on clients arriving with pre-quote documents (the Executioner's kill-1 evidence is about the agency→client flow, not this); the original April wedge is reframed as *unfinished* (checker shipped; the quote-improvement → lead-routing → partner-agency leg that monetizes was never built — the orphan surface was an open-top funnel with a bricked middle). Round-1's agency-branded B survives as the *expansion layer* (branded check portal as a paid feature for agencies who became customers via routed leads), not the acquisition layer. Round 2 (below) re-ran all eight roles against this corrected thesis. Research debt note: B9's competitor refresh must be reframed for this thesis ("AI itinerary verifier" landscape, "check your ChatGPT plan" demand) and is now load-bearing — Oct 6 reset is a real gate before committing build effort.

Method: `wide-open-brainstorm` skill, single-agent mode (no external LLM CLIs). Eight roles as differentiated read-only subagents: Strategist(+Methodologist), Champion, Operator, Customer Whisperer(+Outsider), Trickster(+Cartographer), Skeptic(+Data Steward), Future Self, Executioner(+Devil's Advocate). Web search quota-blocked (resets 2026-10-06; roadmap B9). All role claims spot-verified where load-bearing (both Executioner citations checked in-repo this session).

## Verdict (read this first)

**The kill test did not pass cleanly.** The Executioner's strongest kill is repo-verified and must shape the build: the one recorded real interaction with the target user (`Docs/research/DATA_CAPTURE_UI_UX_AUDIT_2026-04-27.md:6,42`) shows a proprietor-agency client who *phones in* a trip idea and the agent promising "a draft in one or two days" — **no client-supplied written itinerary exists at the moment full-B's funnel starts**. The upload-your-itinerary step may be a door to an empty room at proprietor scale.

But this kills *full-B-as-platform*, not the direction.Converted into build conditions below, the room converged on: **commit to B as the destination, but enter through a hand-carried pilot of one tenant — never through tenancy infrastructure.** (Skeptic and Executioner converged on this independently — highest-signal result of the session.)

Kill status per case:
1. "Clients don't arrive with written itineraries" — **HOLDS as premise threat** (one real data point; falsifiable by one week of Ravi's inbox). Watch: does any client arrive with *any* written artifact (OTA draft, forwarded quote, cousin's Excel, screenshots)?
2. "The checker is a marketing mock" — **STALE, fails.** April audit described the mock; current backend is live-probed real (run works end-to-end, score produced, live checks fire, 189 tests green).
3. "Demo theater for one stakeholder" — partially holds; dissolves if the demo converts Ravi to a *paid/unpaid real pilot* on current product.
4. "Wave A owns the hours" — holds as sequencing constraint, not a kill: pilot rides alongside Wave A; full-B waits behind the gate.

## Champion vs Executioner arbitration (skill §6.5)

**Champion's case:** the consumer wedge died of distribution, not product quality; inversion changes who vouches — the same 0–100 number is an insult from a stranger and a service from your own agent (trust polarity flip); pricing-page copy already tells the inverted story; capability tokens reuse hardened proposal-token machinery; competitive moat = the channel (who may issue the check), not the score.
**Executioner's case:** the funnel's first step is unpopulated at proprietor scale (kill-1 evidence above); full-B builds infrastructure for zero tenants; Wave-A P0s are real work; "yes without sent" is the universal fake-signal of B2B pilots.
**What makes Champion concede:** Ravi confirms clients never bring written plans AND he won't ask them to. **What makes Executioner concede:** any real client artifact (forwarded quote, OTA draft, screenshots) reaches a real check — or Ravi actively wants the branded pre-quote artifact for his own authority.

**Build conditions:**
- **Proceed now (cheap, premise-agnostic):** page-improvement subset (see below); server-sealed completion metric; single hardcoded pilot tenant ("Tenant of One").
- **Prototype first:** branded page for exactly one named agency; plain expiring-nonce links; "Sent/Completed" two-number experiment.
- **Pause until gate passes:** per-tenant branding engine, invite-token infrastructure, automated workspace intake routing, WhatsApp Business integration, pricing-copy rewrite.
- **Kill (→ Option C-lite):** pilot fails — agencies won't send, or sends never complete, or no client artifact ever exists to check.

## Where the room converged (highest signal)

1. **The product is not analysis — it's the brief's arrival.** (Strategist + Operator + Skeptic) The engine already manufactures the agency's most expensive artifact — a structured, evidence-backed pre-quote brief — but today delivers it to a non-operating agency and notifies nobody. "The product isn't the analysis; it's 'lands in Ravi's workspace with a status.'"
2. **Trust polarity + agent-as-hero.** (Champion + Customer Whisperer) Inversion reverses the report's polarity; and the tool must never outshine the agent — every finding framed as "Flagged for Ravi's review," Ravi sees the fuller report first. "The client doesn't learn to trust the software; they learn the software trusts Ravi."
3. **Automating distribution converts a cheap honest "no" into an expensive delayed "no."** (Skeptic + Executioner, independent) The distribution step IS the hypothesis; a human manually sending a URL tests it at full fidelity. Tenant of One. Hand-Carried Pilot.
4. **The score must not be the client's headline.** (Customer Whisperer + Trickster) A 43/100 to an anxious pre-payment person reads "my trip is ruined" (worse: "Ravi sold me a ruined trip"). Reframe: findings as "3 things Ravi can fix before you pay" — the repair estimate, not the grade. Trickster: "the client doesn't fear a bad score — they fear discovering it after paying."
5. **Strategist's keystone:** the checker's honest shallowness is the reason the agency must be in the loop — agency involvement is what makes deeper structured checks safe to enable. "Distribution fixes the data problem, not just the traffic problem."

## Named ideas worth keeping

Practical now: **The Eyebrow** (one circled finding as hero; the client's own itinerary rendered back with 1–3 pins — kill the score-dial-as-hero, demote to a chip) · **Ravi's Second Eyes** (every report closes with the branded line naming the agent's follow-ups) · **Confession Mode** (generate the questions the client should ask their agent) · **Poisoned-Pipe Firewall** (server-sealed events only; client-emitted events quarantined until a trust model exists).
Prototype lane: **The Runner** (workspace button → invite link + prefilled WhatsApp template) · **The Brief Drop** (report materializes as an inquiry card with a real status lifecycle) · **The Handshake** (capability-token claim converts invite → inquiry, revokes token) · **Pre-Trip Seal** (dated "Checked & Cleared" shareable for the family WhatsApp group — the viral object) · **The Worn CV Joint** (every critical finding priced as a fix estimate; the report ends in a quote, not a score).
Dream column (24mo / leapfrog): **The Red String** (causal evidence board over the itinerary timeline) · **Tarmac** (signed, versioned, reusable findings ledger — findings that outlive the deal) · **Hawala Ledger** (capability-token handoffs between agencies = trust that transfers) · **Ghost Companion / MCP-callable diligence** (the check becomes infrastructure other agents invoke; WhatsApp-native flow replaces the link) · **The clearinghouse flip** (clients carry the dossier to any agency; agencies pay for pre-qualified intake).

## Page-improvement shortlist (serves "improve the page" now, no tenancy needed)

1. Hero swap: client's own itinerary rendered back with 1–3 pinned findings; score demoted to a small chip. Navigation = time (one screen per day/leg, progress dots).
2. Client view vs agency view: same pins, two lenses — plain language + "Ravi can fix this" for the client; cost-to-fix + quote hooks for the agency.
3. Findings pre-drafted as WhatsApp-ready messages to the agent.
4. Upload shame-safety: treat garbage input as normal ("Got it, 4 screenshots stitched together — we can work with this"); fix the image-only-PDF raw error; raise the 10-char garbage threshold.
5. Specificity delight: name the actual hotel, the actual arrival gap ("your 6:40am arrival has no transfer").
6. Report closes with the agent's line ("Reviewed with Ravi's travel desk — he'll follow up on the 3 items marked for him").

## The pilot protocol (Data Steward / Methodologist)

Unpoisonable two-number experiment — instrumentation today is client-fed and untrusted (RDA_EX03); do NOT repair the funnel dashboard for this:
- **Sent** — counted by the owner's calendar/notes, not telemetry: 3 agencies × 10 clients, links sent *manually*, two weeks.
- **Completed** — server-validated check completions per nonce link.
- **Go:** ≥1 agency sends to ≥5 real clients unprompted AND ≥50% server-verified completion. **Stop:** enthusiasm without sends, or <20% completion. One dead pilot costs a week; full-B costs the Wave-A P0s plus another five months of synthetic confidence.

## Horizons

6mo: pilot of one tenant, page improved per shortlist, server-sealed metrics, EX-07 fast-path ("already booked" → visa check fires). 12mo (if gate passed): multi-tenant branding, Brief Drop lifecycle, WhatsApp-native flow as primary surface, per-agency diligence memory. 24mo: signed findings ledger, inter-agency token handoffs, extraction-eval moat licensable; leapfrog = diligence as callable infrastructure. Optionality rule: keep web page as harness; keep findings as structured objects (compounding) even while UI shows a number (local maximum).

## Six-hat coverage

White: engine real (live-probed), 0 real users/5 months, Ravi call = no pre-quote doc, NO-GO, Wave-A competition. Yellow: trust flip, copy already aligned, pilot is days-cheap, engine reuse ~100%. Black: empty-room funnel risk, tenant-zero infrastructure, score-as-verdict harm, agent-authority exposure, retention-vs-brief conflict, poisonable KPIs. Green: Eyebrow, repair-estimate framing, seal, confession mode, red string, callable diligence. Red: shame on upload, surveillance fear ("will Ravi see I shopped around?"), agent pride exposure, client remembers a feeling not a feature. Blue: pilot protocol + build conditions + this document.

## Reformulated reusable prompt

"Interrogate [feature] as a pilot-of-one before a platform: map the real two-sided workflow, find the five micro-decisions, run the kill test against the closest recorded real-user evidence, define a two-number unpoisonable experiment with go/stop thresholds, and only then design the page — hero object first, client/agency lenses, shame-safe inputs."

---

# PART 2 — Round 2: the room re-run against the owner's corrected thesis (2026-09-09)

Seed: OPEN checker for ANY itinerary (self / LLM-generated / vendor package) → source-keyed corpus → routing to a vetted-agency marketplace (supply ≈ 1). Same 8 roles, cross-pollinated with the Round-1 digest and Part 1.5's counter-frame.

## Round-1 ledger under the new frame (Strategist)

Survives: "briefs that become quotes" (generalized to *routed* briefs with status); kill-the-score-dial page; Poisoned-Pipe Firewall (promoted to Gate 0 — attribution *is* the corpus schema). Inverts: Hand-Carried Pilot (Ravi becomes receiver #1, not distributor). Dies: Tenant-of-One as strategy (three competitors already ship a check; the moat candidate moves to the source-keyed corpus + acceptance loop). Executioner's Round-1 kill (no pre-quote documents) **dies for layers 1–2** (open traffic doesn't depend on any agency's client list), partially survives for layer 3 (agency portals).

## Round-2 convergences (highest signal)

1. **North star: routed-lead acceptance, not corpus size.** (Strategist) "A corpus entry is complete only when a professional signs" — Acceptance Ledger. Gate B: ≥10 routed briefs, ≥30% accepted in SLA, ≥1 paid fix.
2. **The Ghost Hotel Test is the wedge inside the wedge.** (Operator, independently Trickster's "lien" + Future Self's entity-existence generalization) Entity-existence verification — LLM-invented hotels as hard blockers — is the one test OTA PDFs never fail and LLM plans routinely fail. Reality-check every named entity.
3. **The consent moment IS the product.** (Operator) A user who pastes a hallucinated plan and opts into routing has performed the highest-intent agency-sales action in travel; today that moment evaporates into a clipboard string and an `__UNSET__` agency row.
4. **Findings-first page, provenance stamp not accusation.** (Trickster + Customer Whisperer + Champion) Hero = the plan-as-manifest with pins ("The Manifest", "The Hoist" car-inspection grammar); provenance badge is descriptive ("AI-assisted — verified against 214 live sources"), judgment lives in findings; "Second Opinion" medical framing with a Disagree button per finding; clean reports get the sommelier's nod + a re-check date (the trust engine), zero CTA.
5. **The funnel's two ends were never tested; you built the middle twice.** (Skeptic, echoing Round-1's convergence) Checking is engineering; ROUTING is the unproven leg. Cut-list: multi-format ingestion v1 (one format: pasted LLM-style itineraries), Ammunition Mode, marketplace UI, attribution classifier (declare-radio only), corpus-as-feature.

## Kill test — verdict, with auditor corrections

Executioner verdict: "does not survive" — but its three holding kills need correction after spot-verification:

- **(b) Same-failed channel — HOLDS.** No sitemap, no robots, no blog (CONTENT_SEO_STRATEGY never built), launch NO-GO, 0 organic users in 5 months. The correction changes the hook, not the channel. Watch-item: B9.
- **(e) Category absence — HOLDS as a gate.** "AI itinerary verification" demand is unresearchable until the Oct 6 quota reset; SALES_MARKETING_FIT sets zero ad spend until 50 paying customers. The repo cannot validate demand before asking the owner to commit.
- **(d) Corpus liability — DOWNGRADED.** Its sharpest citation (a shipped "Not stored · Not shared · Session only" promise, test-enforced) **failed verification — no such copy or test exists**; what ships is a consent toggle covering "product improvement" storage. Surviving (d)-core: consent copy does NOT cover marketplace secondary use or vendor-scoring (legal exposure for scoring OTA packages), and EX-02 retention is unresolved. The corpus is therefore a *consent-redesign + legal-scoping task*, not a broken promise.
- **(c) Marketplace illusion — HOLDS as sequencing constraint** (supply = 1; the clearinghouse flip is Round-1 dream-column).
- **(a) Novelty-not-habit — inference, untestable until traffic.**

**Arbitrated verdict: the corrected thesis SURVIVES conditionally** — as a product direction with two untested load-bearing premises (verification demand exists; routed leads get accepted), one hard channel gate (distribution — Oct 6 research and/or owner-approved spend-as-instrument), and one redesign obligation (consent + legal scoping before corpus-as-feature).

## Build conditions

**Proceed now (no kill touches these):** Gate-0 server-sealed events; Ghost Hotel Test (entity-existence gate); page rework per convergence 4 (Manifest + provenance stamp + pins + findings-first + clean-report path + Disagree); Ravi as receiver #1 — manual acceptance test of the first 10 routed briefs before ANY routing code; consent-copy redesign scoping (product-improvement vs routing vs corpus).
**Gated on evidence:** corpus-as-feature (Gate A: ≥200 verified checks, ≥85% extraction, ≥60% yield ≥1 pin, ≥30% pins dedupe into failure clusters); marketplace (Gate B above); Oct 6 B9-reframed research (demand landscape — load-bearing); any ad spend (owner gate: Spend-Is-The-Instrument, $200 test vs zero-spend rule).
**Pause/cut:** multi-format ingestion, attribution classifier, Ammunition Mode, marketplace UI, agency-branded portals (wait for agencies who *arrived via routed leads*).

## Round-2 named ideas (kept)

Second Opinion Engine · Acceptance Ledger · Failure-Mode Atlas (source-attributed failure rates by plan origin — publish early, "PR nuke that names the category") · Ghost Hotel Test · Fix-it Brief · Second-Opinion Escrow (disputes as corpus gold) · The Manifest / The Hoist / The Corked Ritual · Ammunition Mode (parked) · Verify-as-API (content-addressed report artifacts, headless) · The Warranty Layer (agencies as recourse/insurers for AI-booked travel) · Continuous re-verification until travel date (perishable plans = subscription + temporal corpus depth).

## Six-hat coverage (Round 2)

White: engine real; zero corpus bytes ever; supply=1; demand research blocked to Oct 6; no sitemap/robots. Yellow: AI-hallucination wave; highest-intent lead ever generated = diagnostic-attached; engine reuse. Black: channel death; two-products-in-one; consent/legal scoping; LLM vendors self-auditing (hedge = corpus + vetted network). Green: Ghost Hotel; Manifest; Escrow; Atlas; Verify-as-API; Warranty Layer. Red: ego threat of judged AI plans → Disagree button; OTA-buyer anger → leverage not pity; agency first message = free partial fix, never a call. Blue: gates A/B + proceed/gated/pause lists above.

## Reformulated reusable prompt

"Re-run every role against the corrected owner frame before accepting any kill verdict; verify each Executioner citation in-repo before it lands; separate what the kill touches (channel) from what it doesn't (product); define the two funnel ends as the only gates; cut the middle."

---

# PART 3 — Owner ruling on kill (b): the channel was never opened (2026-09-09)

**Pranay's correction (adopted):** *"Why before launch you keep breaking your head… if you build properly, we start marketing properly."*

Kill (b) ("same failed bet — zero organic users") is **circular and downgraded to inadmissible as demand evidence.** The door was never opened: no sitemap/robots, homepage delink, launch NO-GO, all traffic synthetic. Five months of a private dev instance cannot falsify demand — it can only prove a private instance attracts nobody, which nobody doubted. The Sept-1 assessment's word "falsified" overclaimed (it falsified the wedge *as operated*, i.e. operationally nothing); both rounds inherited that overclaim.

**Inverted gate structure:**
- Research (B9, reframed) and any spend test move from *pre-build preconditions* to *post-exposure measurements*. The demand question is only answerable by exposure.
- "Build properly" = the light exposure envelope, NOT the full platform NO-GO stack: honest findings ✅ · kill switch ✅ · abuse caps ✅ · consent ✅ · remaining: Ghost Hotel Test, findings-first page rework, server-sealed funnel counting, one retention-policy line, disclaimer copy. That is the entire pre-launch list.
- The checker earns **its own scoped exposure decision** — separate from the platform NO-GO.
- "Market properly" then runs: sitemap/robots, the ownable hook ("your AI itinerary has holes — we find them before you pay"), and the two server-sealed numbers (completed checks; routed leads accepted) as the standing strategy dashboard. B9 becomes sharpening, not gating.

**What survives from the kills:** (e) shrinks to "name the category honestly when marketing" (no demand claim without data); (d)-core stays as build scope (consent redesign for secondary use; vendor-scoring legal care); sequencing discipline (receiver #1 before routing code; findings before corpus-as-feature) is unchanged.

---

## Appendices (raw role transcripts)

- **Appendix A — Round 1, all 8 role outputs verbatim:** `Docs/exploration/WOBS_AGENCY_BRANDED_CHECKER_2026-09-09_ROUND1_RAW.md` (with auditor verification notes on the Executioner's citations)
- **Appendix B — Round 2, all 8 role outputs verbatim:** `Docs/exploration/WOBS_AGENCY_BRANDED_CHECKER_2026-09-09_ROUND2_RAW.md` (with auditor verification notes, including the failed "Not stored · Session only" citation)

This file (Parts 0–3) is the distilled, decision-grade layer; the appendices are the preserved raw room.

### Part 3.1 — Owner ruling on the "shipped promise" (2026-09-09)

Pranay (on the Executioner's failed citation): *"its not launched so it can be changed… whatever makes us better, makes money for us stays."*

Ruling adopted: **nothing pre-launch is binding** — UI, copy, consent framing, scoring, and "promises" are all freely changeable; the filter for what stays is *does it make us better, does it make money*. The corpus is not contract-blocked (the "Not stored · Not shared · Session only" promise the Executioner cited never existed — failed verification, see Appendix B post-script). Consent UX will be redesigned around the value loop (e.g. "Save this brief so an agency can fix these 3 things") rather than around compliance language. The only pre-exposure obligations retained: retention policy (EX-02) and working erasure (FT-G2) must do what the final copy says, because those are the one unrecoverable trust break once real users exist.

### Part 3.2 — FINAL BUILD DIRECTIVE (owner, 2026-09-09): "we build it" — no Ravi gate, dream shelf merged into the build

Pranay: *"we build it, i am not sure if we will get ravi to meet … so the dream shelf or whatever has to be built now."*

Consequences adopted:
1. **Nothing gates on Ravi meetings.** Ravi is "first receiver whenever available," not a sequencing gate. The receiver-side acceptance metric is replaced (for now) by **demand capture**: the marketplace interaction launches at ANY supply level — matched-choice when agencies exist, consented waitlist/capture when they don't ("no matched agency for your dates yet — we'll send your brief when one is"). Captured demand becomes the lead pool that recruits supply.
2. **Dream shelf, split by what "now" means:**
   - **Pulled into build now (structural, cheap today, expensive to retrofit):** structured findings as objects (not prose strings) — the Atlas/API substrate; content-addressed report artifacts (Verify-as-API substrate — the run output becomes an addressable object); server-sealed funnel metrics (completed checks / pins per check / route-intent clicks); Ghost Hotel Test (entity-existence, v1 = advisory findings only); consent redesign tied to the value loop; source attribution as a declare-radio field from day one.
   - **Built when data exists (the product ships the generator, publishing waits for N):** Failure-Mode Atlas v0 publication (needs real corpus volume; generator built with the structured findings).
   - **Built when the loop closes (needs multiple parties, not just code):** Warranty Layer / inter-agency acceptance ledger / continuous re-verification subscription (scheduler is Phase 3; the paid tier around it waits for exposure).
3. **Phased build order (each phase = shippable units, tests green per phase):**
   - **P1 — The Verifier:** Ghost Hotel entity-existence service (v1 advisory), findings-first Manifest page (provenance stamp, pins, Disagree, clean-report badge + re-check date, score demoted to chip), server-sealed metrics, consent redesign + retention line + disclaimer, keep one ingestion format solid (paste; upload stays as-is).
   - **P2 — The Marketplace interaction:** matched-choice presentation (works at any supply), demand-capture waitlist, user-owned brief via capability tokens ("take it to any agent, or pick from ours"), in-platform first contact (Cold Open rule: first message = free partial fix, no calls).
   - **P3 — The Compounding layer:** source-attribution reports, Atlas generator v0, re-verification scheduler (perishable plans), Verify-as-API (headless, content-addressed).
4. **Sequencing note:** P1 does not wait for the uncommitted tree decision or the full-suite run, but those remain pre-conditions for *exposure*, not for building. Wave A P0/P1s continue in parallel lanes as real work — the checker build does not displace them; it adds a lane.

### Part 3.3 — Marketplace routing refined: relevance-matched choice + sponsored-slot policy (owner, 2026-09-09)

Pranay: matching may be based on *types of customers served, places covered, services*, etc., limiting user choices to the most relevant — with a possible sponsored vendor later.

Adopted design:
- **Match dimensions = brief needs × agency profile.** Brief side (already extracted): destination/dates, traveler-composition flags, finding categories needing a fixer, locale. Agency side (new structured profile fields — add in P2 schema now, avoid backfill later): places covered, customer types served, services offered, languages, response SLA.
- **Capped matched set (top 2–3)** shown in the report close; score = overlap. Capping = no choice paralysis, agency scarcity (prices monetization later), and every shown match is explainable ("covers Kerala + families + visa help").
- **User-owned brief stays**: "take it to any agent, or pick from matched agencies" (EX-04 tokens) — marketplace is the convenient default, never a gate.
- **Sponsored vendor (later, sequenced last):** clearly labeled + separate slot; must pass the same relevance floor for that brief; never displaces the top organic match; only shown when organic supply is thin. Monetization sequence: free matched-choice → lead fees/subscriptions on acceptance data → sponsored placement once agencies compete for visibility.
- **Compounding:** acceptance data (SLA response, fix accepted) becomes the earned ranking signal — relevance improves with use, same flywheel as the Failure-Mode Atlas.
- Honesty guardrails apply unchanged: no invented ratings/badges (post-testimonials-removal rule); vetting criteria displayed must be real and measured.

### Part 3.3-A — Routing-mechanism decision record (full option analysis; EXPLORATION §44 + DOCUMENTATION §8/§61)

**Date:** 2026-09-09 · **Owner:** Pranay · **Status:** accepted (matched choice + BYO brief), with reopen triggers below.
**Context:** The rooms' "Ravi as receiver #1 / one routed handoff" was challenged by the owner: *"we dont route to one, we just give them the marketplace? or is there another way to do that part?"* Analysis of the three distinct mechanisms inside "give them the marketplace":

**Option 1 — Single routing** (tool picks one agency, hands over the brief).
- Pro: clean measurement (acceptance trivially computable); no marketplace UI before supply exists.
- Con as product: Waypoint becomes the gatekeeper — the user never chose ("why did you give MY plan to THIS agency?" reads as a referral racket); concentrates dependency on one agency's responsiveness; abandons the Whisperer finding that choice itself is the trust mechanism.
- **Disposition: deferred as pilot-era measurement simplification; not the product.** Reopen trigger: if supply is exactly one agency AND demand-capture waitlist fails to recruit #2, single-routing returns as the only honest interaction.

**Option 2 — Pure marketplace/directory** (report ends with "here are vetted agencies — browse").
- Pro: maximum user agency; supply scales without matchmaking; no gatekeeper.
- Con: converts diagnostic-attached leads into Yelp (directory listings worth pennies vs warm semi-exclusive briefs agencies pay for); choice paralysis for an anxious one-time user; **breaks measurement** — external contact makes routed-lead acceptance untrackable; coldest cold-start (3-agency directory looks abandoned).
- **Disposition: rejected.** Reopen condition: only if the business model shifts to listing-subscription revenue AND supply density makes browsing real (≥10 agencies + traffic). Evidence that would reopen: directory-style competitors demonstrably monetizing at our scale.
- Doctrine note (EXPLORATION §13): the rejection is not "directories fail everywhere" — it's "directory economics contradict the diagnostic-attached-lead economics this thesis depends on."

**Option 3 — Matched choice (SELECTED): marketplace as the interaction, not a directory.** Report's findings define matching criteria; close presents the top 2–3 matched agencies; user picks who receives the brief; first contact in-product (Cold Open rule: first message = free partial fix of a flagged day, never a call). Owner refinement (Part 3.3): matching dimensions = brief needs × structured agency profile (places covered, customer types served, services, languages, response SLA); sponsored slot later, labeled, relevance-floored, never displacing organic #1.
- Rationale: keeps user agency (no gatekeeper), agencies receive consent-warmed qualified briefs, platform-mediated contact preserves the acceptance north star, matched-set framing survives cold start at any supply level.
- **BYO-brief escape hatch (EX-04 tokens):** "Take this brief to any agent you trust — or pick from our matched agencies." Serves the used-AI-to-avoid-agencies segment; marketplace is the convenient default, not a toll booth.

**Hypotheses in falsifiable form (EXPLORATION §39–40):**
- **H-R1:** Because matched choice preserves user agency while keeping first contact platform-mediated, we believe route-pick conversion and acceptance are both measurable without trap-feel. Weakened/falsified by: users reaching the close but route-pick rate <~5% (trust framing failure), or picked agencies accepting <30% (supply-quality failure). Next discriminating check: first 100 exposed reports.
- **H-R2:** Because the brief is user-owned (capability token), we believe BYO-agency exports widen adoption without cannibalizing routing. Falsified by: BYO exports dominating while marketplace picks → 0 (marketplace premise dead; the checker remains valuable as pure verifier — a survivable outcome).

**Honest constraints carried forward:** cold-start optics ("matched to your plan" at any supply; never "browse our directory" while thin) · honesty rules (real, visible vetting criteria; no invented ratings — post-testimonials rule) · zero-findings reports get no marketplace (clean-report path = trust engine: badge + re-check date).

**Doctrine layering note (DOCUMENTATION §54/§56):** this Part is the canonical decision record; the chat discussion it extracts from is preserved verbatim in the session and summarized in Part 0; raw brainstorm transcripts live separately in Appendices A/B. Distillation must not silently change semantics — where wording matters, the owner's messages are quoted verbatim in Part 0.

### Part 3.4 — BUILD LOG: "do all" executed (2026-09-09)

**P1 — The Verifier (complete):**
- Ghost Hotel Test wired into the pipeline: `finalize_result_with_live_checker(build_entity_checks_fn=…)` attaches `public_checker_entity_checks` (advisory, fail-open, cap 3/run) to packet+validation; destination reuse via new public `live_checks.extract_destination()`.
- Server-sealed funnel (Gate 0): `check_completed` event added to the store schema (allowlist + required props `input_mode`/`finding_count`/`execution_ms`), emitted only by `public_checker_service` after trip persistence; **client `/events` endpoint rejects it 403** — the completion count cannot be client-poisoned. Existing server-side `intake_started`/`first_credible_finding_shown` confirmed as the sealed attempt/finding counters.
- Manifest page rework: findings-first ("What your plan is missing" above the header grid), Provenance bar, score dial demoted to 56px "Health check" chip, per-finding "Looks fine" dispute (UI-honest: local-only, no telemetry until server-side escrow), entity-check advisory cards, consent copy made truthful (no "future training" claim), EX-05 disclaimer mounted on result view + upload footer.

**P2 — The Marketplace interaction (complete):**
- `spine_api/services/agency_marketplace.py`: structured profiles (places/customer-types/services/languages/SLA), scored-overlap matching (capped top-3, explainable reasons), demand-capture lead store (routed vs waitlist at any supply), contact validation.
- Endpoints: `POST /api/public-checker/matches` + `POST /api/public-checker/route-request` (public prefixes, kill-switched, 12/min + 6/min, consent required 422, trip-id paths stay auth-protected — no FT-G2 regression).
- Frontend matched-choice close: `RouteRequestPanel` — "Get these N things fixed" → matched list with reasons + SLA → explicit consent checkbox + contact → sent confirmation; waitlist path when supply is empty; BYO-brief share preserved.

**P3 — Compounding layer (partial by design):**
- DONE: declare-radio attribution (`declared_plan_source`: self/ai/vendor, contract field + intake-event property + trip meta + `PlanSourcePicker` UI, default 'ai'); Failure-Mode Atlas v0 generator (`tools/failure_mode_atlas.py` — source×destination×category aggregation over file-store trips, markdown/json output; publication waits for corpus volume).
- Explicitly deferred (recorded, not lost): continuous re-verification scheduler (needs exposure + retention; client re-audit exists), Verify-as-API formalization (run+GET already machine-callable; content-addressed artifacts wait for exposure), Warranty Layer (needs multi-party acceptance data).

**Evidence:** backend sweep 182 passed (checker stack + middleware + mount-auth + startup invariants + rate limiter + events + analytics); marketplace + sealed-metrics units 33 passed; frontend tsc clean, 46/46 (honesty-sweep extended: disclaimer present ×2, no "future training" claim, score demoted). Ruff clean. **Drift engaged mid-build:** a parallel writer swapped my disclaimer mount with an overclaiming variant ("Your travel advisor reviews every plan") — merged back to the honest EX-05 text.

### Part 3.5 — P3 completion + exploration/discussion records (2026-09-09, "complete it, explore if needs that, discuss if needs that")

**Built now — re-verification v0 (on-demand, read-only):**
- `POST /api/public-checker/re-verify {trip_id}` — recomputes live climate/safety signals + advisory entity checks against the STORED packet; returns `overall_score_preview` + fresh signals + `checked_at`. Read-only by design (no write-path risk; report versioning waits for exposure). Fail-open on provider outage. Kill-switched, 6/min, trip 404-safe.
- The **scheduled** loop remains deferred with its trigger intact: it needs the retention policy live and a background-loop owner; on-demand covers the user value at v0 ("check my plan again before travel").
- 8 tests: fresh-signal preview (score 61→51 after penalty), provider-outage fail-open (stored score unchanged), 404, kill switch.

**Built now — Verify-as-API seed: report fingerprint:**
- `compute_report_fingerprint()` — deterministic findings-only sha256 (`fp_<24hex>`), returned as `report_fingerprint` on every run response and displayed short-form in the Provenance bar. Key-order invariant, changes when findings change, **excludes raw text** (consent-dependent), so it is shareable next to the report. This is the tamper-evidence seed for signed findings; the API-key/public-docs layer is an exposure decision, not a code gap.

**Explored — Warranty Layer (Acceptance Ledger) design record (no code — genuinely blocked on multi-party data):**
- Concept states per lead: `captured → routed → accepted (agency claims) → fixed (agency reports resolution) → paid`. The warranty is the `accepted→fixed` signature: a professional stakes their SLA against the findings.
- What exists: lead records (P2) already carry `status routed|captured` + timestamps — the ledger's first two states are real.
- What's missing (hard blockers, in order): (1) in-product agency response mechanism (Cold Open — P2 follow-up), (2) ≥1 agency actually responding to routed briefs (demand-capture proof), (3) dispute path (Second-Opinion Escrow, P3 follow-up). Build order = strictly sequential; nothing to code today that wouldn't be rewritten.
- Falsifier (EXPLORATION §39): *Because routed briefs arrive pre-diagnosed, we believe agencies will accept ≥30% within SLA. Weakened if pilot agencies accept <10% (diagnostic isn't warm enough) or respond only to high-value trips (selection bias breaks the warranty promise for everyone else).* Next discriminating check: first 10 routed briefs, hand-carried.
- Revisit trigger: first real routed lead (waitlist capture exists).

**Discussed — Verify-as-API formalization (owner decision, exposure-gated):**
- Built: the machine surface exists de facto (POST run + GET report are JSON APIs; fingerprint makes reports verifiable).
- Open decision for later: publishing API docs + issuing API keys turns the checker into third-party infrastructure (LLM vendors calling self-verify — Future Self's leapfrog). That is a **product exposure decision** (auth model, rate economics, abuse posture), gated on the same launch decision as everything else. Not buildable meaningfully pre-exposure; recorded as the standing post-launch option.

**Evidence (this increment):** 8 re-verify/fingerprint tests + 190-test backend sweep + ruff clean + frontend tsc clean 46/46 (fingerprint shown in Provenance bar; route-map + middleware allowlists updated for re-verify).

### Part 3.6 — Completion wave: EX-04 tokens, retention, dispute escrow (2026-09-09, "complete the implementations and the exploration work")

**EX-04 capability tokens (closes AUD-04 — the live-probed anonymous 401 defect):**
- `spine_api/services/public_checker_access.py`: opaque bearer tokens (32-byte urlsafe), **stored hashed** (raw token never persists), bound to one trip, TTL-bounded by retention, revocable; constant-time verification; fail-closed on any mismatch.
- Every run now issues `access_token` + `retention_days` on the response (contract + spine.ts extended).
- Token-authorized routes (middleware-prefixed `/api/public-checker/trip/`, enforced again in-router): `GET trip/{id}`, `GET trip/{id}/export`, `DELETE trip/{id}` (delete cascades artifacts + tokens). The authed agency-scoped routes are untouched.
- Frontend: token captured to sessionStorage on run; report fetch, export, and delete use the token route with `Authorization: Bearer` when present (old paths remain the fallback for authed contexts). The anonymous owner can now actually use "Manage your saved data" — the erasure path is exercisable.

**Retention (D-03 implemented with EX-02 defaults, env-tunable):**
- `PUBLIC_CHECKER_RETENTION_DAYS` (default 90; 0 = disabled) bounds trip rows, tokens, and consent-gated upload artifacts: `sweep_expired_public_checker_trips()` deletes by age, public-checker-source-scoped only, and cascades token revocation. Deliberately **file-store-only v0** — SQL lifecycle belongs to the durable-store endgame (E-G), recorded.
- `.1` event-segment age pruning: `prune_old_event_segments(max_age_days=180)` closes the FT-06/EX-10 age gap (size rotation shipped earlier).
- Invocation: sweep is explicit-invocation/tool-ready (wiring into a background loop waits for the loop-owner decision; automatic startup sweep is an env-toggle away and intentionally default-off).

**Second-Opinion Escrow v0 (dispute path):**
- `POST /api/public-checker/disputes {trip_id, finding_text, verdict}` (public, kill-switched, 6/min) records the client-claimed disagreement with **`verified: false`, `origin: client`** — quarantined honestly: disputes become corpus rows only after server-side confirmation. The frontend "Looks fine" button now posts best-effort (silent fail).

**Exploration completeness (EXPLORATION §59, WOBS):** Covered — engine reality, rule taxonomy, scoring, tenancy, funnel/sealed metrics, marketplace mechanics, matching, disputes, retention, tokens, exposure envelope. Not covered: scheduled re-verification loop (trigger: retention live + loop owner), API-keys layer (trigger: exposure GO), multi-party warranty (trigger: first accepted routed brief). High-value unknowns: B9 demand landscape (Oct 6), D-03 numbers ratification (defaults now live as env), real-traffic conversion. Blind spots: no real-user UX observation yet; non-India market fit unexamined.

**Evidence:** access/retention 11 tests, sealed-metrics 5, marketplace API 7, marketplace units 19, re-verify/fingerprint 8, entity 16, live-checker wiring 10, honesty-sweep suite 46/46 frontend, tsc clean; backend sweep 190; ruff clean after 2 F401 fixes.

### Part 3.7 — Disclaimer sign-off (2026-09-09)

Owner approved the EX-05 disclaimer text **as-is** for both mounts (result view + upload footer). The "pending owner sign-off" label is closed; code comment + EX-05 doc record the approval. Honesty-sweep continues to assert the binding phrase ("not legal, visa, or booking advice") — future wording edits must update the sweep in the same change. Pre-exposure punch-list item 5 of 5 now closed; remaining pre-flip items are mechanical (retention automation wiring, robots/sitemap, host env) and gated only on the exposure-scope choice itself (hold / checker-only GO / GO + spend-test), which remains open.
