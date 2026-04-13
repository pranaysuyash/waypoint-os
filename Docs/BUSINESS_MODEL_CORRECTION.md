# Business Model Correction: White-Label B2B SaaS Platform

**Date**: 2026-04-13
**Purpose**: Correct understanding of what this product actually is
**Status**: Replaces previous UX assumptions about direct customer interaction

---

## The Critical Correction

### What I Got Wrong

I documented this as if **you are the agency** serving customers directly.

**WRONG MODEL:**
```
You → Customer (via "Agency OS" branded portal)
```

### The Correct Model

You're building a **white-label B2B SaaS platform** that travel agencies subscribe to.

```
You (Platform) → Agency (Subscriber) → Agency's Customers
```

**Agencies use your tool to serve THEIR customers.**
**Customers never see "Agency OS" branding.**

---

## The Actual Business Model

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOU (Platform Builder)                                                        │
│  ───────────────────────────────────────────────────────────────────────────────│
│  Build: Agency OS Platform                                                     │
│  Sell: SaaS subscription to travel agencies                                     │
│  Your customers: Travel agencies (not end travelers)                            │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓ SaaS Subscription
┌─────────────────────────────────────────────────────────────────────────────────┐
│  TRAVEL AGENCY (Your Customer)                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│  Uses: Agency OS dashboard to manage their customers                            │
│  Sees: Their branding, their customers, their data                             │
│  Pays: Monthly/annual subscription to you                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓ White-labeled experience
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY'S CUSTOMERS (End Travelers)                                             │
│  ───────────────────────────────────────────────────────────────────────────────│
│  Sees: Agency's branding, agency's logo, agency's domain                       │
│  Interacts with: Agency (via your platform, invisibly)                         │
│  Never knows: "Agency OS" exists                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## What This Changes for UX

### Agent Dashboard (Your Main Product)

**What agencies see:**
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  [AGENCY LOGO] Priya Travels                                                 │
│  ───────────────────────────────────────────────────────────────────────────────│
│  Powered by Agency OS                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Agency's own branding, colors, logo]                                         │
│  [Their customer list, their trips, their revenue]                            │
│  [Your NB01-NB02-NB03 logic running invisibly]                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**"Powered by Agency OS"** = Small/subtle footer attribution (or completely white-label)

### Customer Portal (Branded to Each Agency)

