# Research: Data Strategy & Persistence

**Status**: 🔴 High Priority - Blocking implementation phase  
**Topic ID**: 2  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-04-09

---

## Quick Summary

**What**: How to store CanonicalPackets, customer data, documents  
**Why**: Notebooks use in-memory objects; real system needs persistence  
**Scope**: Database choice, schema design, retention, security  
**Status**: Initial research phase

---

## The Core Question

The system generates rich state objects (CanonicalPackets) with:
- Facts (explicit data)
- Derived signals (computed)
- Hypotheses (guesses)
- Unknowns (missing)
- Contradictions (conflicts)
- Provenance (evidence trails)

Where does this live? For how long? How do we query it?

---

## 1. Database Selection

### Options

| Database | Type | Pros | Cons | Best For |
|----------|------|------|------|----------|
| **PostgreSQL** | Relational + JSON | Reliable, JSONB support, proven | Schema migrations | Primary database |
| **MongoDB** | Document | Schema flexibility, nested docs | Less mature transactions | Rapid iteration |
| **SQLite** | Embedded | Zero setup, portable | Not for multi-user | Single-agent use |
| **MySQL** | Relational | Widely supported | JSON support weaker | Legacy compatibility |
| **DynamoDB** | NoSQL | Serverless, fast | Complex queries hard | AWS-native apps |

### Recommendation

**PostgreSQL with JSONB**

**Why**:
- Industry standard for reliability
- JSONB columns for flexible CanonicalPackets
- Full ACID transactions
- Excellent Python support (SQLAlchemy, psycopg2)
- Can evolve schema gradually
- Vector extension (pgvector) for similarity search

**Configuration**:
- PostgreSQL 15+
- JSONB for CanonicalPacket storage
- Normalized tables for customers, bookings
- Read replicas for scale (future)

---

## 2. Schema Design

### Core Tables

```sql
-- Customers (the humans)
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE,  -- WhatsApp number
    email VARCHAR(255),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Travel Agencies (for multi-tenant)
CREATE TABLE agencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255),
    tier VARCHAR(20),  -- solo, small, enterprise
    settings JSONB     -- per-agency config
);

-- Agents (users of the system)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agency_id UUID REFERENCES agencies(id),
    name VARCHAR(255),
    email VARCHAR(255),
    role VARCHAR(20),  -- owner, senior, junior
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions (conversations)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    agent_id UUID REFERENCES agents(id),
    stage VARCHAR(50),  -- discovery, shortlist, proposal, booking
    status VARCHAR(20),  -- active, closed, converted
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CanonicalPackets (the state objects)
CREATE TABLE packets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    packet_version INT DEFAULT 1,  -- for revision tracking
    
    -- Core state (stored as JSONB)
    facts JSONB,
    derived_signals JSONB,
    hypotheses JSONB,
    unknowns JSONB,
    contradictions JSONB,
    
    -- Metadata
    decision_state VARCHAR(50),  -- ASK_FOLLOWUP, PROCEED, etc.
    confidence_score FLOAT,
    
    -- Provenance
    created_at TIMESTAMP DEFAULT NOW(),
    source_envelope_ids UUID[]  -- links to raw inputs
);

-- Events (audit trail)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    packet_id UUID REFERENCES packets(id),
    event_type VARCHAR(50),  -- fact_extracted, blocker_resolved, etc.
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Bookings (final output)
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),
    customer_id UUID REFERENCES customers(id),
    status VARCHAR(20),  -- confirmed, canceled, completed
    details JSONB,       -- itinerary, costs, etc.
    created_at TIMESTAMP DEFAULT NOW()
);
```

### JSONB Structure (CanonicalPacket)

```json
{
  "packet_id": "uuid",
  "schema_version": "0.1",
  "stage": "discovery",
  
  "facts": {
    "destination_city": {
      "value": "Singapore",
      "confidence": 0.95,
      "authority_level": "explicit_user",
      "extraction_mode": "direct_extract",
      "evidence_refs": [...]
    }
  },
  
  "derived_signals": {
    "trip_type": {
      "value": "international",
      "confidence": 1.0,
      "authority_level": "derived_signal"
    }
  },
  
  "hypotheses": {
    "budget_tier": {
      "value": "mid_range",
      "confidence": 0.7,
      "authority_level": "soft_hypothesis"
    }
  },
  
  "unknowns": [
    {
      "field_name": "exact_dates",
      "reason": "not_present_in_source",
      "severity": "hard"
    }
  ],
  
  "contradictions": [
    {
      "field_name": "budget_range",
      "values": ["2L", "3L"],
      "sources": ["email", "call"],
      "status": "open"
    }
  ],
  
  "decision_state": "ASK_FOLLOWUP",
  "confidence_score": 0.65
}
```

