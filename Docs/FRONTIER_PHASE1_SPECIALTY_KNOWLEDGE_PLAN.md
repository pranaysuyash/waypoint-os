# Frontier Phase 1 — Specialty Knowledge Salvage Plan

**Date:** 2026-04-30
**Status:** PLAN ONLY. No implementation without explicit approval.
**Scope:** Specialty knowledge only. No Ghost, Sentiment, Federation, Legacy, or FrontierDashboard.

---

## 1. How specialty_knowledge.py Works Today

### Source

`src/intake/specialty_knowledge.py` (63 lines) — 5 real niche definitions with keywords, checklists, compliance, safety notes, and urgency:

| Niche | Urgency | Keywords |
|-------|---------|----------|
| Academic Research Logistics | HIGH | grant, field site, sampling, research, pi, professor, university |
| Human Remains Repatriation | CRITICAL | repatriation, mortuary, remains, death certificate, funeral, casket |
| Sub-Aquatic & Diving Operations | NORMAL | diving, saturation, rebreather, compressor, nitrox, scuba |
| Medical Tourism & Post-Op Recovery | HIGH | surgery, recovery, post-op, dental, elective, clinic, treatment, patient |
| MICE (Meetings & Incentives) | NORMAL | conference, exhibition, incentive, convention, delegate, summit, keynote |

### Detection

`SpecialtyKnowledgeService.identify_niche(text)` — keyword-based match against the input text. Returns `List[SpecialtyKnowledgeEntry]` (Pydantic models).

### Where It Runs

`frontier_orchestrator.py:116-131` — called during every pipeline run:
```python
analysis_text = " ".join([
    packet.raw_note or "",
    str(packet.facts.get("trip_purpose", "")),
    str(packet.facts.get("destination_candidates", "")),
    str(packet.facts.get("resolved_destination", "")),
])
specialty_hits = SpecialtyKnowledgeService.identify_niche(analysis_text)
```

### Current Data Path

```
specialty_knowledge.py
  → frontier_orchestrator.py:117-119  (result.specialty_knowledge populated) ✅
  → orchestration.py:334              (frontier_result has it) ✅
  → orchestration.py:337-343          (frontier dict written to decision.rationale) ✅
  → BUT: specialty_knowledge NOT included in frontier dict ❌  ← THE GAP
  → server.py:972                     (decision saved to TripStore) ✅
  → frontend: store.result_decision   (loaded from trip) ✅
```

### The Fix: ONE LINE

In `orchestration.py:337-343`, add `specialty_knowledge` to the frontier dict:

```python
decision.rationale["frontier"] = {
    "ghost_triggered": frontier_result.ghost_triggered,
    "ghost_workflow_id": frontier_result.ghost_workflow_id,
    "sentiment_score": frontier_result.sentiment_score,
    "anxiety_alert": frontier_result.anxiety_alert,
    "intelligence_hits": frontier_result.intelligence_hits,
    "specialty_knowledge": [h.model_dump() for h in frontier_result.specialty_knowledge],  # ← ADD
}
```

No other backend changes needed. No new API fields. No new RunStatusResponse fields. No frontier_result wiring. The data flows through the existing decision persistence path.

---

## 2. Whether Specialty Hits Are Persisted Today

**No.** The frontier dict is written to `decision.rationale["frontier"]` but `specialty_knowledge` is the ONE field missing from it. All other fields (ghost_triggered, ghost_workflow_id, sentiment_score, anxiety_alert, intelligence_hits) ARE written and persisted.

After the fix, specialty hits will flow through:
1. `decision.rationale["frontier"]["specialty_knowledge"]` → `_to_dict()` → TripStore (persisted)
2. `_checkpoint_result_steps()` → RunLedger (decision checkpoint)
3. Frontend `useHydrateStoreFromTrip` → `store.result_decision.rationale.frontier.specialty_knowledge`

---

## 3. Whether Safety Tab Can Receive Them from Existing Trip Data

**Yes.** The SafetyTab currently reads `result_safety`, `result_traveler_bundle`, `result_internal_bundle`. It does NOT read `result_decision`. **One additional store read needed:**

```tsx
const { result_decision, ... } = useWorkbenchStore();
const specialtyHits = result_decision?.rationale?.frontier?.specialty_knowledge;
```

Or use the fallback chain: `result_decision || trip?.decision`.

---

## 4. Smallest Backend Contract Change

**None.** No changes to:
- `spine_api/contract.py` — existing types sufficient
- `spine_api/server.py` — existing decision persistence path sufficient
- `frontend/src/types/spine.ts` — `rationale` is typed as `Rationale` but `frontier` is a dynamic dict, accessed via bracket notation

The `Rationale` type in `spine.ts` has typed fields (hard_blockers, soft_blockers, contradictions, confidence, confidence_scorecard, feasibility). The `frontier` sub-key is a dynamically added dict on the rationale object. In practice, `result_decision?.rationale?.frontier?.specialty_knowledge` works via optional chaining through `any` types.

---

## 5. Target Page: Safety Tab → "Special Handling Checklist"

### Why Safety

The specialty knowledge file contains:
- **Compliance requirements** (Fly America Act, HIPAA, IATA TACT, Nagoya Protocol)
- **Safety notes** (no-fly time after diving, emergency care proximity)
- **Checklists** (verification items for regulators/insurers)
- **Urgency levels** (CRITICAL for human remains, HIGH for medical/research)

This is closer to "operational handling requirements" than "trip options." The Safety tab already shows "Content Review" and "Customer-Facing Message" — it's the right place for an agent to verify compliance before sending.

### Why NOT Options/Strategy

