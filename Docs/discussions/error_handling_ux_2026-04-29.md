# Error Handling & UX — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, users see errors  
**Approach:** Independent analysis — what user sees when things break  

---

## 1. The Core Truth: Users Don't Read Stack Traces+

### Your Reality (Solo Dev))

| Scenario | Bad UX | Good UX |
|----------|--------|---------|
| **AI fails** | `500 Internal Server Error` | "AI is busy, try in 5 mins 😊" |
| **WhatsApp API down** | `403 Forbidden` | "WhatsApp is having issues, call us: +91 98765 43210" |
| **DB connection fails** | `503 Service Unavailable` | "System is updating, back in 2 mins ⚙️" |
| **Customer sends bad input** | `400 Bad Request` | "Please include destination + dates 📍" |

**My insight:**   
As solo dev, **YOU get the stack trace**. Customer gets **friendly message only**.  
Every error = **opportunity to build trust** (or destroy it).

---

## 2. My Error Handling Model (Lean, Practical))+

### Error Types (What Can Go Wrong))+

| Error Type | Level | User Message | Action |
|-----------|-------|--------------|--------|
| **AI API fails** | ERROR | "AI is busy, try in 5 mins 😊" | Auto-retry 3x |
| **WhatsApp API fails** | ERROR | "WhatsApp issues, call us: +91 98765 43210" | Alert YOU |
| **DB connection fails** | CRITICAL | "Updating system, back in 2 mins ⚙️" | Restart Railway |
| **Enquiry not found** | WARN | "Enquiry not found, check link 🔍" | Check QR code |
| **Payment proof invalid** | WARN | "Please send clearer photo 📸" | Ask again |
| **Rate limited** | WARN | "Too many requests, slow down 🐢" | Wait 1 min |

**My insight:**   
AI fails = **retry 3x** (often transient).  
DB fails = **CRITICAL** (restart Railway in 2 mins).

---

### Frontend Error Boundaries (React))+

```typescript
// app/error-boundary.tsx+
'use client';

export class ErrorBoundary extends React.Component<{
  children: React.ReactNode+
  state: { hasError: boolean; error?: Error } = { hasError: false };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to Sentry (if configured)
    console.error('UI Error:', error, errorInfo);
    
    // Log to your backend
    fetch('/api/log-error', {
      method: 'POST',
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        url: window.location.pathname
      })
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2>😊 Something went wrong</h2>
            <p>Our team is fixing it. Try in 2 mins.</p>
            <button onClick={() => window.location.reload()}>
              Reload →
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Wrap app:
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

**My insight:**   
Error boundary = **catches React crashes**.  
Sentry logs = YOU debug remote.

---

### WhatsApp Error Replies (API Down))+

```python
# spine_api/error_handlers.py+
from fastapi import Request, HTTPException+
from fastapi.responses import JSONResponse+
import traceback+

async def whatsapp_error_handler(request: Request, exc: Exception):
    """Handle WhatsApp API errors gracefully."""
    
    # Meta API auth error (YOU need to fix)
    if isinstance(exc, HTTPException) and exc.status_code == 403:
        # Alert YOU immediately
        await notify_agent(
            severity="CRITICAL",
            message="🚨 WhatsApp API key expired! Fix now."
        )
        # Tell customer (via SMS maybe?)
        return JSONResponse(
            status_code=200,  # WhatsApp expects 200
            content={
                "error": "WhatsApp issues, call us: +91 98765 43210"
            }
        )
    
    # Generic error
    error_id = generate_short_id()
    logger.error(f"Error {error_id}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=200,
        content={
            "error": "System busy, try in 5 mins 😊",
            "error_id": error_id
        }
    )

# Register:
@app.exception_handler(Exception)
async def global_error_handler(request, exc):
    if request.url.path.startswith('/api/whatsapp'):
        return await whatsapp_error_handler(request, exc)
    raise exc
