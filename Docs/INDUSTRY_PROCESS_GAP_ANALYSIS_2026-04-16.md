# Industry-Grounded Process Gap Analysis — Waypoint OS

**Date:** 2026-04-16  
**Method:** Analysis from real travel agency operations knowledge — what boutique agencies actually do daily that this system doesn't address, regardless of whether it's documented anywhere in the repo.  
**Scope:** Indian outbound travel agency operations (primary market), applicable globally.

## Repo implementation evidence

The repo contains partial implementation for a few of the processes listed below. These are real code artifacts, but they do not constitute the complete industry workflow described in this gap analysis.

- `src/decision/rules/visa_timeline.py` implements a visa timeline risk rule, destination lead-time table, and urgency-based risk assessment.
- `src/intake/packet_models.py` defines `LifecycleInfo.payment_stage` and `SubGroup.payment_status`, indicating payment tracking placeholders exist.
- `src/intake/extractors.py` extracts `visa_status` from text, which feeds visa risk and document-blocker logic.
- `src/analytics/review.py` and `src/analytics/engine.py` implement owner review actions, feedback severity, recovery workflow, and escalation metadata.
- `src/intake/negotiation_engine.py` includes a supplier negotiation stub for group and budget opportunities.
- `src/intake/decision.py` contains a `visa_insurance` heuristic budget bucket and the `pending_policy_lookup` placeholder for cancellation/refund policy routing.

## Actual implementation work found

These are the concrete repo artifacts that are already implemented at some level.

1. Visa timeline risk assessment
   - `src/decision/rules/visa_timeline.py`
   - `src/decision/hybrid_engine.py`
   - `src/intake/extractors.py` for `visa_status` extraction

2. Visa/insurance heuristic signals
   - `src/intake/decision.py` `visa_insurance` budget bucket
   - `src/intake/decision.py` `visa_status` document-blocker logic

3. Payment state placeholders
   - `src/intake/packet_models.py` `LifecycleInfo.payment_stage`
   - `src/intake/packet_models.py` `SubGroup.payment_status`

4. Feedback / review / recovery flow
   - `src/analytics/review.py`
   - `src/analytics/engine.py`

5. Supplier negotiation stub
   - `src/intake/negotiation_engine.py`

6. Cancellation/refund policy placeholder
   - `src/intake/decision.py` `pending_policy_lookup`

## Prioritized implementation work

The highest-priority work to move this gap area toward completion is:

- Implement full financial state tracking: quote amount, client collections, outstanding balance, supplier cost confirmation, and overdue detection.
- Build visa/document workflow support: requirement lookup, per-destination document checklists, application status tracking, and timed document reminders.
- Add cancellation/refund policy computation: supplier cancellation terms, refund eligibility, credit note handling, and alternative rebooking options.
- Expand active-trip operations: PNR/voucher tracking, flight disruption monitoring, transfer/DMC coordination, and pre-departure reminders.
- Add insurance recommendation and mandatory coverage rules, especially for visa-sensitive destinations.
- Formalize supplier-side models: contracted rates, room categories, allotments, meal plans, and supplier confirmation workflows.

---

## 1. FINANCIAL OPERATIONS — The Entire Money Layer Is Missing

Travel agencies are fundamentally **financial intermediaries**. They collect money, pay suppliers, and keep the spread. This entire layer is absent.

### 1.1 Pricing & Costing

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Component-level costing** | Build price from: flights + hotels + transfers + activities + visa fees + insurance + forex markup + agency margin — each sourced separately | ❌ No costing model at all |
| **Markup strategy by component** | Hotels: 15-25% markup. Flights: flat fee or 3-5%. Transfers: 30-40%. Activities: 20-30%. Different rules per component. | ❌ No component-level pricing |
| **Dynamic pricing awareness** | Hotel rates change daily. Airlines have fare buckets (Y/B/M/H/Q). Agencies track "will this price hold until client confirms?" | ❌ No price volatility concept |
| **Package vs à la carte pricing** | Bundled package price vs itemized breakdown. Client sees package; agent sees margin per component. | ❌ No dual pricing view |
| **Seasonal rate calendars** | Peak/shoulder/off-peak rates by destination. "Europe Jul-Aug is 40% more than Sep-Oct." Affects feasibility. | ❌ Budget feasibility has no seasonal intelligence |
| **Child/infant pricing** | Hotels: child sharing = free or 50%. Flights: infant = 10%, child = 75%. Different rules per supplier. | ❌ Party composition doesn't affect pricing |
| **Group discount thresholds** | 10+ pax = 1 free. 15+ = group fare on airline. 20+ = dedicated coach vs SIC. | ❌ No group pricing tiers |

