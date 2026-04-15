# Risk Area Catalog

**Date:** 2026-04-15
**Purpose:** Define the full set of risk areas that should be surfaced in travel feasibility investigations, agency operations, and product design.

---

## Overview

This catalog is a canonical list of risk areas for the travel agency product. It is designed to support:

- Scenario creation and testing
- Feasibility checks and risk flags
- Product requirements and feature prioritization
- Customer communication and contingency planning

The risk areas are grouped into five primary categories:

1. Customer-side risks
2. Vendor-side risks
3. Operational risks
4. External risks
5. SaaS Provider risks

Each category contains high-level risk buckets and concrete examples relevant to agency travel planning.

---

## 1. Customer-side Risks

These are risks that originate from the customer or their travel party.

### 1.1 Budget & expectation risk

- Budget stated is too low for the itinerary.
- Budget excludes critical buckets (flights, transfers, food, insurance, shopping, buffer).
- Customer expects luxury service but books a midrange package.
- Customer underestimates seasonal price inflation.

### 1.2 Document & compliance risk

- Passport validity insufficient for destination requirements.
- Visa or entry authorizations not obtained or not understood.
- Transit visa rules are ignored for multi-leg routes.
- Health certificates, insurance, or vaccination requirements are missing.

### 1.3 Itinerary suitability risk

- Activity level mismatched to traveler composition (senior, toddler, medical restrictions).
- Daily schedule too aggressive for the group.
- Multiple long transfers are planned without adequate rest.
- Customer selects destinations or experiences that are incompatible with physical mobility.

### 1.4 Data quality & assumptions risk

- Customer input is incomplete, ambiguous, or contradictory.
- Dates are fuzzy, destination names are misspelled, or party composition is unclear.
- The customer has hidden constraints not surfaced in the request.
- The customer assumes something that cannot be delivered (e.g., tickets included when they are not).

### 1.5 Payment & commitment risk

- Customer is unwilling to pay deposits or commit to confirmed rates.
- Payment method risk exists (credit authorization, corporate policy, sanction restrictions).
- Refund expectations do not match the supplier or airline policy.

### 1.6 Behavioral & satisfaction risk

- Customer sentiment is negative or uncertain from early interactions.
- There is a mismatch between the customer’s stated goal and the proposed itinerary.
- Customers are likely to overbook or change plans frequently.

### 1.7 Group booking & coordination risk

- Different sub-parties within the same booking have different readiness states.
- One family member has the right documents while another does not.
- Child seat, twin rooms, or family-room requests are not synchronized with the supplier.
- Multiple vendors are not aligned on the same transfer, pick-up time, or itinerary segment.
- One group member wants a different activity than the rest, causing split logistics.

### 1.8 Communication & accessibility risk

- Language barriers prevent effective communication with local suppliers or during travel.
- Time zone differences complicate coordination and support availability.
- Disability accommodations are not requested or not available at destinations.
- Medical emergency communication plans are inadequate for the group.
- Customer has specific dietary, religious, or cultural needs that are not communicated.

### 1.9 Insurance & emergency preparedness risk

- Travel insurance coverage is inadequate for the trip scope or group needs.
- Medical evacuation or emergency response plans are not in place.
- Trip cancellation insurance does not cover the stated reasons.
- Customer assumes coverage that is not included in the policy.
- Emergency contact information is incomplete or outdated.

---

## 2. Vendor-side Risks

These are risks that come from the suppliers, partners, or travel ecosystem.

### 2.1 Supplier availability risk

- Hotels or resorts are sold out, especially in peak season.
- Flights or trains are unavailable on the chosen dates.
- Tour operators have limited capacity for the requested group size.

### 2.2 Supplier reliability risk

- Vendor cancellations or last-minute schedule changes.
- Poor service quality from a contracted supplier.
- Supplier miscommunication or failure to deliver advertised amenities.

### 2.3 Price volatility risk

- Exchange rate movement changes the real cost.
- Fuel surcharges or airline ticket prices spike.
- Local taxes, tourism levies, or supplier fees are added after the quote.

### 2.4 Contract & payment risk

- Supplier contract terms are unfavorable or not fully understood.
- Prepayment terms are too aggressive or non-refundable.
- Supplier credit or settlement risk exists.

