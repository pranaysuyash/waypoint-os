# Pipeline Stage Data Scope Review

**Date**: 2026-06-26  
**Source**: [TRAVEL_AGENCY_TODO.md](../TRAVEL_AGENCY_TODO.md) — Architecture TODOs  
**Status**: ✅ Complete  

---

## 1. Executive Summary

The Waypoint OS pipeline currently defines **4 production stages** (`discovery` → `shortlist` → `proposal` → `booking`) with a 4-tier readiness model (`intake_minimum` → `quote_ready` → `proposal_ready` → `booking_ready`). However, the data flowing through each stage has accumulated organically — fields intended for later stages (passport numbers, legal names, payer details) sit in the same JSON blobs as intake fields.

**The core design principle**: *Park full people management until later stages. Don't jam it into Intake.* The Intake stage should capture only lightweight trip intent — who's roughly going, where, when, budget. The full traveler roster (legal names, passport numbers, DOB, relationships) belongs in the Booking stage. Medical info, emergency contacts, and document ownership belong in the Pre-trip/Output stage.

This review audits each stage, defines its data scope, identifies scope violations, and provides a migration path.

---

## 2. The Four Production Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE STAGE FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │  DISCOVERY   │───▶│  SHORTLIST   │───▶│  PROPOSAL    │───▶│  BOOKING  │  │
│  │  (Intake)    │    │  (Options)   │    │  (Quote)     │    │  (Book)   │  │
│  └─────────────┘    └──────────────┘    └──────────────┘    └───────────┘  │
│        │                  │                   │                  │          │
│        ▼                  ▼                   ▼                  ▼          │
│  Lightweight intent   Destinations +     Full proposal +    Legal names +  │
│  (rough who/where/    options brief      pricing + safety   passport + DOB │
│  when/budget)                                               + payer + EMI  │
│                                                                             │
│  READINESS TIER:     READINESS TIER:    READINESS TIER:     READINESS TIER:│
│  intake_minimum      quote_ready        proposal_ready      booking_ready  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Stage Map (code evidence)

From `spine_api/services/trip_lifecycle_service.py`:
```python
VALID_STAGES = {"discovery", "shortlist", "proposal", "booking"}
```

From `src/intake/readiness.py`:
```python
TIER_STAGE_MAP: Dict[ReadinessTier, str] = {
    "intake_minimum": "discovery",
    "quote_ready": "shortlist",
    "proposal_ready": "proposal",
    "booking_ready": "booking",
}
```

---

## 3. Stage-by-Stage Data Scope

### 3.1 Discovery (Intake) Stage

**Purpose**: Capture lightweight trip intent — enough to save a trip and start planning.

**Minimum required fields** (from `src/intake/validation.py`):
```python
INTAKE_MINIMUM = [
    "destination_candidates",
    "date_window",
]
```

**Full "quote-ready" fields** (the 6-field MVB that unlocks shortlist):
```python
QUOTE_READY = [
    "destination_candidates",   # Where
    "origin_city",              # From where
    "date_window",              # When (rough)
    "party_size",               # How many people (rough count)
    "budget_raw_text",          # Budget (original text, may be rough)
    "trip_purpose",             # Why (leisure, business, family, etc.)
]
```

**Additional structured fields stored at intake** (from `spine_api/models/trips.py`):
| Field | Type | Purpose |
|-------|------|---------|
| `party_composition` | Optional[str] | Rough composition description ("2 adults, 1 child") |
| `pace_preference` | Optional[str] | Preferred pace (relaxed, balanced, packed) |
| `lead_source` | Optional[str] | How the lead came in (WhatsApp, referral, website) |
| `activity_provenance` | Optional[str] | What triggered this trip |
| `date_year_confidence` | Optional[str] | Confidence in date/year accuracy |
| `trip_priorities` | Optional[str] | Must-haves and preferences |
| `date_flexibility` | Optional[str] | How rigid the dates are |
| `follow_up_due_date` | Optional[datetime] | When to follow up |

**Design principle**: Intake captures only **trip-level intent**, never traveler-level identity. Field names and values are **semantic** (e.g., `"family of 4"` not `["Pranay, age 42, passport X123", "Riya, age 38, passport Y456"]`).

