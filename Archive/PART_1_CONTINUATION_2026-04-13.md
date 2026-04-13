# PART 1 Continuation (Codex Intake)

- Source: User-shared continuation of the first ChatGPT discussion in this Codex session
- Intake timestamp (IST): 2026-04-13 14:23:41
- Context: This extends `Archive/PART_1_RAW.md` and should be treated as the same conversation thread.

## Key Additions Captured

### 1. Agency-side operational realities
- Agency tie-ups with preferred hotels/suppliers are a first-class constraint.
- Internal seasonal packages and network/consortium inventory are common sourcing paths.
- Planning is a multi-objective optimization problem:
  - traveler fit
  - margin/commercial viability
  - operational simplicity
  - conversion probability
  - revision burden/risk

### 2. Sourcing hierarchy direction
- Working hierarchy (default):
  1. Internal packages
  2. Preferred supplier inventory
  3. Network/consortium supply
  4. Open market
- Implication: product must support routing and explain trade-offs, not only open-market “best deal” search.

### 3. Additional nuanced requirements
- Build a context graph across travelers, trips, suppliers, destinations, activities, risks, and outcomes.
- Learn from all confirmed/completed trips (closed-loop learning).
- Strong customer classification and bracket updates over time.
- Person-level activity suitability checks (avoid group-level wasted spend).
- Explicit shopping budget capture and budget decomposition.
- Live cost awareness during intake.
- Practical destination intelligence (where to eat/shop, what to buy/eat).
- Potential review-signal ingestion for ranking (with evidence tagging).

### 4. Product direction confirmation
- Primary business remains B2B agency OS (not B2C).
- Side validation surface can be a free “planning intelligence engine”:
  - intake + fit checks + itinerary audit + mismatch detection
  - no full booking/support obligations in v1

### 5. Audit/compare wedge expansion
- Support upload and compare for:
  - PDF
  - pasted text
  - screenshots
  - URLs (including OTA/package pages)
- Outputs should include:
  - fit/value/waste analysis
  - subgroup suitability
  - missing spend buckets
  - optional improved alternative

### 6. Voice session architecture intent
- Two-screen model:
  - Agency screen seeds context and generates link.
  - Traveler screen joins voice session with live brief panel.
- Backend orchestration should be adaptive:
  - question router
  - state extractor
  - classifier
  - gap detector
  - specialist checks
  - brief builder/consensus for handoff
- Stop criteria and confidence/evidence tagging are mandatory.

## Status
- This file is a preservation artifact (historical continuity), not a replacement of raw logs.
- Next user drops should continue as `PART_2_RAW*` / continuation artifacts using the same pattern.
