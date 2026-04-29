# Travel Risk Assessment 03: Supplier Safety

> Research document for supplier safety auditing, incident tracking, safety ratings, and India-specific compliance standards (FSSAI, AICTE, state tourism certifications) for hotels, transport operators, activity providers, and guides.

---

## Document Overview

**Focus:** Supplier safety audit systems and compliance standards
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Safety Audit Framework
- What safety criteria should we audit for different supplier types (hotels, transport, activities, guides)?
- How do we verify compliance without physical inspection at every supplier?
- What is the cadence for re-auditing? Annual? Event-triggered?
- How do we handle suppliers that fail safety audits?

### 2. Hotel Safety
- What fire safety standards are relevant in India and abroad? (NBC India, local fire codes)
- How do we verify fire safety compliance? (Fire NOC, fire drill records, equipment certification)
- What food safety standards apply? (FSSAI in India, HACCP internationally)
- What building safety standards exist? (Structural safety, earthquake resistance, flood risk)

### 3. Transport Safety
- How do we verify transport operator licensing? (State transport authority, RTO, international equivalents)
- What vehicle safety standards apply? (Fitness certificates, insurance, driver verification)
- How do we assess driver qualifications and training? (License verification, background checks)
- What about aviation safety? (DGCA in India, IATA certification, airline safety records)

### 4. Activity Provider Safety
- What certifications matter for adventure activity providers? (AICTE, UIAA, PADI, etc.)
- How do we verify guide qualifications? (MoTourism certified, first aid, language proficiency)
- What safety equipment requirements exist for different activities?
- How do we assess insurance coverage adequacy for activity providers?

### 5. India-Specific Standards
- What are the FSSAI requirements for hotels and restaurants serving travelers?
- What does AICTE (Adventure Tour Operators Association of India) certify?
- What state tourism department certifications exist and are they meaningful?
- How do we verify "Incredible India" approved operator status?

### 6. Safety Rating System
- How do we present supplier safety ratings to agents?
- What is the rating scale and what does each level mean?
- How do ratings factor into supplier recommendations and search results?
- How do we handle rating disputes from suppliers?

---

## Research Areas

### A. Supplier Safety Audit Data Model

```typescript
interface SupplierSafetyAudit {
  auditId: string;
  supplierId: string;
  supplierType: SupplierType;
  auditDate: Date;
  auditor: AuditorInfo;
  auditType: AuditType;
  status: AuditStatus;
  results: AuditSection[];
  overallScore: SafetyScore;
  certification: SafetyCertification[];
  findings: AuditFinding[];
  nextAuditDue: Date;
}

type SupplierType =
  | 'hotel'
  | 'resort'
  | 'homestay'
  | 'transport_operator'      // Bus, taxi, coach companies
  | 'airline'
  | 'activity_provider'       // Adventure, water sports, trekking
  | 'guide'                   // Individual tour guides
  | 'restaurant'              // Standalone restaurants on tours
  | 'event_venue'             // MICE venues
  | 'cruise_line';

type AuditType =
  | 'initial'                 // First audit before onboarding
  | 'routine'                 // Scheduled periodic audit
  | 'event_triggered'         // Triggered by incident or complaint
  | 'random'                  // Surprise audit
  | 'self_declaration'        // Supplier self-assessment (lower weight)
  | 'renewal';                // Certification renewal audit

type AuditStatus =
  | 'scheduled'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'remediation_required'
  | 'suspended';

interface SafetyScore {
  overall: number;                     // 0-100
  categories: Record<SafetyCategory, number>;
  grade: SafetyGrade;
  validUntil: Date;
}

type SafetyGrade = 'A+' | 'A' | 'B+' | 'B' | 'C' | 'D' | 'F';
// A+ (90-100): Exceptional safety standards, exceeds requirements
// A  (80-89):  Meets all requirements, strong safety culture
// B+ (70-79):  Meets most requirements, minor gaps
// B  (60-69):  Meets basic requirements, some improvement areas
// C  (50-59):  Below standard, remediation required within 90 days
// D  (40-49):  Significant safety concerns, restricted use
// F  (<40):    Fails safety standards, do not use

type SafetyCategory =
  | 'fire_safety'
  | 'food_safety'
  | 'structural_safety'
  | 'transport_safety'
  | 'equipment_safety'
  | 'staff_qualifications'
  | 'emergency_preparedness'
  | 'insurance_coverage'
  | 'regulatory_compliance'
  | 'environmental_safety';

interface AuditFinding {
  findingId: string;
  category: SafetyCategory;
  severity: 'critical' | 'major' | 'minor' | 'observation';
  description: string;
  recommendation: string;
  remediationDeadline: Date;
  status: 'open' | 'in_progress' | 'resolved' | 'overdue';
  evidence?: string;                   // Photo, document reference
}
```

