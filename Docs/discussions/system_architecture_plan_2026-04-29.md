# System Architecture Plan — First Principles

**Date:** 2026-04-29
**Context:** All core entities defined — now planning the system that orchestrates them
**Approach:** Independent analysis — bridging the gap between entity models and working software

---

## 1. The Core Problem: Current Architecture is Upside-Down**

### Current State (What Exists)

```
Frontend (Next.js)
  └─ BFF Proxy (/api/[...path])
       └─ spine_api (FastAPI)
              ├─ src/intake/ (NB01, NB02, NB03)
              ├─ src/decision/ (hybrid_engine, rules)
              ├─ src/analytics/ (metrics, review)
              └─ src/security/ (encryption, privacy)
```

### What's Missing (Critical Gaps)

1. **No entity APIs** — no `/api/customers`, `/api/bookings`, `/api/vendors`
2. **No database models** — entities exist only as Pydantic schemas (CanonicalPacket)
3. **No persistence layer** — CanonicalPacket is ephemeral (generated per-run)
4. **No relationship graph** — enquiry → customer → bookings → vendors (not queryable)
5. **AI Engine is isolated** — processes inquiries but doesn't persist structured entities

**My insight:**  
The current system is a **stateless processing pipeline** masquerading as an application.  
We need a **stateful entity graph** with the AI Engine as a **component**, not the whole system.

---

## 2. My Proposed Architecture: Entity-First Design**

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Enquiry UI  │  │Customer UI │  │Booking UI  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                  │                  │           │
│  ┌──────┴──────────────┴──────────────┴──────┐ │
│  │          BFF Layer (State Management)         │ │
│  │  (React Query, Zustand stores, proxies)    │ │
│  └──────────────────┬───────────────────────┘ │
└─────────────────────────┼─────────────────────────────┘
                          │ HTTP/JSON
┌─────────────────────────┼─────────────────────────────┐
│  BACKEND (FastAPI)  │                        │
│  ┌───────────────────┴───────────────────────┐ │
│  │          Entity API Layer                      │ │
│  │  /api/enquiries, /api/customers,           │ │
│  │  /api/bookings, /api/vendors,             │ │
│  │  /api/communications, /api/agents          │ │
│  └───────────────────┬───────────────────────┘ │
│                    │                              │
│  ┌───────────────────┴───────────────────────┐ │
│  │          AI Engine (spine_api)                 │ │
│  │  /api/spine/run (stateless, called by       │ │
│  │   entity APIs when AI assistance needed)        │ │
│  └───────────────────┬───────────────────────┘ │
│                    │                              │
│  ┌───────────────────┴───────────────────────┐ │
│  │          Persistence Layer                      │ │
│  │  PostgreSQL (entities) + Redis (cache)     │ │
│  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Key insight:**  
AI Engine is a **called service**, not the **routing layer**.  
Entity APIs own the business logic; AI Engine assists when needed.

---

## 3. Database Schema (Entity-Relationship)**

### Core Tables (PostgreSQL)**

