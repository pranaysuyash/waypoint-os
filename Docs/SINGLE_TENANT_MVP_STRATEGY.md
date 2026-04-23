# Single-Tenant MVP Strategy

> **⚠️ DEPRECATED — EXPLORATORY DRAFT (2026-04-13)**
>
> This document represents an early exploratory phase and **does not reflect the current architecture direction**. The system is now being built as a **multi-tenant platform** with full workspace governance, comprehensive onboarding, and production-grade auth from the outset.
>
> **Current direction**: See [`ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md`](ONBOARDING_AUTH_WORKSPACE_MULTI_TENANT_ROADMAP_2026-04-23.md) and [`WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md`](WORKSPACE_GOVERNANCE_ROADMAP_LIVING_2026-04-22.md).
>
> This document is preserved for historical reference and contains useful discussion on deployment sequencing and cost constraints that remain relevant.

**Date**: 2026-04-13
**Purpose**: Simplified architecture for solo developer - one agency first
**Related**: `BUSINESS_MODEL_CORRECTION.md`, `UX_TECHNICAL_ARCHITECTURE.md`

---

## The Philosophy

> **"Make it work for ONE agency before making it work for MANY."**

Multi-tenant white-label SaaS is the goal, NOT the starting point.

---

## MVP: Single Agency, Single Tenant

### What You Actually Build First

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOUR PLATFORM (Single-Tenant)                                                │
│  ───────────────────────────────────────────────────────────────────────────────│
│  Serves: ONE agency (you, or one partner agency)                              │
│  Customers: That agency's customers only                                      │
│  Branding: Either your brand OR that agency's brand (not both)                │
│  Complexity: NONE - just a simple web app                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Option A: You ARE The Agency (Simplest)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOU = AGENCY (for MVP)                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Build: Agency OS for YOUR travel agency                                      │
│  Use: To serve YOUR customers                                                  │
│  Learn: What features matter, what agents need                                │
│  Prove: The product works with real customers                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Immediate feedback loop (you are the user)
- No customer discovery needed (you know your own pain)
- Single codebase, no tenant isolation
- Ship faster

**Cons:**
- You're running a travel agency (or acting like one)
- Harder to distinguish "product problems" from "agency problems"
- Eventually need to pivot to multi-tenant

---

### Option B: One Partner Agency (Recommended)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOU + ONE PARTNER AGENCY                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Find: ONE travel agency willing to be your design partner                    │
│  Build: FOR THEM specifically (not generic "for anyone")                      │
│  Host: On your domain or a subdomain                                          │
│  Revenue: Revenue share or fixed fee during MVP                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Real customer feedback from day one
- You learn what agencies actually need
- Can charge from day one (even if discounted)
- Still single-tenant (simple codebase)

**Cons:**
- Need to find the right partner agency
- Their requirements might be specific to them
- Still need to refactor for multi-tenant later

---

## Single-Tenant Architecture

### What You DON'T Need (Yet)

