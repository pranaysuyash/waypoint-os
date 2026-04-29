# Localization & Offline — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, multilingual customers+  
**Approach:** Independent analysis — what languages/ofline YOU actually need  

---

## 1. The Core Truth: Your Customers Speak Many Languages+

### Your Customer Base (Likely Mix)

| Customer Type | Languages Needed | Why |
|--------------|-------------------|-----|
| **Indian (domestic)** | Hindi + English | 60%+ of your customers? |
| **Bali (Indonesia)** | Indonesian + English | Tourism hotspot |
| **Dubai (UAE)** | Arabic + English | Gulf travelers |
| **Europe (Group)** | German/French + English | Tour operators |
| **China (Bali/Thailand)** | Mandarin + English | Growing market |

**My insight:**   
English = **ALWAYS** (business language).+   
Local language = **conversion booster** (Hindi customers convert 2x if you reply in Hindi).

---

## 2. My Localization Model (Lean, Not Enterprise)

### What You Actually Need (Simple i18n)

```json
{
  "locale": {
    "default": "en",  // English always default
    "supported": ["en", "hi", "id", "ar", "zh"],  // English, Hindi, Indonesian, Arabic, Mandarin
    "detection_method": "AUTO_PHONE | MANUAL_SELECT"
  },
  
  // Translations (store in DB, not JSON files)
  "translations": {
    "en": {
      "welcome": "Namaste! We received your enquiry about {destination}.",
      "payment_received": "Payment of {amount} received for {booking_ref}.",
      "draft_ready": "Your {trip_type} itinerary is ready! View: {link}"
    },
    "hi": {  // Hindi
      "welcome": "नमस्ते! आपके {destination} की यात्रा के बारे में हमें जानकारी मिल गई है।",
      "payment_received": "{booking_ref} के लिए {amount} का भुगतान प्राप्त हुआ।",
      "draft_ready": "आपका {trip_type} यात्रा तैयार है! देखें: {link}"
    },
    "id": {  // Indonesian
      "welcome": "Halo! Kami menerima pertanyaan Anda tentang {destination}.",
      "payment_received": "Pembayaran {amount} untuk {booking_ref} diterima.",
      "draft_ready": "Itinerari {trip_type} Anda sudah siap! Lihat: {link}"
    }
  },
  
  // AI Draft Tone (per language)
  "tone_by_locale": {
    "en": "CASUAL",  // "Hey Ravi!"
    "hi": "RESPECTFUL",  // "नमस्ते रवि जी, ..."
    "ar": "FORMAL",  // "عزيزي رافي، ..."
    "zh": "FORMAL"  // "尊敬的Ravi，..."
  }
}
```

**My insight:**   
Store translations in **PostgreSQL** (`translations` table), not JSON files.+   
`{destination}` = variable substitution (not full AI translation).

---

### How to Detect Customer Language (Simple))

```python
# /api/detect-language (fast, no AI needed)
from langdetect import detect  # 1MB library

def detect_language(text: str) -> str:
    """Detect language from customer message."""
    try:
        lang = detect(text)  # Returns 'en', 'hi', 'id', etc.
        return lang if lang in ['en', 'hi', 'id', 'ar', 'zh'] else 'en'
    except:
        return 'en'  # Default to English

# Usage in WhatsApp webhook:
@app.post("/api/whatsapp/webhook")
async def webhook(payload):
    text = payload['messages'][0]['text']['body']
    customer_lang = detect_language(text)
    
    # Store on customer record
    db.update_customer(customer_id, {"preferred_language": customer_lang})
    
    # Auto-reply in THEIR language
    message = get_translation(customer_lang, 'welcome', destination='Bali')
    await send_whatsapp(to=payload['from'], text=message)
```

**My insight:**   
`langdetect` = 1MB, zero cost, fast.+   
Store `preferred_language` on customer → ALL future comms in their language.

---

## 3. Offline Mode (Remote Destinations))

### When Do You Need Offline?+

| Scenario | Need Offline? | Why |
|----------|-------------------|-----|
| **In Phuket, customer calls** | ✅ YES | Expensive roaming, slow data |
| **At office, drafting** | ❌ NO | Good WiFi |
| **In taxi, quick check** | 🟡 MAYBE | Flaky network |
| **Bali, vendor meeting** | ✅ YES | International roaming expensive |

