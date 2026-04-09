# Research: Integration Architecture

**Status**: 🔴 High Priority - Blocking implementation phase  
**Topic ID**: 1  
**Parent**: [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md)  
**Last Updated**: 2026-04-09

---

## Quick Summary

**What**: How the AI pipeline connects to real-world systems  
**Why**: Core AI is solid, but it needs to actually *do* things  
**Scope**: WhatsApp, booking APIs, CRMs, payments, documents  
**Status**: Initial research phase

---

## The Core Question

The Notebooks 01-03 define the "brain." But the brain needs:
- **Eyes/ears**: To receive customer messages (WhatsApp, email)
- **Memory**: To store data (database, files)
- **Voice**: To respond to customers (WhatsApp, email)
- **Hands**: To book things (hotel APIs, flight APIs)
- **Wallet**: To process payments

This doc explores the options.

---

## 1. WhatsApp Integration (Primary Channel)

### The Problem
Travel agencies in India run on WhatsApp. Not email. Not phone. WhatsApp.

### Options

| Option | Pros | Cons | Cost | Complexity |
|--------|------|------|------|------------|
| **WhatsApp Business API** | Official, reliable, rich features | Needs Meta approval, business verification | ~$0.005/message | Medium |
| **WhatsApp Cloud API** | Same as above, hosted by Meta | Same approval process | ~$0.005/message | Medium |
| **Third-party providers (Twilio, MessageBird)** | Easier setup, handles Meta relationship | Additional cost layer | ~$0.008/message | Low |
| **Unofficial libraries (yowsup, etc.)** | Free, no approval | Against ToS, can be banned, unreliable | Free | High risk |

### Recommendation
**Twilio WhatsApp Business API** for MVP

**Why**:
- Handles Meta relationship & approval
- Good Python SDK
- Reliable
- Cost is acceptable (~₹0.40/message at scale)

**Process**:
1. Apply for WhatsApp Business Account via Twilio
2. Get Facebook Business Manager verified
3. Use Twilio Python SDK for send/receive
4. Webhook for incoming messages

### Open Questions
- [ ] Approval timeline (2-4 weeks?)
- [ ] Phone number requirements (dedicated vs existing)
- [ ] Message template approval for outbound
- [ ] Rate limits

---

## 2. Hotel & Flight Booking APIs

### The Problem
System needs to check availability, get prices, maybe even book.

### Options

#### Hotel APIs

| Provider | Coverage | API Quality | Cost | Notes |
|----------|----------|-------------|------|-------|
| **Booking.com Affiliate API** | Global, massive | Good | Commission-based | Read-only, good for search |
| **Expedia Rapid API** | Global | Good | Commission | Read-only |
| **Agoda API** | Asia strong | Medium | Commission | Read-only |
| **Hotelbeds** | B2B focused | Good | Wholesale rates | Need travel agency license |
| **Direct hotel chains** (Marriott, etc.) | Limited to chain | Varies | Direct contract | High volume needed |
| **MakeMyTrip API** | India focused | Unknown | Unknown | Need partnership |

#### Flight APIs

| Provider | Coverage | API Quality | Cost | Notes |
|----------|----------|-------------|------|-------|
| **Amadeus** | Global | Excellent | Per query + transaction | Industry standard, expensive |
| **Sabre** | Global | Excellent | Per query + transaction | Amadeus competitor |
| **Travelport** | Global | Good | Per query | Another GDS |
| **Skyscanner API** | Global search | Good | Commission | Search only, no booking |
| **Kiwi.com API** | Aggregator | Good | Commission | Good for small players |
| **Direct airlines** | Single airline | Varies | Direct | Need individual integrations |

### Recommendation

**Phase 1 (MVP)**: No direct booking APIs
- Use Booking.com API for price/availability check only
- Agent manually books via existing relationships
- System generates quote, agent executes

**Phase 2 (Scale)**: Integration with 1-2 preferred suppliers
- Partner with Hotelbeds or regional consolidator
- Direct API for top 20 hotels used by agencies
- Commission-based model

**Rationale**:
- Booking APIs are expensive and complex
- Agencies already have relationships
- Don't want to become OTA, want to enable agencies

### Open Questions
- [ ] What's the cost of Amadeus for 1000 queries/month?
- [ ] Can we get Hotelbeds access with small volume?
- [ ] What APIs do Indian agencies actually want?

---

## 3. CRM Integration

### The Problem
Agencies have customer data somewhere. Usually Excel. Sometimes nothing. Sometimes basic CRM.

### Options

| CRM | Market Share (India) | API | Notes |
|-----|----------------------|-----|-------|
| **Excel/Google Sheets** | 60%+ | Google Sheets API | Default assumption |
| **Zoho CRM** | 20% | Good REST API | Popular with SMBs |
| **Salesforce** | 10% | Excellent API | Enterprise only |
| **HubSpot** | 5% | Good API | Growing |
| **Freshsales** | 3% | Good API | Indian company |
| **Custom/None** | 2% | N/A | Need full system |

