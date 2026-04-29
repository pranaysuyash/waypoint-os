# Travel Risk Assessment 02: Traveler Safety

> Research document for real-time traveler tracking, emergency SOS systems, geo-fencing, safe check-ins, and traveler risk profiling with India-specific embassy and consulate integration.

---

## Document Overview

**Focus:** Traveler safety features and real-time protection systems
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Real-Time Tracking
- How do we track traveler location in real-time while respecting privacy?
- What location sources are available? (GPS, flight data, hotel check-in, manual)
- How granular should tracking be? Country-level? City-level? Exact GPS?
- What are the privacy regulations (India DPDP Act, GDPR) around traveler tracking?

### 2. Geo-Fencing
- How do we define dangerous zones and alert travelers approaching them?
- What data sources define dangerous areas? (Crime maps, conflict zones, disaster areas)
- How do we prevent false positives that cause unnecessary panic?
- How do geo-fences change in real-time during evolving incidents?

### 3. Emergency SOS
- What does one-tap SOS activation look like on mobile?
- What happens after SOS is triggered? (Agent notification, emergency services, family)
- How do we handle SOS when the traveler has no connectivity?
- What are the legal implications of providing emergency coordination?

### 4. Safe Check-In System
- How frequently should travelers check in? Does it vary by risk level?
- What happens when a traveler misses a check-in?
- How do we make check-ins frictionless to ensure compliance?
- Can we automate check-ins via location data?

### 5. Traveler Risk Profile
- How do demographics (age, health conditions, nationality) affect risk?
- How do we build a risk profile without being discriminatory?
- How does prior travel experience factor into risk assessment?
- What data can we ethically collect and use for profiling?

### 6. India-Specific Integration
- How do we integrate with Indian embassy/consulate emergency services?
- What is the MEA helpline workflow? (+91-11-2301 2113, Toll-free 1800-11-3029)
- How does the MADAD portal work for Indian citizens in distress abroad?
- What coordination is needed with NRI/PIO cell in Indian missions?

---

## Research Areas

### A. Real-Time Tracking Architecture

```typescript
interface TravelerTrackingSystem {
  travelers: ActiveTravelerTracking[];
  geoFences: GeoFence[];
  checkInSchedule: CheckInSchedule[];
  sosAlerts: SOSAlert[];
}

interface ActiveTravelerTracking {
  trackingId: string;
  travelerId: string;
  tripId: string;
  status: TrackingStatus;
  currentLocation: TravelerLocation;
  locationHistory: LocationRecord[];
  checkInStatus: CheckInStatus;
  riskProfile: TravelerRiskProfile;
  emergencyContacts: EmergencyContact[];
  privacySettings: TrackingPrivacy;
}

type TrackingStatus =
  | 'active_tracking'       // GPS tracking enabled, real-time
  | 'passive_tracking'      // Flight + hotel data only
  | 'check_in_only'         // Manual check-in, no GPS
  | 'offline'               // No connectivity
  | 'sos_active'            // Emergency SOS in progress
  | 'trip_ended';           // Tracking concluded

interface TravelerLocation {
  latitude: number;
  longitude: number;
  accuracy: LocationAccuracy;
  source: LocationSource;
  timestamp: Date;
  address?: string;
  region?: string;
  country: string;
}

type LocationAccuracy =
  | 'exact'                 // GPS-level (~10m)
  | 'neighborhood'          // ~1km
  | 'city'                  // ~10km
  | 'region'                // ~50km
  | 'country';              // Only country known

type LocationSource =
  | 'gps'                   // Mobile app GPS (opt-in)
  | 'flight_booking'        // Derived from flight reservation
  | 'hotel_checkin'         // Derived from hotel booking
  | 'manual_checkin'        // Traveler checked in via app
  | 'wifi_positioning'      // WiFi-based location
  | 'cell_tower'            // Cell tower triangulation
  | 'ip_geolocation';       // Approximate from IP address

interface TrackingPrivacy {
  trackingLevel: TrackingLevel;
  shareWithFamily: boolean;
  shareWithAgent: boolean;
  shareWithEmployer: boolean;         // For corporate travel
  dataRetentionDays: number;
  allowHistoricalReview: boolean;
}

type TrackingLevel =
  | 'full_gps'              // Real-time GPS tracking
  | 'city_level'            // Only city-level location shared
  | 'check_in_only'         // Only manual check-ins
  | 'none';                 // No tracking (emergency only)

// Privacy approach:
// - Default: passive_tracking (flight + hotel data from bookings)
// - Upgrade: Traveler opts in to GPS tracking
// - High-risk destinations: Encourage full GPS, require check-in
// - GDPR/DPDP compliance: Clear consent, data minimization, right to delete
// - Data retention: 90 days post-trip by default, configurable
```