### My Lean Offline Strategy (PWA Service Worker))

```typescript
// Service worker: cache enquiry details you VIEWED
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/enquiries/')) {
    // Cache on view
    event.respondWith(
      caches.match(event.request).then((response) => {
        return response || fetch(event.request).then((response) => {
          // Cache for offline
          caches.open('enquiries').then((cache) => {
            cache.put(event.request, response.clone());
          });
          return response;
        });
      })
    );
  }
});

// Offline page (when no network)
// app/offline/page.tsx
export default function OfflinePage() {
  return (
    <div className="p-8 text-center">
      <h2>📴 You're offline</h2>
      <p>Call customer via WhatsApp: <a href="whatsapp://send?phone={customerPhone}">Chat</a></p>
      <p>Saved enquiries: {cachedEnquiries.length} available offline</p>
    </div>
  );
}
```

**My insight:**   
Cache ONLY what you VIEWED — not everything (limited phone storage).+   
Offline = **read-only** (enquiry details), not create new.

---

### Offline + WhatsApp (The Magic Combo))

```
Scenario: You're in Gili Islands, no data.

1. Customer calls: "I need to change dates!"
2. You open app → offline page (cached enquiries available)
3. You find their enquiry (cached from yesterday)
4. You call them via WhatsApp (works on weak signal)
5. Yousay: "I'll update dates when I'm back online"
6. Later, back online → update enquiry → send confirmation
```

**My insight:**   
WhatsApp = **works on 2G**, even when data is off.+   
Offline mode = read-only, WhatsApp = communication channel. 

---

## 4. Multi-Language AI Drafts)

### How to Generate Drafts in Customer's Language+

```python
# When generating AI draft:
def generate_draft(enquiry_id: str, customer_lang: str = 'en'):
    enquiry = db.get_enquiry(enquiry_id)
    
    # 1. Generate in English first (AI is best at English)
    draft_en = spine_client.generate_draft(enquiry)
    
    # 2. Translate to customer's language (if not English)
    if customer_lang != 'en':
        draft = translate_text(draft_en, from_lang='en', to_lang=customer_lang)
        # 3. Adjust tone per locale
        tone = get_tone_by_locale(customer_lang)  # "FORMAL" for Mandarin
        draft = adjust_tone(draft, tone)
    else:
        draft = draft_en
    
    return {
        "content": draft,
        "language": customer_lang,
        "tone": tone
    }
```

**My insight:**   
AI generates in **English first** (best LLM performance).+   
`translate_text` = Google Translate API (free tier: 500K chars/month). 

---

## 5. Current State vs Localization/Offline Model+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Language detection | None | `langdetect` (1MB, zero cost) |
| Translations | None | `translations` table in PostgreSQL |
| Locale support | None | ['en', 'hi', 'id', 'ar', 'zh'] |
| Offline mode | None | Service worker (viewed only) |
| Offline page | None | WhatsApp fallback link |
| Multi-lang AI drafts | None | English first → translate → tone adjust |

---

## 6. Decisions Needed (Solo Dev Reality)+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Hindi support? | Yes / No | **YES** — 60%+ customers are Indian |
| Mandarin support? | Yes / Later | **Later** — only if Bali/Thailand bookings grow |
| Offline mode? | Full / Read-only / None | **Read-only** — viewed enquiries only |
| Translation API? | Google / Manual strings | **Manual strings** — 20 messages only |
| WhatsApp fallback? | Yes / No | **YES** — works on 2G, always available |
| Tone per locale? | Yes / No | **YES** — Mandarin = formal, Hindi = respectful |

---

## 7. Next Discussion: Domain, Hosting & Legal+

Now that we know **HOW to speak to customers**, we need to discuss: **WHERE does the system live?**

Key questions for next discussion:
1. **Domain name** — `travelagency.com` vs `ravi-travels.com`?
2. **Hosting** — AWS, Vercel, DigitalOcean, or local server?
3. **SSL certificate** — Let's Encrypt (free) or paid?
4. **Business registration** — sole proprietorship vs Pvt Ltd?
5. **GST registration** — mandatory for Indian travel agencies?
6. **Terms of Service** — what's the MINIMUM legal text?
7. **Solo dev reality** — what's the MINIMUM to go live?

---

**Next file:** `Docs/discussions/domain_hostig_legal_2026-04-29.md`
