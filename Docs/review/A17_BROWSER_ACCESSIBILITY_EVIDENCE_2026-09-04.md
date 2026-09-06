# A-17 WelcomeCard browser and accessibility evidence

Date: 2026-09-04\
Scope: `frontend/src/components/onboarding/WelcomeModal.tsx` (`WelcomeCard`)\
Owner: A-17 browser/accessibility evidence lane

## Disposition

**PARTIAL — local browser evidence captured; release-level accessibility proof remains open.**

This report records what was directly observed in a local development run. It
does not promote local dev evidence to hosted, production, native-device,
real-user, or screen-reader evidence.

The component is intentionally a non-modal onboarding card. The expected
semantic contract is therefore a labelled `region`, no `dialog` role, no modal
focus trap, and no page scroll lock while the card is visible.

## Runtime preconditions and evidence boundary

The project preview was run with the required local services:

| Check | Result | Evidence boundary |
| --- | --- | --- |
| Frontend `http://localhost:3005` | HTTP 200 | Local Next.js development server only |
| Backend `http://localhost:8000/health` | HTTP 200, `status: ok` | Local development server only |
| Backend `http://localhost:8000/metrics` | HTTP 200, `status: ok` | Local development server only |

The backend required a development-only ephemeral `PROPOSAL_SIGNING_KEY` to
start, and the run used `SPINE_API_DISABLE_AUTH=1` with the non-production
frontend session seed. No secret value is recorded here. This means the run
proves the rendered local contract under a seeded development session; it does
not prove production authentication, hosted routing, or provider behavior.

The health response also reported `llm.available: false` and
`issues: ["LLM not available or not configured"]`. The overview emitted
unrelated 404/500 resource failures and visible unavailable/error states while
the WelcomeCard still rendered. Those failures are retained as runtime
residuals and are not attributed to A-17.

## Desktop browser assertions

Browser daemon assertion at `http://localhost:3005/overview`, viewport
`2560 x 1049`:

```json
{
  "url": "http://localhost:3005/overview",
  "title": "Waypoint OS — Agency Overview",
  "viewport": { "width": 2560, "height": 1049 },
  "card": true,
  "role": "region",
  "labelledby": "welcome-card-title",
  "describedby": "welcome-card-description",
  "dialogCount": 0,
  "buttons": [
    { "label": "Close welcome card", "type": "button" },
    { "label": "Process your first inquiryPaste a customer note and let Waypoint extract the trip details.", "type": "button" },
    { "label": "Review the Lead InboxSee all captured inquiries ready for planning and quotes.", "type": "button" },
    { "label": "Configure your workspaceInvite team members and customize agency settings.", "type": "button" },
    { "label": "Get started", "type": "button" }
  ],
  "bodyOverflow": "visible"
}
```

Interpretation:

- The card is present and exposed as `role="region"`.
- The region has the expected heading and description references.
- There are zero `dialog` nodes, consistent with non-modal behavior.
- The five expected controls are native buttons.
- `bodyOverflow: visible` indicates the card did not lock page scrolling.

Screenshot inspected before recording:

- [Desktop WelcomeCard screenshot](./assets/a17_welcome_card_desktop_2026-09-04.png)

The inspected image shows the fixed lower-right card, complete heading,
description, quick links, tip, and primary action while the underlying overview
remains visible.

## Mobile browser assertions

The same browser daemon page was resized to `390 x 844` and asserted again:

```json
{
  "url": "http://localhost:3005/overview",
  "viewport": { "width": 390, "height": 844 },
  "card": true,
  "className": "fixed inset-x-2 bottom-2 z-40 overflow-hidden rounded-2xl border shadow-2xl backdrop-blur-sm",
  "openIntake": true,
  "quickLinkCount": 3,
  "dialogCount": 0,
  "bodyOverflow": "visible"
}
```

Interpretation:

- The compact branch is active at the mobile viewport.
- The `Open intake` action is rendered.
- All three quick links remain represented.
- The card remains a non-dialog region and does not lock page scrolling.

Screenshot inspected before recording:

- [Mobile WelcomeCard screenshot](./assets/a17_welcome_card_mobile_390x844_2026-09-04.png)

The inspected image shows the compact bottom card fully visible at 390px,
including the heading, description, `Open intake`, and `Get started` controls.

## Accessibility and interaction observations

These observations came from the CUA accessibility tree and browser daemon
assertions, after inspecting the rendered page:

1. The accessibility tree exposed a labelled region with heading
   `Welcome to Waypoint`, description text, a close button, three quick-link
   buttons, a `PRO TIP` label, and the `Get started` button.
2. The tree contained no `dialog` role. This is expected because the card is
   non-modal and must not trap the user in an onboarding overlay.
3. A native close button received focus with no explicit `tabindex` override
   (`tabIndex: null` from the DOM assertion), preserving ordinary keyboard
   button behavior.
4. Keyboard traversal began at the page's `Skip to main content` control and
   subsequently reached the user menu and page links. This is consistent with
   ordinary document traversal; it is not a complete focus-order audit.
5. Activating `Close welcome card` removed the card and wrote
   `waypoint:welcome-seen:v1=1` to local storage. Reloading the overview kept
   the card hidden, demonstrating the local persistence contract.
6. A quick-link navigation attempt was not promoted to an A-17 pass because a
   later daemon navigation invalidated the execution context while the route
   transition was still settling. Unit-level navigation coverage may exist,
   but this report intentionally does not claim a clean browser route proof.

## Remaining limitations and follow-up tasks

The following are still open before A-17 can be marked fully verified:

- Run a real screen reader pass (VoiceOver/NVDA or equivalent) and record the
  spoken name, description, control order, and announcement after dismissal.
- Complete a keyboard-only audit from page entry through every card control,
  including visible focus, reverse traversal, Escape behavior if applicable,
  and focus after dismissal. The current evidence covers only initial and
  partial traversal.
- Run automated accessibility checks (for example axe) and a measured contrast
  audit for text, borders, focus indicators, and disabled/error states.
- Verify the three quick-link actions independently in a clean browser
  context, with a stable post-click URL and destination sentinel. The current
  run deliberately leaves this as unpromoted due to navigation timing.
- Repeat the visual check on a real mobile device or an approved device
  harness; `390 x 844` is a browser viewport emulation, not device proof.
- Repeat with the real authentication/session path and hosted environment;
  the current run used development session hydration and an auth bypass.
- Triage the unrelated overview 404/500 resource failures and unavailable
  cards separately. They did not prevent WelcomeCard rendering, but they make
  the page unsuitable as a clean end-to-end release fixture.

## Evidence files

- `Docs/review/assets/a17_welcome_card_desktop_2026-09-04.png`
- `Docs/review/assets/a17_welcome_card_mobile_390x844_2026-09-04.png`
- This report: `Docs/review/A17_BROWSER_ACCESSIBILITY_EVIDENCE_2026-09-04.md`

## Final handoff

The local implementation has direct evidence for semantic region exposure,
non-modal behavior, responsive desktop/mobile rendering, native button focus,
close persistence, and absence of body scroll locking. It does not yet have
complete screen-reader, full keyboard, measured contrast, clean quick-link
navigation, device, hosted, or production-auth evidence. Keep A-17 in
**PARTIAL** status until those evidence gaps are intentionally closed or
explicitly accepted as release exclusions.
