# Agency Marketplace & Storefront — Master Index

> Exploration of public-facing agency storefronts, trip catalogs, direct booking, and customer acquisition.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Platform Architecture](STOREFRONT_01_ARCHITECTURE.md) | Multi-tenant hosting, storefront-workbench bridge, analytics |
| 02 | [Trip Catalog & Listings](STOREFRONT_02_TRIP_LISTINGS.md) | Trip catalog model, search, detail pages, listing optimization |
| 03 | [Direct Booking Engine](STOREFRONT_03_BOOKING_ENGINE.md) | Booking flow, payment processing, communication, booking management |
| 04 | [SEO & Marketing](STOREFRONT_04_SEO_MARKETING.md) | SEO architecture, social sharing, content marketing, campaign tracking |

---

## Key Themes

- **Storefront is the digital shopfront** — Every agency gets a branded, public-facing website where customers browse trips, inquire, and book — without needing to visit the agent's office.
- **Workbench is the back office** — Storefront handles customer-facing interactions; Workbench handles agent operations. The bridge between them is seamless — inquiries flow in, bookings flow out.
- **WhatsApp is the primary channel** — In India, WhatsApp drives more travel inquiries than email or phone forms. Every storefront interaction should have a WhatsApp CTA.
- **SEO is free customer acquisition** — Well-optimized destination pages and blog posts bring organic traffic at zero marginal cost. Content marketing compounds over time.
- **Conversion over traffic** — A storefront with 1,000 visitors and 20 bookings beats one with 10,000 visitors and 5 bookings. Optimize the funnel, not just the top.

## Integration Points

- **Trip Builder** — Published trips appear on storefront; agent manages inventory
- **Booking Engine** — Storefront bookings flow into Workbench as provisional bookings
- **Communication Hub** — WhatsApp and email notifications at every booking stage
- **Payment Processing** — Razorpay integration for UPI, cards, EMI, and net banking
- **Analytics & BI** — Traffic, conversion, and campaign performance dashboards
- **White Label** — Storefront theming per agency with custom domain support
- **Document Generation** — Itinerary, voucher, and invoice downloads from customer portal