### Recommendation

**Primary**: Google Sheets integration
**Secondary**: Zoho CRM integration

**Why**:
- Most agencies use Excel/Sheets
- Sheets API is easy
- Can import/export
- Zoho is #2 in India

**Approach**:
- System has its own database (canonical source)
- Sync to Sheets for agency convenience
- Two-way sync: System updates Sheets, Sheets can update System

### Open Questions
- [ ] How many agencies actually use CRM vs Excel?
- [ ] What's the sync frequency? (Real-time vs daily)
- [ ] Conflict resolution (if both change)

---

## 4. Payment Processing

### The Problem
Agencies need to collect money. System should help track, maybe facilitate.

### Options

| Gateway | India Support | API | Cost | Notes |
|---------|---------------|-----|------|-------|
| **Razorpay** | Excellent | Excellent | 2% + GST | Indian leader |
| **Stripe** | Good | Excellent | 2-3% | Global standard |
| **PayU** | Good | Good | 2% + GST | Indian competitor |
| **Instamojo** | Good | Good | 2% + ₹3 | Good for small |
| **Bank transfers/UPI** | Universal | Manual | Free | Still dominant in B2B |

### Recommendation

**Primary**: Razorpay
**Secondary**: UPI tracking

**Why**:
- Razorpay is Indian leader
- Excellent API
- Supports UPI, cards, netbanking
- Good developer experience

**Scope**:
- Phase 1: Track payments (manual entry of bank/UPI payments)
- Phase 2: Razorpay integration for card payments
- Phase 3: Full payment facilitation

### Open Questions
- [ ] Do agencies want system to collect money or just track?
- [ ] Razorpay vs PayU cost comparison at scale
- [ ] UPI reconciliation automation

---

## 5. Document Storage

### The Problem
Passport scans, tickets, hotel vouchers, insurance docs. Need secure storage.

### Options

| Storage | Security | Cost | India Region | Notes |
|---------|----------|------|--------------|-------|
| **AWS S3** | Excellent | $0.023/GB | Mumbai | Industry standard |
| **Google Cloud Storage** | Excellent | $0.020/GB | Mumbai | Slightly cheaper |
| **Azure Blob** | Excellent | $0.018/GB | Pune/Pune 2 | Cheapest |
| **DigitalOcean Spaces** | Good | $0.020/GB | Bangalore | Simpler |
| **Local storage** | Varies | Hardware cost | Local | Compliance issues |

### Recommendation

**AWS S3 with encryption**

**Why**:
- Industry standard
- Excellent security features
- Mumbai region (data sovereignty)
- Glacier for old backups

**Configuration**:
- Server-side encryption (AES-256)
- Bucket in Mumbai region
- Lifecycle: Move to Glacier after 1 year
- Access logging
- IAM roles (no hardcoded credentials)

### Open Questions
- [ ] Estimated storage per customer (passports, tickets, etc.)
- [ ] Retention policy (how long keep docs after trip)
- [ ] GDPR/data localization requirements

---

## 6. Email/SMS Gateway

### The Problem
Backup communication channel. Also for document delivery.

### Options

| Provider | Email | SMS | India Pricing | Notes |
|----------|-------|-----|---------------|-------|
| **SendGrid** | Excellent | No | $0.0001/email | Industry standard |
| **AWS SES** | Excellent | Via SNS | $0.0001/email | Cheapest |
| **Twilio** | Via SendGrid | Excellent | ₹0.20-0.50/SMS | Unified with WhatsApp |
| **MSG91** | No | Excellent | ₹0.13-0.18/SMS | Indian provider |
| **Exotel** | No | Excellent | ₹0.15-0.25/SMS | Indian, voice too |

### Recommendation

**Email**: AWS SES
**SMS**: MSG91 (backup)

**Why**:
- SES is cheapest for email
- MSG91 is Indian (better delivery, pricing)
- Keep Twilio just for WhatsApp

### Open Questions
- [ ] Do we need SMS or is WhatsApp enough?
- [ ] Email deliverability in India (Gmail filters)

---

## 7. Webhooks & Event Infrastructure

### The Problem
System needs to receive events: incoming WhatsApp, booking confirmations, payment webhooks.

### Options

| Approach | Complexity | Reliability | Cost |
|----------|------------|-------------|------|
| **AWS API Gateway + Lambda** | Medium | High | Pay per use |
| **FastAPI/Flask on VPS** | Low | Medium | Fixed cost |
| **Cloudflare Workers** | Low | High | Pay per use |
| **Ngrok (dev only)** | Very low | Low | Free/Paid |

### Recommendation

**FastAPI on VPS for MVP**
**AWS Lambda for scale**