### 2.5 Capacity & escalation risk

- Supplier has limited capacity for group transfers or support.
- The operator cannot handle emergencies or late changes.
- There is no backup vendor for critical services.

### 2.6 Service delivery & execution risk

- Driver or transfer provider is unreachable or does not show up.
- Confirmed activity bookings are rejected on arrival (e.g. safari entry denied, attraction sold out).
- Requested equipment is unavailable (child seat, wheelchair, safety gear).
- Supplier reschedules or changes the confirmed service after the booking is made.
- Local vendor mismatch: a family booking gets a vehicle that cannot fit the party.
- Booking confirmation exists but the operational handoff is incomplete.

### 2.7 Quality & reputation risk

- Supplier has poor customer reviews or low ratings on travel platforms.
- Service quality varies significantly from what is advertised.
- Supplier engages in unethical practices (overbooking, false advertising).
- Local reputation issues affect the experience (unsafe areas, unreliable partners).
- Sustainability or ethical concerns with the supplier's operations.

---

## 3. Operational Risks

These are risks from the agency’s own processes, systems, and team.

### 3.1 Technology risk

- Core systems are unavailable due to API outages or infrastructure failure.
- LLM or other AI components hallucinate incorrect plans.
- Data loss, corruption, or incomplete state reconstruction occurs.

### 3.2 Process risk

- The intake workflow does not capture critical details.
- Risk checks are skipped or not enforced in the proposal process.
- There is no clear handoff between design, quoting, and booking stages.

### 3.3 People risk

- The team is overloaded, causing mistakes.
- Key knowledge is held by one person.
- Burnout or sickness removes the only person who can verify final proposals.

### 3.4 Compliance & legal risk

- The product violates privacy or data protection rules.
- The agency provides advice that exceeds its liability boundaries.
- Terms and disclaimers are missing or unclear.

### 3.5 Scaling & capacity risk

- The business cannot support more customers without more staff.
- Monitoring and alerting are absent for high-risk behavior.
- Support capacity is insufficient for urgent itinerary changes.

### 3.6 Security & fraud risk

- Customer data is exposed due to inadequate security measures.
- Payment processing is vulnerable to fraud or chargebacks.
- AI-generated content includes biased or harmful information.
- Third-party integrations introduce security vulnerabilities.
- Regulatory compliance for data protection is not maintained.

---

## 4. External Risks

These are risks outside the direct control of the customer, vendor, or agency.

### 4.1 Market & macro risk

- Travel demand shifts suddenly due to macroeconomic changes.
- Competitors launch similar solutions or pricing.
- Payment, banking, or regulatory changes affect the market.

### 4.2 Geopolitical & regulatory risk

- Travel bans, border closures, or visa policy changes occur.
- Sanctions or geopolitical events affect routes or suppliers.
- Local regulations change for entry requirements or tourism operations.

### 4.3 Weather & natural disaster risk

- Seasonal weather disrupts flights, tours, or activities.
- Natural disasters force cancellations or route changes.
- Extreme weather affects safety and insurance coverage.

### 4.4 Third-party dependency risk

- Airline, hotel, payment gateway, or data provider outages.
- Global LLM provider downtime or rate limiting.
- API changes from key integrations.

### 4.5 Health & pandemic risk

- New health advisories or pandemic restrictions are imposed.
- Destination-specific medical risks are higher than assumed.
- Health infrastructure in-country is insufficient for the group.

### 4.6 Transport & schedule disruption risk

- Flights are delayed, canceled, or rescheduled, affecting connections.
- Transfers are delayed due to traffic, airport logistics, or driver no-show.
- Booked train, ferry, or shuttle legs are changed by the carrier.
- A multi-leg itinerary is exposed to cascading delays across suppliers.
- Last-minute flight or transfer changes create customer service and rebooking load.

### 4.7 Economic & inflation risk

- Currency exchange rates fluctuate significantly, affecting costs.
- Inflation in destination countries increases local prices unexpectedly.
- Economic downturns reduce travel demand or supplier capacity.
- Fuel price increases lead to higher transportation costs.
- Global economic events impact travel insurance premiums or availability.

### 4.8 Cybersecurity & digital infrastructure risk

