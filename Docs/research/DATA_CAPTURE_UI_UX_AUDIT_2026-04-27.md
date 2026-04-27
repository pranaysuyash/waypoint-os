# Data Capture UI/UX Audit — Ravi Singapore Call Scenario

Date: 2026-04-27  
Scope: no code changes; code-grounded audit of how a logged-in agency owner should capture a real inbound call lead in the current app.  
Scenario owner: Ravi, logged-in agency owner.  
Traveler scenario: Pranay called Ravi in late November 2024 about a Singapore family trip around 9-14 February 2025 for two adults, one 1.7-year-old child, and two parents. Traveler wants the itinerary not rushed. Ravi suggested Universal Studios and nature parks, then said he would return with a draft in one or two days.

## Executive Verdict

Current verdict: partially usable, not best-in-class yet.

The current capture UI can preserve the call as freeform input and can run the spine in `discovery` / `normal_intake`, which is the correct stage for this scenario. It is not yet a strong agency-owner data-capture experience because the UI does not guide Ravi through caller relationship, source/provenance, adult/child/elderly composition, year ambiguity, follow-up commitment, or non-rushed pacing as first-class fields.

The right product direction is not to replace the freeform transcript. The freeform transcript should stay as source-of-truth evidence, but the capture surface should add a structured lead intake layer around it: source, caller/contact, relationship context, dates with year clarity, party composition, pace preference, must-consider attractions, constraints, missing info, and promised follow-up due date.

## How Ravi Should Capture It Today

Use the existing workspace intake panel if a trip/lead already exists, or create the lead by running a new workbench/spine run if the app exposes the workbench in the logged-in flow.

Recommended current entry:

- Stage: `Discovery`
- Request Type: `New Request`
- Customer Message: paste the call as close to verbatim as possible, with the caller-facing facts only.
- Agent Notes: record Ravi-only context, assumptions, and next action.
- Trip Details after save/run:
  - Destination: `Singapore`
  - Type: `Family leisure`
  - Party Size: `5`
  - Dates: `around 9-14 Feb 2025; call happened late Nov 2024; Jan/Feb initially mentioned`
  - Budget: unknown

Recommended Customer Message text:

```text
Caller says he got Ravi's number through his wife, who is a colleague of Divya. They are planning a Singapore trip sometime in January or February, with tentative dates around 9-14 February. Traveling party: caller, wife, 1.7-year-old child, and both parents. They want approximately 5 days and do not want the itinerary to be rushed. Interests discussed: Universal Studios and nature parks.
```

Recommended Agent Notes text:

```text
Relationship lead: caller came through Divya's colleague network. Call happened in late November 2024; tentative travel date appears to be 9-14 February 2025. Need confirm exact year/date window, origin city, budget, parents' ages/mobility, child nap/stroller needs, passport/visa readiness, hotel category, and whether Universal Studios is a must-have or optional. Ravi promised to return with a draft in 1-2 days, so follow-up should be due within 48 hours.
```

## Code-Grounded Current-State Evidence

- `frontend/src/components/workspace/panels/IntakePanel.tsx:541-678` renders the active intake surface: trip detail summary, `Customer Message`, `Agent Notes`, `Stage`, and `Request Type`.
- `frontend/src/components/workspace/panels/IntakePanel.tsx:132-171` sends `raw_note`, `owner_note`, `structured_json`, `itinerary_text`, `stage`, `operating_mode`, `strict_leakage`, and `scenario_id` to the spine run.
- `spine_api/server.py:412-436` turns `raw_note`, `owner_note`, `structured_json`, and `itinerary_text` into source envelopes, preserving different source roles.
- `spine_api/server.py:519-601` runs the spine and saves processed output as a trip.
- `frontend/src/components/workspace/panels/IntakePanel.tsx:173-203` saves `customerMessage` and `agentNotes`, and only includes trip detail edits when an edit mode is active.
- `frontend/src/components/workspace/panels/IntakePanel.tsx:253-309` lets operators edit individual destination, type, party, date, and budget fields and logs field-level changes.
- `frontend/src/lib/api-client.ts:256-284` models trip summary fields plus `customerMessage`, `agentNotes`, and `rawInput`; it does not currently model lead source, caller/contact, relationship context, child age detail, parents/mobility detail, itinerary pacing, or follow-up due date as first-class fields.
- `frontend/src/app/api/trips/route.ts:9-47` currently exposes `GET /api/trips`; there is no explicit frontend `POST /api/trips` route for manually creating a lead from a phone call.
- `frontend/src/app/api/trips/[id]/route.ts:38-49` allows patching basic trip fields only; structured scenario capture fields are not patchable today.
- `src/intake/decision.py:253-307` defines discovery minimum viable brief fields as destination, origin, date window, and party size as hard blockers, with budget and preferences as soft blockers.
- `src/intake/decision.py:1816-1829` generates follow-up questions for missing destination, origin, dates, party, budget, purpose, and preferences.

