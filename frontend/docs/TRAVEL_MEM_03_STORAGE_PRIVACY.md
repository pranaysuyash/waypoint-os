# Travel Photography & Memories — Storage, Privacy & Delivery

> Research document for photo storage architecture, India DPDP compliance, consent management, sharing mechanisms, and delivery workflows for travel agency memory products.

---

## Key Questions

1. **How do we store trip photos cost-effectively at scale?**
2. **What privacy and consent requirements apply under India DPDP Act?**
3. **How do travelers share and receive memory products?**
4. **What delivery workflows handle physical and digital products?**

---

## Research Areas

### Photo Storage Architecture

```typescript
interface PhotoStorageConfig {
  // Tiered storage
  tiers: {
    HOT: {
      description: "Active trips — photos in last 90 days";
      backend: "S3 Standard | GCP Standard";
      redundancy: "dual-region";
      cost_per_gb_month: number;           // ~$0.023
    };
    WARM: {
      description: "Completed trips — 90 days to 2 years";
      backend: "S3 Infrequent Access | GCP Nearline";
      redundancy: "single-region";
      cost_per_gb_month: number;           // ~$0.0125
    };
    COLD: {
      description: "Archive — older than 2 years";
      backend: "S3 Glacier | GCP Coldline";
      redundancy: "single-region";
      cost_per_gb_month: number;           // ~$0.004
      retrieval_delay: "1-12 hours";
    };
  };

  // Lifecycle rules
  lifecycle: {
    hot_to_warm_days: 90;                  // after trip end
    warm_to_cold_days: 730;                // 2 years
    delete_after_days: 2555;               // 7 years (legal hold)
    thumbnail_keep: "ALWAYS";              // thumbnails never go to cold
  };
}

interface StorageQuota {
  // Per-trip quota
  per_trip: {
    free_photos: 100;
    free_storage_mb: 500;
    max_photo_size_mb: 25;
    max_photos: 500;                       // premium
    max_storage_mb: 2500;                  // premium
  };

  // Agency-level quota
  agency: {
    included_storage_gb: 50;               // per month
    overage_cost_per_gb: number;           // ₹5/GB/month
    estimated_annual: {
      trips: 1200;
      photos_per_trip: 80;
      avg_photo_mb: 4;
      total_gb: 375;                       // ~375 GB/year
      estimated_cost_inr: 22500;           // after tiering
    };
  };
}

// ── Storage cost simulation ──
// ┌─────────────────────────────────────────────────────┐
// │  Photo Storage — Cost Analysis (1200 trips/year)       │
// │                                                       │
// │  Input:                                               │
// │  • 80 photos/trip avg × 4MB = 320MB/trip             │
// │  • 1200 trips = 384 GB raw                            │
// │                                                       │
// │  After optimization:                                  │
// │  • Auto-resize to max 2048px (saves ~40%)            │
// │  • WebP conversion (saves ~30% over JPEG)            │
// │  • Thumbnail generation (200px, 400px, 800px)        │
// │  • Effective: 230 GB originals + 18 GB thumbs        │
// │                                                       │
// │  Monthly cost (tiered):                               │
// │  Hot (90 days):   ~57 GB × $0.023 = $1.31           │
// │  Warm (rest):    ~173 GB × $0.0125 = $2.16          │
// │  Thumbnails:      ~18 GB × $0.023 = $0.41           │
// │  Monthly total:                        $3.88         │
// │  Annual total:                         ₹3,900        │
// │                                                       │
// │  vs. unoptimized: ₹22,500/year                       │
// │  Savings: 83% through tiering + compression          │
// └─────────────────────────────────────────────────────┘
```

### India DPDP Compliance

