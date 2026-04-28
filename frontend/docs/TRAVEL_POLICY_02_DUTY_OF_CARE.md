# Travel Policy & Duty of Care — Duty of Care

> Research document for traveler tracking, risk assessment, emergency protocols, and employer duty of care obligations during business travel.

---

## Key Questions

1. **What are the legal duty of care obligations for employers sending employees on travel?**
2. **How do we track traveler location in real-time during trips?**
3. **What risk assessment framework applies to travel destinations?**
4. **What emergency protocols must be in place?**
5. **How do we communicate with travelers during crises?**

---

## Research Areas

### Duty of Care Legal Framework

```typescript
interface DutyOfCareFramework {
  legalObligations: LegalObligation[];
  riskAssessment: RiskAssessment;
  travelerTracking: TravelerTracking;
  emergencyProtocols: EmergencyProtocol[];
  communication: CrisisCommunication;
}

interface LegalObligation {
  jurisdiction: string;                // "India", "EU", "US", "UK"
  law: string;                        // "Occupational Health & Safety Act"
  requirement: string;                // What employers must do
  penalty: string;                    // Consequences of non-compliance
}

// Duty of care obligations by jurisdiction:
//
// INDIA:
// - Occupational Safety, Health and Working Conditions Code, 2020
// - Employers must ensure employee safety during work-related travel
// - Must provide travel insurance for international trips
// - Must have emergency response plan
// - Liability for negligence in case of injury/death during business travel
// - Not as codified as EU/US, but growing judicial precedent
// - Penalty: Civil liability for damages, criminal negligence in extreme cases
//
// EUROPEAN UNION:
// - EU Directive 89/391/EEC (Framework Directive on OSH)
// - Employers must assess risks before sending employees abroad
// - Must provide information about destination risks
// - Must ensure adequate insurance coverage
// - Must have means to contact and assist travelers
// - Penalty: Significant fines, criminal liability in severe cases
//
// UNITED STATES:
// - OSHA General Duty Clause
// - No specific travel duty of care law, but case law establishes obligation
// - Duty to warn of known dangers at destination
// - Duty to provide reasonable safety measures
// - Penalty: Lawsuits for negligence, workers' compensation claims
//
// Key obligations (universal):
// 1. Pre-trip risk assessment for destination
// 2. Travel insurance coverage (medical, evacuation, repatriation)
// 3. Real-time traveler tracking and communication capability
// 4. Emergency response plan and 24/7 support
// 5. Post-incident support (medical, legal, psychological)
// 6. Documentation of all safety measures taken

// Duty of care checklist per trip:
// [ ] Destination risk assessment completed
// [ ] Traveler briefed on destination risks and safety measures
// [ ] Travel insurance purchased (medical, evacuation, repatriation)
// [ ] Emergency contact numbers provided to traveler
// [ ] Embassy/consulate contact information for destination country
// [ ] Passport validity checked (6+ months remaining)
// [ ] Visa requirements verified and obtained
// [ ] Vaccination requirements checked and completed
// [ ] Medical conditions noted, medication arranged
// [ ] Communication plan established (check-in schedule)
// [ ] Traveler tracking activated (GPS / app-based)
// [ ] Emergency evacuation plan confirmed
// [ ] Company emergency hotline shared with traveler
// [ ] Next of kin emergency contact recorded
```

### Traveler Tracking System

