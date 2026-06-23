# Travel Agency Main App Simulation - 2026-06-23

## Scope

This is a dedicated main-app simulation, not a landing-page review.
The goal was to exercise the real agent/customer workflow in the actual app surface and record what feels clear, what stalls, and what needs a workaround.

## Live surfaces checked

- `/workbench?draft=new&tab=intake&capture_mode=call&entry=new`
- `/trips/trip_c0fd9ad83511/intake`
- `/trips/trip_c0fd9ad83511/strategy`
- `/trips/trip_c0fd9ad83511/ops`
- `/trips/trip_c5cc2e04e021/output`
- `/insights`
- `/audit`

## Scenario 1: Small agency, one operator, fast turnaround

What worked:

- The trip header is readable and gives the operator immediate context.
- The strategy page gives a clear next-step plan instead of vague system output.
- The copy-to-customer action is a useful time saver when the operator wants to send a draft quickly.

What felt weak:

- The output surface could become a dead end when the saved traveler bundle was missing.
- The operator had to guess whether the trip was actually ready to hand off or just waiting on persistence.

Workaround:

- Show a derived customer draft when the generated bundle is missing, but label it clearly as derived.

## Scenario 2: Large agency, multi-reviewer handoff

What worked:

- The review/policy layer makes it harder to send something casually without checking it.
- The distinction between agent view and customer view is useful for internal QA.

What felt weak:

- The output screen needed a clearer bridge between "reviewed" and "sendable."
- If the final bundle is absent, the handoff path is too easy to lose.

Workaround:

- Keep the output preview visible and add a direct link back to quote assessment.

## Scenario 3: India-based agency, budget-sensitive booking

What worked:

- Budget and trip priorities stay visible in the planning surfaces.
- The app already supports a fast compare-and-review style that fits price-sensitive workflows.

What felt weak:

- If the output bundle is missing, the operator has to rebuild the customer-facing message manually.

Workaround:

- Derive the customer draft from the live strategy and decision so the operator can continue without rewriting from scratch.

## Scenario 4: African agency, fast mobile-first handoff

What worked:

- The app can surface a short, readable opening and keep the response concise.
- The customer-safe copy flow is better than a fake "send" button because it gives the operator something tangible to hand off.

What felt weak:

- An empty output screen is especially costly in fast handoff workflows because it interrupts momentum.

Workaround:

- Replace the empty state with a truthful preview whenever the trip already has strategy/decision context.

## Scenario 5: Global agency, long-haul and multi-currency work

What worked:

- The strategy layer keeps the budget anchor and priorities visible.
- The app is strong when it gives the operator a comparison-ready plan instead of a generic summary.

What felt weak:

- The output stage still needed a durable representation of the customer-ready draft, not just a promise that it exists elsewhere.

Workaround:

- Keep the derived preview on screen until the persisted bundle arrives.

## Scenario 6: Owner analytics and operational oversight

What worked:

- The insights page loads again after clearing the stale Turbopack cache and restarting the dev server.
- The route now returns 200 and the browser title stays on `Waypoint OS — Insights`, which means the owner-facing analytics surface is back to a live state.
- The funnel copy no longer shows impossible percentages when stage counts are not comparable.
- The chart wrappers now declare explicit minimum dimensions, which removes the first-load Recharts width warning in a clean browser replay.
- The shell navigation now treats planned items as inert instead of pretending they are clickable actions.

What felt weak:

- The live browser snapshot still spends time in loading/hydration before the analytics cards appear.
- Recharts emits width warnings during the initial render, which suggests the chart container still wants a more stable sizing contract.

Workaround:

- Keep the server restart and cache reset in the playbook for this route whenever Turbopack starts surfacing internal cache errors.
- Prefer truthful fallback text over impossible conversion percentages.
- Keep analytics verification tied to the authenticated browser session; a fresh headless Chrome profile still lands on the sign-in gate even though the authenticated app tab is healthy.

## Scenario 7: Audit trail review

What worked:

- The audit route exists and the backend exposes a real `/api/audit` contract.
- The route is meant to be the owner/admin review surface for stage transitions, validation outcomes, and overrides.

