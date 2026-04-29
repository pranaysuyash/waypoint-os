# Agent Performance & Workforce Management — Master Index

> Comprehensive research on agent performance metrics, scheduling, training, compensation, and workforce compliance for Indian travel agencies.

---

## Series Overview

This series explores how a modern travel agency platform manages its most valuable asset: its agents. From measuring individual performance and designing fair compensation to building skill-based routing and ensuring labor law compliance, every aspect of workforce management is covered with an India-specific lens.

**Target Audience:** Product managers, HR/operations teams, backend engineers building payroll/commission systems, frontend engineers building dashboards, compliance officers

**Key Constraint:** Indian travel agencies operate under a complex web of central and state labor laws (PF, ESI, TDS, Shops & Establishments, POSH, Maternity Benefit Act) that directly impact system design. Variable compensation (commission) is a significant portion of agent income and must be modeled with statutory compliance from day one.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [WORKFORCE_01_PERFORMANCE.md](WORKFORCE_01_PERFORMANCE.md) | Agent performance metrics, KPI framework, performance dashboards, goal tracking, review workflow, India salary structures |
| 2 | [WORKFORCE_02_SCHEDULING.md](WORKFORCE_02_SCHEDULING.md) | Shift management, coverage planning, workload balancing, skill-based routing, leave management, holiday staffing, India labor law compliance |
| 3 | [WORKFORCE_03_TRAINING.md](WORKFORCE_03_TRAINING.md) | Training management, learning paths by role, destination certifications, compliance training (GST, DPDP, AML), skill gap analysis, mentorship |
| 4 | [WORKFORCE_04_COMPENSATION.md](WORKFORCE_04_COMPENSATION.md) | Compensation structures, commission engine, bonus triggers, team incentives, ESOP/profit sharing, PF/ESI/TDS compliance |

---

## Key Themes

### 1. Performance as a System, Not a Scorecard

Agent performance in travel agencies is multidimensional. Revenue alone does not capture customer satisfaction, response speed, or operational accuracy. A weighted KPI framework (revenue, conversion, responsiveness, quality, operations, growth) with role-specific weights ensures agents are evaluated holistically. See WORKFORCE_01_PERFORMANCE for the full KPI model.

### 2. Skill-Based Everything

Modern travel agencies route customers to agents based on skill, not availability alone. A Kerala honeymoon query should reach a Kerala-certified, Hindi-speaking honeymoon specialist, not the next available agent. This requires skill profiles, routing algorithms, and a continuous skill development engine. See WORKFORCE_02_SCHEDULING for routing and WORKFORCE_03_TRAINING for skill development.

### 3. Commission as First-Class Data

Commission is not a payroll afterthought -- it is often 30-60% of a top performer's take-home pay. The commission calculation engine must handle tiered rates, destination-based multipliers, customer tier adjustments, caps, clawbacks, and statutory deductions (TDS, PF, ESI). See WORKFORCE_04_COMPENSATION for the full commission engine design.

### 4. India Regulatory Compliance by Default

Every workforce management system must account for:
- **Central Acts:** PF (EPF), ESI, Payment of Wages, Minimum Wages, Gratuity, Maternity Benefit, POSH, Payment of Bonus
- **State Acts:** Shops & Establishments (registration, working hours, holidays vary by state), Professional Tax (rate varies by state)
- **Tax:** TDS on salary (Section 192), TDS on commission (Section 194H), TCS on overseas packages (Section 206C)
- **Data Protection:** DPDP Act, 2023 (customer data handling, consent management)

Non-compliance penalties range from ₹1,000 per Shops & Est. violation to ₹250 crore per DPDP Act violation. Compliance is not optional.

### 5. Seasonality as a Design Constraint

Indian travel is highly seasonal (Oct-Mar international peak, Apr-Jun domestic peak, Jul-Sep monsoon lull). Performance targets, commission rates, staffing levels, and training schedules must all account for seasonality. Static annual plans fail in this industry.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Agent Training (AGENT_TRAINING_*) | Training content, onboarding, knowledge management |
| Commission Tracking (COMMISSION_*) | Commission calculation, tracking, payouts, reporting |
| Analytics & BI (ANALYTICS_*) | Performance dashboards, metrics, predictive analytics |
| CRM (CRM_*) | Customer relationship data feeding performance metrics |
| Help Desk (HELP_DESK_*) | Customer satisfaction and complaint metrics |
| Agency Settings (AGENCY_SETTINGS_04_*) | Team management, role configuration |
| Regulatory Compliance (REGULATORY_*) | IATA licensing, travel-specific regulations |
| Data Governance (DATA_GOVERNANCE_*) | Employee data privacy, DPDP Act compliance |
| Finance (FINANCE_*) | Payroll integration, accounting for commissions |
| Workspace (WORKSPACE_*) | Agent workspace with performance widgets |
| Gamification (GAMIFICATION_*) | Leaderboards, badges, achievement systems |
| Mobile App (MOBILE_APP_*) | Agent mobile access to performance data |
| Offline Mode (OFFLINE_*) | Performance metrics caching for offline access |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| KPI Engine | Custom TypeScript service | Weighted KPI calculation with seasonal adjustments |
| Dashboard Charts | Recharts / Chart.js | Performance visualization (sparklines, funnels, leaderboards) |
| Commission Engine | Custom rule engine (Drools-style) | Multi-rule commission calculation with caps and overrides |
| Payroll Integration | RazorpayX Payroll / Zoho Payroll API | Salary processing with statutory deductions |
| Shift Scheduling | Custom + calendar sync (Google/Outlook) | Shift templates, rotations, coverage planning |
| Skill Routing | Custom algorithm (hybrid weighted) | Skill-based agent-customer matching |
| LMS | Docebo / TalentLMS / Moodle | Training content delivery and assessment |
| Compliance Calendar | Custom notification service | Statutory deadline tracking and alerts |
| ESOP Management | Vega / Trustio / ESOP Direct | ESOP grants, vesting, exercise tracking |
| HRMS | Darwinbox / Keka / Zoho People | Employee records, leave, attendance |
| Analytics | PostHog / Custom warehouse | Training effectiveness, performance trends |
| Notification | FCM / SNS / WhatsApp Business API | Shift alerts, review reminders, commission credits |

---

**Created:** 2026-04-28