### Why This Design?

1. **Normalized + JSONB hybrid**:
   - Normalized: Customers, agents, bookings (stable schema)
   - JSONB: CanonicalPackets (evolving schema)

2. **Versioning**:
   - `packet_version` tracks revisions
   - Can reconstruct history
   - Audit trail in events table

3. **Query flexibility**:
   - JSONB operators for complex queries
   - GIN indexes for fast JSON searches

---

## 3. Vector Database (for Similarity Search)

### Use Cases

1. **Customer matching**: "Find customers similar to this one"
2. **Recommendation**: "Customers like this liked X"
3. **Duplicate detection**: "Is this the same customer?"
4. **Knowledge retrieval**: "Similar past scenarios"

### Options

| Vector DB | Hosting | Cost | Notes |
|-----------|---------|------|-------|
| **pgvector** | Self-hosted (PostgreSQL) | Free | Good for <100K vectors |
| **Pinecone** | Managed | $70/month starter | Easy, scalable |
| **Weaviate** | Self or managed | Varies | Graph + vector |
| **Chroma** | Self-hosted | Free | New, simple |
| **Qdrant** | Self or managed | Varies | Rust-based, fast |

### Recommendation

**pgvector for MVP**
**Pinecone for scale**

**Why**:
- pgvector = one less system (same PostgreSQL)
- Easy to start
- Migrate to Pinecone later if needed

### Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Customer embeddings
CREATE TABLE customer_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scenario embeddings (for similarity)
CREATE TABLE scenario_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    packet_id UUID REFERENCES packets(id),
    embedding vector(1536),
    outcome VARCHAR(50),  -- converted, abandoned, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Similarity search index
CREATE INDEX ON customer_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 4. Data Retention & GDPR

### Retention Policy

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| **Active customer data** | Indefinite | Business need |
| **Completed bookings** | 7 years | Tax/legal |
| **Canceled bookings** | 2 years | Analytics |
| **Abandoned sessions** | 1 year | Re-engagement |
| **Raw WhatsApp logs** | 90 days | Debugging |
| **Passport scans** | Trip date + 6 months | Security |

### GDPR/Compliance

**Requirements**:
- Right to deletion (anonymization, not hard delete)
- Data export (portability)
- Consent tracking
- Breach notification

**Implementation**:
```sql
-- Soft delete (GDPR compliance)
ALTER TABLE customers ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE customers ADD COLUMN anonymized BOOLEAN DEFAULT FALSE;

-- Export view (for data portability)
CREATE VIEW customer_export AS
SELECT id, name, email, phone, created_at
FROM customers
WHERE deleted_at IS NULL;

-- Consent tracking
CREATE TABLE consent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    consent_type VARCHAR(50),  -- marketing, data_processing
    granted BOOLEAN,
    recorded_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. Backup & Disaster Recovery

### Strategy

| Layer | Frequency | Retention | Method |
|-------|-----------|-----------|--------|
| **Database** | Daily | 30 days | pg_dump to S3 |
| **WAL (Write-Ahead Log)** | Continuous | 7 days | Streaming to S3 |
| **Document Storage** | Real-time | Versioned | S3 cross-region |
| **Full snapshot** | Weekly | 12 weeks | RDS snapshot |

### Recovery Objectives

- **RPO (Recovery Point Objective)**: 1 hour (max data loss)
- **RTO (Recovery Time Objective)**: 4 hours (max downtime)

---

## 6. Migration from Existing Systems

### The Problem

Agencies have data in:
- WhatsApp (unstructured)
- Excel/Google Sheets
- Some CRM
- Agent's heads

### Migration Strategy

**Phase 1: Manual Import** (MVP)
- CSV upload for customer lists
- Document upload for passports/tickets
- Agent manually fills key fields

**Phase 2: Assisted Import**
- AI extraction from WhatsApp export
- Excel parser with field mapping
- Validation workflow

**Phase 3: Continuous Sync**
- Google Sheets two-way sync
- WhatsApp webhook for real-time

### Excel Import Schema

```python
# Expected CSV columns
csv_mapping = {
    "Customer Name": "customers.name",
    "Phone": "customers.phone", 
    "Email": "customers.email",
    "Last Trip": "bookings.destination",
    "Last Trip Date": "bookings.trip_date",
    "Preferences": "customers.preferences",  # JSONB
}
```

---

## 7. Query Patterns

### Common Queries

```sql
-- Get latest packet for session
SELECT * FROM packets 
WHERE session_id = ? 
ORDER BY created_at DESC 
LIMIT 1;