## Scenario Fit Assessment

What the current UI captures well:

- It can preserve the messy real call in a raw text field.
- It separates traveler/customer wording from Ravi's internal notes.
- It has the right early-stage settings: `Discovery` and `New Request`.
- It can edit destination, party size, dates, budget, and trip type after extraction.
- It can run the canonical spine path without creating a duplicate route.

What it captures weakly:

- The relationship source is not first-class: "wife's colleague of Divya" becomes plain text, not a lead-source/provenance field.
- Caller identity and traveler party identity are conflated: the caller is the lead contact, but the traveling party includes wife, child, and parents.
- The 1.7-year-old child is reduced to generic party composition unless the raw text extractor catches child age reliably.
- Parents are not captured as older travelers with mobility/medical constraints unless Ravi writes that explicitly.
- "We do not want it rushed" is a high-value pacing constraint, but the UI does not give it a first-class slot.
- The call date vs travel year ambiguity is not made explicit in the UI. In this scenario, "Jan or Feb" during a November 2024 call should resolve to Jan/Feb 2025, with 9-14 February 2025 as tentative.
- Ravi's promise to revert in one or two days is operationally critical, but there is no visible follow-up due-date control in intake.
- Universal Studios and nature parks are suggested possibilities, not traveler-confirmed must-haves. The UI does not help distinguish `suggested by agent` from `requested by traveler`.

## First-Principles Capture Model

A travel-agency intake UI should preserve four layers separately:

1. Source evidence: what was actually said, by whom, and when.
2. Structured facts: destination, origin, dates, party, budget, trip style, documents, constraints.
3. Operator interpretation: Ravi's assumptions, relationship context, confidence, and next-action commitment.
4. System obligations: follow-up questions, due dates, risk checks, and handoff state.

The current UI has layer 1 and part of layer 2, but layer 3 and layer 4 are mostly text-only or downstream output. That is the main UX gap.

## Recommended Full Capture Flow

For this scenario, the ideal first screen should be an intake workspace, not a blank generic CRM form.

Recommended sections:

- Source
  - Channel: phone call
  - Call date: late November 2024
  - Lead source: warm referral
  - Relationship: caller's wife is a colleague of Divya
  - Owner: Ravi

- Contact and travelers
  - Primary contact: caller
  - Traveling adults: caller, wife, two parents
  - Child: one child, age 1.7 years
  - Unknowns: parents' ages, mobility, documents

- Trip intent
  - Destination: Singapore
  - Date window: 9-14 February 2025 tentative
  - Earlier phrasing: Jan/Feb, clarified by call context
  - Duration: about 5 days
  - Pace: not rushed
  - Candidate activities: Universal Studios, nature parks
  - Budget: missing
  - Origin: missing

- Operational commitment
  - Follow-up promised: draft in 1-2 days
  - Due date: 48 hours from call capture
  - Required next action: prepare draft plus ask missing questions

- Confidence and ambiguity
  - Date year: inferred from November 2024 call context
  - Activities: agent-suggested, not yet traveler-confirmed
  - Parent constraints: unknown, must ask
  - Budget: unknown, must ask

## Prioritized Findings

### P0 — Missing dedicated new-call/new-lead creation path

