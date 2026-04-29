# Logging & Observability — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, need logs for debugging  
**Approach:** Independent analysis — minimum viable logging, not enterprise  

---

## 1. The Core Truth: Logs = Your Eyes When Things Break+

### Your Reality (Solo Dev))

| What Happens | Without Logs | With Logs |
|--------------|---------------|------------|
| **AI fails** | ❌ NO idea WHY | ✅ See stack trace + input |
| **WhatsApp API down** | ❌ wonder why | ✅ `403 Forbidden` logged |
| **DB query slow** | ❌ "It's slow" | ✅ `EXPLAIN` shows missing index |
| **Customer says "I never got that!"** | ❌ Your word vs theirs | ✅ Logged: sent at 2:30pm |

**My insight:**   
Logs = **insurance policy** (cheap, saves hours debugging).   
Railway/Vercel = **built-in**, zero setup.

---

## 2. My Logging Model (Lean, Structured))

### Python (spine_api, logging.json))+

```python
# spine_api/utils/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'enquiry_id'):
            log_record['enquiry_id'] = record.enquiry_id
        if hasattr(record, 'customer_id'):
            log_record['customer_id'] = record.customer_id
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms
        
        return json.dumps(log_record)

# Setup
def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler (Railway captures this)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
```

**My insight:**   
JSON = **machine-readable**, Railway/Vercel parse it.   
`enquiry_id` in every log = filter later. 

---

### Next.js (Frontend, console.log = enough))+

```typescript
// lib/logger.ts (simple wrapper)
export const log = {
  info: (message: string, context?: Record<string, unknown>) => {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'INFO',
      message,
      ...context
    }))
  },
  
  warn: (message: string, context?: Record<string, unknown>) => {
    console.warn(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'WARN',
      message,
      ...context
    }))
  },
  
  error: (message: string, error?: Error, context?: Record<string, unknown>) => {
    console.error(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: 'ERROR',
      message,
      error: error?.message,
      stack: error?.stack,
      ...context
    }))
  }
}

// Usage:
log.info('Enquiry created', { enquiry_id: 'eq-001', channel: 'whatsapp' })
log.error('WhatsApp API failed', error, { customer_id: 'cust-042' })
```

**My insight:**   
`console.log` = Railway captures it. Don't over-engineer.   
Add `enquiry_id` everywhere = filter in 1 click. 

---

## 3. What to Log (Minimum Viable))+

### Python (spine_api))+

| Event | Level | Fields to Include |
|-------|-------|-------------------|
| **Enquiry created** | INFO | `enquiry_id`, `channel`, `customer_id` |
| **AI analysis start** | INFO | `enquiry_id`, `model_used` |
| **AI analysis done** | INFO | `enquiry_id`, `duration_ms`, `decision_state` |
| **Booking created** | INFO | `booking_id`, `customer_id`, `value` |
| **Payment marked** | INFO | `booking_id`, `amount`, `method` |
| **WhatsApp sent** | INFO | `to_number`, `enquiry_id`, `message_length` |
| **API error** | ERROR | `endpoint`, `status_code`, `error` |
| **DB slow query** | WARN | `query`, `duration_ms` (>1s) |

**My insight:**   
Log **decision_state** = debug AI failures fast.   
`duration_ms` > 1000ms = warn (performance clue). 

---

### Next.js (Frontend))+

| Event | Level | Fields to Include |
|-------|-------|-------------------|
| **Page view** | INFO | `url`, `enquiry_id` (if viewing) |
| **Draft sent** | INFO | `enquiry_id`, `channel` |
| **Payment marked** | INFO | `booking_id`, `amount` |
| **API error** | ERROR | `endpoint`, `status`, `message` |
| **WhatsApp click** | INFO | `enquiry_id`, `action` |

**My insight:**   
Log **page views** = know customer journey.   
Don't log PII (passport numbers) — mask them. 

---

## 4. Log Storage (Where Do They Go?))+

### Railway (Backend — Built-in, FREE))+

| Provider | Cost | Retention | Search? |
|----------|------|-----------|---------|
| **Railway Logs** | FREE | 7 days | ✅ Web UI |
| **S3 (optional)** | $0.50/GB | Forever | ✅ Athena queries |

