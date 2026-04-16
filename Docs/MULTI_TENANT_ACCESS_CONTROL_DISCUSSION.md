# Multi-Tenant Access Control & Identification Discussion

**Date**: 2026-04-16
**Purpose**: Define how users, agencies, customers, and vendors are identified and access controlled
**Status**: Discussion document - needs decisions

---

## Current Implementation Status

### Existing Models

**SourceEnvelope** (`specs/source_envelope.schema.json:41-52`):
```json
{
  "actor_type": "traveler" | "agency_owner" | "agent_operator" | "system",
  "actor_id": "string | null"
}
```
- **Purpose**: Track who provided data (provenance)
- **Limitation**: Not for access control, only data attribution

**CanonicalPacket** (`specs/canonical_packet.schema.json:342-343`):
```json
{
  "customer_id": {
    "value": "string",
    "confidence": 0.0,
    "authority_level": "explicit_user",
    "evidence_refs": [...]
  }
}
```
- **Purpose**: Track which customer this trip belongs to
- **Limitation**: Trip data, not access control

---

## Multi-Tenant Access Model

### Layer 1: Agency (Tenant) Identification

**How Agencies Are Identified**:
```
┌─────────────────────────────────────────────────────────────────────┐
│  TENANT MANAGEMENT                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Agency ID: tenant_id (UUID)                                    │
│  Identification Methods:                                          │
│  • Subdomain: priyatravels.agency-os.com                       │
│  • Custom Domain: trips.priyatravels.com                       │
│  • API Key: For programmatic access                              │
│                                                                 │
│  Agency Config:                                                  │
│  {                                                             │
│    "tenant_id": "uuid-here",                                     │
│    "agency_name": "Priya Travels",                              │
│    "branding": {...},                                           │
│    "plan": "professional",                                       │
│    "whatsapp_config": {...},                                      │
│    "team_members": [...]                                          │
│  }                                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Tenant Isolation** (Critical for Multi-Tenant):
```sql
-- ALL queries must filter by tenant_id
SELECT * FROM packets
WHERE tenant_id = 'priyatravels-uuid'
AND customer_phone = '+91-98765-43210';

-- Prevent cross-tenant access
-- Packet from Agency A cannot be accessed by Agency B
```

---

### Layer 2: Agency User Identification & Access

**User Roles Within Agency**:
```
┌─────────────────────────────────────────────────────────────────────┐
│  AGENCY: Priya Travels (tenant_id: priyatravels-uuid)           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USERS:                                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ OWNER (priya@priyatravels.com)                        │   │
│  │ role: owner                                              │   │
│  │ permissions: [                                            │   │
│  │   "agency:*",              # Full agency access             │   │
│  │   "team:manage",           # Add/remove team members        │   │
│  │   "billing:manage",        # Subscription, invoices        │   │
│  │   "branding:manage",      # Logo, colors, domain         │   │
│  │   "integrations:manage",   # WhatsApp, email, CRM        │   │
│  │   "analytics:view",        # All metrics                  │   │
│  │   "packets:*"             # All trip packets              │   │
│  │ ]                                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ SENIOR AGENT (rahul@priyatravels.com)                  │   │
│  │ role: agent                                              │   │
│  │ permissions: [                                            │   │
│  │   "packets:read",         # View trip packets            │   │
│  │   "packets:write",        # Edit trip packets            │   │
│  │   "packets:delete",      # Delete trip packets            │   │
│  │   "messages:send",        # Send to customers           │   │
│  │   "analytics:view",        # Limited to own stats        │   │
│  │   "proposals:create"      # Create proposals             │   │
│  │ ]                                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ JUNIOR AGENT (ankit@priyatravels.com)                    │   │
│  │ role: junior                                             │   │
│  │ permissions: [                                            │   │
│  │   "packets:read",         # View assigned only           │   │
│  │   "packets:write:assigned", # Edit assigned only           │   │
│  │   "messages:send:assigned", # Send to assigned customers   │   │
│  │   "analytics:view:own"    # Very limited stats          │   │
│  │ ]                                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**User Database Schema**:
```sql
CREATE TABLE agency_users (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),  -- Multi-tenant!
  email VARCHAR(100) UNIQUE,
  password_hash VARCHAR(255),
  role VARCHAR(20) NOT NULL,  -- owner, agent, junior
  permissions JSONB,  -- Explicit permission list
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  last_login_at TIMESTAMP,

  UNIQUE(tenant_id, email)  -- Email unique within agency
);
```

**Authentication Flow**:
```python
# User logs in to priyatravels.agency-os.com
POST /api/auth/login
{
  "email": "rahul@priyatravels.com",
  "password": "hashed_password"
}

# Response
{
  "access_token": "jwt_token_here",
  "user": {
    "id": "user-uuid",
    "email": "rahul@priyatravels.com",
    "role": "agent",
    "tenant_id": "priyatravels-uuid",
    "permissions": ["packets:read", "packets:write", ...]
  }
}

# JWT contains tenant_id and permissions
# Middleware validates on every request
```

