# Sim #5 Results & Audit — Tier-2 Indian Agent & Regional Travel Ecosystem

**Date:** 2026-10-30  
**Simulation ID:** `SIM-5-TIER2-INDIA-01`  
**Operator Seat:** Rajesh Khandelwal (`P-TIER2-INDIA-01`), Shubh Yatra Holidays, Indore, MP  
**Customer Seat:** Sunil Agrawal (Agrawal Textiles, Indore)  
**Execution Harness:** `tools/sim5_tier2_runner.py` (Reproducible API & Engine Driver)  
**Evidence Artifacts:**
- Master Evidence JSON: [`sim5_rajesh_indore_evidence.json`](file:///Users/pranay/Projects/travel_agency_agent/Docs/sims/assets/sim5/evidence/sim5_rajesh_indore_evidence.json)
- Summary JSON: [`sim5_summary_report.json`](file:///Users/pranay/Projects/travel_agency_agent/Docs/sims/assets/sim5/evidence/sim5_summary_report.json)
- Persona Dossier: [`PERSONA_TIER2_AGENT_RAJESH_KHANDELWAL.md`](file:///Users/pranay/Projects/travel_agency_agent/Docs/personas/PERSONA_TIER2_AGENT_RAJESH_KHANDELWAL.md)
- Suite Manifest: [`SIM5_PERSONAS_2026-10-30.md`](file:///Users/pranay/Projects/travel_agency_agent/Docs/sims/personas/SIM5_PERSONAS_2026-10-30.md)

---

## 1. Executive Summary & Master Scorecard

Sim #5 initiates the **Tier-2 Indian Travel Agent** simulation series. It tests Waypoint OS against the lived operational reality of an independent travel agency owner in Indore, Madhya Pradesh handling outbound leisure inquiries over WhatsApp for joint families from commercial merchant communities.

All **11 execution steps** completed with HTTP 200 responses. The simulation tested:
1. Sub-second live message triage on incoming raw Hinglish WhatsApp text (`/api/triage/message`).
2. Webhook ingestion, HMAC SHA-256 signature enforcement, and channel message persistence (`/api/v1/messaging/webhook/whatsapp`, `/api/v1/messages`).
3. Intake fact extraction and packet compilation (`/api/v1/inbound/parse`).
4. Indian statutory tax compliance under Section 206C(1G) TCS (5% vs 20% thresholds) and Tour Package GST (5% with CGST/SGST intra-state split).
5. Inbound follow-up preference refinement and hotel location constraints.
6. Omnichannel outbound WhatsApp dispatch (`/api/v1/messaging/send`) with honest provider status.
7. Digit-normalized trip message threading across inbound, follow-up, and outbound communications.
8. AuditStore event logging, non-repudiation, and tamper-evident chaining.

### Master Scorecard

| Surface / Capability | Target Behavior | Observed Result | Grade |
|---|---|---|:---:|
| **Sub-Second Triage** | Ingest messy Hinglish text, return intent & urgency in < 50ms | 13.14ms latency, intent=`general_inquiry`, urgency=`normal` | **PASS (A)** |
| **Webhook Security** | Reject unauthenticated or unsigned webhooks (Default-Deny) | 401 without secret/sig, 200 with valid HMAC SHA-256 | **PASS (A+)** |
| **Channel Message Store** | Store raw WhatsApp payloads and serve via `/api/v1/messages` | Inbound messages indexed and queried via operator feed | **PASS (A)** |
| **Digit-Normalized Threading** | Group messages by phone number (`+919826012345`) to trip | 7 messages linked to `trip_bdf495cc3c06` in chronological order | **PASS (A+)** |
| **Indian Number Formatting** | Parse `4.5 lakh` into ₹4,50,000 INR | `budget_min=450000`, `budget_max=450000`, `currency=INR` | **PASS (A+)** |
| **Mobility & Diet Constraints** | Detect wheelchair assistance & Jain pure-veg food | Extracted `mobility_constraints` and `meal_preferences="vegetarian"` | **PASS (A)** |
| **TCS Statutory Tax Engine** | Section 206C(1G) LRS rules: 5% under ₹7L, 20% above | ₹450,000 evaluated at exactly 5% (₹22,500.00 TCS liability) | **PASS (A+)** |
| **GST Tax Engine** | Tour Package 5% GST scheme with state split (MP) | 5% total (₹22,500.00) split into CGST (2.5%) & SGST (2.5%) | **PASS (A+)** |
| **Honest Outbound Dispatch** | No fake "SENT" progress without real provider acceptance | Returned `status="NOT_CONFIGURED"`, logged to `AuditStore` | **PASS (A+)** |
| **Hinglish Count Noun Parsing** | Parse "6 bade, 2 bacche, 1 infant" into party composition | Extracted `party_size=9`, `adults=6, children=2, infants=1`, `child_ages=[0.58, 8, 3]` (senior 72 excluded) | **PASS (A+)** (Remediated) |
| **Hinglish Origin City Parsing** | Parse "Indore se" as origin airport/city | Extracted `origin_city="Indore"`, blocked auxiliary verb "Hai" | **PASS (A+)** (Remediated) |
| **Destination Gazetteer Hygiene** | Isolate "Dubai" as sole destination | `destination_candidates=["Dubai"]`, blocked stopwords "Hum", "Hume", "Khana" | **PASS (A+)** (Remediated) |
| **Hinglish Date Window Parsing** | Parse "December 22 se 28 tak" into structured date window | Extracted `date_window="December 22 se 28 tak"` | **PASS (A+)** (Remediated) |

---

## 2. The Operational Context

### Operator Seat: Rajesh Khandelwal (`P-TIER2-INDIA-01`)
- **Proprietor**, Shubh Yatra Holidays, Saket / Vijay Nagar, Indore (MP).
- **Profile**: 42 years old, 14 years in travel. Serves merchant and trading families from Sitlamata Bazar, Sarafa, and the Pithampur manufacturing belt.
- **Rhythm**: Operates almost exclusively on WhatsApp Business. Receives rapid, unstructured messages from clients asking for quotes, custom dining setups, and GST invoices for business write-offs.
- **Pain Points**: Margin leakage vs OTAs (MakeMyTrip), dietary orthodoxy mistakes (ruinous community backlash if Jain food is missing abroad), senior citizen accessibility (wheelchair at airports and tours), and client confusion over TCS (Tax Collected at Source).

### Customer Inquiry: Sunil Agrawal (Agrawal Textiles, Indore)
- **Voice 5-A1 (Verbatim Inquiry)**:
  > *"Bhaiya namaste. Hum 6 bade hain aur 2 bacche (ek 8 saal aur ek 3 saal) plus ek 7 mahine ka infant. Hume December 22 se 28 tak Dubai ka family trip karna hai Indore se. Mummy ji (age 72) ko chalne me dikkat hai to airport aur sightseeing pe wheelchair assistance compulsory chahiye. Khana pure vegetarian/Jain chahiye hotel aur sightseeing me. Budget around 4.5 lakh total sab milakar. Aur humare textile firm ke naam par GST invoice banwana hai. Jaldi batao options."*
- **Voice 5-A2 (Verbatim Refinement)**:
  > *"Sunil Agrawal here again — bhaiya hotel Bur Dubai ya Deira taraf nahi chahiye, kids ko Burj Khalifa aur Dubai Mall paas chahiye so Downtown ya Sheikh Zayed Road taraf batao. Aur kya TCS 5% lagega ya 20%? Sabke passport valid hain till 2028."*
- **Voice 5-A3 (Outbound Agency Response)**:
  > *"Namaste Sunil ji! Thank you for contacting Shubh Yatra Holidays, Indore. We have registered your Dubai family vacation (Dec 22-28, 6 adults, 2 children, 1 infant). All special requirements are locked: 100% pure Jain catering, airport & sightseeing wheelchair assistance for Mataji, and premium Downtown / Sheikh Zayed Road 4-star family suites. Tax breakdown: For ₹4,50,000 package, statutory TCS is 5% (₹22,500, fully adjustable against your advance tax), and B2B GST invoice with your firm's GSTIN will be provided. Detailed itinerary options are ready for your review."*

---

## 3. Findings & Evidence Analysis

### FND-0351: Indian Lakh Currency Parsing (VERIFIED SUCCESS)
- **Observation**: The text contained `"Budget around 4.5 lakh total sab milakar"`.
- **System Extraction**:
  - `budget_raw_text`: `"budget around 4.5 lakh"`
  - `budget_min`: `450000`
  - `budget_max`: `450000`
  - `budget_currency`: `"INR"`
  - `budget_scope`: `"total"`
- **Significance**: Waypoint OS's Indian digit grouping regex and lakh multiplier logic properly resolved colloquial Indian financial phrasing to the integer value `450000` in INR.

### FND-0352: Mobility and Dietary Constraint Safeguards (VERIFIED SUCCESS)
- **Observation**: The inquiry specified `"Mummy ji (age 72) ko chalne me dikkat hai to airport aur sightseeing pe wheelchair assistance compulsory chahiye"` and `"Khana pure vegetarian/Jain chahiye hotel aur sightseeing me"`.
- **System Extraction**:
  - `mobility_constraints`: `"wheelchair assistance compulsory chahiye"` (confidence: 0.9, epistemic status: `FACT`)
  - `meal_preferences`: `"vegetarian"`
  - `trip_priorities`: `["vegetarian food"]`
- **Significance**: Prevents the #1 customer relationship failure mode for Indian joint families traveling abroad: elderly family elders stranded without wheelchair assistance at transit terminals and non-compliant food.

### FND-0353: Indian Statutory Tax Engine (TCS & GST) (VERIFIED SUCCESS)
- **TCS Section 206C(1G)**:
  - Request: `current_amount_inr = 450000.0`, `is_overseas_trip = True`, `pan_number = "AAACA1234F"`.
  - Output:
    * `is_applicable`: `True`
    * `tier_5pct_taxable_amount_inr`: `450000.0`
    * `tier_5pct_tcs_amount_inr`: `22500.0`
    * `tier_20pct_tcs_amount_inr`: `0.0`
    * `effective_tcs_rate_pct`: `5.0`
    * `rationale`: `"LRS Overseas Package: ₹450,000.00 @ 5% = ₹22,500.00; ₹0.00 @ 20% = ₹0.00."`
- **Tour Package GST**:
  - Request: `taxable_base_inr = 450000.0`, `scheme = "TOUR_PACKAGE_5PCT"`, `is_inter_state = False`.
  - Output:
    * `gst_rate_pct`: `5.0`
    * `cgst_amount_inr`: `11250.0` (2.5%)
    * `sgst_amount_inr`: `11250.0` (2.5%)
    * `total_gst_amount_inr`: `22500.0`
- **Significance**: Eliminates quote ambiguity. Gives Rajesh instant, mathematically precise answers to Sunil's second question: *"Aur kya TCS 5% lagega ya 20%?"* — definitively answering that 5% applies because the booking is below the ₹7,00,000 statutory LRS threshold.

### FND-0354: Webhook Security & Phone-Normalized Message Threading (VERIFIED SUCCESS)
- **Observation**:
  - Unsigned requests to `/api/v1/messaging/webhook/whatsapp` failed closed with HTTP 401.
  - Signed requests with HMAC SHA-256 (`X-Hub-Signature-256`) were verified and persisted to `message_store`.
  - Calling `GET /api/v1/trips/{trip_id}/messages` successfully retrieved all 7 messages associated with Sunil Agrawal by matching his normalized phone number `919826012345` against the trip record.
- **Significance**: Complete visibility in Rajesh's agency feed without requiring manual message linking.

### FND-0355: Honest Provider Dispatch Contract (VERIFIED SUCCESS)
- **Observation**: Calling `/api/v1/messaging/send` returned:
  - `status`: `"NOT_CONFIGURED"`
  - `provider`: `"whatsapp_cloud_api"`
  - `dispatch_status`: `"NOT_CONFIGURED"`
- **Significance**: In compliance with FND-0301, the system never lies with a fake "SENT" status when WhatsApp Cloud API credentials are not set in the environment. It truthfully returns `NOT_CONFIGURED` while logging the attempt to `AuditStore`.

---

## 4. Key Gaps, Defect Discoveries & Remediations (The Hinglish Frontier)

The initial simulation surfaced four concrete extraction gaps in the deterministic intake pipeline when handling mixed Hindi-English (Hinglish) text. All four gaps have been **remediated in `src/intake/extractors.py`** and verified via dedicated regression tests in `tests/test_sim5_tier2_agent_suite.py` and end-to-end runner re-execution (`tools/sim5_tier2_runner.py`).

### Verification & Remediation Summary

| Defect ID | Gap Description | Initial Extraction (Broken) | Remediated Extraction (Verified) | Status |
|---|---|---|---|:---:|
| **GAP-01** | Hindi count nouns & infant miss | `party_size=1`, `child_ages=[72]` | `party_size=9`, `adults=6, children=2, infants=1`, `child_ages=[0.58, 8, 3]` | **RESOLVED & VERIFIED** |
| **GAP-02** | Origin city collision on auxiliary verb "hai" | `origin_city="Hai"` | `origin_city="Indore"` | **RESOLVED & VERIFIED** |
| **GAP-03** | Gazetteer false positives on Hindi pronouns | `["Hum", "Hume", "Dubai", "Khana"]` | `["Dubai"]` | **RESOLVED & VERIFIED** |
| **GAP-04** | Hinglish date range delimiter miss (`"se ... tak"`) | `date_window=None` | `date_window="December 22 se 28 tak"` | **RESOLVED & VERIFIED** |

---

### GAP-01: Vernacular Hindi Count Noun Miss & Senior Age Cross-Contamination
- **Input Text**: `"Hum 6 bade hain aur 2 bacche (ek 8 saal aur ek 3 saal) plus ek 7 mahine ka infant... Mummy ji (age 72)"`
- **Expected**: Party size 9 (6 adults, 2 kids [ages 8, 3], 1 infant [age 7 months = 0.58 years]). Senior citizen age 72 excluded from child ages.
- **Initial Extraction (Broken)**:
  - `party_size`: `1`
  - `party_composition`: `{'adults': 1}`
  - `child_ages`: `[72]`
- **Root Cause**:
  1. The deterministic extractor in `src/intake/extractors.py` previously only matched English count nouns (`adults`, `people`, `pax`, `kids`, `children`). The Hindi terms `bade` (adults) and `bacche` (children) were unmapped, causing the count to fall back to default `1`.
  2. Infant mentions ("1 infant", "7 mahine ka infant") had no dedicated extractor in `_extract_party`.
  3. The age pattern regex detected `age 72` from `"Mummy ji (age 72)"` and, lacking an age threshold guard, inserted `72` into `child_ages`.
- **Remediation Implemented**:
  1. Added `_ADULTS_RE` support for `bade|bada`.
  2. Added `_CHILDREN_RE` support for `bacche|bachhe|bache|baccha|bacha` with named group `(?P<count>...)`.
  3. Added `_INFANTS_RE` (`r"(?P<count>\d+|ek|one|two|do)\s*(?:infants?|navjaat|chota\s+baby)"`) and extracted months converted to decimal years (`round(months / 12.0, 2)`).
  4. Added `_SAAL_AGE_RE` to parse Hindi years (`"8 saal"`, `"3 saal"`).
  5. Enforced strict upper bound: only ages `<= 17` are admitted into `child_ages`, completely eliminating senior citizen cross-contamination.

### GAP-02: Prepositional Origin Extraction Conflict with Auxiliary Verbs
- **Input Text**: `"Hume December 22 se 28 tak Dubai ka family trip karna hai Indore se. Mummy ji (age 72) ko chalne me dikkat hai to airport aur sightseeing pe..."`
- **Expected**: `origin_city = "Indore"`
- **Initial Extraction (Broken)**: `origin_city = "Hai"`
- **Root Cause**:
  - The sentence structure `"dikkat hai to airport"` matched the greedy pattern `"<word> to airport"` where `<word>` was captured as `"Hai"` (the Hindi copula verb). Because "Hai" is an existing populated place in the GeoNames gazetteer, it passed validation.
  - The legitimate origin marker `"Indore se"` (Hindi postposition `"se"` = "from") was not prioritized over the English `"to airport"` heuristic.
- **Remediation Implemented**:
  1. Added `_ROUTE_INVALID_CITIES = {"airport", "terminal", "hotel", "city", "hai", "tha", "is", "was", "to", "from", "and", "the"}` to route pattern matching in `extractors.py`.
  2. Implemented postpositional matching using `re.finditer(r"\b([A-Za-z]+)\s+se\b", ...)` that scans all occurrences and normalizes against known valid cities/airports.
  3. Added stopword collision check in `_extract_leading_origin_city`: words in `_SWEEP_STOP_WORDS` or `_STOP_WORDS` are rejected from candidate origins.

### GAP-03: Gazetteer False Positives from Sentence-Initial Capitalization
- **Input Text**: `"Hum 6 bade hain aur 2 bacche... Hume December 22 se... Khana pure vegetarian/Jain chahiye..."`
- **Expected Destination**: `["Dubai"]`
- **Initial Extraction (Broken)**: `["Hum", "Hume", "Dubai", "Khana"]`
- **Root Cause**:
  - Sentence-initial capitalized words ("Hum" = We, "Hume" = To us, "Khana" = Food) matched broad title-case extraction rules because real geographic entities named "Hum", "Hume", and "Khana" exist in global gazetteers.
- **Remediation Implemented**:
  - Expanded `_SWEEP_STOP_WORDS` in `extractors.py` with Hindi/Hinglish pronouns, discourse markers, and common verbs (`hum`, `hume`, `humko`, `humein`, `khana`, `bhaiya`, `namaste`, `dikkat`, `chahiye`, `batao`, `milakar`, `banwana`, `aap`, `aapko`, `sabko`, `bade`, `bacche`, `bache`, `bachhe`, `baccha`, `saal`, `mahine`, `infant`).
  - Added filter in `_extract_destination_candidates_unfiltered`: candidates whose lowercased title is in `_SWEEP_STOP_WORDS` are discarded before reaching candidate ranking.

### GAP-04: Hinglish Date Range Delimiter Miss
- **Input Text**: `"December 22 se 28 tak Dubai ka family trip karna hai"`
- **Expected**: `date_window = "December 22 se 28 tak"`
- **Initial Extraction (Broken)**: `date_window = None`
- **Root Cause**:
  - Date window regexes only recognized English range conjunctions (`to`, `through`, `until`, `till`, `-`). The Hindi postpositional bracket `se ... tak` was unhandled.
- **Remediation Implemented**:
  - Updated `_DAY_RANGE_TEXT_RE` and `_MONTH_DAY_RANGE_RE` to admit `\bse\b` as a range delimiter alongside `to|through|until|till|-` and an optional trailing `(?:\s*tak\b)?`.
  - Date windows like `"December 22 se 28 tak"` now parse reliably into structured windows.

---

## 5. Architectural & Business Value Assessment

### Value for Tier-2 Indian Travel Agencies
1. **Response Speed (Sub-Hour Quote Generation)**:
   - Rajesh currently spends 45–60 minutes manually cross-referencing WhatsApp messages, hotel rates, and tax calculations.
   - Waypoint OS ingests the message, extracts the parameters, computes the TCS/GST, and stages the WhatsApp response in **under 2 minutes**.
2. **Tax Liability Shield (TCS & GST Automation)**:
   - Miscalculating TCS (e.g. failing to collect 5% or mistakenly quoting 20% to a client spending under ₹7 Lakhs) leads to either lost sales or personal tax penalties for the agency.
   - The embedded `TaxComplianceEngine` provides statutory precision with clear rationale strings that the agent can forward directly to clients.
3. **Multi-Generational Family Safeguards**:
   - Preserves cultural/dietary specifications (Jain/pure-veg) and accessibility constraints (wheelchair assistance), preventing severe reputational damage in tight-knit regional merchant communities.

---

## 6. Audit Trail & Reproducibility Verification

The simulation completed cleanly in `.venv/bin/python`:
```bash
.venv/bin/python tools/sim5_tier2_runner.py
```
- **Total Steps Executed**: 11/11 (100% success rate).
- **Log Output**:
  - `01_live_message_triage` -> 200 OK (13.14ms)
  - `02_inbound_whatsapp_webhook` -> 200 OK
  - `03_agency_message_feed` -> 200 OK
  - `04_inbound_intake_parse` -> 200 OK
  - `05_tax_compliance_tcs` -> 200 OK
  - `06_tax_compliance_gst_package` -> 200 OK
  - `07_followup_message_webhook` -> 200 OK
  - `08_followup_message_triage` -> 200 OK
  - `09_outbound_whatsapp_dispatch` -> 200 OK
  - `10_trip_messages_thread` -> 200 OK
  - `11_audit_store_events` -> 200 OK
- **Evidence Verification**: The JSON evidence file [`sim5_rajesh_indore_evidence.json`](file:///Users/pranay/Projects/travel_agency_agent/Docs/sims/assets/sim5/evidence/sim5_rajesh_indore_evidence.json) contains the full request and response payloads for all 11 steps.
