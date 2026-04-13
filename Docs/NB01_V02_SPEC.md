# NB01 v0.2 Change Spec: Intake → Agency-OS Packet

**Date**: 2026-04-12
**Source**: Feedback on `TEST_GAP_ANALYSIS.md` + `15_MISSING_CONCEPTS.md` + `FIELD_DICTIONARY_AND_MIGRATION.md`
**Reviewed**: 7 corrections applied (operating_mode top-level, no fact/derived duplication, structured budget/dates, resolved-destination progression, SubGroup struct, visibility semantics, tri-contract lock)
**Scope**: NB01. Co-locks with NB02 contract and NB03 contract via shared schema.
**Principle**: No "out of scope." Everything the travel-agency OS needs gets modeled now. Only external execution is deferred.

---

## Current State (v0.1)

NB01 is one giant code cell (881 lines), structured as:

| Section                    | Lines   | What                                                                                                    |
| -------------------------- | ------- | ------------------------------------------------------------------------------------------------------- |
| 1. Core Domain Models      | 1–100   | `AuthorityLevel`, `EvidenceRef`, `ExtractionMode`, `Slot`, `UnknownField`                               |
| 2. Source Envelope         | 100–140 | `SourceEnvelope`                                                                                        |
| 3. Canonical Packet        | 140–260 | `CanonicalPacket` with `facts`, `derived_signals`, `hypotheses`, `unknowns`, `contradictions`, `events` |
| 4. Conflict Resolution     | 260–310 | `ConflictResolutionPolicy.resolve()`                                                                    |
| 5. Source Adapter          | 310–350 | `SourceAdapter`                                                                                         |
| 6. Normalization Utilities | 350–390 | `Normalizer` (city, budget only)                                                                        |
| 7. Extraction Pipeline     | 390–750 | `ExtractionPipeline` with mock LLM, 2 derived signals, unknowns                                         |
| Test Suite                 | 750–881 | 5 inline print-tests (not assertions)                                                                   |

### v0.1 Vocabulary (to be replaced)

| Current Field          | v0.2 Destination                                                                        | Why                                                             |
| ---------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `destination_city`     | `destination_candidates` (facts) → later `resolved_destination` (NB02/03)               | Semi-open destinations are not a single city                    |
| `travel_dates`         | `date_window` (raw) + `date_start`/`date_end` (normalized)                              | "March or April" is a window, not a date                        |
| `budget_range`         | `budget_raw_text` + `budget_min` + `budget_max` + `budget_flexibility` + `budget_scope` | "around 2L, can stretch" is five signals, not one string        |
| `traveler_count`       | `party_size` + `party_composition`                                                      | "big family" is not a number                                    |
| `traveler_details`     | `passport_status` + `visa_status` per traveler                                          | Booking/document reality                                        |
| `traveler_preferences` | `soft_preferences` + `hard_constraints` + `meal_preferences` + `hotel_preferences`      | Preferences are not one blob                                    |
| `trip_purpose`         | `trip_purpose` + `trip_style`                                                           | "family vacation" vs "adventure backpacking" are different axes |
| _(none)_               | `operating_mode` (top-level)                                                            | System routing, not traveler truth                              |
| _(none)_               | `visibility` semantics on owner fields                                                  | Structural boundary, not procedural                             |

---

## v0.2 Packet Shape: Top-Level Fields

The `CanonicalPacket` dataclass has these top-level attributes. **Nothing else.**

| Field                 | Type               | Purpose                                                                                                              |
| --------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------- |
| `packet_id`           | str                | Unique identifier                                                                                                    |
| `schema_version`      | str                | `"v0.2"` — migration guard                                                                                           |
| `stage`               | str                | `"discovery" \| "shortlist" \| "proposal" \| "booking"`                                                              |
| `operating_mode`      | str                | `normal_intake \| audit \| emergency \| follow_up \| cancellation \| post_trip \| coordinator_group \| owner_review` |
| `decision_state`      | Optional[str]      | Set by NB02, not NB01                                                                                                |
| `facts`               | Dict[str, Slot]    | Explicit or imported truths only                                                                                     |
| `derived_signals`     | Dict[str, Slot]    | Computed routing/judgment values only                                                                                |
| `ambiguities`         | List[Ambiguity]    | First-class ambiguity markers                                                                                        |
| `hypotheses`          | Dict[str, Slot]    | Weak inferences                                                                                                      |
| `unknowns`            | List[UnknownField] | Explicit missing-field markers                                                                                       |
| `contradictions`      | List[Dict]         | Conflicting values between sources                                                                                   |
| `source_envelope_ids` | List[str]          | Provenance                                                                                                           |
| `revision_count`      | int                | How many times requirements changed                                                                                  |
| `event_cursor`        | int                | Audit trail cursor                                                                                                   |
| `events`              | List[Dict]         | Append-only event log                                                                                                |

### Key rule: `operating_mode` is top-level, not in `facts`

`operating_mode` is a **system routing classification**, not a traveler fact. Burying it inside `facts["intake_mode"]` (as v0.2 draft originally did) mixes traveler truth with system routing, and NB02/NB03 will treat it inconsistently.

**Correct**: `packet.operating_mode` at top level, alongside `packet.stage` and `packet.decision_state`.
**Incorrect**: `packet.facts["intake_mode"]` as just another fact slot.

### Key rule: no duplication between facts and derived signals

| Concept                                  | Where It Lives           | Why                                                |
| ---------------------------------------- | ------------------------ | -------------------------------------------------- |
| `customer_id`                            | **facts**                | Explicitly known / imported                        |
| `past_trips`                             | **facts**                | Imported from CRM/history                          |
| `is_repeat_customer`                     | **derived_signals** ONLY | Computed from `customer_id` lookup                 |
| `origin_city` + `destination_candidates` | **facts**                | Explicitly extracted                               |
| `domestic_or_international`              | **derived_signals** ONLY | Computed from facts                                |
| `budget_min` / `budget_max`              | **facts** (normalized)   | Explicitly extracted or normalized                 |
| `budget_feasibility`                     | **derived_signals** ONLY | Computed from budget vs cost table                 |
| `urgency`                                | **derived_signals** ONLY | Computed from `date_end` vs today                  |
| `sourcing_path`                          | **derived_signals** ONLY | Computed from destination + budget + owner context |