What felt weak:

- The frontend page was reading `data.items` even though the backend returns `entries`, which would have made a healthy response look empty.
- That mismatch would have hidden real audit activity from the operator.

Workaround:

- Read `entries` first and keep `items` as a fallback only for legacy payloads.

## Scenario 8: Global quote review

What worked:

- The review queue now renders the right currency for each quote card.
- A Nigeria-based review no longer looks like a USD quote just because the UI hardcoded a dollar sign.

What felt weak:

- The review summary block still speaks in generic progress-value terms, so it may need a separate currency policy if the dashboard ever aggregates multi-currency reviews into one figure.

Workaround:

- Use the review payload currency for each row so the card stays truthful for Indian, African, and global agencies.
- Keep planned modules visually marked as planned, but do not make them clickable if there is no real route behind them.

## Scenario 9: Documents shell for incomplete trips

What worked:

- The documents route is a real shell over the canonical document contracts, not a duplicate workflow.
- The page gives a direct trip selector and a clean path back to the trip workspace when fuller context is needed.

What felt weak:

- Trips with missing destination data were collapsing to anonymous `Unknown (...)` labels in the selector.
- That made the picker hard to scan for operators who are already moving through a large queue.

Workaround:

- Reuse the existing lead title pattern and fall back to the trip reference when destination data is incomplete.

## Scenario 10: Suppliers route shell

What worked:

- The suppliers route now opens as a real page instead of a 404.
- The page gives the operator a direct trip selector, supplier risk context, and a link back to the full trip workspace.

What felt weak:

- Before the route was added, the shell advertised `Suppliers` but the browser landed on a dead page.
- That is a trust break because the nav looked live even though the route did not exist.

Workaround:

- Keep the suppliers route as a canonical shell with honest context until a deeper supplier workflow is actually implemented.

## Scenario 11: Knowledge Base route shell

What worked:

- The knowledge route now opens as a real shell instead of a 404.
- The old `/knowledge-base` slug now redirects cleanly to the canonical `/knowledge` surface.
- The page gives a calm placeholder for playbooks, preferences, and memory without pretending the deeper system already exists.

What felt weak:

- Before the route existed, both the canonical and legacy slugs were dead ends.
- That was a trust issue because the nav implied a memory surface even though the app had nowhere to send the user.

Workaround:

- Keep `/knowledge` as the canonical route and redirect legacy `/knowledge-base` traffic into it.

## Scenario 12: Clean browser session on protected agent surfaces

What worked:

- The login credentials `newuser@test.com` / `testpass123` are valid against the backend auth API.
- Once authenticated with a cookie jar, `/api/settings` returns the full agency settings payload and `/api/auth/me` resolves cleanly.
- The protected surfaces are therefore wired to real auth-backed data rather than fake placeholder content.

What felt weak:

- In a clean browser session, `/workbench` and `/settings` sat on the loading shell while `/api/auth/me` returned 401.
- That meant the live browser simulation could not progress into the main app workflow until sign-in happened.

Workaround:

- Treat the browser profile as the thing to initialize, not the route itself.
- Authenticate first, then validate workbench/settings flow state in the same browser session.

## Scenario 13: Seasonal campaign planner, small agency vs global agency

What worked:

- The seasonal campaign page now supports a real create/simulate/preflight/dry-run loop in the live browser.
- A small Indian agency plan for `Monsoon Kerala Small Agency` produced distinct outputs for baseline, aggressive, and conservative scenarios after the backend fix.
- The global `Global Holiday Portfolio` plan also carried the same flow cleanly, which makes the planner usable for both budget-sensitive regional work and larger multi-market campaigns.
- The live card keeps the forecast readable with leads, bookings, margin, confidence, and notes all on the same screen.
- The chosen scenario now stays attached to dry-run and dispatch results too, so the operator does not lose context after leaving the simulation row.

What felt weak:

- Before the scenario fix, the dropdown felt cosmetic because aggressive and conservative produced nearly the same output.
- The result card still does not surface a compact scenario badge, so the user has to infer the active scenario from the select control and the notes line.