**What travelers see:**
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOUR TRIP TO EUROPE                                              [Priya Travels Logo]│
│  ───────────────────────────────────────────────────────────────────────────────│
│  priyatravels.com/your-trip/Sharma-Europe-2024                               │
│                                                                                  │
│  [Agency's branding, agency's colors, agency's domain]                         │
│  [Your platform powering it invisibly]                                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key points:**
- Portal lives on agency's domain (or subdomain)
- Agency's branding, not yours
- Traveler thinks "this is Priya Travels' portal"
- Your tech is completely invisible

---

## Multi-Tenant Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOUR PLATFORM (Agency OS)                                                     │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ TENANT MANAGEMENT                                                           ││
│  │ • Agency signup/subscription                                                ││
│  │ • Branded subdomain (agency.agency-os.com or custom domain)                 ││
│  │ • White-label configuration                                                 ││
│  │ • Billing per agency                                                       ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ CORE LOGIC (NB01-NB02-NB03)                                                 ││
│  │ • Intake & Normalization                                                    ││
│  │ • Decision Engine                                                           ││
│  │ • Session Strategy                                                          ││
│  │ [Used by ALL agencies, but results isolated by tenant]                     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ SHARED SERVICES                                                              ││
│  │ • Budget feasibility tables (shared across agencies)                        ││
│  │ • Supplier database (agencies can contribute, everyone benefits)            ││
│  │ • Template library (agencies can customize)                                ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY TENANT (e.g., Priya Travels)                                            │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ AGENCY DASHBOARD                                                            ││
│  │ • Priya's customers, Priya's trips, Priya's revenue                         ││
│  │ • Priya's branding/colors                                                  ││
│  │ • Priya's team (if multi-agent)                                             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ CUSTOMER PORTAL (priyatravels.com/trips/...)                              ││
│  │ • Branded to Priya Travels                                                 ││
│  │ • Priya's logo, colors, domain                                             ││
│  │ • Powered by Agency OS (subtle or hidden)                                  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Customer-Facing Product Layers

### Layer 1: Agency OS (Your B2B Product)

**Target customer:** Travel agencies
**What they see:**
- Dashboard to manage their customers
- NB01-NB02-NB03 decision engine
- Team management (if they have staff)
- Analytics on their business
- Settings: branding, domain, WhatsApp integration

**Pricing:** SaaS subscription (₹999-4,999/month depending on tier)

### Layer 2: Branded Customer Portal (Agency's Front-End)

**Target user:** Agency's customers
**What they see:**
- Agency's branding (logo, colors, name)
- Agency's domain (priyatravels.com)
- Agency's WhatsApp number
- Agency's email address

**Key point:** They don't know Agency OS exists

### Layer 3: Audit Mode (Your Lead Gen Tool)

**Target user:** Anyone (could be agency's lead gen tool, or your direct marketing)
**What they see:**
- Could be branded to Agency OS (your lead gen)
- OR white-label for agencies (they embed on their site)

---

## How the Portal URLs Actually Work

### Option A: Subdomain (Easier)

```
Agency: Priya Travels
Their portal: priyatravels.agency-os.com
Their customers visit: priyatravels.agency-os.com/trip/abc123

[Customer sees "Priya Travels" branding, but domain has "agency-os"]
```

**Pros:** Easy to implement, SSL handled by you
**Cons:** Not fully white-label

### Option B: Custom Domain (True White-Label)

```
Agency: Priya Travels
Their portal: trips.priyatravels.com or priyatravels.com/trips
Their customers visit: priyatravels.com/trip/Sharma-Europe-2024

[Customer sees ONLY Priya Travels branding, zero Agency OS mention]
```

**Pros:** Fully white-label, professional
**Cons:** Agency must configure DNS, SSL certificates

### Option C: Embedded (Simplest)

```
Agency: Priya Travels
Their existing site: priyatravels.com
They embed: An iframe or widget on their site

[Customer stays on agency's site, your tech loads invisibly]
```

**Pros:** No domain changes for agency
**Cons:** Iframe limitations, SEO considerations

---

## What an Agency Sets Up

### Agency Onboarding Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY SIGNUP                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  1. CREATE ACCOUNT                                                              │
│     ┌─────────────────────────────────────────────────────────────────────────────┐│
│     │ Agency Name: Priya Travels                                               ││
│     │ Contact Person: Priya Sharma                                             ││
│     │ Email: priya@priyatravels.com                                           ││
│     │ Phone: +91-98765-43210                                                   ││
│     │                                                                         ││
│     │                                                                         ││
│     │                                    [Create Account →]                  ││
│     └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  2. CHOOSE PLAN                                                                  │
│     ┌─────────────────────────────────────────────────────────────────────────────┐│
│     │ ⭐ STARTER - ₹999/month                                                   ││
│     │    • 1 agent                                                              ││
│     │    • 50 customers/month                                                    ││
│     │    • Subdomain (your.agency-os.com)                                      ││
│     │                                                                         ││
│     │ ⭐⭐ PROFESSIONAL - ₹2,499/month                                          ││
│     │    • 3 agents                                                             ││
│     │    • 200 customers/month                                                  ││
│     │    • Custom domain                                                        ││
│     │                                                                         ││
│     │ ⭐⭐⭐ AGENCY - ₹4,999/month                                              ││
│     │    • Unlimited agents                                                     ││
│     │    • Unlimited customers                                                  ││
│     │    • White-label everything                                               ││
│     │                                                                         ││
│     │                                    [Select Plan →]                       ││
│     └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  3. BRANDING SETUP                                                              │
│     ┌─────────────────────────────────────────────────────────────────────────────┐│
│     │ Upload your logo:                                                    [Upload]││
│     │                                                                         ││
│     │ Choose primary color:                                         [Color Picker]││
│     │                                                                         ││
│     │ Choose secondary color:                                       [Color Picker]││
│     │                                                                         ││
│     │ Preview:                                                                   ││
│     │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│     │ │ [LOGO] Priya Travels                                                  │  ││
│     │ │ ───────────────────────────────────────────                         │  ││
│     │ │ Your trip options are ready!                                        │  ││
│     │ └────────────────────────────────────────────────────────────────────────┘  ││
│     │                                                                         ││
│     │                                    [Save & Continue →]                  ││
│     └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  4. DOMAIN SETUP (If Professional plan or higher)                               │
│     ┌─────────────────────────────────────────────────────────────────────────────┐│
│     │ Your portal domain:                                                       ││
│     │                                                                         ││
│     │ ○ Use subdomain: priyatravels.agency-os.com (Easier)                      ││
│     │ ● Use custom domain: trips.priyatravels.com                             ││
│     │                                                                         ││
│     │ If custom domain, add DNS record:                                       ││
│     │ Type: CNAME                                                             ││
│     │ Name: trips                                                              ││
│     │ Value: agency-os.com                                                     ││
│     │                                                                         ││
│     │                                    [Verify Domain →]                     ││
│     └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  5. TEAM SETUP (If they have staff)                                             │
│     ┌─────────────────────────────────────────────────────────────────────────────┐│
│     │ Invite your team:                                                         ││
│     │                                                                         ││
│     │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│     │ │ [Add Team Member]                                                     │  ││
│     │ │                                                                         │  ││
│     │ │ Name: Rahul Sharma                        Role: Agent  [Remove]         │  ││
│     │ │ Email: rahul@priyatravels.com             Status: Active               │  ││
│     │ │                                                                         │  ││
│     │ │ Name: Ankit Kumar                         Role: Junior  [Remove]         │  ││
│     │ │ Email: ankit@priyatravels.com              Status: Pending              │  ││
│     │ │                                                                         │  ││
│     │ │                                    [Invite Another →]                   ││
│     │ └────────────────────────────────────────────────────────────────────────┘  ││
│     │                                                                         ││
│     │                                    [Complete Setup →]                    ││
│     └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## What This Changes for WhatsApp Integration

### Agency Connects THEIR WhatsApp Business

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRIYA TRAVELS' WhatsApp Business                                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  • WhatsApp Business App with Priya's phone number                             │
│  • Or WATI connected to Priya's number                                          │
│  • Customers message Priya on WhatsApp                                         │
│  • Priya uses Agency OS dashboard to generate responses                        │
│  • Priya copies/pastes or sends via WhatsApp API (connected to Agency OS)     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Your Platform's Role

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY OS (Your Platform)                                                      │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  For each agency, you manage:                                                   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ AGENCY SETTINGS                                                             ││
│  │ ───────────────────────────────────────────────────────────────────────────││
│  │                                                                            ││
│  │ WhatsApp Integration:                                                       ││
│  │ ○ Manual (Copy-paste) - Agency handles WhatsApp manually                  ││
│  │ ● WATI (API) - Agency connects their WATI API key                           ││
│  │ ○ Twilio - Agency connects their Twilio account                            ││
│  │                                                                            ││
│  │ WATI API Key: [agency-enters-their-key]                                  ││
│  │ WhatsApp Business Number: +91-98765-43210                                ││
│  │                                                                            ││
│  │ Test Connection: [Send Test Message]                                       ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  When agency's customer messages:                                              │
│  1. Message comes to agency's WhatsApp number                                 │
│  2. Webhook sends to Agency OS (if API connected)                              │
│  3. Agency OS processes through NB01-NB02-NB03                                │
│  4. Agency OS sends suggested response to dashboard                           │
│  5. Agent (Priya) reviews and sends via WhatsApp                               │
│  OR                                                                          │
│  5b. Agency OS auto-sends via WhatsApp API (if agency enables)                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Point

**You DON'T provide WhatsApp service.**
You provide the **tools for agencies to connect THEIR WhatsApp.**

Each agency uses their own:
- Phone number
- WhatsApp Business account
- WATI/Twilio account (or manual)

You just build the integration layer.

---

## What This Changes for Pricing

### Your SaaS Pricing

| Plan | Price | Features | For Agency |
|------|-------|----------|-----------|
| **Starter** | ₹999/month | 1 agent, 50 customers, subdomain | Solo agents |
| **Professional** | ₹2,499/month | 3 agents, 200 customers, custom domain | Growing teams |
| **Agency** | ₹4,999/month | Unlimited, white-label, API access | Established agencies |

### Agency's Cost to Serve Their Customers

| Item | Agency Pays |
|------|-------------|
| Your platform fee | ₹999-4,999/month |
| WhatsApp Business App | Free |
| WATI (if they want automation) | ~$49/month |
| Custom domain | ~₹100/year (already have usually) |
| Total | ~₹1,500-5,500/month for a full customer management system |

---

## What This Changes for Audit Mode

### Audit Mode as Agency Lead Gen Tool

**Option A: You run Audit Mode**
- You acquire leads
- You distribute to agencies who pay for leads
- Or you use Audit Mode to sell Agency OS subscriptions

**Option B: Agencies embed Audit Mode on THEIR sites**
- Agency puts "Audit your booking" widget on their site
- Uses your tech white-label
- Leads go directly to agency
- You charge for the Audit Mode feature

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY'S WEBSITE (priyatravels.com)                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Widget embedded on agency's site]                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📋 Already booked somewhere? Audit your booking for FREE!                  ││
│  │                                                                           ││
│  │ [Upload your booking]                                                      ││
│  │                                                                           ││
│  │ Powered by Agency OS technology                                            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  Traveler uses Audit Mode → Results show "Priya Travels can fix this"        │
│  Lead goes to Priya Travels                                                    │
│  You charge Priya for Audit Mode feature                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Corrected UX Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOU (Platform)                                                                │
│  Build & Sell: Agency OS SaaS platform                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                    ↓ Subscription
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AGENCY (Your Customer) - e.g., Priya Travels                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Uses: Agency OS dashboard (white-label to them)                              │
│  Connects: Their WhatsApp, email, domain                                      │
│  Serves: Their end customers                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                    ↓ White-labeled experience
┌─────────────────────────────────────────────────────────────────────────────────┐
│  END CUSTOMER (Agency's Customer, NOT yours)                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Sees: Priya Travels branding                                                │
│  Visits: priyatravels.com (your tech powering it invisibly)                   │
│  Messages: +91-98765-43210 (agency's WhatsApp)                                │
│  NEVER sees: "Agency OS" branding                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Implications

### Multi-Tenancy Required

```python
# src/services/tenant_service.py

class Tenant(BaseModel):
    tenant_id: str
    agency_name: str
    plan: str  # "starter", "professional", "agency"
    branding: BrandingConfig
    domain: str | None  # Custom domain
    whatsapp_config: WhatsAppConfig | None
    team_members: List[TeamMember]

class BrandingConfig(BaseModel):
    logo_url: str
    primary_color: str
    secondary_color: str
    agency_name: str
    agency_email: str
    agency_phone: str
    agency_whatsapp: str

async def get_tenant_context(request: Request) -> Tenant:
    """
    Get tenant from request (subdomain or custom domain)
    """
    host = request.headers["host"]

    # Check if custom domain
    tenant = await db.fetch_one(
        "SELECT * FROM tenants WHERE custom_domain = $1",
        host
    )

    if not tenant:
        # Check if subdomain
        subdomain = host.split(".")[0]
        tenant = await db.fetch_one(
            "SELECT * FROM tenants WHERE subdomain = $1",
            subdomain
        )

    if not tenant:
        raise HTTPException(404, "Agency not found")

    return tenant

# Middleware to inject tenant context
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    tenant = await get_tenant_context(request)
    request.state.tenant = tenant
    response = await call_next(request)
    return response

# Now all endpoints have tenant context
@app.get("/api/portal/trip/{link_id}")
async def get_trip_portal(link_id: str, request: Request):
    tenant = request.state.tenant

    # Get trip data with tenant's branding
    trip_data = await get_trip_data(link_id, tenant.tenant_id)

    return {
        "trip": trip_data,
        "branding": tenant.branding,
        "agency": {
            "name": tenant.agency_name,
            "phone": tenant.agency_phone,
            "email": tenant.agency_email
        }
    }
```

### Tenant Isolation

```python
# All data must be isolated by tenant_id

# Customer portal URL
# priyatravels.agency-os.com/trip/abc123
# ^^^^^^^^^^^^^^^ subdomain identifies tenant

# Database query
async def get_customer_packets(tenant_id: str, customer_phone: str):
    return await db.fetch_all(
        """SELECT * FROM packets
           WHERE tenant_id = $1
           AND customer_phone = $2""",
        tenant_id,  # Isolation!
        customer_phone
    )

# WhatsApp webhook
# Agency's WATI account sends webhook to your platform
@app.post("/webhooks/whatsapp/{tenant_id}")
async def whatsapp_webhook(tenant_id: str, payload: dict):
    # Validate webhook belongs to tenant
    tenant = await get_tenant(tenant_id)

    # Verify webhook signature
    if not verify_webhook(payload, tenant.whatsapp_config.webhook_secret):
        raise HTTPException(401, "Invalid webhook")

    # Process message
    message = payload["message"]
    customer_phone = payload["from"]

    # NB01-NB02-NB03 processing with tenant context
    result = await process_inquiry(
        tenant_id=tenant_id,
        message=message,
        customer_phone=customer_phone
    )

    # Send response via tenant's WhatsApp
    await send_whatsapp(
        tenant_config=tenant.whatsapp_config,
        to=customer_phone,
        message=result.suggested_message
    )
```

---

## Summary: The Corrected Model

### You Are Building

| Layer | What | Who Pays | Who Sees |
|-------|------|----------|---------|
| **Agency OS** | B2B SaaS platform | Agencies (subscription) | Agencies (dashboard) |
| **White-label Portal** | Customer-facing tech | Agencies (included) | Agency's customers (branded to agency) |
| **Audit Mode** | Lead gen tool | Agencies (feature) or You (lead gen) | End travelers |

### Key Corrections from Previous Docs

| Previous (Wrong) | Corrected |
|------------------|-----------|
| Traveler sees "Agency OS" portal | Traveler sees agency's branded portal |
| You provide WhatsApp service | Agency connects THEIR WhatsApp |
| You send messages to travelers | Agency sends messages (your tech assists) |
| Single-tenant (one agency) | Multi-tenant (hundreds of agencies) |
| You run travel agency | You build tools FOR travel agencies |

---

## Related Documentation Needs Updates

The following documents need to be updated to reflect the multi-tenant white-label model:

- ~~`UX_AND_USER_EXPERIENCE.md`~~ - Needs rewrite for B2B SaaS
- ~~`UX_DASHBOARDS_BY_PERSONA.md`~~ - Still valid (agency personas use YOUR dashboard)
- ~~`UX_MESSAGE_TEMPLATES_AND_FLOWS.md`~~ - Still valid (agencies send these, not you)
- ~~`UX_TECHNICAL_ARCHITECTURE.md`~~ - Needs multi-tenant architecture added
- ~~`UX_MULTI_CHANNEL_STRATEGY.md`~~ - Needs rewrite (agency connects channels, not you)

---

*This is a fundamental correction to the entire product model. Acknowledged and documented.*
