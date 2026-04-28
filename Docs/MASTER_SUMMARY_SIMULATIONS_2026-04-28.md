# Master Summary: Simulated Interviews, Personas, and Scenarios

**Date:** 2026-04-28
**Purpose:** Comprehensive index of all simulations created in this session
**Files Created:** 15+ new documents across `Docs/` and `Docs/personas/`

---

## 1. Simulated User Interviews Created

| # | File | Persona | Duration | Key Insight |
|---|------|----------|----------|---------|
| 1 | `SIMULATED_USER_INTERVIEW_2026-04-27.md` | **P1: Solo Agent (Priya)** | ~50 min | "The tool understands clients but then what? I can't generate proposals." |
| 2 | `SIMULATED_USER_INTERVIEW_AGENCY_OWNER_2026-04-28.md` | **P2: Agency Owner (Rajesh)** | ~55 min | "I don't want to review proposals. I want proposals to be good enough that I don't need to." |
| 3 | `SIMULATED_USER_INTERVIEW_JUNIOR_AGENT_2026-04-28.md` | **P3: Junior Agent (Amit)** | ~45 min | "The tool taught me WHAT to ask. Now teach me WHY, so I become a senior faster." |
| 4 | `SIMULATED_USER_INTERVIEW_TRAVELER_2026-04-28.md` | **S2: Family Coordinator (Meera)** | ~50 min | "After Singapore, she forgot my father-in-law uses a walker. We felt like STRANGERS again." |
| 5 | `SIMULATED_USER_INTERVIEW_SUPPLIER_2026-04-28.md` | **New: Hotel Supplier (Dinesh)** | ~50 min | "The tool is smart for the AGENT. But that intelligence doesn't flow to ME — the person delivering the service." |
| 6 | `SIMULATED_USER_INTERVIEW_OTA_SWITCHER_2026-04-28.md` | **New: OTA Switcher (Sunita)** | ~50 min | "I pay Priya commission for personalised service. If she doesn't REMEMBER me, why am I not just on MakeMyTrip?" |
| 7 | `SIMULATED_USER_INTERVIEW_CORPORATE_TM_2026-04-28.md` | **New: Corporate TM (Vikram)** | ~55 min | "I'm spending ₹18Cr a year and I can't tell you which vendor is overcharging me." |

---

## 2. New Personas Created

| ID | File | Persona | Role | Annual Spend/Impact |
|----|------|----------|------|-------------------|
| **P4** | `personas/PERSONA_CORPORATE_TRAVEL_MANAGER.md` | **Vikram Sethi** — Corporate Travel Manager | Manages ₹18Cr travel spend for 1,200 employees | CFO reporting, policy enforcement, vendor negotiations |
| **P5** | `personas/PERSONA_DMC_LIAISON.md` | **Anjali Perera** — DMC Liaison | Handles 400 leads/year, 120 bookings | Destination intelligence, rate sheets, margin protection |

### Persona P4 (Corporate Travel Manager) Key Facts:
- **Pain:** "Concur costs ₹4.8L/year and it's STILL clunky."
- **Buying Trigger:** Policy engine (auto-reject grade violations) + vendor rate comparison
- **Willingness to Pay:** ₹1L/month for 1,000+ employees (₹12L/year = 2.5x cheaper than Concur)
- **Gating Factor:** Must integrate with SAP for expense automation

### Persona P5 (DMC Liaison) Key Facts:
- **Pain:** "70% of leads are impossible. $2,000 for Maldives? That's not a lead, that's a waste of time."
- **Moat:** Local intelligence ("whale watching in July = 5% success") that OTAs don't have
- **Willingness to Pay:** Preferred DMC status in sourcing hierarchy (more agency leads)
- **Biggest Frustration:** Rate sheets go stale after 30 days; agencies quote wrong prices

---

## 3. New Scenarios Created

### P4 (Corporate Travel Manager) Scenarios:

| ID | File | Scenario | Priority | Key Metric |
|----|------|----------|----------|-------------|
| **P4-S1** | `personas_scenarios/P4-S1_POLICY_VIOLATION.md` | P0 | Grade 3 + ₹14K hotel = BLOCK (policy limit ₹8K) |
| **P4-S2** | `personas_scenarios/P4-S2_PREFERED_VENDOR_RATE.md` | P0 | Hotel X ₹9K vs. Preferred IHG ₹6.5K (₹2.5K savings/night) |
| **P4-S3** | `personas_scenarios/P4-S3_BULK_RATE_NEGOTIATION.md` | P1 | ₹80L annual spend → Negotiate 20% discount (save ₹16L) |
| **P4-S4** | `personas_scenarios/P4-S4_DUTY_OF_CARE.md` | P1 | Coup in Thailand → 3 employees there → Evacuation protocol <2 hours |
| **P4-S5** | `personas_scenarios/P4-S5_CFO_REPORT.md` | P1 | Auto-generate ₹18Cr quarterly report in 5 min (saves 12-16 days/year) |
| **P4-S6** | `personas_scenarios/P4-S6_APPROVAL_WORKFLOW.md` | P1 | ₹3L trip (Grade 3) → VP approval required |
| **P4-S7** | `personas_scenarios/P4-S7_GRADE_MISMATCH.md` | P0 | Junior books business class → BLOCK (economy only for Grade 1-3) |
| **P4-S8** | `personas_scenarios/P4-S8_VENDOR_PERFORMANCE.md` | P2 | Hotel X: 3.2/5 score (12 room-size complaints) → Reduce discount |

### P5 (DMC Liaison) Scenarios:

| ID | File | Scenario | Priority | Key Metric |
|----|------|----------|----------|-------------|
| **P5-S1** | `personas_scenarios/P5-S1_IMPOSSIBLE_BUDGET.md` | P0 | $2,000 for Maldives (min $3,200) → Auto-reject + suggest Sri Lanka |
| **P5-S2** | `personas_scenarios/P5-S2_DESTINATION_INTELLIGENCE.md` | P0 | Whale watching in July = 5% success → Suggest dolphins (60%) |
| **P5-S3** | `personas_scenarios/P5-S3_MARGIN_SPLIT.md` | P1 | DMC margin 33% (target 18%), Agency $0 → Add 15% commission |
| **P5-S4** | `personas_scenarios/P5-S4_LOCAL_ACTIVITY.md` | P1 | "Best house reef" → Resort X (north atoll), not generic "House Reef" |
| **P5-S5** | `personas_scenarios/P5-S5_LEAD_FEASIBILITY.md` | P0 | Family of 10, 2 days, Maldives → Reject (min 4 days) |
| **P5-S6** | `personas_scenarios/P5-S6_CRISIS_PROTOCOL.md` | P2 | Cyclone warning → 3 clients affected → Protocols in 25 minutes |
| **P5-S7** | `personas_scenarios/P5-S7_RELATIONSHIP_FLAG.md` | P2 | Agency X overpromised 5/15 times (33%) → Flag + reduce leads 50% |
| **P5-S8** | `personas_scenarios/P5-S8_RATE_SHEET_FRESHNESS.md` | P1 | Rate sheet 45 days old → Agencies quoting ₹300 (now ₹380) |

---

## 4. Cross-Cutting Findings (All Interviews)

### Finding 1: The "Last Mile" Problem Is Universal**
- **Priya (P1):** Can't generate proposals (4 hours → minutes is the dream)
- **Rajesh (P2):** Can't scale quality across 14 agents (confidence-gated approvals needed)
- **Amit (P3):** Can't verify system outputs (75 min verification vs. 10 min generation)
- **Meera (S2):** Can't see trip options with family (WhatsApp relay burden)
- **Dinesh (P5):** Doesn't receive the intelligence the tool generates (supplier brief gap)
- **Sunita (OTA Switcher):** Misses OTA features (reviews, instant booking, price transparency)
- **Vikram (P4):** Can't see vendor overpayments (₹45L/year wasted)

