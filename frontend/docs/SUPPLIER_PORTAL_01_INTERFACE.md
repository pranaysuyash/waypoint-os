# Supplier Portal — Vendor-Facing Platform Interface

> Research document for supplier-facing portal, vendor self-service, inventory management interface, booking notification system, supplier profile management, and vendor-platform interaction for the Waypoint OS platform.

---

## Key Questions

1. **What interface do suppliers (hotels, activity providers, transport companies) need?**
2. **How do suppliers manage their inventory and rates on the platform?**
3. **What booking and fulfillment workflows involve the supplier directly?**
4. **How do suppliers view performance, payments, and analytics?**

---

## Research Areas

### Supplier Portal System

```typescript
interface SupplierPortal {
  // The supplier's own interface into the Waypoint OS platform
  portal_overview: {
    description: "Self-service portal for hotels, activity providers, transport operators, and other travel service suppliers to manage their presence on the platform";
    users: {
      HOTEL_MANAGER: "Updates room inventory, rates, photos; confirms bookings; responds to reviews";
      ACTIVITY_PROVIDER: "Manages activity schedules, availability, pricing; confirms bookings";
      TRANSPORT_OPERATOR: "Updates vehicle availability; confirms transfers; tracks driver assignments";
      RESTAURANT_MANAGER: "Manages reservation slots, menu, pricing for included meal plans";
      TOUR_GUIDE: "Updates availability, languages, specialization; accepts tour assignments";
    };
    access: "Web portal + mobile-responsive; login with business email; role-based access (owner, manager, staff)";
  };

  supplier_dashboard: {
    HOME_VIEW: {
      greeting: "Welcome, [Supplier Name] — [Property/Service]";
      today_summary: {
        check_ins: 3;
        check_outs: 2;
        pending_bookings: 1;
        messages: 4;
        revenue_this_month: "₹4,52,000";
        rating: "4.3/5 (128 reviews)";
      };
      alerts: [
        "Agency request: Confirm booking #BK-4521 for Dec 20-23 (3 rooms)",
        "Review response needed: Guest rated 2/5 — please respond",
        "Inventory alert: Dec 24-26 fully booked — consider adding allocation",
        "Rate suggestion: Your competitors are priced 15% lower for January",
      ];
    };

    // ── Supplier portal — dashboard view ──
    // ┌─────────────────────────────────────────────────────┐
    // │  🏨 Taj Holiday Inn Cochin · Supplier Dashboard           │
    // │                                                       │
    // │  Today: Dec 15, 2026                                  │
    // │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
    // │  │ Check-ins│ │ Check-out│ │ Pending  │ │ Messages ││
    // │  │    3     │ │    2     │ │    1     │ │    4     ││
    // │  └──────────┘ └──────────┘ └──────────┘ └──────────┘│
    // │                                                       │
    // │  This Month:                                          │
    // │  Revenue: ₹4,52,000 · Bookings: 47 · Rating: 4.3/5  │
    // │  Occupancy: 72% · Avg rate: ₹6,200/night               │
    // │                                                       │
    // │  Action Required:                                     │
    // │  🔴 Confirm booking #BK-4521 (Dec 20-23, 3 rooms)       │
    // │  🟡 Respond to review: "Room was not clean"              │
    // │  🟢 Update January rates (seasonal pricing)              │
    // │                                                       │
    // │  [Bookings] [Inventory] [Rates] [Reviews] [Payments]    │
    // │  [Profile] [Analytics] [Messages] [Settings]             │
    // └─────────────────────────────────────────────────────────┘
  };

  core_features: {
    BOOKING_MANAGEMENT: {
      incoming_bookings: {
        view: "List of bookings from agency with dates, rooms/guests, special requests";
        actions: ["Confirm", "Request modification", "Decline (with reason)", "Add internal notes"];
        sla: "Confirm within 4 hours during business hours; 12 hours max";
        auto_confirm: "Repeated bookings from same agency can auto-confirm if within allocation";
      };
      booking_calendar: {
        view: "Calendar view of all bookings (check-in/check-out dates, room types, guest names)";
        conflicts: "Highlight double-bookings or over-allocation";
      };
      special_requests: {
        view: "Guest requests (early check-in, vegetarian dinner, room preference)";
        actions: "Accept, Decline, Note additional charges";
      };
    };

    INVENTORY_AND_RATES: {
      room_inventory: {
        daily_view: "Room availability by date and room type";
        allocation: "Set how many rooms allocated to the agency vs. other channels";
        blocking: "Block rooms for maintenance, renovation, or private events";
        seasonal_setup: "Configure availability patterns by season (high/low/shoulder)";
      };
      rate_management: {
        base_rates: "Set base rate per room type per season";
        agency_rates: "Special negotiated rates for the agency (contracted)";
        dynamic_pricing: "Enable/disable dynamic pricing based on demand (optional)";
        rate_calendar: "Visual calendar showing rates per night — bulk edit capability";
        competitor_intelligence: "See average market rates for your area (anonymized)";
      };
    };

    PROFILE_MANAGEMENT: {
      property_details: {
        basic_info: "Hotel name, address, star category, contact details",
        amenities: "Update amenities list (pool, gym, spa, restaurant, wheelchair access)",
        photos: "Upload and manage property photos (min 10, max 50)",
        room_types: "Define room categories with photos and descriptions",
        policies: "Check-in/out times, cancellation policy, child policy, pet policy",
      };
      meal_plans: {
        options: "Define meal plans (room only, breakfast, half board, full board)",
        menu: "Upload restaurant menu for guest reference",
        dietary: "Mark vegetarian/vegan/Jain/halal options available",
      };
    };

    REVIEWS_AND_FEEDBACK: {
      view_reviews: "See all guest reviews with ratings breakdown";
      respond: "Respond to reviews publicly (visible to agency and future guests)";
      insights: "Review analytics — average score, trend, common complaints, strengths";
      action_items: "AI-flagged improvement areas based on review patterns";
    };

    PAYMENTS_AND_STATEMENTS: {
      statements: "Monthly statements with booking-wise breakdown";
      payment_status: "Track paid, pending, and disputed payments from agency";
      invoice_history: "All invoices generated with payment status";
      tax_documents: "GST invoices, TDS certificates, payment proofs";
    };

    ANALYTICS: {
      occupancy_trends: "Monthly occupancy rate with comparison to previous period";
      revenue_trends: "Revenue by month, by room type, by booking source";
      booking_patterns: "Lead time analysis, cancellation rate, average stay duration";
      guest_demographics: "Nationality and group size breakdown (anonymized)";
      performance_score: "Agency's A-F grade with improvement suggestions";
    };
  };
}
```

