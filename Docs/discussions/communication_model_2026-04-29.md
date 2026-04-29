# Communication Model — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — after vendor model  
**Approach:** Independent analysis — ANOTHER MAJOR GAP, no comms tracking exists  

---

## 1. The Core Problem: Communication Doesn't Exist in the Schema**

### Current Schema State

Only these exist, all unrelated to comms tracking:
```json
// In StructuredRisk model
"message": "string",  // Risk description text
"short_message": "string"  // Badge text
```
```json
// In context_deconstruction_pipeline
"suggested_opening": "Mention we've drafted..."  // AI hint only
```

### Why This is a MAJOR Gap (First Principles)

The business description says:
> "they talk to and process diff. stuff with agents (travel agents not ai agents), **vendors**, **send drafts and other comms. to the buyers**"

**Communication is 50%+ of the actual work:**
1. **Agents send comms** to customers (drafts, confirmations, resolutions)
2. **Agents talk to vendors** (quotes, availability, negotiations)
3. **Customers reply** with feedback, changes, complaints
4. **System sends automated comms** (confirmations, reminders)
5. **Internal comms** (agent-to-agent, agent-to-manager)

The schema has **ZERO tracking** of any of this.

---

## 2. My Communication Entity Model**

### Core Communication Record**

```json
{
  "comm_id": "string (UUID)",
  "comm_type": "CUSTOMER_OUT | CUSTOMER_IN | VENDOR_OUT | VENDOR_IN | INTERNAL_NOTE | SYSTEM_AUTO",
  
  // Participants
  "enquiry_id": "string",  // Links to the enquiry
  "booking_id": "string | null",  // If about a specific booking
  "sender_type": "HUMAN_AGENT | CUSTOMER | VENDOR | SYSTEM",
  "sender_id": "string",  // agent_id, customer_id, vendor_id, or "system"
  "recipient_type": "HUMAN_AGENT | CUSTOMER | VENDOR | SYSTEM",
  "recipient_id": "string",
    
  // Channel & Format
  "channel": "whatsapp | email | telegram | wechat | voice_call | in_person | system",
  "format": "text | html | voice_note | image | pdf | video | mixed",
  "language": "string (ISO 639-1)",  // "en", "hi", "zh"
    
  // Content
  "subject": "string | null",  // Email subject, WhatsApp chat name
  "body_text": "string",  // Plain text content
  "body_html": "string | null",  // Rich text if email
  "body_summary": "string | null",  // AI-generated summary
    
  // Attachments
  "attachments": [
    {
      "attachment_id": "string",
      "type": "image | pdf | voice_note | video | voucher | itinerary",
      "url": "string",
      "filename": "string",
      "size_bytes": "integer"
    }
  ],
    
  // Metadata
  "sent_at": "string (ISO8601)",
  "delivered_at": "string | null",
  "read_at": "string | null",
  "replied_at": "string | null",
    
  // Processing
  "ai_assisted": "boolean",  // Was AI used to draft/generate?
  "ai_confidence": "number (0.0-1.0) | null",
  "human_edited": "boolean",  // Did human edit the AI draft?
  "template_used": "string | null",  // Template ID if used
    
  // Tracking
  "in_reply_to_comm_id": "string | null",  // Thread tracking
  "thread_id": "string",  // Groups related comms
  "is_internal": "boolean",  // Not sent to external parties
  "visibility": "agent_only | customer_visible | vendor_visible"
}
```

---

### Communication Thread Model**

```json
{
  "thread_id": "string (UUID)",
  "enquiry_id": "string",
  "thread_type": "ENQUIRY_DISCUSSION | BOOKING_SUPPORT | VENDOR_NEGOTIATION | INTERNAL_ESCALATION",
  "participants": [
    {
      "type": "HUMAN_AGENT | CUSTOMER | VENDOR",
      "id": "string",
      "role": "primary | cc | bcc"
    }
  ],
  "status": "ACTIVE | ARCHIVED | CLOSED",
  "comm_count": "integer",
  "first_comm_at": "string (ISO8601)",
  "last_comm_at": "string (ISO8601)",
  "subject_summary": "string"  // AI-generated thread summary
}
```

**My insight:**  
Threads should **auto-close** after 30 days of no activity. Re-opening creates a new thread linked to the old one.

---

## 3. Draft & Template System**

### AI-Assisted Draft Model**