### B. Hotel Safety Audit Checklist

```typescript
interface HotelSafetyAuditChecklist {
  fireSafety: FireSafetyChecklist;
  foodSafety: FoodSafetyChecklist;
  structuralSafety: StructuralSafetyChecklist;
  guestSafety: GuestSafetyChecklist;
  emergencyPreparedness: EmergencyPreparednessChecklist;
  staffTraining: StaffTrainingChecklist;
}

interface FireSafetyChecklist {
  // Certification
  fireNocObtained: boolean;            // Fire No Objection Certificate
  fireNocDate: Date;
  fireNocIssuingAuthority: string;     // Local fire department
  fireNocExpiry: Date;

  // Equipment
  smokeDetectorsInstalled: boolean;
  smokeDetectorCoverage: 'common_areas' | 'all_rooms' | 'full_building';
  fireExtinguishersPresent: boolean;
  fireExtinguisherCount: number;       // Per floor
  fireExtinguisherLastChecked: Date;
  sprinklerSystem: boolean;
  fireAlarmSystem: boolean;
  fireAlarmConnectedToFireDept: boolean; // Monitored alarm

  // Escape routes
  emergencyExitSigns: boolean;
  emergencyExitSignsIlluminated: boolean; // Battery-backed illumination
  emergencyExitRouteMapInRooms: boolean;
  emergencyExitsUnobstructed: boolean;
  numberOfEmergencyExits: number;

  // Training
  staffFireDrillFrequency: 'monthly' | 'quarterly' | 'biannual' | 'annual' | 'none';
  lastFireDrillDate: Date;
  staffFireSafetyTraining: boolean;

  // Additional
  kitchenFireSuppressionSystem: boolean;
  laundryFireSafetyMeasures: boolean;
  basementParkingVentilation: boolean;
}

interface FoodSafetyChecklist {
  // India-specific: FSSAI
  fssaiLicenseActive: boolean;
  fssaiLicenseNumber: string;
  fssaiLicenseExpiry: Date;
  fssaiRating: number;                 // FSSAI hygiene rating (if available)

  // International: HACCP
  haccpCertified: boolean;
  haccpCertificationBody: string;

  // General
  kitchenInspectionPassed: boolean;
  kitchenInspectionDate: Date;
  foodHandlingTraining: boolean;
  foodStorageCompliance: boolean;
  waterQualityTested: boolean;
  waterQualityReportDate: Date;

  // FSSAI specifics:
  // - FSSAI license is mandatory for all food businesses in India
  // - Categories: Registration (turnover < 12L), State License (< 20Cr), Central License (> 20Cr)
  //   Hotels with > 5-star rating need Central License
  // - Hygiene rating: 1-5 scale displayed at establishment
  // - FoSCoS portal: foscos.fssai.gov.in for license verification
  // - Annual return filing required
}

interface GuestSafetyChecklist {
  cctvInCommonAreas: boolean;
  cctvCoveragePercent: number;
  securityGuardsRoundTheClock: boolean;
  electronicRoomLocks: boolean;
  safeInRoom: boolean;
  peepholeOnRoomDoor: boolean;
  wellLitCorridors: boolean;
  wellLitParkingArea: boolean;
  firstAidKitAvailable: boolean;
  aedAvailable: boolean;               // Automated External Defibrillator
  wheelchairAccessible: boolean;
  swimmingPoolLifeguard: boolean;      // If pool exists
  childSafetyMeasures: boolean;        // Pool fence, window guards, etc.
}
```