| Complexity | Multi-Tenant Needs | Single-Tenant Reality |
|------------|---------------------|----------------------|
| **Tenant isolation** | `WHERE tenant_id = X` on every query | No tenant_id needed |
| **White-label branding** | Agency uploads logo, configures colors | One branding (yours or partner's) |
| **Custom domains** | DNS config per tenant, SSL per domain | One domain (yours) |
| **Tenant-specific WhatsApp** | Each agency connects their WATI | One WhatsApp (yours or partner's) |
| **Multi-tenant billing** | Per-tenant subscriptions, prorating | No billing (or simple fixed fee) |
| **Team management** | Agencies invite their staff | No team management (you = admin) |

### What You DO Need (Simple)

```python
# No tenant_id anywhere!

# Customer lookup
async def get_customer(phone: str):
    return await db.fetch_one(
        "SELECT * FROM customers WHERE phone = $1",
        phone
    )

# Packets
async def get_packet(packet_id: str):
    return await db.fetch_one(
        "SELECT * FROM packets WHERE id = $1",
        packet_id
    )

# That's it! No tenant filtering.
```

### Database Schema (Single-Tenant)

```sql
-- No tenant_id columns!

CREATE TABLE customers (
    id UUID PRIMARY KEY,
    phone VARCHAR(20) UNIQUE,
    name VARCHAR(100),
    email VARCHAR(100),
    preferences JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE packets (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    packet_id VARCHAR(50) UNIQUE,
    stage VARCHAR(20),
    facts JSONB,
    ambiguities JSONB,
    contradictions JSONB,
    decision_state VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- That's it! Single agency, simple tables.
```

---

## The "Scaffold" Approach

Build the product so multi-tenancy CAN be added later, without rebuilding:

### Good Practices (Enable Future Multi-Tenant)

| Practice | Single-Tenant Now | Multi-Tenant Later |
|----------|-------------------|--------------------|
| **Config file** | Hardcode one agency | Add agency_id lookup |
| **Auth** | Simple login | Add agency_id to user model |
| **Queries** | Direct table access | Use repository pattern |
| **Frontend** | Hardcode branding | Add branding config object |

### Example: Future-Proof Code

```python
# SINGLE-TENANT NOW (MVP)

class Config:
    AGENCY_NAME = "Priya Travels"  # Hardcoded
    AGENCY_LOGO = "/logo.png"
    AGENCY_PHONE = "+91-98765-43210"
    AGENCY_EMAIL = "priya@priyatravels.com"

# FRONTEND
const branding = {
  name: "Priya Travels",  // From config
  logo: "/logo.png",
  phone: "+91-98765-43210"
};

# LATER: Add tenant lookup

class Config:
    def get_agency_config(agency_id: str):
        return db.fetch_one("SELECT * FROM agencies WHERE id = $1", agency_id)

# FRONTEND (later)
const branding = await fetch(`/api/branding`);
```

---

## Deployment Options

### Option 1: Single Domain (Simplest)

```
Domain: agency-os.com (or your-brand.com)
All traffic: Goes to your app
All customers: See your branding (or partner's)
```

### Option 2: Subdomain for Partner (Still Simple)

```
Your app: app.agency-os.com
Partner agency: priya.agency-os.com (points to same app!)
Difference: Just branding config loaded from subdomain
```

```python
# Still single-tenant codebase!
# Just load different branding based on subdomain

def get_branding_from_host(host: str):
    subdomain = host.split(".")[0]
    
    if subdomain == "priya":
        return PRIYA_BRANDING
    else:
        return DEFAULT_BRANDING
```

This is **NOT multi-tenant** - it's just branding config. Still one database, one codebase.

---

## When to Add Multi-Tenancy

### Add When You Have:

- [ ] 3+ paying agencies who want to use the product
- [ ] Validation that the core product works
- [ ] Revenue to justify the complexity
- [ ] Maybe: Funding or time to dedicate to the refactor

### Signs You're Ready:

1. **Agencies are asking** - "Can I use this for my agency?"
2. **You're saying no to revenue** - Turning away interested agencies
3. **Core features are stable** - NB01-NB02-NB03 is working well
4. **You have help** - Not solo anymore, or have time for big refactor

### Until Then:

Stay single-tenant. Ship faster. Learn more.

---

## Migration Path: Single → Multi

When you ARE ready, here's the rough approach:

```python
# STEP 1: Add agency_id to all tables (3 days)
ALTER TABLE customers ADD COLUMN agency_id UUID;
ALTER TABLE packets ADD COLUMN agency_id UUID;
-- etc for all tables

# STEP 2: Create agencies table (1 day)
CREATE TABLE agencies (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    branding JSONB,
    plan VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

# STEP 3: Add agency_id to queries (3-5 days)
# Before:
async def get_customer(phone: str):
    return await db.fetch_one("SELECT * FROM customers WHERE phone = $1", phone)

# After:
async def get_customer(phone: str, agency_id: str):
    return await db.fetch_one(
        "SELECT * FROM customers WHERE phone = $1 AND agency_id = $2",
        phone, agency_id
    )

# STEP 4: Add middleware to inject agency_id (2 days)
@app.middleware("http")
async def agency_middleware(request: Request, call_next):
    # Get agency from subdomain or header
    agency_id = get_agency_from_request(request)
    request.state.agency_id = agency_id
    response = await call_next(request)
    return response

# STEP 5: Build agency admin UI (1 week)
# Dashboard where agencies can configure branding, invite team, etc.

# TOTAL: ~2-3 weeks of focused work
```

---

## Recommended MVP Approach

### Phase 1: Build for ONE Agency (You or Partner)

**Duration:** 2-3 months
**Goal:** Prove product works with real customers

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SINGLE-TENANT MVP                                                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • ONE agency (you or partner)                                                │
│  • ONE database (no tenant_id)                                                │
│  • ONE branding (config file, not database)                                   │
│  • ONE WhatsApp (manual copy-paste or single WATI)                            │
│  • ONE domain (yours or simple subdomain)                                     │
│                                                                                  │
│  Focus: Core features (NB01-NB02-NB03) + basic dashboard                       │
│                                                                                  │
│  Success metric: 100+ trips processed successfully                             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Add Multi-Tenant (When Ready)

**Duration:** 2-3 weeks
**Trigger:** 3+ agencies want to use it

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  MULTI-TENANT REFACTOR                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • Add agency_id everywhere                                                    │
│  • Add tenant middleware                                                       │
│  • Add agency admin UI                                                          │
│  • Add billing per agency                                                      │
│  • Add white-label branding                                                    │
│                                                                                  │
│  Focus: Enable multiple agencies to use same platform                         │
│                                                                                  │
│  Success metric: 5 agencies using platform concurrently                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## What This Means for Your Current Planning

### DELETE from scope (for now):

- Multi-tenant architecture
- White-label branding system
- Agency signup/onboarding
- Per-agency billing
- Team management (multiple agents per agency)
- Custom domains per agency
- Agency admin dashboard

### KEEP in scope (MVP):

- Core decision engine (NB01-NB02-NB03)
- Agent dashboard (for ONE agency)
- Customer portal (for ONE agency's customers)
- WhatsApp integration (ONE account)
- Basic analytics (for ONE agency)

### The Key Insight

**You're not building a SaaS platform yet.** You're building a **tool for one agency**.

If that tool proves valuable, THEN you turn it into a SaaS platform.

---

## Comparison: Single vs Multi Tenant

| Aspect | Single-Tenant MVP | Multi-Tenant SaaS |
|--------|-------------------|-------------------|
| **Code complexity** | Low | High |
| **Database queries** | Simple | Complex (tenant filtering) |
| **Testing** | Test one scenario | Test N scenarios |
| **Deployment** | One app | Multi-app with routing |
| **Branding** | Config file | Database per agency |
| **Billing** | None/Simple | Per-tenant subscriptions |
| **Time to MVP** | 2-3 months | 6-9 months |
| **Time users wait** | Start now | Wait until multi-tenant done |

---

## The Smart Path

```
NOW (Single-Tenant)
    |
    v
Build product for ONE agency
    |
    v
Ship to real customers
    |
    v
Learn what matters
    |
    v
Get 10 agencies interested
    |
    v
    |
    v
LATER (Multi-Tenant Refactor)
    |
    v
Add agency_id to tables
    |
    v
Add agency admin UI
    |
    v
White-label branding
    |
    v
Per-agency billing
    |
    v
NOW you have a SaaS platform
```

---

## Summary

As a solo developer:

1. **Start single-tenant** - Build for ONE agency
2. **Prove value first** - Get real customer feedback
3. **Add complexity later** - Multi-tenant when you have demand

The multi-tenant white-label SaaS is the **destination**, not the **starting point**.

---

*Single-tenant MVP: Ship months sooner, validate with real users, add complexity when you have paying customers waiting for it.*