Workaround:

- Keep the scenario control and the result notes aligned, and treat the backend simulation profile as the source of truth for distinct what-if planning.
- If we want the planner to feel more decision-ready, the next improvement should be a compact scenario summary next to the active select value.
- Keep the dispatch card scenario-visible so the dry run and the actual send path stay tied to the same what-if assumption.

## Scenario 14: Quote-ready family trip, stale escalation strategy

What worked:

- The trip intake page correctly showed `Ready to build options` for the Nairobi-to-Zanzibar family request.
- The saved trip view preserved the important traveler fields: origin, destination, party size, dates, budget, and priorities.

What felt weak:

- The options page initially opened with `Escalate to senior review due to critical contradictions.` even though the trip itself was already quote-ready.
- That made the operator-facing planning surface feel out of sync with the trip readiness signal and risked implying a harder blocker than the app actually had.

Workaround:

- Prefer the live trip readiness when it already says the trip is quote-ready or better, and treat escalation wording as stale if it conflicts with the trip state.
- Keep the options brief aligned with the current trip fields so the operator can continue without second-guessing the workflow state.

## Scenario 15: Safety review without a persisted safety bundle

What worked:

- The workbench still keeps the decision state visible when the safety bundle has not been stored yet.
- The safety tab now shows a derived customer-message QA preview instead of only a dead-end warning.

## Scenario 16: Signed-in trips queue at scale

What worked:

- A fresh signed-in browser session reached `/trips` cleanly after login and the queue loaded real data instead of a stub.
- The page immediately surfaced `100 in planning` and `96 needs details`, which gives the operator a fast workload readout.
- The card view grouped duplicates into `12 grouped cards`, so the scan surface stays readable even when the queue is large.
- The workspace API returned real workspace trips with `200 OK`, so the trips page is reading the canonical queue rather than a fake front-end-only list.

What felt weak:

- The route still depends on an initialized auth session, so a clean browser profile needs the login step before the queue becomes useful.
- The queue summary mixes grouped-card counts with total trip counts, which is honest but easy to misread if the operator is moving quickly.

Workaround:

- Keep the grouped-card summary and the `needs details` badge visible because they are the fastest way to triage a large queue.
- Treat `/trips` as a prioritization surface first and a full inventory second.

## Scenario 17: Documents and suppliers shells on a large queue

What worked:

- Both `/documents` and `/suppliers` opened as truthful route-level shells instead of dead links.
- The picker now preserves distinct tail references, so the operator can jump into the correct trip workspace when needed.
- The first rows now read like `Trip details incomplete · Updated today · 1294`, `... · C2DD`, `... · A22A`, which makes the large queue readable instead of collapsing into the same visible label.

What felt weak:

- The picker is still long, so it would benefit from inline search or further grouping if the queue keeps growing.

Workaround:

- Keep these as honest shells for now, and treat the current picker labels as good enough for the large-workspace operator flow.

What felt weak:

- Without the fallback, the safety tab read like the work had stopped even when the trip already had useful decision and output context.

Workaround:

- Fall back to the current decision and traveler preview so the operator can still review the message path while the stored safety bundle is missing.

## Scenario 9: Global agency, large corporate group with hyphenated traveler count

What worked:

- The workbench accepted a real corporate offsite request from Lagos to Cape Town.
- The trip page preserved the money in the right currency, `NGN`, and the saved trip showed `18 pax` instead of dropping the group size.
- The trip workspace carried the procurement shape forward with `1 rooming list · shareable with procurement`, which is the kind of detail a larger agency needs to move fast.

What felt weak:

- Before the parser fix, the same live request said `18-traveler` and the decision layer still asked for party size even though the number was in the message.
- That meant the app could mishandle a real-world phrasing used by operators and front-desk staff in global markets.

Workaround:

- Teach the party parser to recognize hyphenated traveler counts like `18-traveler`, not just the space-separated `18 travelers` form.

## Clean findings