**✅ In scope**: destination, origin, dates, party size (count), budget (rough text), purpose, preferences, pace, lead source  
**❌ Out of scope** (stays out of Intake): legal names, passport numbers, DOB, relationships, payer details, medical info, emergency contacts

---

### 3.2 Shortlist (Options) Stage

**Purpose**: Generate and narrow down options for the traveler.

**Additional data entering at this stage**:
- Options brief / strategy document (generated by the system)
- Destination candidates narrowed to preferred options
- Option pricing estimates (per option, not final)
- Session strategy with follow-up questions
- Derived signals: budget_feasibility, sourcing_path, preferred_supplier_available

**Stored in**:
```python
# From Trip model
strategy: Optional[dict]  # Strategy document with options
extracted: dict           # Contains derived signals
validation: dict          # Validation results
```

**✅ In scope**: Options brief, pricing estimates, session strategy, derived signals  
**❌ Out of scope**: Legal traveler identities, booking commitments, payments

---

### 3.3 Proposal Stage

**Purpose**: Generate a complete, priced proposal ready for the traveler.

**Additional data entering at this stage**:
- `traveler_bundle` — Traveler-facing proposal document
- `internal_bundle` — Internal-facing operations document
- `fees` — Fee structure and breakdown
- `safety` — Safety and leakage assessment
- `decision` — Decision state and blockers

**Stored in**:
```python
# From Trip model
traveler_bundle: Optional[dict]  # Traveler-facing proposal
internal_bundle: Optional[dict]  # Internal ops document
fees: Optional[dict]             # Fee structure
safety: dict                     # Safety/leakage result
decision: dict                   # Decision with blockers
```

**Readiness check** (from `src/intake/readiness.py`):
```python
PROPOSAL_READY_DELTA = [
    "trip_priorities",      # Must-haves / preferences
    "date_flexibility",     # How rigid are the dates
]
# Plus pipeline outputs: traveler_bundle, internal_bundle, fees, safety pass, no critical blockers
```

**✅ In scope**: Proposal documents, pricing breakdown, safety assessment, fee structure  
**❌ Out of scope**: Actual booking data (legal names, passports), payments

---

### 3.4 Booking Stage

**Purpose**: Collect PII, legal information, and payment details to execute the booking.

**This is where full people management happens.**

**Booking data schema** (from `spine_api/routers/public_collection.py`):
```python
class BookingTravelerModel(BaseModel):
    traveler_id: str
    full_name: str
    date_of_birth: str
    passport_number: Optional[str] = None
    passport_expiry: Optional[str] = None
    nationality: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    special_requirements: Optional[str] = None

class BookingPayerModel(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None

class BookingDataModel(BaseModel):
    travelers: List[BookingTravelerModel]
    payer: Optional[BookingPayerModel] = None
    payment_method: Optional[str] = None
    payment_tracking: Optional[dict] = None
```

**Additional booking stage data**:
- `pending_booking_data` — Customer-submitted booking data (encrypted)
- `booking_data` — Agency-approved booking data (encrypted)
- `booking_data_source` — How booking data was captured
- `booking_documents` — Uploaded documents (passport scans, visa docs)
- `booking_tasks` — Generated booking tasks
- `booking_collection_tokens` — Public collection tokens for customer data submission
- `payment_queue_items` — Payment tracking records

**Stored encrypted** (from `alembic/versions/add_booking_collection.py`):
```python
pending_booking_data: Optional[dict]  # Encrypted at rest
booking_data: Optional[dict]          # Encrypted at rest
```

**Readiness check** (from `src/intake/readiness.py`):
```python
# Booking-ready requires booking_data with semantic minimum:
# - travelers list non-empty
# - every traveler has traveler_id, full_name, date_of_birth
# - payer present with name
# - passport details optional (destination-specific rules coming)
```

**✅ In scope**: Full traveler roster with legal names, DOB, passport numbers, nationality, contact info, payer details, payment method, EMI structure, document uploads  
**Encrypted at rest**: Yes — `booking_data` and `pending_booking_data` are blob-encrypted  
**❌ Out of scope**: Medical info, emergency contacts, visa document ownership — these belong in Pre-trip/Output

---

### 3.5 Pre-Trip / Output Stage (Future — Not Yet a Separate Stage)

