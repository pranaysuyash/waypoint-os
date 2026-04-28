# Persona: Corporate Travel Manager (CTM)

**Date Created:** 2026-04-28
**Persona ID:** P4
**Archetype:** Corporate Travel Manager / Business Travel Specialist
**Related Docs:** `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` (Tier 2: Corporate Travel Manager), `Docs/DETAILED_AGENT_MAP.md`

---

## 1. Profile Summary

| Attribute | Detail |
|-----------|--------|
| **Name** | Vikram Sethi (pseudonym) |
| **Age** | 42 |
| **Location** | Bangalore, India |
| **Role** | Corporate Travel Manager, TechCorp (1,200 employees) |
| **Experience** | 12 years in corporate travel; managed travel for 3 companies |
| **Team Size** | 4 people — 2 booking coordinators, 1 visa specialist, 1 finance liaison |
| **Annual Travel Spend** | ~₹18Cr (flights, hotels, cabs, visas, insurance) |
| **Tech Stack** | Concur (expense), SAP Concur (travel), Excel (tracking), WhatsApp (with travelers) |
| **Biggest Frustration** | "I'm spending ₹18Cr a year and I can't tell you which vendor is overcharging me." |

---

## 2. The Real Job (Day-to-Day)**

### Daily Responsibilities:**

1. **Policy Enforcement:** Ensure all bookings comply with company travel policy (max ₹8K/night for managers, ₹12K for VPs, economy flights under 6 hours, business class above).
2. **Cost Optimization:** Negotiate bulk rates with hotels near office locations, maintain preferred airline partnerships, track fare trends.
3. **Traveler Support:** Handle escalations — flight cancellations, visa rejections, medical emergencies abroad.
4. **Reporting & Analytics:** Monthly reports to CFO: "We spent ₹1.5Cr this month. Here's where, why, and how to reduce it."
5. **Vendor Management:** Renew contracts with hotel chains, negotiate corporate rates with airlines, manage cab partnerships.
6. **Compliance & Safety:** Ensure all travelers have valid visas, travel insurance, and emergency contacts. Track "duty of care" requirements.

### Tools They Use Today:**

| Tool | Purpose | Pain |
|------|---------|------|
| **Concur** | Booking + expense integration | Expensive (₹400/user/year), clunky UI, slow |
| **Excel** | Cost tracking, vendor performance | Manual, error-prone, no real-time data |
| **Email** | Vendor negotiations, approvals | 150+ emails/day, buried approvals |
| **WhatsApp** | Traveler support, crisis response | No audit trail, 47 groups for 1,200 employees |
| **Memory** | "Hotel X is reliable near Whitefield office" | Dies when Vikram takes leave |

### Key Pressures:**

- **Cost pressure:** CFO asks: "Why did we spend ₹18Cr this year? Show me the breakdown."
- **Policy violations:** "Manager booked ₹15K/night hotel when policy says ₹8K. Who approved this?"
- **Traveler complaints:** "Flight was at 6 AM, I'm exhausted." "Hotel had no wifi." "Cab didn't show up."
- **Vendor overcharging:** "We're paying ₹10K/night at Hotel X, but Booking.com shows ₹7K."
- **Knowledge loss:** When Vikram is out, nobody knows which hotels are reliable, which airlines delay frequently.

---

## 3. Industry Context**

### How This Role Varies:**

| Company Size | Travel Manager Role |
|--------------|----------------------|
| **<200 employees** | Usually HR or Ops person handles travel part-time |
| **200-1,000** | Dedicated travel manager, 1-2 supporting staff |
| **1,000-5,000** | Team of 4-8, specialized by region/vendor |
| **5,000+** | Full department, often outsourced to corporate travel agencies |

### Certifications/Qualifications:**

- **GBTA (Global Business Travel Association)** certification preferred
- **IATA/ARC** accreditation for corporate ticketing
- **MBA in Operations/Finance** (common for senior roles)
- Most learn on the job: "Nobody teaches you how to negotiate with Taj Hotels"

---

## 4. Current System Coverage**

### What the Codebase Implements That Serves This Role:**

| Feature | File | Coverage |
|---------|------|---------|
| **Budget enforcement** | `src/intake/decision.py` (budget vs. actual) | ⚠️ Partial — individual trip, not policy |
| **Preferred vendor tracking** | Not implemented | ❌ None |
| **Cost analytics** | Not implemented | ❌ None |
| **Policy compliance checking** | Not implemented | ❌ None |
| **Duty of care (visa/insurance)** | `src/intake/decision.py` (hard blockers) | ⚠️ Partial — visa only |

### What Should Exist (Gaps):**