---

### Layer 3: Customer Identification & Portal Access

**Customer Data Model**:
```sql
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),  -- Multi-tenant!
  customer_id VARCHAR(50) UNIQUE,  -- Human-readable ID
  name VARCHAR(100),
  email VARCHAR(100),
  phone VARCHAR(20) UNIQUE,
  preferences JSONB,  -- Past trips, dietary needs, etc.
  created_at TIMESTAMP DEFAULT NOW(),

  UNIQUE(tenant_id, phone)  -- Phone unique within agency
);

CREATE TABLE packets (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  customer_id UUID REFERENCES customers(id),
  packet_id VARCHAR(50) UNIQUE,
  stage VARCHAR(20),
  facts JSONB,
  -- ... rest of packet fields

  INDEX(tenant_id, customer_id)  -- Fast lookups
);
```

**Customer Portal Access Models**:

**Option A: Magic Link (Recommended for MVP)**
```
1. Agency generates portal link:
   https://priyatravels.agency-os.com/trip/Sharma-Europe-2024?token=abc123

2. Link expires in 7 days
3. Customer clicks link → JWT validated → Portal loads

4. No password needed for customers
```

**Option B: Phone Verification**
```
1. Customer enters phone: +91-98765-43210
2. System sends OTP via WhatsApp/SMS
3. Customer verifies → Session created
4. Access limited to trips linked to this phone
```

**Option C: Email + Password**
```
1. Customer creates account on agency's branded portal
2. Agency approves account
3. Customer logs in to see their trips
```

**Customer Portal Permissions**:
```python
# Customer JWT has limited scope
{
  "sub": "customer-uuid",
  "tenant_id": "priyatravels-uuid",
  "scope": ["portal:read"],  # Can only view, not edit
  "packet_access": ["packet-123", "packet-456"]  # Specific trips
}

# Can only access:
GET /api/portal/packets?ids=packet-123,packet-456  # ✅ Allowed
POST /api/portal/packets/123/update  # ❌ Forbidden
GET /api/admin/analytics  # ❌ Forbidden
```

---

### Layer 4: Vendor Identification & Access

**Vendor Data Model**:
```sql
CREATE TABLE vendors (
  id UUID PRIMARY KEY,
  vendor_id VARCHAR(50) UNIQUE,  -- Human-readable: "vendor_taj_001"
  name VARCHAR(100),
  type VARCHAR(20),  -- accommodation, transport, activities
  contact_info JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vendor_contracts (
  id UUID PRIMARY KEY,
  vendor_id UUID REFERENCES vendors(id),
  tenant_id UUID NOT NULL REFERENCES tenants(id),  -- Agency-specific!
  discount_percentage DECIMAL(5,2),
  terms JSONB,
  is_active BOOLEAN DEFAULT true,

  UNIQUE(vendor_id, tenant_id)  -- One contract per vendor per agency
);
```

**Vendor Access Models**:

**Option A: API-Only (Recommended for MVP)**
```
┌─────────────────────────────────────────────────────────────────────┐
│  VENDOR: Taj Hotels                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Access:                                                     │
│  • API Key for inventory updates                               │
│  • Webhook URL for booking notifications                        │
│  • No direct login to Agency OS dashboard                      │
│                                                                 │
│  API Calls:                                                   │
│  POST /api/vendors/inventory/update                             │
│    {                                                         │
│      "vendor_key": "taj-api-key-xyz",                           │
│      "rooms": [...]                                            │
│    }                                                         │
│                                                                 │
│  POST /api/webhooks/vendor/booking                               │
│    {                                                         │
│      "agency_id": "priyatravels",                             │
│      "booking": {...}                                          │
│    }                                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

**Option B: Vendor Portal (Future)**
```
Vendors get their own dashboard to:
- Update inventory
- View bookings from partner agencies
- Manage special offers

Authentication: vendor_api_key (not password)
```

**Shared vs. Agency-Specific Vendors**:
```python
# Global vendor (all agencies can see)
{
  "vendor_id": "vendor_taj_001",
  "name": "Taj Hotels",
  "type": "accommodation",
  "is_global": true,
  "contracts": [
    {"tenant_id": "priyatravels", "discount": "15%"},
    {"tenant_id": "rahultours", "discount": "12%"}
  ]
}