### 1.2 Payment & Collections

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Deposit → Balance collection** | Typically: 30-50% deposit at booking, balance 30 days before travel. Track per-booking. | ❌ No payment tracking |
| **Multi-party payment splits** | Group trips: Family A pays ₹3L, Family B pays ₹2.5L, each with different payment schedules. | ❌ No payment splitting |
| **Payment reminders & escalation** | "Balance due in 7 days. 3 days. Tomorrow. OVERDUE." Auto-escalate to owner if overdue. | ❌ No payment lifecycle |
| **Refund processing** | Client cancels → calculate refund per supplier cancellation policy → process refund → track completion. | ❌ No refund workflow |
| **Credit note management** | Supplier issues credit note instead of cash refund → agency tracks credit → applies to future booking. | ❌ No credit note tracking |
| **Commission reconciliation** | Supplier pays commission 30-60 days post-travel. Track: expected vs received vs disputed. | ❌ No commission tracking |

### 1.3 Indian-Specific Financial Compliance

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **TCS (Tax Collected at Source)** | 5% TCS on overseas tour packages above ₹7L (as of 2024 rules). Must collect, remit to govt, issue certificate. | ❌ Not modeled |
| **GST invoicing** | 18% GST on service fee. Different treatment for domestic vs international. Reverse charge on foreign suppliers. | ❌ No invoicing |
| **LRS (Liberalized Remittance Scheme) limits** | Individual limit USD 250K/year for overseas remittances. Agency must verify client hasn't exceeded. | ❌ No LRS awareness |
| **FEMA compliance** | Foreign Exchange Management Act rules on overseas payments. Agency must maintain records. | ❌ No compliance tracking |
| **PAN card collection** | Required for transactions above ₹50K. Agency must collect and verify. | ❌ No document compliance |

---

## 2. SUPPLIER OPERATIONS — The Entire Supply Side Is Missing

Agencies don't just plan trips — they **procure** them from a network of suppliers.

### 2.1 Hotel Operations

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Rate negotiation & contracts** | Annual rate contracts with preferred hotels. "We get ₹8K/night when rack rate is ₹12K." Track contracted vs rack rates. | ❌ No supplier contracts |
| **Allotment management** | Pre-blocked rooms at contracted rates. "We have 5 rooms at Marriott Jaipur for Dec 20-25." Release date = 30 days prior. | ❌ No allotment concept |
| **Room category matching** | Client says "nice room" → agent maps to: Superior/Deluxe/Premium/Suite. Each hotel uses different naming. Standardize. | ❌ No room taxonomy |
| **Meal plan selection** | CP (breakfast) / MAP (breakfast+dinner) / AP (all meals) / EP (no meals). Affects price 20-40%. | ❌ No meal plan modeling |
| **Blackout dates** | Hotels block high-demand dates. "No availability Dec 24-26 at any rate." Must check before quoting. | ❌ No blackout awareness |
| **Confirmation & voucher** | Hotel confirms → agency issues voucher to client with booking ref, check-in time, meal plan, room type. | ❌ No voucher generation |
| **Check-in/out coordination** | Early check-in (before 2PM) or late checkout (after 12PM) — must request, sometimes extra charge. | ❌ Not modeled |

### 2.2 Airline/Flight Operations

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **PNR management** | Every booking has a PNR (Passenger Name Record). Track: confirmed / waitlisted / cancelled. Manage name changes, seat selection, meal requests. | ❌ No PNR concept |
| **Fare rules awareness** | Non-refundable vs refundable. Change fees. Name change rules. Baggage allowance. Vary by fare class. | ❌ No fare rule modeling |
| **Ticketing deadlines** | "Hold expires in 48 hours — must ticket or lose fare." Critical operational deadline. | ❌ No deadline tracking |
| **Sector-wise routing** | Multi-city: DEL→LHR→PAR→ROM→DEL. Each sector has different airlines, times, connection risks. | ❌ No multi-sector routing |
| **Waitlist management** | Indian Railways, certain airlines: book on waitlist, confirm when seat opens. Track probability of confirmation. | ❌ No waitlist tracking |
| **Reissue/rebooking** | Flight change → reissue ticket → calculate fare difference → collect/refund difference. | ❌ No rebooking workflow |
| **Baggage policy mapping** | "Ryan Air = no checked bag. Emirates = 30kg." Must inform client. Affects total cost. | ❌ No baggage modeling |

