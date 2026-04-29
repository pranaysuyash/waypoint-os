# Tour Guide & Escort Management — Master Index

> Comprehensive research on tour guide profiles, assignment algorithms, day-of-tour operations, and performance analytics.

---

## Series Overview

This series covers how Waypoint OS manages the complete guide lifecycle — from profile and certification management through intelligent trip matching, real-time tour operations, and performance analytics.

**Target Audience:** Operations team, HR, backend engineers, UX designers

**Key Constraint:** Indian tour guides are a mix of full-time, freelance, and contract workers with varying certification levels across states

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [TOUR_GUIDE_01_PROFILES.md](TOUR_GUIDE_01_PROFILES.md) | Guide profiles, certifications, skill matrix, availability |
| 2 | [TOUR_GUIDE_02_ASSIGNMENT.md](TOUR_GUIDE_02_ASSIGNMENT.md) | Matching algorithm, multi-guide planning, substitution, briefing |
| 3 | [TOUR_GUIDE_03_OPERATIONS.md](TOUR_GUIDE_03_OPERATIONS.md) | Real-time tracking, check-in, incidents, modifications, debrief |
| 4 | [TOUR_GUIDE_04_PERFORMANCE.md](TOUR_GUIDE_04_PERFORMANCE.md) | KPIs, scoring, training gaps, seasonal trends, benchmarking |

---

## Key Themes

### 1. Skill-Based Matching
Guides are matched to trips using a weighted scoring algorithm that considers destination expertise, language skills, specialization, availability, and cost fit.

### 2. Real-Time Operations Support
Live tour tracking with location sharing, customer check-in, incident management, and ops dashboard support guides during active tours.

### 3. Continuous Performance Improvement
Multi-dimensional performance scoring identifies training gaps and drives professional development through data, not guesswork.

### 4. Multi-Guide Coordination
Large groups and multi-destination trips require coordinated guide teams with clear roles, handoff protocols, and shared briefing documents.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Workforce (WORKFORCE_*) | Agent scheduling, compensation, training |
| Vendor Management (VENDOR_*) | Guide as a vendor type |
| Activities & Experiences (ACTIVITIES_*) | Activity-specific guide requirements |
| Group Travel (GROUP_*) | Multi-guide assignment for large groups |
| Customer Portal (CUSTOMER_PORTAL_*) | Guide rating and review display |
| Risk Assessment (RISK_*) | Tour safety protocols |
| Mobile Experience (MOBILE_*) | Guide mobile app |
| Workspace (WORKSPACE_*) | Guide assignment in agent workspace |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Profile Management | Custom | Guide CRUD, certifications, skills |
| Matching Engine | Custom algorithm | Weighted scoring and ranking |
| Real-time Tracking | WebSocket + GPS | Live tour monitoring |
| Check-in System | QR codes + GPS | Customer attendance tracking |
| Incident Management | Custom workflow | Escalation and resolution |
| Performance Analytics | Custom + charts | KPI dashboards and scoring |

---

**Created:** 2026-04-29