### C. Transport Operator Safety Audit

```typescript
interface TransportSafetyAudit {
  operatorId: string;
  operatorType: TransportOperatorType;
  licensing: TransportLicensing;
  vehicles: VehicleSafety[];
  drivers: DriverSafety[];
  safetyRecord: TransportSafetyRecord;
}

type TransportOperatorType =
  | 'bus_operator'            // AC/Non-AC buses, Volvo, etc.
  | 'taxi_operator'           // Radio taxi, app-based
  | 'coach_operator'          // Tourist coaches
  | 'tempo_traveller'         // Force Tempo Traveller (common in India)
  | 'car_rental'              // Self-drive and chauffeured
  | 'auto_rickshaw'           // Auto-rickshaws (tourist areas)
  | 'boat_operator'           // Ferries, tourist boats
  | 'airline'                 // Domestic/international airlines
  | 'rail_operator';          // Tourist trains, charter trains

interface TransportLicensing {
  // India-specific
  rtoRegistrationNumber: string;       // Regional Transport Office
  tradeLicenseActive: boolean;
  stateTransportPermit: string;        // State permit for inter-state
  nationalPermit: boolean;             // All-India permit
  insuranceValid: boolean;
  insuranceExpiry: Date;
  insuranceType: 'third_party' | 'comprehensive' | 'fleet';

  // Tourist vehicle specific
  touristVehiclePermit: boolean;       // Under Motor Vehicles Act
  permitNumber: string;
  permitExpiry: Date;

  // Fitness
  vehicleFitnessCertificate: boolean;
  fitnessExpiry: Date;
  pollutionCertificate: boolean;       // PUC - Pollution Under Control
  pollutionExpiry: Date;

  // For airlines
  dgcaApproval?: boolean;              // Directorate General of Civil Aviation
  iataCode?: string;
  iosRegistry?: string;                // IATA Operational Safety Audit
}

interface VehicleSafety {
  vehicleId: string;
  registrationNumber: string;
  type: string;                        // "Volvo B11R", "Toyota Innova", etc.
  yearOfManufacture: number;
  seatingCapacity: number;
  lastServiceDate: Date;
  nextServiceDue: Date;

  safetyEquipment: {
    seatBelts: 'all_seats' | 'front_only' | 'none';
    fireExtinguisher: boolean;
    firstAidKit: boolean;
    emergencyExit: boolean;
    gpsTracking: boolean;
    speedGovernor: boolean;            // Mandatory for commercial vehicles in India
    cctvCamera: boolean;
    reflectiveTape: boolean;           // Mandatory on commercial vehicles
  };

  // Verification
  rcBookValid: boolean;                // Registration Certificate
  roadTaxPaid: boolean;
  insuranceValid: boolean;
  fitnessCertificateValid: boolean;
}

interface DriverSafety {
  driverId: string;
  licenseNumber: string;
  licenseType: string;                 // "LMV", "HPMV", "Heavy Motor Vehicle"
  licenseValidUntil: Date;
  licenseIssuingRTO: string;
  backgroundCheckDone: boolean;
  backgroundCheckDate: Date;
  policeVerification: boolean;         // Mandatory for tourist vehicle drivers
  yearsOfExperience: number;
  defensiveDrivingTraining: boolean;
  firstAidTraining: boolean;
  medicalFitnessCertificate: boolean;
  medicalFitnessExpiry: Date;
  accidentRecord: AccidentRecord[];
}
```

### D. Activity Provider & Guide Safety

