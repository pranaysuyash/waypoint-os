# Agency Network & Franchise Management — Master Index

> Exploration of agency network models, branch operations, franchise lifecycle, consortium structures, and multi-entity platform architecture for scaling travel agencies in India.

---

## Series Overview

This series explores how a travel agency platform supports agencies scaling beyond a single office. From corporate multi-branch networks to franchise models and consortium alliances, the platform must serve fundamentally different governance, financial, and operational structures while sharing a common codebase.

**Target Audience:** Platform architects, backend engineers, product managers, business development teams

**Key Constraint:** Indian travel agencies operate in a fragmented regulatory environment (GST per entity, IATA accreditation tied to legal entity, state-level licenses) that makes network operations significantly more complex than in unified markets.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [FRANCHISE_01_NETWORK_MODEL.md](FRANCHISE_01_NETWORK_MODEL.md) | Network models (single, multi-branch, franchise, consortium), ownership structures, brand hierarchy, territory management, franchise agreement terms, commission flows, network governance |
| 2 | [FRANCHISE_02_BRANCH_OPERATIONS.md](FRANCHISE_02_BRANCH_OPERATIONS.md) | Branch-level P&L, inter-branch trip transfers, performance metrics, resource sharing (agents, inventory, supplier contracts), communication protocols |
| 3 | [FRANCHISE_03_FRANCHISE_ONBOARDING.md](FRANCHISE_03_FRANCHISE_ONBOARDING.md) | Franchisee onboarding process, brand compliance enforcement, training and certification, franchisee portal, royalty and fee management, compliance auditing, renewal/termination |
| 4 | [FRANCHISE_04_CONSORTIUM.md](FRANCHISE_04_CONSORTIUM.md) | Consortium model for independent agencies, shared inventory pooling, joint marketing, B2B marketplace, mutual referral system, revenue sharing, governance, legal structures for India |

---

## Key Themes

### 1. Network as a First-Class Concept
The platform treats "network" as a first-class entity, not just a collection of unrelated tenants. Network nodes share branding, inventory, supplier contracts, and governance rules. This requires a network-aware data model that propagates configuration, enforces policies, and tracks inter-node transactions.

### 2. Financial Multi-Entity by Design
Every network node is a separate financial entity with its own GST registration, bank account, and P&L. The platform must track inter-entity transactions (royalties, referrals, inventory sharing, revenue splits) and support consolidated reporting at the network level. This is fundamentally different from single-entity agency accounting.

### 3. Governance Varies by Network Type
A franchise has centralized governance (franchisor controls). A consortium has democratic governance (members vote). A multi-branch corporate network has hierarchical governance (HQ controls). The platform must support all three models with configurable decision-making, policy enforcement, and dispute resolution mechanisms.

### 4. Territory is Both Physical and Digital
Traditional territory management (pin codes, city boundaries) collides with digital reality (website bookings, WhatsApp inquiries, referral networks). The platform must model both physical territory rules and digital attribution (who gets credit for an online booking from a franchise territory).