```sql
-- Customers
CREATE TABLE customers (
  customer_id UUID PRIMARY KEY,
  customer_type VARCHAR(20),  -- INDIVIDUAL, CORPORATE, PARTNER
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255) UNIQUE,
  phone_primary VARCHAR(20),
  phone_whatsapp VARCHAR(20),
  preferred_channel VARCHAR(20),
  acquisition_source VARCHAR(50),
  referred_by_customer_id UUID REFERENCES customers(customer_id),
  customer_segment VARCHAR(20),  -- VIP, HIGH_VALUE, STANDARD
  health_score DECIMAL(3,2),  -- 0.00-1.00
  total_spend_lifetime DECIMAL(12,2),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Human Agents
CREATE TABLE agents (
  agent_id UUID PRIMARY KEY,
  agent_type VARCHAR(20),
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  email VARCHAR(255) UNIQUE,
  seniority VARCHAR(20),  -- JUNIOR, SENIOR, TEAM_LEAD, MANAGER
  status VARCHAR(20),  -- ACTIVE, BUSY, AWAY, OFFLINE
  max_concurrent_enquiries INT,
  languages JSONB,  -- [{"language": "en", "can_support": true}]
  skills JSONB,  -- {"trip_types": ["leisure", "medical"], "regions": ["SE_ASIA"]}
  performance_score DECIMAL(3,2),
  created_at TIMESTAMP
);

-- Vendors
CREATE TABLE vendors (
  vendor_id UUID PRIMARY KEY,
  vendor_type VARCHAR(30),  -- ACCOMODATION, AIR_TRANSPORT, etc.
  company_name VARCHAR(255),
  brand_name VARCHAR(255),
  primary_contact JSONB,
  operating_countries TEXT[],  -- ARRAY['Thailand', 'Indonesia']
  vendor_tier VARCHAR(20),  -- PREFERRED, CONTRACTED, AD_HOC
  overall_rating DECIMAL(2,1),  -- 1.0-5.0
  complaint_rate DECIMAL(3,2),  -- 0.00-1.00
  commission_rate_default DECIMAL(5,2),  -- 0.00-100.00
  contract_status VARCHAR(20)
);

-- Enquiries
CREATE TABLE enquiries (
  enquiry_id UUID PRIMARY KEY,
  enquiry_type VARCHAR(20),  -- NEW_TOUR, IN_PROGRESS_ISSUE, POST_TRIP
  enquiry_subtype VARCHAR(30),
  channel VARCHAR(20),  -- whatsapp, email, telegram, etc.
  acquisition_source VARCHAR(50),
  geography_scope VARCHAR(20),  -- LOCAL, DOMESTIC, INTERNATIONAL
  trip_pattern VARCHAR(30),  -- SINGLE_DESTINATION, MULTI_DESTINATION
  status VARCHAR(30),  -- RECEIVED, TRIAGED, RESEARCHING, ...
  customer_id UUID REFERENCES customers(customer_id),
  assigned_agent_id UUID REFERENCES agents(agent_id),
  priority VARCHAR(10),  -- LOW, NORMAL, HIGH, URGENT
  related_booking_ids UUID[],  -- ARRAY of booking_ids
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Bookings
CREATE TABLE bookings (
  booking_id UUID PRIMARY KEY,
  enquiry_id UUID REFERENCES enquiries(enquiry_id),
  booking_type VARCHAR(20),
  status VARCHAR(30),  -- QUOTED, CONFIRMED, IN_PROGRESS, COMPLETED
  customer_id UUID REFERENCES customers(customer_id),
  assigned_agent_id UUID REFERENCES agents(agent_id),
  start_date DATE,
  end_date DATE,
  total_value DECIMAL(12,2),
  currency VARCHAR(3),
  payment_status VARCHAR(20),
  created_at TIMESTAMP,
  confirmed_at TIMESTAMP
);

-- Booking Items (flights, hotels, etc.)
CREATE TABLE booking_items (
  item_id UUID PRIMARY KEY,
  booking_id UUID REFERENCES bookings(booking_id),
  item_type VARCHAR(20),  -- FLIGHT, HOTEL, TRANSFER, etc.
  vendor_id UUID REFERENCES vendors(vendor_id),
  description TEXT,
  base_price DECIMAL(10,2),
  total_price DECIMAL(10,2),
  currency VARCHAR(3),
  status VARCHAR(20),
  voucher_url VARCHAR(500)
);

-- Communications
CREATE TABLE communications (
  comm_id UUID PRIMARY KEY,
  enquiry_id UUID REFERENCES enquiries(enquiry_id),
  booking_id UUID REFERENCES bookings(booking_id),
  sender_type VARCHAR(20),  -- HUMAN_AGENT, CUSTOMER, VENDOR, SYSTEM
  sender_id VARCHAR(100),  -- agent_id, customer_id, or vendor_id
  recipient_type VARCHAR(20),
  recipient_id VARCHAR(100),
  channel VARCHAR(20),
  subject VARCHAR(255),
  body_text TEXT,
  ai_assisted BOOLEAN,
  sent_at TIMESTAMP
);

-- Drafts
CREATE TABLE drafts (
  draft_id UUID PRIMARY KEY,
  enquiry_id UUID REFERENCES enquiries(enquiry_id),
  booking_id UUID REFERENCES bookings(booking_id),
  draft_type VARCHAR(30),
  generated_by VARCHAR(20),  -- AI_ENGINE, HUMAN_AGENT, TEMPLATE
  content_current TEXT,
  version INT,
  status VARCHAR(20),  -- DRAFTING, READY_TO_SEND, SENT
  sent_comm_id UUID REFERENCES communications(comm_id),
  created_at TIMESTAMP
);
```

