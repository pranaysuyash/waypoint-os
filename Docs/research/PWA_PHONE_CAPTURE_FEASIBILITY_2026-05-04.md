# PWA Phone Capture Feasibility (2026-05-04)

## Your Idea
- Phone should open directly into enquiry capture with minimal taps.
- Include quick status visibility.
- Explore direct call recording from phone.

## Current State (Repo)
- No PWA manifest/service-worker implementation is present in `frontend/` yet.
- `New Inquiry` already exists as an action CTA and can be redirected into a capture-first flow.

## Recommendation

### 1) Yes: Build a phone-first PWA shell
Use PWA primarily for:
- One-tap home-screen launch into `New Inquiry` capture mode.
- Fast lead statuses: `new`, `incomplete`, `in_progress`, urgent follow-ups.
- Optional offline draft save and later sync.

### 2) Yes: Phone-first UX shape
- Launch route: `/workbench?entry=new&capture_mode=call` (or future `/inquiries/new`).
- Default screen on phone:
  - Large text box for customer note
  - optional voice-note upload/transcribe
  - one primary CTA: `Save and Process`
- Secondary tab: `My Follow-ups Today` with simple status chips.

### 3) Call recording feasibility (important)

#### What is possible
- Record a voice memo in-app/PWA (microphone) and transcribe.
- Record calls if the call happens inside your own VoIP stack (Twilio/Plivo/WebRTC app), with explicit consent flow.

#### What is generally NOT possible in normal web/PWA
- A browser/PWA cannot reliably capture native cellular call audio (both sides) directly from the phone dialer.
- OS-level restrictions (especially iOS) block direct access to telephony stream for web apps.

#### For native app too
- Native can do more, but direct PSTN call recording is still heavily constrained by platform/carrier/legal rules.
- Compliance and user-consent requirements are mandatory and region-dependent.

## Best Practical Path
1. **Now (low risk):** PWA + post-call capture (text or voice memo) + transcription + one-click process.
2. **Next (medium):** Push notifications for follow-up/status changes.
3. **Later (higher complexity):** In-app VoIP calling with explicit recording consent if true call recording is a hard requirement.

## New Goal Proposal
Ship a **Mobile Intake PWA v1** focused on speed, not telephony integration:
- home-screen installable,
- launch-to-capture in one tap,
- `Save and Process` in one flow,
- lightweight status/follow-up view,
- optional voice memo transcription.
