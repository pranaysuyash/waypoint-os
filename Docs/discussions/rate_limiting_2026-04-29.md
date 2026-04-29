# Rate Limiting — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, protect APIs+  
**Approach:** Independent analysis — minimum viable rate limiting, not enterprise  

---

## 1. The Core Truth: You're Small, But Need Basic Protection+

### Your Reality (Solo Dev))

| Threat | Probability | Impact |
|---------|-------------|--------|
| **Customer clicks 100x** | HIGH (accidental) | 🟡 LOW (slow for them) |
| **Bot attacks API** | LOW | 🔴 HIGH (crash DB) |
| **WhatsApp API limit** | MEDIUM (1000/day) | 🔴 CRITICAL (banned) |
| **Competitor scrapes** | LOW | 🟡 LOW (SEO data) |

**My insight:**   
As solo dev, **slow down = lost customer**.   
Rate limit = **insurance policy** (5 mins setup).

---

## 2. My Rate Limiting Model (Lean, Practical))+

### What You Actually Need (Simple))+

| API | Limit | Why |
|-----|-------|-----|
| **POST /api/enquiries** | 10/min/IP | Accidental double-click |
| **POST /api/whatsapp/send** | 1/sec | Meta limit (20/sec burst) |
| **GET /api/enquiries** | 60/min/IP | Normal browsing |
| **POST /api/bookings** | 5/min/IP | Rarely created |
| **ALL APIs** | 100/min/IP | Global safety net |

**My recommendation:**   
**Token bucket** (not fixed window). Allows bursts.   
`1/sec` for WhatsApp = safe margin (Meta = 20/sec).

---

### FastAPI (slowapi — 5 Mins, Zero De)

```python+
# spine_api/middleware/rate_limit.py+
from slowapi import Limiter+
from slowapi.storage import MemoryStorage+
from fastapi import Request+

limiter = Limiter(
    key_func=lambda: request.client.host,  # By IP+
    storage=MemoryStorage(),  # Solo dev = memory (no Redis)
    default_limits=["100 per day", "10 per minute"]
)

# Apply globally+
app = FastAPI()
app.state.limiter = limiter+

# Per-endpoint+
@app.post("/api/enquiries", dependencies=[Depends(limiter.limit("10/minute"))])
async def create_enquiry(payload: EnquiryCreate):
    # ...
    pass

@app.post("/api/whatsapp/send", dependencies=[Depends(limiter.limit("1/second"))])
async def send_whatsapp_message(payload: WhatsAppSend):
    # ...
    pass

@app.get("/api/enquiries", dependencies=[Depends(limiter.limit("60/minute"))])
async def get_enquiries():
    # ...
    pass
```

**My insight:**   
`slowapi` = 5 mins, built for FastAPI.   
`MemoryStorage()` = zero infra (solo dev). 

---

### WhatsApp API (Meta's Limit — Already Exists))+

