# API Documentation — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, maybe someday hire developer  
**Approach:** Independent analysis — minimum viable docs, not enterprise  

---

## 1. The Core Truth: Future You Will Forget+

### Your Reality (Solo Dev Today)

| Question | Answer for You Today | If You Hire Developer |
|----------|----------------------|--------------------------|
| **API docs?** | ❌ NO (you know it) | ✅ YES (they don't) |
| **Swagger?** | ❌ NO (waste of time) | ✅ MAYBE (FastAPI auto-generates) |
| **README?** | ✅ YES (setup instructions) | ✅ YES (onboarding) |
| **Architecture diagram?** | 🟡 MAYBE (for you) | ✅ YES (they need overview) |

**My insight:**   
Write API docs **NOW** (while it's fresh in your head).  
6 months from now → you'll forget WHY you built X endpoint.

---

## 2. My API Documentation Model (Lean, Auto-Generated))

### What You Actually Need (Simple))

```markdown
# API.md (in repo root)

## Overview
- Base URL: `https://your-agency.up.railway.app`
- Auth: Bearer token (JWT)
- Content-Type: `application/json`

## Enquiries
### POST /api/enquiries
Creates new enquiry (triggers AI analysis).

**Request:**
```json
{
  "raw_text": "Bali honeymoon June 15-20, family of 4, budget ₹1.2L",
  "channel": "whatsapp",
  "acquisition_source": "inbound_organic"
}
```

**Response:**
```json
{
  "enquiry_id": "eq-2026-0042",
  "status": "TRIAGED",
  "customer_id": "cust-042",
  "ai_summary": "Bali honeymoon, June 15-20, family of 4..."
}
```

### GET /api/enquiries/`{id}`
Returns enquiry details + AI analysis.

**Response:**
```json
{
  "enquiry_id": "eq-2026-0042",
  "status": "DRAFTING",
  "customer": { "name": "Ravi Kumar", "segment": "VIP" },
  "ai_draft": "Hi Ravi! 👋 Your Bali itinerary is ready..."
}
```

---

### Bookings
### POST /api/bookings
Creates booking from confirmed enquiry.

**Request:**
```json
{
  "enquiry_id": "eq-2026-0042",
  "customer_id": "cust-042",
  "start_date": "2026-06-15",
  "end_date": "2026-06-20"
}
```

**Response:**
```json
{
  "booking_id": "bk-001",
  "status": "CONFIRMED",
  "total_value": 120000,
  "currency": "INR"
}
```

---

### Communications
### POST /api/communications
Sends message via WhatsApp/email.

**Request:**
```json
{
  "enquiry_id": "eq-2026-0042",
  "channel": "WHATSAPP",
  "body_text": "Hi Ravi! Your Bali itinerary is ready..."
}
```

**Response:**
```json
{
  "comm_id": "comm-123",
  "sent_at": "2026-04-29T14:30:00Z",
  "status": "SENT"
}
```

---

## 3. Swagger/OpenAPI (Auto-Generated, Zero Work))

### Why This is FREE (FastAPI Built-in))

```python
# spine_api/server.py (already has this!)
from fastapi import FastAPI

app = FastAPI(
    title="Travel Agency API",
    description="AI-assisted travel agency system",
    version="1.0.0"
)

@app.post("/run", response_model=SpineRunResponse)
async def run_spine(payload: RunRequest):
    """Run AI analysis on enquiry.
    
    Args:
        payload: Raw enquiry text + context
        
    Returns:
        AI analysis with decision state
    """
    # ... implementation
```

**My insight:**   
FastAPI auto-generates Swagger at `/docs` — ZERO extra work.  
Visit: `https://your-agency.up.railway.app/docs` → full interactive API docs.

---

### What You Get (Automatic))

```
Visit /docs → See:
- POST /api/enquiries (with "Try it out" button)
- GET /api/bookings/{id} (test with real ID)
- POST /api/whatsapp/send (see required fields)
- Authentication requirements (Bearer token)
- Response schemas (auto from Pydantic models)
```

**My insight:**   
`/docs` = **interactive tester**.  
New dev can test API in 5 minutes (no reading needed).

---

## 4. README.md (Critical, Write Now))

### What to Include (1 Page Max))

```markdown
# Travel Agency OS

## Quick Start
1. Clone: `git clone https://github.com/you/travel-agency.git`
2. Install: `cd spine_api && uv pip install -r requirements.txt`
3. Setup: Copy `.env.example` → `.env` (fill keys)
4. Run backend: `uv run uvicorn spine_api.server:app --port 8000`
5. Run frontend: `cd frontend && npm run dev`
6. Open: `http://localhost:3000`

## Environment Variables (.env)
- `SPINE_API_PORT=8000`
- `DATABASE_URL=postgresql://user:pass@localhost/travel_agency`
- `WHATSAPP_API_KEY=...` (from Meta Business)
- `S3_BUCKET=my-agency-backups`
- `ENCRYPTION_KEY=...` (32-char random)

## Architecture
- Frontend: Next.js → Vercel (https://yourname-travels.com)
- Backend: FastAPI → Railway (https://your-agency.up.railway.app)
- DB: PostgreSQL (included in Railway)
- Backups: S3 (offsite)

## API Docs
- Swagger: https://your-agency.up.railway.app/docs
- Health: https://your-agency.up.railway.app/health

## First Login
1. Go to http://localhost:3000
2. Login with: [your creds]
3. Bookmark: /enquiries (your daily view)

## Common Tasks
- New enquiry: WhatsApp scan QR → auto-creates
- Reply: Open enquiry → "Draft Reply" → send
- Payment: Customer says "Paid" → mark as paid

## Troubleshooting
- DB connection error: Check `DATABASE_URL` in `.env`
- WhatsApp not working: Check `WHATSAPP_API_KEY` + webhook
- Slow queries: Run `EXPLAIN ANALYZE` on slow query

## Support
- WhatsApp: +91 98765 43210
- Email: hello@yourname-travels.com
```

**My insight:**   
1-page README = **new dev can start in 30 minutes**.  
Include **troubleshooting** — they'll hit these issues.

---

## 5. Architecture Diagram (Mermaid, 5 Minutes))

### What to Draw (Simple))

```mermaid
graph TD
    A[Frontend Next.js] -->|HTTP| B(BFF Layer)
    B -->|FastAPI| C[Spine API]
    C -->|DB| D[(PostgreSQL)]
    C -->|S3| E[Backups]
    A -->|WhatsApp| F[Meta API]
    B -->|Calendar| G[Google Calendar]
    
    style A fill:#e1f5fe
    style C fill:#fce4ec
    style D fill:#d4edda
```

**My insight:**   
Mermaid = **text-based**, lives in repo.  
Update when you change architecture (1 minute).

---

## 6. Postman Collection (Maybe Later))

### When You Need It (Testing API))

| Need | Tool | Why |
|------|------|-----|
| **Test API** | Swagger `/docs` | Built-in, interactive |
| **Share with dev** | Postman Collection | They can import |
| **Automated tests** | Swagger JSON | Export → use in CI |

**My recommendation:**   
Skip Postman for now — **Swagger `/docs` is enough**.  
Export Swagger JSON later: `https://your-agency.up.railway.app/openapi.json`.

---

## 7. Current State vs Documentation Model+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| README | Minimal | 1-page quick start + troubleshooting |
| Swagger/OpenAPI | Built-in (`/docs`) | ✅ YES — zero work |
| Architecture diagram | None | Mermaid (5 mins, in repo) |
| Postman collection | None | ❌ SKIP — Swagger enough |
| Code comments | Some | Add docstrings to NEW code only |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Write README now? | Yes / No | **YES** — while fresh in head |
| Swagger? | Now / Later | **NOW** — built-in, zero work |
| Architecture diagram? | Mermaid / None | **Mermaid** — 5 mins, in repo |
| Postman? | Yes / No | **NO** — Swagger enough |
| Docstrings? | All / New code only | **New code only** — don't rewrite |

---

## 9. Final Discussion Complete!+

**We've now covered ALL areas from first principles:**

1. ✅ Enquiry types & stages
2. ✅ Channels, acquisition (updated with inputs)
3. ✅ Customer model
4. ✅ Human agent model (SKIP for solo dev)
5. ✅ Vendor model
6. ✅ Communication model
7. ✅ Booking model
8. ✅ System architecture
9. ✅ Payments (status-only, no collection)
10. ✅ Notifications & alerts (WhatsApp-primary)
11. ✅ Roles & Permissions (SKIP for solo dev)
12. ✅ Search & Discovery (PostgreSQL FTS)
13. ✅ Reporting & Analytics (3 reports)
14. ✅ Audit & Compliance (GDPR, DPDPA)
15. ✅ Testing Strategy (unit + integration)
16. ✅ Mobile & PWA (WhatsApp Business API)
17. ✅ Backup & Security (3 layers, S3)
18. ✅ Integrations (WhatsApp, Google Calendar)
19. ✅ Onboarding (docs for future hire)
20. ✅ Performance & Scaling (PostgreSQL indexes)
21. ✅ Localization & Offline (Hindi, Mandarin)
22. ✅ Domain & Hosting & Legal (Domain, Vercel/Railway)
23. ✅ Marketing & SEO (Google My Business, referrals)
24. ✅ Monitoring & Alerting (UptimeRobot, Sentry)
25. ✅ Business Continuity (emergency contacts)
26. ✅ Third-Party Risks (WhatsApp ban, etc.)
27. ✅ API Documentation (Swagger `/docs`, README)

---

## 10. Next Step: FINAL Implementation Roadmap+

Now that ALL discussions are complete, we build:  
**`Docs/discussions/implementation_roadmap_2026-04-29.md`**

This is the **LIVING document** (update as we implement).

---

**Next file:** `Docs/discussions/implementation_roadmap_2026-04-29.md`
