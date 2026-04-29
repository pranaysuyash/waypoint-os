# WhatsApp Business Platform — Sales & Service Flows

> Research document for WhatsApp-native sales conversations, customer service automation, payment collection, and rich media delivery for travel agencies.

---

## Key Questions

1. **How do complete sales flows work on WhatsApp?**
2. **What customer service automations reduce agent workload?**
3. **How do we collect payments through WhatsApp?**
4. **What rich media delivery drives engagement?**

---

## Research Areas

### WhatsApp Sales Conversation Engine

```typescript
interface WhatsAppSalesEngine {
  // AI-assisted sales conversation
  conversation_flows: {
    // Inquiry to booking
    FULL_SALES: {
      steps: [
        {
          step: "INQUIRY";
          trigger: "Customer sends first message";
          customer_says: "Singapore trip chahiye June mein";
          ai_assist: {
            detected_destination: "Singapore";
            detected_dates: "June";
            suggested_response: "Ji bilkul! Singapore is beautiful in June. Kitne log hain aur budget kitna rakha hai?";
          };
        },
        {
          step: "QUALIFY";
          customer_says: "4 adults, 2 kids, around ₹2 lakh";
          ai_assist: {
            travelers: 6;
            budget: "₹2L";
            segment: "FAMILY_MID_RANGE";
            action: "Create draft in workbench + generate 2 proposals";
          };
        },
        {
          step: "PROPOSE";
          agent_sends: {
            type: "IMAGE";
            caption: "Singapore 5N Family — 2 options\n\nOption 1 (₹1.85L): 4-star + all meals + Universal + Gardens\nOption 2 (₹1.55L): 3-star + breakfast + same activities\n\nPDF attached with details 👇";
            attachments: ["proposal_image.png", "detailed_itinerary.pdf"];
          };
        },
        {
          step: "CLOSE";
          customer_says: "Option 1 achhi hai, book kar do";
          agent_sends: {
            type: "INTERACTIVE";
            buttons: [
              { id: "pay_50k", title: "Pay ₹50K Advance" },
              { id: "pay_full", title: "Pay Full ₹1.85L" },
              { id: "emi_plan", title: "EMI Plan (3 payments)" },
            ];
          };
        },
      ];
    };
  };
}

// ── AI-assisted sales conversation ──
// ┌─────────────────────────────────────────────────────┐
// │  Agent Assist — WhatsApp Sales                          │
// │  Conversation: +91-98XXX-XXXX (New inquiry)             │
// │                                                       │
// │  [Customer] "Singapore trip chahiye June mein,          │
// │   family ke saath. 4 adults, 2 kids."                   │
// │                                                       │
// │  ┌─ AI Analysis ───────────────────────────────────┐│
// │  │ Destination: Singapore (HIGH confidence)        ││
// │  │ Dates: June (flexible)                           ││
// │  │ Travelers: 6 (4 adults + 2 kids)                ││
// │  │ Budget: Not stated                               ││
// │  │ Language: Hinglish → use Hindi/English mix       ││
// │  │ Intent: STRONG (specific destination + dates)    ││
// │  │                                                 ││
// │  │ Customer match:                                 ││
// │  │ ❌ No existing CRM record (new customer)         ││
// │  │ ✅ Created: TRV-4521 (new lead)                  ││
// │  └─────────────────────────────────────────────────┘│
// │                                                       │
// │  Suggested reply:                                     │
// │  "Ji bilkul! Singapore is amazing in June.             │
// │   Budget kitna rakha hai? Aur dates fixed hain         │
// │   ya flexible?"                                        │
// │                                                       │
// │  Quick replies:                                       │
// │  [Use Suggested] [English Version] [Custom Reply]       │
// │                                                       │
// │  Auto-actions:                                        │
// │  ☐ Create draft in workbench                          │
// │  ☐ Generate 2 package proposals                       │
// │  ☐ Check June Singapore rates                          │
// └─────────────────────────────────────────────────────┘
```

### Customer Service Automation

