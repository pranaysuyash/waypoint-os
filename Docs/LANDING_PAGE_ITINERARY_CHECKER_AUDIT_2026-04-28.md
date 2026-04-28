# Landing Page & Itinerary Checker Audit

Date: 2026-04-28

## Scope

Reviewed the public marketing implementation in:
- `frontend/src/app/page.tsx`
- `frontend/src/app/itinerary-checker/page.tsx`
- `frontend/src/components/marketing/MarketingVisuals.tsx`
- `frontend/src/components/marketing/marketing.tsx`
- `frontend/src/components/marketing/marketing.module.css`
- `frontend/src/app/__tests__/public_marketing_pages.test.tsx`

## Audit Summary

The homepage and itinerary checker page are visually polished and conceptually aligned to a boutique travel agency GTM story.

The home page successfully positions Waypoint OS as an agency operation workspace. The itinerary checker page is strong on lead-gen framing and customer-facing trust language.

However, the biggest gap is product truth: the itinerary checker appears to be a marketing-first surface rather than a backend-enabled upload/analyze tool. That gap creates risk if the page is published before the actual experience is implemented.

## Primary findings

### 1. Itinerary checker looks like a real tool but is currently a marketing mock

- The page presents an upload-first experience and analysis snapshot.
- The code contains UI previews and notebook-style interaction, but no actual upload or analysis backend wiring is visible in the audited source.
- This is a high-priority review issue because it affects product credibility and user expectations.

### 2. Privacy and data-handling claims need stronger support

- The itinerary checker page uses phrases like "privacy-safe handling" and "consumer-safe findings."
- There is no explicit public privacy signal, data retention statement, or upload consent explanation in the current implementation.
- This is an implementation concern for trust and compliance.

### 3. Homepage should make the wedge path more clearly actionable

- The home page correctly includes the itinerary checker wedge, but it reads more like a marketing teaser than a direct, low-friction trial path.
- For agency buyers, the primary conversion remains "Book a demo." The wedge should be more explicitly framed as a public trial / lead-generation funnel.

### 4. Product specificity is too abstract for conversion

- Copy emphasizes agency workflow and judgement, but lacks concrete feature detail beyond "brief, questions, owner checks, client-safe response."
- For a B2B audience, the page should surface at least 3 real product capabilities or outcomes clearly.

### 5. Test coverage checks page copy but not experience truth

- Existing tests validate hero copy, CTA links, and anchor behavior.
- There is no test verifying whether the upload/analysis section is actual interactive behavior or merely static content.

## Recommended review/implementation actions

1. **Verify the itinerary checker implementation**
   - Confirm whether `/itinerary-checker` has a backend upload/analysis flow or if it is currently a demo/mock page.
   - If it is a mock, mark it clearly and/or implement the real upload and analysis experience before pushing the page as a public tool.

2. **Add explicit privacy/handling copy**
   - Add a short statement describing what happens to uploaded plans, how long they are retained, and whether the tool uses them only for analysis.
   - If the public tool exposes any PII or review notes, make the handling policy clear.

3. **Strengthen the home page wedge CTA**
   - Make the itinerary checker path feel like a concrete public funnel: "Try the public itinerary checker" or "Test your plan before you book."
   - Consider adding a second hero CTA or a mini testimonial/proof point tied to the checker.

4. **Clarify product outcomes on the home page**
   - Add 3 explicit capability bullets, such as: intake normalization, risk question generation, owner review escalation.
   - Keep the current agency judgment language, but attach it to tangible deliverables.

5. **Add tests for the itinerary checker experience**
   - Add a test that confirms the upload area is not presented as an interactive upload if the feature is not implemented.
   - Add tests for new privacy/help text if copy is expanded.

## Implementation outcome (2026-04-28)

All five recommended actions are implemented. Decision on itinerary checker: **keep as an interactive marketing demo** — the `NotebookAnalyzer` is already a credible interactive experience; building a real backend pipeline is a separate Phase 3+ scope item.

### Changes made

| File | Change |
| :--- | :--- |
| `frontend/src/app/itinerary-checker/page.tsx` | Hero upload card kicker changed from "Upload itinerary" to **"Sample preview"**; upload zone CTA now directs users to `#notebook` (live interactive experience) instead of `#checks` (static copy); explicit **privacy statement** added to the trust card (`data-testid="privacy-statement"`) explaining data is not stored, not shared, session-only; third `ProofChip` updated to "Not stored · Not shared · Session only". |
| `frontend/src/app/page.tsx` | `productMoments` updated to name three concrete capabilities: **Intake normalization**, **Risk question generation**, **Owner review escalation**. Wedge section `h2` changed to "Test your plan before you book. Free, no account needed." Wedge CTA changed from secondary "Open itinerary checker" to primary **"Try the free itinerary checker"** with arrow icon. |
| `frontend/src/app/__tests__/public_marketing_pages.test.tsx` | 4 new tests added: homepage wedge CTA is actionable; homepage names concrete capabilities; itinerary checker hero is labeled "Sample preview" and is not a real form; privacy statement is present and contains "not stored / not shared / session". GSAP `matchMedia` mock added to `vitest.setup.tsx` to fix pre-existing test failure. |

**Test result**: 7/7 passing (was 2/3 before, with one pre-existing failure).

### Remaining open item

The `NotebookAnalyzer` runs hardcoded simulated analysis (no backend call). This is appropriate for now but should be replaced with a real `/api/itinerary-check` endpoint as part of Phase 3 agentic autonomy work (P3-04 Scenario Replay Engine is the closest existing task). When that ships, remove the simulated step timers and update tests to verify real API call behavior.