| Meta Limit | Your Action |
|-------------|--------------|
| **1000 msgs/day** | Count via DB (not slowapi) |
| **20/sec burst** | `asyncio.sleep(0.1)` in queue |
| **Per-phone limit** | Meta enforces (you don't need to) |

```python+
# utils/whatsapp_queue.py+
import asyncio+

message_queue = asyncio.Queue()

async def send_whatsapp_with_retry(to: str, text: str, max_retries: int = 3):
    """Send with rate limit (1/sec safe)."""
    for attempt in range(max_retries):
        try:
            # 1. Check daily limit (1000/day)
            today_count = db.count_whatsapp_msgs_today()
            if today_count >= 950:  # 50 buffer
                raise Exception("Daily limit near")
            
            # 2. Rate limit: 1/sec+
            await asyncio.sleep(1)
            
            # 3. Send+
            response = await meta_api.send_message(to, text)
            return response
            
        except RateLimitError:
            await asyncio.sleep(60)  # Wait 1 min+
    
    raise Exception("WhatsApp rate limit exceeded after retries")
```

**My insight:**   
`today_count >= 950` = 50 msg buffer (Meta says 1000).   
`asyncio.sleep(1)` = zero cost rate limiting. 

---

## 3. Next.js (Frontend — Optional, Later))+

### Why You Might Need It (Low Priority))+

| Issue | Without Rate Limit | With Rate Limit |
|-------|-------------------|-------------------|
| **Customer clicks 10x** | ❌ 10 enquiries created | ✅ Only 1 created |
| **Tab open 24h** | ❌ 1000 API calls | ✅ ~60/min max |

### Middleware (Later, 5 Mins))+

```typescript+
// middleware.ts (Next.js)+
import { NextResponse } from "next/server";
import rateLimit from "express-rate-limit";  # Use via adapter+

// Later: when you have 100+ customers+
// const limiter = rateLimit({
//   windowMs: 60 * 1000,  // 1 minute+
//   max: 60  // 60 requests per minute+
// });

export function middleware(request: Request) {
  // Skip for now (solo dev = 1 user)+
  return NextResponse.next();
}
```

**My insight:**   
Frontend rate limit = **NOT needed** (you're the only user).   
Add when you have 10+ customers. 

---

## 4. Per-User vs Per-IP (What's Better?))+

### Comparison (Solo Dev))+

| Method | Pros | Cons |
|--------|------|------|
| **Per-IP** | ✅ Simple (slowapi default) | ❌ Same IP = same office |
| **Per-User (JWT)** | ✅ Accurate (your JWT) | ❌ Needs JWT decode |

**My recommendation:**   
**Per-IP** for now (solo dev = 1 IP mostly).   
Per-User = when you have 10+ customers. 

---

### Per-User (Later, 5 Mins))+

```python+
# spine_api/middleware/rate_limit.py+
from fastapi import Request, Depends+
from slowapi import Limiter+

def get_client_id(request: Request):
    """Get user ID from JWT (not IP)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return request.client.host  # Fallback to IP+
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload.get("sub", request.client.host)
    except:
        return request.client.host

limiter = Limiter(
    key_func=get_client_id,  # User ID or IP+
    storage=MemoryStorage()
)
```

**My insight:**   
`get_client_id()` = YOUR user ID (you're the only agent).   
Fallback to IP = safety net. 

---

## 5. Redis (Later, Not Now))+

### When You Need Redis (10+ Customers))+

| Storage | Now | Later (10+ customers) |
|---------|-----|--------------------------|
| **MemoryStorage** | ✅ YES (fast, zero cost) | ❌ NO (server restart = reset) |
| **Redis** | ❌ NO (overkill) | ✅ YES (persistent across restarts) |

### Redis Setup (Later, 10 Mins))+

```python+
# Later: when you have 10+ customers+
from slowapi.storage import RedisStorage+

limiter = Limiter(
    key_func=lambda: request.client.host,
    storage=RedisStorage(host="localhost", port=6379)  # Railway Redis add-on+
)
```

**My insight:**   
Redis = **$5/month** (Railway add-on).   
Not needed for 1 user (you). 

---

## 6. Headers (What User Sees))+

### What to Return (Transparent))+

```python+
# Automatic with slowapi+
@app.post("/api/enquiries")
@limiter.limit("10/minute")
async def create_enquiry(request: Request):
    # If rate limited, slowapi returns:+
    # HTTP 429+
    # Headers:+
    #   X-RateLimit-Limit: 10+
    #   X-RateLimit-Remaining: 3+
    #   Retry-After: 30+
    pass
```

**My insight:**   
`X-RateLimit-Remaining: 3` = frontend can show "3 tries left".   
`Retry-After: 30` = browser waits 30s. 

---

### Frontend Handling (Graceful))+

```typescript+
// utils/api-client.ts+
export async function apiCall(endpoint: string, options?: RequestInit) {
  const res = await fetch(endpoint, options);
  
  if (res.status === 429) {
    const retryAfter = res.headers.get("Retry-After");
    const seconds = parseInt(retryAfter || "30");
    
    showWarning(`Too many requests! Wait ${seconds}s...`);
    
    // Auto-retry after wait+
    await new Promise(resolve => setTimeout(resolve, seconds * 1000));
    return apiCall(endpoint, options);  // Retry+
  }
  
  return res;+
}
```

**My insight:**   
`Retry-After` = frontend auto-waits.   
Show warning = user knows WHY. 

---

## 7. Current State vs Rate Limit Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Backend rate limit | None | `slowapi` (5 mins, MemoryStorage) |
| Per-IP vs Per-User | None | Per-IP (you're the only user) |
| WhatsApp limit | Meta enforces | `today_count >= 950` + `sleep(1)` |
| Frontend rate limit | None | ❌ SKIP (1 user) |
| Redis | None | ❌ LATER (10+ customers) |
| Headers | None | `X-RateLimit-*` (automatic) |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| slowapi? | Now / Later | **NOW** — 5 mins, zero cost |
| Per-IP or Per-User? | IP / User | **IP** — you're solo |
| WhatsApp limit? | Now / Later | **NOW** — Meta will ban |
| Frontend limit? | Now / No | **NO** — 1 user only |
| Redis? | Now / Later | **LATER** — 1 user = memory enough |

---

## 9. Next Discussion: Feature Flags & Toggles)+

Now that we know **HOW to protect APIs**, we need to discuss: **How to turn features on/off without deploy?**

Key questions for next discussion:
1. **Feature flags** — enable AI drafting for VIP only? (test new features)
2. **Kill switch** — turn off WhatsApp if API down? (emergency)
3. **A/B testing** — show 2 draft versions? (later)
4. **Config file** — `.feature_flags.json` vs env vars?
5. **Solo dev reality** — will you EVER need this? (maybe not)

---

**Next file:** `Docs/discussions/feature_flags_2026-04-29.md`
