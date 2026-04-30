# Intake Actionable Missing Details

Date: 2026-04-30

## Scope

Implemented the intake-screen feedback for the `Need Customer Details` state so the diagnostic panel is directly actionable instead of passive.

## Completed

- `Missing Customer Details` now splits unresolved items into `Required missing fields` and `Recommended details`.
- Every unresolved row now has direct actions on the row:
  - `Add ...`
  - `Ask traveler`
- Inline editors now exist on the blocker panel itself for:
  - budget
  - origin city
  - trip priorities / must-haves
  - date flexibility
- `Suggested Follow-up` is now generated from the remaining unresolved rows only.
- The primary CTA now changes by state:
  - required gaps present -> `Draft follow-up`
  - required gaps resolved -> `Continue to options` or `Build trip options`
- `Notes` is now collapsible when the screen is in missing-details mode so the page stays task-led instead of putting the large note fields at the same visual priority.
- `Trip Details` and `Known Trip Details` now surface origin and the newly captured planning inputs more clearly.
- Footer actions on this screen now use the shared button primitive instead of a one-off treatment.

## Persistence Notes

- `budget` and `origin` persist through canonical trip fields.
- `trip priorities / must-haves` and `date flexibility` are currently persisted through tagged lines in `agentNotes`.

Current tagged note format:

```txt
Trip priorities: ...
Date flexibility: ...
```

This keeps the screen actionable immediately without inventing a duplicate route or shadow persistence path.

## Follow-up Architecture Gap

The trip model still lacks dedicated first-class fields for:

- trip priorities / must-haves
- date flexibility

If these inputs need downstream policy, search, or analytics ownership beyond intake UX, the next correct step is a canonical model/API addition rather than expanding the tagged-note fallback.

## Verification

- `./node_modules/.bin/tsc --noEmit`
- `npm test -- --run src/components/workspace/panels/__tests__/IntakePanel.test.tsx`
- `curl -s http://localhost:8000/health`
- `curl -Ls -o /dev/null -w "%{http_code}" http://localhost:3000/trips/trip_4b9e0d894872/intake`