**My insight:**  
Use **JSONB** for flexible fields (languages, skills, operating_countries) — they're not relational, they're attribute bags.  
Use **ARRAY types** for simple lists (related_booking_ids, operating_countries).

---

## 4. API Structure (RESTful, Entity-First)**

### Core Entity Endpoints

```
/api/enquiries
  GET    /              → List enquiries (filter by status, agent, customer)
  POST   /              → Create new enquiry (triggers AI intake)
  GET    /:id           → Get enquiry details + related entities
  PATCH  /:id           → Update enquiry (status, assignment)
  GET    /:id/timeline   → Full timeline (comms, status changes, mods)
  
/api/customers
  GET    /              → List customers (filter by segment, health)
  POST   /              → Create customer (or auto-create on enquiry)
  GET    /:id           → Customer profile + enquiry/booking history
  PATCH  /:id           → Update profile, preferences
  GET    /:id/lifetime-value → Compute CLV, churn risk
  
/api/bookings
  GET    /              → List bookings (filter by status, date, customer)
  POST   /              → Create booking (from confirmed enquiry)
  GET    /:id           → Booking details + items + payments
  PATCH  /:id           → Modify booking (dates, travellers)
  POST   /:id/cancel    → Cancel booking (with reason, auto-refund calc)
  GET    /:id/vouchers   → List all voucher URLs
  
/api/vendors
  GET    /              → Search vendors (filter by type, region, rating)
  POST   /              → Create vendor (admin only)
  GET    /:id           → Vendor profile + performance
  PATCH  /:id           → Update contract, tier
  GET    /:id/bookings   → Historical bookings with this vendor
  
/api/communications
  GET    /              → List comms (filter by enquiry, booking)
  POST   /              → Send comm (auto-detect channel)
  GET    /:id           → Comm details + attachments
  POST   /drafts         → Generate AI draft
  PATCH  /drafts/:id    → Human edits draft
  POST   /drafts/:id/send → Send draft → create comm record
  
/api/agents
  GET    /              → List agents (filter by status, skills)
  PATCH  /:id/status    → Update availability
  GET    /:id/workload    → Current enquiries, performance
  POST   /auto-assign     → Auto-assign enquiry to best agent
```

### AI Engine Endpoint (Called by Entity APIs)**

```
/api/spine/run
  POST   /              → Run AI Engine on enquiry
  Input:  enquiry_id (loads from DB, not raw text)
  Output: CanonicalPacket (unchanged schema for compatibility)
  
  Called when:
    - New enquiry created (auto-run NB01 + NB02)
    - Agent requests "re-analyze"
    - Booking modification requested (re-check risks)
```

**My insight:**  
Entity APIs should **own business logic** (assignment rules, SLA calculations).  
AI Engine is **stateless** — takes input, returns analysis, Entity API persists results.

---

## 5. AI Engine Integration (spine_api Re-Design)**

### Current State (Broken)

```python
# spine_api/server.py
@app.post("/run")
async def run_spine(payload: RunRequest):
    # NB01: Parse raw text → CanonicalPacket
    packet = run_nb01(payload.raw_note)
    
    # NB02: Decision (ASK_FOLLOWUP, PROCEED, etc.)
    decision = run_nb02(packet)
    packet['decision_state'] = decision
    
    return packet  # <-- Ephemeral! Not persisted!
```

### My Proposed Flow (Entity-Aware)

```python
# Entity API calls AI Engine
@app.post("/api/enquiries/{enquiry_id}/analyze")
async def analyze_enquiry(enquiry_id: str):
    # 1. Load enquiry + customer + past bookings from DB
    enquiry = db.get_enquiry(enquiry_id)
    customer = db.get_customer(enquiry.customer_id)
    past_trips = db.get_past_trips(customer.id)
    
    # 2. Call AI Engine with full context
    packet = spine_client.run(
        raw_note=enquiry.raw_text,
        customer_context=customer,
        past_trips=past_trips
    )
    
    # 3. Persist results to DB
    db.update_enquiry(enquiry_id, {
        'facts': packet.facts,
        'derived_signals': packet.derived_signals,
        'decision_state': packet.decision_state
    })
    
    # 4. Return updated enquiry
    return db.get_enquiry(enquiry_id)
```

**My insight:**  
AI Engine should be a **Python library** (importable), not just an HTTP service.  
Entity APIs can `import spine_api` and call it in-process for lower latency.

