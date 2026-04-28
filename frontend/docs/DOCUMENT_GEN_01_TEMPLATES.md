# Document Generation — Template Engine

> Research document for document template design, variable management, and template lifecycle.

---

## Key Questions

1. **What document types does a travel agency generate (itineraries, quotes, vouchers, tickets, invoices, contracts)?**
2. **How do we build a template engine that non-developers can maintain?**
3. **What variable/merge field system handles complex nested data (multi-day itinerary, multiple travelers)?**
4. **How do we support multi-brand and white-label document templates?**
5. **What's the template versioning and approval workflow?**

---

## Research Areas

### Document Type Taxonomy

```typescript
type DocumentType =
  // Customer-facing
  | 'itinerary'           // Day-by-day trip itinerary
  | 'quote'               // Price quotation for services
  | 'confirmation'        // Booking confirmation voucher
  | 'ticket'              // Flight, train, event ticket
  | 'invoice'             // Tax invoice / receipt
  | 'voucher'             // Hotel, activity, transfer voucher
  | 'travel_guide'        // Destination guide / tips
  | 'insurance_policy'    // Insurance policy document
  | 'visa_letter'         // Visa support letter
  | 'welcome_package'     // Pre-departure welcome document
  // Internal
  | 'booking_sheet'       // Internal booking details
  | 'supplier_voucher'    // Voucher sent to supplier
  | 'commission_report'   // Agent commission statement
  | 'ledger_report'       // Financial ledger
  // Contractual
  | 'service_agreement'   // Customer service agreement
  | 'terms_conditions'    // Terms and conditions
  | 'privacy_notice';     // Privacy policy acknowledgement

interface DocumentTemplate {
  templateId: string;
  name: string;
  type: DocumentType;
  brandId: string;
  version: number;
  status: 'draft' | 'active' | 'deprecated';
  sections: TemplateSection[];
  variables: TemplateVariable[];
  styling: TemplateStyle;
  format: 'pdf' | 'html' | 'docx' | 'email_html';
  createdAt: Date;
  updatedAt: Date;
  updatedBy: string;
}

interface TemplateSection {
  sectionId: string;
  name: string;
  type: 'header' | 'body' | 'table' | 'itinerary_day' | 'footer' | 'watermark';
  content: string;           // Template markup with variables
  conditional?: string;      // Show only if condition met
  repeatable?: boolean;      // Repeat for each item (e.g., each day)
  repeatSource?: string;     // Variable path to array
}

interface TemplateVariable {
  path: string;               // e.g., "trip.travelers[0].name"
  label: string;
  type: 'string' | 'number' | 'date' | 'currency' | 'image' | 'array' | 'object';
  format?: string;
  fallback?: string;          // If value is null
  required: boolean;
}
```

### Template Composition Patterns

**Itinerary template structure:**

```
┌─────────────────────────────────┐
│ HEADER (brand logo, trip title) │
├─────────────────────────────────┤
│ TRIP SUMMARY (dates, travelers) │
├─────────────────────────────────┤
│ DAY 1 ──────────────────────── │
│ │ Transfer │ Flight │ Hotel │  │
│ │ Details  │ Info   │ Info  │  │
│ ───────────────────────────────│
│ DAY 2 ──────────────────────── │
│ │ Activity │ Lunch  │ Free  │  │
│ ───────────────────────────────│
│ ... (repeat for each day) ...  │
├─────────────────────────────────┤
│ COST SUMMARY                    │
├─────────────────────────────────┤
│ TERMS & CONDITIONS              │
├─────────────────────────────────┤
│ FOOTER (contact, social links)  │
└─────────────────────────────────┘
```

### Multi-Brand Support

```typescript
interface BrandConfig {
  brandId: string;
  name: string;
  logo: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    text: string;
    background: string;
  };
  fonts: {
    heading: string;
    body: string;
  };
  footer: {
    address: string;
    phone: string;
    email: string;
    website: string;
    socialLinks: Record<string, string>;
  };
  legalEntity: string;
  gstNumber: string;
}
```

---

## Open Problems

1. **Complex nested data rendering** — An itinerary with 7 days, 3 segments per day, and 2 travelers creates deeply nested template rendering. Template engines struggle with this.

2. **Template editor for non-developers** — Agents should customize templates (add logos, change wording) without touching code. Need a visual template builder.

3. **Conditional sections** — "Include flight details only if flights are booked" — conditional logic in templates adds complexity. How to express conditions declaratively?

4. **Template preview with real data** — Agents need to preview documents with actual trip data before generating. This requires real-time template rendering in the browser.

5. **Localization in templates** — Same template needs to produce English, Hindi, and bilingual documents. Variable labels and static text need translation support.

---

## Next Steps

- [ ] Evaluate template engines (Handlebars, Nunjucks, React-to-PDF, Carbone)
- [ ] Design variable schema for itinerary data model
- [ ] Research visual template builders for non-technical users
- [ ] Study multi-brand document generation patterns
- [ ] Design template versioning and approval workflow
