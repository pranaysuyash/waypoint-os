# Travel Agency Customer Live Simulation - 2026-06-17

## Scenario

Persona: traveler / customer

Simulation goal:

- arrive cold on the public checker
- understand the offer without help
- paste a realistic itinerary
- get a useful result
- decide whether this feels trustworthy and worth sharing or using further

Verification context:

- frontend: `http://localhost:3100`
- backend: `http://localhost:8000`
- live browser simulation run against the repo-started app
- no account used
- anonymous traveler flow only

Live simulation path:

1. Open `/itinerary-checker`
2. Read the public landing experience
3. Switch to `Paste itinerary`
4. Paste a realistic Singapore itinerary
5. Submit via `Score My Itinerary`
6. Review the result state
7. Check post-result actions exposed to a traveler

Sample itinerary used:

```text
Day 1: Fly Mumbai to Singapore on Singapore Airlines, arrive 7:10 PM, taxi to Marina Bay Sands.
Day 2: Gardens by the Bay at 9 AM, Marina Bay area, evening river cruise.
Day 3: Sentosa full day with cable car and aquarium.
Day 4: Universal Studios Singapore.
Day 5: Free morning, shopping on Orchard Road, evening flight back to Mumbai.
Travelers: couple with one parent aged 68. Budget: about USD 4500 total. Concern: not too rushed, easy walking, low friction transfers.
```

## What Happened

### Stage 1: Land on the public checker

What I am trying to do:

- figure out what this tool is
- decide whether it is worth trying

What happened:

- the page loaded cleanly
- the value proposition was immediately understandable
- the tool clearly signaled:
  - free
  - no sign-up required
  - useful for messy travel inputs
  - shareable with an agent later

What felt good:

- strong top-of-funnel clarity
- low-friction entry
- the page looks productized, not like a rough internal tool
- trust signals are visible early

What felt weak:

- the page is strong at promise and framing, but at this stage the customer still has to trust that the back half of the experience is equally strong

### Stage 2: Paste and submit an itinerary

What I am trying to do:

- avoid file upload hassle
- paste my plan directly
- get feedback quickly

What happened:

- `Paste itinerary` was easy to find
- the textarea accepted the itinerary cleanly
- `Score My Itinerary` submitted successfully
- the live API call to `/api/public-checker/run` returned `200`

What felt good:

- the core input path is simple
- copy-paste is the right default for a customer
- no sign-up barrier before submission is a major strength

What felt weak:

- none at the submit step itself; this part is smooth

### Stage 3: Review the result

What I am trying to do:

- understand whether the trip looks okay
- see specific issues
- get a summary I can act on

What happened:

- the result view rendered
- the experience shifted into a scored report state
- the report showed:
  - score `42/100`
  - `Live review`
  - `Live analysis: STOP_NEEDS_REVIEW`
  - `1 hard blockers`
- the visible extracted summary stayed thin:
  - `STATUS: Waiting for parsed itinerary details`
- the main visible finding was:
  - `CRITICAL`
  - `extraction_quality`

What felt good:

- the app does move from landing page to a real result state
- the result has a clear headline score and severity framing
- it does not feel like a fake demo after submit

What felt weak:

- the result feels less helpful than the landing page promises
- `Waiting for parsed itinerary details` is not a satisfying outcome for a customer who just pasted a full trip
- `extraction_quality` reads like an internal/system problem, not a traveler-facing insight
- the result is structurally alive, but emotionally it feels under-explained

### Stage 4: Try to use the result

What I am trying to do:

- export the report
- manage my data
- decide whether I can trust the controls I am seeing

What happened:

- the result screen exposed:
  - `Export JSON`
  - `Delete saved data`
  - `Share report`
  - advisor-revision buttons
- but the anonymous traveler flow hit auth walls on management actions:
  - `GET /api/public-checker/{tripId}/export` returned `401 Not authenticated`
  - `DELETE /api/public-checker/{tripId}` returned `401 Not authenticated`

What felt good:

- the tool clearly wants to support post-result actions

What felt weak:

- customer-visible controls appear available but are not actually usable in the anonymous flow
- that creates a trust problem
- a traveler should not have to discover via failure that visible controls require auth

## Good Stuff

- excellent public entry experience
- strong value proposition
- no-sign-up path is real
- paste-first flow is simple and customer-friendly
- submit works live
- result screen does exist and is not a dead end

## Gaps

- the first live result is weaker than the marketing promise
- extracted summary quality is not yet strong enough for a pasted itinerary like this one
- `extraction_quality` is not good customer-facing language
- `Waiting for parsed itinerary details` feels unfinished
- result-management controls are exposed even though export and delete return `401` in the anonymous flow

## Time Savers

- as a traveler, I can understand the tool in seconds
- as a traveler, I can paste an itinerary instead of formatting a document
- as a traveler, I do not have to create an account before trying it

## Time Wasters

- as a traveler, getting a score without a rich extracted summary makes me work harder to understand what the system really saw
- as a traveler, seeing `extraction_quality` forces me to interpret system language instead of trip advice
- as a traveler, clicking into report-management actions that are not actually available to me would waste trust and time

## Workarounds

- use the checker as an early signal tool, not yet as a fully self-sufficient trip brief
- treat the score and blocker count as directional until the extracted summary becomes more consistently rich
- if the goal is advisor collaboration, treat `Share report` as the safer visible action than export/delete until the anonymous permissions story is clarified

## Journey Map

### Arrive

- Goal: decide whether to try the checker
- Outcome: succeeds
- Emotional state: curious -> reassured

### Paste

- Goal: get fast analysis without setup
- Outcome: succeeds
- Emotional state: reassured -> engaged

### Review result

- Goal: understand the trip and issues clearly
- Outcome: partial success
- Emotional state: engaged -> uncertain

### Use result

- Goal: export, manage, or share confidently
- Outcome: partial failure
- Emotional state: uncertain -> skeptical

## Bottom Line

This customer flow is strong at the top and weaker at the bottom.

What works:

- the public landing page
- the no-sign-up promise
- the paste-and-submit flow
- the existence of a real scored result

What does not yet fully work from a customer point of view:

- the result depth and clarity after submission
- the traveler-facing readability of the first critical finding
- the trustworthiness of visible manage/export controls in an anonymous session

Clean customer verdict:

- acquisition experience: strong
- submission experience: strong
- first-result usefulness: mixed
- post-result trust/controls: weak

The biggest customer-facing opportunity is not “make the page prettier.” It is:

- make the first result feel genuinely useful
- hide or reframe actions the anonymous traveler cannot actually use
- translate system-quality issues into traveler-helpful language
