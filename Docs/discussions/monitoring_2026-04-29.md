# Monitoring & Alerting — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, system down = no business  
**Approach:** Independent analysis — minimum viable monitoring, not enterprise  

---

## 1. The Core Truth: If System is Down, You Lose Money+

### Your Reality (Solo Dev)

| What Happens | Impact | Cost if Ignored |
|--------------|--------|------------------|
| **Website down** | No new enquiries via form | ₹5000+ lost/day |
| **WhatsApp API down** | Can't receive messages | ₹10000+ lost/day |
| **Backend API down** | Can't send drafts | ₹3000+ lost/day |
| **DB corrupts** | Lose all data | BUSINESS OVER |

**My insight:**  
As solo dev, monitoring = **insurance policy**.  
UptimeRobot FREE tier = ₹0/month, saves ₹5000+ if down.

---

## 2. My Monitoring Model (Zero-Cost, Effective)

### What to Monitor (Critical Only)+

| Service | Why Monitor | Tool (FREE) |
|---------|--------------|-------------|
| **Frontend (Vercel)** | Customer can't access site | UptimeRobot (50 monitors FREE) |
| **Backend (Railway)** | API + spine_api down | Railway built-in alerts |
| **WhatsApp API** | Can't receive messages | Meta API health check |
| **PostgreSQL** | Data unreadable | Railway built-in |
| **S3 backup** | Backups failing | AWS CloudWatch (FREE tier) |

**My recommendation:**  
**UptimeRobot FREE** (50 monitors) + **Railway built-in** = enough.  
Don't buy Datadog/New Relic — ₹10000/month = overkill.

---

### UptimeRobot Setup (5 Minutes, FREE)+

```bash
# 1. Sign up: https://uptimerobot.com (FREE)
# 2. Add monitors:

## Monitor 1: Frontend
URL: https://yourname-travels.vercel.app
Friendly Name: "Travels Frontend"
Alert Contacts: Your WhatsApp (+91 98765 43210)
Alert When: Down for 5 minutes

## Monitor 2: Backend API
URL: https://your-agency.up.railway.app/health
Friendly Name: "Travels Backend API"
Alert Contacts: Your WhatsApp
Alert When: Down for 5 minutes

## Monitor 3: WhatsApp API
URL: https://your-agency.up.railway.app/api/whatsapp/health
Friendly Name: "WhatsApp API"
Alert Contacts: Your WhatsApp
Alert When: Down for 2 minutes
```

**My insight:**  
`/health` endpoint = simple `{"status": "ok"}` check.  
Alerts to **WhatsApp** — you're always there.

---

### Health Check Endpoints (Backend)+

```python
# spine_api/health.py (or /api/health)
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    # 1. Check DB
    try:
        db.execute("SELECT 1")
        db_status = "ok"
    except:
        db_status = "error"
    
    # 2. Check WhatsApp API (Meta)
    wa_status = "ok"
    try:
        meta_api.get_business_profile()  # Light call
    except:
        wa_status = "error"
    
    # 3. Check S3 backup (last backup <48h?)
    last_backup = db.get_last_backup_time()
    backup_status = "ok" if (datetime.now() - last_backup).hours < 48 else "stale"
    
    overall = "ok" if all(s == "ok" for s in [db_status, wa_status, backup_status]) else "error"
    
    return {
        "status": overall,
        "checks": {
            "database": db_status,
            "whatsapp_api": wa_status,
            "backups": backup_status
        },
        "timestamp": datetime.now().isoformat()
    }
```

**My insight:**  
`last_backup` check = auto-detect if S3 upload failed.  
48h stale = alert YOU (backups should be daily).

---

## 3. Error Tracking (Sentry FREE Tier)+

### Why You Need It (Debug Remote)+

| Without Sentry | With Sentry |
|---------------|----------------|
| ❌ No idea WHY it crashed | ✅ Stack trace + line number |
| ❌ No idea WHICH customer | ✅ User ID + enquiry ID |
| ❌ No idea HOW many affected | ✅ Count: 5 errors in 1 hour |

### Setup (5 Minutes, FREE)+