The app has strong workspace editing once a trip exists, but the visible BFF route inventory only shows `GET /api/trips` and `GET/PATCH /api/trips/[id]`. Manual phone-call capture needs a first-class "New Lead" or "Capture Call" path that creates a trip through the canonical spine pipeline, not through a duplicate route.

Decision: add this later by extending the canonical trip/spine path, not by creating a competing route shape.

### P0 — Follow-up promise is not operationalized

Ravi promised a draft in one or two days. Today that can only live in notes. It should become a due-date/task artifact visible in inbox/workspace and tied to SLA.

Decision: make follow-up commitment structured and visible before this is considered launch-ready for agency owners.

### P1 — Party composition needs adult/child/elderly detail, not just party size

The top-level summary shows `party` as a number. This is inadequate for a toddler-plus-parents Singapore scenario because suitability, pacing, transfers, stroller needs, and parent mobility risks depend on composition.

Decision: keep party size, but add structured traveler composition fields and keep raw transcript as evidence.

### P1 — Date ambiguity should be explicitly resolved with provenance

The scenario contains a real-world temporal trap: the call was in late November 2024, "Jan or Feb" means 2025, and tentative dates are 9-14 February 2025. The UI should show this as an inferred date window with a confirmation state, not silently flatten it.

Decision: add date-window confidence/provenance and a "confirm with traveler" flag.

### P1 — Pace preference should be first-class

"We don't want it rushed" changes itinerary generation. It should not be buried in a transcript, because it affects Universal Studios day selection, rest windows, transfers, and elder/toddler suitability.

Decision: create a `pace_preference` / `trip_pacing` field or equivalent canonical slot.

### P1 — Lead source and relationship context are commercially important

Warm referral through Divya is operationally different from a cold lead. It affects tone, trust, priority, and follow-up urgency. Current UI has no structured source/provenance field.

Decision: add referral/source metadata without leaking unnecessary personal relationship details into traveler-facing output.

### P2 — UI relies on hidden hover edit controls

The trip detail edit affordance is hover-only in display mode. That is inefficient for touch devices and weak for discoverability. It also conflicts with high-throughput call capture where Ravi needs obvious fields and keyboard-first progression.

Decision: keep inline edit for existing workspaces, but add an always-visible capture mode for new calls.

## 11-Dimension Audit

Code: 🟡 Current code supports freeform capture and canonical processing, but lacks first-class structured fields for the scenario.

Operational: ❌ Ravi cannot reliably manage the promised 1-2 day follow-up from the intake UI alone.

User Experience: 🟡 The UI is usable for a technical operator who knows what to paste, but not yet obvious for an agency owner capturing calls in real time.

Logical Consistency: 🟡 Discovery blockers align with missing origin/date/party/budget logic, but date-year inference and source confidence are not surfaced.

Commercial: 🟡 Warm-referral value is captured only in notes, so prioritization and relationship-aware service are not system-visible.

Data Integrity: 🟡 Raw text preserves evidence, but structured fields lose important distinctions such as agent-suggested vs traveler-requested activities.

Quality & Reliability: 🟡 Existing tests cover intake render/actions, but not this call-capture scenario or year ambiguity.

Compliance: 🟡 The app separates customer message and owner notes, but referral names and family details need clear internal/traveler-safe boundaries.

Operational Readiness: ❌ Missing task/due-date handling for Ravi's promised draft.

Critical Path: 🟡 First fix should be lead capture + follow-up commitment, then composition/date/pacing refinement.

Final Verdict: Code path exists for rough capture; feature is not best-solution ready for real agency call intake.

## Implementation Direction For Later

Do not add a duplicate API route or parallel policy stack.

Recommended later implementation sequence:

1. Add a first-class `Capture Call` / `New Lead` UI that writes through the canonical spine/trip flow.
2. Preserve raw transcript and owner notes exactly as source evidence.
3. Add structured lead metadata: source channel, referral source, call date, primary contact, follow-up due date.
4. Add structured traveler composition: adults, child age, parents/elderly indicators, mobility unknowns.
5. Add date-window model with inferred year, confidence, and needs-confirmation state.
6. Add pacing preferences and activity provenance: traveler requested vs agent suggested.
7. Add regression tests for this exact scenario: Singapore, Nov 2024 call, Feb 2025 trip, toddler, parents, non-rushed pace, no budget, follow-up due in 48 hours.

