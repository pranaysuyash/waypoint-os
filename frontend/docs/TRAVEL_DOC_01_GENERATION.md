# Travel Document Lifecycle — Generation Engine

> Research document for travel document generation, template engine, PDF pipeline, and India-specific document formatting.

---

## Key Questions

1. **How do we generate professional travel documents at scale?**
2. **What template engine supports conditional content and multi-language?**
3. **How do we produce print-quality PDFs with branding?**
4. **What India-specific formatting do travel documents require?**

---

## Research Areas

### Document Type Taxonomy

```typescript
type TravelDocumentType =
  // Customer-facing
  | "ITINERARY"          // day-by-day trip plan
  | "QUOTE"              // pricing proposal
  | "BOOKING_CONFIRMATION"
  | "VOUCHER"            // hotel/activity voucher
  | "TICKET"             // flight/rail ticket
  | "INVOICE"            // tax invoice (GST)
  | "RECEIPT"            // payment receipt
  | "TRAVEL_SUMMARY"     // quick reference card
  | "PACKING_LIST"       // weather-based packing guide
  | "EMERGENCY_CARD"     // contacts, embassy, insurance
  // Internal
  | "VENDOR_CONFIRMATION"
  | "COMMISSION_STATEMENT"
  | "RECONCILIATION_REPORT"
  // Legal
  | "BOOKING_CONTRACT"
  | "TERMS_CONDITIONS"
  | "INSURANCE_CERTIFICATE"
  | "VISA_APPLICATION";

interface DocumentGenerationRequest {
  type: TravelDocumentType;
  trip_id: string;
  booking_id: string | null;
  agency_id: string;

  // Template
  template_id: string | null;          // null = default
  locale: string;                      // "en-IN", "hi-IN"

  // Branding
  include_letterhead: boolean;
  include_watermark: boolean;
  color_scheme: string | null;

  // Content scope
  sections: string[];                  // which sections to include
  include_photos: boolean;
  include_maps: boolean;

  // Format
  output_format: "PDF" | "HTML" | "BOTH";
  quality: "SCREEN" | "PRINT";
}

// ── Document generation pipeline ──
// ┌─────────────────────────────────────────────────────┐
// │  Request → Template Selection → Data Binding         │
// │       → Conditional Sections → Branding              │
// │       → PDF Rendering → Quality Check                │
// │       → Storage → Delivery                           │
// └─────────────────────────────────────────────────────┘
```

### Template Engine

```typescript
interface DocumentTemplate {
  id: string;
  name: string;
  type: TravelDocumentType;
  version: number;

  // Layout
  html_template: string;               // Handlebars/Mustache template
  css_template: string;                 // page-specific styles
  page_size: "A4" | "LETTER" | "A5";
  orientation: "PORTRAIT" | "LANDSCAPE";
  margins: { top: number; right: number; bottom: number; left: number };

  // Sections
  sections: TemplateSection[];
  conditional_sections: ConditionalSection[];

  // Branding
  supports_branding: boolean;
  header_template: string | null;
  footer_template: string | null;
  logo_placeholder: string | null;

  // Variables
  required_variables: string[];
  optional_variables: string[];

  // Multi-language
  supported_locales: string[];
  locale_overrides: Record<string, Record<string, string>>;
}

interface TemplateSection {
  id: string;
  name: string;                        // "Flight Details", "Hotel Bookings"
  order: number;
  html: string;
  required: boolean;
}

interface ConditionalSection {
  id: string;
  condition: string;                   // "{{has_flights}} == true"
  section: TemplateSection;
}

// ── Itinerary template structure ──
// ┌─────────────────────────────────────────────────────┐
// │  ITINERARY TEMPLATE                                    │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ HEADER: Agency logo + name + contact          │   │
// │  └───────────────────────────────────────────────┘   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ TRIP OVERVIEW: Destination, dates, travelers  │   │
// │  └───────────────────────────────────────────────┘   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ DAY 1: [if:has_flights]                       │   │
// │  │   Flight: DEL → SIN (SG-101)                  │   │
// │  │   Transfer: Airport → Hotel                    │   │
// │  │   Check-in: Marina Bay Sands                  │   │
// │  │   Evening: Gardens by the Bay                 │   │
// │  │   [if:has_restaurant_reservation]             │   │
// │  │     Dinner: Lau Pa Sat 19:00                  │   │
// │  └───────────────────────────────────────────────┘   │
// │  ... (repeat per day)                                  │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ COST SUMMARY: Itemized with totals + GST      │   │
// │  └───────────────────────────────────────────────┘   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ TERMS & CONDITIONS: Cancellation, refund      │   │
// │  └───────────────────────────────────────────────┘   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ FOOTER: Emergency contacts, agency details    │   │
// │  └───────────────────────────────────────────────┘   │
// └─────────────────────────────────────────────────────┘
```

