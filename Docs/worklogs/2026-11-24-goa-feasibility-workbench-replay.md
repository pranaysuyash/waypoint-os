# Goa feasibility replay in the public checker and Workbench

24 November 2026 · Local preview with isolated test data

Both surfaces now show the overnight hotel and same-day Goa pacing advisories from the existing Waypoint OS feasibility flow. The traveler can see what needs confirmation before booking. The advisor sees the same evidence on the Workbench tab that opens after processing and can refer back to it from Decision and Trip Details.

## Exact replay

> Delhi se Goa jana hai bhai, 2 adults + ek 5 yr ka kid. 18 Dec 2026 ki flight Delhi 23:55 to Goa 02:25 next day. Hotel check-in 18 Dec likha hai, North Goa side, hotel abhi final nahi. 19th ko Baga + Dudhsagar + Old Goa ek hi din kar lenge? 35k max total sabka, flights included. Return ka date abhi decide nahi. Veg food chahiye.

Chrome submitted the original note verbatim through both interfaces. The browser checks compared the exact request payloads and matched the two advisory IDs, messages, and details across both responses.

| Surface | Observed behavior | Evidence |
| --- | --- | --- |
| Anonymous public checker | HTTP 200, `ASK_FOLLOWUP`. Displayed Delhi → Goa, outbound 18 Dec 2026 and three travelers. Its report asked for the return date and displayed both advisories. | [Public report](../evidence/gtm-goa-workbench-2026-11-24/public-report.png) |
| Authenticated Workbench | Dev test-agency signup returned HTTP 201 and session verification returned 200. Browser submitted via New Inquiry. Run accepted with 200 and advanced from queued to completed. The decision was `ASK_FOLLOWUP`. The UI opened Risk Review automatically and displayed both findings. | [Risk Review](../evidence/gtm-goa-workbench-2026-11-24/workbench-feasibility.png) |
| Workbench tabs | Browser switched to Decision and Trip Details and found the same advisories in both. | [Decision](../evidence/gtm-goa-workbench-2026-11-24/workbench-decision.png) · [Trip Details](../evidence/gtm-goa-workbench-2026-11-24/workbench-trip-details.png) |
| API parity | Both results carried `overnight_hotel_arrival` and `goa_day_pacing` with the same messages, authority and source fields. | [Replay receipt](../evidence/gtm-goa-workbench-2026-11-24/replay.json) |

The hotel message connects the 02:25 arrival on 19 December with the proposed 18 December check-in. If the traveler books the previous night, the advisor should confirm the hotel will hold the room for the after-midnight arrival. The pacing message identifies the separate Dudhsagar access leg from Collem and asks for the access arrangements and expected return time before judging the rest of the day. [Government of Goa Dudhsagar guide](https://www.goa.gov.in/places/dudhsagar-waterfalls/)

## Integration notes

- The shared finalizer emits structured advisory records using the existing risk contract. It retains the earlier public fields for report compatibility. Both renderers use the same decoder. The advisories leave quote blockers and readiness scoring alone.
- Workbench polls the run ledger. Its earlier packet checkpoint preceded finalization, so the two advisories could exist in the result without appearing in the polled packet. The finalized packet is now written to the existing packet checkpoint when the advisories are present.
- The first authenticated browser replay found the records in run status while the default Risk Review tab omitted them. The existing review tabs now render the same feasibility section. A fresh replay verified automatic landing and manual tab switching.

## Open gaps

| Gap | What the replay establishes | What remains |
| --- | --- | --- |
| Questions differ across surfaces | The public report asks for the return date. Workbench shows **Waiting on Customer** and asks for trip style to generate a quote. | Align the review messaging so an advisor can distinguish the missing return date from the quote workflow's trip-style requirement. Add an acceptance case for this distinction. |
| Workbench run and decision labels | The same screen displays **Processed successfully**, **Processing Complete**, **Waiting on Customer**, and **Overall Confidence: 0%**. | Explain engine completion separately from traveler readiness. Verify what produced the displayed 0% and distinguish missing confidence from a measured zero before presenting it as an operator signal. |
| Pacing coverage | The rule recognizes the three named Goa stops in a same-day clause. | General day-level timing, activity duration, opening windows, child/rest buffers, transport estimates and dated operator availability need coverage and validation. |
| Overnight coverage | This note explicitly states next-day arrival and the matching proposed check-in date. | Carrier and hotel policy confirmation, plus wider formats and ambiguities, remain open. |
| Advisor resolution | The advisory is visible in the authenticated workflow. | Supplier confirmation, assignment and resolution history were outside this replay. Draft promotion, quote creation, and saved-trip reload were untested. |

## Verification

- Local Next.js and FastAPI handled the real browser requests in an isolated development environment, with a synthetic test agency and a UTF-8 test database. Earlier attempts exposed an isolated database encoding mismatch and a Next.js error. The final replay completed against the refreshed preview. Backend health and frontend returned 200. An unauthenticated metrics probe returned 401.
- Focused Python tests passed 17 of 17. The regression checks that both advisories are serialized with the expected IDs and add no blockers. Workbench Risk Review tests passed 10 of 10. TypeScript and whitespace checks passed.
- Evidence covers an actual desktop Chrome run with local services. Hosted behavior, provider confirmation, real-device mobile behavior and practitioner acceptance remain open for this change. [Council research and wider itinerary coverage](../exploration/ITINERARY_CHECKS_INDUSTRY_COUNCIL_2026-11-24.md)