### B. Geo-Fencing System

```typescript
interface GeoFence {
  fenceId: string;
  name: string;                        // "Downtown Nairobi - High Crime Zone"
  type: GeoFenceType;
  geometry: GeoFenceGeometry;
  riskLevel: RiskLevel;
  riskTypes: RiskDimensionType[];
  description: string;
  validFrom: Date;
  validUntil?: Date;                   // Ongoing if null
  source: string;                      // "MEA Advisory", "Local police", "Commercial intel"
  alertConfig: GeoFenceAlertConfig;
}

type GeoFenceType =
  | 'danger_zone'            // Known high-crime or conflict area
  | 'restricted_area'        // Government-restricted, no-go zone
  | 'disaster_zone'          // Active natural disaster area
  | 'health_risk'            // Disease outbreak zone
  | 'civil_unrest'           // Active protests, curfew area
  | 'border_sensitive'       // Sensitive border region
  | 'natural_hazard'         // Flood-prone, landslide-prone area
  | 'custom';                // Agent-defined fence

interface GeoFenceGeometry {
  type: 'circle' | 'polygon' | 'corridor';
  // Circle: center point + radius
  center?: { lat: number; lng: number };
  radiusKm?: number;
  // Polygon: list of coordinates
  points?: { lat: number; lng: number }[];
  // Corridor: path + width (for roads, routes)
  path?: { lat: number; lng: number }[];
  widthKm?: number;
}

interface GeoFenceAlertConfig {
  alertTraveler: boolean;
  alertAgent: boolean;
  alertFamily: boolean;
  triggerOnEnter: boolean;             // Alert when traveler enters zone
  triggerOnProximity: boolean;         // Alert when traveler is within X km
  proximityThresholdKm: number;
  severity: AlertSeverity;
  message: string;                     // Pre-configured alert message
  recommendations: string[];           // "Avoid area after dark", "Use taxi not walk"
}

// Geo-fence examples for Indian travelers:
//
// 1. Nairobi, Kenya:
//    - Eastleigh neighborhood: High crime, terrorism risk
//    - Geo-fence: circle, 2km radius around Eastleigh center
//    - Alert: "Avoid Eastleigh area. High crime and security incident risk."
//
// 2. Bangkok, Thailand:
//    - Protest areas during political unrest (dynamic, event-based)
//    - Geo-fence: polygon around protest sites (updated in real-time)
//    - Alert: "Political protest in progress. Avoid the area."
//
// 3. Jammu & Kashmir, India:
//    - Border areas: Restricted, security risk
//    - Geo-fence: corridor along LOC
//    - Alert: "Restricted area. Travel only with authorized permits."
//
// 4. Bali, Indonesia:
//    - Mount Agung exclusion zone during volcanic activity
//    - Geo-fence: circle, 4km radius around crater
//    - Alert: "Volcanic activity. Stay outside exclusion zone."
```

### C. Emergency SOS System