```bash
# Railway auto-captures stdout/stderr
# View logs: https://railway.app/project/your-project/logs

# Optional: Ship to S3 (for long-term)
# .env:
LOG_S3_BUCKET=my-agency-logs
LOG_S3_KEY_ID=AKIAIOSFODNN7EXAMPLE
LOG_S3_SECRET=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

**My insight:**   
7 days = enough for debugging.   
S3 = $0.50/GB if you need forever. 

---

### Vercel (Frontend — Built-in, FREE))+

| Provider | Cost | Retention | Search? |
|----------|------|-----------|---------|
| **Vercel Logs** | FREE | 7 days | ✅ Web UI |
| **Sentry (optional)** | FREE (5k events) | 30 days | ✅ Search |

```bash
# Vercel auto-captures console.log
# View logs: https://vercel.com/your-org/project/logs
```

**My insight:**   
Vercel = 7 days FREE. Enough for solo dev.   
Sentry = already planned (error tracking). 

---

## 5. Log Rotation (Keep Disk Clean))+

### Railway (Auto, You Do Nothing))+

| Setting | Default | Change? |
|---------|---------|---------|
| **Retention** | 7 days | ❌ NO (enough) |
| **Max size** | 100MB | ❌ NO (small app) |
| **Log level** | INFO | 🟡 MAYBE (DEBUG for 1 day) |

**My insight:**   
Railway = **auto-rotation**. Set and forget.   
DEBUG = 10x log volume, use for 1 day only. 

---

## 6. Structured Logging (JSON Benefits))+

### Why JSON > Text+

| Format | Searchable? | Machine-Readable? | Human-Readable? |
|--------|-------------|--------------------|-------------------|
| **Text** | ❌ NO | ❌ NO | ✅ YES |
| **JSON** | ✅ YES | ✅ YES | 🟡 MAYBE |

```json
// Text log (BAD)
[2026-04-29 14:30:00] INFO: Enquiry eq-001 created for Ravi

// JSON log (GOOD)
{"timestamp":"2026-04-29T14:30:00Z","level":"INFO","message":"Enquiry created","enquiry_id":"eq-001","customer_name":"Ravi","channel":"whatsapp"}
```

**My insight:**   
JSON = **filter in Railway UI**: `enquiry_id: "eq-001"`.   
Text = grep only (slow, painful). 

---

## 7. Sensitive Data Masking (CRITICAL))+

### What NOT to Log+

| Data | Log? | Why NOT |
|------|-------|----------|
| **Passport numbers** | ❌ NO | PII, GDPR violation |
| **WhatsApp API keys** | ❌ NO | Security risk |
| **Encryption keys** | ❌ NO | ALL data compromised |
| **Customer phone** | 🟡 MAYBE | Mask: "+91 987******10" |
| **Email addresses** | ✅ YES | Not sensitive |

```python
# Mask PII before logging
def mask_pii(value: str, mask_char='*') -> str:
    if len(value) <= 4:
        return '*' * len(value)
    return value[:2] + mask_char * (len(value) - 4) + value[-2:]

# Usage:
log.info('Payment received', {
    'customer_id': cust_id,
    'phone': mask_pii('+919876543210', '*')  # "+91******10"
})
```

**My insight:**   
Mask PII = **legal requirement** (GDPR/DPDP).   
`*' * 6` = still recognizable, not full exposure. 

---

## 8. Current State vs Logging Model)++

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Log format | None | JSON (machine-readable) |
| Log storage | None | Railway/Vercel built-in (FREE) |
| Structured fields | None | `enquiry_id`, `customer_id`, `duration_ms` |
| PII masking | None | Mask passport/phone |
| Log rotation | None | Railway auto (7 days) |
| Sentry | Planned | ✅ YES (errors only) |

---

## 9. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| JSON format? | Text / JSON | **JSON** — searchable |
| S3 long-term? | Yes / No | **NO** — 7 days enough |
| PII masking? | Full / Mask / None | **MASK** — legal requirement |
| DEBUG logs? | Always / 1 day / Never | **1 day** — when debugging |
| Log level in prod? | DEBUG / INFO / WARN | **INFO** — quiet, important only |

---

## 10. Next Discussion: Error Handling & UX+

Now that we know **WHERE logs go**, we need to discuss: **What does user see when things break?**

Key questions for next discussion:
1. **Error boundaries** — React catches crash, shows friendly message?
2. **API errors** — 500, 404, 401 → user-friendly text?
3. **WhatsApp failures** — API down → auto-retry?
4. **Graceful degradation** — DB down → show cached data?
5. **Solo dev reality** — what's the MINIMUM error handling?

---

**Next file:** `Docs/discussions/error_handling_ux_2026-04-29.md`