```typescript
interface PhotoConsentFlow {
  trip_id: string;
  traveler_id: string;

  // Consent dimensions
  consents: {
    // Core storage consent
    photo_storage: {
      granted: boolean;
      granted_at: string | null;
      purpose: "Provide memory products for your trip";
      retention: "7 years or until you request deletion";
      withdrawable: true;
    };

    // AI processing
    ai_processing: {
      granted: boolean;
      granted_at: string | null;
      purpose: "Auto-organize, caption, and select best photos";
      details: [
        "Scene recognition (landmark, food, group photo)",
        "Quality scoring for best-of selection",
        "Auto-captioning (no face recognition)",
      ];
      withdrawable: true;
    };

    // Face detection (separate, opt-in)
    face_detection: {
      granted: boolean;
      granted_at: string | null;
      purpose: "Group photos by people appearing in them";
      details: [
        "Face clustering (not identification)",
        "Person grouping within your trip only",
        "No cross-trip face matching",
        "No external face database comparison",
      ];
      biometric: true;                    // requires explicit DPDP consent
      withdrawable: true;
    };

    // Agency branding on shared content
    agency_branding: {
      granted: boolean;
      granted_at: string | null;
      purpose: "Add agency watermark to social-ready content";
      withdrawable: true;
    };

    // Photo sharing with other travelers
    group_sharing: {
      granted: boolean;
      granted_at: string | null;
      purpose: "Share your photos with other trip members";
      scope: "TRIP_MEMBERS_ONLY";
      withdrawable: true;
    };
  };
}

// ── Consent collection flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Photo Consent — WhatsApp + App Flow                   │
// │                                                       │
// │  Step 1: Trip booking confirmation                     │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  📸 Trip Photos & Memories                     │   │
// │  │                                               │   │
// │  │  We'd love to help preserve your trip          │   │
// │  │  memories! Here's what we'd like to do:        │   │
// │  │                                               │   │
// │  │  ✅ Store your trip photos (7 years)           │   │
// │  │  ✅ Auto-organize by day & location            │   │
// │  │  ✅ Create a digital memory book               │   │
// │  │  ☐ Group photos by people (optional)           │   │
// │  │  ☐ Add agency watermark on shares (optional)   │   │
// │  │                                               │   │
// │  │  [Accept All] [Customize] [Skip]               │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Step 2: Post-trip consent check                       │
// │  "Your Singapore photos are ready! Review your         │
// │   sharing preferences before we generate your          │
// │   memory book."                                       │
// │                                                       │
// │  Step 3: Ongoing — withdraw anytime                    │
// │  WhatsApp: "Send DELETE PHOTOS to remove all"         │
// │  App: Settings → Privacy → Photo Consent              │
// └─────────────────────────────────────────────────────┘
```

### Data Privacy Architecture

```typescript
interface PhotoPrivacyEngine {
  // PII stripping before storage
  stripExifPii(photo: Photo): Photo;

  // Access control
  checkAccess(photo_id: string, requester: string): AccessDecision;

  // Data subject rights
  handleDeletionRequest(traveler_id: string): DeletionResult;
  handleExportRequest(traveler_id: string): ExportResult;
}

interface AccessDecision {
  allowed: boolean;
  reason: string | null;
  conditions: {
    requires_consent: string[];           // which consents needed
    blurred_faces: boolean;               // show with faces blurred
    watermark: boolean;                   // add agency watermark
    expires_at: string | null;            // time-limited access
  };
}

// ── Privacy-first architecture ──
// ┌─────────────────────────────────────────────────────┐
// │  Photo Privacy Architecture                            │
// │                                                       │
// │  Upload pipeline:                                     │
// │  1. Client-side: strip GPS from EXIF (unless opted in)│
// │  2. Server: validate file type, scan for malware      │
// │  3. Storage: encrypt at rest (AES-256)                │
// │  4. Thumbnail: generate without EXIF                  │
// │  5. AI: process only if ai_processing consent granted │
// │                                                       │
// │  Access matrix:                                       │
// │  ┌──────────────────────────────────────────────┐    │
// │  │ Requester    | Own photos | Group | Agency    │    │
// │  │ ──────────────────────────────────────────── │    │
// │  │ Traveler     | Full       | If consent | No  │    │
// │  │ Co-traveler  | If consent | If consent | No  │    │
// │  │ Agent        | No*        | No*       | No*  │    │
// │  │ Agency admin | No*        | No*       | No*  │    │
// │  │                                               │    │
// │  │ * Agency can see:                             │    │
// │  │   - Photo count, storage used (metadata)      │    │
// │  │   - AI-generated summaries (no raw photos)    │    │
// │  │   - Memory book previews (customer-shared)    │    │
// │  └──────────────────────────────────────────────┘    │
// │                                                       │
// │  DPDP Section 8 compliance:                           │
// │  • Purpose limitation: photos only for stated purpose │
// │  • Data minimization: only requested data collected   │
// │  • Retention: auto-delete per lifecycle policy        │
// │  • Grievance officer: 72-hour response SLA           │
// └─────────────────────────────────────────────────────┘
```

### Delivery Workflows