```typescript
interface SOSAlert {
  alertId: string;
  travelerId: string;
  tripId: string;
  activatedAt: Date;
  status: SOSStatus;
  location: TravelerLocation;
  travelerMessage?: string;            // Voice/text note from traveler
  response: SOSResponse;
  escalation: SOSEscalation[];
}

type SOSStatus =
  | 'active'                 // SOS triggered, awaiting response
  | 'acknowledged'           // Agent/emergency team acknowledged
  | 'assistance_en_route'    // Help is on the way
  | 'resolved'               // Situation resolved
  | 'false_alarm'            // Traveler confirmed false alarm
  | 'timed_out';             // No response within threshold

interface SOSResponse {
  acknowledgedBy: string;
  acknowledgedAt?: Date;
  actionPlan: string;
  contactsNotified: SOSNotification[];
  emergencyServices: EmergencyServiceContact[];
  timeline: SOSResponseEvent[];
}

interface SOSEscalation {
  level: number;                       // 1 = agent, 2 = agency owner, 3 = emergency services
  triggeredAt: Date;
  triggeredBy: string;
  action: string;
  contactsNotified: string[];
}

// SOS activation flow:
//
// 1. Traveler activates SOS (one-tap or hold-3-seconds)
//    - App sends: GPS location + trip ID + traveler ID + timestamp
//    - If offline: Queues for delivery when connectivity resumes
//    - Optional: Traveler can add voice note or select emergency type
//
// 2. System processes SOS
//    - Matches to assigned agent
//    - Loads trip details, destination, local emergency numbers
//    - Checks destination risk level and active advisories
//    - Starts escalation timer
//
// 3. Agent notification (immediate)
//    - Push notification + SMS + in-app alert
//    - Agent sees: traveler location, trip details, emergency contacts
//    - Agent must acknowledge within 5 minutes
//
// 4. If not acknowledged → Escalation Level 2
//    - Agency owner / emergency team notified
//    - Agency emergency protocol activated
//
// 5. If critical situation → Escalation Level 3
//    - Local emergency services contacted
//    - Indian embassy/consulate notified (for international trips)
//    - Family emergency contact notified
//    - Insurance provider alerted (if travel insurance purchased)
//
// 6. Resolution and documentation
//    - All actions logged with timestamps
//    - Post-incident report generated
//    - Insurance claim triggered if applicable

interface EmergencyServiceContact {
  type: 'police' | 'ambulance' | 'fire' | 'consulate' | 'embassy';
  name: string;
  phone: string;
  country: string;
  notes?: string;
}

// India-specific emergency contacts:
//
// DOMESTIC (India):
// Police: 100 (or 112 for emergency)
// Ambulance: 108 (or 112)
// Fire: 101
// Women helpline: 1090, 181
// Tourism helpline: 1363 (MoTourism)
// Railway emergency: 139
// NDRF control room: +91-11-24363260
//
// INTERNATIONAL (Indian citizens abroad):
// MEA helpline: +91-11-2301 2113
// MEA toll-free: 1800-11-3029 (from India)
// MADAD portal: madad.gov.in (Register grievances)
// Indian Embassy/Consulate: varies by country
//
// For Indian missions abroad, we maintain a database:
// - Country → Embassy/Consulate details
// - Emergency contact numbers
// - Working hours vs. after-hours emergency
// - Email for consular services
```

### D. Safe Check-In System

```typescript
interface CheckInSchedule {
  scheduleId: string;
  travelerId: string;
  tripId: string;
  frequency: CheckInFrequency;
  nextCheckInDue: Date;
  gracePeriod: number;                 // Minutes after due time before escalation
  missedCheckIns: MissedCheckIn[];
}

type CheckInFrequency =
  | { type: 'daily'; time: string }              // "Daily at 20:00 local time"
  | { type: 'per_location'; onArrival: boolean; onDeparture: boolean }
  | { type: 'interval'; hours: number }          // "Every 6 hours"
  | { type: 'risk_based'; rules: RiskBasedCheckInRule[] };

interface RiskBasedCheckInRule {
  destinationRiskLevel: RiskLevel;
  frequency: CheckInFrequency;
  escalationOnMiss: boolean;
}

// Risk-based check-in defaults:
// Risk 1 (Minimal):   Optional, once-per-trip check-in
// Risk 2 (Low):       Daily check-in recommended
// Risk 3 (Medium):    Daily check-in required, auto-escalate if missed
// Risk 4 (High):      Twice-daily check-in, immediate escalation if missed
// Risk 5 (Critical):  Hourly check-in or GPS tracking, consider evacuation

interface CheckInRecord {
  checkInId: string;
  travelerId: string;
  tripId: string;
  timestamp: Date;
  type: CheckInType;
  location?: TravelerLocation;
  status: 'safe' | 'need_assistance' | 'emergency';
  message?: string;
  automated: boolean;                  // Was this auto-generated from GPS/booking data?
}

type CheckInType =
  | 'manual'                 // Traveler tapped "I'm safe"
  | 'scheduled'              // Response to scheduled check-in prompt
  | 'location_auto'          // Auto-generated from location data
  | 'sos'                    // Triggered via SOS button
  | 'arrival'                // At new destination/city
  | 'departure';             // Leaving a destination

interface MissedCheckIn {
  scheduledTime: Date;
  gracePeriodEnd: Date;
  escalationStatus: 'pending' | 'contacting_traveler' | 'contacting_agent'
                  | 'contacting_family' | 'contacting_authorities' | 'resolved';
  resolution?: string;
}

// Check-in UX on mobile (low friction):
//
// ┌──────────────────────────────────────┐
// │  Safe Check-In              9:41 PM  │
// │                                      │
// │  ┌──────────────────────────────┐    │
// │  │                              │    │
// │  │     I'M SAFE                 │    │
// │  │     (tap to check in)        │    │
// │  │                              │    │
// │  └──────────────────────────────┘    │
// │                                      │
// │  ┌─────────┐  ┌─────────┐           │
// │  │ Need    │  │  SOS    │           │
// │  │ Help    │  │  🚨     │           │
// │  └─────────┘  └─────────┘           │
// │                                      │
// │  Last check-in: Today 9:00 PM       │
// │  Next check-in: Tomorrow 9:00 AM    │
│  │  Location: Singapore, Marina Bay   │
// │                                      │
// └──────────────────────────────────────┘
```