```typescript
interface TravelerTracking {
  active: ActiveTraveler[];
  checkIns: CheckInRecord[];
  location: LocationTracking;
  alerts: TrackingAlert[];
}

interface ActiveTraveler {
  travelerId: string;
  name: string;
  companyId: string;
  trip: TripSummary;
  currentLocation: TravelerLocation;
  checkInStatus: CheckInStatus;
  riskLevel: RiskLevel;
  insurance: InsuranceStatus;
  emergencyContacts: EmergencyContact[];
}

interface TripSummary {
  tripId: string;
  destination: string;
  departureDate: Date;
  returnDate: Date;
  purpose: string;                     // "Client meeting"
  flightDetails: FlightSummary;
  hotelDetails: HotelSummary;
  itinerary: DailyLocation[];
}

interface TravelerLocation {
  lastKnown: GeoLocation;
  lastUpdated: Date;
  source: LocationSource;
  accuracy: string;                    // "city", "hotel", "exact"
}

type LocationSource =
  | 'flight_data'                      // From airline booking (origin/destination)
  | 'hotel_checkin'                    // Hotel check-in data
  | 'app_gps'                          // Mobile app GPS (opt-in)
  | 'manual_checkin'                   // Traveler manual check-in
  | 'wifi_location'                    // WiFi-based location (corporate network)
  | 'cell_tower';                      // Cell tower triangulation

// Location tracking approach:
// Privacy-preserving, opt-in model:
// 1. Flight data: Automatic (from booking system)
//    - Know: Departure airport, arrival airport, flight times
//    - Don't know: Exact location between flights
//
// 2. Hotel check-in: Automatic (from booking system)
//    - Know: Hotel name, address, check-in/out dates
//    - Accurate: City-level location during hotel stay
//
// 3. Manual check-in: Traveler-initiated
//    - Traveler checks in via app: "Arrived at hotel" / "At client office"
//    - Required: Once per day for high-risk destinations
//    - Required: At each new city/location
//
// 4. GPS tracking (opt-in): Mobile app
//    - Continuous GPS only during active trip dates
//    - Data purged 30 days after trip completion
//    - Only accessible by travel admin and emergency response team
//    - Traveler can disable anytime (notifies admin)
//
// Privacy requirements:
// - Location data is personal data under DPDP Act (India), GDPR (EU)
// - Must obtain explicit consent before GPS tracking
// - Purpose limitation: Safety only, not productivity monitoring
// - Data retention: Purge 30 days after trip completion
// - Access control: Travel admin + emergency team only
// - Traveler can view and export their own location data
// - No location data sharing with third parties

interface CheckInStatus {
  lastCheckIn: Date;
  nextCheckInDue: Date;
  frequency: CheckInFrequency;
  overdue: boolean;
  overdueBy?: number;                  // Minutes
}

type CheckInFrequency =
  | 'none'                             // Low-risk destination
  | 'daily'                            // Standard business travel
  | 'twice_daily'                      // High-risk destination
  | 'every_4_hours';                   // Very high risk / active crisis

// Check-in workflow:
// System sends check-in reminder (push notification + email + SMS)
// Traveler responds: "I'm safe" or provides location update
// If no response within 2 hours:
//   1. Retry notification (all channels)
//   2. Call traveler's mobile phone
//   3. Call hotel (if known)
//   4. Contact local emergency services (if high risk)
//   5. Notify company travel admin and emergency contact
//   6. Activate crisis response protocol

type RiskLevel = 'low' | 'medium' | 'high' | 'very_high' | 'critical';

// Risk level assessment:
// Low: Stable country, low crime, good healthcare, no travel advisories
//   Example: Singapore, Japan, most of Western Europe
//   Check-in: None required
//
// Medium: Generally safe, some areas of concern
//   Example: India (most cities), Thailand, UAE, South Africa
//   Check-in: Daily
//
// High: Elevated risk factors
//   Example: Parts of Africa, Middle East, South America
//   Check-in: Twice daily
//   Requirements: Pre-trip briefing, enhanced insurance
//
// Very High: Active travel advisory
//   Example: Conflict zones, post-disaster areas, political unrest
//   Check-in: Every 4 hours
//   Requirements: Executive approval, security briefing, GPS tracking
//
// Critical: Active crisis (natural disaster, terrorist incident, pandemic)
//   Check-in: Continuous monitoring
//   Requirements: Immediate response protocol, evacuation planning
```

