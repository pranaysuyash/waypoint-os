# Product B Flow Brainstorm - Cartographer - 2026-05-07

## 10,000ft
Information architecture should mirror decision pressure: what must be fixed now, what can be negotiated, what is optional.

## 1,000ft
Primary views:
1. Intake workspace (text/upload)
2. Findings board (severity lanes)
3. Evidence drawer (why this was flagged)
4. Share kit (agent-ready artifacts)
5. Re-audit compare view (before vs after)

Grouping dimensions:
- Cost
- Suitability
- Logistics
- Policy/constraints
- Confidence

## Ground level
At-a-glance model:
- Top strip: Overall trip risk state
- Middle: 5-8 prioritized findings
- Right rail: "Actions to ask your agent"
- Footer: "What changed since last revision"

## The thing most people miss about this
Navigation is strategy. If the UI does not naturally produce a shareable action packet, the GTM mechanism fails even if analysis quality is high.

## Addendum - IA to Behavior Conversion (2026-05-07)
Assessment: Real and directly tied to wedge performance.

What to tighten:
1. Make "Action packet" the primary outcome view, not a side panel:
   - Findings board should feed directly into forward-ready agent message.
2. Enforce evidence-first interaction pattern:
   - Every severity item must expose evidence in one click, no hidden deep nav.
3. Add explicit "sendability" checks in UI:
   - Is this finding clear, specific, and askable as a question?
4. Re-audit compare should quantify progress:
   - Include clear delta markers for risk reduction and unresolved critical items.
5. Keep architecture flat in early versions:
   - Avoid deep navigation trees that delay first action.

Cartographer call: Treat IA as a GTM system. The default journey must end in a concrete message the traveler can send to their existing agent immediately.
