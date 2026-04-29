# Integrations — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, WhatsApp-primary, need key integrations  
**Approach:** Independent analysis — only integrate what saves YOU time  

---

## 1. The Core Principle: Every Integration = Maintenance Cost**

### Your Reality (Solo Dev)

| Integration | Time to Build | Maintenance/Month | Worth It? |
|--------------|---------------|-------------------|-----------|
| **WhatsApp Business API** | 20h | 2h | ✅ YES — core workflow |
| **Google Calendar** | 5h | 0.5h | ✅ YES — travel dates |
| **Zoho/QuickBooks** | 15h | 1h | 🟡 MAYBE — manual invoice ok |
| **CRM import (Excel)** | 3h | 0h | ✅ YES — migrate old data |
| **Google Maps API** | 2h | 0h | 🟡 MAYBE — nice widget |
| **Stripe/Razorpay** | SKIP | — | ❌ NO — no collection |

**My insight:**  
As solo dev, **every integration is a debt**. Only integrate what saves YOU >5h/month.

---

## 2. WhatsApp Business API (CRITICAL Integration)**

### Why This is #1 Priority**

| Without API | With API |
|--------------|------------|
| ❌ You manually reply to every message | ✅ Auto-ack + AI draft ready |
| ❌ No record of chats (phone only) | ✅ All chats in system DB |
| ❌ Can't scale when you hire help | ✅ Multiple agents can login |
| ❌ No message templates | ✅ Pre-approved templates |

**My insight:**  
Personal WhatsApp = **bottleneck**. You're the only one who can reply.  
Business API = **scale** (hire help later, they login with their phone).

---

### WhatsApp Business API Setup (Meta Cloud API)**

```python
# /api/whatsapp/setup (one-time)
@app.post("/api/whatsapp/setup")
async def setup_whatsapp(payload: WhatsAppSetup):
    # 1. Verify webhook (Meta calls you)
    webhook_url = "https://your-agency.com/api/whatsapp/webhook"
    
    # 2. Register phone number
    response = meta_api.register_phone(
        display_name="Travel Agency OS",
        pin="123456"  # Verify via SMS
    )
    
    # 3. Upload message templates (pre-approved by Meta)
    templates = [
        {
            "name": "enquiry_received",
            "category": "ALERT_UPDATE",
            "language": "en",
            "components": [{
                "type": "body",
                "text": "Hi {{1}}, we received your enquiry about {{2}}. Agent will reply in {{3}} mins."
            }]
        },
        # ... more templates
    ]
    for t in templates:
        meta_api.create_template(t)
    
    # 4. Generate QR code (customers scan → chat)
    qr_code_url = meta_api.generate_qr_code()
    
    return {
        "status": "ready",
        "qr_code_url": qr_code_url,
        "phone_number": response['display_phone_number']
    }
```

**My insight:**  
`pin="123456"` — Meta sends SMS to verify you own the phone.  
`qr_code_url` — print this, stick on office wall, customers scan.

---

### Webhook: Receiving Messages (The Magic)**

```python
# /api/whatsapp/webhook (Meta calls this)
@app.post("/api/whatsapp/webhook")
async def whatsapp_webhook(payload: dict):
    # 1. Verify signature (security)
    if not verify_meta_signature(payload):
        return {"error": "Invalid signature"}, 401
    
    # 2. Extract message
    message = payload['messages'][0]
    from_number = message['from']  # "+919876543210"
    text = message['text']['body']
    message_id = message['id']
    
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
        "acquisition_source": "inbound_organic",
        "raw_text": text,
        "status": "RECEIVED"
    })
    
    # 5. Trigger AI analysis (async)
    spine_client.analyze_async(enquiry.id)
    
    # 6. Auto-reply (template)
    await send_whatsapp_template(
        to=from_number,
        template_name="enquiry_received",
        params=[customer.first_name, "your trip", "30"]
    )
    
    # 7. Alert YOU (notification)
    await notify_agent(
        severity="INFO",
        message=f"📩 New WhatsApp: {text[:50]}..."
    )
    
    return {"status": "ok"}
```

**My insight:**  
`verify_meta_signature` — Meta signs webhooks, verify or anyone can fake messages.  
`first_name: "Unknown"` — update later when they say "I'm Ravi."

---

### Sending Messages (Replies, Drafts)**

```python
# /api/whatsapp/send (your reply)
@app.post("/api/whatsapp/send")
async def send_whatsapp_message(payload: SendMessage):
    # 1. Format message (Markdown → WhatsApp format)
    text = payload.text
    text = convert_markdown_to_whatsapp(text)  # *bold*, _italic_
    
    # 2. Send via Meta API
    response = meta_api.send_message(
        to=payload.customer_phone,
        text=text,
        preview_url=True  # Show link preview
    )
    
    # 3. Log in communications table
    db.create_communication({
        "enquiry_id": payload.enquiry_id,
        "sender_type": "HUMAN_AGENT",
        "sender_id": "you",
        "recipient_type": "CUSTOMER",
        "recipient_id": payload.customer_id,
        "channel": "whatsapp",
        "body_text": text,
        "sent_at": datetime.now()
    })
    
    return {"message_id": response['messages'][0]['id']}
```