### Finding 2: Memory/Personalization Is the Loyalty Driver**
- **Priya → Client:** "Priya knows us so well" = repeat business
- **Meera → Agent:** "She forgot my father-in-law uses a walker" = feels like a stranger
- **Sunita → OTA Switch:** "MakeMyTrip didn't remember. I pay Priya to REMEMBER."

### Finding 3: Factual Accuracy Is Existential Risk**
- **Rajesh:** "Wrong visa info = lawsuit + reputation destroyed"
- **Amit:** "I trust the system after 3 weeks. If it's wrong, I won't catch it."
- **Dinesh:** "10-year-old celiac got sick because dietary wasn't flow to me."

### Finding 4: Pricing Models Must Be Tiered**
| Segment | Tool Price | Value Proposition | ROAS Example |
|----------|------------|-------------------|--------------|
| **Solo Agent** | ₹999-1,499/month | Save 1-2 deals/month = ₹40-100K value | 30-70x |
| **Small Agency (3-5 agents)** | ₹3,999-6,999/month | Standardize quality, train juniors 2x faster | 10-20x |
| **Corporate (1,000+ employees)** | ₹1L/month (₹12L/year) | Save ₹45L/year on overpayments alone | 4x vs. Concur (₹4.8L/year) |

### Finding 5: AI Must Be Invisible to Clients**
- **Priya:** "If clients find out an AI planned their trip, I'm done."
- **Meera:** "As long as it feels like Priya wrote it, I'm fine."
- **Sunita:** "I pay commission for HER expertise. If a robot planned it, I want my money back."

---

## 5. Prioritized Implementation Roadmap

### Phase 1: Make It Usable (P1 Persona — Solo Agents)
| Feature | Why | Files to Create |
|---------|-----|-----------------|
| **Proposal Generator** | Solves 4-hour → 15-min gap | `src/proposal/generator.py`, `frontend/components/ProposalBuilder.tsx` |
| **Trip Workspace** | Multi-trip context (Priya has 15 active) | `src/workspace/`, `frontend/components/TripWorkspace.tsx` |
| **Customer Memory** | "Repeat customer" detection | `src/customer/`, `frontend/components/CustomerProfile.tsx` |
| **Follow-up Reminders** | Ghost detection (72h silence) | `src/lifecycle/reminders.py`, `frontend/components/GhostAlert.tsx` |

### Phase 2: Make It Adoptable (P2 Persona — Agency Owners)
| Feature | Why | Files to Create |
|---------|-----|-----------------|
| **Confidence-gated Approval** | Scale quality without Rajesh | `src/approval/workflow.py`, `frontend/components/ApprovalGate.tsx` |
| **Margin Dashboard (Owner Only)** | Revenue visibility | `src/analytics/margins.py`, `frontend/components/MarginDashboard.tsx` |
| **Agent Performance Tracking** | Junior ramp-up visibility | `src/analytics/agents.py`, `frontend/components/AgentPerformance.tsx` |
| **Workload Distribution** | Balanced utilization | `src/workload/`, `frontend/components/WorkloadView.tsx` |

### Phase 3: Make It an OS (P4/P5 Personas — Enterprise + Suppliers)
| Feature | Why | Files to Create |
|---------|-----|-----------------|
| **Policy Engine (P4)** | ₹45L/year saved on violations | `src/policy/engine.py`, `frontend/components/PolicyViolationBanner.tsx` |
| **Vendor Rate Comparison (P4)** | ₹45L/year saved vs. market | `src/vendor/rate_checker.py`, `frontend/components/VendorRateAlert.tsx` |
| **DMC Rate Sheet Upload (P5)** | Eliminates "sold out" surprises | `src/dmc/rate_upload.py`, `frontend/components/RateSheetUpload.tsx` |
| **Destination Intelligence (P5)** | "Whale watching in July = NO" | `src/dmc/intelligence.py`, `data/destination_intelligence/` |

---

## 6. File Inventory

