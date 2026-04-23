# Output Panel: UX/UI Deep Dive

> Every interaction state, edge case, and visual design decision

---

## Part 1: UX Philosophy

### The Output Challenge

**Problem:** Creating professional travel documents is complex and error-prone.

**User Goals:**
1. **Agent:** Generate quotes quickly, customize for customers, look professional
2. **Owner:** Ensure brand consistency, pricing accuracy, legal compliance
3. **Customer:** Clear, attractive documents that inspire confidence

**Design Principles:**

| Principle | Description | Application |
|-----------|-------------|------------|
| **Preview First** | Always show before finalizing | Live preview while editing |
| **Progressive Disclosure** | Start simple, reveal complexity | Basic quote → Advanced options |
| **Visual Hierarchy** | Guide eye to what matters | Price prominent, details secondary |
| **Brand Consistency** | Enforce professional appearance | Template-driven, non-customizable basics |
| **Speed Over Perfection** | Good enough now, perfect later | Quick generate, then refine |

---

## Part 2: Panel Layout

### 2.1 Default State

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WORKSPACE │ Thailand Honeymoon                                  │
│            │ Status: Ready to Book                        [Save] │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────────────────────────────────────────────┐  │
│  │   TRIP    │  │                                                   │  │
│  │           │  │              OUTPUT PANEL                         │  │
│  │  Details  │  │                                                   │  │
│  │           │  │  ┌─────────────────────────────────────────────┐  │  │
│  │           │  │  │                                             │  │  │
│  │           │  │  │         No bundles generated yet           │  │  │
│  │           │  │  │                                             │  │  │
│  │           │  │  │   [Generate Quote] [Generate Itinerary]   │  │  │
│  │           │  │  │                                             │  │  │
│  │           │  │  │   Create professional documents to send   │  │  │
│  │           │  │  │   to your customer                          │  │  │
│  │           │  │  │                                             │  │  │
│  │           │  │  └─────────────────────────────────────────────┘  │  │
│  │           │  │                                                   │  │
│  └───────────┘  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Bundle List State

```
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT PANEL                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Generated Bundles                                    [+ New]    │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                   │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │   │
│  │  │ 📄 Quote       │  │ 📋 Itinerary  │  │ 🎫 Vouchers   │    │   │
│  │  │                │  │                │  │                │    │   │
│  │  │ v1.2           │  │ v1.0           │  │ v1.0           │    │   │
│  │  │ Apr 23, 3:30pm │  │ Apr 23, 4:00pm │  │ Apr 24, 10am   │    │   │
│  │  │                │  │                │  │                │    │   │
│  │  │ [View] [Send]  │  │ [View] [Send]  │  │ [View] [Send]  │    │   │
│  │  └────────────────┘  └────────────────┘  └────────────────┘    │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Bundle Detail State

```
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT PANEL                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │ ← Back to Bundles                                    Actions   │      │
│  │                                                             │      │
│  │  ┌──────────────┐  ┌─────────────────────────────────┐    │      │
│  │  │              │  │                                 │    │      │
│  │  │  THAILAND    │  │  Quote v1.2                     │    │      │
│  │  │  HONEYMOON   │  │  Ready to send                   │    │      │
│  │  │  QUOTE       │  │  Generated 2 hours ago            │    │      │
│  │  │              │  │                                 │    │      │
│  │  │              │  │  [👁️ Preview] [✏️ Edit] [📤 Send]  │    │      │
│  │  │              │  │  [🔄 Regenerate] [📋 Duplicate]    │    │      │
│  │  └──────────────┘  └─────────────────────────────────┘    │      │
│  │                                                             │      │
│  │  ┌─────────────────────────────────────────────────────┐    │      │
│  │  │  Delivery Status                                     │    │      │
│  │  ├─────────────────────────────────────────────────────┤    │      │
│  │  │  ✅ Sent via WhatsApp  (2 hours ago)                 │    │      │
│  │  │     Opened by customer (1 hour ago)                  │    │      │
│  │  │  ✅ Sent via Email     (2 hours ago)                 │    │      │
│  │  │     Opened 2 times, clicked 1 link                   │    │      │
│  │  └─────────────────────────────────────────────────────┘    │      │
│  │                                                             │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Generation Flow

