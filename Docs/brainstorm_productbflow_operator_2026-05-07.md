# Product B Flow Brainstorm - Operator - 2026-05-07

## 10,000ft
Day-one experience must feel like "fast audit assistant," not "new travel platform." Keep interaction narrow and deterministic.

## 1,000ft
Proposed flow:
1. Landing: "Paste your trip plan or upload docs"
2. Input chooser: freeform text default, upload optional
3. Minimal required fields: destination, dates, traveler profile, budget band
4. Clarification only when needed (max 3 questions)
5. Audit run with progress steps visible
6. Results grouped by severity: Must fix / Should review / Optional optimizations
7. One-click outputs:
   - Copy questions for agent
   - Shareable summary
   - Revision checklist
8. Re-audit revised plan

Operational guardrails:
- Session persistence
- Locale/currency normalization
- Legal-safe language templates
- Confidence labels per finding

## Ground level
Micro-decisions:
- Use "finding + why it matters + exact question to ask" format
- Keep each finding under 3 lines
- Default to 5-8 findings max
- Capture "shared with agent" event explicitly

## The thing most people miss about this
Most drop-off happens before value is felt. The first credible finding must appear extremely early or the whole wedge collapses.

## Addendum - Flow Reliability and Instrumentation (2026-05-07)
Assessment: Real and execution-critical.

What to tighten:
1. Add explicit SLA for first value:
   - Time-to-first-credible-finding target <= 60-90 seconds end-to-end.
2. Clarification budget must be adaptive:
   - Max 3 questions by default, but allow zero-question fast-path when evidence is sufficient.
3. Evidence payload is mandatory per finding:
   - Every finding needs source snippet or rule reference to avoid "AI opinion" rejection.
4. Output artifacts should mirror traveler behavior:
   - Primary artifact is forward-ready message for existing agent; secondary artifact is checklist.
5. Re-audit loop must preserve diff view:
   - Show what changed from previous plan and why it improved/worsened.

Operator call: Keep the flow narrow and deterministic, but instrument each step so we can prove where drop-off occurs and whether first-value timing is actually being met.