## Adoption Strategy: Make The App Easy To Get Used To

Adoption goal: Ravi and similar agency owners should not need to "learn software" first. The app should fit the way they already work: phone calls, WhatsApp messages, quick notes, promises to follow up, and repeated itinerary drafting.

### In-App Adoption

#### 1. Start from the user's real workflow, not system concepts

The first action should be framed as `Capture a call`, `Paste WhatsApp`, or `Start from email`, not `Run spine` or `Create packet`.

Recommended first-run choices:

- `Capture phone call`
- `Paste WhatsApp chat`
- `Import email`
- `Start from existing itinerary`
- `Try sample family Singapore call`

This maps to the owner's mental model before introducing internal stages like discovery, packet, decision, or strategy.

#### 2. Use a guided capture sheet beside the freeform transcript

Do not remove the raw transcript. Put a short structured sheet next to it:

- Who contacted us?
- How did they get our number?
- Where do they want to go?
- When are they thinking?
- Who is traveling?
- What did they explicitly ask for?
- What did we suggest?
- What did we promise next?

The sheet should be fillable manually, prefilled by extraction, and always traceable back to the original words.

#### 3. Show "what the app understood" immediately

After Ravi pastes the call, the app should show a plain-language understanding before deeper pipeline views:

```text
I understood this as:
Singapore family trip, around 9-14 Feb 2025, 5 travelers, includes toddler and parents, wants relaxed pacing. Missing: origin, budget, parents' mobility, passport/visa status. Follow-up promised in 1-2 days.
```

That teaches the system by giving the operator a correction surface.

#### 4. Make correction the core habit

Every extracted field should have three quick actions:

- Confirm
- Edit
- Mark unknown / ask traveler

This is better than expecting the operator to trust automation or inspect raw JSON.

#### 5. Add "next best question" prompts

For Ravi's scenario, the app should suggest the next call/WhatsApp questions:

- "Which city are you flying from?"
- "What budget range should I keep in mind?"
- "Are the February 9-14 dates fixed?"
- "Any mobility concerns for parents?"
- "Should Universal Studios be included or only considered?"
- "Do you prefer a relaxed schedule with one major activity per day?"

This turns the app into a working assistant instead of a passive form.

#### 6. Use progressive disclosure for advanced concepts

New agency users should not see every spine stage, validation artifact, policy flag, and debug object up front. The first screen should show:

- Lead summary
- Missing info
- Suggested follow-up
- Draft status
- Follow-up due date

Advanced views such as packet, decision, strategy, safety, and raw JSON should remain available but not define the first-use experience.

#### 7. Add role-aware modes

Different users need different first screens:

- Owner mode: lead value, risk, follow-up commitments, draft approval.
- Junior agent mode: step-by-step questions, coaching, do/don't guidance.
- Operations mode: SLA, assignments, blocked trips, overdue promises.
- Expert mode: packet/decision/debug detail.

Ravi as owner should see "what do I need to do next for this client?" before implementation details.

#### 8. Turn empty states into practice states

Empty inbox/workspace states should offer:

- Capture your first call
- Paste a WhatsApp chat
- Try the Singapore family scenario
- Watch a 90-second walkthrough

The sample should be realistic and editable, not a canned demo that hides complexity.

#### 9. Add habit loops

The app should reward the operational habit, not vanity activity:

- "Follow-up due tomorrow"
- "3 missing fields before quote"
- "Draft ready for review"
- "Traveler-safe response generated"
- "This trip is ready to send"

This makes the app become the daily work queue.

#### 10. Build trust with provenance

Every important conclusion should answer: "Where did this come from?"

Examples:

- Date inferred from call context.
- Toddler age extracted from "1.7 year old kid".
- Universal Studios was agent-suggested, not traveler-requested.
- "Not rushed" came directly from traveler preference.

This helps Ravi correct the system without feeling like the app is making unexplained decisions.

### Outside-App Adoption

#### 1. WhatsApp-first intake bridge

