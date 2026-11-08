# Real-World Booking Pain Points — market research vs Waypoint coverage (2026-11-08)

**Purpose:** validate the council-wave build against pain actually posted online by
travel agencies, boutique agency owners, and travelers. Sources fetched live via
TinyFish (WebSearch quota-blocked).owner directive: research + document + map gaps.

## Agency-side pains (evidence → Waypoint status)

### 1. Commission reconciliation hell — THE back-office pain
**Evidence:** tern.travel/blog/travel-back-office-still-runs-on-software-from-1987 (fetched):
supplier statements arrive with bookings that are "missing, short-paid, overpaid,
split across brands, or waiting on payout logic that only your team knows how to
apply"; month-end "runs on exceptions"; incumbent back office (TRAMS/TRES, 1987)
+ point solutions (SION, TripSuite) unchanged since before the web.
**Waypoint:** commission ingest breadth (CSV/email/OCR → fuzzy/booking-ref match →
manual-link → durable payout) built this wave; reconciliation via
`reconcile_trip_commission`; margin via MarginPolicy. **Gap (filed FND-0404):**
batch durability now fixed; breadth vs real supplier statement formats still
unproven until pilots. Revisit trigger: DP-04a vendor feeds.

### 2. Airlines disrupting bookings (IRROPS chaos)
**Evidence:** r/TravelAgent 1f1ut3a (fetched): "Airlines screwing up all our hard
work!" — agents cite carrier-caused churn as a top ongoing problem.
**Waypoint:** IRROPS taxonomy + report/radar/resolve + watcher + passenger-rights
claim engine (EC261/UK261/DOT). **Gap (filed FND-0405, closed this session for
UI):** operator entry now exists; live provider detection still DP-04a-gated.

### 3. Group payment collection — chasing 30 people to pay
**Evidence:** r/travelagents 1afmyqt (fetched): agents describe collecting money
and sending repeated payment reminders to ~30 group members as a "train wreck";
advice was to refuse the job without professional tooling.
**Waypoint:** payment mandates + tracking exist (money boundary = tracking-only,
ADR-008). **GAP (filed FND-0407):** per-traveler payment schedules, automated
reminders, and shareable per-traveler payment links are NOT built as a coherent
group-collection surface. This is a concrete, evidence-backed product gap.

### 4. Client acquisition / trust (oversupply; 70% book independently)
**Evidence:** r/TravelAgent 1f1ut3a (fetched): agents cite oversupply + the rise
of self-booking; consensus: stand out via online presence + trust.
**Waypoint:** honest public proposals (e-sign, de-attributed requirements,
why-this-fits, reacceptance protection — built this wave) directly serve the
trust axis. Marketing/SEO remains the GTM lane, not product.

### 5. Back-office fragmentation
**Evidence:** same tern piece + r/travelagents beginner-faq: agencies stitch
SION/TripSuite/ClientBase point solutions.
**Waypoint:** the unified-OS thesis is the answer; note module-decomposition
ADR (51c) is owner-gated — fragmentation INSIDE the product mirrors the market's
fragmentation pain if left unbounded.

## Traveler-side pains

### 6. Confirmed reservations canceled / hotels overbooked
**Evidence:** r/travel 1nq4134 "Hotel canceled my confirmed reservation";
r/travel 1j9vy15 "Overbooked hotel via Booking.com – no solution".
**Waypoint:** confirmations tracked with defect grading; cancellation *detection*
on confirmed bookings rides the R2-H watcher extension (schedule_change/
cancellation triggers). **GAP (filed FND-0408):** traveler-visible booking-change
monitoring is post-pilot per R2-I ruling — evidence above confirms market demand.

### 7. Wrong dates / booking mistakes
**Evidence:** r/hotels 18wykdu "3rd party website booked the wrong dates";
r/Bookingcom 1wh66m0 accidental wrong dates.
**Waypoint:** this is Waypoint's core competency — extraction + canonical facts +
blocking unknowns + repair loop + authority-ranked corrections (this wave's
contract work). Strength, validated.

## Coverage summary
Covered and evidenced: commission reconciliation (R2-B), IRROPS handling,
honest-proposal trust. Open product gaps: group payment collection (FND-0407),
traveler-visible change monitoring (FND-0408), provider feeds (DP-04a owner
gate). Not product: client acquisition (GTM lane).

## Falsifiers
- Tern blog is a vendor marketing piece — its "1987" framing is directional,
  corroborated by the Reddit threads' independent complaints.
- Reddit anecdotes are individual; treat as hypothesis-generating demand
  signals, not market-size evidence.