**Purpose**: Post-booking readiness for actual travel — emergency contacts, medical info, document ownership, traveler communications.

**Note**: This is NOT yet a separate stage in the pipeline. Booking is currently the terminal stage. These fields are aspirational — they need schema and stage additions.

**Data that will belong here**:
| Field | Type | Notes |
|-------|------|-------|
| Emergency contacts | Per-traveler | Names, phone numbers, relationship |
| Medical info | Per-traveler | Allergies, conditions, medications |
| Document ownership | Per-traveler, per-document | Who holds which visa, passport, ticket |
| Traveler-facing itinerary | Document | Ready-to-share trip document |
| Insurance details | Per-trip | Policy number, coverage, contacts |
| Post-trip survey | Per-trip | Satisfaction, NPS |
| Travel alerts | Per-trip | Active disruption monitoring |

**Current gaps**:
- No separate stage code for pre-trip/output
- Emergency contact and medical info fields don't exist in any schema
- Document ownership is tracked at trip-level, not traveler-level

---

## 4. Scope Boundary Rules

### Rule 1: Intake Has No Individual Identity

```
❌ NEVER in Intake:
   "travelers": [
     {"name": "Pranay Singh", "age": 42, "passport": "X1234567"},
     {"name": "Riya Singh", "age": 38, "passport": "Y7890123"}
   ]

✅ ALWAYS in Intake:
   "party_size": 2
   "party_composition": "2 adults"
   "trip_purpose": "family vacation"
```

**Rationale**: Travelers don't expect to provide passport numbers before they've seen a proposal. Asking for PII at intake creates friction, reduces conversion, and increases data liability for trips that never convert.

### Rule 2: Booking Data Is the PII Boundary

All personally identifiable information (legal names, passport numbers, DOB) enters through the **Booking stage only** — either via:
- **Public collection** (customer-facing form via tokenized link, `POST /api/public-booking/submit`)
- **Agency entry** (operator enters on behalf of customer)

**Encryption boundary**: `booking_data` and `pending_booking_data` are encrypted at rest (`SQLTripStore._encrypt_field_for_storage`). No other trip fields are encrypted.

### Rule 3: Medical + Emergency Data Belongs Post-Booking

Medical conditions, allergies, emergency contacts, and dietary requirements are **traveler-level data** that should only be collected after booking is committed. The current system has some of these blended into `special_requirements` in the booking stage — these should migrate to a dedicated pre-trip data model.

### Rule 4: Financial Allocation Belongs at Payment Stage

Payment structure (who pays what share, EMI plans, payment tracking, commission splits) belongs in the Payment stage, which starts at booking but may extend through the trip lifecycle. The current `payment_queue` and `payment_tracking` models live in the booking data JSON, which is acceptable for v0 but should be normalized into a dedicated payment schema.

---

## 5. Current Scope Violations (Deferred Debt)

| Violation | Location | Impact | Fix |
|-----------|----------|--------|-----|
| `booking_data` is a single JSON blob | `spine_api/models/trips.py:64-66` | No schema validation at DB level | Normalize into `booking_travelers`, `booking_payer`, `booking_payment` tables |
| `special_requirements` in booking data | `BookingTravelerModel` | Medical info (post-booking) mixed with booking time data | Move medical info to pre-trip model when stage is added |
| `pending_booking_data` is encrypted but not versioned | `alembic/versions/add_booking_collection.py` | Schema migrations on encrypted data are difficult | Add `booking_data_schema_version` field |
| `fees` is a JSON blob with no schema | `spine_api/models/trips.py` | Frontend has to guess the shape | Add `FeeBreakdown` Pydantic model to contract |
| No separate payment stage | Implicit | Payment tracking mixed into booking data | Add `payment` stage to `VALID_STAGES` |
| No pre-trip/output stage | Implicit | No place for emergency contacts, medical info, document ownership | Add `pre_trip` stage to `VALID_STAGES` |
| `raw_input` stores owner notes and structured overlay | `spine_api/models/trips.py:73` | Overlay may contain operator-entered PII before booking stage | Ensure `raw_input` is not served to unauthorized consumers |

---

## 6. Implementation Recommendations

### Immediate (No Schema Change)