If something can be computed from other fields, it is a derived signal, not a fact.

---

## v0.2 Schema: Facts (canonical slot names)

All are `Dict[str, Slot]` entries in `CanonicalPacket.facts`.

### Party & Travelers

| Field                  | Type      | Example                                      | Replaces         |
| ---------------------- | --------- | -------------------------------------------- | ---------------- |
| `party_size`           | int       | `5`                                          | `traveler_count` |
| `party_composition`    | dict      | `{"adults": 2, "children": 2, "elderly": 1}` | — new            |
| `child_ages`           | list[int] | `[8, 12]`                                    | — new            |
| `mobility_constraints` | str       | `"parents can't walk much"`                  | — new            |
| `medical_constraints`  | str       | `"hypertension"`                             | — new            |

### Destination

| Field                    | Type                                                 | Example                    | Replaces           |
| ------------------------ | ---------------------------------------------------- | -------------------------- | ------------------ |
| `destination_candidates` | list[str]                                            | `["Andaman", "Sri Lanka"]` | `destination_city` |
| `destination_status`     | `"definite" \| "semi_open" \| "open" \| "undecided"` | `"semi_open"`              | — new              |
| `origin_city`            | str                                                  | `"Bangalore"`              | — kept             |

> **Downstream resolution**: `destination_candidates` is the discovery-stage representation. Shortlist/proposal/booking stages need a single active planning target. NB02 introduces `resolved_destination` when the traveler selects one candidate. NB01 never sets `resolved_destination`.

### Dates & Duration (structured, not loose strings)

| Field             | Type                                             | Example                                   | Replaces       |
| ----------------- | ------------------------------------------------ | ----------------------------------------- | -------------- |
| `date_window`     | str                                              | `"June-July 2026"` — raw text as captured | `travel_dates` |
| `date_start`      | Optional[str]                                    | `"2026-06-01"` — ISO 8601 if parseable    | — new          |
| `date_end`        | Optional[str]                                    | `"2026-07-31"` — ISO 8601 if parseable    | — new          |
| `date_confidence` | `"exact" \| "flexible" \| "window" \| "unknown"` | `"window"`                                | — new          |
| `duration_nights` | Optional[int]                                    | `5`                                       | — new          |

> `date_window` stores the raw captured text. `date_start`/`date_end` are normalized fields populated only when the parser can extract concrete dates. Urgency computation uses `date_end` (or `date_start` if `date_end` absent). If both are None, urgency is "unknown".

### Budget (structured numeric, not loose strings)

| Field                | Type                                                  | Example                      | Replaces                 |
| -------------------- | ----------------------------------------------------- | ---------------------------- | ------------------------ |
| `budget_raw_text`    | str                                                   | `"around 4-5L, can stretch"` | `budget_range` (partial) |
| `budget_min`         | Optional[int]                                         | `400000` (in INR base units) | — new                    |
| `budget_max`         | Optional[int]                                         | `500000` (in INR base units) | — new                    |
| `budget_currency`    | str                                                   | `"INR"`                      | — new                    |
| `budget_flexibility` | `"fixed" \| "stretch" \| "flexible" \| "unknown"`     | `"stretch"`                  | — new                    |
| `budget_scope`       | `"total" \| "per_person" \| "per_night" \| "unknown"` | `"total"`                    | — new                    |

> NB02 feasibility logic operates on `budget_min`/`budget_max` (numbers), not `budget_raw_text` (string). If only `budget_raw_text` is extractable, `budget_min`/`budget_max` remain None and feasibility returns "unknown" rather than crashing.

### Trip Intent

| Field               | Type      | Example                             | Replaces                          |
| ------------------- | --------- | ----------------------------------- | --------------------------------- |
| `trip_purpose`      | str       | `"family leisure"`, `"pilgrimage"`  | — kept                            |
| `trip_style`        | str       | `"luxury resort"`, `"backpacking"`  | — new                             |
| `hotel_preferences` | str       | `"5-star, kid-friendly"`            | — split from traveler_preferences |
| `meal_preferences`  | str       | `"strict vegetarian, Jain options"` | — split                           |
| `hard_constraints`  | list[str] | `["no long layovers"]`              | — new                             |
| `soft_preferences`  | list[str] | `["beach access", "pool"]`          | — split                           |

### Agency & Owner Context (with visibility semantics)

| Field                    | Type                  | Example                           | Visibility        |
| ------------------------ | --------------------- | --------------------------------- | ----------------- |
| `agency_notes`           | str                   | `"past customer, Singapore 2024"` | **internal_only** |
| `owner_constraints`      | list[OwnerConstraint] | see below                         | **internal_only** |
| `owner_priority_signals` | dict                  | `{"margin_target": 0.15}`         | **internal_only** |

```python
@dataclass
class OwnerConstraint:
    """An owner constraint with explicit visibility semantics."""
    text: str                       # "never book Supplier X in Goa"
    visibility: Literal["internal_only", "traveler_safe_transformable"]
    # internal_only: never shown to traveler, not even transformed
    #   e.g. "never use Supplier X", "this family always overspends"
    # traveler_safe_transformable: can be rephrased neutrally for traveler
    #   e.g. "family prefers shorter transfers" → "We'll minimize layover time"
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
```

> **Why this matters**: Without visibility semantics, NB03 sanitization remains procedural ("don't mention contradictions") instead of structural. The `OwnerConstraint.visibility` field makes the boundary enforceable at the type level. Any renderer that receives a traveler-safe packet can filter out `internal_only` fields by construction.

### Customer Memory

