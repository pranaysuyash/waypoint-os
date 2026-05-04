# Mobile Intake Exploration Backlog (2026-05-04)

## Objective
Create an execution-ready exploration list to reduce enquiry-capture friction for agency users on phone while preserving the canonical intake/workbench flow.

## Priority Exploration Tracks

1. Capture latency budget
- Measure time from `New Inquiry` tap to first saved note.
- Measure time from first save to first processed output.
- Add instrumentation and define target thresholds.

2. Field minimization experiment
- Compare mandatory-only capture vs optional-expanded capture.
- Track completion rate, time-to-submit, and quality of downstream outputs.

3. Voice workflow quality
- Add voice memo upload/transcription in capture flow.
- Evaluate transcription accuracy on noisy call notes.
- Introduce confidence tagging and fallback prompts.

4. Offline-first draft capture
- Support offline draft creation on phone.
- Queue sync and conflict handling when connectivity returns.

5. Status triage UX
- Build phone-first status lanes: `Today`, `Overdue`, `Waiting`.
- Enable one-tap actions for follow-up and reopen.

6. Follow-up automation at capture time
- Auto-generate follow-up draft from captured details.
- Auto-create reminder deadlines and owner assignment.

7. Consent and compliance track
- Define consent text for audio/transcription usage.
- Add audit logging for consent and transcript access.
- Create jurisdiction policy matrix for recording/transcription constraints.

8. Channel intake adapters
- Normalize WhatsApp/email/itinerary inputs into canonical capture schema.
- Preserve source provenance while avoiding duplicate processing paths.

9. Notification strategy
- Push alerts for overdue follow-ups.
- Push alerts for run completion and critical blockers.

10. Role-based mobile surface
- Define `Quick Capture` mode for high-speed intake.
- Keep full planning workspace separate for deeper operations.

## Suggested Sequencing
- Wave 1: 1, 2, 5
- Wave 2: 3, 6, 9
- Wave 3: 4, 7, 8, 10

## Definition of Done (Per Exploration Item)
- Problem statement and measurable hypothesis.
- Experiment or implementation slice documented.
- Evidence captured (metrics, screenshots, logs, user feedback).
- Decision recorded: adopt, modify, defer, or reject.