| Gap | Why Critical | Impact |
|-----|-------------|--------|
| **Policy engine** | "Manager can't book >₹8K/night" | Prevents violations BEFORE booking |
| **Preferred vendor rate comparison** | "Are we overpaying Hotel X?" | Saves ₹50L-1Cr/year |
| **Traveler duty-of-care dashboard** | "Who's traveling? Where? Are they safe?" | Legal compliance |
| **Cost analytics by department** | "Engineering spent ₹4Cr, Sales spent ₹6Cr" | CFO reporting |
| **Vendor performance scoring** | "Hotel X had 3 complaints this month" | Data-driven contract renewals |
| **Approval workflow** | "Manager must approve >₹15K trips" | Policy enforcement |
| **Bulk rate negotiation support** | "We need 200 room-nights at Taj, what's the best rate?" | Leverages ₹18Cr spend |

---

## 5. AI Agent Specification (Corporate Travel Manager Agent)**

### Role: Policy & Compliance Agent

| Attribute | Detail |
|-----------|--------|
| **Type** | Validator / Policy Enforcer |
| **Purpose** | Ensures all bookings comply with corporate travel policy before confirmation |
| **Inputs** | `trip_brief`, `company_policy_rules`, `traveler_grade` (Junior/Mid/VP), `preferred_vendor_rates` |
| **Outputs** | `policy_violations[]`, `suggested_alternatives[]`, `approval_required` (boolean) |
| **Decision Authority** | BLOCK bookings that violate policy; ESCALATE to manager for overrides |
| **Escalation Triggers** | Booking >2x policy limit, traveler grade mismatch, non-preferred vendor used without justification |
| **Boundaries** | Cannot approve policy overrides (human manager only); cannot renegotiate vendor rates (human only) |

### Example Decision Flow:**

```
Input: "Book Taj West End, ₹14K/night, for Manager-grade employee. Company policy: Max ₹8K/night."

Agent Decision:
  - ❌ POLICY VIOLATION: ₹14K > ₹8K (Manager grade)
  - ✅ Alternative: "Taj budget hotel, ₹7.5K/night, preferred vendor"
  - ⚠️ Escalation: "Manager requests override. Requires VP approval (2x policy)."
```

---

## 6. Scenario Coverage (To Be Built)**

| Scenario ID | Scenario Name | What It Tests | Priority |
|-------------|---------------|--------------|----------|
| **P4-S1** | Policy Violation Catch | System catches a Manager booking a VP-grade hotel | P0 |
| **P4-S2** | Preferred Vendor Rate Check | "Hotel X charging us ₹10K, market rate ₹7K" | P0 |
| **P4-S3** | Bulk Rate Negotiation | "200 room-nights, what's our best negotiated rate?" | P1 |
| **P4-S4** | Duty-of-Care Dashboard | "Who's traveling to Thailand? Any visa issues?" | P1 |
| **P4-S5** | Cost Analytics Report | "Engineering spent ₹4Cr this quarter, here's the breakdown" | P2 |
| **P4-S6** | Approval Workflow | "Manager approves trip >₹15K, auto-escalate to VP" | P1 |
| **P4-S7** | Traveler Grade Mismatch | "Junior engineer booked business class — flag and block" | P0 |
| **P4-S8** | Vendor Performance Scoring | "Hotel X had 3 complaints this month, suggest alternatives" | P2 |

---

## 7. Key Quotes (Simulated)**

> "I'm spending ₹18Cr a year and I can't tell you which vendor is overcharging me."

> "Concur costs ₹400 per user per year for 1,200 employees. That's ₹4.8L just for the software. And it's STILL clunky."

> "When I'm on leave, nobody knows that Hotel X near Whitefield is reliable and Hotel Y has cockroach complaints. That knowledge is in my head."

> "The CFO asks: 'Why did we spend ₹18Cr?' I have to build an Excel sheet for 3 days to answer that."

> "If a system could tell me: 'You're overpaying Hotel X by 30%, here are 3 alternatives at your preferred rate,' that alone is worth ₹50L a year."

---

## 8. Methodology Notes**

- Persona created based on Tier 2 (Corporate Travel Manager) in `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` (lines 65-130 approx).
- Corporate travel dynamics drawn from real-world GBTA frameworks and Concur/SAP enterprise workflows.
- Policy engine concept inspired by gaps in current system: no policy checking, no preferred vendor tracking, no cost analytics.
- **Next Step:** Build scenarios P4-S1 through P4-S8 as separate files in `Docs/personas_scenarios/`.
- **Validation:** Check with real corporate travel managers at mid-size (500-2,000 employee) companies. Their ₹5-20Cr annual spend creates acute pain that boutique agencies don't face.
