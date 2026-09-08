# Research — Provider Connector & India Payments Path (2026-09-08)

**Roadmap items B6/B7.** Evidence tier: **orientation only** — web search quota was exhausted mid-research; findings below come from prior session research plus model-knowledge comparison, explicitly flagged for live re-verification. Do not treat vendor specifics as current.

---

## B6 — Provider connector for real inventory

### Orientation: the two shortlisted consolidators

| | **TBO** | **Mystifly (Rate Gain)** |
|---|---|---|
| Scope | Flights + hotels + holidays + transfers + rail, one wallet | Flight-only consolidator (LCC + GDS + NDC mix) |
| Strength | 450+ airlines, ~1M hotels; strong India/SEA/ME corridors | Deeper flight fare mix; lighter-weight REST/iFrame integration |
| Fit for Waypoint | One integration could back **both** flight and hotel inventory later | Fastest path to flight quotes only |
| Onboarding | Business docs, IATA-or-non-IATA paths by market, possible deposit, days–weeks approval | Similar docs; known for quick sandbox key issuance |

**Waypoint mapping (canonical paths to extend):** the adapter seam already exists — `src/distribution/amadeus_sandbox_adapter.py` behind `RealityTier` + `provider_connected` metadata, and the preview-only GDS router (`/api/v1/gds-sandbox/*`, badged). A real connector is a NEW adapter class implementing the same flight-order contract (with native provider idempotency keys per Part H/J), registered via env selection exactly like the Stripe adapter's sandbox/livemode split. No router changes; the reality tier flips only when the provider contract is verified (S3).

### Recommendation shape (for the DECIDE row)

1. Prototype **Mystifly sandbox first** (flights-only, fastest sandbox, maps 1:1 to the existing flight-order contract).
2. Evaluate TBO in parallel only if hotel inventory becomes the bottleneck (one-wallet economics).
3. Gate: real connector ships with `provider_connected: true` **only after** a live booking round-trips with a supplier-side confirmation that survives the exactly-once guarantees (Part H P0 design: provider idempotency key + side-effect marker).

### Open questions for owner/Ravi

- Corridors that matter most (domestic India vs international)?
- Expected monthly booking volume (deposits/credit terms)?
- Is hotel inventory needed in v1 of real quotes?

## B7 — India payments path

### Orientation

| Rail | Fit for Waypoint's mandate model |
|---|---|
| **Razorpay** (UPI/cards/netbanking, Route/razorpayX) | Widest traveler coverage in India; hosted pages + webhooks; mandates support for recurring; maps to the existing Stripe-style webhook-signature verification pattern in `stripe_issuing_adapter`/payment mandate ledger |
| **UPI directly (NPCI)** | Lowest fees but requires PSP sponsorship + heavier compliance — not v1 |
| **Stripe** | Excellent API but negligible India traveler coverage for UPI-dominant customers; keep for international travelers |

**Waypoint mapping:** `payment_mandate_service` (consent artifacts, F-04) and the FX/settlement preview routers are provider-neutral. An India rail is another adapter behind the same mandate CAS; the AT-15 posture (mandates required before money moves) is unchanged by rail choice.

**Recommendation shape:** Razorpay first for traveler-facing collection (UPI reach), Stripe retained for international cards; both behind the same `PaymentMandateLedger.authorize_charge` CAS so consent enforcement is rail-independent.

### Open questions for owner/Ravi

- UPI share of his travelers' payments; refund/chargeback volume; GST invoicing requirements (GST number on invoices is a hard requirement in India — not currently modeled).

---

## Action

Both items feed DECIDE rows (roadmap Wave C). Neither should be implemented until (a) live vendor verification replaces this orientation tier, and (b) owner answers the open questions above.