### 3.1 Generate Button → Type Selection

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Select Bundle Type                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  What would you like to generate?                                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📄 QUOTE                                                        │   │
│  │  Price quotation for customer approval                          │   │
│  │  Includes: Pricing breakdown, inclusions, payment terms        │   │
│  │                                                                 │   │
│  │  [Generate Quote]                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📋 ITINERARY                                                    │   │
│  │  Detailed day-by-day trip plan                                  │   │
│  │  Includes: Schedule, activities, timings, notes               │   │
│  │                                                                 │   │
│  │  [Generate Itinerary]                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🎫 VOUCHERS                                                     │   │
│  │  Individual booking vouchers                                   │   │
│  │  Includes: Flight, hotel, activity confirmations               │   │
│  │                                                                 │   │
│  │  [Generate Vouchers]                                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📄 INVOICE                                                     │   │
│  │  Final invoice for payment                                      │   │
│  │  Includes: Line items, taxes, payment instructions            │   │
│  │                                                                 │   │
│  │  [Generate Invoice]                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Cancel]                                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Generation Progress

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Generating Quote...                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │    ████████████████████████░░░░░░░░ 75%                       │   │
│  │                                                                  │   │
│  │    Gathering trip details... ✓                                   │   │
│  │    Fetching live pricing... ✓                                    │   │
│  │    Applying agency template... ✓                                │   │
│  │    Generating PDF... (in progress)                               │   │
│  │                                                                  │   │
│  │    This usually takes 2-3 seconds                               │   │
│  │                                                                  │   │
│  │    [Cancel Generation]                                          │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Generation Complete

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ✓ Quote Generated!                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Your quote is ready to review and send.                             │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │    [👁️ Preview Quote]  [📤 Send to Customer]  [✏️ Make Edits]    │   │
│  │                                                                  │   │
│  │    [Close]                                                       │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 4: Preview Interface

### 4.1 PDF Preview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Preview: Thailand Honeymoon Quote v1.2                     [✕ Close] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────────────────────────────────────────────┐    │   │
│  │  │                   TRAVEL AGENCY NAME                   │    │   │
│  │  │                                                            │    │   │
│  │  │  ✈️  THAILAND HONEYMOON QUOTE                            │    │   │
│  │  │                                                            │    │   │
│  │  │  ┌──────────────────────────────────────────────────┐    │    │   │
│  │  │  │  CUSTOMER:                                          │    │    │   │
│  │  │  │    John & Jane Doe                                  │    │    │   │
│  │  │  │                                                    │    │    │   │
│  │  │  │  TRIP DETAILS:                                     │    │    │   │
│  │  │  │    Destination: Thailand - Phuket + Krabi          │    │    │   │
│  │  │  │    Dates: June 15-22, 2026 (7 nights)              │    │    │   │
│  │  │  │    Travelers: 2 Adults                             │    │    │   │
│  │  │  │                                                    │    │    │   │
│  │  │  │  PRICING:                                          │    │    │   │
│  │  │  │    Package Cost:      ₹1,85,000                   │    │    │   │
│  │  │  │    Taxes & Fees:        ₹35,000                    │    │    │   │
│  │  │  │    ─────────────────────────────────              │    │    │   │
│  │  │  │    Total Amount:       ₹2,20,000                   │    │    │   │
│  │  │  │                                                    │    │    │   │
│  │  │  │  INCLUDES:                                         │    │    │   │
│  │  │  │    ✓ Round-trip flights (Mumbai-Phuket)           │    │    │   │
│  │  │  │    ✓ 5-Star accommodation (3 nights each)          │    │    │   │
│  │  │  │    ✓ Daily breakfast                               │    │    │   │
│  │  │  │    ✓ Airport transfers                              │    │    │
│  │  │  │    ✓ Island tours                                   │    │    │   │
│  │  │  │                                                    │    │    │   │
│  │  │  │  PAYMENT TERMS:                                    │    │    │   │
│  │  │  │    • 30% advance to confirm                         │    │    │   │
│  │  │  │    • Balance 30 days before travel                 │    │    │   │
│  │  │  │                                                    │    │    │   │
│  │  │  │  This quote is valid for 48 hours from issuance.   │    │    │   │
│  │  │  │                                                    │    │    │   │
│  │  │  │  For any queries, contact:                        │    │    │   │
│  │  │  │  📞 +91 98765 43210  |  ✉️ agent@agency.com          │    │    │   │
│  │  │  └──────────────────────────────────────────────────┘    │    │   │
│  │  │                                                            │    │   │
│  │  └────────────────────────────────────────────────────────┘    │   │
│  │                                                                  │   │
│  │  [← Prev]              Page 1 of 3              [Next →]          │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Download PDF] [Print] [Share Link] [Send to Customer]               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Preview Actions