### 2.3 Ground Services & DMC Coordination

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Transfer planning** | Airport→hotel, hotel→hotel, hotel→airport. Vehicle type by party size: sedan (1-3), SUV (4-6), van (7-12), coach (13+). | ❌ No transfer planning |
| **DMC (Destination Management Company)** | Local partner handles ground services. Agency sends "service voucher" with all details. DMC confirms. | ❌ No DMC coordination |
| **SIC vs PVT transfers** | Seat-In-Coach (shared, cheap) vs Private (dedicated, expensive). Different for budget vs premium clients. | ❌ No transfer type modeling |
| **Activity/excursion booking** | Skip-the-line tickets, guided tours, experiences. Must book in advance for popular ones. Time-slot management. | ❌ No activity booking |
| **Guide arrangement** | Local guide by language (Hindi/English/other). Full-day vs half-day. Licensed guide requirements vary by country. | ❌ No guide management |
| **Emergency local contacts** | DMC emergency phone for each destination. Client must have this before travel. | ❌ No emergency contact management |

---

## 3. DOCUMENT & COMPLIANCE OPERATIONS

### 3.1 Visa Processing (Not Just Checking — Managing)

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Visa requirement lookup** | Indian passport → [destination] = visa required/free/on-arrival/e-visa. Changes frequently. | ❌ No visa database |
| **Document checklist per country** | Schengen: passport, photos, bank statements (6mo), ITR, cover letter, travel insurance, hotel vouchers, flight tickets. Different per consulate. | ❌ No document checklists |
| **Appointment booking** | VFS/consulate appointment scheduling. Some have 2-3 week waits. Must plan timeline. | ❌ No appointment tracking |
| **Application tracking** | Submitted → Under review → Approved/Rejected. Track per traveler. | ❌ No visa application status |
| **Visa timeline vs travel date** | "Travel in 45 days but Schengen visa takes 15-21 business days. Submit by [date] or trip is at risk." | ❌ No timeline risk calculation |
| **Visa rejection handling** | If rejected → appeal? Re-apply? Change destination? Refund? Cascading impact on entire trip. | ❌ No rejection workflow |
| **Multi-destination visa strategy** | "Schengen covers 27 countries. Apply at consulate of main destination. If Italy 4 nights + France 3 nights → apply at Italian consulate." | ❌ No multi-destination visa logic |

### 3.2 Travel Insurance

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Policy recommendation** | Based on destination, duration, traveler age, pre-existing conditions. Senior travelers (65+) need specialized cover. | ❌ No insurance recommendation |
| **Mandatory vs optional** | Schengen visa requires €30K minimum medical insurance. Some countries mandate it. | ❌ No mandatory insurance rules |
| **Claims assistance** | Trip cancelled due to illness → help client file claim → track resolution. | ❌ No claims workflow |
| **Policy document delivery** | Send policy PDF to client before travel. Include emergency claim numbers. | ❌ No document delivery |

### 3.3 Forex & Currency

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Forex card arrangement** | Multi-currency forex cards (Thomas Cook, BookMyForex). Load USD/EUR/GBP. Track rates. | ❌ Not modeled |
| **Cash forex** | Some destinations are cash-heavy (SE Asia, parts of Europe). Advise on carry amounts. | ❌ Not modeled |
| **Currency conversion in quotes** | Quote in INR but components priced in USD/EUR. Must show conversion rate used. Rate valid for X days. | ❌ No multi-currency |

---

## 4. COMMUNICATION & RELATIONSHIP OPERATIONS

### 4.1 Pre-Trip Communication Cadence

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Booking confirmation package** | Day 0: Detailed email with booking ref, payment schedule, cancellation policy, next steps. | ❌ No confirmation package |
| **Document collection reminders** | D-60: "Please share passport copies." D-45: "Passport reminder." D-30: "URGENT: passports needed for visa." | ❌ No timed reminders |
| **Pre-departure briefing** | D-7: Complete trip dossier — day-by-day itinerary, hotel addresses, emergency contacts, weather forecast, packing tips, cultural notes. | ❌ No trip dossier generation |
| **D-3 confirmation** | D-3: "Your trip starts in 3 days! Here are your documents: [flight tickets] [hotel vouchers] [insurance] [visa copy]." | ❌ No pre-departure automation |
| **D-1 reminder** | D-1: Airport terminal, check-in time, baggage rules, forex reminder, emergency numbers. | ❌ No D-1 automation |
| **Travel advisory alerts** | Government travel warnings, weather alerts, strikes, political instability — must relay to clients with active bookings. | ❌ No advisory monitoring |