```typescript
interface ActivityProviderAudit {
  providerId: string;
  activityTypes: ActivityType[];
  certifications: ActivityCertification[];
  equipment: EquipmentAudit[];
  guides: GuideQualification[];
  insurance: ProviderInsurance;
  safetyRecord: ActivitySafetyRecord;
}

type ActivityType =
  | 'trekking'
  | 'mountaineering'
  | 'river_rafting'
  | 'scuba_diving'
  | 'snorkeling'
  | 'paragliding'
  | 'bungee_jumping'
  | 'zip_line'
  | 'safari'
  | 'skiing'
  | 'water_skiing'
  | 'kayaking'
  | 'rock_climbing'
  | 'camping'
  | 'hot_air_balloon'
  | 'atv_riding'
  | 'horse_riding'
  | 'cycling_tour'
  | 'food_walk'
  | 'heritage_walk';

interface ActivityCertification {
  name: string;
  issuingBody: string;
  certificateNumber: string;
  validFrom: Date;
  validUntil: Date;
  verified: boolean;
}

// India-specific adventure certifications:
//
// AICTE (Adventure Tour Operators Association of India):
//   - Not to be confused with All India Council for Technical Education
//   - AICTE sets safety standards for adventure tourism in India
//   - Certification covers: Equipment standards, guide qualifications, safety protocols
//   - Recognized by Ministry of Tourism, Government of India
//
// Indian Mountaineering Foundation (IMF):
//   - For mountaineering expeditions above 6000m
//   - Mandatory for peaks in Indian Himalayas
//   - Issues climbing permits
//
// Ministry of Tourism, Government of India:
//   - "Incredible India" approved tour operator status
//   - Adventure tourism guidelines issued in 2018 (revised periodically)
//   - Classification: Approved / Provisional / Suspended
//
// State-level certifications:
//   - Himachal Pradesh: HP Tourism Development Corp approval for adventure ops
//   - Uttarakhand: Adventure tourism registration mandatory
//   - Goa: Water sports operators need Goa Tourism registration
//   - Kerala: Adventure tourism guidelines by Kerala Tourism
//   - Rajasthan: Desert safari operators registered with Rajasthan Tourism
//
// International certifications (for outbound):
//   - PADI: Professional Association of Diving Instructors (diving)
//   - UIAA: International Climbing and Mountaineering Federation
//   - IRF: International Rafting Federation
//   - PAI: Paragliding international certifications

interface GuideQualification {
  guideId: string;
  name: string;
  licenseNumber?: string;
  licenseIssuingAuthority: string;
  specializations: string[];
  languages: string[];
  firstAidCertified: boolean;
  firstAidExpiry: Date;
  cprCertified: boolean;
  wildernessFirstResponder: boolean;
  yearsOfExperience: number;
  clientRatings: number;               // Average rating
  incidentsReported: number;
  training: GuideTraining[];
}

interface GuideTraining {
  course: string;                      // "MoTourism Guide Training"
  provider: string;
  completionDate: Date;
  certificateId: string;
}

// India: Ministry of Tourism Regional Guide Program:
// - "Licensed Tourist Guide" - trained and certified by MoTourism
// - Regional guides: Certified for specific regions/states
// - State-level guide licenses (e.g., Kerala Tourism, Rajasthan Tourism)
// - Foreign language guides: Specialized training in French, German, Japanese, etc.
// - Verification: Ministry of Tourism website or state tourism portal
```

### E. Safety Rating Display for Agents