**Why**:
- FastAPI is Python-native
- Easier to debug than Lambda
- Can migrate to Lambda later
- Use ngrok for development

### Architecture
```
WhatsApp Message
    ↓
Twilio Webhook
    ↓
FastAPI Endpoint (/webhook/whatsapp)
    ↓
Queue (Redis/RabbitMQ)
    ↓
Notebook 01 Processing
    ↓
Database Update
    ↓
Response Generation
    ↓
Twilio Send
```

---

## Integration Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRAVEL AGENCY AI COPILOT                           │
│                              Integration Layer                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   CUSTOMER       │  │     AGENT        │  │     SYSTEM       │          │
│  │   INTERFACE      │  │   INTERFACE      │  │   INTEGRATIONS   │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│  ┌────────▼─────────┐  ┌────────▼─────────┐  ┌────────▼─────────┐          │
│  │ WhatsApp         │  │ Web Dashboard    │  │ Booking APIs     │          │
│  │ (Twilio)         │  │ (React/Vue)      │  │ (Booking.com)    │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│  ┌────────▼─────────────────────▼─────────────────────▼─────────┐          │
│  │                    AI PIPELINE (Notebooks 01-03)              │          │
│  │  • Intake & Normalization                                   │          │
│  │  • Gap & Decision                                           │          │
│  │  • Session Strategy                                         │          │
│  └────────┬─────────────────────┬─────────────────────┬─────────┘          │
│           │                     │                     │                     │
│  ┌────────▼─────────┐  ┌────────▼─────────┐  ┌────────▼─────────┐          │
│  │ Data Storage     │  │ Document Store   │  │ Payment          │          │
│  │ (PostgreSQL)     │  │ (AWS S3)         │  │ (Razorpay)       │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Cost Estimates (Monthly, 1000 bookings)

| Component | Cost (USD) | Notes |
|-----------|------------|-------|
| WhatsApp (Twilio) | $200 | ~5000 messages |
| Database (RDS) | $50 | db.t3.micro |
| Document Storage (S3) | $10 | ~100GB |
| Email (SES) | $5 | ~5000 emails |
| Compute (VPS/Lambda) | $50 | Depending on load |
| **Total** | **~$315** | **~₹26,000** |

**Per booking**: ~$0.31 (₹26)

---

## Implementation Phases

### Phase 1: MVP (Month 1-2)
- ✅ WhatsApp send/receive (Twilio)
- ✅ Database (PostgreSQL)
- ✅ Document storage (S3)
- ✅ Basic web dashboard
- ❌ No booking APIs (manual)
- ❌ No payments (track only)

### Phase 2: Integration (Month 3-4)
- ✅ Booking.com API (search only)
- ✅ Razorpay (payments)
- ✅ Zoho CRM sync
- ✅ Email (SES)

### Phase 3: Scale (Month 5-6)
- ✅ Hotelbeds/partnership
- ✅ Advanced analytics
- ✅ Multi-channel (SMS backup)
- ✅ Mobile app

---

## Open Questions (To Research)

### WhatsApp
- [ ] Twilio approval timeline for India
- [ ] Message template requirements
- [ ] Phone number: new or port existing?

### Booking APIs
- [ ] Hotelbeds minimum volume requirements
- [ ] Booking.com affiliate program approval
- [ ] Amadeus cost for 1000 queries/month

### CRM
- [ ] Survey: % agencies using Excel vs CRM
- [ ] Google Sheets API rate limits

### Payments
- [ ] Razorpay vs PayU: feature comparison
- [ ] UPI reconciliation automation options

### Security
- [ ] PII handling requirements in India
- [ ] Data localization laws
- [ ] Travel industry compliance standards

---

## Next Actions

1. **Apply for Twilio WhatsApp** (start approval process)
2. **Set up AWS account** (S3, RDS, SES)
3. **Apply for Booking.com Affiliate** (read-only access)
4. **Survey 10 travel agents** (CRM usage, API needs)
5. **Spike: FastAPI webhook handler** (2-day prototype)

---

## References

- [Twilio WhatsApp Business API](https://www.twilio.com/whatsapp)
- [Booking.com Affiliate Program](https://www.booking.com/affiliate-program/v2.html)
- [Razorpay Documentation](https://razorpay.com/docs/)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)
- [Google Sheets API](https://developers.google.com/sheets/api)

---

## Related Topics

- [DATA_STRATEGY.md](DATA_STRATEGY.md) - Database design
- [SECURITY_AND_COMPLIANCE.md](SECURITY_AND_COMPLIANCE.md) - PII, encryption
- [LLM_STRATEGY.md](LLM_STRATEGY.md) - Model costs (add to total)
- [EXPLORATION_TOPICS.md](../EXPLORATION_TOPICS.md) - Master index

---

*Status: Initial research phase. Update as research progresses.*