| Field         | Type       | Example                                       | Where                      |
| ------------- | ---------- | --------------------------------------------- | -------------------------- |
| `customer_id` | str        | `"gupta_family"`                              | **facts** — explicit/known |
| `past_trips`  | list[dict] | `[{"dest": "Dubai", "date": "2025-01", ...}]` | **facts** — imported       |

> `is_repeat_customer` is a **derived signal**, not a fact. Computed from `customer_id` presence + CRM lookup. See Derived Signals section.

### Documents & Visa

| Field             | Type           | Example                                                          | Where     |
| ----------------- | -------------- | ---------------------------------------------------------------- | --------- |
| `passport_status` | dict[str, str] | `{"adult_1": "valid_until_2029", "adult_2": "expired_jan_2025"}` | **facts** |
| `visa_status`     | dict           | `{"destination": "Dubai", "requirement": "required", ...}`       | **facts** |

### Existing Plans

| Field                | Type | Example                                                        |
| -------------------- | ---- | -------------------------------------------------------------- |
| `existing_itinerary` | str  | raw itinerary text if customer already has one                 |
| `traveler_plan`      | str  | `"has_flights_booked"`, `"has_hotel_only"`, `"nothing_booked"` |

### Multi-Party / Coordinator (structural, not loose dict)

| Field            | Type                | Example                                  |
| ---------------- | ------------------- | ---------------------------------------- |
| `sub_groups`     | dict[str, SubGroup] | `{"family_a_reddy": SubGroup(...), ...}` |
| `coordinator_id` | Optional[str]       | `"mrs_reddy"`                            |

```python
@dataclass
class SubGroup:
    """A sub-group within a multi-party trip. Structural, not a loose dict blob."""
    group_id: str                   # "family_a_reddy"
    label: str                      # "Reddy family"
    size: int                       # 4
    composition: Dict[str, int]     # {"adults": 2, "children": 2}
    budget_share: Optional[int]     # 300000 (in INR base units)
    payment_status: Literal["not_started", "partial", "paid", "emi_pending"]
    document_status: Literal["not_submitted", "partial", "complete"]
    constraints: List[str]          # ["need ground-floor rooms"]
    contact: Optional[str]          # phone/email for this sub-group
    notes: Optional[str] = None
```

> **Why structural**: `sub_groups` as a generic `dict[str, dict]` gets messy when NB02 needs per-group payment status, per-group document completeness, per-group constraints, per-group contact/authority, per-group budget share. Defining `SubGroup` now keeps NB02/NB03 usable for coordinator-group mode later.

---

## v0.2 Schema: Derived Signals

These are computed from facts. Stored in `CanonicalPacket.derived_signals`. **Nothing here is a fact.**

| Signal                         | Computed From                                         | Example Values                                                             | Purpose                    |
| ------------------------------ | ----------------------------------------------------- | -------------------------------------------------------------------------- | -------------------------- |
| `domestic_or_international`    | `origin_city` + `destination_candidates`              | `"international"`, `"domestic"`, `"mixed"`                                 | Sourcing path hint         |
| `is_repeat_customer`           | `customer_id` presence + CRM lookup stub              | `true`/`false`                                                             | Memory-aware questioning   |
| `sourcing_path`                | destination + budget + origin + owner_constraints     | `"internal_package"`, `"preferred_supplier"`, `"network"`, `"open_market"` | Core agency differentiator |
| `preferred_supplier_available` | destination + budget_tier + internal_packages         | `true`/`false`                                                             | Lead with internal package |
| `estimated_minimum_cost`       | destination_candidates + party_size + trip_style      | `480000` (int)                                                             | Budget feasibility         |
| `budget_feasibility`           | `budget_min`/`budget_max` vs `estimated_minimum_cost` | `"infeasible"`, `"tight"`, `"feasible"`, `"unknown"`                       | Hard rejection signal      |
| `composition_risk`             | `party_composition` + `destination_candidates`        | `"elderly_international_risk"`, `"toddler_longhaul_risk"`, `"none"`        | Suitability flag           |
| `document_risk`                | `passport_status` + `visa_status` + `date_end`        | `"passport_expired_timeline_risk"`, `"none"`                               | Visa/passport blocker      |
| `operational_complexity`       | destination_candidates + duration + party_composition | `"low"`, `"medium"`, `"high"`                                              | Routing complexity         |
| `urgency`                      | `date_end` parsed → days until travel                 | `"high"` (<7d), `"medium"` (<21d), `"low"` (>21d), `"unknown"`             | Suppress soft blockers     |
| `value_gap`                    | `budget_min`/`budget_max` vs `estimated_minimum_cost` | `"under_budget_by_80K"`, `"on_target"`, `"over_budget"`                    | Audit mode signal          |
| `internal_data_present`        | hypotheses + contradictions existence                 | `true`/`false`                                                             | Force internal draft       |
| `booking_readiness`            | composite of docs + payment + supplier confirmation   | `0.0`–`1.0`                                                                | Gate score                 |

### The `ambiguities` list is NOT a derived signal

It is a **top-level list field** on `CanonicalPacket`, parallel to `unknowns` and `contradictions`. Ambiguity is a distinct concept: the field exists but its value is not resolved. Unknown means the field is absent. Contradiction means the field has conflicting values.

```python
@dataclass
class Ambiguity:
    """First-class ambiguity marker — not hidden under unknowns."""
    field_name: str
    ambiguity_type: Literal[
        "unresolved_alternatives",     # "Andaman or Sri Lanka"
        "value_vague",                  # "big family"
        "date_window_only",             # "March or April"
        "budget_unclear_scope",         # "around 2L" — total vs per-person?
        "budget_stretch_present",       # "can stretch if it's good"
        "composition_unclear",          # "3 of them I think"
        "destination_open",             # "somewhere with beaches"
    ]
    raw_value: str
    normalized_value: Optional[str] = None
    confidence: float = 0.0
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    notes: Optional[str] = None
```

---

## Exact NB01 Changes

### Change 1: Add `Ambiguity`, `OwnerConstraint`, `SubGroup` dataclasses