```typescript
interface SupplierSafetyRating {
  supplierId: string;
  supplierName: string;
  supplierType: SupplierType;
  overallGrade: SafetyGrade;
  overallScore: number;
  lastAuditDate: Date;
  nextAuditDate: Date;
  flags: SafetyFlag[];
  certifications: string[];
}

type SafetyFlag =
  | 'certified'               // All audits passed
  | 'pending_audit'           // Awaiting initial or renewal audit
  | 'minor_findings'          // Minor issues found, still approved
  | 'remediation_required'    // Issues found, remediation in progress
  | 'restricted_use'          // Can only be used with disclosure to customer
  | 'suspended'               // Do not use until re-audited
  | 'blacklisted';            // Permanently removed from platform

// Safety rating display in agent workspace:
//
// ┌──────────────────────────────────────────────────────────────────────┐
// │  SUPPLIER SEARCH RESULTS                              [Filter: ▼]  │
// │                                                                      │
// │  Safety Filter:  [All] [A+/A] [B+/B] [C] [D/F] [Not Audited]       │
// │                                                                      │
// │  ┌────────────────────────────────────────────────────────────────┐  │
// │  │ ★ Taj Palace Hotel, New Delhi                    Safety: A+   │  │
// │  │   🔥 Fire: A+ | 🍽 Food: A | 🏗 Structure: A+ | ⚕ Staff: A  │  │
// │  │   Certified: FSSAI ✓ Fire NOC ✓ NBC ✓ Last Audit: Mar 2026   │  │
// │  │   [View Details] [Safety Certificate]                          │  │
// │  └────────────────────────────────────────────────────────────────┘  │
// │                                                                      │
// │  ┌────────────────────────────────────────────────────────────────┐  │
// │  │ Heritage Inn, Jaipur                             Safety: B    │  │
// │  │   🔥 Fire: B | 🍽 Food: B+ | 🏗 Structure: B | ⚕ Staff: B   │  │
// │  │   Certified: FSSAI ✓ Fire NOC ✓ Last Audit: Jan 2026         │  │
// │  │   ⚠ 2 minor findings open (fire exit signage)                 │  │
// │  │   [View Details] [Safety Certificate]                          │  │
// │  └────────────────────────────────────────────────────────────────┘  │
│ │                                                                      │
│ │  ┌────────────────────────────────────────────────────────────────┐  │
│ │  │ Mountain Adventures, Rishikesh                  Safety: C ⚠   │  │
│ │  │   Equipment: C | Guides: B+ | Insurance: D                    │  │
│ │  │   Certified: AICTE ✓ Insurance: ⚠ Expired                    │  │
│ │  │   ⚠ Remediation required by May 15, 2026                     │  │
│ │  │   [View Details] [Remediation Plan]                           │  │
│ │  └────────────────────────────────────────────────────────────────┘  │
│ │                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### F. Safety Incident Tracking

```typescript
interface SupplierSafetyIncident {
  incidentId: string;
  supplierId: string;
  supplierType: SupplierType;
  reportedDate: Date;
  incidentDate: Date;
  type: SafetyIncidentType;
  severity: IncidentSeverity;
  description: string;
  affectedTravelers: number;
  injuries: number;
  fatalities: number;
  rootCause: string;
  correctiveAction: string;
  status: 'open' | 'investigating' | 'resolved' | 'litigation';
  regulatoryNotification: boolean;     // Was authority notified?
  insuranceClaim: boolean;
  impactOnRating: SafetyGrade;         // What was the rating impact?
}

type SafetyIncidentType =
  | 'fire'                    // Fire incident at premises
  | 'food_poisoning'          // Mass food poisoning
  | 'structural_failure'      // Building collapse, balcony failure
  | 'transport_accident'      // Vehicle accident
  | 'drowning'                // Swimming pool, water activity
  | 'equipment_failure'       // Adventure equipment malfunction
  | 'guide_negligence'        // Guide error leading to injury
  | 'security_breach'         // Theft, assault on premises
  | 'natural_disaster_impact' // Supplier affected by disaster
  | 'health_violation'        // Failed health inspection
  | 'safety_violation';       // General safety standard violation

type IncidentSeverity =
  | 'minor'                   // No injuries, near-miss
  | 'moderate'                // Minor injuries, resolved on-site
  | 'serious'                 // Hospitalization required
  | 'severe'                  // Multiple hospitalizations
  | 'critical'                // Fatality or life-threatening
  | 'catastrophic';           // Multiple fatalities