### 5. India-Specific Regulatory Depth
Indian franchise and consortium operations face unique regulatory complexity: GST per entity, IATA accreditation non-transferability, RBI guidelines for fee collection, Competition Act constraints on collective behavior, and DPDP Act requirements for multi-entity customer data. The platform must encode these constraints, not leave them to manual compliance.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Multi-Tenancy (MULTI_TENANCY_*) | Tenant isolation, provisioning, and per-tenant configuration — franchise nodes are tenants with network-level shared resources |
| White Label (WHITELABEL_*) | Brand theming, multi-brand management — franchise brand hierarchy extends white-label with compliance enforcement |
| Finance & Accounting (FINANCE_*) | Per-trip profitability, P&L tracking — extended to multi-entity with inter-branch ledgers and royalty billing |
| Commission Management (COMMISSION_*) | Commission calculation and tracking — extended to multi-level network commission flows |
| Regulatory & Licensing (REGULATORY_*) | Agency licensing, IATA accreditation — extended to franchise-specific compliance (sub-agent arrangements, GST per entity) |
| Partner Management (PARTNER_*) | Partner and affiliate programs — consortium membership model parallels partner tiers |
| Supplier Integration (SUPPLIER_INTEGRATION_*) | Supplier contracts and inventory — shared supplier contracts across network nodes |
| Booking Engine (BOOKING_ENGINE_*) | Booking state machine — extended for inter-branch trip transfers with revenue splitting |
| Onboarding (ONBOARDING_*) | Agency and agent onboarding — franchise onboarding is a specialized variant with brand compliance and training |
| Data Governance (DATA_GOVERNANCE_*) | Data quality and lineage — extended for multi-entity data sharing boundaries and DPDP Act compliance |
| Contract Management (CONTRACT_*) | Contract templates and lifecycle — franchise agreements and consortium membership agreements |
| Analytics & BI (ANALYTICS_*) | Dashboards and reporting — branch performance dashboards, network-level consolidated analytics |

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Network Data Model | PostgreSQL + RLS | Multi-tenant data with network-level shared resources |
| Inter-Entity Ledger | Custom double-entry | Track royalties, referrals, and revenue splits across entities |
| Territory Engine | PostGIS + Pin Code DB | Geographic territory mapping and overlap detection |
| Brand Compliance | Template engine + CDN | Locked brand assets with franchisee override layers |
| Royalty Billing | Scheduled jobs + NACH | Automated billing calculation and auto-debit collection |
| Inventory Pooling | Redis distributed locks | Concurrent booking conflict resolution for shared inventory |
| B2B Marketplace | Full-text search + real-time | Listing, search, and claim workflow for consortium marketplace |
| Referral Tracking | Event sourcing | Immutable referral lifecycle tracking with attribution windows |
| Settlement Engine | Graph algorithm | Multi-party netting for monthly batch settlement |
| Franchisee Portal | Next.js (shared frontend) | Self-service portal for financial, compliance, and operational views |
| Compliance Auditing | Checklist engine + scoring | Automated and manual audit tracking with scoring rubrics |
| Communication | WebSocket + message queue | Inter-branch messaging with priority routing and filtering |
| Document Generation | PDF engine + templates | Franchise agreements, royalty statements, compliance reports |
| GST Integration | GSTN API + e-invoicing | Multi-entity GST filing, e-invoice generation per node |
| Monitoring | Per-tenant metrics + network rollup | Branch health, network performance, early warning alerts |

---

## India-Specific Regulatory Reference

| Regulation | Impact on Network Operations | Platform Handling |
|-----------|------------------------------|-------------------|
| GST (CGST/SGST/IGST) | Separate registration per legal entity; 18% on franchise royalties; 5% on tour packages | Multi-entity GST tracking, e-invoicing, inter-entity billing |
| IATA Accreditation | Non-transferable; franchisees need sub-agent arrangement or own accreditation | Sub-agent ticketing workflow, BSP billing through franchisor |
| RBI NACH Mandates | Auto-debit for royalty collection; capped per agreement terms | Automated NACH mandate registration, dispute handling |
| TDS (Section 194J) | 10% TDS on franchise fees paid to franchisor | Automated TDS deduction and certificate generation |
| DPDP Act 2023 | Customer data ownership, consent for sharing, portability on exit | Multi-entity consent management, data portability workflow |
| Competition Act 2002 | No price fixing, no market allocation, no bid rigging | Consortium policies designed for compliance, no pricing mandates |
| Consumer Protection 2019 | Both franchisor and franchisee liable for service deficiency | Liability allocation in agreements, insurance requirements |
| Companies Act 2013 | Section 8 company for consortium; compliance requirements | Consortium legal entity management, annual filing tracking |
| Shop & Establishment | State-level license per branch/franchise location | Multi-location license tracking with renewal alerts |
| Professional Tax | State-level; varies by state; per-employee | Multi-state payroll compliance for network employees |

---

**Created:** 2026-04-28