```json
{
  "draft_id": "string (UUID)",
  "enquiry_id": "string",
  "draft_type": "ITINERARY_PRESENTATION | QUOTE | CONFIRMATION | APOLOGY | FOLLOW_UP | NEGOTIATION",
    
  // Content
  "generated_by": "AI_ENGINE | HUMAN_AGENT | TEMPLATE",
  "base_template_id": "string | null",
    
  // AI generation params
  "ai_prompt": "string | null",  // What was asked of the AI
  "ai_model_used": "string | null",  // "gpt-4", "claude", etc.
  "ai_temperature": "number | null",
    
  // Version control
  "version": "integer",  // Draft v1, v2, v3...
  "content_current": "string",  // Latest version
  "content_history": [
    {
      "version": 1,
      "content": "string",
      "edited_by": "agent_id | AI",
      "edited_at": "string (ISO8601)",
      "change_summary": "Initial AI draft"
    },
    {
      "version": 2,
      "content": "string",
      "edited_by": "agent_id",
      "edited_at": "string (ISO8601)",
      "change_summary": "Added budget breakdown, softened tone"
    }
  ],
    
  // Quality
  "tone": "FORMAL | CASUAL | FRIENDLY | APOLOGETIC | URGENT",
  "language": "string",
  "personalization_score": "number (0.0-1.0)",  // How personalized vs template?
    
  // State
  "status": "DRAFTING | READY_TO_SEND | SENT | REJECTED | ARCHIVED",
  "approved_by_agent_id": "string | null",
  "sent_at": "string | null",
  "sent_comm_id": "string | null"  // Links to Communication record
}
```

**My insight:**  
`personalization_score` should be **computed**. Low scores (<0.3) mean "too templated, add customer-specific details."

---

### Template Library Model**

```json
{
  "template_id": "string (UUID)",
  "template_type": "FOLLOW_UP | QUOTE | APOLOGY | CONFIRMATION | NEGOTIATION | THANK_YOU",
  "name": "string",  // "Standard Bali Quote - Family"
  "description": "string | null",
    
  // Scope
  "applicable_for": {
    "enquiry_types": ["NEW_TOUR", "IN_PROGRESS_ISSUE"],
    "trip_types": ["family", "leisure"],
    "customer_segments": ["STANDARD", "VIP"],
    "languages": ["en", "hi"]
  },
    
  // Content
  "subject_template": "string",  // "Your {destination} itinerary is ready!"
  "body_template": "string",  // Supports {customer_name}, {destination}, etc.
  "tone": "FORMAL | CASUAL | FRIENDLY | APOLOGETIC",
    
  // Variables
  "available_variables": ["customer_name", "destination", "dates", "budget", "agent_name"],
  "required_variables": ["customer_name", "destination"],
    
  // Usage
  "usage_count": "integer",
  "last_used_at": "string (ISO8601) | null",
  "created_by_agent_id": "string",
  "is_active": "boolean",
  "is_system_template": "boolean"  // System-provided vs user-created
}
```

**My insight:**  
Templates should **auto-suggest** based on enquiry type + trip type + customer segment.  
VIP customers should have **dedicated templates** with personalized touches.

---

## 4. Communication Flow Patterns**

### Pattern 1: New Tour Enquiry Response**

```
Customer sends enquiry (WhatsApp)
  └─ System creates Communication record (CUSTOMER_IN)
       └─ AI analyzes, creates summary
            └─ Agent reviews, clicks "Draft Response"
                 └─ AI generates draft (tone = CASUAL for leisure, FORMAL for corporate)
                      └─ Agent edits draft (human_edited = true)
                           └─ Agent clicks "Send"
                                └─ System creates Communication record (CUSTOMER_OUT)
                                     └─ Updates enquiry stage to PRESENTED
```

---

### Pattern 2: Vendor Quote Request**

```
Agent needs hotel quote (Bali, family of 4, June 15-20)
  └─ Agent clicks "Request Quote from Vendors"
       └─ System shows preferred vendors (vendor_tier = PREFERRED)
            └─ Agent selects 3 vendors, clicks "Send Requests"
                 └─ AI generates 3 similar drafts (tone = PROFESSIONAL)
                      └─ System sends via vendor's preferred channel (email for hotels, WhatsApp for local guides)
                           └─ Creates 3 Communication records (VENDOR_OUT)
                                └─ Sets reminder: "Follow up in 24h if no response"
```

---

### Pattern 3: Complaint Resolution**

```
Customer sends complaint (email)
  └─ System creates Communication record (CUSTOMER_IN, thread_type = BOOKING_SUPPORT)
       └─ AI analyzes sentiment, urgency = HIGH
            └─ Agent assigned (seniority >= SENIOR due to complaint)
                 └─ Agent contacts vendor (VENDOR_OUT): "Why was room not ready?"
                      └─ Vendor replies (VENDOR_IN): "Overbooked, upgrading to suite"
                           └─ Agent drafts apology + solution (CUSTOMER_OUT, tone = APOLOGETIC)
                                └─ Manager approves (approval_required = true for complaints)
                                     └─ Sent to customer
                                          └─ System tracks: complaint_resolved = true
```

