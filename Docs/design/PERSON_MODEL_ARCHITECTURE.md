# Person Model & Relationship Architecture

**Status**: Design Proposal — v2 (Edges + Graph-Readable)
**Date**: 2026-05-05
**Authors**: Architecture Discussion (session notes)
**Revision History**:

| Date | Version | Change |
|---|---|---|
| 2026-05-05 | v1 | Initial relational model (persons + person_relationships + trip_person) |
| 2026-05-05 | v2 | Replaced typed junction tables with polymorphic edges table after pushback: "these queries are graph problems, not SQL join problems" |

---

## 1. The Problem

### Current State

The system has no durable person/customer entity. Today:

- `customerName` in the inbox is derived from unstructured trip text via `_derive_customer_name()` at `inbox_projection.py:250-259`, a cascade of blind JSON path guesses through nested trip blobs
- `customer_id` exists as a bare `Optional[str]` field slot in `LifecycleInfo` at `packet_models.py:214-236` — no FK, no table, no constraints
- `customers:read` / `customers:write` permission strings are defined in `auth.py:163-175` but are dead code — no routes to gate
- Repeat customer detection is keyword-based: checks for words like `"past"`, `"previous"`, `"repeat"`, `"returning"`, `"last time"` in agent notes at `extractors.py:1835-1850`
- The scoring functions at `decision.py:1509-1625` (churn risk, retention risk, etc.) are mathematically correct but always return `0.0` in production because `LifecycleInfo` is never populated from real data

In short: **people are ghosts in the system**. They appear in agent notes, in JSON blobs, in email fields — but there is no durable record of who they are, what they've done, or how they're connected.

### Why This Matters Now

- Every enquiry creates a new "person" — the system cannot distinguish a first-time caller from a repeat customer
- Referrals are invisible — if Person A sends Person B, there's no link, no attribution, no network effect
- Emergency contacts are stored as unstructured text — unreachable in a crisis
- A single person playing multiple roles (SPOC on one trip, traveler on another, referrer for a third) is either duplicated or lost entirely
- The global nature of the business means phones, emails, name formats, and identity patterns vary by country — the model must handle all of them

---

## 2. First Principles

### Separation of Person from Role

The core insight: **a person is not their relationship to a trip.** A person exists independently. Their role on a given trip is a property of the relationship, not the person.

A single person can be:
- The SPOC for their own family trip
- The emergency contact for their parents' trip
- The referrer who sent a colleague
- A traveler on a corporate group booking

None of these roles change who they are. All of these roles link back to the same durable Person record.

### The Person Is the Atom

The Person is the smallest addressable unit. Everything else is a relationship or an attribute:

- `Phone` is an attribute of a Person (one Person can have many phones)
- `Email` is an attribute of a Person (one Person can have many emails)
- `Role` is a relationship between a Person and a Trip (one Person can have different roles on different trips)
- `Referral` is a relationship: Person A referred Person B to the agency
- `Relationship` is a labeled connection between two Persons: "Person B is Person A's emergency contact," "Person B is Person A's spouse"

### Global by Design

