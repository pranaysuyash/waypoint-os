# Itinerary finding, recheck, and learning plan

November 24, 2026. Builds on the [report-first implementation](2026-11-21-gtm-checker-report-first.md) and [post-verification council](2026-11-21-gtm-checker-live-backend-verification.md#november-24-post-verification-ui-and-product-council).

## Free traveler experience

The traveler brings one itinerary. The checker should make the relationship between an itinerary detail, its consequence, and a specific action visible. A good first result lets a traveler recognize the trip as theirs and understand one thing they can do immediately, including providing a missing fact that controls the check. A report earns distribution when the traveler can use it independently. Advisor referrals and the public learning loop have separate success measures.

| Situation | First visual and action |
|---|---|
| Known material issue | An affected leg or itinerary excerpt alongside one finding, impact, and an action. Expand source and assumptions when the underlying evidence exists. |
| Missing or ambiguous input | The actual question alongside the recognized facts and an inline edit. Keep useful partial results. |
| Successful recheck | Update extracted facts and findings from the latest response and show the changed fact close to the next action. A follow-on prototype should compare the affected finding before and after when stable finding IDs exist. |
| Source unavailable or no issue flagged | Explain the coverage and any verification left to the traveler. Show lookup-time weather separately from conditions applicable to travel dates. |

Connection timelines, conflicting itinerary lines, and property evidence rows are candidate visuals. The condition for shipping one is a backend finding with the relevant submitted fields, applicability, source, and unknowns. A connection timeline needs exact leg times and date basis, ticket and baggage facts where relevant, and a clear textual equivalent. Keep the illustration on the intake surface and the live view source-bound.

### Implemented now

- Puts the first concrete backend clarification or finding in the report header and shows recognizable extracted destination, dates and traveler count there when present.
- Gives the traveler an inline editor populated with their submitted text and reuses the existing checker. It preserves the prior report and edited text on request failure. The original input is not retained through the recheck opt-in path. Booking stage is preserved on the revised request.
- Replaces the warning's “Looks fine” label with explicit feedback wording and describes the branded agency as linked to the checker. Listed coverage is profile information.
- A future field-level editor should preserve the original text separately, support uncertain interpretations, and recheck only affected findings when the backend has stable finding identities. Current UI edits and submits the itinerary text as a whole.

## Learning loop and OpenAI credits

First train or improve city-role extraction, where destination, origin, connection, venue, and unknown must remain distinct. Train only after a useful benchmark exists. A model may propose values with source spans. The product pipeline should verify spans, validate fields, control decisions and provider lookups, and abstain when evidence is inadequate. [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

Use a permissioned, minimal corpus of excerpts with reviewed fact corrections. Contribution should be separate from saving a report and sending an advisor request. A proposed after-report contribution preview should show the exact redacted excerpt, the initial parse and the traveler correction, and explain the intended use. Keep raw uploads and contact or booking identifiers out of the evaluation corpus. Treat a user correction as a candidate label. Keep a held-out set grouped by itinerary/template family, including place-role ambiguity, local dates, multilingual inputs, and genuinely unknown facts. Use coverage and correction patterns to choose new checks independently of whether a user contacts an agency.

Run `python -m tools.verification.checker_extraction_probe` from the repo root to compare four fictional cases with the current intake destination extractor. Adding `--openai` enables up to four requests to the pinned gpt-4.1-mini snapshot and checks destination/connection roles and exact source spans. The baseline correctly identified Dubai, Kyoto/Osaka, and the unknown case. The overnight example returned Doha where the expected destination was Istanbul. The provider lane returned HTTP 401 `invalid_api_key`; there were no model predictions or measured model usage. This is a smoke probe, not a quality benchmark. A valid project key with model access is required for the provider lane. No traveler data was sent and no model is wired into the checker by this change.

## Acceptance

Observe a traveler checking their own itinerary, locating and correcting a material fact, and explaining the changed or still-unresolved action without prompting. Separately verify a known issue, missing input, true no-flag result, and provider outage. Label synthetic browser recordings as UI evidence. Prove provider coverage, decision usefulness, real-device behavior, and voluntary contribution independently.

## Verification

Desktop (1440 × 900) and mobile emulation (390 × 844) passed the Playwright replay with synthetic checker responses. Assertions cover the first clarification in view, focus and text preservation, failure retaining the previous report and edited draft, and success moving focus to the updated report with the new date visible. The same run exercised first-check failure, malformed results, share cancellation, export, no match, and a synthetic advisor receipt. Backend health returned 200, authenticated metrics returned 401 without credentials, and the foreground checker returned 200. The recorded requests use browser fixtures. Physical devices, customer understanding, and a real provider rerun with this revision remain open.

- [Desktop recording](../evidence/gtm-checker-recheck-2026-11-24/desktop-walkthrough.mp4)
- [Mobile-emulated recording](../evidence/gtm-checker-recheck-2026-11-24/mobile-walkthrough.mp4)
- [First clarification](../evidence/gtm-checker-recheck-2026-11-24/desktop-after-partial.png), [failed recheck with edit preserved](../evidence/gtm-checker-recheck-2026-11-24/mobile-after-recheck-retry.png), [updated report](../evidence/gtm-checker-recheck-2026-11-24/mobile-after-recheck.png)

### Shared credential rerun

After the owner pointed to the Projects-level environment files, explicitly loading the shared OpenAI credential for the probe process produced four successful Responses API calls with `gpt-4.1-mini-2025-04-14`. Earlier project credential failure remains part of the run history. No credential was copied into the project environment or logged. Only the four built-in fictional inputs were submitted.

| Case | Current destination parser | OpenAI destination and connection roles |
|---|---|---|
| Transit and hotel | Correct destination, Dubai | Incorrectly labeled Istanbul as both destination and explicit connection |
| Overnight | Incorrect destination, Doha | Returned both Doha and Istanbul as destinations. Expected Istanbul only |
| Two stays | Correct destinations, Kyoto and Osaka | Correct destinations and Seoul connection |
| Unknown | Correct abstention | Correct abstention |

The parser got 3/4 destination sets right. The model got 2/4 destination sets and 2/4 combined role cases right. The parser's connection roles were outside this probe's baseline. Every model evidence span occurred literally in the synthetic input, yet two role assignments were wrong. Observed usage was 738 tokens (568 input, 170 output), and request latency ranged from 0.84 to 4.05 seconds. The sample is a diagnostic smoke test. Keep the model offline pending role-specific evaluation and a larger held-out set.

### Interactive preview check

The preceding footage is a fixture recording and was premature as a handoff for trying the interactive flow. A subsequent desktop Chrome run submitted a synthetic Singapore itinerary through the local Next.js page and the isolated FastAPI backend, with no request interception. Both submissions returned HTTP 200 and included Open-Meteo evidence. The initial report was blocked for review. In the inline editor, adding November 27–30 and a trip purpose produced a completed run with the new travel window. The decision remained ASK_FOLLOWUP, and the visible heading “Your check needs more details” reflected that partial result. This run verifies live browser submission and recheck, with the preview bound to localhost.

### Overnight route regression

The synthetic Doha-to-Istanbul case exposed two interacting errors. The lodging extractor treated “staying in Istanbul” as a named property and the intake scan masked the city. The destination scan also lacked an origin guard for “Doha 23:55 to Istanbul 01:10”. The updated lodging extractor skips known places after ambiguous “in” cues, and the origin guard recognizes timed directional legs with a known arrival place. This change corrects destination assignment. It does not introduce an origin fact or a transfer-duration verdict.

Both regression tests failed before the change and passed after it (S2). The focused destination, lodging and live-check suites passed 30 tests. All four local extraction probe destination cases now pass. The first live browser replay failed because the isolated backend lacked public geography reference files. After adding only the shipped city datasets and restarting the isolated backend, the same Chrome submission returned HTTP 200, showed Istanbul as the sole destination candidate, and returned no Istanbul lodging finding. The backend reply still required review. No weather source or transfer calculation was observed for this run.

[Live desktop overnight report](../evidence/gtm-checker-overnight-2026-11-24/desktop-real-report.png)

The first corrected live report still asked for departure city. The same timed-leg grammar now supplies Doha as a leading origin fact, and the report header shows it. A third regression reproduced the missing origin before that change. The follow-up browser run through the real local API then showed Doha and Istanbul and stopped asking for the departure city. The report still requires review for other missing details. Final verification includes 31 focused backend tests and a clean TypeScript check. [Live desktop report with both city roles](../evidence/gtm-checker-overnight-2026-11-24/desktop-origin-and-destination.png).

### Rough Indian itinerary smoke test

Submitted one fictional Hinglish Delhi-to-Goa family plan through the local Next.js browser and real FastAPI pipeline without interception. Travel note and selected response fields are in the [observed result](../evidence/gtm-checker-hinglish-2026-11-24/observed-result.json). The [report screenshot](../evidence/gtm-checker-hinglish-2026-11-24/desktop-real-report.png) shows the traveler-facing result.

HTTP 200 returned a blocked report with Delhi, three travelers (two adults and one five-year-old), and a firm INR 35,000 total. The extraction promoted Baga and Old Goa to destination candidates, omitting Goa as the trip destination. Open-Meteo evidence targeted Bagà instead of the intended Goa. The result lacked travel dates altogether despite the explicitly supplied outbound date and overnight arrival. Return date was genuinely undecided. The report did not address the practical hotel question about a 02:25 arrival on December 19 for a December 18 reservation, nor the three-stop day. This is one targeted synthetic-input case, and the report stays unverified for actual booking decisions. Follow-through priority is destination and geocode consistency before expanding provider-backed findings, then partial date retention and overnight hotel arrival guidance.

### Goa itinerary repair and live replay

The unchanged synthetic note was submitted in Chrome on desktop and a mobile-emulated viewport through the actual Next.js and isolated FastAPI services. Both responses returned HTTP 200 and ASK_FOLLOWUP. The UI shows Delhi, Goa, outbound 18 Dec 2026, the sole clarification “Add your return date when you know it,” and a prominent late hotel arrival finding based on the explicit 02:25 next-day arrival and proposed previous-night check-in. The finding recommends confirming after-midnight arrival and room hold with the hotel. The original Bagà weather card is absent. The lookup now reads scoped destination fields, declines ambiguous destination lists and name mismatches, and omits weather for an unscoped Goa state-level place lookup.

The extractor prefers a clear Hinglish trip destination over a later stop list, retains the outbound date without inventing a return, and distinguishes an explicit undecided return from other partial itineraries. The booking advice comes from a deterministic itinerary check. This change does not assess timing between the three sightseeing stops or verify hotel conditions with a provider.

35 focused backend and 11 frontend tests passed. TypeScript and whitespace checks passed. Desktop and mobile-emulated screenshots and selected response evidence were inspected.

[Desktop UI](../evidence/gtm-checker-hinglish-2026-11-24/desktop-fixed-report.png) · [Mobile-emulated UI](../evidence/gtm-checker-hinglish-2026-11-24/mobile-fixed-report.png) · [Response evidence](../evidence/gtm-checker-hinglish-2026-11-24/fixed-result.json)

### Goa same-day pacing

Added a deterministic advisory for the three named stops when the submitted itinerary groups them on one day and Goa is the resolved destination. It asks the traveler to confirm Dudhsagar access and return-to-Collem timing, then budget time for remaining transfers and visits. It points to the [Government of Goa Dudhsagar guide](https://www.goa.gov.in/places/dudhsagar-waterfalls/) for access context. No live travel duration, access slot, or dated feasibility claim is produced.

The exact original synthetic note returned HTTP 200 and ASK_FOLLOWUP in desktop Chrome and the mobile-emulated retry through the real local API. It still showed Goa, the 18 December outbound, one return date clarification, and the hotel arrival finding. The first mobile attempt hit an intermittent isolated file-store privacy guard false positive on a generated UUID and returned 500. The retry passed without changing the note or weakening the guard. The guard issue remains separate. 19 backend and 11 frontend focused tests and TypeScript passed.

[Desktop report](../evidence/gtm-checker-hinglish-2026-11-24/desktop-pacing-report.png) · [Mobile-emulated report](../evidence/gtm-checker-hinglish-2026-11-24/mobile-pacing-report.png) · [Live response and UI text](../evidence/gtm-checker-hinglish-2026-11-24/pacing-result.json)