**Location**: Section 1 (Core Domain Models), after `UnknownField`

Three new dataclasses: `Ambiguity` (see above), `OwnerConstraint` (see Agency section), `SubGroup` (see Multi-Party section).

Add `ambiguities` field to `CanonicalPacket`:

```python
ambiguities: List[Ambiguity] = field(default_factory=list)
```

Add method:

```python
def add_ambiguity(self, ambiguity: Ambiguity) -> None:
    self.ambiguities.append(ambiguity)
    self._emit_event("ambiguity_added", {
        "field_name": ambiguity.field_name,
        "ambiguity_type": ambiguity.ambiguity_type,
    })
```

### Change 2: Add top-level `operating_mode` and `schema_version`

**Location**: Section 3 (CanonicalPacket dataclass)

Add to CanonicalPacket top-level fields:

```python
schema_version: str = "v0.2"
operating_mode: str = "normal_intake"
```

Remove any plan to store `intake_mode` inside `facts`. It is `packet.operating_mode` at top level, classified by the intake-mode classifier (Change 9).

### Change 3: Rename legacy fields (v0.1 → v0.2) with structured replacements

**Location**: Everywhere — field mappings, mock LLM, unknowns list, normalizer, tests.

| Old v0.1 Name          | New v0.2 Name(s)                                                                                            | Nature of Change            |
| ---------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------- |
| `destination_city`     | `destination_candidates` (list) + `destination_status`                                                      | Singular → plural + status  |
| `travel_dates`         | `date_window` (str) + `date_start` (opt) + `date_end` (opt) + `date_confidence`                             | String → structured         |
| `budget_range`         | `budget_raw_text` + `budget_min` (opt int) + `budget_max` (opt int) + `budget_flexibility` + `budget_scope` | String → structured numeric |
| `traveler_count`       | `party_size` (int) + `party_composition` (dict)                                                             | Scalar → composition        |
| `traveler_details`     | `passport_status` (dict) + `visa_status` (dict)                                                             | Split                       |
| `traveler_preferences` | `soft_preferences` + `hard_constraints` + `meal_preferences` + `hotel_preferences`                          | Split                       |

**Migration strategy**: NB01 emits v0.2 names only. NB02 gets a `LEGACY_ALIASES` dict for backward compatibility with existing fixtures:

```python
# In NB02 only (NOT in NB01):
LEGACY_ALIASES = {
    "destination_city": "destination_candidates",
    "travel_dates": "date_window",
    "budget_range": "budget_min",       # was "budget_total" — now maps to numeric
    "traveler_count": "party_size",
}
```

### Change 4: Expand `Normalizer` with ambiguity detection + date/budget parsing

**Location**: Section 6 (Normalization Utilities)

#### 4a. Ambiguity pattern detection

```python
class Normalizer:
    # ... existing CITY_NORMALIZATIONS, BUDGET_NORMALIZATIONS ...

    AMBIGUITY_PATTERNS = {
        "unresolved_alternatives": [
            r"\b(\w+)\s+or\s+(\w+)\b",
            r"\beither\s+(.+?)\s+or\s+(.+?)\b",
        ],
        "value_vague": [
            r"\b(?:big|large|huge)\s+family\b",
            r"\bsome\b\s+(?:where|place)",
            r"\baround\b",
            r"\bmaybe\b",
            r"\bthinking\s+about\b",
        ],
        "date_window_only": [
            r"\b(?:around|sometime\s+in|during)\s+",
        ],
        "budget_stretch_present": [
            r"\bcan\s+stretch\b",
            r"\bflexible\b.*budget\b",
            r"\bbudget\s+is\s+flexible\b",
            r"\bif\s+it'?s\s+good\b",
        ],
        "budget_unclear_scope": [
            r"\baround\s+[\d.]+\s*[LlKk]?\b",
            r"\bapprox\.?\b",
        ],
        "composition_unclear": [
            r"\b(?:I\s+think|about|around|roughly)\s+\d+\b",
            r"\b(?:big|large)\s+family\b",
        ],
        "destination_open": [
            r"\bsomewhere\s+(?:with|for|that)\b",
            r"\bany\s+(?:place|destination|where)\b",
        ],
    }

    @classmethod
    def detect_ambiguities(cls, field_name: str, raw_value: str) -> List[Ambiguity]:
        import re
        ambiguities = []
        for amb_type, patterns in cls.AMBIGUITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, raw_value, re.IGNORECASE):
                    ambiguities.append(Ambiguity(
                        field_name=field_name,
                        ambiguity_type=amb_type,
                        raw_value=raw_value,
                        confidence=0.8,
                    ))
                    break
        return ambiguities
```

#### 4b. Budget parser (structured numeric)

```python
    BUDGET_UNITS = {"l": 100000, "k": 1000, "lac": 100000, "lakh": 100000}

    @classmethod
    def parse_budget(cls, raw: str) -> Dict[str, Any]:
        """
        Parse budget text into structured form.
        "4-5L" → {"raw": "4-5L", "min": 400000, "max": 500000, "currency": "INR"}
        "around 2L" → {"raw": "around 2L", "min": None, "max": None, "currency": "INR"}
        "flexible" → {"raw": "flexible", "min": None, "max": None, "currency": "INR"}
        """
        import re
        result = {"raw": raw, "min": None, "max": None, "currency": "INR"}

        # Try range: "4-5L", "4 to 5L", "400K-500K"
        range_match = re.search(
            r"(\d+(?:\.\d+)?)\s*[-–—to]+\s*(\d+(?:\.\d+)?)\s*([LlKk]+)?", raw
        )
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            unit_str = (range_match.group(3) or "").lower()
            multiplier = cls.BUDGET_UNITS.get(unit_str, 1)
            result["min"] = int(low * multiplier)
            result["max"] = int(high * multiplier)
            return result

        # Try single value: "2L", "400000"
        single_match = re.search(r"(\d+(?:\.\d+)?)\s*([LlKk]+)?", raw)
        if single_match:
            val = float(single_match.group(1))
            unit_str = (single_match.group(2) or "").lower()
            multiplier = cls.BUDGET_UNITS.get(unit_str, 1)
            result["min"] = int(val * multiplier)
            result["max"] = int(val * multiplier)
            return result

        # No numeric value extractable
        return result
```