Many agencies already live in WhatsApp. Adoption improves if Ravi can forward or paste a WhatsApp conversation into the app and get the same structured capture result.

Later path:

- Forward message to a business number.
- App creates/updates a lead.
- App replies internally with missing fields and suggested response.
- Ravi approves before anything traveler-facing is sent.

#### 2. Phone-call recap workflow

After a call, Ravi should be able to dictate or type a quick recap:

```text
Singapore family trip, Feb 9-14, 5 pax, toddler plus parents, relaxed pace, I promised draft in two days.
```

The app should turn that into a structured lead with a due date.

#### 3. Email import

For longer itinerary requests, the app should accept forwarded emails or copied email threads and preserve sender/date context.

Important: imported content should preserve provenance and not overwrite manually confirmed fields without review.

#### 4. Calendar/task integration

The 1-2 day follow-up promise should appear where Ravi already checks work:

- in-app task
- email reminder
- calendar/task integration later
- daily digest of promised follow-ups

The product should become a reliability layer for promises made during sales calls.

#### 5. Templates for common agency conversations

Useful templates:

- Family trip with toddler
- Parents/senior travelers
- Honeymoon
- Visa-sensitive international trip
- Budget unclear
- Warm referral
- Corporate trip
- Cancellation/emergency

Templates should prefill the right capture checklist, not force a rigid form.

#### 6. Founder/owner onboarding package

Outside the app, onboarding should be concrete:

- "Bring one real call or WhatsApp chat."
- "Paste it in."
- "Confirm what the app understood."
- "Send yourself the follow-up checklist."
- "Draft the first response."

This is stronger than a generic product tour because it creates value with the owner's own data.

#### 7. Lightweight training assets

Recommended assets:

- 90-second "capture your first lead" video.
- One-page call-capture cheat sheet.
- Three realistic sample calls with expected output.
- WhatsApp message examples.
- "What to put in Customer Message vs Agent Notes" guide.

Keep these accessible from the intake screen and onboarding emails.

#### 8. Agency rollout rhythm

For a small agency:

1. Owner uses it for 5 real leads.
2. Owner defines preferred capture style.
3. Junior agent shadows those examples.
4. Junior agent captures new leads with app coaching.
5. Owner reviews only blocked/high-value trips.

This avoids forcing the whole team to change behavior at once.

### Product Principles For Adoption

- Teach by doing, not by manuals.
- Preserve raw evidence before asking for structure.
- Make the next action obvious.
- Prefer correction over configuration.
- Show why the app thinks something.
- Never make operators learn internal architecture before getting value.
- Integrate with phone, WhatsApp, email, and reminders because that is where travel-agency work already happens.
- Make every first-session success use a real client scenario, not an artificial demo.

### Highest-Leverage Adoption Feature

The single best next adoption feature is a `Capture Call` flow with:

- transcript/recap paste area,
- AI-prefilled structured sheet,
- confirm/edit/ask controls,
- visible follow-up due date,
- suggested WhatsApp follow-up,
- source/provenance on extracted facts,
- one-click creation of the trip in the canonical spine/trip path.

That would make Ravi's real Singapore call feel natural inside the app and would also teach him how to use the system through the work he already does.

## Incremental UI Change Size And Migration Shape

This should not be implemented as a replacement of the existing intake UI. The current workspace intake panel already has useful fields, persistence paths, stage/mode selection, save, process, ready-gate behavior, and downstream packet/decision/strategy views. Replacing it would increase risk and retrain existing users unnecessarily.

The better product shape is:

```text
New prominent entry CTAs
  -> lightweight capture modal/page
  -> prefilled current intake UI
  -> operator confirms/edits
  -> existing Process Trip / workspace flow continues
```

In other words: keep the current UI as the canonical working surface, but add easier doors into it.

### Recommended Entry CTAs

Place a large, obvious CTA group in the empty inbox/workspace state, the dashboard quick actions area, and the intake page header:

- `Capture Phone Call`
- `Paste WhatsApp Chat`
- `Import Email`
- `Start From Itinerary`
- `Try Sample Singapore Family Trip`

Each CTA should create or open a capture assistant that asks for the minimum channel-specific information, then populates the existing intake fields.