-- Find sessions with hard blockers
SELECT s.*, p.decision_state
FROM sessions s
JOIN packets p ON s.id = p.session_id
WHERE p.decision_state = 'ASK_FOLLOWUP'
AND s.status = 'active';

-- Search customers by name/phone
SELECT * FROM customers 
WHERE name ILIKE '%sharma%'
OR phone LIKE '%98765%';

-- Get customer history
SELECT s.*, p.facts, b.status as booking_status
FROM sessions s
LEFT JOIN packets p ON s.id = p.session_id
LEFT JOIN bookings b ON s.id = b.session_id
WHERE s.customer_id = ?
ORDER BY s.created_at DESC;

-- Vector similarity search (pgvector)
SELECT customer_id, 
       embedding <-> query_embedding AS distance
FROM customer_embeddings
ORDER BY distance
LIMIT 5;
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_packets_session ON packets(session_id, created_at DESC);
CREATE INDEX idx_events_packet ON events(packet_id, created_at);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_email ON customers(email);

-- JSONB indexes for common queries
CREATE INDEX idx_packets_decision ON packets(decision_state);
CREATE INDEX idx_packets_facts ON packets USING GIN (facts);
```

---

## 8. Cost Estimates

### RDS PostgreSQL (AWS)

| Tier | Instance | Storage | Monthly Cost |
|------|----------|---------|--------------|
| **Dev** | db.t3.micro | 20GB | ~$15 |
| **MVP** | db.t3.small | 100GB | ~$50 |
| **Scale** | db.r5.large | 500GB | ~$200 |
| **Enterprise** | db.r5.xlarge | 2TB | ~$500 |

### Storage (S3)

| Data Type | Size/Customer | 1000 Customers | Monthly Cost |
|-----------|---------------|----------------|--------------|
| **Database** | ~100KB | ~100MB | Included in RDS |
| **Documents** | ~10MB | ~10GB | ~$0.25 |
| **Backups** | ~50MB | ~50GB | ~$1.15 |
| **Logs** | ~5MB | ~5GB | ~$0.12 |

### Vector DB

| Option | 10K vectors | 100K vectors | 1M vectors |
|--------|-------------|--------------|------------|
| **pgvector** (self) | Free | Free | Free |
| **Pinecone** | $70/mo | $70/mo | $200/mo |

---

## Decision Matrix

| Question | Answer |
|----------|--------|
| Primary database? | PostgreSQL |
| CanonicalPacket storage? | JSONB column |
| Vector search? | pgvector (MVP), Pinecone (scale) |
| Retention? | 7 years bookings, 1 year abandoned |
| Backup? | Daily dumps + continuous WAL |
| Encryption? | At-rest (AWS), in-transit (TLS) |

---

## Open Questions

- [ ] Multi-tenant schema? (separate DBs vs schemas vs row-level security)
- [ ] Partitioning strategy for packets table? (by date)
- [ ] Cache layer needed? (Redis for hot sessions)
- [ ] Real-time sync requirements? (WebSockets vs polling)
- [ ] Data residency requirements? (India-only hosting?)

---

## Next Actions

1. **Set up PostgreSQL 15** (local dev)
2. **Create initial schema** (migrations)
3. **Install pgvector** (test similarity search)
4. **Design migration tool** (CSV import)
5. **Set up S3 bucket** (document storage)

---

## References

- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Best_practices)
- [GDPR Compliance Guide](https://gdpr.eu/checklist/)

---

## Related Topics

- [INTEGRATION_ARCHITECTURE.md](INTEGRATION_ARCHITECTURE.md) - WhatsApp, APIs
- [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) - Encryption, PII
- [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) - Master index

---

*Status: Initial research phase. Update as schema evolves.*