# Agency-specific vendor (only one agency sees)
{
  "vendor_id": "vendor_local_001",
  "name": "Rajasthan Palace Tours",
  "type": "transport",
  "tenant_id": "priyatravels",  -- Belongs to Priya only
  "is_global": false
}
```

---

## Critical Design Decisions Needed

### 1. Authentication Method for Agency Users

**Question**: How do agency staff authenticate?

**Options**:
| Method | Pros | Cons | Recommendation |
|--------|-------|-------|----------------|
| **Email + Password** | Simple, standard | Password management | ✅ MVP |
| **Google SSO** | No passwords, secure | Requires Google Cloud setup | Phase 2 |
| **Magic Link** | No passwords, email-based | Agency may prefer traditional login | Future |

**Decision**: Email + password for MVP, SSO for later

---

### 2. Customer Portal Access

**Question**: How do customers access their trip portals?

**Options**:
| Method | Pros | Cons | Recommendation |
|--------|-------|-------|----------------|
| **Magic Link** | No signup, expires for security | Need to regenerate each time | ✅ MVP |
| **Phone + OTP** | Uses existing WhatsApp | SMS costs | Phase 2 |
| **Email + Password** | Persistent access | Friction for one-time trips | Future |

**Decision**: Magic links for MVP (no customer accounts needed)

---

### 3. Vendor Access Level

**Question**: Do vendors need direct UI access, or API-only?

**Options**:
| Method | Pros | Cons | Recommendation |
|--------|-------|-------|----------------|
| **API-Only** | Simple, secure | Vendors can't self-serve | ✅ MVP |
| **Vendor Portal** | Self-service, transparency | Build UI, manage access | Phase 2 |
| **Hybrid** | Best of both | Complex | Future |

**Decision**: API-only for MVP, vendor portal when multiple vendors onboard

---

### 4. Permission Granularity

**Question**: How fine-grained should permissions be?

**Options**:
| Approach | Example | Complexity | Recommendation |
|----------|----------|--------------|----------------|
| **Role-Based** | "agent" role has X permissions | Simple | ✅ MVP |
| **Resource-Based** | Can edit packet-123 but not packet-456 | Complex | Future |
| **Attribute-Based** | Can edit packets created_by = self | Very complex | Not needed |

**Decision**: Role-based permissions for MVP

---

### 5. Cross-Agency Data Sharing

**Question**: Can agencies see shared data (vendor database, budget tables)?

**Options**:
| Approach | Description | Recommendation |
|----------|--------------|----------------|
| **Isolated** | Each agency has separate data | ❌ Duplicates effort |
| **Shared Read-Only** | Global vendors, budgets visible to all | ✅ MVP |
| **Contributory** | Agencies add to shared pool | Phase 2 |

**Decision**: Shared read-only for vendors/budgets, contributions later

---

## Implementation Priority (MVP)

### Phase 1: Single-Tenant (Current Focus)
- [ ] Simple login (email + password) for ONE agency
- [ ] Magic links for customer portals
- [ ] API-only vendor access
- [ ] Basic role permissions (owner vs agent)

### Phase 2: Multi-Tenant (When Ready)
- [ ] Tenant identification via subdomain
- [ ] Tenant isolation in all queries
- [ ] Per-tenant branding
- [ ] Agency signup/onboarding

### Phase 3: Advanced Features
- [ ] SSO for agencies
- [ ] Vendor portal
- [ ] Fine-grained permissions
- [ ] Cross-agency data contributions

---

## Security Considerations

### Tenant Isolation (Critical)
```python
# Middleware to prevent cross-tenant access
@app.middleware("http")
async def tenant_isolation(request: Request, call_next):
    user = get_user_from_jwt(request)
    requested_tenant_id = request.state.tenant_id

    # User can only access their own tenant
    if user.tenant_id != requested_tenant_id:
        raise HTTPException(403, "Cross-tenant access forbidden")

    return await call_next(request)
```

### JWT Token Structure
```python
# Agency user JWT
{
  "sub": "user-uuid",
  "tenant_id": "priyatravels-uuid",
  "role": "agent",
  "permissions": ["packets:read", "packets:write"],
  "exp": 1234567890
}

# Customer portal JWT
{
  "sub": "customer-uuid",
  "tenant_id": "priyatravels-uuid",
  "scope": ["portal:read"],
  "packet_access": ["packet-123", "packet-456"],
  "exp": 1234567890  # Short expiry (7 days)
}

# Vendor API JWT
{
  "sub": "vendor-uuid",
  "vendor_id": "vendor_taj_001",
  "scope": ["vendor:inventory:update", "vendor:bookings:view"],
  "exp": 1234567890
}
```

---

## Open Questions

1. **User Onboarding**: How do new agencies sign up? (Manual approval vs. self-serve?)
2. **Team Management**: Can agency owners invite team members? (Yes for MVP?)
3. **Customer Identity**: Can a customer belong to multiple agencies? (Phone collision across tenants?)
4. **Vendor Contracts**: How are vendor contracts negotiated? (Out of band for MVP?)
5. **Data Portability**: Can agencies export their data? (GDPR requirement?)

---

## Next Steps

1. **Decide on MVP authentication method** for agency users
2. **Choose customer portal access model** (magic link vs. other)
3. **Define exact role permissions** for owner, agent, junior
4. **Design database schema** for users, customers, vendors
5. **Implement tenant middleware** (even if single-tenant now, scaffold for future)
6. **Build authentication endpoints** (login, logout, token refresh)
7. **Implement permission checks** on all API routes

---

*This document captures the multi-tenant access control discussion. Decisions needed before implementation.*
