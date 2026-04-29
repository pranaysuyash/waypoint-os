# Implementation Roadmap — Living Document

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — ties ALL 37+ first-principles discussions into actionable sprints  
**Approach:** Living document — update as we implement  

---

## 1. The Big Picture (What We've Defined)

We've spent today discussing **37+ areas from first principles**. Here's what we NOW know:

### Core Entities (Defined)
| Entity | Discussion Doc | Status |
|--------|---------------|--------|
| **Enquiry** | `enquiry_types_and_stages_2026-04-29.md` | ✅ Defined |
| **Customer** | `customer_model_2026-04-29.md` | ✅ Defined |
| **Vendor** | `vendor_model_2026-04-29.md` | ✅ Defined |
| **Booking** | `booking_model_2026-04-29.md` | ✅ Defined |
| **Communication** | `communication_model_2026-04-29.md` | ✅ Defined |
| **Payment** | `payments_and_gateways_2026-04-29.md` | ✅ Defined (status-only) |

### Infrastructure (Defined)
| Area | Discussion Doc | Status |
|------|---------------|--------|
| **Architecture** | `system_architecture_plan_2026-04-29.md` | ✅ Defined |
| **Database** | `system_architecture_plan_2026-04-29.md` | ✅ PostgreSQL schema |
| **API** | `api_documentation_2026-04-29.md` | ✅ FastAPI + Swagger |
| **Frontend** | `system_architecture_plan_2026-04-29.md` | ✅ Next.js + PWA |
| **Mobile** | `mobile_and_pwa_2026-04-29.md` | ✅ WhatsApp Business API |

### Operations (Defined)
| Area | Discussion Doc | Status |
|------|---------------|--------|
| **Search** | `search_and_discovery_2026-04-29.md` | ✅ PostgreSQL FTS |
| **Notifications** | `notifications_and_alerts_2026-04-29.md` | ✅ WhatsApp-primary |
| **Reports** | `reporting_and_analytics_2026-04-29.md` | ✅ 3 core reports |
| **Compliance** | `audit_and_compliance_2026-04-29.md` | ✅ GDPR + DPDP |
| **Backup** | `backup_and_security_2026-04-29.md` | ✅ 3 layers |
| **Hosting** | `domain_hosting_legal_2026-04-29.md` | ✅ Vercel + Railway |

---

## 2. Implementation Phases (What to Build When)

### Phase 1: FOUNDATIONS (Week 1-2) — ✅ DOING NOW

| Task | Discussion Doc | Est. Time | Status |
|------|---------------|-----------|--------|
| **Setup repo + README** | `api_documentation_2026-04-29.md` | 1h | ❌ TODO |
| **PostgreSQL schema** | `system_architecture_plan_2026-04-29.md` | 3h | ❌ TODO |
| **FastAPI skeleton** | `api_documentation_2026-04-29.md` | 2h | ❌ TODO |
| **Next.js scaffold** | `system_architecture_plan_2026-04-29.md` | 2h | ❌ TODO |
| **`.env.example`** | `environment_management_2026-04-29.md` | 1h | ❌ TODO |
| **GitHub Actions CI** | `ci_cd_pipeline_2026-04-29.md` | 2h | ❌ TODO |
| **First deploy** | `domain_hosting_legal_2026-04-29.md` | 1h | ❌ TODO |

**Phase 1 Goal:** `https://yourname-travels.com` shows "Hello World" + DB connected.

---

### Phase 2: CORE ENTITIES (Week 3-4)

| Task | Discussion Doc | Est. Time | Dependency |
|------|---------------|-----------|------------|
| **Customer model + API** | `customer_model_2026-04-29.md` | 4h | Phase 1 |
| **Enquiry model + API** | `enquiry_types_and_stages_2026-04-29.md` | 6h | Customer |
| **Vendor model + API** | `vendor_model_2026-04-29.md` | 4h | Phase 1 |
| **Booking model + API** | `booking_model_2026-04-29.md` | 6h | Enquiry |
| **Communication model + API** | `communication_model_2026-04-29.md` | 4h | Customer |

**Phase 2 Goal:** Create customer → enquiry → booking → send WhatsApp.

---

### Phase 3: AI INTEGRATION (Week 5-6)

| Task | Discussion Doc | Est. Time | Dependency |
|------|---------------|-----------|------------|
| **Spine API integration** | `system_architecture_plan_2026-04-29.md` | 6h | Phase 2 |
| **AI draft generation** | `communication_model_2026-04-29.md` | 4h | Spine API |
| **WhatsApp Business API** | `mobile_and_pwa_2026-04-29.md` | 8h | Phase 1 |
| **Webhook: receive messages** | `integrations_2026-04-29.md` | 4h | WhatsApp API |
| **Auto-reply + AI draft** | `notifications_and_alerts_2026-04-29.md` | 3h | Above |

**Phase 3 Goal:** Customer sends WhatsApp → AI analyzes → you reply in 30 mins.

---

### Phase 4: SEARCH + REPORTS (Week 7-8)

| Task | Discussion Doc | Est. Time | Dependency |
|------|---------------|-----------|------------|
| **Full-text search** | `search_and_discovery_2026-04-29.md` | 3h | Phase 2 |
| **Revenue report** | `reporting_and_analytics_2026-04-29.md` | 2h | Phase 2 |
| **Conversion funnel** | `reporting_and_analytics_2026-04-29.md` | 2h | Phase 2 |
| **Vendor scorecard** | `reporting_and_analytics_2026-04-29.md` | 2h | Phase 2 |