### Supplier Communication

```typescript
interface SupplierCommunication {
  // Communication between platform and suppliers
  channels: {
    PORTAL_MESSAGES: {
      description: "In-app messaging between agency and supplier";
      use: "Booking queries, rate negotiations, special requests, general coordination";
    };

    WHATSAPP_BUSINESS: {
      description: "WhatsApp messages for urgent booking confirmations";
      use: "Auto-send booking details to supplier WhatsApp; supplier replies confirm/reject";
    };

    EMAIL_NOTIFICATIONS: {
      description: "Email for booking confirmations, statements, and policy updates";
      use: "New booking alert, monthly statement, rate change request from agency";
    };

    API_WEBHOOKS: {
      description: "Real-time API for large suppliers with their own systems";
      use: "Booking pushed to supplier's PMS; confirmation pushed back via webhook";
    };
  };

  notification_rules: {
    BOOKING_CREATED: {
      channels: ["Portal notification", "WhatsApp message", "Email"];
      urgency: "Immediate";
      content: "Booking ID, dates, rooms/guests, guest name, special requests, confirm-by deadline";
    };

    BOOKING_MODIFIED: {
      channels: ["Portal notification", "WhatsApp message"];
      urgency: "Immediate";
      content: "What changed (dates, room count, guest count), updated booking details";
    };

    BOOKING_CANCELLED: {
      channels: ["Portal notification", "Email"];
      urgency: "Immediate";
      content: "Cancellation reason, cancellation fee (if any), inventory released";
    };

    RATE_UPDATE_REQUEST: {
      channels: ["Portal notification", "Email"];
      urgency: "Within 48 hours";
      content: "Agency requests rate update for specific dates with suggested rate";
    },

    PAYMENT_RECEIVED: {
      channels: ["Portal notification", "Email"];
      urgency: "Daily batch";
      content: "Payment amount, booking references, payment method, bank credit details";
    };
  };
}
```

---

## Open Problems

1. **Supplier adoption** — Many Indian hotels and activity providers are not tech-savvy. Portal adoption requires training, simple UX, and WhatsApp-first alternative for non-portal users.

2. **Data quality** — Suppliers may upload low-quality photos, incomplete descriptions, or incorrect rates. Quality gates and review processes are needed before content goes live.

3. **Rate parity** — Suppliers may offer different rates on different platforms (OTAs, direct, agency). Managing rate parity and preventing conflicts is a commercial challenge.

4. **Real-time inventory sync** — For larger suppliers with their own PMS (Property Management Systems), real-time two-way inventory sync via API is essential but technically complex.

5. **Supplier churn** — If a supplier gets few bookings through the portal, they stop using it. The portal must provide enough value (analytics, payment tracking, review management) even during low-booking periods.

---

## Next Steps

- [ ] Build supplier portal with dashboard, booking management, inventory, and rate management
- [ ] Create booking notification system with WhatsApp-first delivery
- [ ] Implement profile management with photo upload and quality gates
- [ ] Build payment statement and invoice tracking for suppliers
- [ ] Create supplier analytics dashboard with occupancy, revenue, and performance trends
- [ ] Design review response system for supplier-guest interaction
- [ ] Build API/webhook integration for large suppliers with their own PMS
