# Multi-Brand & White Label — Master Index

> Exploration of white-label platform architecture, dynamic branding, reseller networks, and multi-tenant operations.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Architecture & Strategy](WHITELABEL_01_ARCHITECTURE.md) | White-label model, multi-tenant architecture, usage limits & billing |
| 02 | [Branding & Theming](WHITELABEL_02_BRANDING.md) | Dynamic theming, brand asset management, document branding, preview & publishing |
| 03 | [Reseller & Partner Network](WHITELABEL_03_RESELLER.md) | Reseller model, partner hierarchy, revenue sharing, partner onboarding |
| 04 | [Operations & Scaling](WHITELABEL_04_OPERATIONS.md) | Multi-tenant deployment, monitoring, config management, scaling |

---

## Key Themes

- **Single codebase, infinite brands** — One platform serves all agencies. Customization through configuration, not code forks. Row-level security isolates tenant data while sharing infrastructure.
- **Branding is deep, not skin-deep** — White-label covers every touchpoint: login page, workbench, customer portal, emails, PDFs, WhatsApp messages. Agencies see their brand everywhere customers do.
- **Partner networks multiply reach** — A reseller ecosystem (platform → master partner → reseller → agency) multiplies distribution without proportional cost. Revenue sharing aligns incentives across all tiers.
- **Operations must be invisible** — Phased rollouts, tenant-aware monitoring, automated config migration. Platform updates should be seamless to every tenant, regardless of their customization level.
- **Scale by design, not by retrofit** — Architecture choices (row-level security, CDN asset delivery, per-tenant caching) must support growth from 10 to 500+ tenants without re-architecture.

## Integration Points

- **Authentication & Authorization** — Tenant context from JWT, role-based access per brand
- **Notification System** — Branded email/WhatsApp templates per tenant
- **Analytics & BI** — Per-tenant analytics dashboards and reporting
- **Billing & Payments** — Subscription management, usage metering, revenue sharing
- **Document Generation** — Branded itineraries, quotes, invoices per tenant
- **Integration Hub** — Per-tenant connector credentials and configuration