### Interviews (7 files):
```
Docs/
├── SIMULATED_USER_INTERVIEW_2026-04-27.md                      (Priya, P1)
├── SIMULATED_USER_INTERVIEW_AGENCY_OWNER_2026-04-28.md    (Rajesh, P2)
├── SIMULATED_USER_INTERVIEW_JUNIOR_AGENT_2026-04-28.md   (Amit, P3)
├── SIMULATED_USER_INTERVIEW_TRAVELER_2026-04-28.md      (Meera, S2)
├── SIMULATED_USER_INTERVIEW_SUPPLIER_2026-04-28.md      (Dinesh, P5-Supplier)
├── SIMULATED_USER_INTERVIEW_OTA_SWITCHER_2026-04-28.md   (Sunita, OTA Switcher)
└── SIMULATED_USER_INTERVIEW_CORPORATE_TM_2026-04-28.md  (Vikram, P4)
```

### New Personas (2 files):
```
Docs/personas/
├── PERSONA_CORPORATE_TRAVEL_MANAGER.md    (P4 - Vikram)
└── PERSONA_DMC_LIAISON.md                (P5 - Anjali)
```

### New Scenarios (16 files):
```
Docs/personas_scenarios/
├── P4-S1_POLICY_VIOLATION.md          (Grade 3 + ₹14K hotel → BLOCK)
├── P4-S2_PREFERED_VENDOR_RATE.md      (Hotel X ₹9K vs. IHG ₹6.5K)
├── P4-S3_BULK_RATE_NEGOTIATION.md   (₹80L spend → 20% discount)
├── P4-S4_DUTY_OF_CARE.md             (Coup → evacuation protocol)
├── P4-S5_CFO_REPORT.md               (₹18Cr quarterly report in 5 min)
├── P4-S6_APPROVAL_WORKFLOW.md         (VP approval for >₹50K trips)
├── P4-S7_GRADE_MISMATCH.md           (Junior + business class → BLOCK)
├── P4-S8_VENDOR_PERFORMANCE.md        (Hotel X: 3.2/5 → reduce discount)
├── P5-S1_IMPOSSIBLE_BUDGET.md         ($2,000 for Maldives → reject)
├── P5-S2_DESTINATION_INTELLIGENCE.md   (Whale watching July = 5%)
├── P5-S3_MARGIN_SPLIT.md              (DMC 33% + Agency $0 → fix)
├── P5-S4_LOCAL_ACTIVITY.md            (Best house reef → Resort X)
├── P5-S5_LEAD_FEASIBILITY.md         (Family of 10, 2 days → reject)
├── P5-S6_CRISIS_PROTOCOL.md           (Cyclone → 3 protocols in 25 min)
├── P5-S7_RELATIONSHIP_FLAG.md         (Agency X 33% overpromise → flag)
└── P5-S8_RATE_SHEET_FRESHNESS.md      (Rate sheet 45 days old → alert)
```

---

## 7. Next Steps

1. **Validate with real users:** These are ALL simulated. Before building anything, validate with 1-2 real users per persona.
2. **Start with Phase 1:** Solo agents (P1) are the wedge. Build proposal generator + trip workspace first.
3. **Instrument the gaps:** Every `❌ Not implemented` in the scenario files is a ticket. Every `✅ Partial` is a 1-day fix.
4. **Document as you build:** Every new file you create → add to `Docs/CODEBASE_ANALYSIS_2026-04-12.md` (or create an update).
5. **Run the real interviews:** The simulated ones are a starting point. The real ones will surprise you.

---

## 8. Methodology Notes

- **All interviews are simulated** based on existing documentation in the repository.
- **Personas P4 and P5** are NEW (not in original docs). They fill critical gaps: corporate travel and DMC/supplier perspectives.
- **Scenarios P4-S1 through P5-S8** are NEW (not in original `test_scenarios_catalog.md`). They cover enterprise and supplier use-cases.
- **Real validation needed:** Every insight here is extrapolated from docs, not real user conversations. The real interviews will uncover different (likely messier) truths.
- **No code changes:** Per user instruction, all documents are written, no git commands, no code modifications.