### 4.2 During-Trip Operations

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Flight status monitoring** | Track flight delays/cancellations for active travelers. Proactively call if flight disrupted. | ❌ No flight monitoring |
| **Hotel check-in confirmation** | Verify client checked in. If not → call hotel → call client → resolve. | ❌ No check-in tracking |
| **Daily check-in (premium)** | High-value clients: "How's the trip going? Anything you need?" on Day 2-3. | ❌ No during-trip communication |
| **Issue escalation during trip** | "Hotel room is dirty" → call hotel GM → resolve → follow up with client → document for future reference. | ❌ No real-time issue handling |
| **Rebooking on disruption** | Flight cancelled → find alternative → rebook → inform client → update all downstream (hotel check-in, transfers). | ❌ No cascading rebooking |

### 4.3 Post-Trip Operations

| Process | What Agencies Actually Do | System State |
|---------|--------------------------|-------------|
| **Feedback collection** | D+3 to D+5: "How was your trip?" Structured feedback on hotel, flights, activities, guide, transfers. | ❌ No feedback collection |
| **Supplier feedback loop** | "Hotel XYZ got 3/5 from Sharma family — rooms were dated." Log against supplier. Affects future recommendations. | ❌ No supplier scoring from feedback |
| **Referral ask** | D+7: "Glad you enjoyed it! Know anyone planning a trip? We'd love a referral." Timing matters — too early feels transactional. | ❌ No referral workflow |
| **Review solicitation** | Ask for Google/TripAdvisor review. Provide direct link. Track who reviewed. | ❌ No review management |
| **Repeat booking trigger** | 6 months later: "Last year you went to Singapore — thinking about this year's trip?" Based on travel pattern. | ❌ No repeat trigger |
| **Anniversary/birthday marketing** | "Your wedding anniversary is next month — how about a surprise trip?" | ❌ No occasion-based marketing |

---

## 5. OPERATIONAL INTELLIGENCE — What Agencies Track That Isn't Modeled

### 5.1 Destination Intelligence

| Knowledge | What Agencies Maintain | System State |
|-----------|----------------------|-------------|
| **Destination seasonality matrix** | Best time to visit × destination × trip type. "Maldives: Nov-Apr for beach, avoid May-Oct monsoon." | ❌ No seasonality data |
| **Destination suitability by traveler type** | "Bali: great for honeymoons, OK for families with teens, bad for elderly." Per-destination, per-segment ratings. | ❌ No suitability matrix |
| **Destination-specific gotchas** | "Vietnam: ATMs charge 50K VND fee. Thailand: don't point feet at Buddha. Japan: no tipping." Cultural/practical notes. | ❌ No destination knowledge base |
| **Connection risk awareness** | "2hr layover at JFK T1→T4 = risky. 3hr at Dubai = comfortable. Istanbul IST has fast connections." | ❌ No connection risk modeling |
| **Visa processing time by consulate** | "Italian consulate Mumbai: 10 days. Delhi: 21 days. Kolkata: 7 days." Varies by city and season. | ❌ No consulate-specific data |
| **Health requirements** | "Kenya: Yellow Fever vaccine mandatory. Malaria prophylaxis recommended for Tanzania." | ❌ No health requirement database |

### 5.2 Competitive Intelligence

| Knowledge | What Agencies Need | System State |
|-----------|-------------------|-------------|
| **OTA price benchmarking** | "MakeMyTrip is selling Bali 5N at ₹45K. We're quoting ₹62K. Can we justify the premium?" | ❌ No competitive pricing |
| **Competitor package comparison** | "Thomas Cook's Europe 10D is ₹1.8L — includes what? Excludes what? Where do we win?" | ❌ No competitor analysis |
| **Value-add differentiation** | "OTA gives hotel+flight. We add: airport lounge, local SIM, travel kit, 24/7 support, curated experiences." Must articulate clearly. | ❌ No differentiation framework |

### 5.3 Agent Performance Metrics (Real KPIs)

