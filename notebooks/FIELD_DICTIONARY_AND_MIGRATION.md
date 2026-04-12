# Canonical Field Dictionary and Migration Map

**Method**: Compared `specs/canonical_packet.schema.json` (26 fact fields) against actual NB02 MVB (15 fields) and NB03 usage. Identified every drift, alias, and missing field.

---

## Drift Summary

| Dimension | Count | Detail |
|-----------|-------|--------|
| Schema fields (canonical) | 26 | The source of truth |
| NB02 MVB fields | 15 | Decision/blocker vocabulary |
| Fields in both | 7 | origin_city, budget, dates, destination, traveler_count, preferences, dietary |
| Schema-only (not in NB02) | 19 | Party composition, trip context, constraints, documents |
| NB02-only (not in schema) | 8 | Trip purpose, selected destinations/itinerary, payment, special requests, activity, accommodation |
| Alias pairs | 20 | NB02 maps alternate names to canonical fields |

---

## Unified Field Dictionary

### Traveler Composition

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| `party_size` | `traveler_count` | **`party_size`** (NB02: `traveler_count`) | All | **Hard** (all stages) | **Yes** — "big family", "maybe 4 or 5" are valid values but don't resolve uncertainty | NB02 uses `traveler_count` but schema says `party_size`. Alias needed. |
| `adult_count` | *(not in NB02)* | **`adult_count`** (add to NB01) | Booking | Hard (booking) | No | Missing from current implementation. |
| `child_count` | *(not in NB02)* | **`child_count`** (add to NB01) | Discovery+ | Soft (discovery), Hard (booking) | No | Missing from current implementation. |
| `elderly_present` | *(not in NB02)* | **`elderly_present`** (add to NB01) | Discovery+ | Soft (discovery), Hard (proposal) | No | Missing from current implementation. Critical for suitability. |
| `child_ages` | *(not in NB02)* | **`child_ages`** (add to NB01) | Discovery+ | Soft (discovery), Hard (booking) | No | Missing from current implementation. Toddler vs teen changes everything. |
| *(schema gap)* | `traveler_composition` (NB01 fixture) | **`party_composition`** (add to schema) | Discovery+ | Hard (all) | **Yes** — "2 adults + 2 kids (8,12)" is precise; "big family" is ambiguous | Neither schema nor NB02 has a structured composition field. This is the single biggest gap. |

### Origin / Destination

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| `origin_city` | `origin_city` (aliases: `origin`, `departure_city`, `departure`) | **`origin_city`** ✅ | All | **Hard** (all) | No | Well-aligned. 4 aliases covered. |
| `origin_country` | *(not in NB02)* | **`origin_country`** (add to NB01) | Booking | Soft | No | Low priority for domestic travel. |
| `destination_candidates` | `destination_city` | **`destination_candidates`** (rename NB02 field) | Discovery+ | **Hard** (all) | **Yes** — schema already anticipates plural; NB02 uses singular `destination_city` | Schema is smarter: `destination_candidates` implies multiple options. NB02's `destination_city` implies one decided place. This mismatch causes "Andaman or Sri Lanka" to be treated as resolved. |
| `domestic_or_international` | *(not in NB02)* | **`domestic_or_international`** (derived signal) | Discovery | Soft | No | Currently computed inline in NB01 classifier. Should be explicit. |

### Trip Context

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| `trip_type` | `trip_purpose` | **`trip_purpose`** (NB02 name wins — more natural) | Discovery+ | Soft (discovery) | No | Schema says `trip_type` ("leisure", "pilgrimage", "corporate"). NB02 says `trip_purpose`. Same concept, different name. |
| `date_window` | `travel_dates` (aliases: `travel_dates_from`, `travel_dates_to`, `dates`) | **`date_window`** (schema name wins) | All | **Hard** (all) | **Yes** — "March" vs "March 15-20" vs "maybe April" | Schema uses `date_window` (implies flexibility). NB02 uses `travel_dates` (implies fixed). This mismatch hides ambiguity. |
| `duration_nights` | *(not in NB02 MVB)* | **`duration_nights`** (add to NB02) | Shortlist+ | Soft | No | Present in NB01 classifier, not wired to MVB. |

### Budget

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| `budget_total` | `budget_range` (aliases: `budget`, `budget_total`, `budget_band`) | **`budget_total`** (schema name wins) | Discovery+ | Soft (discovery) | **Yes** — "around 2L" vs "exactly 3L" | Schema separates `budget_total`, `budget_currency`, `budget_flexibility`. NB02 collapses all into `budget_range`. Flexibility signal is lost. |
| `budget_currency` | *(not in NB02)* | **`budget_currency`** (add to NB01) | Booking | Soft | No | Assume INR for now. |
| `budget_flexibility` | *(not in NB02)* | **`budget_flexibility`** (add to NB01/NB02) | Discovery+ | Soft | **Yes** — "can stretch", "flexible", "fixed" | This is the stretch signal. Schema has it, code doesn't use it. |