### Risk Assessment Framework

```typescript
interface RiskAssessment {
  destination: DestinationRisk;
  traveler: TravelerRiskProfile;
  trip: TripRiskFactors;
  composite: CompositeRiskScore;
}

interface DestinationRisk {
  destination: string;
  categories: RiskCategory[];
  overall: RiskLevel;
  lastAssessed: Date;
  sources: RiskDataSource[];
}

interface RiskCategory {
  name: RiskCategoryName;
  level: RiskLevel;
  details: string;
  mitigation: string;                  // Recommended mitigation
  source: string;                      // "MEF Travel Risk Map"
}

type RiskCategoryName =
  | 'political'                        // Political stability, government type
  | 'security'                         // Crime, terrorism, civil unrest
  | 'health'                           // Disease, medical facilities, air quality
  | 'natural_disaster'                 // Earthquake, flood, hurricane risk
  | 'infrastructure'                   // Road safety, aviation safety, utilities
  | 'legal'                            // Legal system, detention risk, consular access
  | 'cultural'                         // Cultural sensitivities, religious restrictions
  | 'cyber'                            // Cyber security, data privacy, surveillance
  | 'environmental';                   // Pollution, climate hazards, wildlife

// Risk data sources:
// 1. Government travel advisories:
//    - MEA India (Advisories for Indians abroad): mea.gov.in
//    - US State Department Travel Advisories: travel.state.gov
//    - UK FCDO Travel Advice: gov.uk/foreign-travel-advice
//    - Australian DFAT Smartraveller: smartraveller.gov.au
//
// 2. Commercial risk intelligence:
//    - International SOS Travel Risk Map: internationalsos.com
//    - Control Risks: controlrisks.com
//    - WorldAware (formerly iJET): worldaware.com
//
// 3. Health data:
//    - WHO Disease Outbreak News: who.int
//    - CDC Travel Health Notices: cdc.gov/travel
//    - India National Centre for Disease Control: ncdc.gov.in
//
// 4. Security data:
//    - Global Terrorism Database: start.umd.edu/gtd
//    - OSAC (US Overseas Security Advisory Council): osac.gov
//
// 5. Natural disaster:
//    - GDACS (Global Disaster Alert System): gdacs.org
//    - India NDMA (National Disaster Management Authority): ndma.gov.in

// Risk assessment workflow:
// 1. Agent creates corporate travel booking
// 2. System auto-assesses destination risk from data sources
// 3. Risk score compared against company policy thresholds
//    - Low/Medium: Auto-approved (with safety briefing)
//    - High: Requires travel admin approval + pre-trip briefing
//    - Very High: Requires executive approval + security briefing + GPS tracking
//    - Critical: Blocked (manual override requires CEO approval)
// 4. Pre-trip safety package generated:
//    - Destination risk summary
//    - Emergency numbers and embassy contacts
//    - Health recommendations and vaccination requirements
//    - Cultural sensitivity notes
//    - Transportation safety advice
//    - Communication plan (check-in schedule)
// 5. Travel insurance requirements calculated:
//    - Medical coverage minimum by destination
//    - Evacuation coverage for high-risk destinations
//    - Repatriation coverage for all international travel
```

### Emergency Response Protocols