#### 4c. Date parser (structured)

```python
    @classmethod
    def parse_date_window(cls, raw: str) -> Dict[str, Any]:
        """
        Parse date window text into structured form.
        "2026-03-15 to 2026-03-22" → {"start": "2026-03-15", "end": "2026-03-22", "confidence": "exact"}
        "March or April 2026" → {"start": None, "end": None, "confidence": "window"}
        """
        import re
        from datetime import datetime

        result = {"window": raw, "start": None, "end": None, "confidence": "unknown"}

        # Exact ISO range: "2026-03-15 to 2026-03-22"
        iso_range = re.search(
            r"(\d{4}-\d{2}-\d{2})\s+(?:to|–|-)\s+(\d{4}-\d{2}-\d{2})", raw
        )
        if iso_range:
            result["start"] = iso_range.group(1)
            result["end"] = iso_range.group(2)
            result["confidence"] = "exact"
            return result

        # Month window: "March or April 2026", "June-July 2026"
        month_window = re.search(
            r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s*(?:or|[-–—to])\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s+(\d{4})",
            raw, re.IGNORECASE,
        )
        if month_window:
            result["confidence"] = "window"
            return result

        # Fuzzy: "around March 2026", "sometime in May 2026"
        fuzzy = re.search(
            r"(?:around|sometime\s+in|during)\s+((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)\s+(\d{4})",
            raw, re.IGNORECASE,
        )
        if fuzzy:
            result["confidence"] = "flexible"
            return result

        return result
```

### Change 5: Parse budget as structured numeric (not string)

**Location**: Section 7, `_extract_from_freeform`

```python
# Budget detection → structured form
import re
budget_patterns = [
    r"(?:around\s+)?(\d+(?:\.\d+)?\s*[-–—to]+\s*\d+(?:\.\d+)?\s*[LlKk]?)",  # "4-5L"
    r"(?:around\s+)?(\d+(?:\.\d+)?\s*[LlKk])",  # "2L"
    r"(?:budget\s+(?:of\s+)?)?(\d{4,})",  # "400000"
]
for pattern in budget_patterns:
    budget_match = re.search(pattern, text_lower)
    if budget_match:
        raw_budget = budget_match.group(0)
        parsed = Normalizer.parse_budget(raw_budget)
        results["budget_raw_text"] = {
            "value": raw_budget,
            "confidence": 0.8,
            "authority_level": "explicit_user",
            "excerpt": raw_budget,
        }
        if parsed["min"] is not None:
            results["budget_min"] = {
                "value": parsed["min"],
                "confidence": 0.9,
                "authority_level": "explicit_user",
                "excerpt": raw_budget,
            }
        if parsed["max"] is not None:
            results["budget_max"] = {
                "value": parsed["max"],
                "confidence": 0.9,
                "authority_level": "explicit_user",
                "excerpt": raw_budget,
            }
        break

# Budget flexibility
if any(phrase in text_lower for phrase in ["can stretch", "flexible budget", "budget is flexible", "if it's good"]):
    results["budget_flexibility"] = {
        "value": "stretch",
        "confidence": 0.85,
        "authority_level": "explicit_user",
        "excerpt": "...",
    }
```

### Change 6: Parse dates as structured

**Location**: Section 7, `_extract_from_freeform`

```python
# Date detection → structured form
date_patterns = [
    r"(\d{4}-\d{2}-\d{2}\s+(?:to|–|-)\s+\d{4}-\d{2}-\d{2})",  # ISO range
    r"((?:March|April|May|June|July|August|September|October|November|December|January|February)\s*(?:or|[-–—to])\s*(?:March|April|May|June|July|August|September|October|November|December)?\s*\d{4})",  # month window
    r"(around\s+(?:March|April|May|June|July|August|September|October|November|December|January|February)\s+\d{4})",  # fuzzy
]
for pattern in date_patterns:
    date_match = re.search(pattern, text_lower)
    if date_match:
        raw_date = date_match.group(0)
        parsed = Normalizer.parse_date_window(raw_date)
        results["date_window"] = {
            "value": parsed["window"],
            "confidence": 0.8 if parsed["confidence"] != "exact" else 0.95,
            "authority_level": "explicit_user",
            "excerpt": raw_date,
        }
        if parsed["start"]:
            results["date_start"] = {
                "value": parsed["start"],
                "confidence": 0.95,
                "authority_level": "explicit_user",
                "excerpt": raw_date,
            }
        if parsed["end"]:
            results["date_end"] = {
                "value": parsed["end"],
                "confidence": 0.95,
                "authority_level": "explicit_user",
                "excerpt": raw_date,
            }
        results["date_confidence"] = {
            "value": parsed["confidence"],
            "confidence": 0.9,
            "authority_level": "derived_signal",
            "excerpt": "Derived from date_window parsing",
        }
        break
```

### Change 7: Parse party composition (not just count)

**Location**: Section 7, `_extract_from_freeform`