```typescript
interface WhatsAppServiceAutomation {
  // Auto-response for common queries
  auto_responses: {
    VISA_STATUS: {
      trigger: "Customer asks about visa status";
      detection: ["visa status", "visa update", "visa ho gaya", "visa kitne din"];
      auto_reply: {
        template: "Your {destination} visa status:\n\n{traveler_name}: {status}\n\nExpected: {expected_date}";
        data_source: "Visa tracking system";
      };
    };

    ITINERARY_REQUEST: {
      trigger: "Customer asks for itinerary";
      detection: ["itinerary", "plan", "schedule", "kya plan hai", "kahan jana hai"];
      auto_reply: {
        action: "Send current itinerary PDF + summary text";
        include_map: true;
      };
    };

    PAYMENT_STATUS: {
      trigger: "Customer asks about payment";
      detection: ["payment", "balance", "kitna baki", "receipt", "invoice"];
      auto_reply: {
        template: "Payment status for {destination}:\n\nTotal: ₹{total}\nPaid: ₹{paid}\nBalance: ₹{balance}\nDue by: {due_date}\n\nPay now: {payment_link}";
      };
    };

    WEATHER_QUERY: {
      trigger: "Customer asks about weather";
      detection: ["weather", "mausam", "rain", "temperature", "kitni garmi"];
      auto_reply: {
        action: "Fetch real-time weather for trip destination";
        include_forecast: "5-day";
      };
    };
  };
}

// ── Auto-response examples ──
// ┌─────────────────────────────────────────────────────┐
// │  Customer: "Visa status kya hai Singapore ka?"          │
// │                                                       │
// │  Auto-detected: VISA_STATUS query                      │
// │  Auto-reply sent (no agent action needed):             │
// │                                                       │
// │  "Your Singapore visa status:                          │
// │                                                       │
// │  ✅ Rajesh Sharma: APPROVED (May 15)                   │
// │  ✅ Priya Sharma: APPROVED (May 15)                    │
// │  ⏳ Aarav Sharma: PROCESSING (applied May 10)          │
// │  ⏳ Anaya Sharma: PROCESSING (applied May 10)          │
// │                                                       │
// │  Expected: May 22 for remaining applicants              │
// │                                                       │
// │  Questions? Reply here or contact your agent."          │
// │                                                       │
// │  Agent notification: "Visa status auto-served to        │
// │  Sharma family. 2 visas still pending."                  │
// └─────────────────────────────────────────────────────┘
```

### WhatsApp Payment Collection

```typescript
interface WhatsAppPayments {
  // Payment methods available on WhatsApp
  payment_methods: {
    RAZORPAY_LINK: {
      description: "Send payment link in WhatsApp message";
      flow: "Customer clicks → opens Razorpay → pays → confirmation auto-sent";
      supports: ["UPI", "Credit Card", "Debit Card", "Net Banking", "EMI"];
      settlement: "T+1 to agency bank account";
    };

    WHATSAPP_PAY: {
      description: "Native WhatsApp Pay (UPI-based, India)";
      flow: "Customer clicks Pay → UPI payment → confirmation in chat";
      limit: "₹1L per transaction (UPI limit)";
      availability: "Android + iOS in India";
    };

    PAYMENT_PLAN: {
      description: "Split payment into installments";
      structure: {
        advance: { percentage: 25; trigger: "Booking confirmed" };
        second: { percentage: 25; trigger: "30 days before travel" };
        final: { percentage: 50; trigger: "7 days before travel" };
      };
      auto_reminder: true;
    };
  };
}

// ── WhatsApp payment flow ──
// ┌─────────────────────────────────────────────────────┐
// │  Payment Collection via WhatsApp                        │
// │                                                       │
// │  Agent sends:                                          │
// │  ┌───────────────────────────────────────────────┐   │
// │  │ "Great news, Sharma ji! Your Singapore trip     │   │
// │  │  is ready to confirm. 🎉                       │   │
// │  │                                               │   │
// │  │  💰 Payment: ₹1,85,000                        │   │
// │  │  Advance: ₹50,000 (to confirm booking)        │   │
// │  │  Balance: ₹1,35,000 (before May 15)            │   │
// │  │                                               │   │
// │  │  Choose payment option:"                       │   │
// │  │                                               │   │
// │  │  [💳 Pay ₹50K Advance]                         │   │
// │  │  [💳 Pay Full ₹1.85L]                          │   │
// │  │  [📅 EMI Plan (3 × ₹61,667)]                   │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Customer taps: [💳 Pay ₹50K Advance]                   │
// │  → Opens Razorpay checkout (UPI / Card / NetBanking)   │
// │  → Customer pays ₹50,000 via UPI                        │
// │  → Razorpay webhook → auto-confirmation                │
// │                                                       │
// │  Auto-sent to customer:                                │
// │  "✅ Payment received! ₹50,000 for Singapore trip.     │
// │   Booking confirmed! 🎉                                 │
// │   Balance ₹1,35,000 due by May 15.                     │
// │   Your itinerary will follow shortly."                  │
// │                                                       │
// │  Agent dashboard updated: Payment received, trip        │
// │  status → CONFIRMED                                    │
// └─────────────────────────────────────────────────────┘
```