```python
# spine_api/main.py (FastAPI)
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://xxx@o450xxx.ingest.us.sentry.io/xxxxx",  # FREE: 5k errors/month
    integrations=[FastApiIntegration()],
    environment="production",
    release="travel-agency@1.0.0"
)

# Frontend (Next.js)
# sentry.next.config.js
module.exports = {
  dsn: "https://xxx@o450xxx.ingest.us.sentry.io/xxxxx",
  maxBreadth: 5,  # FREE: 5k events/month
};
```

**My insight:**  
FREE tier = **5k errors/month**. You'll use <100.  
Sentry = **remote debugger** (you're solo, no QA team).

---

## 4. Performance Monitoring (Simple)+

### What to Track (Solo Dev)+

| Metric | Tool | Why |
|--------|------|-----|
| **Frontend load time** | Vercel Analytics (FREE) | Page >3s = customer leaves |
| **API response time** | Railway Metrics (built-in) | API >2s = YOU feel slow |
| **DB query time** | Railway Metrics | Query >1s = add index |

**My insight:**  
Vercel Analytics = **built-in**, zero setup.  
Railway Metrics = **built-in**, shows CPU/RAM/Disk.

---

### Custom Performance Logger (Simple)+

```python
# utils/perf_logger.py
import time
from functools import wraps

def log_slow_query(threshold_s: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed = time.time() - start
            if elapsed > threshold_s:
                print(f"SLOW: {func.__name__} took {elapsed:.2f}s")
                # Log to Sentry if very slow
                if elapsed > 5.0:
                    sentry_sdk.capture_message(f"SLOW QUERY: {func.__name__} = {elapsed:.2f}s")
            return result
        return wrapper
    return decorator

# Usage:
@log_slow_query(threshold_s=2.0)
async def search_enquiries(db, query: str):
    return db.search(query)  # Logged if >2s
```

**My insight:**  
SLOW query log = YOU know when to add index.  
Threshold 2s = reasonable for solo dev.

---

## 5. WhatsApp API Monitoring (Critical)+

### Why This is #1 Priority+

| Failure Mode | Impact | Detection |
|--------------|--------|-----------|
| **Meta bans you** | Business DEAD | `403 Forbidden` on API call |
| **Webhook fails** | Messages not received | `500 Error` on webhook |
| **Rate limited** | Can't send replies | `429 Too Many Requests` |

### Health Check (Meta API)+

```python
# /api/whatsapp/health (called by UptimeRobot)
@app.get("/api/whatsapp/health")
async def whatsapp_health():
    try:
        # Light call: get business profile
        profile = meta_api.get_business_profile()
        return {
            "status": "ok",
            "phone_number": profile['display_phone_number'],
            "verified_name": profile['verified_name']
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}, 500
```

**My insight:**  
If `verified_name` fails = **API key expired/revoked**.  
UptimeRobot alerts YOU → fix in 5 minutes.

---

## 6. Current State vs Monitoring Model+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Uptime monitoring | None | UptimeRobot FREE (50 monitors) |
| Error tracking | None | Sentry FREE (5k events/month) |
| Performance | None | Railway + Vercel built-in |
| Health endpoints | None | `/api/health` + `/api/whatsapp/health` |
| Backup monitoring | None | Check last_backup <48h |
| Alert channel | None | WhatsApp (YOU are there) |

---

## 7. Decisions Needed (Solo Dev Reality)+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| UptimeRobot? | Yes / No | **YES** — FREE, 5-min setup |
| Sentry? | Yes / Later | **YES** — FREE, debug remote |
| Custom metrics? | Grafana / Simple logs | **Simple logs** — print to Railway |
| Health endpoints? | Now / Later | **NOW** — UptimeRobot needs URL |
| Alert channel? | Email / WhatsApp | **WhatsApp** — you're always there |
| Performance alerts? | Yes / No | **NO** — check weekly manually |

---

## 8. Next Discussion: Business Continuity+

Now that we know **if system is down**, we need to discuss: **What if YOU are down?**

Key questions for next discussion:
1. **Hit by bus scenario** — who takes over? (family/friend?)
2. **WhatsApp banned** — what's the backup channel? (Telegram?)
3. **Meta bans API** — what's the workaround? (new number?)
4. **Solo dev reality** — what's the MINIMUM contingency plan?

---

**Next file:** `Docs/discussions/business_continuity_2026-04-29.md`