```python
# Party composition
composition = {}
adult_match = re.search(r"(\d+)\s+adults?", text_lower)
if adult_match:
    composition["adults"] = int(adult_match.group(1))
child_match = re.search(r"(\d+)\s+(?:kids?|children?|child|toddlers?|infants?)", text_lower)
if child_match:
    composition["children"] = int(child_match.group(1))
    # Extract child ages if present: "kids ages 8 and 12"
    ages_match = re.search(r"(?:kids?|children?|child|ages?)\s+(?:ages?\s+)?(\d+(?:\s+and\s+\d+|\d+\s*,\s*\d+)?)", text_lower)
    if ages_match:
        ages = [int(a) for a in re.findall(r"\d+", ages_match.group(1))]
        results["child_ages"] = {
            "value": ages,
            "confidence": 0.9,
            "authority_level": "explicit_user",
            "excerpt": ages_match.group(0),
        }
elderly_match = re.search(r"(\d+)\s+(?:elderly|seniors?|parents?|grandparents?)", text_lower)
if elderly_match:
    composition["elderly"] = int(elderly_match.group(1))

# Generic size fallback: "5 people", "family of 5"
if not composition:
    size_match = re.search(r"(?:family\s+(?:of\s+)?|group\s+(?:of\s+)?|(\d+)\s+(?:people|persons|pax|travelers))", text_lower)
    if size_match:
        size = int(size_match.group(1) or size_match.group(0))
        results["party_size"] = {
            "value": size,
            "confidence": 0.7,
            "authority_level": "explicit_user",
            "excerpt": size_match.group(0),
        }

if composition:
    results["party_composition"] = {
        "value": composition,
        "confidence": 0.85,
        "authority_level": "explicit_user",
        "excerpt": "...",
    }
    results["party_size"] = {
        "value": sum(composition.values()),
        "confidence": 0.9,
        "authority_level": "derived_signal",
        "extraction_mode": "derived",
        "excerpt": "Sum of composition",
    }
```

### Change 8: Owner context with visibility semantics

**Location**: Section 7, `_extract_from_freeform`

```python
# Owner constraints — with visibility classification
owner_constraint_matches = []
if "never " in text_lower or "don't book" in text_lower or "avoid " in text_lower:
    # Internal-only: these are agency rules, not traveler preferences
    owner_constraint_matches.append({
        "text": constraint_text,
        "visibility": "internal_only",
    })

if "family prefers" in text_lower or "they like" in text_lower or "they always" in text_lower:
    # May be traveler_safe_transformable
    owner_constraint_matches.append({
        "text": constraint_text,
        "visibility": "traveler_safe_transformable",
    })

if owner_constraint_matches:
    results["owner_constraints"] = {
        "value": owner_constraint_matches,
        "confidence": 0.9,
        "authority_level": "explicit_owner",
        "excerpt": "...",
    }

# Agency notes — historical context
if any(phrase in text_lower for phrase in ["past customer", "they've been", "previously", "last time"]):
    results["agency_notes"] = {
        "value": context_text,
        "confidence": 0.8,
        "authority_level": "explicit_owner",
        "excerpt": "...",
    }
```

### Change 9: Repeat-customer hooks (fact vs derived, not both)

**Location**: Section 3 (CanonicalPacket) + Section 7 (extraction)

`CanonicalPacket` gains `customer_id` and `past_trips` as fact fields (set via `set_fact()`). `is_repeat_customer` is computed ONLY as a derived signal.

```python
def _check_repeat_customer(self, text: str, envelope: SourceEnvelope) -> Optional[str]:
    """
    Stub for CRM lookup. Returns customer_id if detected, None otherwise.
    In production, matches phone/email to customer database.
    """
    if any(phrase in text.lower() for phrase in ["they've been to", "previously went", "last time they", "past trip"]):
        return "detected_repeat_customer"  # stub ID
    return None
```

After extraction, if `customer_id` is set:

```python
if "customer_id" in packet.facts:
    packet.set_derived_signal("is_repeat_customer", Slot(
        value=True,
        confidence=0.8,
        authority_level="derived_signal",
        extraction_mode="derived",
        evidence_refs=[EvidenceRef(
            ref_id=f"ref_{uuid.uuid4().hex[:6]}",
            envelope_id="derived",
            evidence_type="derived",
            excerpt="customer_id detected in input",
        )],
    ))
```

### Change 10: Multi-party extraction with `SubGroup` structure

**Location**: Section 7, `_extract_from_freeform`

```python
def _extract_sub_groups(self, text: str, envelope_id: str) -> Dict[str, SubGroup]:
    """
    Extract sub-group information for multi-party/coordinator scenarios.
    For prototype, detects explicit multi-family signals and creates minimal SubGroups.
    """
    sub_groups = {}
    # Detect patterns like "Family A: 4 people, 3L budget"
    family_pattern = re.findall(
        r"(family\s+\w+)\s*[:;]?\s*(\d+)\s*(?:people|persons|pax)(?:.*?budget.*?(\d+[LKk]+))?",
        text, re.IGNORECASE,
    )
    for label, size, budget in family_pattern:
        group_id = label.lower().replace(" ", "_")
        budget_int = None
        if budget:
            parsed = Normalizer.parse_budget(budget)
            budget_int = parsed.get("min") or parsed.get("max")
        sub_groups[group_id] = SubGroup(
            group_id=group_id,
            label=label,
            size=int(size),
            composition={},
            budget_share=budget_int,
            payment_status="not_started",
            document_status="not_submitted",
            constraints=[],
            contact=None,
        )

    return sub_groups
```

### Change 11: Add `operating_mode` classifier (top-level, not in facts)

**Location**: Section 7, `extract()` method

```python
def _classify_operating_mode(self, envelopes: List[SourceEnvelope]) -> str:
    """
    Determine operating mode from input characteristics.
    Sets top-level packet.operating_mode, NOT a fact slot.
    """
    for env in envelopes:
        text = ""
        if isinstance(env.content, str):
            text = env.content.lower()
        elif isinstance(env.content, dict):
            text = str(env.content).lower()

        if any(kw in text for kw in ["emergency", "urgent", "medical", "hospital", "evacuate"]):
            return "emergency"
        if any(kw in text for kw in ["cancel", "cancellation", "refund"]):
            return "cancellation"
        if any(kw in text for kw in ["review quote", "check this quote", "audit", "what did we send"]):
            return "audit"
        if any(kw in text for kw in ["follow up", "no response", "ghost", "not responding"]):
            return "follow_up"
        if any(kw in text for kw in ["post trip", "how was", "feedback", "review request"]):
            return "post_trip"
        if any(kw in text for kw in ["owner review", "quote disaster", "margin erosion"]):
            return "owner_review"
        if any(kw in text for kw in ["coordinat", "3 families", "multiple families"]):
            return "coordinator_group"

    return "normal_intake"
```

