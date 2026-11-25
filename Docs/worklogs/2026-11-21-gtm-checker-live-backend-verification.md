# Checker live-backend verification and design follow-through

November 21, 2026. Companion to the [report-first implementation](2026-11-21-gtm-checker-report-first.md).

## Real backend and provider

The verification used the current backend source, separate loopback FastAPI instances, isolated file stores, and a disposable local PostgreSQL instance for application startup. The database was empty, and unrelated audit tables fell back to file storage. Test input and advisor contact were synthetic. Browser requests went through Next.js and the real FastAPI endpoints. No API was intercepted or mocked.

| Check | Observed result |
|---|---|
| Unmodified valid branded route | HTTP 500. The SlowAPI header wrapper requires an injected Starlette Response argument on the agency profile handler. A missing profile can return 404 before reaching that wrapper, so the earlier unknown-slug check did not catch this. |
| Unmodified public checker, Tokyo | Actual browser POST returned 200 and ASK_FOLLOWUP. The report lacked provider evidence and the matches response returned a null destination and empty match list. Direct API variations with Tokyo also returned no provider evidence. A direct Open-Meteo Tokyo request returned 200. The adapter returns no current-conditions object when no threshold fires, so an absent weather block cannot distinguish clean conditions from omitted or unavailable evidence. |
| Unmodified public checker, Singapore | Actual API POST returned 200 and an Open-Meteo current conditions result in trip `trip_8117335225b7`. Its subsequent test-agency route request returned 200 and `routed`. |
| Branded browser, isolated route correction | A disposable copy added the missing Response argument only. The real branded page, report run, and named consent request then completed. The Singapore report returned 26°C, feels like 31.5°C, 92% humidity, and 6.8 km/h wind as current conditions. The report remained partial with ASK_FOLLOWUP. These values describe conditions at lookup, not conditions for the trip dates. |
| Agency persistence | Report `trip_16f52bbdf52c`, routed lead `lead_c1864100e2dc`, and agency-local work item `wi_bb2a8ad361be` correlate in the isolated files. The work item has an identity key and references the original trip. No agency Workbench acceptance, operator response, email or SMS was observed. The test agency was explicitly named by its branded link. This does not establish geographic marketplace matching for Singapore. |
| Physical mobile | Apple device inventory, ADB and Mobile MCP showed no connected physical device. No physical-device recording. Remote physical fleet use is pending authorization and a route to the isolated app. |

The one-line branded route correction was made only in an isolated runtime copy. It is not in the workspace implementation. The prior report-first changes were preserved.

**Evidence:** [Desktop MP4](../evidence/gtm-live-2026-11-21/desktop-provider-and-handoff.mp4) · [Branded intake](../evidence/gtm-live-2026-11-21/desktop-branded-intake.png) · [Provider-backed report](../evidence/gtm-live-2026-11-21/desktop-branded-report.png) · [Named consent](../evidence/gtm-live-2026-11-21/desktop-advisor-consent.png) · [Receipt](../evidence/gtm-live-2026-11-21/desktop-advisor-receipt.png).

## Prioritized improvements