- Good: the planning and strategy surfaces are directionally right.
- Good: the customer-safe copy flow is a real time saver.
- Good: the app makes review and send policy visible instead of hiding them.
- Bad: output could become a dead end when the generated bundle was missing.
- Bad: the operator had to infer readiness from a blank state instead of seeing a usable preview.
- Bad: a fake "send" action would have hidden the real work.

## What changed after the simulation

- The output screen now falls back to a derived preview when the persisted bundle is missing.
- The derived preview is labeled so it does not masquerade as saved output.
- The preview includes a direct link back to quote assessment or options, depending on what the trip already has.
- The derived preview no longer reuses the generic internal-draft wording when the trip is still waiting on follow-up details.
- The quote-assessment page no longer shows an advance button while shortlist fields are still missing; it now explains that the missing fields must be completed first.
- The planning helper now says `Prepare the traveler-ready draft before sending.` for internal-draft states instead of surfacing internal wording.
- The insights funnel now falls back to `—` when a comparison would otherwise produce a misleading conversion rate.
- The frontend dev server was restarted cleanly after clearing Turbopack's stale cache, which restored `/insights` from a 500 back to 200.
- Party-size extraction now accepts hyphenated traveler phrasing like `18-traveler`, so global group requests no longer fall back to a false `please provide party size` blocker.
- The documents trip selector now keeps incomplete trips readable by using a fallback trip reference instead of anonymous `Unknown` labels.
- The documents and suppliers trip pickers now use a clearer tail reference, so large queues no longer collapse into the same visible `TC_R`-style label.
- The suppliers nav item now has a real route behind it, so the shell no longer sends operators to a 404.
- The knowledge-base nav destination now has a real route and legacy slug support, so both the canonical and old paths stay truthful.
- Clean browser sessions on protected agent pages now clearly reveal the auth boundary, which makes the simulation honest about when the browser itself needs initialization versus when the route is genuinely broken.
- Protected workbench and settings pages now surface an explicit sign-in notice instead of leaving the operator on an ambiguous loading shell when the browser session is not authenticated.
- Seasonal campaign simulation now differentiates baseline, aggressive, and conservative planning outputs instead of only changing the label, which makes the what-if planner feel real in the live browser.
- Seasonal dry-run and dispatch now keep the chosen scenario visible in the result card, so the planner does not drop context between what-if analysis and action.
- Quote-ready trips now fall back to a derived options brief when a stored escalation strategy conflicts with the live readiness signal, which keeps the planning surface aligned with the trip state.
- Safety review now keeps a useful customer-message QA preview visible even when the persisted safety bundle is missing, instead of only showing a dead-end warning.

## Remaining watchout

- If the backend later persists the final traveler/internal bundles consistently, the UI should keep preferring the saved bundle and only use the derived preview as fallback.
- Fresh browser sessions still need a reliable auth path before live route inspection becomes frictionless; one authenticated session rendered correctly, while a separate headless session landed on Unauthorized until the app session was established.
- The auth-backed pages are healthy once signed in, but a clean browser profile still needs an actual login step before the protected surfaces can be judged as loaded.
- The protected pages now make the login step explicit, so the operator gets a clear next action instead of a frozen-looking skeleton when the session is missing.
- The insights chart container still emits a width warning during initial render; it does not block the page, but it is worth tightening before launch.
- The authenticated browser tab is the trustworthy source for `/insights`; a fresh unauthenticated browser profile is expected to show the sign-in gate.
- Audit data now reads from the correct `entries` field, so the empty-state only appears when there truly are no audit events.
- Review cards now use the quote currency from the payload instead of forcing dollars, which keeps the review queue truthful for global agencies.
- Hyphenated traveler counts are now recognized in extraction, so the operator-facing trip page keeps the correct group size for requests like `18-traveler`.
- The documents and suppliers pickers now expose a clearer tail reference per row, which keeps large queues usable for an operator scanning a shared workspace.
- The suppliers route now shows actual supplier context instead of a dead-end 404, which keeps the nav truthful for an operator exploring the app.
- The knowledge base now has a real shell and redirect path, so the app no longer advertises a memory surface it cannot open.