Set on packet:

```python
packet.operating_mode = self._classify_operating_mode(envelopes)
```

### Change 12: Expand `_compute_derived_signals` for v0.2

**Location**: Section 7

Keep existing `trip_type` and `group_type` logic (updated to v0.2 field names). Add:

```python
    def _compute_derived_signals(self, packet: CanonicalPacket) -> None:
        # === EXISTING (updated to v0.2 names) ===
        # trip_type: domestic_or_international
        # group_type: from party_composition

        # === NEW: domestic_or_international ===
        if "destination_candidates" in packet.facts and "origin_city" in packet.facts:
            dests = packet.facts["destination_candidates"].value
            origin = packet.facts["origin_city"].value
            # Simple heuristic — will be enriched with real destination database
            international = ["Japan", "Paris", "Tokyo", "London", "New York", "Singapore", "Thailand", "Dubai", "Maldives", "Europe"]
            if isinstance(dests, list):
                all_domestic = all(d not in international for d in dests)
                all_intl = all(d in international for d in dests)
                signal = "domestic" if all_domestic else ("international" if all_intl else "mixed")
            else:
                signal = "international" if dests in international else "domestic"

            packet.set_derived_signal("domestic_or_international", Slot(
                value=signal, confidence=0.9, authority_level="derived_signal",
                extraction_mode="derived",
                evidence_refs=[EvidenceRef(
                    ref_id=f"ref_{uuid.uuid4().hex[:6]}", envelope_id="derived",
                    evidence_type="derived",
                    excerpt=f"Computed from destination_candidates={dests}, origin={origin}",
                )],
            ))

        # === NEW: is_repeat_customer (derived ONLY, not in facts) ===
        if "customer_id" in packet.facts:
            packet.set_derived_signal("is_repeat_customer", Slot(
                value=True, confidence=0.8, authority_level="derived_signal",
                extraction_mode="derived",
                evidence_refs=[EvidenceRef(
                    ref_id=f"ref_{uuid.uuid4().hex[:6]}", envelope_id="derived",
                    evidence_type="derived",
                    excerpt="customer_id present in facts",
                )],
            ))

        # === NEW: urgency (from date_end) ===
        if "date_end" in packet.facts:
            urgency = self._parse_urgency(packet.facts["date_end"].value)
            if urgency:
                packet.set_derived_signal("urgency", Slot(
                    value=urgency["level"],
                    confidence=urgency["confidence"],
                    authority_level="derived_signal",
                    extraction_mode="derived",
                    evidence_refs=[EvidenceRef(
                        ref_id=f"ref_{uuid.uuid4().hex[:6]}", envelope_id="derived",
                        evidence_type="derived",
                        excerpt=f"Computed from date_end={packet.facts['date_end'].value}",
                    )],
                    notes=urgency.get("notes", ""),
                ))

        # === NEW: internal_data_present ===
        if packet.hypotheses or packet.contradictions:
            packet.set_derived_signal("internal_data_present", Slot(
                value=True, confidence=1.0, authority_level="derived_signal",
                extraction_mode="derived",
            ))

        # === NEW: sourcing_path (stub) ===
        if "destination_candidates" in packet.facts:
            # Stub — will be enriched with real supplier data
            default_path = "open_market"
            if packet.facts.get("owner_constraints"):
                default_path = "network"  # owner has opinions → has network
            packet.set_derived_signal("sourcing_path", Slot(
                value=default_path, confidence=0.5, authority_level="derived_signal",
                extraction_mode="derived",
                notes="Stub — enrich with internal package lookup and preferred supplier data",
            ))
```

### Change 13: Add schema validation at end of NB01

**Location**: New Section 8 (after extraction pipeline), new Section 9 (tests)

```python
@dataclass
class PacketValidationReport:
    """Result of validating a CanonicalPacket against v0.2 schema."""
    is_valid: bool
    missing_canonical_slots: List[str]
    ambiguity_report: List[Dict[str, Any]]
    evidence_coverage: Dict[str, int]
    legacy_alias_warnings: List[str]
    warnings: List[str]

def validate_packet(packet: CanonicalPacket, stage: str = "discovery") -> PacketValidationReport:
    """
    Validate a CanonicalPacket against v0.2 schema.
    Every NB01 run should end with this check.
    """
    missing = []
    legacy_warnings = []
    warnings = []

    # Stage-appropriate MVB fields
    discovery_mvb = [
        "destination_candidates", "origin_city", "date_window",
        "party_size", "budget_raw_text", "trip_purpose",
    ]
    for f in discovery_mvb:
        if f not in packet.facts:
            missing.append(f)

    # Check for legacy field names (migration guard)
    legacy_names = ["destination_city", "travel_dates", "budget_range", "traveler_count"]
    for name in legacy_names:
        if name in packet.facts:
            legacy_warnings.append(f"Legacy field '{name}' found — migrate to v0.2 name")

    # Verify no facts contain derived-signal-only fields
    derived_only_in_facts = ["is_repeat_customer", "domestic_or_international", "urgency", "budget_feasibility", "sourcing_path"]
    for name in derived_only_in_facts:
        if name in packet.facts:
            warnings.append(f"Field '{name}' should be a derived signal, not a fact")

    # Ambiguity coverage
    ambiguity_report = [{"field": a.field_name, "type": a.ambiguity_type, "raw_value": a.raw_value} for a in packet.ambiguities]

    # Evidence coverage
    evidence_coverage = {k: len(v.evidence_refs) for k, v in packet.facts.items()}

    is_valid = len(missing) == 0 and len(legacy_warnings) == 0

    return PacketValidationReport(
        is_valid=is_valid,
        missing_canonical_slots=missing,
        ambiguity_report=ambiguity_report,
        evidence_coverage=evidence_coverage,
        legacy_alias_warnings=legacy_warnings,
        warnings=warnings,
    )
```