### E. Traveler Risk Profile

```typescript
interface TravelerRiskProfile {
  profileId: string;
  travelerId: string;
  demographics: TravelerDemographics;
  healthFactors: HealthFactors;
  travelHistory: TravelHistorySummary;
  currentRiskModifiers: RiskModifier[];
  compositeRiskScore: number;          // 0-100, higher = more at-risk
}

interface TravelerDemographics {
  age: number;
  gender?: string;                     // Optional — only used for risk assessment
  nationality: string;
  residentCountry: string;
  languagesSpoken: string[];           // Affects communication in emergencies
  travelExperienceLevel: 'novice' | 'intermediate' | 'experienced';
}

interface HealthFactors {
  hasPreExistingConditions: boolean;
  conditions?: string[];               // Encrypted, only shared with medical providers
  requiresMedication: boolean;
  medicationDetails?: string;          // Encrypted
  mobilityLimitations: boolean;
  allergies?: string[];
  bloodGroup?: string;
  emergencyMedicalNotes?: string;      // Free text, encrypted
  travelVaccinations: VaccinationRecord[];
}

interface VaccinationRecord {
  vaccine: string;                     // "Yellow Fever", "COVID-19", "Hepatitis B"
  date: Date;
  validUntil?: Date;
  certificateNumber?: string;
}

// Risk modifiers based on traveler profile:
//
// Higher risk factors:
//   - Age > 65 or < 12: +10 to composite score
//   - Pre-existing conditions: +15
//   - First-time international traveler: +10
//   - Solo traveler: +5
//   - Doesn't speak local language: +5
//   - No travel insurance: +10
//   - Traveling to high-altitude destination (>3000m): +5
//
// Lower risk factors:
//   - Experienced traveler (5+ international trips): -10
//   - Fluent in destination language: -5
//   - Comprehensive travel insurance: -5
//   - Group travel (4+ people): -5
//   - Business travel with corporate support: -5

interface RiskModifier {
  factor: string;
  impact: number;                      // Positive = increases risk
  category: 'demographic' | 'health' | 'experience' | 'trip' | 'insurance';
}

interface TravelHistorySummary {
  totalTrips: number;
  internationalTrips: number;
  countriesVisited: string[];
  previousIncidents: TravelIncident[];
  averageTripsPerYear: number;
}

interface TravelIncident {
  tripId: string;
  type: 'medical' | 'safety' | 'lost_document' | 'missed_flight' | 'other';
  description: string;
  resolved: boolean;
}
```

### F. Indian Embassy/Consulate Integration

