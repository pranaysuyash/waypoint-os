# Discovery Gap Analysis: Document/Visa Management

**Date**: 2026-04-16
**Gap Register**: #10 (P1 — visa/passport hard-blockers at booking stage)
**Scope**: Visa requirement lookup, document checklists, per-person document tracking, visa timeline risk, multi-destination visa strategy, application status tracking, document upload/storage. NOT: visa compliance for tax (#15).

---

## 1. Executive Summary

The system can *extract* visa and passport status from free text (regex patterns in `extractors.py` L617-676) and can *flag* document risk as a booking-stage blocker (`decision.py` L1070-1097). **But it cannot verify, look up, track, or manage any of this.** There is no visa requirement database, no per-country document checklists, no timeline calculation ("visa takes 15 business days, travel is in 12 days"), no application tracking, no document upload or storage. The system can detect "my passport expires in March" but cannot answer "does a citizen of India need a visa for Thailand?" or "what documents do I need for Schengen?"

---

## 2. Evidence Inventory

### What's Documented

| Doc | What | Location |
|-----|------|----------|
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L95-101 | 7 missing processes: visa lookup, per-country checklists, application tracking, timeline risk, multi-destination visa logic, mandatory insurance rules, document collection | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L108 | Insurance requirements linked to visa type (Schengen €30K minimum) | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L129,131 | D-45 document collection reminders; D-3 document delivery | Docs/ |
| `INDUSTRY_PROCESS_GAP_ANALYSIS` L256 | Emergency document workflow (passport theft/loss) | Docs/ |
| `PERSONA_PROCESS_GAP_ANALYSIS` L54, L121, L251 | Visa/passport as P1 hard blocker; "No visa requirement database" | Docs/ |
| `15_MISSING_CONCEPTS` L107-118 | Missing Concept #7: `passport_status`, `visa_requirements`, `valid_passport`, `valid_visa` fields | notebooks/ |
| `TRIP_VISA_DOCUMENT_RISK_SCENARIO` | Dedicated scenario document for visa/document risk investigation | Docs/context/ |
| `RISK_AREA_CATALOG` L40-45 | Document compliance risks: passport validity, visa not obtained, transit visa rules, health certificates | Docs/context/ |
| `COVERAGE_MATRIX` L85 | "Promote visa/passport checks into canonical hard-blocker logic" | Docs/ |
| `TEST_GAP_ANALYSIS` L69, L232-241 | P0 Scenario P1-S4 "Visa Problem at Last Minute" — missing `valid_passport`/`valid_visa` blockers | Docs/ |

### What's Implemented

| Code | What | Status |
|------|------|--------|
| `extractors.py` L617-676 | `_extract_passport_visa()`: regex extraction of passport status (per-traveler or "all") and visa status (required/not_required/unknown) | **Working** — text extraction only |
| `decision.py` L167-168 | `passport_status`, `visa_status` as booking-stage hard blockers | **Working** — field names only |
| `decision.py` L1070-1097 | `document_risk` risk flag: checks passport expiry, visa application status, timeline risk | **Working** — intake-time flags only |
| `decision.py` L53, L918, L956 | `visa_insurance` budget bucket in 27 destination cost ranges | **Working** — heuristic cost estimates |
| `strategy.py` L233-234 | Priority scores: `passport_status: 15`, `visa_status: 16` | **Working** — priority ranking |

### What's NOT Implemented

- No visa requirement database (nationality → destination → requirement)
- No per-country document checklists 
- No visa timeline calculation (application time vs. travel date)
- No multi-destination visa strategy (Schengen coverage)
- No application status tracking (submitted → review → approved/rejected)
- No document upload/storage (no S3, no upload endpoint)
- No per-person document progress tracker
- No `visa_requirements` fact in CanonicalPacket (only `visa_status` from regex)
- No `valid_passport`/`valid_visa` as canonical hard blockers (field names differ)
- No mandatory insurance rules engine (Schengen €30K minimum)
- No document collection reminders (D-45, D-30, D-15)
- No emergency document workflow (passport theft/loss)

---

## 3-4. Gap Taxonomy & Data Model (Combined)

### Structural Gaps

| Gap ID | Concept | Implementation | Blocks |
|--------|---------|----------------|--------|
| **DV-01** | Visa requirement database | None — regex-guessed from text | All visa compliance |
| **DV-02** | Document checklist per destination | None | Document completeness checking |
| **DV-03** | Document upload/storage | None — no S3, no upload endpoint | File collection |
| **DV-04** | Application status tracking | None — no workflow states | Visa progress |
| **DV-05** | Per-person document tracker | None — `passport_status` is per-trip not per-traveler | Group travel document management |

```python
@dataclass
class VisaRequirement:
    nationality: str          # "IN" (ISO 3166-1 alpha-2)
    destination: str          # "TH" (ISO 3166-1 alpha-2)
    visa_type: str            # "visa_free" | "visa_on_arrival" | "e_visa" | "consulate_visa" | "not_allowed"
    max_stay_days: int        # 30, 90, 180
    processing_time_days: int # 0 for visa-free, 3 for e-visa, 15 for consulate
    required_documents: List[str]  # ["passport_6mo_validity", "photo_2x2", "bank_statement_3mo", ...]
    mandatory_insurance: bool = False
    insurance_minimum_coverage: Optional[str] = None  # "EUR_30000" for Schengen
    fee: Optional[str] = None  # "USD 80"
    notes: str = ""           # "Schengen visa covers 27 countries"

@dataclass
class TravelerDocument:
    traveler_name: str
    document_type: str        # "passport", "visa", "insurance", "photo", "bank_statement", ...
    status: str               # "not_started" | "collected" | "submitted" | "approved" | "rejected" | "not_applicable"
    collected_at: Optional[str] = None
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    file_url: Optional[str] = None     # S3/R2 link after upload
    expiry_date: Optional[str] = None  # For passport/visa expiry

@dataclass
class DocumentChecklist:
    trip_id: str
    travelers: List[TravelerDocument]
    checklist_complete: bool = False
    timeline_risk: str = "none"  # "none" | "tight" | "at_risk" | "impossible"
    submission_deadline: Optional[str] = None
```

---

## 5-8. Phase-In, Decisions, Risks, Out of Scope

### Phase 1: Visa Requirement Lookup + Checklist (P1, ~3-4 days, blocked by #02)

1. Create `VisaRequirement` data structure with initial dataset for top 20 India→destination pairs
2. Wire `visa_requirements` as a canonical fact (not just regex from text)
3. Compute `timeline_risk`: visa processing time vs. travel date
4. Generate per-destination document checklist
5. Add `valid_passport`/`valid_visa` as canonical hard blockers

**Acceptance**: Agent enters "Indian passport, traveling to Thailand" → system returns: "Visa on arrival, 15 days max. Required documents: passport 6mo validity, return ticket, hotel booking. Timeline: OK (visa on arrival, no pre-application needed)."

### Phase 2: Document Upload + Per-Person Tracker (P2, ~3-4 days, blocked by #02, #08)

1. Add S3/R2 file upload endpoint
2. Create per-traveler `TravelerDocument` tracker
3. Add document status progress dashboard
4. Wire to notification engine for collection reminders (D-45, D-30, D-15)

**Acceptance**: Agent can upload passport photo per traveler. System shows "Sharma family: 3 of 4 passports collected, 0 of 4 visas applied."

### Phase 3: Application Tracking + Multi-Destination (P2, ~2-3 days)

1. Add application status workflow (submitted → review → approved/rejected)
2. Add multi-destination visa strategy (Schengen rule)
3. Add mandatory insurance rules linked to visa type
4. Add emergency document replacement workflow

**Acceptance**: Agent can track "Schengen visa submitted Mar 1, expected approval Mar 15, covers all 4 EU destinations." System flags if travel date < expected approval date.

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Visa requirement data | (a) Static dataset for top 20 routes, (b) Sherpa/API integration, (c) Community-maintained database | **(a) Static dataset for MVP** — covers 80% of Indian agency queries. Add API integration later. |
| Document storage | (a) Local filesystem, (b) S3/R2, (c) Cloudflare R2 | **(b) S3/R2** — matches existing infrastructure recommendation |
| Scope for MVP | (a) All nationalities, (b) India outbound only, (c) Top 20 destinations only | **(b) India outbound only** — matches target market |

| Risk | Severity | Mitigation |
|------|----------|------------|
| Visa data becomes stale | High | Add `last_verified` date. Cache-bust monthly. Crowdsource corrections. |
| Wrong visa advice leads to denied entry | Critical | Clear disclaimer: "Verify requirements with official sources." System recommends, agent confirms. |
| Document upload security | Medium | S3 signed URLs with expiry. Virus scanning on upload. |

**Out of Scope**: Real-time government API integration, automated visa application submission, passport renewal reminder service, travel insurance claims processing.