No country-specific assumptions in the model:
- No single-phone-number assumption (a person may have a personal, work, and WhatsApp number)
- No phone-format enforcement (numbers are stored as-is with a country code prefix, normalized per locale)
- No email requirement (many travelers globally don't use email as primary contact)
- Name is a single string field (no first/last name split — many naming conventions don't fit that mold)
- Addresses are flexible per-country formats

---

## 3. Data Model

### Core Entity: `Person`

```python
class Person(Base):
    """A person known to the agency.

    A Person is any individual who has interacted with the agency in any capacity:
    lead, traveler, SPOC, referrer, emergency contact, supplier contact, etc.
    This is the single durable identity record. Everything else is a relationship
    or an attribute.

    Created on first contact (inbound call, WhatsApp, walk-in, referral).
    Enriched over time as more data becomes available.
    """
    __tablename__ = "persons"

    id: UUID                  # stable internal PK, never changes
    agency_id: FK → Agency    # tenant-scoped (each agency has its own persons)

    name: str | None          # best known name, enriched over time
    notes: str | None         # freeform agent notes about this person

    # Status
    status: PersonStatus      # lead | active | dormant | churned | blacklisted
    is_organization: bool     # True if this represents a company/entity

    # Timestamps
    created_at: datetime
    updated_at: datetime
    first_contact_at: datetime | None  # first interaction with this agency
    last_contact_at: datetime | None   # most recent interaction

    # Relationships
    contacts: list[PersonContact]
    trip_roles: list[TripPerson]

    # Computed (materialized view or query-time)
    # total_trips, total_spend, first_trip_date, last_trip_date
```

### Entity: `PersonContact`

```python
class PersonContact(Base):
    """A contact method for a Person.

    A person can have multiple contacts of different types.
    No single type is required or assumed primary.
    """
    __tablename__ = "person_contacts"

    id: UUID
    person_id: FK → Person

    type: ContactType         # phone | email | whatsapp | telegram | wechat | signal | other
    value: string             # the actual contact value (normalized per type)
    label: string | None      # "Work", "Personal", "Emergency", etc.
    is_verified: bool         # has this contact been confirmed?
    verified_at: datetime | None

    # Unique per agency (a phone can't belong to two Persons in the same agency)
    # But a person can have multiple phones
    unique: (agency_id, type, value)
```

### Entity: `PersonRelationship`

```python
class PersonRelationship(Base):
    """A labeled connection between two Persons known to the agency.

    Examples:
      - Person A is Person B's emergency contact
      - Person A is Person B's spouse
      - Person A referred Person B (includes trip reference)
      - Person A is Person B's employer
    """
    __tablename__ = "person_relationships"

    id: UUID
    agency_id: FK → Agency

    from_person_id: FK → Person   # the subject
    to_person_id: FK → Person     # the object
    relationship_type: str        # emergency_contact | spouse | parent | child | colleague | employer | referrer | other
    label: str | None             # freeform descriptor: "Mother", "Driver", "Colleague from Acme Corp"
    trip_id: FK → Trip | None     # if this relationship was established through a specific trip

    # A person can only have one relationship of a given type to another person
    unique: (from_person_id, to_person_id, relationship_type)
```

### Junction Entity: `TripPerson`

```python
class TripPerson(Base):
    """A Person's specific role(s) and data on a single Trip.

    One person can have multiple roles on the same trip (e.g., both traveler and SPOC).
    One trip has many TripPerson records (the party, plus SPOCs, emergency contacts, etc.).
    """
    __tablename__ = "trip_persons"

    id: UUID
    trip_id: FK → Trip
    person_id: FK → Person

    roles: list[PersonRole]   # [spoc, traveler] or [traveler, emergency_contact_for]

    # Role-specific details stored as JSON
    details: dict | None

    # Example details per role:
    #   traveler:   {"passport_number": "...", "passport_expiry": "...", "dietary_requirements": "..."}
    #   emergency:  {"relationship": "spouse", "phone": "+1-555-0100"}
    #   referrer:   {"referral_channel": "word_of_mouth", "referral_date": "..."}
    #   billing:    {"company_name": "...", "gst_number": "..."}

    created_at: datetime
    updated_at: datetime
```

### Enums

```python
class PersonStatus(enum.Enum):
    lead = "lead"               # contacted but never booked
    active = "active"           # has at least one active/upcoming trip
    dormant = "dormant"         # no trip in > 12 months
    churned = "churned"         # explicitly lost or marked as unlikely to return
    blacklisted = "blacklisted" # explicitly blocked from future bookings

class ContactType(enum.Enum):
    phone = "phone"
    email = "email"
    whatsapp = "whatsapp"
    telegram = "telegram"
    wechat = "wechat"
    signal = "signal"
    other = "other"

class PersonRole(enum.Enum):
    lead_source = "lead_source"       # the person who initiated contact
    spoc = "spoc"                     # primary point of contact for this trip
    traveler = "traveler"             # actually traveling
    emergency_contact = "emergency_contact"  # to be notified in an emergency
    billing_contact = "billing_contact"      # responsible for payment
    referrer = "referrer"             # referred another person to this trip
```

### Trip Model Changes

```python
# New field on Trip:
spoc_id: FK → Person | None  # primary contact for this trip (denormalized for fast access)
# The full party, including non-travelers, is in TripPerson
```

---

## 4. What This Enables

### Phase 1 — Identity (MVP)
- Person created automatically on first contact from any channel
- Phone-based auto-linking: same phone number across enquiries → same Person
- Contact enrichment: email, name, and labels added over time
- `_derive_customer_name()` output feeds into the Person `name` field as a starting guess
- Inbox shows the Person's best known name instead of "Customer abc123"

### Phase 2 — Relationships
- Emergency contacts are Persons with `PersonRole.emergency_contact` on a Trip
- Referrals are `PersonRelationship` records with `relationship_type: "referrer"`
- Family/groups are visible through `PersonRelationship`: spouse, parent, child, sibling
- Corporate contacts are Persons with `is_organization: True`

### Phase 3 — History & Scoring
- Lifecycle scoring functions wired to real data: `total_trips`, `total_spend`, `last_trip_date`
- Churn risk computed from actual inactivity, not 0.0
- Repeat detection from DB query, not keyword heuristic
- Cross-trip memory: preferences, past complaints, travel style accumulated per Person

### Phase 4 — Network Effects
- Referral attribution: Person who referred → Person who booked → Trip
- LTV computation per Person across all trips
- Network graph: who-knows-who within the agency's customer base
- Supplier-side person tracking (tour guides, drivers, hotel managers as Persons)

### Future (Phase 5+)
- Person merge/dedup (when two records turn out to be the same person)
- Consent lifecycle (withdrawal, erasure, data portability)
- Cross-agency identity (Person known to Agency A moves to Agency B)
- Self-serve traveler portal with Person-based login

---

## 5. Key Architecture Decisions

### Decision 1: Single Table, Not Multiple

**Chosen**: Single `persons` table with `TripPerson` for role mapping.

Rejected alternatives:
- **Separate tables per role** (travelers, contacts, SPOCs, referrers) — creates join complexity, violates DRY, makes cross-role queries hard ("is this person connected to any of our trips in any capacity?")
- **Separate CRM module** — premature modularization. The Person model is foundational. It should live at the same layer as Trip and Agency.

### Decision 2: Contacts Are a Separate Table, Not JSON

**Chosen**: `person_contacts` table with one row per contact method.

Rationale:
- Queryability: "find all Persons with this phone number" is a simple SELECT
- Multiple contacts: one Person can have 5 phones, 3 emails, a WhatsApp, and a WeChat
- Verification status per contact
- Avoids JSON path queries for common lookups

### Decision 3: Phone Is Lookup Key, Not Primary Key

**Chosen**: UUID is the internal PK. Phone is a uniquely-indexed lookup on `person_contacts`.

Rationale:
- Phone numbers change (new carrier, new country)
- A Person can have multiple phones
- Different countries have different phone formats
- UUIDs never collide, never change

### Decision 4: Auto-Creation on First Contact

**Chosen**: Any inbound contact from an unrecognized contact method creates a Person with `status: "lead"`.

Rationale:
- Zero friction for agents — no manual creation step
- The Person record starts with just a phone or email, enriched over time
- The existing `_derive_customer_name()` heuristic fills in the `name` field as a starting guess
- An agent can merge or correct records later

### Decision 5: No First/Last Name Split

**Chosen**: Single `name` string.

Rationale:
- Many global naming conventions (single name, patronymic, family-name-first) don't fit first/last
- Parsing a single name into components is unreliable across cultures
- If structured names are needed later, add a `name_parts` helper column

### Decision 6: is_organization Is a Flag on Person, Not a Separate Table

**Chosen**: `is_organization: bool` on Person.

Rationale:
- An organization has contacts, relationships, and trip roles just like an individual
- Separate table would duplicate the PersonContact + PersonRelationship + TripPerson model
- The flag affects behavior (e.g., not a "traveler" role) but not structure

### Decision 7: PersonStatus Is Agent-Managed, Not Fully Automatic

**Chosen**: Status can be set manually by the agent. Computed signals (`last_trip_date > 12 months → dormant hint`) are shown to the agent, who decides.

Rationale:
- Automatic status transitions have edge cases: a "dormant" person who just called doesn't become "active" until they book
- The agent knows the context (e.g., "this person is a VIP who only books once every 2 years — not dormant")
- If rules-based status computation is desired later, it can be added as a suggestion, not an override

---

## 6. Integration Points

### Existing Code That Maps (or Will Map)

| Current Code | Maps To | Notes |
|---|---|---|
| `_derive_customer_name()` `inbox_projection.py:250-259` | Person.name | Heuristic feeds into best-known name |
| `customer_id` in `LifecycleInfo` `packet_models.py:214` | Trip.spoc_id → Person.id | Replace loose string with FK |
| Repeat detection keywords `extractors.py:1835-1850` | DB query: Person → TripPerson → Trip count | No more keyword heuristic |
| `score_churn_risk()` `decision.py:1590` | Computed from Person.last_trip_at | Wire after Phase 1 |
| `score_retention_risk()` `decision.py:~1600` | Computed from Person.total_trips + last_trip_at | Wire after Phase 1 |
| `retention_consent` frontend types | Person-level consent field | Migrate from trip-level to person-level |
| `customerName` in `InboxTripItem` | Person.name (looked up via trip.spoc_id) | No more heuristic derivation |

### API Endpoints (Phase 1)

| Method | Path | Permission | Description |
|---|---|---|---|
| POST | /api/persons | `customers:write` | Create person |
| GET | /api/persons | `customers:read` | List/search persons (by phone, email, name) |
| GET | /api/persons/{id} | `customers:read` | Get person with contacts, relationships |
| PATCH | /api/persons/{id} | `customers:write` | Update person fields |
| GET | /api/persons/{id}/trips | `customers:read` | Get trip history for this person |

---

## 7. What This Document Does Not Cover

These are deferred to future design discussions:

- **Consent lifecycle** — withdrawal of consent, right to erasure, data portability. The Person model provides the hooks; the enforcement module is separate.
- **Merge/dedup** — how to handle two Person records discovered to be the same person. Model supports it; tooling is future.
- **Cross-agency identity** — if the same Person is known to Agency A and also to Agency B (not the same tenant). Out of scope for the single-tenant pattern.
- **Supplier-side persons** — tour guides, drivers, hotel managers who are Persons known to the agency but not customers. The model supports this via `is_organization: False` and absence of traveler roles, but the use case is not designed.
- **Self-serve traveler portal** — Person-based login for travelers to view their own trips. Requires auth changes.
- **Person activity timeline** — a chronological feed of all interactions (calls, emails, trips, notes) for a Person. This is ISSUE-003 from the gap register (Interaction/Activity Timeline).

---

## 8. Open Questions

1. **Organization as Person or separate model?** The current design uses `is_organization: bool` on Person. This means a company has contacts and relationships like any person. The alternative is a separate `Organization` model with its own contacts table. The chosen approach avoids duplication but means "Acme Corp" and "John from Acme Corp" are both Persons with a `spouse` relationship — awkward. Consider whether organizations need relationship tracking differently.

2. **Contact verification flow** — who verifies a contact, and how? The agent? The person via OTP? The model has `is_verified` but no workflow around it.

3. **Phone normalization per country** — do we normalize at write time or query time? Write-time is faster. Query-time handles more formats. Recommendation: normalize on write per country code prefix (e.g., `+1` → E.164 for US, `+91` → E.164 for India), store raw value alongside normalized form.

4. **Blacklisted Persons** — a blacklisted person should not be able to create new trips. How is this enforced? At the API level (check Person.status before saving)? At the enquiry level (block inbound from a phone)?

5. **Referral attribution** — if Person A refers Person B, and Person B books a trip, should the referral `TripPerson` be on Person B's trip, or should it be a `PersonRelationship` between A and B? The current design uses `PersonRelationship` with `relationship_type: "referrer"` and an optional `trip_id`. This handles both "referral to the agency" (no specific trip) and "referral to a specific trip."

---

## 9. Document References

| Document | Relationship |
|---|---|
| `Docs/DISCOVERY_GAP_CUSTOMER_LIFECYCLE_2026-04-16.md` | Gap analysis this doc supersedes for model design |
| `Docs/discussions/customer_model_2026-04-29.md` | First-principles analysis (4-level model proposal) |
| `Docs/discussions/crm_approach_2026-04-29.md` | CRM-vs-booking-first framing |
| `frontend/docs/CRM_01_PROFILES.md` | Legacy profile schema (19 interfaces — superseded) |
| `frontend/docs/CRM_02_HISTORY.md` | Legacy history schema (14 interfaces — superseded) |
| `Docs/PII_GUARD_RAILS_IMPLEMENTATION_2026-04-26.md` | Privacy architecture — Person model inherits PII classifications |
| `spine_api/core/auth.py:163-175` | `customers:read`/`customers:write` permission strings |
| `src/intake/extractors.py:1835-1850` | Current keyword-based repeat detection (to be replaced) |
| `src/intake/decision.py:1509-1625` | Scoring functions to wire to real data |
| `src/intake/inbox_projection.py:250-259` | `_derive_customer_name()` heuristic (to be replaced) |
