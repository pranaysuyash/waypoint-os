# Technical Infrastructure

**Date**: 2026-04-14
**Purpose**: What tech stack, hosting, and architecture for a solo builder

---

## Solo Builder Principles

1. **Boring is better** — Use proven tech, not bleeding edge
2. **Managed > self-hosted** — Your time > cost savings
3. **Simple > flexible** — You can change it later
4. **Fast to iterate > perfect architecture** — Ship fast

---

## Recommended Stack

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  THE STACK                                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Frontend:   HTMX or simple React (you don't need SPA complexity)               │
│  Backend:    Python + FastAPI (you already use Python)                          │
│  Database:   Postgres (boring, reliable, everything works with it)              │
│  Auth:       Clerk or Auth0 (managed, don't build auth yourself)                │
│  Hosting:    Render or Railway (one-click deploy, scales later)                 │
│  Queue:      PostgreSQL SKIP LOCKED or simple background jobs                    │
│  Storage:    Render disk or Cloudflare R2                                       │
│  Monitoring: Sentry for errors, basic logs for everything else                  │
│  Analytics:  PostHog or just database queries                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Why This Stack?

| Component | Choice | Why |
|-----------|--------|-----|
| **Frontend** | HTMX or React | You already know Python; HTMX keeps you in Python. React if you need rich UI. |
| **Backend** | FastAPI | Fast, modern, type-safe, async if needed |
| **Database** | Postgres | Works for everything, reliable, great ecosystem |
| **Auth** | Clerk | Drop-in, handles OAuth/magic links, free tier is generous |
| **Hosting** | Render | Simple, free tier, scales to thousands of users, auto-SSL |

---

## Hosting Options Compared

| Provider | Pros | Cons | Cost (monthly) |
|----------|------|------|----------------|
| **Render** | One-click, auto-SSL, easy scaling | No persistent storage on free | Free → $25+ |
| **Railway** | Great DX, built-in Postgres | Can get expensive quickly | Free → $20+ |
| **Fly.io** | Multi-region, fast | More complex setup | Free → $10+ |
| **AWS/GCP** | Powerful, everything | Too complex for solo | $50+ to start |

**Recommendation**: Render for simplicity. Railway if you want better DX.

---

## Architecture (Keep It Simple)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SINGLE-TENANT MVP ARCHITECTURE                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐             │
│  │   Browser      │ ──▶ │   FastAPI      │ ──▶ │   Postgres     │             │
│  │   (HTMX/React) │     │   (Python)     │     │   (Database)   │             │
│  └────────────────┘     └────────────────┘     └────────────────┘             │
│                                │                                                 │
│                                ▼                                                 │
│                         ┌────────────────┐                                     │
│                         │   OpenAI API   │                                     │
│                         │   (Anthropic)  │                                     │
│                         └────────────────┘                                     │
│                                                                                  │
│  Background jobs: Same server, separate process                                 │
│  Storage: Render disk or Cloudflare R2                                         │
│  Auth: Clerk (managed service)                                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**No microservices. No message queue (yet). No CDN (yet).**

---

## Single vs. Multi-Tenant (For Now)

### Single-Tenant (MVP)

One agency, one workspace, simple:

```python
# Everything is scoped to one agency
# No tenant_id filtering needed
# Simpler code, faster to build
```

**When to move to multi-tenant**: When you have 3+ paying agencies.

### Multi-Tenant (Later)

```python
# Add tenant_id to all queries
# Row-level security in Postgres
# Agency isolation in UI
```

---

## Key Decisions to Make Now

### 1. ORM or Raw SQL?

| Option | Pros | Cons |
|--------|------|------|
| **SQLAlchemy** | Powerful, established | Verbose, learning curve |
| **Piccolo** | Modern, async-friendly | Less mature |
| **Raw SQL** | Full control, simple | More boilerplate |

**Recommendation**: SQLAlchemy 2.0 with async support, or just raw SQL for simple queries.

---

### 2. Async or Not?

```python
# Async (recommended)
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}
```

**Why async**: You'll be calling external APIs (OpenAI). Async = concurrent requests.

---

### 3. How to Handle Background Jobs?

| Option | When to use |
|--------|-------------|
| **FastAPI BackgroundTasks** | Simple fire-and-forget |
| **Celery** | Too complex for MVP |
| **Postgres SKIP LOCKED** | Simple job queue built into DB |
| **APScheduler** | In-process scheduled tasks |

**Recommendation**: FastAPI BackgroundTasks + Postgres job table with SKIP LOCKED for reliable queue.

---

### 4. How to Store LLM Chats?

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    agency_id UUID NOT NULL,
    trip_id UUID,
    role TEXT NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tokens INTEGER,
    cost DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Why**: Full chat history for debugging, cost tracking, and learning.

---

## Cost Projections (Monthly)

| Service | Free tier | Paid (when you exceed) |
|---------|-----------|------------------------|
| **Render** | ~750 hours/month | $25+ |
| **Postgres on Render** | 90 days, then $7 | $7-20 |
| **Clerk Auth** | 5,000 MAU free | $25+ |
| **OpenAI API** | — | Usage-based (expect $20-100 initially) |
| **Sentry** | 5K errors/month | $26+ |
| **Cloudflare R2** | 10GB free | $0.015/GB |

**Expected burn**: $0-50/month for pilot phase, $100-300/month at 50 customers.

---

## Security Basics (Do These)

1. **Environment variables** for secrets (never commit .env)
2. **HTTPS only** (Render auto-SSL)
3. **Input validation** (Pydantic models)
4. **SQL injection protection** (ORM or parameterized queries)
5. **Rate limiting** (slow attacks, prevent abuse)
6. **CORS** (restrict to your domains)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Monitoring (What You Actually Need)

| Tool | Purpose |
|------|---------|
| **Sentry** | Error tracking (must have) |
| **Render logs** | Basic request logging |
| **Simple health check** | /ping endpoint |
| **Uptime robot** | Alerts when site is down |

```
GET /ping → 200 OK
GET /health → {status: "ok", db: "connected", llm: "ready"}
```

---

## Data Backup Strategy

| Data | Backup strategy |
|------|-----------------|
| **Postgres** | Render automated backups + daily export to S3/R2 |
| **User uploads** | Direct to R2/S3, no backup needed |
| **Code** | Git (already backed up) |

---

## When to Scale Up

| Trigger | Action |
|---------|--------|
| > 100 concurrent requests | Add Redis caching |
| Database slowing down | Add connection pooling, then read replica |
| Slow LLM responses | Async queue + background workers |
| Expensive hosting | Move to AWS/GCP for reserved instances |

**Don't optimize prematurely.** Render scales fine to thousands of users.

---

## Tech Debt You'll Accumulate (It's Okay)

| Debt | When to fix |
|------|-------------|
| No tests (at first) | Add tests before each major feature |
| Hardcoded config | Extract to env when you deploy to second environment |
| Monolithic repo | Split when you have distinct services |
| No CI/CD | Add GitHub Actions when deploying to production |

---

## Quick Start Checklist

- [ ] Create Render account
- [ ] Create Postgres database on Render
- [ ] Create Clerk account for auth
- [ ] Create Sentry account for error tracking
- [ ] Create basic FastAPI app with health check
- [ ] Deploy to Render
- [ ] Set up environment variables
- [ ] Test /ping endpoint
- [ ] Done — start building features

---

## Summary

**Stack**: Python/FastAPI + Postgres + HTMX + Clerk + Render

**Architecture**: Simple monolith, no microservices

**Cost**: $0-50/month for pilots

**Philosophy**: Boring tech, managed services, ship fast

**You can always refactor later. First priority: something that works.**