```typescript
interface EmergencyProtocol {
  id: string;
  trigger: EmergencyTrigger;
  level: EmergencyLevel;
  actions: EmergencyAction[];
  escalation: EmergencyEscalation;
  communication: EmergencyCommunication;
}

type EmergencyTrigger =
  | 'natural_disaster'                 // Earthquake, flood, hurricane
  | 'political_unrest'                 // Civil unrest, coup, protests
  | 'terrorist_incident'               // Terrorist attack in traveler's vicinity
  | 'health_emergency'                 // Disease outbreak, pandemic
  | 'traveler_missing'                 // Check-in overdue, cannot contact
   | 'traveler_medical'                // Traveler hospitalized or injured
  | 'traveler_arrest'                  // Traveler detained by authorities
  | 'flight_disruption'                // Major flight cancellation, airport closure
  | 'infrastructure_failure';          // Major power outage, telecom failure

type EmergencyLevel =
  | 'monitor'                          // Situation developing, monitor only
  | 'alert'                            // Active concern, prepare response
  | 'response'                         // Active response required
  | 'crisis';                          // Full crisis management activated

// Emergency response playbook:
//
// NATURAL DISASTER (e.g., earthquake in traveler's destination):
// Monitor: Earthquake detected near destination
//   → Check if any travelers in affected area
//   → Pull traveler location data
//   → Send "Are you safe?" check-in request
//
// Alert: Earthquake confirmed, significant magnitude
//   → Activate response team
//   → Attempt contact with all travelers in area
//   → Assess local infrastructure (airport, hospital, telecom)
//   → Issue travel advisory for incoming travelers
//
// Response: Confirmed impact on travelers
//   → Coordinate with local emergency services
//   → Arrange alternative accommodation if hotel damaged
//   → Arrange evacuation flights if airport operational
//   → Contact families / next of kin (with traveler consent)
//   → Coordinate with embassy / consulate
//   → Arrange medical assistance if needed
//
// Crisis: Widespread disaster, multiple travelers affected
//   → Full crisis management team activated
//   → Dedicated hotline for affected travelers
//   → Family liaison team for next of kin
//   → Media relations (if public attention)
//   → Insurance claims coordination
//   → Post-crisis support (medical, psychological)

// Communication during emergencies:
// Channel priority:
// 1. SMS (most reliable, works on basic phones)
// 2. WhatsApp (high adoption in India, works on WiFi)
// 3. Phone call (for direct contact)
// 4. Email (for detailed instructions)
// 5. App push notification (if app installed)
// 6. Company emergency hotline (reverse: traveler calls in)
//
// Communication templates:
// "EMERGENCY: [Event] reported in [Location]. Are you safe?
//  Reply SAFE or call [Emergency Number]. Do NOT travel to [Area]."
//
// "UPDATE: [Event] situation in [Location]. Your flight [Number] on [Date]
//  has been [cancelled/redirected]. New arrangement: [Details].
//  Contact [Agent Name] at [Number] for assistance."

// Post-traveler-incident support:
// Medical: Insurance claim filing, medical records transfer
// Legal: Legal counsel if arrested, embassy liaison
// Psychological: Counseling services (confidential)
// Financial: Emergency fund advance, expense reimbursement
// Travel: Rebooking, early return arrangement
// Documentation: Incident report, lessons learned
```

---

## Open Problems

1. **Privacy vs. safety trade-off** — GPS tracking provides the best traveler safety but faces resistance from employees who see it as surveillance. Building trust through transparency and strict data controls is essential.

2. **Risk data timeliness** — Travel advisories from governments are often slow to update. Commercial risk intelligence is expensive. Crowd-sourced risk data (social media, news) is fast but unreliable.

3. **International coordination** — When a crisis hits a foreign country, the agency must coordinate with local authorities, embassies, insurance companies, and airlines — all with different operating hours, languages, and processes.

4. **Traveler non-compliance** — Travelers may disable tracking, skip check-ins, or ignore safety briefings. Enforcing compliance without being heavy-handed is an ongoing challenge.

5. **Cost of duty of care** — Comprehensive duty of care (tracking, insurance, emergency response) adds ₹500-2,000 per trip. Companies may resist the cost until an incident demonstrates the value.

---

## Next Steps

- [ ] Build traveler tracking system with privacy-preserving location management
- [ ] Create risk assessment engine with automated destination scoring
- [ ] Design emergency response protocol library with playbooks
- [ ] Implement check-in system with escalating notification chain
- [ ] Study duty of care platforms (International SOS, WorldAware, Concur Risk Messaging)