```

**My insight:**   
WhatsApp expects **200 even on errors**.  
`error_id` = YOU track in logs ("Error ABC12 happened again?"). 

---

### User-Friendly Messages (i18n))+

```json
{
  "error_messages": {
    "en": {
      "ai_busy": "AI is busy, try in {minutes} mins 😊",
      "whatsapp_down": "WhatsApp issues, call: {phone}",
      "db_down": "Updating system, back in {minutes} mins ⚙️",
      "not_found": "{entity} not found, check link 🔍",
      "invalid_input": "Please include: {fields} 📍",
      "rate_limited": "Slow down 🐢, wait {seconds}s"
    },
    "hi": {
      "ai_busy": "AI व्यस्त है, {minutes} मिनट में ट्रयास करें 😊",
      "whatsapp_down": "WhatsApp में समस्या, कॉल करें: {phone}",
      "db_down": "सिस्टम अपडेट हो रहा है, {minutes} मिनट में वापस आएगा ⚙️",
      "not_found": "{entity} नहीं मिला, लिंक चेक करें 🔍",
      "invalid_input": "कृपया शामिल करें: {fields} 📍",
      "rate_limited": "धीरे करें 🐢, {seconds}s प्रतीक्षा करें"
    }
  }
}
```

**My insight:**   
In Hindi: "AI व्यस्त है" = friendly, trust-building.  
Variables `{minutes}` = dynamic (tell exact time).

---

## 3. API Error Responses (Consistent))+

### Spine API (FastAPI))+

```python
# spine_api/responses.py+
from pydantic import BaseModel+

class ErrorResponse(BaseModel):
    """Consistent error response."""
    error: str+
    error_code: str+
    message: str  # User-friendly
    error_id: str  # For tracking
    details: dict | None = None+

# Usage in endpoints:
@app.post("/api/enquiries/{id}/draft")
async def generate_draft(enquiry_id: str):
    enquiry = db.get_enquiry(enquiry_id)
    if not enquiry:
        return ErrorResponse(
            error="NOT_FOUND",
            error_code="ENQUIRY_NOT_FOUND",
            message="Enquiry not found, check link 🔍",
            error_id=generate_short_id()
        )
    
    if enquiry.status == "COMPLETED":
        return ErrorResponse(
            error="INVALID_STATE",
            error_code="ENQUIRY_ALREADY_COMPLETED",
            message="This enquiry is already completed ✅",
            error_id=generate_short_id()
        )
    
    # Process...
    return {"status": "ok", "draft": draft}
```

**My insight:**   
`error_code` = frontend can **act differently** per code.  
`error_id` = YOU find in logs instantly.

---

### Next.js API Routes (BFF))+

```typescript
// app/api/[...path]/route.ts+
export async function GET(request: Request) {
  try {
    const response = await fetch(`${API_BASE_URL}${request.nextUrl.pathname}`);
    
    if (!response.ok) {
      const error = await response.json();
      
      // Map backend errors to user messages
      switch (error.error_code) {
        case 'ENQUIRY_NOT_FOUND':
          return NextResponse.json(
            { message: error.message },
            { status: 404 }
          );
        case 'RATE_LIMITED':
          return NextResponse.json(
            { message: error.message },
            { status: 429 }
          );
        default:
          return NextResponse.json(
            { message: 'System busy, try in 5 mins 😊' },
            { status: 500 }
          );
      }
    }
    
    return NextResponse.json(await response.json());
    
  } catch (error) {
    // Log to Sentry
    console.error('BFF Error:', error);
    
    return NextResponse.json(
      { message: 'System busy, try in 5 mins 😊' },
      { status: 500 }
    );
  }
}
```

**My insight:**   
BFF = **translates** backend errors to user-friendly.  
Never expose stack trace to user.

---

## 4. Toast/Notification UX (Frontend))+

### What User Sees (Success + Error))+

```typescript
// components/Toast.tsx+
import { toast } from 'react-hot-toast';+

export const showSuccess = (message: string) => {
  toast.success(message, {
    duration: 3000,
    icon: '✅',
  });
};

export const showError = (message: string, error_id?: string) => {
  toast.error(
    `${message}${error_id ? ` (Ref: ${error_id})` : ''}`,
    {
      duration: 5000,
      icon: '😊',
      action: {
        label: 'Report',
        onClick: () => reportError(error_id)
      }
    }
  );
};

export const showWarning = (message: string) => {
  toast(message, {
    duration: 4000,
    icon: '⚠️',
  });
};

// Usage:
await generateDraft(enquiryId);
showSuccess('Draft ready! View →');