### How Each CTA Should Populate Current UI

`Capture Phone Call`:

- Opens a paste/dictate recap field.
- Optional fields: call date, caller name, source/referral, promised follow-up.
- Populates `Customer Message` with traveler-facing facts.
- Populates `Agent Notes` with source, assumptions, follow-up promise, internal context.
- Prefills trip summary fields where confidence is high: destination, date window, party size, type.

`Paste WhatsApp Chat`:

- Accepts copied chat text.
- Preserves raw transcript as evidence.
- Detects participants and separates customer statements from agency/owner statements where possible.
- Prefills the current intake fields, but requires confirmation before overwriting existing confirmed fields.

`Import Email`:

- Accepts pasted email or later Gmail/IMAP import.
- Preserves sender/date/subject provenance.
- Extracts trip facts into the same intake fields.
- Keeps email thread context in notes/source metadata.

`Start From Itinerary`:

- Accepts a rough itinerary, PDF text, or copied proposal.
- Populates `itinerary_text` and extracts destination/date/party/budget where possible.
- Routes to audit/review if the input is an existing plan rather than a new request.

`Try Sample Singapore Family Trip`:

- Loads the Ravi/Singapore scenario as a safe practice lead.
- Lets the operator edit it like a real lead.
- Shows the expected missing fields and follow-up checklist.

### UI Change Size

Small UI change:

- Add CTA group and helper examples.
- No new data model.
- CTAs only insert text into current `Customer Message` and `Agent Notes`.
- Good for onboarding, but not enough for operational reliability.

Medium UI change:

- Add a capture assistant modal/page.
- Channel-specific prompts.
- Prefill trip summary fields and current textareas.
- Add extraction review: confirm/edit/ask.
- Add follow-up due date as structured UI state if backend supports it, or a clearly marked notes fallback if not yet supported.

Large UI/product change:

- Add first-class lead source, contact, traveler composition, activity provenance, date-confidence, pace preference, and follow-up-task fields.
- Add external imports and reminders.
- Add deduplication/thread matching.
- Add audit/provenance view for every extracted fact.
- Add channel integrations and approval controls.

The recommended first implementation is the medium change. It gives the agency a much easier front door while preserving the existing intake/workspace architecture.

## Outside-App Channels And Integration Sizing

Outside-app capture should be treated as additional entry channels into the same canonical intake flow, not separate products.

### Chatbot / Assistant Link

Agency-facing assistant link:

- Ravi opens a private link or internal assistant.
- He types or dictates the call recap.
- Assistant returns the structured intake draft.
- One click opens the app with current intake fields prefilled.

This is useful early because it requires less integration complexity than WhatsApp Business and keeps approval internal.

Traveler-facing chatbot:

- Should come later.
- It needs stricter tone controls, consent, privacy boundaries, and escalation rules.
- It must not send or promise anything without owner-approved policy.

### Telegram

Telegram is technically easier than WhatsApp for a first bot-style capture flow:

- Agency forwards a message or sends a recap to the bot.
- Bot replies with extracted facts and missing questions.
- Bot links to the app's prefilled intake screen.

Best use: internal agency capture and reminders, not traveler-facing automation at first.

### WhatsApp

WhatsApp is commercially important because agencies already work there, but implementation is heavier:

- WhatsApp Business API setup.
- Message templates and approval constraints.
- Contact identity matching.
- Thread grouping.
- Consent and data retention rules.
- Human approval before traveler-facing replies.

Best first WhatsApp version: paste/forward-style ingestion or internal WhatsApp-to-app bridge. Full two-way traveler automation should wait until the internal capture/review flow is solid.

### Email

Email is a strong early integration:

- Easier provenance: sender, subject, timestamp, thread.
- Good for longer itinerary requests.
- Gmail import can populate the same capture assistant.
- Lower messaging-policy friction than WhatsApp.

Best first email version: paste/import email content into the capture assistant, then later Gmail connector/thread import.

### Calendar / Tasks

Follow-up promises should leave the app:

- daily digest of due follow-ups,
- calendar/task reminder,
- email reminder,
- later WhatsApp/Telegram internal reminder.