### Change 14: Split the monolith cell

**Location**: NB01 notebook structure

| Cell | Content                                                                                                                                   |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Markdown header: "Notebook 01: Intake and Normalization v0.2"                                                                             |
| 2    | Core domain models: `AuthorityLevel`, `EvidenceRef`, `ExtractionMode`, `Slot`, `UnknownField`, `Ambiguity`, `OwnerConstraint`, `SubGroup` |
| 3    | Source Envelope: `SourceEnvelope`                                                                                                         |
| 4    | Canonical Packet: `CanonicalPacket` with v0.2 top-level fields                                                                            |
| 5    | Conflict Resolution: `ConflictResolutionPolicy`                                                                                           |
| 6    | Source Adapter: `SourceAdapter`                                                                                                           |
| 7    | Normalization Utilities: `Normalizer` with ambiguity detection, budget parser, date parser                                                |
| 8    | Operating Mode Classifier: `_classify_operating_mode`                                                                                     |
| 9    | Extraction Pipeline: `ExtractionPipeline` with v0.2 rules                                                                                 |
| 10   | Derived Signals: `_compute_derived_signals` v0.2                                                                                          |
| 11   | Schema Validation: `validate_packet`                                                                                                      |
| 12   | Test Suite: Assertion-based tests                                                                                                         |

---

## Tests to Add (NB01-specific)

Replace the 5 print-tests with assertion-based tests:

| #   | Test                                          | What It Validates                                                                                                                                            |
| --- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Freeform + ambiguity                          | "Andaman or Sri Lanka" → `destination_candidates=["Andaman","Sri Lanka"]`, `destination_status="semi_open"`, `ambiguity` with type `unresolved_alternatives` |
| 2   | Structured budget                             | "around 4-5L, can stretch" → `budget_min=400000`, `budget_max=500000`, `budget_flexibility="stretch"`, `ambiguity` type `budget_stretch_present`             |
| 3   | Structured dates                              | "2026-03-15 to 2026-03-22" → `date_start="2026-03-15"`, `date_end="2026-03-22"`, `date_confidence="exact"`                                                   |
| 4   | Party composition                             | "2 adults, 2 kids ages 8 and 12, 1 elderly" → `party_composition`, `child_ages=[8,12]`, `party_size=5` derived                                               |
| 5   | Owner constraints + visibility                | "never use Hotel X" → `owner_constraints` with `visibility="internal_only"`                                                                                  |
| 6   | Repeat customer (fact vs derived)             | "past customer, Singapore 2024" → `customer_id` in facts, `is_repeat_customer` ONLY in derived_signals                                                       |
| 7   | Multi-party structure                         | "3 families, different budgets" → `sub_groups` with `SubGroup` objects                                                                                       |
| 8   | Operating mode (top-level)                    | "medical emergency in Singapore" → `packet.operating_mode="emergency"`, NOT in facts                                                                         |
| 9   | Urgency from date_end                         | "2026-03-15" (7 days from now) → `urgency="high"` derived signal                                                                                             |
| 10  | Schema validation                             | Packet missing `date_window` → validation report lists it                                                                                                    |
| 11  | Legacy field rejection                        | Packet with `destination_city` in facts → validation warning                                                                                                 |
| 12  | Derived-only fields not in facts              | `is_repeat_customer` never appears in `packet.facts`                                                                                                         |
| 13  | Destination candidates → downstream readiness | `destination_candidates` list is valid for discovery; `resolved_destination` is NOT set by NB01                                                              |

---

## Tri-Contract Lock: Schema + NB02 + NB03

**Do not update NB01 in isolation.** The following three artifacts must be updated together in one pass:

1. **`canonical_packet.schema.json` v0.2** — the single source of truth for all field names, types, and constraints
2. **NB02 field dictionary and blocker vocabulary** — updated MVB fields using v0.2 names, `LEGACY_ALIASES` for backward compat, ambiguity-aware blocker engine
3. **NB03 accepted input shape and sanitization rules** — uses `operating_mode` to select strategy builder, uses `visibility` to filter owner fields from traveler-safe output

The shared vocabulary:

| v0.2 Field                  | NB01 Emits                 | NB02 Consumes                            | NB03 Consumes                     |
| --------------------------- | -------------------------- | ---------------------------------------- | --------------------------------- |
| `destination_candidates`    | ✅ (list)                  | Hard blocker if empty/undecided          | Questions use candidates list     |
| `date_start` / `date_end`   | ✅ (opt ISO str)           | Urgency, visa timeline risk              | Date-aware framing                |
| `budget_min` / `budget_max` | ✅ (opt int)               | Feasibility, branch logic                | Budget-appropriate options        |
| `party_composition`         | ✅ (dict)                  | Suitability risk, sourcing               | Composition-aware questions       |
| `operating_mode`            | ✅ (top-level str)         | Judgment routing, mode-specific blockers | Strategy builder selection        |
| `owner_constraints`         | ✅ (list[OwnerConstraint]) | Risk flag: constraint violation          | Filtered by visibility            |
| `ambiguities`               | ✅ (list[Ambiguity])       | New blocker class: ambiguous ≠ missing   | Clarification question generation |
| `sub_groups`                | ✅ (dict[str, SubGroup])   | Per-group readiness check                | Coordinator-aware prompts         |
| `is_repeat_customer`        | — (derived only)           | Memory-aware questioning                 | History-aware framing             |
| `sourcing_path`             | — (derived only)           | Routing: which supplier tier             | Sourcing-aware proposal           |
| `budget_feasibility`        | — (derived only)           | Hard rejection if infeasible             | Reality-check framing             |
| `urgency`                   | — (derived only)           | Suppress soft blockers if high           | Speed-first question ordering     |

---

_This spec is the contract for NB01 v0.2. It incorporates all 7 review corrections. Once implemented alongside the NB02 and NB03 contract updates, NB01 is the agency-OS intake engine, not a generic trip planner._