- Options: shows session goal, priorities, tone, opening. Specialty checklists aren't about trip options — they're about compliance/safety.
- Trip Details: shows extracted facts. Specialty checklists aren't extraction artifacts — they're handling requirements.
- Decision: shows decision state, rationale, budget, suitability. Specialty hits could supplement but the Decision tab is already 443 lines.

### UI Placement

In SafetyTab, after the "Content Review" and "Jargon Found" sections, BEFORE "Customer-Facing Message":

```
Content Review          [PASS/FAIL]
Jargon Found            [if any]
Special Handling Checklist   [NEW — only if specialty hits exist]
Customer-Facing Message
Agent-Only Notes
```

---

## 6. Proposed Implementation

### Files to Change

| File | Change | Lines |
|------|--------|-------|
| `src/intake/orchestration.py` | Add `specialty_knowledge` to frontier dict | ~1 line |
| `frontend/src/app/(agency)/workbench/SafetyTab.tsx` | Add Special Handling section | ~50 lines |

### Backend Change (1 line)

```python
# src/intake/orchestration.py, line 337-343
decision.rationale["frontier"] = {
    "ghost_triggered": frontier_result.ghost_triggered,
    "ghost_workflow_id": frontier_result.ghost_workflow_id,
    "sentiment_score": frontier_result.sentiment_score,
    "anxiety_alert": frontier_result.anxiety_alert,
    "intelligence_hits": frontier_result.intelligence_hits,
    "specialty_knowledge": [h.model_dump() for h in frontier_result.specialty_knowledge],
}
```

### Frontend Change (~50 lines)

Add to SafetyTab:

```tsx
// Read result_decision from store
const { result_decision, ... } = useWorkbenchStore();
const activeDecision = result_decision || (trip?.decision as DecisionOutput | null);
const specialtyHits = (activeDecision?.rationale as any)?.frontier?.specialty_knowledge;

// Only show when real hits exist
{specialtyHits && specialtyHits.length > 0 && (
  <div className={styles.section}>
    <h3 className={styles.sectionTitle}>Special Handling Checklist</h3>
    {specialtyHits.map((hit, i) => (
      <div key={i} className={styles.card}>
        {/* Niche name + urgency badge */}
        {/* Checklist items */}
        {/* Compliance notes */}
        {/* Safety notes */}
        <p className={styles.detectionSource}>
          Detected from inquiry text
        </p>
      </div>
    ))}
  </div>
)}
```

### UI Copy (agency-appropriate)

```
SPECIAL HANDLING CHECKLIST

Academic Research Logistics          HIGH
↳ Checklist
  ✓ ATA Carnet for Sensors
  ✓ Research Visa Verification
  ✓ Hazmat Manifest (Batteries)
  ✓ Cold Chain Protocol

↳ Compliance
  • Fly America Act
  • Nagoya Protocol Disclosure

↳ Safety
  Coordinate with institutional field safety office for remote site tracking.

Detected from inquiry text
```

For CRITICAL niches (Human Remains): red/yellow urgency badge.
For HIGH niches: amber badge.
For NORMAL: neutral badge.

### What if No Hits

Show nothing. No section. No "No specialty requirements detected." No fake empty state. Just silently absent.

---

## 7. Test Plan

### Backend Test

```bash
# Verify specialty detection works end-to-end
cd /Users/pranay/Projects/travel_agency_agent
SPINE_API_DISABLE_AUTH=1 uv run python -c "
from src.intake.specialty_knowledge import SpecialtyKnowledgeService

# Should match medical tourism
hits = SpecialtyKnowledgeService.identify_niche('Patient needs post-surgery recovery trip to Thailand with dental treatment')
print('Medical hits:', len(hits))
for h in hits:
    print(' ', h.niche, '-', h.urgency)

# Should match academic research
hits = SpecialtyKnowledgeService.identify_niche('Professor needs field site logistics for research grant in Peru')
print('Academic hits:', len(hits))
for h in hits:
    print(' ', h.niche, '-', h.urgency)
"
```

### Backend Pipeline Test

```bash
SPINE_API_DISABLE_AUTH=1 uv run python -c "
from src.intake.orchestration import run_spine_once
from src.intake.packet_models import SourceEnvelope

env = SourceEnvelope.from_freeform('Patient needs surgery recovery trip to Bangkok, post-op care required', 'agency_notes', 'agent')
result = run_spine_once(envelopes=[env])
fr = result.decision.rationale.get('frontier', {})
print('Specialty knowledge in decision:', fr.get('specialty_knowledge'))
"
```

### Frontend Test

Add to SafetyTab test:
- Test: specialty hits render as checklist cards
- Test: no hits → no section rendered
- Test: CRITICAL urgency gets red badge
- Test: compliance notes are displayed
- Test: "Detected from inquiry text" label present

---

## 8. What Remains Parked

| Item | Status |
|------|--------|
| Ghost Concierge | Parked — not touched |
| Sentiment / Emotional State | Parked — not touched |
| Federated Intelligence | Parked — not touched |
| Legacy Aspirations | Parked — not touched |
| FrontierDashboard component | Parked — not touched |
| Frontier OS tab | Already removed (Phase 0) |
| Frontier settings toggles | Already removed (Phase 0) |
| `result_frontier` store field | Parked — not used |
| `routers/frontier.py` | Parked — not used |
| Backend frontier models | Parked — not used |

---

## 9. Implementation Order

1. Backend: add 1 line to `orchestration.py` (specialty_knowledge → frontier dict)
2. Backend: verify with `run_spine_once()` test that specialty hits flow through
3. Frontend: add Special Handling section to SafetyTab
4. Frontend: test with mock decision data
5. Frontend: run build + workbench tests
6. Verify end-to-end: submit a "surgery recovery Bangkok" inquiry, see specialty checklist in Safety tab