**My insight:**  
`preview_url=True` — if you send `http://localhost:3000/enquiry/eq-42`, shows preview.  
ALWAYS log in `communications` table — dispute evidence.

---

## 3. Google Calendar (Travel Dates Sync)**

### Why This Matters**

| Use Case | Without Calendar | With Calendar |
|----------|----------------|---------------|
| **"Ravi goes to Bali June 15"** | ❌ You forget, double-book | ✅ Calendar reminder 1 day before |
| **Agent availability** | ❌ You book meeting on travel day | ✅ Calendar blocks travel dates |
| **Vendor follow-up** | ❌ Forget to call hotel | ✅ Auto-reminder on check-in day |

**My insight:**  
Google Calendar = **your external brain**. Sync travel dates → get alerts.

---

### Google Calendar Integration (Simple)**

```python
# /api/calendar/sync (one-way: system → Google)
@app.post("/api/calendar/sync")
async def sync_to_google_calendar(booking_id: str):
    booking = db.get_booking(booking_id)
    
    # 1. Create event
    event = {
        "summary": f"🌴 {booking.customer_name} — Bali Trip",
        "start": {"date": booking.start_date},
        "end": {"date": booking.end_date},
        "description": f"Booking: {booking.booking_reference}\nValue: ₹{booking.total_value}",
        "location": booking.destination,
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 1440},  # 1 day before
                {"method": "email", "minutes": 60}  # 1 hour before
            ]
        }
    }
    
    # 2. Call Google Calendar API
    calendar_id = "your-agency@gmail.com"
    response = google_calendar.events().insert(
        calendarId=calendar_id,
        body=event
    ).execute()
    
    # 3. Save event ID (for updates/deletes)
    db.update_booking(booking_id, {
        "google_calendar_event_id": response['id']
    })
    
    return {"event_id": response['id']}
```

**My insight:**  
`reminders` — popup 1 day before = you call customer "Ready for Bali?"  
`description` — include booking reference, value (quick lookup).

---

## 4. CRM Import (Excel/CSV — Migrate Old Data)**

### Why This Matters**

You have 3 years of old customer data in Excel/Google Sheets.  
System is USELESS without it (can't check "Ravi's past trips").

### Simple CSV Import (Pandas)**

```python
# /api/import/customers (one-time migration)
@app.post("/api/import/customers")
async def import_customers(file: UploadFile):
    # 1. Read CSV/Excel
    df = pd.read_csv(file.file)  # or pd.read_excel()
    
    imported = 0
    errors = []
    
    for _, row in df.iterrows():
        try:
            # 2. Map columns (flexible)
            customer = {
                "first_name": row.get('First Name', 'Unknown'),
                "last_name": row.get('Last Name', ''),
                "email": row.get('Email', None),
                "phone_primary": row.get('Phone', None),
                "acquisition_source": "imported"
            }
            
            # 3. Validate (skip duplicates)
            if db.find_customer_by_phone(customer['phone_primary']):
                continue
            
            db.create_customer(customer)
            imported += 1
            
        except Exception as e:
            errors.append({"row": _, "error": str(e)})
    
    return {
        "imported": imported,
        "errors": errors,
        "total_rows": len(df)
    }
```

**My insight:**  
`pd.read_csv` — handles Excel too (`.xlsx`).  
Skip duplicates by phone — old data has many copies of same customer.

---

## 5. Integrations You Can Skip (For Now)**

| Integration | Why Skip | Alternative |
|--------------|-----------|-------------|
| **Zoho/QuickBooks** | Manual invoice works | Generate PDF, email to accountant |
| **Google Maps API** | Nice widget only | Customer tells you destination |
| **Stripe/Razorpay** | We don't collect | Customer pays via UPI/cheque |
| **Mailchimp** | Manual comms ok | WhatsApp broadcast (free) |
| **Slack/Discord** | You're solo, no team | WhatsApp groups |

**My insight:**  
Every integration you SKIP = **10-20 hours saved**.  
Add them LATER if they save you >5h/month.

---

## 6. Current State vs Integrations Model**

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| WhatsApp API | None | Business API + webhook + templates |
| Calendar sync | None | Google Calendar (travel dates) |
| CRM import | None | CSV/Excel → PostgreSQL |
| Invoice software | None | SKIP — manual PDF ok |
| Payment gateway | SKIP | No collection |

---

## 7. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| WhatsApp API now? | Yes / Later | **YES** — core workflow |
| Calendar sync? | Auto / Manual | **Manual** — add events yourself |
| CRM import? | Now / Later | **Now** — need old data |
| Invoice software? | Zoho / Manual | **Manual** — PDF + email |
| API keys storage? | `.env` / AWS Secrets | **`.env`** — solo dev |

---

## 8. Next Discussion: Onboarding**

Now that we know **WHAT connects**, we need to discuss: **How does a new agent learn?**

Key questions for next discussion:
1. **First login** — what does a new agent see? (tour?)
2. **Quick start guide** — "How to reply on WhatsApp in 3 steps"?
3. **Video tutorials** — Loom recordings for key workflows?
4. **Tooltip system** — in-app hints ("Click here to draft")?
5. **Solo dev reality** — will you EVER hire? (if not, skip onboarding)

---

**Next file:** `Docs/discussions/onboarding_2026-04-29.md`