### Rich Media Delivery

```typescript
interface RichMediaDelivery {
  // Visual content delivery via WhatsApp
  content_types: {
    VISUAL_PROPOSAL: {
      format: "Carousel of images (3-5 slides)";
      content: ["Cover with trip name", "Day-by-day itinerary", "Hotel photos", "Price breakdown"];
      generation: "Auto-generated from workbench data";
    };

    ITINERARY_PDF: {
      format: "PDF document (6-8 pages)";
      content: ["Cover", "Day-by-day plan", "Hotels with photos", "Inclusions/exclusions", "T&C"];
      delivery: "WhatsApp document message";
    };

    TRIP_VOUCHER: {
      format: "PDF per service (hotel, flight, activity)";
      content: ["Booking reference", "Dates", "Confirmation number", "QR code for check-in"];
      delivery: "Individual PDF per service";
    },

    MEMORY_BOOK_PREVIEW: {
      format: "PDF or image carousel";
      content: ["3-page preview of memory book"];
      call_to_action: "Download full PDF or order print";
    };
  };
}

// ── Rich media delivery examples ──
// ┌─────────────────────────────────────────────────────┐
// │  WhatsApp — Rich Media Types                            │
// │                                                       │
// │  📸 Visual Proposal (Image carousel)                    │
// │  ┌───────┐ ┌───────┐ ┌───────┐                       │
// │  │Cover  │ │Day-by │ │Price  │                       │
// │  │Page   │ │Day    │ │Break  │                       │
// │  │"SGP   │ │Plan   │ │down   │                       │
// │  │5N"    │ │       │ │       │                       │
// │  └───────┘ └───────┘ └───────┘                       │
// │  Auto-generated from workbench, 2 variants              │
// │                                                       │
// │  📄 Itinerary PDF (6-8 pages)                           │
// │  Full trip document with photos, maps, contacts         │
// │  Delivered as WhatsApp document                         │
// │                                                       │
// │  🎫 Service Vouchers (PDF per booking)                  │
// │  Hotel voucher · Flight e-ticket · Activity voucher     │
// │  QR codes for easy check-in                             │
// │                                                       │
// │  📸 Memory Book Preview (image + PDF)                   │
// │  3-page preview + full PDF download link                │
// │  Print order option                                     │
// │                                                       │
// │  🎬 Highlight Reel (video)                              │
// │  30-second MP4 video of trip highlights                 │
// │  Delivered as WhatsApp video (under 16MB)               │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Template rejection risk** — Marketing templates get rejected more often. Need utility-category framing for as many messages as possible.

2. **Payment link trust** — Customers may not trust payment links in WhatsApp. Razorpay branding and UPI deep links improve trust.

3. **Rich media generation quality** — Auto-generated visual proposals must look professional. Poor formatting damages credibility.

4. **Conversation volume management** — 100+ concurrent conversations need intelligent routing and AI triage to prevent agent overload.

---

## Next Steps

- [ ] Build AI-assisted sales conversation engine with real-time suggestions
- [ ] Create auto-response system for common customer service queries
- [ ] Implement WhatsApp payment collection with Razorpay integration
- [ ] Design rich media generation pipeline for proposals and vouchers