- Travel booking platforms or airline systems are hacked, causing data breaches.
- Digital infrastructure failures affect airport operations or border controls.
- Phishing attacks target travelers with fake booking confirmations.
- Online payment systems are compromised during peak booking periods.
- GPS or navigation systems fail, affecting transfers and activities.

---

## 5. SaaS Provider Risks

These are risks specific to operating the travel agency agent as a software platform and business.

### 5.1 Platform availability & uptime risk

- Service outages due to infrastructure failures or DDoS attacks.
- API rate limiting affects customer usage during peak periods.
- Database performance degrades under high load, causing slow responses.
- Third-party service dependencies (LLMs, payment processors) become unavailable.
- Maintenance windows or deployments cause unexpected downtime.

### 5.2 Data security & privacy risk

- Customer travel data is breached or leaked.
- Inadequate encryption of sensitive information (passports, payment details).
- Non-compliance with GDPR, CCPA, or other data protection regulations.
- Data residency requirements are not met for international customers.
- Third-party data processors introduce security vulnerabilities.

### 5.3 Scalability & performance risk

- User growth outpaces infrastructure capacity.
- Compute costs spike unexpectedly with increased usage.
- Database queries become inefficient as data volume grows.
- API response times degrade under concurrent load.
- Resource allocation is not optimized for cost-efficiency.

### 5.4 Third-party dependency risk

- API keys or credentials for external services are compromised.
- Third-party providers change terms, pricing, or deprecate services.
- Integration failures occur when external APIs change.
- Vendor lock-in makes migration difficult or expensive.
- Supply chain attacks affect open-source dependencies.

### 5.5 Cost management & financial risk

- Cloud infrastructure costs exceed revenue projections.
- Unexpected usage spikes lead to budget overruns.
- Payment processor fees or currency conversion losses.
- Insurance premiums for cyber liability become unaffordable.
- Capital expenditure for hardware or software licenses.

### 5.6 Product liability & legal risk

- AI-generated travel advice leads to customer harm or financial loss.
- Platform is used for illegal activities (sanctions violations, unsafe travel).
- Intellectual property disputes over training data or generated content.
- Class action lawsuits from dissatisfied customers.
- Regulatory changes require expensive platform modifications.

### 5.7 Customer success & retention risk

- High churn rate due to poor user experience or feature gaps.
- Customer support capacity cannot scale with user growth.
- Onboarding process fails to convert trial users to paid customers.
- Feature requests from power users are not prioritized.
- Negative reviews or word-of-mouth damage reputation.

### 5.8 Competitive & market risk

- Competitors launch similar AI travel planning features.
- Market saturation reduces pricing power.
- Customer acquisition costs increase due to competition.
- Technology becomes commoditized, reducing differentiation.
- Strategic partnerships fail or competitors acquire key allies.

### 5.9 Regulatory & compliance risk

- Travel industry regulations change (airline codes, booking standards).
- AI-specific regulations emerge (bias, transparency, explainability).
- International tax implications for SaaS revenue.
- Export controls affect global expansion.
- Accessibility requirements (WCAG) are not met.

### 5.10 Operational & team risk

- Key technical talent leaves, creating knowledge gaps.
- Development velocity slows due to technical debt.
- Security incidents erode customer trust.
- Burnout affects product quality and innovation.
- Remote work challenges impact team collaboration.

---

## Using this Catalog

### Scenario generation

Use these categories to build investigative scenario notes with focused risk axes. For example:

- A budget scenario that crosses customer and vendor budget buckets.
- A visa scenario that combines customer document and external regulation risk.
- A transfer scenario that combines customer mobility and vendor supplier availability.

### Product design

This catalog can inform risk flags, follow-up questions, and proposal advisories. Each risk bucket should map to one or more outputs:

- `verdict`
- `risks[]`
- `critical_changes[]`
- `must_confirm[]`
- `alternative`

### Operational readiness

The agency should treat this catalog as a checklist for launch readiness. If a risk area is not explicitly covered by the product or process, it should be elevated for mitigation.

---

## Recommended next step

Turn this catalog into a risk taxonomy table in the product model, where each risk area includes:

- `risk_id`
- `category`
- `short_name`
- `description`
- `signals`
- `mitigation`
- `severity`

That makes the catalog machine-readable and easier to test against scenarios.