| Metric | What Owners Track | System State |
|--------|------------------|-------------|
| **Lead-to-booking conversion rate** | By agent, by month, by source channel. Industry benchmark: 15-25%. | ❌ No conversion tracking |
| **Average revenue per booking** | Track agent performance on revenue, not just volume. | ❌ No revenue tracking |
| **Quote turnaround time** | Time from inquiry to first quote sent. Target: <4 hours for simple, <24 hours for complex. | ❌ No response time tracking |
| **Revision count per booking** | More than 3 revisions = either client is indecisive or agent didn't understand requirements. | ❌ No revision counting |
| **Customer satisfaction score** | Post-trip CSAT by agent. Directly affects agent incentives. | ❌ No CSAT tracking |
| **Repeat customer rate** | What % of Agent X's clients book again? High repeat = good relationship management. | ❌ No repeat rate tracking |
| **Cancellation rate** | High cancellation rate for an agent may indicate over-promising or poor expectation setting. | ❌ No cancellation analytics |

---

## 6. TRIP TYPES WITH FUNDAMENTALLY DIFFERENT WORKFLOWS

The system treats all trips as generic. In reality, different trip types have radically different workflows.

### 6.1 Honeymoon/Romantic Trips

| Unique Process | What's Different | System State |
|---------------|-----------------|-------------|
| **Surprise elements** | One partner planning secretly. System must support "hidden" notes partner can't see. | ❌ No surprise/hidden mode |
| **Romantic setup coordination** | Cake on bed, flower decoration, candlelight dinner booking, spa couples packages. Coordinate with hotel. | ❌ No special arrangement requests |
| **Anniversary date awareness** | "Wedding anniversary is May 15 — book special dinner that night." | ❌ No occasion awareness |
| **Upsell sensitivity** | Honeymoon travelers accept premium upgrades more readily. Room upgrade, sunset cruise, private dinner. | ❌ No segment-specific upsell logic |

### 6.2 Corporate/MICE Travel

| Unique Process | What's Different | System State |
|---------------|-----------------|-------------|
| **Corporate travel policy compliance** | "Company policy: max ₹8K/night hotel, economy class for <5hr flights, business class for >5hr." | ❌ No policy engine |
| **Approval hierarchy** | Employee → Manager → Finance → Travel desk. Each level approves different spend thresholds. | ❌ No multi-level approval |
| **Expense reporting integration** | Post-trip: generate expense report format compatible with client's system. | ❌ No expense reporting |
| **Venue/conference logistics** | Room blocks, AV equipment, catering, transportation for 50-500 pax. Completely different workflow. | ❌ No MICE module |
| **Billing entity** | Bill to company, not individual. PO numbers, corporate credit terms (30/60/90 days). | ❌ No corporate billing |

### 6.3 Group Series (Fixed Departures)

| Unique Process | What's Different | System State |
|---------------|-----------------|-------------|
| **Minimum pax threshold** | "Tour departs with minimum 15 pax. Currently 11 confirmed, 4 tentative." Track toward threshold. | ❌ No group threshold tracking |
| **Guaranteed vs tentative** | Some bookings are confirmed (paid deposit), some are tentative (verbal commitment). Different weights. | ❌ No booking status tiers |
| **Rooming list management** | Twin sharing, triple sharing, single supplement. Match travelers into rooms. | ❌ No rooming list |
| **Coach seating** | 45-seater coach for 38 pax. Assign seats. Window preferences. Motion sickness consideration. | ❌ No seating management |
| **Group leader/escort** | Tour leader accompanies group. Must be assigned, briefed, equipped with all vouchers. | ❌ No tour leader concept |

### 6.4 Pilgrimage/Religious Travel

| Unique Process | What's Different | System State |
|---------------|-----------------|-------------|
| **Religious calendar awareness** | "Char Dham opens May-Oct only. Hajj dates shift yearly. Vaishno Devi has permit system." | ❌ No religious calendar |
| **Dietary requirements** | Strict vegetarian, Jain (no root vegetables), Halal. Must verify at every restaurant/hotel. | ❌ No dietary requirement tracking |
| **Medical readiness** | High-altitude pilgrimages (Amarnath, Kailash Mansarovar): medical fitness certificate required. | ❌ No medical readiness checks |
| **Permit management** | Inner Line Permits (Arunachal, Sikkim), Protected Area Permits. Must apply in advance. | ❌ No permit tracking |

### 6.5 Multi-Generational Family Travel