### PDF Generation Pipeline

```typescript
interface PDFRenderConfig {
  engine: "PUPPETEER" | "WKHTMLTOPDF" | "WEASYPRINT" | "PLAYWRIGHT";
  quality: "SCREEN" | "PRINT";
  dpi: number;                         // 72 (screen) or 300 (print)

  // Optimization
  compress_images: boolean;
  max_file_size_kb: number | null;
  embed_fonts: boolean;

  // Features
  enable_page_numbers: boolean;
  enable_table_of_contents: boolean;
  enable_header_footer: boolean;
  enable_watermark: boolean;
}

// ── India-specific: GST Invoice format ──
// ┌─────────────────────────────────────────────────────┐
// │  TAX INVOICE                                            │
// │  ┌────────────────────────┬────────────────────────┐ │
// │  │ [Agency Logo]          │ Invoice No: INV-2026-042│ │
// │  │ Agency Name            │ Date: 29-Apr-2026      │ │
// │  │ GSTIN: 27AADCA1234B1Z5 │ Due: 15-May-2026       │ │
// │  │ SAC Code: 9985         │                         │ │
// │  └────────────────────────┴────────────────────────┘ │
// │                                                         │
// │  Bill To:                                               │
// │  Priya Sharma, 2B HK Flat, Mumbai 400001               │
// │  GSTIN: (if business)                                  │
// │                                                         │
// │  ┌──────┬────────────────────┬──────┬─────┬───────┐   │
// │  │ #    │ Description         │ Qty  │Rate │Amount │   │
// │  ├──────┼────────────────────┼──────┼─────┼───────┤   │
// │  │ 1    │ SIN flight (SG-101)│ 2    │16K  │32,000 │   │
// │  │ 2    │ Hotel 5N           │ 1    │9K   │45,000 │   │
// │  │ 3    │ Sentosa tickets    │ 2    │3K   │6,000  │   │
// │  ├──────┼────────────────────┼──────┼─────┼───────┤   │
// │  │      │ Subtotal            │      │     │83,000 │   │
// │  │      │ CGST @ 2.5%        │      │     │2,075  │   │
// │  │      │ SGST @ 2.5%        │      │     │2,075  │   │
// │  │      │ TCS @ 5%           │      │     │4,150  │   │
// │  │      │ GRAND TOTAL        │      │     │91,300 │   │
// │  └──────┴────────────────────┴──────┴─────┴───────┘   │
// │                                                         │
// │  TCS Section 206C(1G): Collected on overseas package    │
// │  PAN: ABCPA1234A | TAN: MUMPA12345A                    │
// └─────────────────────────────────────────────────────────┘
```

### Batch Document Generation

```typescript
interface BatchGenerationRequest {
  trip_id: string;
  documents: TravelDocumentType[];
  format: "PDF" | "HTML";
  deliver_via: "PORTAL" | "EMAIL" | "WHATSAPP" | "ALL";
}

// Typical batch for a confirmed booking:
// 1. Booking Confirmation → customer (WhatsApp + email)
// 2. Hotel Voucher → customer (email)
// 3. Flight Ticket → customer (WhatsApp + email)
// 4. Activity Vouchers (one per activity) → customer (email)
// 5. GST Invoice → customer (email)
// 6. Travel Summary Card → customer (WhatsApp image)
// 7. Emergency Card → customer (WhatsApp image)
// 8. Vendor Confirmation → vendor (email)
// 9. Internal Booking Sheet → agent (portal)
// 10. Commission Statement → agent (portal)
```

---

## Open Problems

1. **Template maintenance** — Document templates change frequently (new regulations, updated terms, new branding). Need versioning and rollback capability.

2. **PDF rendering consistency** — Different PDF engines render HTML differently. Need to standardize on one engine and test across platforms.

3. **Unicode/font support** — Indian languages (Hindi, Tamil, Bengali) require specific fonts that must be embedded in PDFs. Missing fonts cause rendering failures.

4. **WhatsApp file size** — WhatsApp documents are limited to 64MB. Multi-page itineraries with photos may exceed this. Need smart compression.

---

## Next Steps

- [ ] Build template engine with Handlebars + conditional sections
- [ ] Implement PDF generation pipeline with Puppeteer
- [ ] Create GST-compliant invoice template
- [ ] Design batch generation workflow for booking confirmation
- [ ] Build template preview and version management
