# Backend Output Contract Stabilization Assessment

**Date**: 2026-04-24  
**Scope**: `DecisionResult` / `/run` API response → frontend consumption  
**Status**: Assessment complete — stabilization required before frontend panel

---

## 1. Current State (Verified Against Code)

### What Exists and Works

| Component | File | Status |
|---|---|---|
| `SuitabilityFlag` dataclass | `src/intake/packet_models.py:21` | Present |
| `CanonicalPacket.suitability_flags` | `src/intake/packet_models.py:319` | Field present |
| Tier 1+2 scoring integration | `src/intake/decision.py:1301` | Runs in `shortlist/proposal/booking` |
| `risk_flags` field on `DecisionResult` | `src/intake/decision.py:241` | Present |
| API response serialization | `spine_api/server.py:355` | Uses `_to_dict()` |

### What Is Missing

| Component | Why It Matters |
|---|---|
| `SuitabilityProfile` dataclass | Frontend spec expects this shape; nothing in source maps to it |
| `DecisionResult.suitability_profile` | API response cannot deliver what doesn't exist on the result object |
| Transform layer: `List[SuitabilityFlag]` → `SuitabilityProfile` | Backend has raw flags; frontend needs structured profile with summary + dimensions |
| Score aggregation logic | `overallScore` and `summary.status` must be derived from flags |

---

## 2. The Contract Gap

### Frontend Expects (`SUITABILITY_PRESENTATION_CONTRACT_2026-04-22.md`)

```typescript
interface SuitabilityProfile {
  summary: {
    status: "suitable" | "caution" | "unsuitable";
    primaryReason: string;
    overallScore: number;  // 0-100
  };
  dimensions: Array<{
    type: "age" | "mobility" | "weight" | "intensity" | "climate" | "recovery" | "other";
    severity: "low" | "medium" | "high";
    score: number;
    reason: string;
    evidence_id?: string;
  }>;
  overrides: Array<{
    flag: string;
    overridden: boolean;
    override_action?: "suppress" | "downgrade" | "acknowledge";
    override_reason?: string;
    overridden_by?: string;
    overridden_at?: string;
  }>;
}
```

### Backend Currently Produces

Two different shapes in two different places:

**Shape A: `SuitabilityFlag` (on `CanonicalPacket`)**
```python
SuitabilityFlag(
    flag_type="suitability_exclude_scuba",
    severity="critical",
    reason="Child under 5 cannot scuba dive",
    confidence=0.95,
    details={"activity_id": "scuba", "participant_ref": "child_1"},
    affected_travelers=["child_1"],
)
```

**Shape B: Flat dict in `risk_flags` (`DecisionResult`)**
```python
{"flag": "elderly_mobility_risk", "severity": "high", "message": "..."}
```

Neither matches the `SuitabilityProfile` interface. The API serializes `DecisionResult.risk_flags` directly, so the frontend receives flat dicts with no dimension typing.

---

## 3. Stabilization Plan

### Step 1: Add `SuitabilityProfile` dataclass

Location: `src/intake/packet_models.py` (next to `SuitabilityFlag`)

```python
@dataclass
class SuitabilityProfile:
    """Structured suitability output for frontend consumption."""
    summary: Dict[str, Any]  # {status, primaryReason, overallScore}
    dimensions: List[Dict[str, Any]]  # [{type, severity, score, reason, evidence_id}]
    overrides: List[Dict[str, Any]] = field(default_factory=list)
```

### Step 2: Add `suitability_profile` to `DecisionResult`

Location: `src/intake/decision.py:227`

```python
@dataclass
class DecisionResult:
    # ... existing fields ...
    risk_flags: List[Dict[str, Any]] = field(default_factory=list)
    suitability_profile: Optional[Any] = None  # Shadow field — zero breakage
    commercial_decision: str = "NONE"
```

### Step 3: Add transform function

Location: `src/intake/decision.py` (after `generate_risk_flags`)

```python
def _build_suitability_profile(
    packet: CanonicalPacket,
    risk_flags: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Map raw suitability flags to structured profile for frontend."""
    # ... implementation ...
```

### Step 4: Wire in `run_gap_and_decision`

After `generate_risk_flags()` returns, call `_build_suitability_profile()` and assign to `result.suitability_profile`.

### Step 5: Serialization

The existing `_to_dict()` in `spine_api/server.py:343` handles dataclasses via `__dict__` fallback. `SuitabilityProfile` will serialize automatically.

---

## 4. Zero-Breakage Guarantee

| Scenario | Behavior |
|---|---|
| Old frontend (doesn't know `suitability_profile`) | Renders `risk_flags` as before. `suitability_profile` is ignored. |
| New frontend (consumes `suitability_profile`) | Checks `if (decision.suitability_profile)` then renders `SuitabilityCard`. Falls back to `risk_flags` if absent. |
| Old backend tests | Pass unchanged. `suitability_profile` defaults to `None`. |
| New backend tests | Added for `_build_suitability_profile` logic. |

---

## 5. Risk Assessment

| Dimension | Verdict |
|---|---|
| **Code** | Low risk. Additive change. One new dataclass, one new field, one new function. |
| **Operational** | No operator impact until frontend is updated. Backend remains the source of truth. |
| **Data integrity** | No migrations. Shadow field = optional. |
| **Test coverage** | Must add regression tests for `_build_suitability_profile` and API response shape. |
| **Logical consistency** | Dimension type inference from `flag_type` string must be deterministic and documented. |

---

## 6. Implementation Order

1. Add `SuitabilityProfile` dataclass
2. Add `suitability_profile` to `DecisionResult`
3. Implement `_build_suitability_profile()`
4. Wire into `run_gap_and_decision`
5. Add regression tests
6. Verify API response shape against contract spec

---

**Next action**: Proceed with stabilization implementation.
