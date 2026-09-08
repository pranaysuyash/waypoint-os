# Wide-Open Brainstorm — Agency-Branded Checker (Full-B) (2026-09-09)

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