```typescript
interface IndianMissionDatabase {
  missions: IndianMission[];
}

interface IndianMission {
  missionId: string;
  type: 'embassy' | 'high_commission' | 'consulate' | 'consulate_general';
  country: string;
  city: string;
  address: string;
  phone: string;
  emergencyPhone: string;              // After-hours emergency
  email: string;
  consularEmail: string;
  workingHours: string;
  website: string;
  services: MissionService[];
}

type MissionService =
  | 'passport'               // Passport renewal, replacement
  | 'visa'                   // Visa services (for foreigners, info)
  | 'attestation'            // Document attestation
  | 'nri_registration'       // NRI/OCI registration
  | 'emergency_travel'       // Emergency travel document
  | 'repatriation'           // Repatriation coordination
  | 'legal_assistance'       // Legal aid coordination
  | 'death_registration'     // Death abroad registration
  | 'prisoner_welfare'       // Welfare of Indian nationals in custody
  | 'distress_assistance';   // General distress assistance

// MADAD portal integration:
// - URL: madad.gov.in
// - Indian citizens can register consular grievances
// - Track grievance status online
// - Types: Bereavement, Arrest, Detention, Robbery, Accident, Hospitalization
// - Integration: Pre-fill grievance form with traveler data
// - Note: MADAD is for Indian citizens only

// MEA emergency coordination workflow:
//
// 1. Indian citizen in distress abroad
// 2. Agency/traveler contacts MEA helpline (+91-11-2301 2113)
// 3. MEA connects to nearest Indian mission
// 4. Mission provides consular assistance:
//    - Emergency travel document (if passport lost)
//    - Hospital visitation and coordination
//    - Legal assistance referral
//    - Repatriation coordination (in case of death)
//    - Liaison with local authorities
//    - Communication with family in India
// 5. Agency documents all coordination steps

interface FamilyNotificationSystem {
  notificationId: string;
  travelerId: string;
  tripId: string;
  familyContacts: FamilyContact[];
  notificationRules: FamilyNotificationRule[];
  notificationLog: FamilyNotificationRecord[];
}

interface FamilyContact {
  name: string;
  relationship: string;
  phone: string;
  email: string;
  notifyOn: FamilyNotificationEvent[];
}

type FamilyNotificationEvent =
  | 'trip_start'              // "Your family member has started their trip"
  | 'check_in_missed'         // "Traveler missed a check-in"
  | 'sos_activated'           // "Emergency SOS activated"
  | 'location_change'         // "Arrived at new city" (if opted in)
  | 'incident_reported'       // "Incident reported during trip"
  | 'trip_end';               // "Trip completed, traveler is safe"

interface FamilyNotificationRule {
  event: FamilyNotificationEvent;
  channel: 'sms' | 'whatsapp' | 'email' | 'push';
  delay: number;                       // Minutes before sending (for non-critical)
  requiresConsent: boolean;
}
```

---

## Open Problems

1. **Privacy vs. Safety trade-off** — Comprehensive tracking keeps travelers safer but collects sensitive location data. The India DPDP Act 2023 requires explicit consent and purpose limitation. How do we design the consent flow so travelers understand and willingly opt in?

2. **Offline SOS delivery** — Travelers in remote areas may have no connectivity when they need SOS. Can we use SMS-based SOS as fallback? Satellite messaging? What are the reliability and cost implications?

3. **False alarm fatigue** — If every missed check-in triggers agent notification, agents will get desensitized. How do we build smart escalation that distinguishes "forgot to check in" from "genuinely in trouble"?

4. **Cross-border emergency coordination** — When an Indian citizen has an emergency in a third country, coordination involves the Indian embassy, local emergency services, the agency, and the family. The communication chain is complex and slow. How do we streamline this?

5. **Traveler risk profiling ethics** — Profiling based on age, health, and demographics can feel discriminatory. Where is the line between helpful risk assessment and unfair profiling? How do we comply with equality laws?

6. **Family notification sensitivity** — Notifying family of a missed check-in or SOS can cause severe anxiety, especially if it is a false alarm. What is the right delay and escalation threshold before notifying family?

7. **Consular access limitations** — Indian embassies have limited staff and resources. In major crises (natural disasters, mass evacuations), they cannot assist every individual. How do we set realistic expectations?

8. **Battery drain** — Continuous GPS tracking drains mobile batteries. Travelers in remote areas may not have charging access. How do we optimize tracking to minimize battery impact while maintaining safety coverage?

---

## Next Steps

- [ ] Design traveler tracking consent flow compliant with India DPDP Act 2023
- [ ] Build Indian mission database (embassy/consulate contacts for top 50 destinations)
- [ ] Prototype SOS activation flow (mobile UI + backend response pipeline)
- [ ] Design risk-based check-in schedule rules (Risk Level 1-5 → check-in frequency)
- [ ] Research MADAD portal integration (pre-fill grievance forms)
- [ ] Evaluate offline SOS options (SMS fallback, satellite messaging providers)
- [ ] Design smart escalation algorithm for missed check-ins (reduce false alarms)
- [ ] Prototype family notification system with configurable rules
- [ ] Research battery-optimized location tracking strategies
- [ ] Draft traveler risk profiling guidelines with legal review for discrimination compliance
- [ ] Map MEA helpline workflow and document integration points