---

## 5. AI Assistance in Communications**

### Where AI Helps (My Analysis)**

| Task | AI Role | Human Role | Confidence |
|------|----------|------------|------------|
| **Draft generation** | Writes first version | Edits, personalizes | High — structured data available |
| **Tone adjustment** | Converts formal ↔ casual | Sets tone preference | High — clear rules |
| **Translation** | Translates to customer's language | Reviews for nuance | Medium — cultural context |
| **Summarization** | Summarizes long threads | Reviews for accuracy | High — extractive |
| **Personalization** | Inserts customer details | Verifies accuracy | Medium — data dependent |
| **Follow-up reminders** | Suggests when to follow up | Decides yes/no | High — time-based |
| **Sentiment analysis** | Detects urgency/anger | Decides escalation | Medium — cultural nuance |

### Where AI Should NOT Touch (My Recommendation)**

| Task | Why Not |
|------|---------|
| **Final approval for VIP comms** | VIPs need human touch |
| **Apology drafting for serious complaints** | Legal/compliance risk |
| **Refund/cancellation confirmations** | Financial/contract implications |
| **Negotiation with high-value vendors** | Relationship nuances |

---

## 6. Communication Analytics**

### Metrics to Track**

```json
{
  "comm_analytics": {
    // Speed
    "average_first_response_hours": "number",
    "average_resolution_hours": "number",
    "sla_breach_count": "integer",
      
    // Volume
    "total_comms_sent": "integer",
    "total_comms_received": "integer",
    "by_channel": {
      "whatsapp": { "sent": 120, "received": 85 },
      "email": { "sent": 45, "received": 32 }
    },
      
    // AI assistance
    "ai_drafts_generated": "integer",
    "ai_drafts_edited_percent": "number (0.0-100.0)",  // How often humans edit AI drafts
    "ai_tone_adjustments": "integer",
      
    // Quality
    "customer_satisfaction_with_comms": "number (1.0-5.0)",
    "comms_related_complaints": "integer",
      
    // Templates
    "template_usage_count": "integer",
    "most_used_template_id": "string | null"
  }
}
```

**My insight:**  
`ai_drafts_edited_percent > 70%` means **templates need updating** or **AI prompt needs tuning**.

---

## 7. Current Schema vs Communication Model**

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Communication record | None | `Communication` entity with full tracking |
| Thread tracking | None | `Thread` entity grouping related comms |
| Draft storage | None | `Draft` entity with version control |
| Templates | None | `Template` library with variables |
| AI assistance | None | `ai_assisted`, `ai_confidence`, `human_edited` |
| Attachments | `SourceEnvelope.attachments` (inbound only) | Expanded to all comms, outbound too |
| Channel tracking | `source_type` (inbound only) | `channel` for ALL comms |
| Internal notes | None | `is_internal = true` flag |

---

## 8. Decisions Needed**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Communication as top-level entity? | Yes / No | **YES** — it's 50%+ of the work |
| Thread model mandatory? | Yes / Optional | **Optional** — simple enquiries may not need threads |
| AI draft auto-save? | Yes / No | **YES** — version control for drafts |
| Template library scope? | System only / Agents can create | **Both** — system provides base, agents customize |
| Internal notes separate? | Yes / is_internal flag | **is_internal flag** — simpler, one model |
| Auto-close threads? | Yes / No | **YES** — 30 days inactivity |

---

## 9. Next Discussion: Booking Model**

Now that we know:
- **Enquiry types** (new tour, in-progress issue, post-trip)
- **Channels** (WhatsApp, Telegram, WeChat, email, etc.)
- **Customer model** (individual vs corporate, VIP, health score)
- **Human Agent model** (skills, workload, performance)
- **Vendor model** (types, contracts, performance)
- **Communication model** (comms tracking, drafts, templates)

We need to discuss: **What actually gets booked?**

Key questions for next discussion:
1. Booking as entity — what fields? (status, dates, value, payments)
2. Booking vs Enquiry relationship — one-to-one? one-to-many?
3. Booking items — flights, hotels, activities, insurance?
4. Payment tracking — installments, EMI, refunds?
5. Voucher/confirmation management?
6. Booking modifications — change history, who changed what?
7. Cancellation/refund workflow?

---

**Next file:** `Docs/discussions/booking_model_2026-04-29.md`
