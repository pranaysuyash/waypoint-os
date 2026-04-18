# Activity Suitability Matrix — Implementation Handoff (Product B / GTM)

**Date**: 2026-04-16  
**Source Basis**: `Docs/ACTIVITY_SUITABILITY_MATRIX_WEB_FINDINGS_2026-04-16.md`  
**Status**: Partially Implemented (Tier 1 & 2 complete, Tier 3 and external APIs pending)
**Implementation Summary**: `Docs/SUITABILITY_IMPLEMENTATION_SUMMARY_2026-04-18.md`

---

## 1) Objective

Implement a production-grade suitability matrix for activities where suitability is **derived** from structured provider signals, review affinity, and accessibility overlays.

This document converts research into deterministic build instructions:
- provider ingestion priority
- field-level normalization map
- scoring pseudocode
- acceptance gates
- rollout sequencing

---

## 2) Requirements and Constraints

- **REQ-001**: No vendor-provided universal age suitability score is assumed; score must be derived.
- **REQ-002**: All source adapters must persist field-level provenance (`source`, `timestamp`, `raw_field_path`).
- **REQ-003**: Output must expose confidence and missing-signal diagnostics.
- **REQ-004**: Normalized model must support child/elderly/disability personas.
- **CON-001**: Booking Attractions endpoints are Beta; contract drift tolerance is required.
- **CON-002**: Partner access is required for several APIs (Viator/Klook/Musement/GYG/Booking partner paths).
- **CON-003**: Legacy Tripadvisor docs are non-authoritative; current Content API is implementation authority.
- **GUD-001**: Deterministic-first transforms before any LLM heuristics.
- **SEC-001**: Do not ingest/store PII beyond required booking/suitability signals.

---

## 3) Ingestion Priority Order

## Phase A — Core Structured Suitability
1. **Viator** (primary age/traveler constraints)
2. **Booking Attractions (3.2 Beta)** (search/details/reviews/scores breadth)

## Phase B — Holder/Unit Enrichment
3. **Musement** (normalized holder categories and age-labeled holder names)
4. **Klook** (unit restrictions including age bounds and companion constraints)

## Phase C — Affinity + Accessibility Overlays
5. **Tripadvisor Content API** (review metadata + family proxy signals)
6. **Wheelmap** (mobility accessibility layer)
7. **Euan’s Guide** (qualitative disabled-access signal)

## Phase D — Optional Commercial Expansion
8. **GetYourGuide** partner surface (category/review/tour inventory expansion)

---

## 4) Canonical Suitability Model (Normalized)

```text
activity_id: string
provider: enum
provider_activity_id: string
name: string
category: string
location: object

duration_minutes: integer|null
intensity_level: enum(low|medium|high|unknown)

age_min: integer|null
age_max: integer|null
age_band_labels: string[]
requires_adult: boolean|null
traveler_mix_constraints: object|null

mobility_access_status: enum(yes|limited|no|unknown)
step_free_access: boolean|null
accessible_toilet_signal: enum(yes|no|unknown)

language_options: string[]
review_score: number|null
review_count: integer|null
family_affinity_signal: number|null

cancellation_cutoff_hours: integer|null
refund_policy_type: enum(full|partial|none|unknown)

price_min: number|null
price_currency: string|null

source_confidence: number (0..1)
field_confidence: map<string, number>
source_freshness_days: integer|null
provenance: map<string, object>
```

---

## 5) Provider Field Mapping (Initial)

| Canonical Field | Viator | Booking Attractions | Musement | Klook | Tripadvisor | Wheelmap/Euan |
|---|---|---|---|---|---|---|
| `provider_activity_id` | product/activity id | attraction id | activity/product id | product id | location id | place/venue id |
| `name` | title/name | details.name | activity name | internal/display name | location name | venue/place name |
| `category` | product category/type | attraction category/type (if present) | activity type | product/option type | category/group | venue type |
| `duration_minutes` | duration fields | details duration fields (if present) | activity duration (if present) | availability type + option timing | limited | N/A |
| `age_min`, `age_max` | explicit age ranges | derive if exposed; else null | derive from holder name/range | explicit restrictions min/max age | not primary | N/A |
| `requires_adult` | traveler mix constraints | derive from policy if available | infer from holder model | companion/accompanied constraints | N/A | N/A |
| `traveler_mix_constraints` | explicit pax/age-band rules | policy/filters if present | holder + product constraints | unit restrictions | N/A | N/A |
| `review_score`, `review_count` | provider review signals | attractions reviews/scores endpoints | if available | if available | details/reviews responses | qualitative rating only |
| `family_affinity_signal` | derive from tags/reviews if available | derive from reviews text/meta | derive if available | derive if available | trip-type/review segment proxy | N/A |
| `mobility_access_status` | special requirements/access fields (if present) | details attributes if present | limited | limited | sparse | primary source |
| `cancellation_cutoff_hours`, `refund_policy_type` | cancellation policy fields | booking policy fields if present | activity cancellation fields | option policy fields | N/A | N/A |
| `language_options` | language availability | request/response language variants | Accept-Language model | locale model | language param | N/A |
| `source_confidence` | high for explicit constraints | medium-high (beta drift) | high for holder normalization | medium-high partner-gated | high for current API docs | medium-high overlay quality |