| Action | Description | Use Case |
|--------|-------------|----------|
| **Download** | Save PDF locally | Archive, records |
| **Print** | Open print dialog | Physical copy |
| **Share Link** | Generate view link | Customer portal |
| **Send** | Trigger delivery flow | Email/WhatsApp |
| **Edit** | Open editor | Make changes |
| **Regenerate** | Create new version | Data changed |

---

## Part 5: Edit Interface

### 5.1 Edit Mode

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Edit Quote: Thailand Honeymoon v1.2                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌───────────────────────────────────────────────┐    │
│  │   SECTIONS  │  │  CONTENT EDITOR                             │    │
│  │             │  │                                               │    │
│  │  Header     │  │  ┌─────────────────────────────────────────┐  │    │
│  │  ✓ Customer │  │  │ Customer Name                              │  │    │
│  │  ✓ Trip     │  │  │ [John & Jane Doe              ]       │  │    │
│  │  ✓ Pricing  │  │  └─────────────────────────────────────────┘  │    │
│  │  ✓ Includes │  │                                               │    │
│  │  ✓ Terms    │  │  ┌─────────────────────────────────────────┐  │    │
│  │  ✓ Footer   │  │  │ Destination                               │  │    │
│  │             │  │  │ [Thailand - Phuket + Krabi        ]       │  │    │
│  │             │  │  └─────────────────────────────────────────┘  │    │
│  │             │  │                                               │    │
│  │             │  │  ┌─────────────────────────────────────────┐  │    │
│  │  [+ Custom] │  │  │ Package Cost                              │  │    │
│  │             │  │  │ [₹1,85,000                      ]       │  │    │
│  │             │  │  └─────────────────────────────────────────┘  │    │
│  │             │  │                                               │    │
│  │             │  │  [+ Add Field]                                  │    │
│  │             │  │                                               │    │
│  │             │  └───────────────────────────────────────────────┘    │
│  └─────────────┘                                                    │
│                                                                     │
│  [Cancel] [Save as New Version] [Replace Current]                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Inline Edit Options

| Field Type | Edit Options | Validation |
|------------|--------------|------------|
| **Text** | Inline edit, rich text | Length limits |
| **Number** | Number input, currency | Range validation |
| **Date** | Date picker | Format validation |
| **List** | Add/remove items | Min/max items |
| **Boolean** | Toggle | — |
| **Image** | Upload, select from library | Size/format limits |

---

## Part 6: Send/Delivery Interface

