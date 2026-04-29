# Mobile & PWA — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, WhatsApp-primary, need mobile access  
**Approach:** Independent analysis — you live on phone, system must work there  

---

## 1. The Core Truth: You're Mobile-First (WhatsApp)**

### Your Reality (Solo Dev)

| Where You Work | % of Time |
|-------------------|--------------|
| **WhatsApp** | 70% (customer + vendor comms) |
| **Phone browser** | 20% (quick checks, reply) |
| **Desktop** | 10% (drafting, invoicing) |

**My insight:**  
Mobile = PRIMARY, not secondary. System must be **usable on 6-inch screen**.

---

## 2. My PWA Strategy (Progressive Web App)**

### Why PWA Over Native App (Solo Dev)**

| Factor | PWA | Native App (React Native/Flutter) |
|--------|-----|----------------------------------|
| **Cost to build** | 1x (just web) | 3x (separate codebase) |
| **Maintenance** | Same repo | 2 repos |
| **WhatsApp integration** | Web links → opens app | Deep linking setup |
| **Offline mode** | Service worker | Built-in |
| **App store** | No (just URL) | Yes (review process) |
| **Push notifications** | Web Push API | Native (better) |

**My recommendation:**  
**PWA** — you're a web dev, it's ONE codebase.  
Add to homescreen → acts like native app.

---

### PWA Features You Actually Need**

```json
{
  "pwa_config": {
    "name": "Travel Agency OS",
    "short_name": "TA-OS",
    "start_url": "/dashboard",
    "display": "standalone",  // No browser UI
    "background_color": "#0f172a",  // Dark theme
    "theme_color": "#3b82f6",
    "icons": [
      { "src": "/icons/icon-192.png", "sizes": "192x192" },
      { "src": "/icons/icon-512.png", "sizes": "512x512" }
    ],
    
    // What's cached (offline)
    "cache_strategy": {
      "enquiry_list": "network-first",  // Fresh data
      "enquiry_detail": "cache-first",  // View offline
      "drafts": "cache-first",  // Edit offline
      "communications": "network-only"  // Need network
    },
    
    // Offline fallback
    "offline_page": "/offline",  // "You're offline, call customer via WhatsApp"
    
    // Push notifications (Web Push)
    "push_enabled": true,  // Browser notifications
    "vapid_public_key": "string",  // For Web Push
    "notification_icons": { "alert": "/icons/alert.png" }
  }
}
```

**My insight:**  
Cache **enquiry_detail** (view offline) but NOT comms (need network).  
Offline fallback = "Call customer on WhatsApp" — that still works offline.

---

## 3. Mobile-Responsive UI (Critical)**

### What You'll Actually Do on Phone**

```
Mobile Tasks (6-inch screen):
  ✅ Reply to customer WhatsApp (from notification)
  ✅ Mark payment as "done" (quick action)
  ✅ View enquiry details (read-only mostly)
  ✅ Upload receipt photo (payment proof)
  
  ❌ Draft complex itinerary (do on desktop)
  ❌ Generate invoices (do on desktop)
  ❌ Analyze reports (do on desktop)
```