### Preferences / Constraints

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| `pace` | `pace` (NB01 classifier) | **`pace`** ✅ | Discovery+ | Soft | No | Aligned. |
| `trip_style` | `traveler_preferences` | **`trip_style`** (schema name wins) | Discovery+ | Soft (discovery) | No | Schema: `trip_style` ("adventure", "cultural", "relaxed"). NB02: `traveler_preferences` (freeform). Different granularity. |
| `hotel_preferences` | *(not in NB02 MVB)* `hotel_star_pref` (NB01 fixture) | **`hotel_preferences`** ✅ | Shortlist+ | Soft | No | Schema has it, NB01 extracts it, NB02 doesn't block on it. Correct. |
| `meal_preferences` | `dietary_restrictions` | **`meal_preferences`** (schema name wins) | Booking | Soft (booking) | No | Same concept. NB02 name is more clinical. |
| `mobility_constraints` | *(not in NB02)* | **`mobility_constraints`** (add to NB01) | Discovery+ | Soft (discovery), Hard (proposal) | No | Critical for elderly suitability. Missing from implementation. |
| `medical_constraints` | *(not in NB02)* | **`medical_constraints`** (add to NB01) | Discovery+ | Soft (discovery), Hard (booking) | No | Critical for elderly/chronic conditions. Missing from implementation. |
| `hard_constraints` | *(not in NB02)* | **`hard_constraints`** (add to NB02) | Discovery+ | **Hard** (discovery) | No | Schema concept: non-negotiables ("no flights > 6hrs", "must be vegetarian hotel"). NB02 has no equivalent. |
| `soft_preferences` | *(not in NB02)* | **`soft_preferences`** (add to NB02) | Discovery+ | Soft | No | Nice-to-haves vs hard constraints distinction. |
| `agency_notes` | *(not in NB02)* | **`agency_notes`** (add to NB01) | All | Soft | No | Owner-seeded tribal knowledge. Missing from implementation. |

### Documents / Booking

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| `passport_status` | `traveler_details` (NB02 booking MVB) | **`passport_status`** (schema name wins) | Booking | **Hard** (booking) | No | NB02's `traveler_details` is too vague. Schema is precise. |
| `visa_status` | *(not in NB02)* | **`visa_status`** (add to NB01) | Booking | **Hard** (booking) | No | Missing from implementation. Visa crisis scenario can't be modeled. |

### Sourcing / Execution (NOT in schema or NB02)

| Schema Field | NB02/NB03 Field | Recommended Unified Name | Stages | Fills Blocker | Ambiguity Tracking | Notes |
|-------------|-----------------|-------------------------|--------|---------------|-------------------|-------|
| *(not in schema)* | `selected_destinations` | **`selected_destinations`** (add to schema) | Shortlist+ | **Hard** (shortlist+) | No | NB02 MVB has it, schema doesn't. Shortlist-stage concept. |
| *(not in schema)* | `selected_itinerary` | **`selected_itinerary`** (add to schema) | Proposal+ | **Hard** (proposal+) | No | NB02 MVB has it, schema doesn't. Proposal-stage concept. |
| *(not in schema)* | `payment_method` | **`payment_method`** (add to schema) | Booking | **Hard** (booking) | No | NB02 MVB has it, schema doesn't. |
| *(not in schema)* | `special_requests` | **`special_requests`** (add to schema) | Proposal+ | Soft (proposal) | No | NB02 MVB has it, schema doesn't. |
| *(not in schema)* | `activity_preferences` | **`activity_preferences`** (add to schema) | Shortlist+ | Soft (shortlist) | No | NB02 MVB has it, schema doesn't. |
| *(not in schema)* | `accommodation_type` | **`accommodation_type`** (add to schema) | Shortlist+ | Soft (shortlist) | No | NB02 MVB has it, schema doesn't. |
| *(not in schema)* | `sourcing_path` | **`sourcing_path`** (add to both) | Discovery+ | Soft | No | The missing agency differentiator: internal → preferred → network → open. |

---

## Vocabulary Drift: Schema vs NB02 Decision/Blocker Language

### Drift 1: Singular vs Plural (Destination)

| Schema | NB02 | Problem |
|--------|------|---------|
| `destination_candidates` (plural) | `destination_city` (singular) | Schema anticipates multiple options; NB02 assumes one decided place. "Andaman or Sri Lanka" gets stored as a single string value and treated as resolved. |

**Fix**: Rename NB02 field to `destination_candidates`. Track `destination_status` as a derived signal: `decided` | `semi_open` | `open`.