### 6.1 Send Dialog

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Send Quote to Customer                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  How would you like to send this quote?                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📱 WHATSAPP                                  [Recommended]     │   │
│  │                                                                     │   │
│  │  Send directly to customer's WhatsApp                            │   │
│  │                                                                     │   │
│  │  To: +91 98765 43210 (John Doe)                                  │   │
│  │                                                                     │   │
│  │  Message:                                                          │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ Hi! Your Thailand quote is ready. Total: ₹2,20,000 for    │ │   │
│  │  │ your honeymoon. Check the details and let me know if you   │ │   │
│  │  │ have any questions. 🏝️                                     │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                     │   │
│  │  [✏️ Customize Message]                                          │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ✉️ EMAIL                                                       │   │
│  │                                                                     │   │
│  │  Send via email with PDF attachment                              │   │
│  │                                                                     │   │
│  │  To: john.doe@email.com                                          │   │
│  │  Subject: ✈️ Your Thailand Honeymoon Quote                    │   │
│  │                                                                     │   │
│  │  [✏️ Customize Email]                                            │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🔗 SHARE LINK                                                 │   │
│  │                                                                     │   │
│  │  Generate a secure link for customer to view                     │   │
│  │                                                                     │   │
│  │  Link expires in: [7 days ▼]                                    │   │
│  │                                                                     │   │
│  │  [Generate Link] [Copy Link] [View Link]                         │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [Cancel] [Send Now]                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Delivery Status Tracking

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Delivery Status: Quote v1.2                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  📱 WhatsApp                                              ✓ Delivered│   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  Sent: Apr 23, 3:30 PM                                          │   │
│  │  Delivered: Apr 23, 3:31 PM                                     │   │
│  │  Read: Apr 23, 4:15 PM                                          │   │
│  │                                                                  │   │
│  │  [Resend] [View Message]                                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ✉️ Email                                                 ✓ Opened 2×│   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  Sent: Apr 23, 3:30 PM                                          │   │
│  │  Delivered: Apr 23, 3:31 PM                                     │   │
│  │  Opened: Apr 23, 4:00 PM, 4:30 PM                              │   │
│  │  Clicked: 1 link (Itinerary section)                            │   │
│  │                                                                  │   │
│  │  [Resend] [View Email] [Track Clicks]                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  🔗 Share Link                                           📊 12 Views│   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │  Created: Apr 23, 3:30 PM                                       │   │
│  │  Expires: Apr 30, 3:30 PM                                        │   │
│  │  Views: 12 unique, 3 returning                                  │   │
│  │  Avg time spent: 2:45 minutes                                    │   │
│  │                                                                  │   │
│  │  [Copy Link] [Extend Expiry] [View Analytics]                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 7: Template Management UI

### 7.1 Template Selection

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Choose Template                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Select a template for this quote:                                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ✅ Agency Default (Modern)                              (Active) │   │
│  │     Clean, professional design with agency branding            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ○ Premium (Gold)                                                 │   │
│  │     Elegant design for luxury packages                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ○ Minimalist (White)                                            │   │
│  │     Clean, minimal design with focus on content                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ○ Adventure (Colorful)                                          │   │
│  │     Vibrant design for adventure trips                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [+ Upload Custom Template]                                          │
│                                                                         │
│  [Use Selected] [Preview] [Cancel]                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Template Editor

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Template Editor: Agency Default                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌───────────────────────────────────────────────┐    │
│  │  COMPONENTS │  │  EDIT AREA                                    │    │
│  │             │  │                                               │    │
│  │  Header     │  │  ┌─────────────────────────────────────────┐  │    │
│  │  Logo       │  │  │ <div class="header">                      │  │    │
│  │  Title      │  │  │   <img src="{{agency.logo}}" />        │  │    │
│  │  Pricing    │  │  │   <h1>{{destination}} Quote</h1>        │  │    │
│  │  Itinerary  │  │  │ </div>                                  │  │    │
│  │  Terms      │  │  │                                         │  │    │
│  │  Footer     │  │  │                                         │  │    │
│  │             │  │  │                                         │  │    │
│  │  Styles     │  │  │                                         │  │    │
│  │             │  │  │                                         │  │    │
│  │  [+ Add]    │  │  └─────────────────────────────────────────┘  │    │
│  │             │  │                                               │    │
│  └─────────────┘  │  [Save] [Preview] [Cancel]                   │    │
│                   └───────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 8: Empty States & Edge Cases