**My insight:**  
Mobile UI = **quick actions** (reply, mark done, upload photo).  
Complex tasks = desktop (you'll hate doing them on phone).

---

### Mobile UI Layout (Thumb-Friendly)**

```typescript
// Mobile layout (bottom tab bar)
<TabBar>
  <Tab icon="message" label="Chats" />      // WhatsApp-style
  <Tab icon="file-text" label="Enquiries" />
  <Tab icon="bell" label="Alerts" badge={3} />  // Red dot
  <Tab icon="user" label="Profile" />
</TabBar>

// Enquiry list (mobile)
<EnquiryCard>
  <CustomerAvatar src={avatar} />
  <Title>{customerName} • VIP</Title>
  <Snippet>{lastMessageSnippet}</Snippet>
  <QuickActions>
    <Button size="sm">Reply</Button>
    <Button size="sm">Mark Paid</Button>
  </QuickActions>
</EnquiryCard>
```

**My insight:**  
Bottom tab bar = thumb-friendly (Apple HIG).  
Quick actions = NO digging into menus on phone.

---

## 4. WhatsApp Business API Integration (Critical)**

### Why Business API? (Not Personal WhatsApp)**

| Feature | Personal WhatsApp | WhatsApp Business API |
|---------|-------------------|--------------------------|
| **Multiple agents** | ❌ No (1 phone) | ✅ Multiple logins |
| **Automated replies** | ❌ Manual | ✅ Auto-reply |
| **Message templates** | ❌ No | ✅ Pre-approved |
| **Webhook** | ❌ No | ✅ Receive via API |
| **QR code** | ❌ No | ✅ Customers scan → chat |

**My insight:**  
Personal WhatsApp = you're the bottleneck (only YOU can reply).  
Business API = **scale** (hire help later, they can login).

---

### WhatsApp Business API Flow**

```python
# /api/whatsapp/webhook (receive messages)
@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(payload: dict):
    # 1. Verify webhook (Meta security)
    if not verify_signature(payload):
        return {"error": "Invalid signature"}, 401
    
    # 2. Extract message
    message = payload['messages'][0]
    from_number = message['from']  # "+919876543210"
    text = message['text']['body']
    
    # 3. Find or create customer
    customer = db.find_customer_by_phone(from_number)
    if not customer:
        customer = db.create_customer({
            "phone_primary": from_number,
            "first_name": "Unknown"  # Will update later
        })
    
    # 4. Create enquiry (auto)
    enquiry = db.create_enquiry({
        "customer_id": customer.id,
        "channel": "whatsapp",
        "raw_text": text,
        "status": "RECEIVED"
    })
    
    # 5. Trigger AI analysis
    spine_client.analyze(enquiry.id)
    
    # 6. Reply "We received your enquiry"
    await send_whatsapp(
        to=from_number,
        text="Namaste! 👋 We received your enquiry about Bali. Our agent will reply in 30 mins."
    )
    
    return {"status": "ok"}
```

**My insight:**  
Auto-reply = "We got it" → customer feels heard.  
30-min SLA → set expectation (WhatsApp is instant).

---

### WhatsApp Message Templates (Pre-Approved)**

```json
{
  "templates": [
    {
      "name": "enquiry_received",
      "category": "ALERT_UPDATE",
      "language": "en",
      "components": [
        {
          "type": "body",
          "text": "Hi {{1}}, we received your enquiry about {{2}}. Agent will reply in {{3}} mins. Ref: {{4}}"
        }
      ]
    },
    {
      "name": "payment_confirmation",
      "category": "ALERT_UPDATE",
      "components": [
        {
          "type": "body",
          "text": "Payment of ₹{{1}} received for {{2}}. Booking ref: {{3}}"
        }
      ]
    },
    {
      "name": "draft_ready",
      "category": "ALERT_UPDATE",
      "components": [
        {
          "type": "body",
          "text": "Your {{1}} itinerary is ready! View: {{2}}"
        }
      ]
    }
  ]
}
```

**My insight:**  
Templates need **Meta approval** (24-48h). Pre-approve common ones.  
Use `{{1}}` variables — personalized but automated.

---

## 5. Mobile Camera Integration (Receipt Upload)**

### Problem: Payment Proof on Desktop = Friction**

Customer sends UPI screenshot on WhatsApp → you download → upload to desktop → mark as paid.

**Solution: Mobile upload directly.**

```typescript
// Mobile: upload receipt photo
const handleReceiptUpload = async (enquiryId: string) => {
  // 1. Open camera/gallery
  const image = await camera.capture();
  
  // 2. Compress (mobile data)
  const compressed = await compress(image, { quality: 0.7 });
  
  // 3. Upload
  await uploadFile(`/api/enquiries/${enquiryId}/receipts`, compressed);
  
  // 4. Auto-mark as "payment proof uploaded"
  await db.updateEnquiry(enquiryId, { 
    payment_status: "PARTIAL",
    receipt_url: uploadedUrl 
  });
};
```

**My insight:**  
Mobile upload = **10 seconds** vs desktop = **2 minutes** (download + upload).  
Compress image — mobile data is expensive in India.

---

## 6. Offline Mode (Maybe for Remote Destinations)**

### When Do You Need Offline?**

| Scenario | Need Offline? | Why |
|----------|-------------------|-----|
| **In Phuket, customer calls** | ✅ YES | Expensive roaming, slow data |
| **At office, drafting** | ❌ NO | Good WiFi |
| **In taxi, quick check** | 🟡 MAYBE | Flaky network |

### My Lean Offline Strategy**

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
```

**My insight:**  
Cache ONLY what you VIEWED — not everything (limited phone storage).  
Offline = **read-only** (enquiry details), not create new.

---

## 7. Current State vs Mobile Model**

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| PWA | None | Next.js PWA (one codebase) |
| Mobile UI | None | Bottom tab bar + quick actions |
| WhatsApp API | Manual (personal) | Business API (webhook + templates) |
| Push notifications | None | Web Push API (browser) |
| Offline mode | None | Service worker (viewed only) |
| Camera upload | None | `navigator.mediaDevices.getUserMedia()` |

---

## 8. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| PWA vs Native? | PWA / React Native | **PWA** — one codebase |
| WhatsApp Business API? | Now / Later | **Now** — personal = bottleneck |
| Offline mode? | Full / Read-only / None | **Read-only** — viewed enquiries |
| Push notifications? | Web Push / SMS | **Web Push** — free, built-in |
| Camera upload? | Yes / No | **YES** — receipt proof upload |
| Mobile reports? | Yes / No | **NO** — desktop only |

---

## 9. Next Discussion: Backup & Security**

Now that we know **HOW you work** (mobile + WhatsApp), we need to discuss: **What if you lose everything?**

Key questions for next discussion:
1. **Automated backups** — PostgreSQL backup, how often? (daily?)
2. **WhatsApp chat backup** — Google Drive backup? (automatic)
3. **File backups** (receipts, invoices) — S3/R2 or local?
4. **Encryption keys backup** — lose keys = lose ALL PII
5. **Disaster recovery** — can you restore in 1 hour?
6. **Solo dev reality** — what's the MINIMUM backup strategy?

---

**Next file:** `Docs/discussions/backup_and_security_2026-04-29.md`
