# Performance & Scaling — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, PostgreSQL, WhatsApp-primary+  
**Approach:** Independent analysis — don't optimize prematurelye, but know limits  

---

## 1. The Core Truth: You're Small, But Plan for 10x+

### Your Current Reality (Solo Dev)

| Metric | Today | 1 Year (Plan) |
|---------|--------|--------------|
| **Enquiries/month** | ~20 | ~200 |
| **Bookings/month** | ~10 | ~100 |
| **Customers** | ~50 | ~500 |
| **DB size** | ~100MB | ~1GB |
| **WhatsApp msgs/day** | ~30 | ~300 |

**My insight:**   
Premature optimization = waste of YOUR time.+   
Optimize ONLY when **user-visible slowdown** (page load >2s).

---

## 2. My Performance Model (What Matters for Solo Dev)

### Database Performance (PostgreSQL)+

**What Will Slow You Down (in Order):**

```sql
-- 1. Missing indexes (BIGGEST sin)
CREATE INDEX CONCURRENTLY enquiries_status_idx ON enquiries (status);
CREATE INDEX CONCURRENTLY enquiries_customer_id_idx ON enquiries (customer_id);
CREATE INDEX CONCURRENTLY enquiries_created_at_idx ON enquiries (created_at DESC);
CREATE INDEX CONCURRENTLY communications_enquiry_id_idx ON communications (enquiry_id);
CREATE INDEX CONCURRENTLY bookings_customer_id_idx ON bookings (customer_id);

-- 2. Full-text search (already planned)
CREATE INDEX enquiries_search_idx ON enquiries USING GIN (search_vector);

-- 3. Query optimization (EXPLAIN ANALYZE)
EXPLAIN ANALYZE 
SELECT * FROM enquiries 
WHERE customer_id = 'cust-001' 
ORDER BY created_at DESC 
LIMIT 10;
-- If Seq Scan → add index
```

**My insight:**   
Add indexes **after** you see slow queries in logs.+   
`CONCURRENTLY` = add index without locking table (zero downtime).

---

### Application Performance (Next.js + FastAPI)

**What Actually Matters:**

| Factor | Impact | Solo Dev Action |
|--------|--------|-----------------|
| **DB connection pool** | HIGH | `pool_size=10` (default is fine) |
| **N+1 queries** | HIGH | Use `JOIN` in API, not loop+query |
| **Frontend bundle** | MEDIUM | Next.js auto-splits, don't worry |
| **Image optimization** | LOW | Receipts are small, no gallery |
| **Caching** | MEDIUM | React Query cache (built-in) |

```python
# FastAPI: avoid N+1
# BAD: N+1
enquiries = db.get_enquiries()
for eq in enquiries:
    customer = db.get_customer(eq.customer_id)  # N extra queries!

# GOOD: JOIN
enquiries = db.get_enquiries_with_customer()  # 1 query with JOIN
```

**My insight:**   
N+1 = #1 performance killer in APIs.+   
React Query cache = frontend is fast (no re-fetch).

---

## 3. WhatsApp Business API Limits**

### Meta Rate Limits (What You Need to Know)

| Limit Type | Value | What It Means |
|------------|--------|------------------|
| **Messages / 24h** | 1,000 (per phone number) | ~3 msgs/hour → fine for 200 enquiries |
| **Messages / second** | 20 (burst) | Don't send bulk blast |
| **Template messages** | Unlimited after approval | Use templates for alerts |
| **Freeform messages** | 24h window | Customer must reply to open window |

**My insight:**   
1,000 msgs/24h = **enough for 200 enquiries/month** (5 msgs/enquiry avg).+   
24h window = can't spam customer after they go silent.

---

### Handling Rate Limits (Simple Queue)