// On error:
showError("AI is busy, try in 5 mins 😊", "ABC12");
```

**My insight:**   
`error_id` on toast = user can say "Error ABC12 happened!"  
`Report` button = they can alert YOU faster.

---

### WhatsApp Toasts (Messages to Customer))+

```python
# utils/whatsapp_messages.py+
def get_error_message(error_type: str, lang: str = 'en', **kwargs) -> str:
    """Get user-friendly WhatsApp message."""
    messages = {
        'en': {
            'ai_busy': "😊 AI is busy, try in {minutes} mins. Or call: +91 98765 43210",
            'payment_invalid': "📸 Please send clearer photo of payment. WhatsApp us!",
            'enquiry_not_found': "🔍 Enquiry not found. Scan QR again or call +91 98765 43210"
        },
        'hi': {
            'ai_busy': "😊 AI व्यस्त है, {minutes} मिनट में ट्रयास करें। या कॉल करें: +91 98765 43210",
            'payment_invalid': "📸 कृपया पेमेंट की साफ फोटो भेजें। WhatsApp करें!",
            'enquiry_not_found': "🔍 एनक्वायरी नहीं मिली। फिर से QR स्कैन करें या कॉल करें +91 98765 43210"
        }
    }
    
    msg = messages.get(lang, messages['en']).get(error_type, 'System busy, try later 😊')
    return msg.format(**kwargs)

# Usage:
await send_whatsapp(
    to=customer_phone,
    text=get_error_message('ai_busy', lang='hi', minutes=5)
)
```

**My insight:**   
WhatsApp = **primary channel**, must be friendly.  
Always include **phone number** as backup.

---

## 5. Database Error Handling))+

### Connection Pool (Auto-Retry))+

```python
# spine_api/core/database.py+
from sqlalchemy import create_engine, exc+
from sqlalchemy.orm import sessionmaker, scoped_session+
import time+

def create_db_engine():
    """Create engine with retry logic."""
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connection before use
        pool_recycle=3600,  # Recycle connections after 1h
        pool_size=10,
        max_overflow=5
    )
    
    # Test connection on startup
    for attempt in range(3):
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return engine
        except exc.SQLAlchemyError as e:
            if attempt == 2:
                logger.critical(f"DB connection FAILED: {e}")
                raise
            logger.warn(f"DB connection retry {attempt + 1}/3")
            time.sleep(2 ** attempt)
    
    raise Exception("Could not connect to DB")

# Usage:
engine = create_db_engine()
SessionLocal = scoped_session(sessionmaker(bind=engine))
```

**My insight:**   
`pool_pre_ping=True` = catches stale connections.  
3 retries = survive transient DB restarts.

---

### Transaction Rollback (Data Integrity))+

```python
# In API endpoints:
@app.post("/api/bookings")
async def create_booking(payload: BookingCreate):
    db = SessionLocal()
    try:
        # Create booking
        booking = Booking(**payload.dict())
        db.add(booking)
        
        # Create payment record
        payment = Payment(booking_id=booking.id, ...)
        db.add(payment)
        
        db.commit()  # Atomic: both succeed or both fail
        return {"status": "ok", "booking_id": booking.id}
        
    except exc.IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error: {e}")
        return ErrorResponse(
            error="INVALID_DATA",
            error_code="DUPLICATE_BOOKING",
            message="Booking already exists for this enquiry 🔍",
            error_id=generate_short_id()
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {e}")
        raise
        
    finally:
        db.close()
```

**My insight:**   
`db.rollback()` = data integrity (no partial commits).  
`finally: db.close()` = always release connection.

---

## 6. Current State vs Error Handling Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Error boundaries | None | React ErrorBoundary (catches crashes) |
| Friendly messages | None | i18n messages (en + hi) |
| Error codes | None | `error_code` (frontend acts differently) |
| Error ID tracking | None | `error_id` (find in logs instantly) |
| DB retry logic | None | 3x retry + `pool_pre_ping` |
| WhatsApp errors | None | User-friendly via WhatsApp + phone backup |
| Toast notifications | None | react-hot-toast (success/error/warning) |

---

## 7. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Error boundary? | Yes / No | **YES** — 5 mins, catches crashes |
| i18n messages? | en + hi / en only | **en + hi** — 60%+ customers |
| Error ID tracking? | Yes / No | **YES** — find in logs instantly |
| DB retry? | 3x / 1x / None | **3x** — survive transient issues |
| Toast library? | react-hot-toast / None | **react-hot-toast** — 5 mins setup |
| Sentry for errors? | Yes / Later | **Later** — console.error enough |

---

## 8. Next Discussion: Data Export & Portability+

Now that we know **what user sees when things break**, we need to discuss: **What if customer asks "export my data"?**

Key questions for next discussion:
1. **GDPR right-to-export** — JSON/PDF/Excel?
2. **What to include** — enquiries, bookings, PII?
3. **What to exclude** — vendor secrets, internal notes?
4. **How to deliver** — email, WhatsApp, S3?
5. **Solo dev reality** — what's the MINIMUM export needed?

---

**Next file:** `Docs/discussions/data_export_portability_2026-04-29.md`