```typescript
interface MemoryDeliveryEngine {
  // Digital delivery
  deliverDigital(product: DigitalProduct): DeliveryResult;

  // Physical delivery (India)
  deliverPhysical(product: PhysicalProduct): DeliveryResult;

  // WhatsApp-first delivery
  deliverViaWhatsApp(product: MemoryProduct, phone: string): DeliveryResult;
}

interface DeliveryResult {
  delivery_id: string;
  method: "WHATSAPP" | "EMAIL" | "APP_NOTIFICATION" | "COURIER";
  status: "QUEUED" | "SENT" | "DELIVERED" | "FAILED";
  tracking_url: string | null;
  estimated_delivery: string | null;
}

// ── Digital delivery (WhatsApp-first) ──
// ┌─────────────────────────────────────────────────────┐
// │  Memory Book Delivery — WhatsApp Flow                  │
// │                                                       │
// │  Agent triggers: "Generate memory book"                │
// │                                                       │
// │  Auto-step 1: Generate preview (30 seconds)            │
// │  → Agent sees preview in workbench                     │
// │  → Agent can edit/reorder/remove pages                 │
// │                                                       │
// │  Auto-step 2: Customer notification                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  📸 Your Singapore Trip Memory Book is ready!  │   │
// │  │                                               │   │
// │  │  [Preview Image — cover page]                  │   │
// │  │                                               │   │
// │  │  20 pages · 25 photos · 5 days of memories    │   │
// │  │                                               │   │
// │  │  [📥 Download PDF] [🔗 View Online]            │   │
// │  │ [📖 Order Printed Book — ₹1,500]              │   │
// │  │                                               │   │
// │  │  Share on: [WhatsApp] [Instagram] [Facebook]   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Auto-step 3: Follow-up (if no action in 3 days)      │
// │  "Your memory book expires in 7 days. Download now!"  │
// └─────────────────────────────────────────────────────┘

// ── Physical delivery (India) ──
// ┌─────────────────────────────────────────────────────┐
// │  Physical Product Delivery — India Logistics           │
// │                                                       │
// │  Print partners:                                      │
// │  • Printo (pan-India, 3-5 day delivery)              │
// │  • Vistaprint India (photo books, 5-7 days)          │
// │  • Canva Print (ship to 19000+ pincodes)             │
// │  • Local print shops (same city, 1-2 days)           │
// │                                                       │
// │  Order flow:                                          │
// │  1. Customer orders via WhatsApp/App                  │
// │  2. Agency sends print-ready PDF to vendor            │
// │  3. Vendor prints, packs, ships                       │
// │  4. Tracking number → customer + agency              │
// │  5. Delivery confirmation → trigger review request    │
// │                                                       │
// │  Pricing:                                             │
// │  • 20-page hardcover: ₹800 print cost                │
// │  • Agency charges: ₹1,500-2,000                      │
// │  • Shipping: ₹100-200 (included in price)            │
// │  • Agency margin: ₹500-1,000 per book                │
// │                                                       │
// │  Delivery tracking integration:                       │
// │  • Delhivery API for pan-India tracking               │
// │  • DTDC for express delivery                          │
// │  • India Post for remote pincodes                     │
// └─────────────────────────────────────────────────────┘
```

### WhatsApp-First Photo Workflow

```typescript
interface WhatsAppPhotoFlow {
  // Traveler sends photos via WhatsApp
  receivePhoto(from_phone: string, media_url: string, caption: string | null): void;

  // Agent can also send vendor photos
  agentUpload(trip_id: string, photos: File[]): void;

  // Bulk collection for group trips
  collectFromGroup(trip_id: string, phones: string[]): CollectionStatus;
}

interface CollectionStatus {
  trip_id: string;
  total_travelers: number;
  responded: number;
  photos_received: number;
  reminders_sent: number;
  collection_expires: string;              // 30 days post-trip
}

// ── WhatsApp photo collection ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp Photo Collection — Automated                 │
// │                                                       │
// │  Day 1 post-trip:                                     │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  📸 Welcome back from Singapore!               │   │
// │  │                                               │   │
// │  │  Share your trip photos and we'll create a     │   │
// │  │  beautiful memory book for you!                │   │
// │  │                                               │   │
// │  │  Just send photos here (up to 10 at a time)   │   │
// │  │  Or upload all at once: [Upload Link]          │   │
// │  │                                               │   │
// │  │  ⏰ Collection open for 30 days               │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Each photo received:                                  │
// │  "Got it! 📷 Marina Bay Sands — beautiful shot!"     │
// │  "That's photo 12/100. Keep them coming!"             │
// │                                                       │
// │  Day 3 (if < 10 photos):                               │
// │  "Only 5 photos so far — don't let those memories     │
// │   fade! Send your favorites today 📸"                 │
// │                                                       │
// │  Day 7: Auto-generate preview                         │
// │  "Your memory book preview is ready! 15 photos        │
// │   selected from 23 shared. [Preview] [Add More]"      │
// │                                                       │
// │  Day 14: Final reminder                                │
// │  "Last 2 weeks to add photos! Collection closes       │
// │   May 28. [Add Photos] [Generate Book Now]"           │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **WhatsApp media API limits** — WhatsApp Business API has rate limits on media downloads. Bulk photo collection (100+ photos) may need web upload fallback. Need hybrid flow: WhatsApp for convenience, web link for bulk.

2. **Print quality from mobile photos** — Mobile photos may be 12MP+ but poorly composed or lit. AI enhancement (super-resolution, denoising) before print-ready PDF generation is essential. Without it, printed books look amateurish.

3. **Cross-border photo regulations** — Some countries (UAE, Singapore) have strict photography laws. Destination-specific do-not-photograph lists should be included in trip briefings to prevent legal issues.

4. **Consent withdrawal cascade** — If a traveler withdraws photo storage consent mid-trip, what happens to photos already in group albums? Need per-photo consent tracking and cascading removal logic.

---

## Next Steps

- [ ] Design consent collection flow integrated with trip booking
- [ ] Build tiered storage with automatic lifecycle transitions
- [ ] Implement WhatsApp-first photo collection and delivery
- [ ] Create print vendor integration API for physical products