### 8.1 No Trip Data

```
┌─────────────────────────────────────────────────────────────────────────┐
│  OUTPUT PANEL                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                   │   │
│  │          📋                                                     │   │
│  │   Can't generate documents yet                                  │   │
│  │                                                                   │   │
│  │   Trip details are incomplete. Please fill in:                  │   │
│  │                                                                   │   │
│  │   • Destination ✓                                              │   │
│  │   • Travel dates ✗                                             │   │
│  │   • Traveler count ✓                                            │   │
│  │   • Budget estimate ✗                                           │   │
│  │                                                                   │   │
│  │   [Go to Trip Details]                                          │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Generation Failed

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⚠️ Generation Failed                                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  We couldn't generate your quote. Please try again.                 │
│                                                                         │
│  Error: Pricing service unavailable                                  │
│                                                                         │
│  [Retry] [Contact Support] [Close]                                   │
│                                                                         │
│  If this persists, please contact support with reference ID:         │
│  ERR_BUNDLE_GEN_001                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.3 Expired Quote

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Quote v1.2                                       ⚠️ Expired 2 days ago │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  This quote has expired. Prices may have changed.                      │
│                                                                         │
│  Pricing was retrieved on Apr 21, 2026. Current prices may vary.      │
│                                                                         │
│  [Regenerate with Current Prices] [Archive Anyway]                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 9: Responsive Design

### 9.1 Desktop (1280px+)

| Element | Layout |
|---------|--------|
| **Panel** | Full width, side-by-side with other panels |
| **Preview** | Fixed width, centered |
| **Bundle Cards** | 3-column grid |
| **Editor** | Split pane (sections left, editor right) |

### 9.2 Tablet (768px - 1280px)

| Element | Layout |
|---------|--------|
| **Panel** | Full width |
| **Preview** | Responsive width |
| **Bundle Cards** | 2-column grid |
| **Editor** | Stacked (sections above editor) |

### 9.3 Mobile (<768px)

| Element | Layout |
|---------|--------|
| **Panel** | Full width, stacked |
| **Preview** | Full width, swipeable pages |
| **Bundle Cards** | Single column |
| **Editor** | Full width, collapsible sections |

---

## Part 10: Interaction Patterns

### 10.1 Quick Actions

| Action | Trigger | Result |
|--------|---------|--------|
| **Quick Generate** | Long-press Generate button | Skip type selection, use defaults |
| **Quick Send** | Drag bundle to customer | Open send dialog pre-filled |
| **Duplicate** | Right-click bundle | Create copy with new version |
| **Compare** | Select 2 bundles | Side-by-side comparison view |

### 10.2 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Cmd/Ctrl + N` | New bundle |
| `Cmd/Ctrl + P` | Preview selected bundle |
| `Cmd/Ctrl + E` | Edit selected bundle |
| `Cmd/Ctrl + S` | Save edits |
| `Cmd/Ctrl + Enter` | Generate (from edit mode) |
| `Esc` | Close preview/modal |

---

## Summary

**UX/UI Deep Dive Summary:**

| Aspect | Key Decisions |
|--------|--------------|
| **Layout** | Panel-based with collapsible sections |
| **Preview** | Always show before finalizing |
| **Generation** | Async with progress indicator |
| **Editing** | Inline with live preview |
| **Delivery** | Multi-channel with tracking |
| **Templates** | Selectable with preview |

**Design Principles Applied:**
1. Progressive disclosure — simple by default, powerful when needed
2. Visual hierarchy — price prominent, details available
3. Brand consistency — template-driven, enforced
4. Speed first — quick generate, refine later
5. Customer focus — preview their perspective

---

**Status:** UX/UI deep dive complete.
**Version:** 1.0
**Last Updated:** 2026-04-23

**Next:** Business Value Deep Dive (OUTPUT_03)
