# Travel Document Lifecycle — Delivery & Distribution

> Research document for multi-channel document delivery, WhatsApp document sharing, email delivery, portal library, and delivery tracking.

---

## Key Questions

1. **How do we deliver documents across channels (WhatsApp, email, portal, print)?**
2. **What are the constraints and best practices for WhatsApp document delivery?**
3. **How do we track document delivery and engagement?**
4. **How do we handle failed deliveries and retries?**

---

## Research Areas

### Multi-Channel Delivery Architecture

```typescript
interface DocumentDelivery {
  id: string;
  document_id: string;
  trip_id: string;
  booking_id: string | null;

  channels: DeliveryChannel[];
  status: DeliveryStatus;
  tracking: DeliveryTracking[];

  scheduled_at: string | null;
  sent_at: string | null;
  completed_at: string | null;
}

type DeliveryChannel = "WHATSAPP" | "EMAIL" | "PORTAL" | "PRINT" | "SMS_LINK";
type DeliveryStatus = "PENDING" | "SENDING" | "DELIVERED" | "FAILED" | "PARTIAL";

interface DeliveryTracking {
  channel: DeliveryChannel;
  events: DeliveryEvent[];
}

interface DeliveryEvent {
  event: "SENT" | "DELIVERED" | "OPENED" | "DOWNLOADED" | "FAILED" | "BOUNCED" | "EXPIRED";
  timestamp: string;
  details: string | null;
}

// ── Channel comparison ──
// ┌─────────────────────────────────────────────────────┐
// │  Channel    | Max Size  | Tracking    | Best For     │
// │  ─────────────────────────────────────────────────── │
// │  WhatsApp   | 64MB PDF  | Delivered ✓  | Quick share  │
// │  Email      | 25MB att  | Opens ✓      | Formal docs  │
// │  Portal     | Unlimited | Downloads ✓  | Archive      │
// │  Print      | Physical  | None         | Vouchers     │
// │  SMS Link   | URL only  | Clicks ✓     | Quick access │
// └─────────────────────────────────────────────────────┘
```

### WhatsApp Document Delivery

```typescript
interface WhatsAppDocumentDelivery {
  recipient_phone: string;
  document_type: "PDF" | "IMAGE";
  file_url: string;                    // pre-uploaded to WhatsApp media API
  filename: string;
  caption: string;                     // "📋 Your Singapore itinerary is ready!"
  message_template: string | null;     // pre-approved template for business API

  // WhatsApp Business API constraints
  max_file_size_mb: 64;
  supported_types: ["application/pdf", "image/jpeg", "image/png"];
}

// ── WhatsApp delivery flow ──
// ┌─────────────────────────────────────────────────────┐
// │  1. Generate PDF (compressed to < 5MB if possible)  │
// │  2. Upload to WhatsApp media API                    │
// │  3. Send document message via Business API          │
// │  4. Track: sent → delivered → read                  │
// │                                                       │
// │  For large documents (> 5MB):                        │
// │  → Split into sections (Day 1-3, Day 4-6)           │
// │  → Or send as portal link with preview image        │
// └─────────────────────────────────────────────────────┘
```

### Email Document Delivery

```typescript
interface EmailDocumentDelivery {
  to: string[];
  cc: string[];
  bcc: string[];

  subject: string;
  body_template: string;
  body_variables: Record<string, string>;

  attachments: EmailAttachment[];
  inline_images: { cid: string; url: string }[];

  // Tracking
  track_opens: boolean;
  track_clicks: boolean;
  read_receipt: boolean;
}

// ── Email templates for document delivery ──
// ┌─────────────────────────────────────────────────────┐
// │  Type              | Subject                        │
// │  ─────────────────────────────────────────────────── │
// │  Itinerary         | "Your {destination} itinerary"  │
// │  Booking confirm   | "Booking confirmed: {ref}"     │
// │  Invoice           | "Invoice #{number} from {agency}"│
// │  Voucher           | "Hotel voucher: {hotel_name}"  │
// │  Reminder          | "Travel docs for {destination}"│
// │  Post-trip         | "Thank you! Trip summary"      │
// └─────────────────────────────────────────────────────┘
```

### Customer Portal Document Library

```typescript
interface DocumentLibrary {
  customer_id: string;
  documents: LibraryDocument[];
  categories: DocumentCategory[];
}

interface LibraryDocument {
  id: string;
  type: TravelDocumentType;
  trip_id: string;
  filename: string;
  thumbnail_url: string;
  download_url: string;
  file_size_kb: number;
  page_count: number;

  // Status
  status: "CURRENT" | "SUPERSEDED" | "ARCHIVED";
  version: number;
  generated_at: string;
  expires_at: string | null;

  // Access
  download_count: number;
  last_downloaded_at: string | null;
  shared_via: DeliveryChannel[];
}

// ── Portal library view ──
// ┌─────────────────────────────────────────────────────┐
// │  My Documents                        [Search...]     │
// │                                                       │
// │  📂 Singapore Trip (Apr 2026)                        │
// │    📄 Itinerary v2        (Current)  [Download]      │
// │    📄 Booking Confirmation  (Current)  [Download]    │
// │    📄 Hotel Voucher        (Current)  [Download]     │
// │    📄 Flight Ticket        (Current)  [Download]     │
// │    📄 Invoice              (Current)  [Download]     │
// │                                                       │
// │  📂 Kerala Trip (Dec 2025) [Archived]                │
// │    📄 Itinerary v1        (Archived)  [Download]     │
// │    ...                                                │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **WhatsApp Business API approval** — Document messages require pre-approved templates. New document types need template approval (takes 24-48 hours).

2. **Email deliverability** — Travel document emails may land in spam (attachments trigger spam filters). Need proper SPF/DKIM/DMARC setup.

3. **Document versioning for customers** — When an itinerary is updated, customers may have the old version saved. Need clear "superseded" labeling.

4. **Offline access** — Travelers need documents without internet. Need pre-download prompts and offline-accessible portal (PWA).

---

## Next Steps

- [ ] Build multi-channel delivery engine with retry logic
- [ ] Implement WhatsApp document delivery via Business API
- [ ] Create customer portal document library
- [ ] Design delivery tracking dashboard
- [ ] Build automated re-delivery for failed deliveries