| Priority | Area | Proposed change and acceptance |
|---|---|---|
| 1 | Branded route and delivery | Add the injected response to the source route and test a successful profile GET through actual rate-limit middleware. Make an agency-scoped, redacted brief openable from the receiving queue. Model captured, queued, opened, accepted and replied separately. Exercise duplicate submissions and failed enqueue, with one agency operator opening and responding to a synthetic lead. |
| 2 | Coverage and provider trust | Return an explicit result for every attempted check, including no issue found, insufficient input, unavailable, and outside coverage. Split lookup-time conditions, trip-window forecast and seasonal baseline. Include provider, fetch timestamp, applicable interval, and geography. Backend currently emits `seasonality`; the UI looks for `climate`, so seasonal values need an agreed contract and a rendering regression test. Remove ambiguous rendering of current weather for future trips. [Open-Meteo docs](https://open-meteo.com/en/docs) |
| 3 | Destination and intake | Use a typed destination value, with role and evidence span, for both provider queries and marketplace matching. Current weather code can flatten arbitrary fact strings, while marketplace derives needs from the stored packet. Characterize both with city-first notes, connection airports, multiple visits, and hotel names. Surface an editable route when the traveler can resolve an ambiguity. Compare provider and marketplace city IDs on the same report. |
| 4 | New checks | Start with one airport corridor. Check ticket type, bag recheck, terminals, gate cutoff and local time. Then add opening-hours or localized closure checks and transit delays where an agency or operator publishes data. Scope entry and transit requirements to nationality, transit type and dated sources. Test source outages and contradictory facts before broadening geographic access. [Finnair connection guidance](https://www.finnair.com/en/smooth-travelling-at-helsinki-airport/connecting-flights) · [GTFS Realtime](https://gtfs.org/documentation/realtime/reference/) · [IATA Timatic](https://www.iata.org/en/services/compliance/timatic/) |
| 5 | Agents | Trial one bounded extraction and clarification agent in shadow mode against the deterministic baseline. It may propose typed facts and the next decision-changing question, each backed by a text span. Code validates and owns thresholds, provenance, calculations and writes. On a held-out corpus, compare destination and timing accuracy, unsupported claims, question usefulness, latency and cost. Promote only improvements with equivalent or safer abstention. |
| 6 | Visuals and UI | Prototype an accessible connection timeline with planned time, known steps, estimates and unconfirmed constraints. Put the existing trip summary and storage actions behind progressive disclosure. Replace the repeated top warning and separate generic signal labels with one concrete action and its evidence. Expose provider and timestamp in the weather card. Add a readable coverage summary and an advisor receipt link only when the recipient can use it. |
| 7 | UX verification | Test a traveler finding the next action and naming what is still unknown unaided. On physical iOS and Android, record paste, keyboard dismissal, partial report focus, named consent and the receipt. Verify touch targets and dynamic text. Measure source availability and advisor follow-through independently of completion counts. |

This is local end-to-end integration evidence with live provider data for a synthetic trip. Hosted behavior, customer use, commercial provider access and real-device acceptance remain unverified.

## November 24 follow-up

The missing FastAPI response argument is now fixed in the workspace route. The branding regression test sends HTTP requests through FastAPI and SlowAPI, verifies the 30-request limit header on a valid profile, and verifies that an unknown profile returns 404. The valid request reproduced the 500 before the patch. After the patch, all 12 tests in the branding, marketplace and contract-authority suites passed.

A fresh desktop replay used the current workspace backend in the same isolated setup. The branded profile returned 200, and the Singapore report returned actual Open-Meteo current conditions (26.7°C, 90% humidity) with an ASK_FOLLOWUP decision. The named request returned routed for lead `lead_06d1b5e79cbf`. The isolated lead and receiving agency work-item files both contain one record for report `trip_cb919140de65`. Operator acceptance and customer contact remain unverified. Physical-device inventories still showed no connected phone.

[Current desktop recording](../evidence/gtm-live-2026-11-24/desktop-provider-and-handoff.mp4) · [Live report](../evidence/gtm-live-2026-11-24/desktop-branded-report.png) · [Advisor receipt](../evidence/gtm-live-2026-11-24/desktop-advisor-receipt.png)

## November 24 post-verification UI and product council

Three independent reviews examined the recorded flow and screenshots. This review is a product assessment of the synthetic desktop replay.

| Seat | Verdict |
|---|---|
| UI and accessibility | The report repeats the missing-details warning and offers “Looks fine” before identifying actionable inputs. The departure city and trip purpose are below the fold. The branded consent screen says “Agencies matched to your plan” and lists Tokyo and Japan coverage for a Singapore itinerary. The recipient came from the branded link. Distinguish that relationship from geographic matching and show current weather with scope and time. |
| Product | The flow has a useful self-service intake slice. It captured a brief and accurately reported an unconfirmed advisor request. This case didn't help choose a booking. The generic warning didn't explain which detail would unlock which check. Queue persistence establishes routing only. |
| Market skeptic | The Singapore scenario lacked a specific booking choice. Its live weather and intake fields test integration. A narrow branded second opinion on a tight or separate-ticket connection provides a decision to observe. The sample card's unexplained “MCT” claim is also hard to interpret without ticket, terminal and source context. |

**Disposition:** Desktop integration verified. Traveler decision value and advisor fulfillment remain open. The report can support an intake pilot when the linked-recipient copy accurately describes the relationship and the agency has a real receiving workflow.

**Next acceptance case (corrected after owner feedback):** Use one traveler-supplied itinerary with a consequential connection or transfer. Audit the submitted plan as-is. Verify a source-scoped connection warning or a clear explanation of unknown coverage. Place the action and the reason at the top. If one detail materially changes the finding, ask for it inline and recheck. Preserve the partial result if a source fails. Use lookup-time weather only as context for future trips. Exercise a mismatched branded profile and show the linked agency without claiming a match.

**Traveler evidence:** With one staffed agency, propose five initial moderated sessions using realistic, sanitized traveler-supplied plans. Observe what they would verify or correct on their own itinerary before and after seeing the checker report. Progress if at least four of five can state both the correct next action and the remaining uncertainty within one minute, there are zero false assurances, and the report surfaces at least one meaningful issue or verification step travelers would otherwise have missed. Treat this as a formative pilot criterion. Independently verify a named advisor can open the redacted brief under their own account and respond through the agreed channel. Include a physical mobile replay.