This matters because the app becomes useful even when Ravi is not actively staring at it.

## Current Decision

Decision: preserve the current intake/workspace UI as the canonical work surface, and add prominent channel-specific CTAs that populate it.

Do not build a separate intake stack. Do not create duplicate API routes. Do not make external channels canonical before the in-app capture review is reliable.

The adoption-friendly architecture is:

```text
Phone / WhatsApp / Email / Itinerary / Sample Scenario
  -> Capture Assistant
  -> Extracted Facts Review
  -> Existing IntakePanel fields and workspace flow
  -> Existing spine run and downstream panels
```

## Product Recommendation

My recommendation is to make the in-app `Capture Assistant` the center of gravity, and treat every outside channel as a feeder into that assistant.

I would not start by building WhatsApp, Telegram, email, and chatbot integrations in parallel. That creates many entry points before the product has one excellent correction/review experience. The hard product problem is not receiving text; it is turning messy text into trusted, editable, provenance-backed trip facts and follow-up obligations. That must be excellent inside the app first.

Recommended sequencing:

1. Build the in-app capture assistant with the five entry CTAs.
2. Make the assistant populate the current intake UI rather than replacing it.
3. Add source/provenance and extracted-fact confirmation.
4. Add follow-up due date/task handling.
5. Add email import next.
6. Add Telegram/internal bot after that if a lightweight mobile capture path is needed.
7. Add WhatsApp Business only after the internal approval and traveler-safe response path is solid.

### Why This Sequence

The in-app assistant gives immediate adoption value without integration risk. Ravi can paste the Singapore call today-style, see what the app understood, correct it, and continue through the existing workspace. That makes the app easier to learn because the first experience is his own work, not a tutorial.

Email should come before WhatsApp because email carries cleaner provenance: sender, subject, timestamp, thread, and long-form request context. It is also less constrained by business messaging policy.

Telegram is a good internal operations tool, but less commercially necessary for Indian travel-agency customer conversations than WhatsApp. I would use it only if the team wants a fast internal bot for owner/junior-agent capture and reminders.

WhatsApp matters most commercially, but it should not be the first integration. A weak WhatsApp integration will create trust problems quickly: duplicated leads, unclear consent, wrong thread matching, accidental traveler-facing replies, and noisy notifications. The app needs a strong human-review layer before WhatsApp becomes two-way.

Traveler-facing chatbot should be last. An agency-facing assistant is useful early; a traveler-facing chatbot changes the product's promise and risk profile. It needs tone governance, escalation rules, consent, safety boundaries, and clear owner approval policies.

### What I Would Build First

I would build this first:

```text
Dashboard / Inbox big CTA:
  Capture New Lead

Capture New Lead screen:
  1. Choose source: Phone call, WhatsApp paste, Email paste, Itinerary, Sample
  2. Paste/dictate raw input
  3. App extracts facts into a review sheet
  4. Operator confirms/edits/marks unknown
  5. App populates current IntakePanel
  6. Operator clicks Process Trip
```

This is a meaningful UI change, but it is not a rewrite. It is an adoption layer in front of the existing workflow.

### What I Would Avoid First

- Do not build a separate CRM-style lead form that bypasses the current intake/spine flow.
- Do not build a WhatsApp bot that sends traveler-facing replies before operator approval is mature.
- Do not make users choose between "old intake" and "new intake"; that creates product confusion.
- Do not hide the raw transcript after extraction; operators need evidence to trust corrections.
- Do not expose packet/decision/debug concepts as the first-run experience.
- Do not make external integrations write directly into final trip facts without a review step.

### Final Product Shape

The best version is not "form vs chatbot." It is a source-aware capture layer:

- Forms for confirmed facts.
- Freeform transcript for evidence.
- Assistant for extraction and missing questions.
- Tasks/reminders for promises.
- Existing workspace for execution.
- Integrations only as ways to bring source material into the same review flow.

That gives agencies a gentle path into the product: they start by pasting what they already have, then gradually learn to trust and correct the system.

## No-Code Audit Status

This audit intentionally makes no code changes. It records the evidence, current capture guidance, and the product/architecture direction for a later implementation pass.