### Mapping rules
- If multiple providers provide the same canonical field, choose in this precedence:
  1) explicit numeric/typed field
  2) structured enum/normalized holder
  3) derived parse from label/text
  4) null + low confidence

---

## 6) Derived Scoring Pseudocode

```python
def compute_suitability(activity, persona):
    # Weights (v1 default)
    W_AGE = 0.35
    W_ACCESS = 0.20
    W_DURATION = 0.15
    W_CANCEL = 0.15
    W_AFFINITY = 0.15

    age_fit = score_age_fit(activity, persona)
    access_fit = score_accessibility(activity, persona)
    duration_fit = score_duration_intensity(activity, persona)
    cancel_fit = score_cancellation(activity, persona)
    affinity_fit = score_family_affinity(activity, persona)

    raw = (
        W_AGE * age_fit
        + W_ACCESS * access_fit
        + W_DURATION * duration_fit
        + W_CANCEL * cancel_fit
        + W_AFFINITY * affinity_fit
    )

    # Confidence adjustment penalizes sparse/derived-only fields
    confidence = compute_confidence(activity.field_confidence)
    adjusted = raw * confidence

    return {
        "raw_score": round(raw, 4),
        "confidence": round(confidence, 4),
        "final_score": round(adjusted, 4),
        "explanations": build_explanations(activity, persona),
        "missing_signals": list_missing_signals(activity),
    }
```

### Subscore guidance
- `score_age_fit`: hard-fail if persona age outside strict min/max bound where confidence >= threshold.
- `score_accessibility`: emphasize wheelchair/step-free/toilet signals for elderly or mobility-sensitive personas.
- `score_duration_intensity`: penalize long/high-intensity options for seniors/young children.
- `score_cancellation`: reward flexible cancellation for uncertainty-sensitive itineraries.
- `score_family_affinity`: normalized review family signal (Tripadvisor and cross-source review metadata).

---

## 7) Confidence Model (Deterministic)

`field_confidence` defaults:
- 0.95: explicit typed numeric/boolean from official provider field
- 0.80: official structured enum/category/holder normalization
- 0.60: inferred from provider label text (e.g., "Child 3-17")
- 0.40: weak heuristic from unstructured text
- 0.00: missing

`source_confidence` defaults:
- High-authority stable docs/providers: 0.90+
- Beta/volatile endpoint families: 0.70–0.85
- Community overlays/qualitative sources: 0.65–0.85 (field dependent)

Final confidence:
```python
confidence = clamp(weighted_mean(field_confidence.values()), 0.0, 1.0)
```

---

## 8) Implementation Phases (Atomic)

### Phase 1 — Contracts + Adapters
- Define canonical suitability dataclass/schema.
- Create provider adapter interfaces:
  - `adapter_viator.py`
  - `adapter_booking_attractions.py`
  - `adapter_musement.py`
  - `adapter_klook.py`
  - `adapter_tripadvisor.py`
  - `adapter_wheelmap.py`
  - `adapter_euansguide.py`
- Persist provenance map per normalized field.

### Phase 2 — Normalization + Scoring Engine
- Build normalization pipeline and precedence resolver.
- Implement deterministic subscore functions.
- Implement confidence-adjusted final score.
- Emit explanations + missing signal diagnostics.

### Phase 3 — Validation + Eval Harness
- Golden fixtures per provider + mixed-provider merges.
- Persona-based eval set (child family, senior traveler, accessibility-sensitive).
- Regression suite for score stability and monotonic behavior.

### Phase 4 — Product Wiring
- Expose matrix results to Product B/GTM workflows.
- Add configurable weight profile by segment (family/senior/adventure).
- Add drift monitors for Beta providers (Booking attractions).

---

## 9) Acceptance Criteria

- **AC-001**: At least 2 primary providers ingested (Viator + Booking) with canonical mapping completeness >= 80% for required fields.
- **AC-002**: Confidence model populated for every canonical field.
- **AC-003**: Suitability output returns score + explanation + missing signals for all evaluated activities.
- **AC-004**: Accessibility overlay contributes measurable delta in elderly/mobility personas.
- **AC-005**: Regression tests pass with stable ranking order for fixed fixture sets.
- **AC-006**: Provider drift handling is documented and tested for Booking Beta contracts.

---

## 10) Risks and Mitigations

- **RISK-001**: Booking Beta schema changes break parser.
  - **MITIGATION**: versioned adapter contracts + schema smoke tests.

- **RISK-002**: Incomplete age fields across some providers.
  - **MITIGATION**: fallback precedence + explicit low-confidence output.

- **RISK-003**: Accessibility data sparsity by destination.
  - **MITIGATION**: merge multiple overlays + expose coverage indicator.

- **RISK-004**: Partner API access delays.
  - **MITIGATION**: stage adapters behind feature flags and run with available providers first.

---

## 11) File Targets (Suggested)

- `src/suitability/models.py`
- `src/suitability/normalizer.py`
- `src/suitability/scoring.py`
- `src/suitability/confidence.py`
- `src/suitability/adapters/adapter_*.py`
- `tests/suitability/test_mapping_*.py`
- `tests/suitability/test_scoring.py`
- `tests/suitability/test_confidence.py`
- `tests/suitability/test_provider_drift.py`

---

## 12) Execution Note for Downstream Agent

Start with **Viator + Booking** only, land canonical model + scoring + eval harness, then expand adapters in the declared order. Do not block Phase 2 scoring implementation on later provider onboarding.