**Phase 4 Goal:** Find "Ravi's old Bali trip" in 10 seconds.

---

### Phase 5: COMPLIANCE + SECURITY (Week 9-10)

| Task | Discussion Doc | Est. Time | Dependency |
|------|---------------|-----------|------------|
| **PII encryption** | `backup_and_security_2026-04-29.md` | 3h | Phase 2 |
| **Consent tracking** | `audit_and_compliance_2026-04-29.md` | 2h | Phase 2 |
| **GDPR export** | `data_export_portability_2026-04-29.md` | 4h | Phase 2 |
| **Backup automation** | `backup_and_security_2026-04-29.md` | 2h | Phase 1 |
| **UptimeRobot** | `monitoring_and_alerting_2026-04-29.md` | 1h | Phase 1 |

**Phase 5 Goal:** Legally compliant, data backed up, monitored.

---

### Phase 6: POLISH + LAUNCH (Week 11-12)

| Task | Discussion Doc | Est. Time | Dependency |
|------|---------------|-----------|------------|
| **Domain purchase** | `domain_hosting_legal_2026-04-29.md` | 1h | Phase 1 |
| **Google My Business** | `marketing_seo_2026-04-29.md` | 2h | Phase 1 |
| **Referral program** | `marketing_seo_2026-04-29.md` | 2h | Phase 2 |
| **Onboarding docs** | `onboarding_2026-04-29.md` | 2h | All phases |
| **Instagram marketing** | `marketing_seo_2026-04-29.md` | 3h | Phase 1 |

**Phase 6 Goal:** First 10 customers, ₹50k revenue/month.

---

## 3. Current Status (What's Built vs Planned)

### What Exists Now (In Repo)
| Component | Files | Status |
|-----------|-------|--------|
| **Spine API** | `spine_api/` | ✅ Working (AI engine) |
| **CanonicalPacket** | `specs/canonical_packet.schema.json` | ✅ Schema defined |
| **Frontend scaffold** | `frontend/` | ✅ Next.js exists |
| **Discussion docs** | `Docs/discussions/*.md` | ✅ 37+ docs done |

### What's MISSING (To Build)
| Component | Discussion Doc | Priority |
|-----------|---------------|----------|
| **Entity APIs** | `system_architecture_plan_2026-04-29.md` | 🔴 CRITICAL |
| **PostgreSQL tables** | `system_architecture_plan_2026-04-29.md` | 🔴 CRITICAL |
| **WhatsApp integration** | `mobile_and_pwa_2026-04-29.md` | 🔴 CRITICAL |
| **Frontend pages** | `system_architecture_plan_2026-04-29.md` | HIGH |
| **Deployment** | `domain_hosting_legal_2026-04-29.md` | HIGH |

---

## 4. Immediate Next Steps (THIS WEEK)

### Task 1: PostgreSQL Schema (Tomorrow)
```bash
# File: alembic/versions/001_create_entities.py
# Tables: customers, enquiries, bookings, vendors, communications
# Time: 3h
# Discussion: system_architecture_plan_2026-04-29.md
```

### Task 2: Entity APIs (This Week)
```bash
# Files: spine_api/routers/customers.py, enquiries.py, bookings.py
# Time: 10h total
# Discussion: customer_model_2026-04-29.md + booking_model_2026-04-29.md
```

### Task 3: First Deploy (This Week)
```bash
# Vercel (frontend) + Railway (backend)
# Time: 2h
# Discussion: domain_hosting_legal_2026-04-29.md
```

---

## 5. Decisions Made Today (From 37 Discussions)

| Decision | Options | Recommendation |
|-----------|---------|-------------------|
| **Payment collection?** | Yes / No | **NO** — track status only |
| **Human agent model?** | Full / Skip | **SKIP** — solo dev |
| **RBAC?** | Now / Later | **LATER** — hire #2 |
| **Search engine?** | PostgreSQL FTS / Elasticsearch | **PostgreSQL FTS** — zero infra |
| **WhatsApp API?** | Now / Later | **NOW** — core workflow |
| **S3 backups?** | Yes / No | **YES** — ₹0.50/day |
| **Rate limiting?** | slowapi / None | **slowapi** — 5 mins |
| **Feature flags?** | Now / Later | **NOW** — 5 mins |

---

## 6. Open Questions (Need Answers Before Building)

| Question | Discussion Doc | Blocker? |
|-----------|---------------|----------|
| **WhatsApp Business API approved?** | `mobile_and_pwa_2026-04-29.md` | YES — need Meta review |
| **Domain bought?** | `domain_hosting_legal_2026-04-29.md` | NO — can use `.vercel.app` |
| **GST registration?** | `domain_hosting_legal_2026-04-29.md` | NO — after ₹20L revenue |
| **Google My Business created?** | `marketing_seo_2026-04-29.md` | NO — Week 11 |

---

## 7. Update Log (Living Document)

| Date | Update |
|------|--------|
| **2026-04-29** | Created 37+ discussion docs from first principles |
| **2026-04-29** | Defined all entities, infrastructure, operations |
| **2026-04-29** | Phase 1-6 roadmap established |
| **NEXT** | Update as we implement each task |

---

## 8. Next Steps (What Do Now?)

1. **Create PostgreSQL schema** (alembic migration) — 3h
2. **Build Customer API** — 4h
3. **Build Enquiry API** — 6h
4. **Deploy to Railway** — 1h
5. **Update this document** — mark tasks as DONE

---

**This is the LIVING document. Update it as we implement. Each task = link to discussion doc + mark DONE when finished.**