1. **Document the scope rules** in `AGENTS.md` and team onboarding — this is done in this document
2. **Audit existing trips** for booking data that leaked into `extracted` or `raw_input` fields before the Booking stage
3. **Add `booking_data_schema_version` field** to enable future schema migrations on encrypted data

### Short-Term (Add Schemas, No Migration)

4. **Add `FeeBreakdown` Pydantic model** to `spine_api/contract.py` so the frontend has a contract for fee data
5. **Add `pre_trip` and `payment` stages** to `VALID_STAGES` in `spine_api/services/trip_lifecycle_service.py`
6. **Create `PreTripData` Pydantic model** with emergency contacts, medical info, document ownership fields

### Medium-Term (Normalize Booking Data)

7. **Normalize `booking_data` into relational tables**: `booking_travelers`, `booking_payer`, `booking_payment`
8. **Migrate `pending_booking_data` into `booking_travelers` with `status='pending'` flag**
9. **Add traveler-level document tracking**: which traveler holds which passport/visa/ticket
10. **Add per-traveler payment allocation**: who pays what share in a group trip

### Long-Term (Payment + Pre-Trip Stages)

11. **Implement Payment stage** — payment tracking, EMI management, reconciliation
12. **Implement Pre-Trip stage** — emergency contacts, medical info, document readiness, traveler-facing itinerary
13. **Add stage-based data access controls** — later-stage fields are not accessible from earlier-stage API endpoints

---

## 7. Summary Table

| Data Category | Discovery | Shortlist | Proposal | Booking | Pre-Trip | Payment |
|---|---|---|---|---|---|---|
| Destination | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dates (rough) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Party size (count) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Budget (rough) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trip purpose | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Preferences | 🟡 Optional | ✅ | ✅ | ✅ | ✅ | ✅ |
| Options brief | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pricing estimates | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safety assessment | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Traveler bundle | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Legal names** | ❌ | ❌ | ❌ | **✅** | ✅ | ✅ |
| **Passport numbers** | ❌ | ❌ | ❌ | **✅** | ✅ | ✅ |
| **Date of birth** | ❌ | ❌ | ❌ | **✅** | ✅ | ✅ |
| Payer details | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Document uploads | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Emergency contacts | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Medical info | ❌ | ❌ | ❌ | 🟡 Special reqs | ✅ | ❌ |
| Payment tracking | ❌ | ❌ | ❌ | 🟡 Via booking | ❌ | ✅ |
| EMI structure | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Commission splits | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

**Legend**: ✅ In scope | 🟡 Partial/optional | ❌ Not in scope | **✅ Bold** = PII boundary

---

## 8. Key Files Referenced

| File | What It Defines |
|------|----------------|
| `spine_api/services/trip_lifecycle_service.py` | `VALID_STAGES`, stage transitions, reassessment |
| `src/intake/readiness.py` | Readiness tiers, tier→stage map, field requirements per tier |
| `src/intake/validation.py` | `INTAKE_MINIMUM`, `QUOTE_READY`, validation rules |
| `src/intake/constants.py` | `PipelineStage`, `GateIdentifier`, `DecisionState` |
| `src/intake/packet_models.py` | `CanonicalPacket`, `Slot`, authority levels, lifecycle models |
| `spine_api/models/trips.py` | `Trip` SQLAlchemy model with all DB columns |
| `spine_api/contract.py` | `TripPatchRequest`, `TripResponse`, `BookingDataModel` |
| `spine_api/routers/public_collection.py` | `BookingTravelerModel`, `BookingPayerModel`, public submission |
| `spine_api/services/payment_queue_service.py` | Payment queue, payment tracking |
| `spine_api/services/booking_task_service.py` | Booking task generation from booking data |
| `spine_api/services/extraction_service.py` | Extraction-to-booking-data field application |
| `alembic/versions/add_booking_data_to_trips.py` | DB migration: booking_data column |
| `alembic/versions/add_booking_collection.py` | DB migration: pending_booking_data, booking_data_source, encryption |
| `tests/test_booking_collection.py` | Booking data encryption round-trip tests |
| `tests/test_booking_data.py` | Booking data encryption and readiness tests |
| `tests/test_extraction_events.py` | Proves booking_data NOT mutated by extraction events |