### Drift 2: Window vs Dates (Timing)

| Schema | NB02 | Problem |
|--------|------|---------|
| `date_window` (implies range + flexibility) | `travel_dates` (implies fixed) | "March" and "March 15-20" are both valid `travel_dates` values but have very different ambiguity levels. |

**Fix**: Use schema name `date_window`. Add `date_confidence` derived signal: `fixed` | `narrow_window` | `broad_window` | `unknown`.

### Drift 3: Total vs Range (Budget)

| Schema | NB02 | Problem |
|--------|------|---------|
| `budget_total` + `budget_flexibility` (separate fields) | `budget_range` (single field) | "2L" and "around 2L, can stretch" both go into `budget_range`. The flexibility signal is buried in the string. |

**Fix**: Split NB02 field into `budget_total` (numeric) + `budget_flexibility` (enum: `fixed` | `flexible` | `stretch`).

### Drift 4: Party Size vs Traveler Count (Composition)

| Schema | NB02 | Problem |
|--------|------|---------|
| `party_size` + `adult_count` + `child_count` + `elderly_present` + `child_ages` (structured) | `traveler_count` (single number or string) | "5" and "big family" and "2 adults + 2 kids (8,12)" all go into one field. Composition intelligence is impossible. |

**Fix**: Split into schema's structured fields. Add `party_composition` (freeform summary for NB01 extraction) that feeds the structured fields.

### Drift 5: Trip Type vs Trip Purpose (Intent)

| Schema | NB02 | Problem |
|--------|------|---------|
| `trip_type` (enum-like) | `trip_purpose` (freeform) | Minor naming drift. Same concept. |

**Fix**: Standardize on `trip_purpose` (more natural language). Schema should be updated.

### Drift 6: Traveler Details vs Passport/Visa (Documents)

| Schema | NB02 | Problem |
|--------|------|---------|
| `passport_status` + `visa_status` (specific) | `traveler_details` (vague catch-all) | "Traveler details" could mean names, passport numbers, dietary needs, or anything. No specificity. |

**Fix**: Split NB02 field into schema's `passport_status` + `visa_status` + `passenger_names`.

### Drift 7: Missing Agency Context

| Schema | NB02 | Problem |
|--------|------|---------|
| `agency_notes` (owner-seeded context) | Not modeled | The agency owner's tribal knowledge has no home in the current implementation. It's lumped into `explicit_owner` authority but has no dedicated field. |

**Fix**: Add `agency_notes` to NB01 extraction. Treat as `explicit_owner` authority with persistence across customers.

### Drift 8: Missing Constraint Layers

| Schema | NB02 | Problem |
|--------|------|---------|
| `hard_constraints` + `soft_preferences` (layered) | No equivalent | NB02 treats all preferences as equal. Schema distinguishes non-negotiables from nice-to-haves. |

**Fix**: Add `hard_constraints` to NB02 MVB as a soft blocker in discovery. Add `soft_preferences` for the flip side.

### Drift 9: No Sourcing Concept Anywhere

| Schema | NB02 | Problem |
|--------|------|---------|
| Not in schema | Not in NB02 | The entire sourcing hierarchy (internal → preferred → network → open) — the agency's core differentiator — has no representation in any layer. |

**Fix**: Add `sourcing_path` to both schema and NB02 as a derived signal.

---

## Migration Priority

### Immediate (before NB04 or shadow mode)
| Action | Effort | Impact |
|--------|--------|--------|
| Rename `traveler_count` → `party_size` + add `party_composition` | Low | High — composition intelligence |
| Rename `destination_city` → `destination_candidates` + add `destination_status` | Low | High — fixes ambiguity gap |
| Split `budget_range` → `budget_total` + `budget_flexibility` | Medium | High — fixes stretch signal loss |
| Split `traveler_details` → `passport_status` + `visa_status` | Medium | High — enables visa crisis modeling |
| Add `agency_notes` field | Low | Medium — owner knowledge persistence |
| Add `sourcing_path` derived signal | Medium | High — agency differentiator |

### Before Booking Stage
| Action | Effort | Impact |
|--------|--------|--------|
| Add structured party fields (`adult_count`, `child_count`, `elderly_present`, `child_ages`) | Medium | High |
| Add `mobility_constraints` + `medical_constraints` | Low | High |
| Add `hard_constraints` to MVB | Low | Medium |

### Schema Update (align with NB02 reality)
| Action | Effort | Impact |
|--------|--------|--------|
| Add NB02-only fields to schema: `selected_destinations`, `selected_itinerary`, `payment_method`, `special_requests`, `activity_preferences`, `accommodation_type` | Low | Medium — schema should match implementation |
| Rename `trip_type` → `trip_purpose` in schema | Low | Low — cosmetic |
