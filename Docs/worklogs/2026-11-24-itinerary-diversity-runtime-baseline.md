# Itinerary diversity baseline for the practitioner council

24 November 2026 · Synthetic cases against the local public checker

The existing Goa replay showed the two advisories can reach the traveler and advisor. This baseline asks whether the same pipeline surfaces decision-changing details when the itinerary shape or wording changes. It provides material for the practitioner council to challenge. Its labels are engineering observations based on synthetic inputs.

- [Practitioner case cards](../exploration/ITINERARY_PRACTITIONER_REVIEW_PACKET_2026-11-24.md#the-cases)
- [API replay receipt](../evidence/itinerary-diversity-2026-11-24/public-checker-replay.jsonl)
- [Unchanged retries and blocker spot checks](../evidence/itinerary-diversity-2026-11-24/verification-retries.jsonl)
- [Positive browser control in public and authenticated Workbench](2026-11-24-goa-feasibility-workbench-replay.md)

## Method

Send each base case verbatim to the same local Next.js public checker route used by the browser. For the changed and uncertain variants, append the packet's changed fact using a correction cue, or append the uncertain fact using an explicit cue that the earlier text is unreliable. This tests a first submission containing a correction or conflicting note. It does not exercise the interactive edit and recheck state. Booking times, rates and schedules in the cases are fictional.

The live FastAPI service was running from the isolated Goa replay directory. This pass covers the anonymous HTTP route. It does not measure authenticated Workbench parity on the 13 families, rendered reports, provider accuracy, practitioner agreement, or confirmed booking terms. The receipt records the submitted text, HTTP and decision states, extracted values, structured itinerary advisory list, and any returned follow-up. The header field list verifies response shape. Hard and soft blocker values were omitted by the capture because it read a nested decision object while this endpoint returns them at the top level. Those null columns cannot establish that the service had no blockers.

## Results

The first pass covered **39 distinct submissions across 13 itinerary families**. Of those, 36 returned HTTP 200. The other three returned HTTP 200 when replayed unchanged. Two first attempts failed with HTTP 500 in the isolated file store. The backend log showed two privacy-guard rejections of generated UUID-like identifiers treated as phone numbers. One first attempt returned no HTTP response to the capture client. Its transport cause was unclassified. The harness waited and retried after HTTP 429 and preserved the first terminal outcome in the main receipt.

**All 39 variants, counting the successful retries, returned `STOP_NEEDS_REVIEW`, zero structured itinerary feasibility advisories and no follow-up questions.** Five spot checks captured the top-level blocker fields. Each returned `extraction_quality` as the sole hard blocker. This is evidence about the focused snippets and local configuration. It does not establish that every full trip or supported check ends the same way.

This matters for the public checker and advisor alike. The test cases contain enough detail to name a useful next question in several cases, such as asking which airport the onward flight uses or whether a specific booking has a confirmed late handover. The captured response offers no such question in these cases. Check coverage and extraction quality both need attention. The original Goa note remains a separate positive control for exactly two advisories.

## Initial diagnoses

- **F01 plain-English Goa day.** The positive Hinglish control named Goa and triggered pacing. This English base case chose Old Goa as the destination and emitted no pacing advisory. The current rule requires an exact Goa destination plus a narrow same-day phrase or a day heading in the same clause. A shared day model needs place roles and actual day assignments before it can evaluate transfers or time constraints. The changed-day and undated variants are separate cases for that model.
- **F02 overnight prose.** The base retained Delhi and Goa, lost the departure date, and emitted no overnight advisory. The current rule requires a parsed ISO departure date and a narrow flight/check-in wording pattern. The operator-confirmation question should be computed from local dates on structured transport and accommodation legs when available. The changed check-in date and uncertain arrival day require different calls.

## Additional observations for the council

| Scope | Observed in the captured packet | Question for the practitioner |
| --- | --- | --- |
| F03 hotel package | The changed input mapped “Deposit” to a destination. | What exact booking artifact establishes that payment is irreversible, and who can supply it? |
| F04 Helsinki and F05 London | Helsinki was captured as a destination in the flight-connection cases. Heathrow was captured as the destination for the airport change. The structured advisory list had no connection finding in either case. | Which fields would let the advisor distinguish an airport change, same-airport self-transfer and a protected connection? |
| F06 air–rail | The base split Gare du Nord into destination candidates “Gare” and “Nord” alongside Paris and Brussels. | What is the first station or ticket fact to verify before estimating margin? |
| F07 waitlisted train | The base mapped “Train” to a destination. It had no structured advisory about the linked transfer. | When should the advisor advise protecting or cancelling the separately booked transfer? |
| F08 Vatican Museums | The base retained Rome. It returned no structured finding for the conflict between planned arrival and stated admission time. | When would the reservation document alone support holding up this visit? |
| F09 cruise excursion | The base mapped “Guide” to a destination. It had no structured finding for the gap before all-aboard. | Which clock and product terms establish a usable return margin? |
| F10 accessibility | The base extracted party size and an accessibility priority, while selecting “Van” as destination. The structured advisory list was empty. | What counts as confirmation of the specific vehicle and boarding method? |
| F11 transit | The base captured Mumbai and Mexico City. It had no structured finding addressing the transit question. | What missing traveler and ticket facts are necessary to route this to the right document check? |
| F12 disrupted arrival | The base mapped “Car” to a destination and had no structured advisory about the rental handover. | Who can confirm a late handover, and when should the advisor consider changing the booking? |
| F13 sparse multilingual intake | On unchanged retry, the base captured Delhi and listed Goa and North Goa as destination candidates. It produced no scoped question about the unlabeled date or missing return. | What single question would resolve the ambiguity without asking the customer to repeat their partial plan? |

## Further source-to-check examples for review

| Case | Decision-changing model input | Scope and control |
| --- | --- | --- |
| F05 airport change | Actual airport identities, bag collection, ground leg and onward check-in cutoff. | Heathrow’s guidance distinguishes separately booked flights and baggage collection. British Airways describes the London airport-change process. Keep self-transfer checks when the second airport becomes Heathrow. An unspecified London airport needs disambiguation. [Heathrow connecting flights](https://www.heathrow.com/content/heathrow/main/gb/en/connecting-flights.html) · [British Airways flight connections](https://www.britishairways.com/en-gb/information/airport-information/london-heathrow-airport/lhr-connections) |
| F06 open jaw and air–rail | The flight arrival station and onward rail departure station are distinct entities. A surface leg consumes time before the rail cutoff. | The regional transport authority lists RER B as an airport connection. Use dated routing, station access and operational status for a calculation. A rail departure at the airport changes the ground leg. A cropped station needs the missing station before a margin can be calculated. [Île-de-France Mobilités airport transport](https://www.iledefrance-mobilites.fr/en/acceder-aux-aeroports-franciliens-) |
| F12 rental after disruption | Scheduled and revised arrival, branch-specific handover policy, and confirmation for the exact rental. | SIXT publishes delay handling that differs by booking terms and asks for flight details. Use that only for an applicable SIXT booking. A confirmed handover supersedes a generic closing time. Holiday or absent branch-specific information calls for verification. [SIXT flight delay policy](https://www.sixt.com/help-center/articles/what-happens-if-my-flight-is-delayed/) |

## B2B check ownership and acceptance

### Authenticated sample follow-through

Submitted the exact F01, F02, F05 and F06 base inputs from New Inquiry in Chrome with an authenticated synthetic agency. All four reached a blocked terminal state with `STOP_NEEDS_REVIEW`. Their destination candidates matched the public API, including Old Goa, Heathrow, and the split Gare du Nord tokens. None returned a structured itinerary feasibility advisory. In contrast, the Workbench API supplied four or five generic intake questions per case, including travel dates and budget. It supplied no specific question about the visit day assignment, the hotel night, the airport change, or the rail transfer. This separates a shared intake gap from a surface-specific follow-up difference. [Authenticated API evidence](../evidence/itinerary-diversity-2026-11-24/workbench-sample.jsonl)

The Heathrow-to-Gatwick screenshot verifies the blocked state in Risk Review. It shows duplicate incomplete-trip messaging and a narrow title column that pushes readiness below the fold. The receipt's immediate tab text capture was empty before render; the screenshot subsequently rendered Trip readiness and Extraction Quality. The run response establishes the question content. This four-case sample does not establish B2B parity for the remaining cases. [Workbench capture](../evidence/itinerary-diversity-2026-11-24/workbench-flight-transfer.png)

| Order | Existing owner to extend | Acceptance evidence |
| --- | --- | --- |
| 1 · Establish roles and chronology | Shared intake and itinerary normalization. Represent a destination, an activity, a connection airport and a rail station in their own roles. Bind a time to its local day and to its segment. | Preserve the original Hinglish Goa result. F01 must distinguish one day from two days and an unknown day. F02 must distinguish an arrival after the proposed check-in date, a revised check-in, and an unknown arrival date. Retain supporting text and unanswered facts in each case. |
| 2 · Calculate scoped constraints | Existing feasibility and logistics checks. Understand operator, booking and product applicability before calculating a margin. | F04 and F05 distinguish known ticket protection from a combined receipt and identify a change of airport. Abstain from a threshold verdict when the cutoff, product, or terminal is unknown. F06 must preserve the stations and surface leg before assessing the onward train. |
| 3 · Give the advisor the next action | Shared risk record and Workbench Risk Review. Represent missing evidence separately from a sourced concern. Carry the same finding to the public report with an actionable question. | On a real same-note replay, inspect what input is missing, who can supply it and when. The operator can record when and how the booking-specific condition was verified. Verify persistence and reload before claiming resolution. |
| 4 · Broaden check families by measured missing coverage | Existing supplier, accessibility, documentation, and disruption workflows. | Add a case and controls for each supported workflow. Use evidence scoped to the precise itinerary and provider. Have the practitioner panel test materiality and reviewer wording on the specific case. |