---

## 6. Frontend Information Architecture**

### Core Pages (Next.js App Router)**

```
/app
  /dashboard               → Agent dashboard (assigned enquiries, workload)
  /enquiries
    /                     → List + filters (status, type, priority)
    /new                   → New enquiry form (auto-detects channel)
    /[id]                 → Enquiry detail
      /timeline             → Full timeline view
      /draft               → Draft editor (AI-assisted)
      /communications       → All comms for this enquiry
      
  /customers
    /                     → Customer list + search
    /[id]                 → Customer profile
      /enquiries           → Their enquiries
      /bookings            → Their bookings
      /lifetime-value       → CLV, health score
      
  /bookings
    /                     → Booking list + filters
    /new                   → Create booking (from enquiry)
    /[id]                 → Booking detail
      /items                → Flight/hotel/transfer items
      /payments             → Payment tracking
      /modifications        → Change history
      /vouchers            → Download vouchers
      
  /vendors
    /                     → Vendor list + search
    /new                   → Add vendor (admin)
    /[id]                 → Vendor profile
      /performance          → Rating, complaints, response time
      /bookings            → Historical bookings
      
  /communications
    /                     → All comms across enquiries/bookings
    /drafts               → Draft management
    /templates            → Template library
    
  /agents
    /                     → Agent list (admin/manager)
    /[id]                 → Agent profile
      /workload             → Current assignments
      /performance          → Conversion, satisfaction
```

**My insight:**  
Each entity gets its own **section** with list + detail + sub-resources.  
Use **parallel loading** (React Query) for related entities on detail pages.

---

## 7. Migration Strategy (Non-Destructive)**

### Phase 1: Add Entity Tables (Parallel)

1. Create new tables: `customers`, `agents`, `vendors`, `enquiries`, `bookings`, etc.
2. Keep existing `spine_api` + `CanonicalPacket` running (backward compat)
3. New Entity APIs run **alongside** old BFF proxy
4. Frontend gradually adopts new APIs

### Phase 2: Data Migration (Backfill)

1. Parse existing `CanonicalPacket` history → backfill `enquiries` table
2. Extract `facts.customer_id` → create `customers` table
3. Extract `coordinator_id` → create `agents` table
4. Compute `bookings` from `facts.selected_itinerary`

### Phase 3: Cutover (Flip the Switch)

1. Mark old BFF proxy as deprecated (still serves, but no new features)
2. Frontend fully uses new Entity APIs
3. `spine_api` becomes a **called service** (not the router)
4. After 2 release cycles: remove old BFF proxy

**My insight:**  
Don't do a "big bang" migration. Run old + new **in parallel** for 1 sprint.

---

## 8. Key Architectural Decisions**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| AI Engine as library or service? | Library / HTTP service | **Both** — import for in-process, HTTP for isolation |
| Entity API framework? | FastAPI / Django REST / NestJS-style | **FastAPI** — what we have, async, Pydantic-native |
| Database? | PostgreSQL / MongoDB / MySQL | **PostgreSQL** — relational, JSONB for flexibility |
| Cache? | Redis / Memcached / None | **Redis** — session, enquiry locks, agent status |
| Frontend state? | React Query / Redux / Zustand | **React Query + Zustand** — server state + client state |
| Migration approach? | Big bang / Parallel / Gradual | **Parallel** — run old + new together |

---

## 9. What's Next? Implementation Planning**

We've now defined:
1. ✅ **What** (Entities: enquiry, customer, agent, vendor, booking, comms)
2. ✅ **How they relate** (Database schema with foreign keys)
3. ✅ **How to expose them** (RESTful APIs)
4. ✅ **How AI fits** (called service, not the router)
5. ✅ **How frontend consumes** (Information architecture)

### Next Steps (Concrete Actions)

1. **Create database migration** — `alembic/versions/001_add_entity_tables.py`
2. **Implement Entity APIs** — start with `/api/customers` + `/api/enquiries`
3. **Refactor spine_api** — make it importable as `spine_api.run(packet)` not just HTTP
4. **Frontend: new sections** — build `/enquiries/[id]` page first (most critical)
5. **Migration script** — backfill entities from existing data

---

**Next file:** `Docs/discussions/implementation_roadmap_2026-04-29.md`  
(Detailed sprint plan with tasks, dependencies, and timelines)