```python
# utils/whatsapp_queue.py
from celery import Celery  # OR use asyncio.Queue for solo dev

# Simple in-memory queue (solo dev = 1 process)
message_queue = asyncio.Queue()

async def send_whatsapp_with_retry(to: str, text: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            # WhatsApp API has rate limit ~20/sec
            await asyncio.sleep(0.1)  # 100ms gap → 10/sec (safe)
            response = await meta_api.send_message(to, text)
            return response
        except RateLimitError:
            # Wait 60s, retry
            await asyncio.sleep(60)
    raise Exception("WhatsApp rate limit exceeded after retries")

# BATCH sending (for digests)
async def send_bulk(recipients: list, message: str):
    for recipient in recipients:
        await send_whatsapp_with_retry(recipient, message)
        await asyncio.sleep(1)  # 1 msg/sec (ultra-safe)
```

**My insight:**   
`asyncio.Queue` = simple, no Redis/Celery needed for solo dev.+   
1 msg/sec = **zero rate limit issues** (even 10x scale).

---

## 4. When to Scale (Practical Triggers)**

### Database Scaling (PostgreSQL)

| Trigger | Action | Cost |
|---------|--------|------|
| **DB > 10GB** | Add indexes (already done) | Free |
| **Query > 1s** | `EXPLAIN ANALYZE` + index | Free |
| **DB > 100GB** | Partition tables (by month) | Free |
| **Connections exhausted** | Increase `max_connections` | Free |
| **CPU > 80%** | Upgrade VPS (2→4 cores) | ~$10/month |

**My insight:**   
PostgreSQL handles **100GB+ easily** on a $20/month VPS.+   
Partition `communications` table by month → queries are fast (only scan 1 month).

---

### Application Scaling (Next.js + FastAPI)

| Trigger | Action | Cost |
|---------|--------|------|
| **Page load > 2s** | Check N+1 queries | Free |
| **API response > 500ms** | Add DB indexes | Free |
| **1000 enquiries** | Still fine (Next.js handles it) | Free |
| **10000 enquiries** | Maybe add Redis cache | ~$5/month |
| **Concurrent users > 10** | Upgrade VPS | ~$10/month |

**My insight:**   
You have **1 user** (yourself). Concurrency isn't a problem.+   
Scale only when YOU feel slowdown (not theoretical limits).

---

## 5. File Storage Scaling (S3)**

### When S3 Costs Grow

| DB records | Files (receipts) | S3 Cost/Month |
|------------|-------------------|----------------|
| 500 enquiries | ~200 files | ~$0.50 |
| 5000 enquiries | ~2000 files | ~$5 |
| 50000 enquiries | ~20000 files | ~$50 |

**My insight:**   
`S3 Standard-IA` storage = **50% cheaper** for backups.+   
Delete receipt files after 7 years (tax law) → lifecycle policy.

---

## 6. Current State vs Performance Model**

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| DB indexes | None | Add when query > 1s (not before) |
| N+1 queries | Unknown | Audit APIs with `EXPLAIN` |
| WhatsApp limits | None | 1 msg/sec queue (ultra-safe) |
| Caching | None | React Query (built-in) |
| Monitoring | None | Add when slowdown felt |

---

## 7. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Add indexes now? | Yes / No | **NO** — add when slow |
| WhatsApp queue? | Celery / asyncio.Queue | **asyncio.Queue** — zero infra |
| Redis cache? | Now / Later | **Later** — you have 1 user |
| Monitor performance? | Datadog / Simple logs | **Simple logs** — `EXPLAIN ANALYZE` |
| Partition tables? | Now / When > 10GB | **When > 10GB** |

---

## 8. Next Discussion: Localization & Offline+

Now that we know **performance limits**, we need to discuss: **What if you go to remote Bali?**

Key questions for next discussion:
1. **Localization** — Hindi/English for India? Mandarin/English for Bali?
2. **Offline mode** — can you work in Gili Islands (no internet)?
3. **Progressive Web App** — already discussed, but offline details?
4. **Solo dev reality** — will you EVER work offline? (maybe for remote destinations)

---

**Next file:** `Docs/discussions/localization_offline_2026-04-29.md`
