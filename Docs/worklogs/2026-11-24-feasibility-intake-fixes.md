# Feasibility intake repair and deployment evidence

24 November 2026 · Isolated local preview

## Verified changes

The shared result finalizer keeps scoped itinerary evidence and a next question in the packet used by the public report and Workbench. Workbench updates the existing packet checkpoint so the section can render even when the broader inquiry is blocked. The traveler report gives the feasibility question priority in its summary. Existing structured advisories remain advisory.

| Replay family | Base case | Changed and uncertain cases |
| --- | --- | --- |
| F01 Goa day plan | Goa remains the destination, 19 December is shown as a visit date, and the Dudhsagar access question comes with the pacing advisory. | Moving Old Goa changes the follow-up and removes the three-stop warning. Uncertain dates prompt day confirmation. |
| F02 overnight hotel | Preserves 18 December without supplying an unstated year, identifies the local next-day arrival, and asks about a room hold. | A 19 December hotel night prompts a room-availability question. An unknown arrival day prompts for the local arrival date. |
| F05 airport change | Heathrow and Gatwick appear as arrival and onward airports. The question concerns the onward check-in cutoff and checked bags. | A same-airport revision changes the airport in the question. An unspecified London airport prompts disambiguation. |
| F06 air–rail | Paris-CDG and Gare du Nord appear in their transport roles. The question concerns the rail boarding cutoff. | A revised rail station changes the question context. A cropped station prompts for the ticket's departure station. |
| Original Hinglish Goa | Both original advisories and Goa survived the replay. | Existing control only. |

[Public browser capture](../evidence/feasibility-intake-fixes-2026-11-24/public-goa.png) · [Authenticated Workbench capture](../evidence/feasibility-intake-fixes-2026-11-24/workbench-goa.png) · [Cross-surface replay receipt](../evidence/feasibility-intake-fixes-2026-11-24/replay.jsonl)

## Broader regression sweep

All 39 packet variants were submitted on each surface, plus the original Hinglish control. The 12 targeted variants and control had matching destination, feasibility context, question and advisory IDs. The remaining 27 public submissions returned HTTP 200 and `STOP_NEEDS_REVIEW` with no scoped question. In authenticated Chrome, the 27 corresponding Workbench submissions used 27 distinct run IDs. Twenty-six reached the blocked review state. The confirmed-train revision failed, and an unchanged retry explicitly returned `PrivacyGuardError`. The scoped changes did not add any advisory or question to the other nine itinerary families.

An initial direct Workbench probe used the wrong submission endpoint. A later direct probe reused draft metadata and was excluded. The successful browser harness creates each draft through the actual New Inquiry flow. The public batch retried rate limits and local 500s.

[Broader public responses](../evidence/feasibility-intake-fixes-2026-11-24/broader-public.jsonl) · [Broader authenticated browser responses](../evidence/feasibility-intake-fixes-2026-11-24/broader-workbench-browser.jsonl) · [Confirmed-train retry](../evidence/feasibility-intake-fixes-2026-11-24/workbench-f07-retry.json)

Focused verification passed 19 backend tests, 10 Workbench Risk Review tests, TypeScript checking, and the whitespace check. The regression tests cover the dated Goa positive and changed variants, plus partial overnight dates. This is local desktop evidence.

## Deployment blockers

1. **Generalize and validate extraction.** The new patterns cover scoped note shapes and explicit correction wording. They do not generalize to arbitrary destinations, multi-leg notes, unrelated supplier rules, or unmarked contradictions. Partial dates live in the feasibility context. The earlier extraction and quote gate can still report incomplete trip details, so there is no proof the corrected context can drive a supplier or quote decision.
2. **Separate feasibility from quote readiness in the UI.** The Workbench capture shows the next question in Risk Review while the header still repeats generic incomplete-trip copy. The title column also wraps aggressively and can push the new section below the fold. The public report still shows a generic missing-details area beneath the specific question.
3. **Verify production-shaped storage and configuration.** The local replay used a disposable backend checkout and the isolated test agency. Its earlier file-store runs had a privacy-guard false positive. Hosted ingress, production-shaped persistence and reload of findings across sessions, and device checks remain open.
4. **Broad coverage before rollout.** Keep the four targeted families and original Hinglish control as regression cases. The other nine families still need interpreted roles, date/segment evidence or check-specific questions. Review uncertain inputs and negative controls before expanding which output can influence quote or booking decisions.

Practitioner outreach remains on hold. Link future real practitioner findings to the applicable case variant, source and Waypoint feasibility step. [Practitioner packet](../exploration/ITINERARY_PRACTITIONER_REVIEW_PACKET_2026-11-24.md)