| Unique Process | What's Different | System State |
|---------------|-----------------|-------------|
| **Accessibility planning** | Elderly: wheelchair at airport, ground-floor rooms, elevator access, accessible bathrooms, medical facility proximity. | ❌ No accessibility modeling |
| **Activity splitting** | "Adults do scuba diving. Kids go to waterpark. Grandparents relax at spa." Same day, different activities, coordinated timing. | ❌ No split-activity planning |
| **Medical preparation** | "Grandma takes blood pressure medication — carry prescription. Nearest hospital to hotel?" | ❌ No medical planning |
| **Dietary diversity** | "Dad is diabetic. Mom is vegetarian. Kids eat everything. Grandfather is Jain." One table, four diets. | ❌ No multi-dietary management |

---

## 7. RISK & CRISIS MANAGEMENT

| Process | What Agencies Must Handle | System State |
|---------|--------------------------|-------------|
| **Natural disaster response** | Earthquake/tsunami/volcano → check all active travelers in affected area → contact each → arrange evacuation if needed. | ❌ No disaster response workflow |
| **Political instability** | Country-level unrest → identify all travelers in/departing to that country → advise → rebook if needed. | ❌ No geopolitical monitoring |
| **Pandemic protocols** | Testing requirements, vaccination certificates, quarantine rules, travel corridors. Changed weekly during COVID. | ❌ No health protocol management |
| **Airline bankruptcy** | "Jet Airways went bankrupt mid-flight-schedule" → rebook all affected travelers on alternative airlines. | ❌ No carrier risk management |
| **Hotel overbooking** | Hotel overbooked → client arrives, no room → agency must find alternative immediately → compensate. | ❌ No overbooking protocol |
| **Travel insurance claims** | Client hospitalized abroad → coordinate with insurer → manage treatment → arrange medical evacuation if needed. | ❌ No emergency medical coordination |
| **Theft/loss handling** | Passport stolen during trip → contact embassy → get emergency travel document → modify return flights. | ❌ No emergency document workflow |

---

## 8. TECHNOLOGY/INTEGRATION GAPS FROM INDUSTRY STANDARD

| System | Industry Standard | Waypoint OS State |
|--------|------------------|------------------|
| **GDS connectivity** | Amadeus/Sabre/Galileo for real-time flight/hotel inventory and pricing | ❌ Not planned (docs say "not needed" — true for MVP but limits quote accuracy) |
| **Channel manager** | Manage rates across OTAs (Booking.com, Expedia) for agencies that also sell online | ❌ Not in scope |
| **Accounting integration** | Tally (India standard) / QuickBooks / Zoho Books for invoicing and reconciliation | ❌ No accounting integration |
| **CRM integration** | Zoho CRM, HubSpot, or LeadSquared — Indian agencies commonly use these | ❌ No CRM integration |
| **WhatsApp Business API** | Not just copy-paste but proper template messages, broadcast lists, auto-replies, read receipts | ❌ Documented but not built |
| **Payment gateway** | Razorpay/PayU/CCAvenue for online payment links sent to clients | ❌ No payment integration |
| **E-signature** | Digital signature on booking terms and cancellation policy — increasingly required | ❌ No e-signature |
| **Calendar sync** | Sync travel dates to client's Google/Outlook calendar | ❌ No calendar integration |

---

## 9. PROCESS MATURITY ASSESSMENT

### What Waypoint OS Currently Is vs Industry Expectations

| Dimension | Current State | MVP for Pilot | Production-Ready | Industry Leader |
|-----------|--------------|---------------|------------------|-----------------|
| **Intake intelligence** | ✅ Rule-based extraction | Add LLM extraction | Multi-source intake (WhatsApp, email, voice, form) | Real-time learning from corrections |
| **Decision logic** | ✅ Deterministic MVB | Add budget feasibility, ambiguity, urgency | Add commercial logic, supplier awareness | Autonomous decision with confidence gating |
| **Quote generation** | ❌ Not started | Template-based with manual pricing | Component-level costing with live rates | Dynamic packaging with margin optimization |
| **Communication** | ❌ Not started | Copy-to-clipboard | WhatsApp API + email templates | Multi-channel with A/B tested messaging |
| **Supplier management** | ❌ Not started | Preferred supplier list | Rate contracts, allotment tracking | Supplier performance scoring with auto-optimization |
| **Financial operations** | ❌ Not started | Basic invoicing | Payment tracking + TCS + GST | Full reconciliation with accounting integration |
| **Customer intelligence** | ❌ Not started | Basic repeat detection | Preference learning, lifetime value | Predictive next-trip recommendation |
| **Team operations** | ❌ Not started | User accounts + roles | Workload balancing, SLA tracking | AI-assisted assignment, training suggestions |
| **Compliance** | ❌ Not started | Visa requirement lookup | Document checklist + timeline tracking | Automated compliance with regulatory updates |
| **Crisis management** | ❌ Not started | Emergency contact list | Active traveler monitoring | Proactive disruption detection + auto-rebooking |