// Incident → Rating impact rules:
// minor:    No rating change, documented
// moderate: -5 to -10 points, review within 30 days
// serious:  -15 to -25 points, mandatory re-audit
// severe:   -25 to -40 points, suspend pending investigation
// critical: Grade drops to D or F, immediate suspension
// catastrophic: Immediate blacklist, regulatory notification
```

### G. Supplier Safety Compliance Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  SUPPLIER SAFETY COMPLIANCE DASHBOARD                         [Last 30 Days]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  OVERVIEW                                                                       │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Total Suppliers: 1,247    Audited: 892 (71%)    Pending: 355 (29%)      │  │
│  │                                                                          │  │
│  │  Grade Distribution:                                                     │  │
│  │  A+ ████████████████ 312 (35%)                                           │  │
│  │  A  ██████████████ 278 (31%)                                             │  │
│  │  B+ ████████ 145 (16%)                                                  │  │
│  │  B  ██████ 98 (11%)                                                     │  │
│  │  C  ██ 41 (5%)                                                           │  │
│  │  D  █ 12 (1%)                                                            │  │
│  │  F  █ 6 (1%)                                                             │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  ALERTS                                                                         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  ⚠ 6 suppliers with expiring certifications (within 30 days)            │  │
│  │  ⚠ 3 suppliers with unresolved remediation items                         │  │
│  │  ⚠ 12 suppliers pending initial audit (> 90 days since onboarding)      │  │
│  │  🔴 2 suppliers suspended due to incidents                               │  │
│  │  🟡 1 supplier insurance expired                                         │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  UPCOMING AUDITS                                                                │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │  Due This Week:                                                          │  │
│  │  • Taj Palace, Delhi — Renewal audit (Grade: A+)                         │  │
│  │  • Himalayan Adventures, Manali — Event-triggered (incident reported)    │  │
│  │  • Goan Watersports, Goa — Routine annual                                │  │
│  │                                                                          │  │
│  │  Due This Month: 23 audits scheduled                                     │  │
│  │  Overdue: 4 audits (escalated to operations team)                        │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  [Export Report]  [Schedule Audits]  [View Incident Log]  [Compliance Matrix]  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Audit verification at scale** — Physical audits are expensive and time-consuming. Can we rely on document-based verification (fire NOC, FSSAI license) without physical inspection? What is the right balance?

2. **Informal supplier compliance** — Many Indian suppliers (homestays, local guides, auto-rickshaws) operate informally without certifications. How do we assess safety for unregulated suppliers that are commonly booked?

3. **Certification reliability** — Some certifications in India are obtained through bureaucratic process rather than genuine safety compliance. Fire NOCs can be obtained with token compliance. How do we assess the quality behind the certificate?

4. **Cross-border standard differences** — A hotel in India (FSSAI, NBC) has very different certification requirements than one in Thailand (Thai FDA, local fire code). How do we normalize ratings across countries?

5. **Activity provider regulation gaps** — Adventure tourism in India is regulated at the state level with inconsistent enforcement. Some states (Himachal, Uttarakhand) have strong regulations; others have none. How do we handle unregulated markets?

6. **Supplier resistance** — Suppliers may resist safety audits as intrusive or costly, especially small operators. How do we make safety audits a value proposition rather than a burden?

7. **Insurance adequacy assessment** — Many Indian transport operators carry only mandatory third-party insurance, which is grossly inadequate for tourist accidents. How do we assess and enforce adequate insurance coverage?

8. **Real-time safety monitoring** — Audits are point-in-time assessments. A supplier can pass an audit and have a safety incident the next day. How do we build continuous safety monitoring rather than periodic audits?

---

## Next Steps

- [ ] Map India-specific safety certifications and verification methods (FSSAI, Fire NOC, RTO, DGCA)
- [ ] Design safety audit checklist templates for each supplier type
- [ ] Build database schema for safety incident tracking
- [ ] Research state-level adventure tourism regulations across Indian states
- [ ] Prototype supplier safety rating display in agent workspace
- [ ] Design remediation workflow for suppliers that fail audits
- [ ] Research FoSCoS (FSSAI) API for license verification
- [ ] Build compliance dashboard wireframes
- [ ] Study AICTE (Adventure Tour Operators) certification process
- [ ] Evaluate third-party safety audit providers and partnerships
- [ ] Design insurance adequacy scoring for transport operators
- [ ] Research cross-border certification equivalence (e.g., India fire code vs. international)