---

## 10. THE 15 PROCESSES THAT WOULD MAKE A PILOT AGENCY SAY "YES"

If a real boutique agency (5-10 agents, 50-200 bookings/month) were evaluating Waypoint OS today, these are the processes they'd need to see working before signing:

| # | Process | Why It's a Dealbreaker | Current State |
|---|---------|----------------------|---------------|
| 1 | **Intake → structured brief in <2 min** | This is the value proposition | ⚠️ Works but no LLM, rule-based only |
| 2 | **Auto-generated follow-up questions** | Saves 30 min per inquiry | ✅ Works |
| 3 | **Budget feasibility check** | "Don't waste my time on impossible trips" | ❌ Missing |
| 4 | **Quote with 2-3 options + costing** | Core deliverable of an agent's job | ❌ Missing |
| 5 | **Copy-to-WhatsApp for questions AND proposals** | WhatsApp is the channel — must integrate seamlessly | ❌ Missing |
| 6 | **Trip list with status tracking** | "Where is each trip in my pipeline?" | ❌ Mock data only |
| 7 | **Customer recognition on repeat inquiry** | "Don't ask me the same questions twice" | ❌ Missing |
| 8 | **Payment collection tracking** | "Who owes me money?" | ❌ Missing |
| 9 | **Document checklist by destination** | "What does the client need to submit?" | ❌ Missing |
| 10 | **Visa timeline risk alert** | "Visa processing takes 21 days, travel in 30 — apply NOW" | ❌ Missing |
| 11 | **Pre-departure briefing auto-generation** | "Send the client their D-3 package" | ❌ Missing |
| 12 | **Post-trip feedback collection** | "How was it? Would you refer us?" | ❌ Missing |
| 13 | **Owner can see all trips across agents** | "What's my team working on?" | ❌ Stub only |
| 14 | **Margin visibility per booking** | "Am I making money on this trip?" | ❌ Missing |
| 15 | **Mobile-friendly agent view** | Agents work from phones — not optional | ⚠️ Mobile nav exists but limited |

**Current score: 2 of 15 working.** A pilot agency would not sign today.

---

## 11. WHAT THE DOCS DON'T COVER AT ALL

These industry-standard processes aren't even mentioned in any documentation file in the repo:

1. **Component-level trip costing** (flights + hotels + transfers + activities as separate cost items)
2. **Supplier contract/rate management** (contracted rates, allotments, release dates)
3. **PNR/booking reference tracking** (per-supplier confirmation numbers)
4. **Ticketing deadlines** (airline fare hold expiry)
5. **TCS/GST tax compliance** (Indian tax requirements on overseas packages)
6. **LRS/FEMA foreign exchange compliance**
7. **Visa application process management** (not just requirement lookup — the actual submission workflow)
8. **Pre-departure communication cadence** (D-7, D-3, D-1 automated briefings)
9. **During-trip monitoring** (flight status, check-in confirmation)
10. **Supplier feedback from client reviews** (closing the quality loop)
11. **Rooming list management** (for groups)
12. **Transfer vehicle type mapping** (by party size)
13. **Activity/excursion slot booking** (time-sensitive pre-booking)
14. **Forex card arrangement** (multi-currency loading)
15. **Corporate travel policy compliance** (for B2B bookings)
16. **Medical/accessibility requirement planning** (elderly/disabled travelers)
17. **Destination seasonality intelligence** (best-time-to-visit matrix)
18. **Connection risk scoring** (layover time + terminal change + immigration)
19. **Accounting system integration** (Tally/QuickBooks)
20. **Payment gateway integration** (Razorpay/PayU payment links)

---

*This analysis comes from industry operations knowledge, not from the repo's own documentation. These are processes that real travel agencies execute daily that Waypoint OS must eventually support to be a credible "operating system" for the industry.*
