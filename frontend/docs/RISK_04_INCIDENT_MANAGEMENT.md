# Travel Risk Assessment 04: Incident Management

> Research document for incident classification, response playbooks, crisis communication workflows, post-incident analysis, insurance claim triggering, and India-specific coordination with NDRF, MEA helpline, and state emergency services.

---

## Document Overview

**Focus:** End-to-end incident management system for travel emergencies
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### 1. Incident Classification
- How do we classify incidents by type, severity, and scope?
- What is the taxonomy for travel incidents? (Medical, security, natural disaster, political, transport)
- How do we handle incidents that span multiple categories? (Earthquake causing transport disruption and medical emergencies)
- How do we determine incident severity in real-time with incomplete information?

### 2. Response Playbook
- What are the automated vs. manual response actions for each incident type?
- How do response playbooks differ by destination risk level?
- What are the response time SLAs for different severity levels?
- How do we coordinate response when the agent is offline (nighttime, weekends)?

### 3. Crisis Communication
- What is the communication chain: agent → customer → family → insurer?
- How do we ensure communication is timely, accurate, and coordinated?
- What communication templates exist for different incident types?
- How do we handle communication when the traveler is unreachable?

### 4. Post-Incident Analysis
- What data do we capture during and after incidents?
- How do we conduct post-incident reviews (PIR)?
- How do incident learnings feed back into risk scoring and safety systems?
- What reporting is required for regulatory and insurance purposes?

### 5. Insurance Integration
- How do incidents automatically trigger insurance claims?
- What data does the insurer need immediately vs. during claim processing?
- How do we coordinate between the traveler, agency, and insurer?
- What are the common reasons for claim rejection and how do we prevent them?

### 6. India-Specific Coordination
- How do we integrate with NDRF (National Disaster Response Force) for domestic incidents?
- What is the MEA helpline workflow for international incidents involving Indian citizens?
- How do we coordinate with state emergency services (108, 112)?
- What are the protocols for repatriation of Indian citizens who are injured or deceased abroad?

---

## Research Areas

### A. Incident Classification System

```typescript
interface TravelIncident {
  incidentId: string;
  tripId: string;
  travelerId: string;
  reportedAt: Date;
  incidentAt: Date;
  reportedBy: 'traveler' | 'agent' | 'system' | 'third_party' | 'family';
  classification: IncidentClassification;
  severity: IncidentSeverity;
  status: IncidentStatus;
  location: IncidentLocation;
  affectedTravelers: AffectedTraveler[];
  response: IncidentResponse;
  communication: CommunicationLog[];
  timeline: IncidentTimelineEvent[];
  resolution?: IncidentResolution;
}

interface IncidentClassification {
  primaryType: IncidentType;
  secondaryTypes: IncidentType[];       // Incidents often span categories
  scope: IncidentScope;
  tags: string[];
}

type IncidentType =
  // Medical
  | 'medical_illness'          // Traveler falls ill (food poisoning, fever, etc.)
  | 'medical_injury'           // Accident, sports injury, fall
  | 'medical_hospitalization'  // Hospitalization required
  | 'medical_evacuation'       // Medical evacuation/air ambulance needed
  | 'medical_death'            // Traveler death

  // Security
  | 'security_theft'           // Pickpocket, bag snatching, hotel theft
  | 'security_robbery'         // Armed robbery, mugging
  | 'security_assault'         // Physical assault
  | 'security_terrorism'       // Terrorist incident
  | 'security_kidnapping'      // Hostage situation, kidnapping
  | 'security_civil_unrest'    // Caught in protest, riot, civil disturbance
  | 'security_arrest'          // Traveler detained/arrested by local authorities

  // Natural Disaster
  | 'disaster_earthquake'      // Earthquake
  | 'disaster_flood'           // Flooding
  | 'disaster_cyclone'         // Cyclone/hurricane/typhoon
  | 'disaster_tsunami'         // Tsunami
  | 'disaster_volcanic'        // Volcanic eruption
  | 'disaster_landslide'       // Landslide
  | 'disaster_wildfire'        // Wildfire
  | 'disaster_heatwave'        // Extreme heat
  | 'disaster_coldwave'        // Extreme cold

  // Political
  | 'political_unrest'         // Political instability, coup, protest
  | 'political_war'            // Armed conflict breaks out
  | 'political_embassy_alert'  // Embassy issues emergency advisory
  | 'political_border_closure' // Border closed, stranded traveler

  // Transport
  | 'transport_accident'       // Vehicle accident (bus, taxi, train)
  | 'transport_aviation'       // Aviation incident (crash, emergency landing)
  | 'transport_maritime'       // Maritime incident (ferry, cruise)
  | 'transport_delay'          // Major transport delay (>12 hours)
  | 'transport_cancellation'   // Mass cancellation (strike, weather)

  // Documentation
  | 'document_passport_lost'   // Passport lost or stolen
  | 'document_visa_issue'      // Visa problem at border
  | 'document_ticket_issue';   // Ticket/booking not honored

type IncidentSeverity =
  | 'level_1_informational'    // Minor inconvenience, self-resolvable
  | 'level_2_minor'            // Needs agent assistance, no safety risk
  | 'level_3_moderate'         // Needs urgent attention, potential safety risk
  | 'level_4_serious'          // Safety at risk, immediate action needed
  | 'level_5_critical'         // Life-threatening, emergency response
  | 'level_6_mass_event';      // Major event affecting many travelers

type IncidentScope =
  | 'single_traveler'          // One traveler affected
  | 'travel_group'             // Travel group/family affected
  | 'multiple_groups'          // Multiple agency groups affected
  | 'regional'                 // Travelers in a region affected
  | 'destination_wide'         // All travelers at destination affected
  | 'global';                  // Pandemic, global event

type IncidentStatus =
  | 'reported'
  | 'triaged'
  | 'response_active'
  | 'assistance_en_route'
  | 'traveler_safe'
  | 'resolved'
  | 'closed'
  | 'escalated_external'       // Handed to external agencies
  | 'monitoring';              // Watching, no action needed yet
```

### B. Incident Response Playbook

```typescript
interface IncidentResponsePlaybook {
  playbookId: string;
  incidentType: IncidentType;
  severity: IncidentSeverity;
  automatedActions: AutomatedResponse[];
  manualActions: ManualResponse[];
  escalationPath: EscalationStep[];
  communicationPlan: CommunicationPlan;
  timeTargets: ResponseTimeTarget;
  resources: ResponseResource[];
}

interface AutomatedResponse {
  action: string;
  trigger: string;                     // Condition that triggers this action
  delay: number;                       // Seconds after trigger
  channel: string;                     // "push", "sms", "email", "webhook"
  recipient: string;                   // "assigned_agent", "traveler", "emergency_team"
  template: string;                    // Message template ID
}

// Example: Automated response for medical_emergency (level 4-5)
//
// Trigger: SOS activated or agent reports medical emergency
// +0s:   Push notification to assigned agent (with traveler location)
// +0s:   SMS to agent (backup notification)
// +30s:  Load local emergency numbers for traveler's location
// +30s:  Load Indian embassy/consulate contact if international
// +60s:  Prepare insurance claim pre-notification
// +60s:  Alert agency emergency team if agent hasn't acknowledged
// +300s: Escalate to agency owner if no acknowledgment
// +300s: Notify family emergency contact (for level 5)
// +600s: Contact local emergency services if level 5 and no resolution

interface ManualResponse {
  step: number;
  action: string;
  assignee: string;                    // Role: "agent", "emergency_team", "agency_owner"
  description: string;
  checklist: string[];
  timeTarget: number;                  // Minutes to complete this step
}

// Example: Manual response checklist for medical_emergency
//
// Step 1: Contact Traveler (Agent, 5 min target)
//   [ ] Call traveler on registered mobile
//   [ ] If no answer, call hotel reception
//   [ ] Determine: consciousness, injury type, current location
//   [ ] If unconscious/unreachable: proceed to Step 2 immediately
//
// Step 2: Assess and Coordinate (Agent, 10 min target)
//   [ ] Determine severity and type of medical issue
//   [ ] Provide local emergency number (ambulance)
//   [ ] Check if traveler has travel insurance
//   [ ] If international: note Indian embassy/consulate number
//   [ ] Ask traveler to share live location if mobile
//
// Step 3: Activate Support (Emergency Team, 15 min target)
//   [ ] Notify insurance provider (pre-authorization for hospital)
//   [ ] Arrange hospital/clinic if traveler cannot self-arrange
//   [ ] For India: Contact 108 for ambulance, identify nearest hospital
//   [ ] For international: Contact International SOS or equivalent
//   [ ] Arrange translation service if language barrier
//
// Step 4: Family Notification (Agent, 30 min target)
//   [ ] Contact family emergency contact
//   [ ] Provide factual update (no speculation)
//   [ ] Share agency emergency contact for updates
//   [ ] If repatriation needed: discuss logistics and costs
//
// Step 5: Documentation (Agent, ongoing)
//   [ ] Log all communication with timestamps
//   [ ] Collect medical reports and bills
//   [ ] Photograph injuries/scene if possible
//   [ ] Police report if accident/assault (FIR in India)
//   [ ] Insurance claim form initiated

interface EscalationStep {
  level: number;
  triggerCondition: string;
  triggerAfterMinutes: number;
  notifyRoles: string[];
  actions: string[];
}

// Escalation matrix:
// Level 1: Assigned agent handles
// Level 2: Agency emergency team + operations manager (if agent needs support)
// Level 3: Agency owner + external emergency services (for critical incidents)
// Level 4: Crisis management team + regulatory authorities (for mass events)

interface ResponseTimeTarget {
  acknowledgment: number;              // Seconds until someone acknowledges
  firstContact: number;                // Minutes until traveler is contacted
  assistanceArranged: number;          // Minutes until help is arranged
  familyNotified: number;              // Minutes until family is notified
  insuranceNotified: number;           // Minutes until insurer is notified
  resolution: number;                  // Hours until incident is resolved
}

// Response time targets by severity:
// Level 1 (Informational):   Acknowledge: 1hr, Resolve: 24hr
// Level 2 (Minor):           Acknowledge: 30min, Resolve: 12hr
// Level 3 (Moderate):        Acknowledge: 15min, Resolve: 6hr
// Level 4 (Serious):         Acknowledge: 5min, Resolve: 4hr
// Level 5 (Critical):        Acknowledge: 2min, Resolve: 2hr
// Level 6 (Mass Event):      Acknowledge: immediate, Resolve: ongoing
```

### C. Crisis Communication Workflow

```typescript
interface CrisisCommunicationPlan {
  planId: string;
  incidentId: string;
  stakeholders: CommunicationStakeholder[];
  channels: CommunicationChannel[];
  templates: CommunicationTemplate[];
  log: CommunicationRecord[];
}

interface CommunicationStakeholder {
  role: StakeholderRole;
  name: string;
  contactInfo: ContactInfo;
  notifyAt: StakeholderNotificationLevel;
  communicationFrequency: string;      // "every_30_min", "hourly", "daily_update"
}

type StakeholderRole =
  | 'traveler'
  | 'assigned_agent'
  | 'agency_emergency_team'
  | 'agency_owner'
  | 'family_contact'
  | 'insurance_provider'
  | 'indian_embassy'
  | 'local_authorities'
  | 'supplier'
  | 'media_spokesperson';

type StakeholderNotificationLevel =
  | 'immediate'               // Notify right away for any incident
  | 'level_3_plus'            // Notify for moderate and above
  | 'level_4_plus'            // Notify for serious and above
  | 'level_5_only';           // Notify for critical only

interface CommunicationTemplate {
  templateId: string;
  incidentType: IncidentType;
  stakeholderRole: StakeholderRole;
  channel: 'sms' | 'whatsapp' | 'email' | 'phone_call' | 'push';
  subject?: string;
  body: string;                        // Template with placeholders
  tone: 'reassuring' | 'informational' | 'urgent' | 'formal';
}

// Communication templates (examples):
//
// TEMPLATE: medical_emergency → family_contact → phone_call
// Tone: Reassuring
// Script:
//   "Hello, this is [agent_name] from [agency_name]. I'm calling about
//    [traveler_name] who is currently on a trip to [destination].
//    I want to let you know that [traveler_name] has had a medical
//    situation. [He/She] is currently [status: conscious/receiving
//    treatment/at hospital]. We are coordinating with local medical
//    services and your travel insurance provider [insurer_name].
//    Our team is actively monitoring the situation. You can reach me
//    directly at [agent_phone] for updates. Please don't hesitate
//    to call."
//
// TEMPLATE: natural_disaster → traveler → sms
// Tone: Urgent
// Body:
//   "[AGENCY_NAME] ALERT: [disaster_type] reported in [location].
//    If you are in the affected area, move to higher ground / safe
//    location immediately. Call us at [emergency_number] or activate
//    SOS in the app. We are monitoring and will assist."
//
// TEMPLATE: incident_update → insurance_provider → email
// Tone: Formal
// Subject: "Incident Report — Policy [policy_number] — [incident_type]"
// Body:
//   "Dear Claims Team, This is to notify you of an incident involving
//    policyholder [traveler_name], Policy #[policy_number].
//    Incident Type: [incident_type]
//    Date/Time: [incident_date] at [incident_time] [timezone]
//    Location: [incident_location]
//    Severity: [severity_level]
//    Current Status: [status]
//    Hospital: [hospital_name] (if applicable)
//    Please confirm pre-authorization for medical expenses.
//    Agency Contact: [agent_name] at [agent_phone]"

// Communication chain visualization:
//
// ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
// │ Incident │────▶│  Agent   │────▶│ Customer │     │          │
// │ Detected │     │ Notified │     │ Contacted│     │          │
// └──────────┘     └────┬─────┘     └──────────┘     │          │
//                       │                             │          │
//                       ├─────────────┐               │          │
//                       │             │               │          │
//                       ▼             ▼               ▼          │
//                ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
//                │  Family  │  │ Insurer  │  │   Supplier   │   │
//                │ Notified │  │ Alerted  │  │  Contacted   │   │
//                └──────────┘  └──────────┘  └──────────────┘   │
//                                                                  │
//              For international incidents:                        │
//                ┌──────────┐  ┌──────────┐                       │
//                │  Indian  │  │  Local   │                       │
//                │ Embassy  │  │Authority │                       │
//                └──────────┘  └──────────┘
```

### D. Post-Incident Analysis

```typescript
interface PostIncidentReview {
  reviewId: string;
  incidentId: string;
  conductedDate: Date;
  conductedBy: string;
  participants: string[];
  timeline: IncidentTimelineEvent[];
  rootCause: RootCauseAnalysis;
  responseEvaluation: ResponseEvaluation;
  learnings: IncidentLearning[];
  actionItems: PostIncidentAction[];
  feedBackToRiskScore: boolean;
}

interface IncidentTimelineEvent {
  timestamp: Date;
  event: string;
  actor: string;
  category: 'detection' | 'notification' | 'response' | 'communication'
          | 'escalation' | 'resolution' | 'external';
  notes?: string;
}

interface RootCauseAnalysis {
  method: '5_whys' | 'fishbone' | 'timeline_analysis' | 'simple';
  rootCause: string;
  contributingFactors: string[];
  preventable: boolean;
  preventionMeasures: string[];
}

interface ResponseEvaluation {
  responseTimeMet: boolean;
  communicationTimely: boolean;
  stakeholderSatisfaction: Record<string, number>; // Role → 1-5 rating
  whatWentWell: string[];
  whatCouldImprove: string[];
  playbookFollowed: boolean;
  playbookGaps: string[];
}

interface IncidentLearning {
  category: 'process' | 'training' | 'technology' | 'supplier' | 'communication';
  learning: string;
  recommendation: string;
  priority: 'high' | 'medium' | 'low';
  assignedTo: string;
}

interface PostIncidentAction {
  actionId: string;
  type: 'system_update' | 'process_change' | 'training' | 'supplier_action'
       | 'risk_score_update' | 'playbook_update';
  description: string;
  assignedTo: string;
  dueDate: Date;
  status: 'pending' | 'in_progress' | 'completed';
}

// Post-incident review triggers:
// Level 1-2: Agent self-review, documented in trip notes
// Level 3: Agent + supervisor review within 7 days
// Level 4: Formal PIR with operations team within 3 days
// Level 5: Full crisis review with agency leadership within 24 hours
// Level 6: External review + regulatory reporting
```

### E. Insurance Claim Integration

```typescript
interface InsuranceClaimTrigger {
  claimId: string;
  incidentId: string;
  policyNumber: string;
  insurerId: string;
  triggeredAt: Date;
  triggeredBy: 'automatic' | 'agent';
  claimType: InsuranceClaimType;
  status: ClaimStatus;
  documents: ClaimDocument[];
  communication: ClaimCommunication[];
  settlement?: ClaimSettlement;
}

type InsuranceClaimType =
  | 'medical_expense'          // Hospital bills, doctor fees, medication
  | 'medical_evacuation'       // Air ambulance, medical transport
  | 'repatriation'             // Return of remains to home country
  | 'trip_cancellation'        // Trip cancelled due to covered reason
  | 'trip_interruption'        // Trip cut short due to covered reason
  | 'baggage_loss'             // Lost or stolen baggage
  | 'baggage_delay'            // Baggage delayed > 12 hours
  | 'flight_delay'             // Flight delay > 6 hours
  | 'personal_liability'       // Traveler caused injury/damage to third party
  | 'legal_expense'            // Legal costs abroad
  | 'hijack_distress'          // Distress allowance during hijacking
  | 'adventure_sports'         // Adventure sports injury
  | 'document_loss';           // Costs to replace lost passport/documents

type ClaimStatus =
  | 'pre_notification'         // Initial alert to insurer
  | 'submitted'                // Formal claim submitted
  | 'documents_pending'        // Awaiting documents from traveler
  | 'under_review'             // Insurer reviewing
  | 'surveyor_appointed'       // Surveyor assigned (for large claims)
  | 'approved'                 // Claim approved
  | 'partially_approved'       // Partial payment approved
  | 'rejected'                 // Claim rejected
  | 'disputed'                 // Traveler disputes rejection
  | 'settled';                 // Payment received

interface ClaimDocument {
  documentType: string;
  description: string;
  source: 'traveler' | 'agent' | 'hospital' | 'police' | 'airline';
  status: 'required' | 'collected' | 'submitted' | 'verified';
  fileUrl?: string;
  collectedAt?: Date;
}

// Common claim documents by incident type:
//
// Medical:
//   [ ] Hospital bills (original)
//   [ ] Discharge summary
//   [ ] Doctor's consultation notes
//   [ ] Prescription receipts
//   [ ] Medical reports (X-ray, blood tests)
//   [ ] Travel insurance policy copy
//   [ ] Passport copy (first and last page)
//   [ ] Visa copy
//   [ ] Boarding pass / ticket copy
//
// Theft/Robbery:
//   [ ] Police report / FIR
//   [ ] Itemized list of stolen items with values
//   [ ] Purchase receipts for stolen items
//   [ ] Travel insurance policy copy
//   [ ] Passport copy
//
// Trip Cancellation:
//   [ ] Cancellation reason documentation
//   [ ] Medical certificate (if medical reason)
//   [ ] Death certificate (if bereavement)
//   [ ] Original booking confirmations
//   [ ] Refund details from suppliers
//   [ ] Travel insurance policy copy

// Common claim rejection reasons (and prevention):
//
// 1. Pre-existing condition not disclosed
//    Prevention: Capture health declaration at policy purchase
//
// 2. Intoxication-related injury
//    Prevention: Cannot prevent, but document objectively
//
// 3. Unapproved adventure activity
//    Prevention: Ensure adventure sports cover is included if itinerary has any
//
// 4. Delayed reporting (>72 hours for theft)
//    Prevention: Automated prompt to file police report within 24 hours
//
// 5. Insufficient documentation
//    Prevention: Provide checklist immediately after incident
//
// 6. Destination under travel advisory
//    Prevention: Flag at booking if destination has active advisory
```

### F. India-Specific Emergency Coordination

```typescript
interface IndiaEmergencyCoordination {
  domestic: IndiaDomesticEmergency;
  international: IndiaInternationalEmergency;
}

interface IndiaDomesticEmergency {
  // For incidents within India involving travelers

  // Emergency Numbers
  emergencyNumbers: {
    allEmergency: '112';               // Single emergency number (Pan-India)
    police: '100';
    ambulance: '108';                  // EMRI (Emergency Management & Research Institute)
    fire: '101';
    womenHelpline: '181';
    childHelpline: '1098';
    tourismHelpline: '1363';           // Ministry of Tourism
    railwaySecurity: '182';
    railwayEnquiry: '139';
    ndrfControl: '+91-11-24363260';
  };

  // NDRF Coordination
  ndrf: {
    activation: NDRFActivation;
    stateNDRF: StateNDRF[];
  };

  // State Emergency Services
  stateServices: StateEmergencyService[];
}

interface NDRFActivation {
  // NDRF (National Disaster Response Force) activation criteria:
  // - State government requests NDRF deployment
  // - For L3 (serious) and above natural disasters
  // - NDRF battalions: 16 battalions across India
  // - Response time: Typically 12-24 hours for deployment
  // - Capabilities: Search & rescue, medical, flood rescue, CBRN
  // - Agency role: Report to state emergency ops center, assist travelers
  //
  // When to expect NDRF:
  // - Major earthquake (Richter > 5.0 in populated area)
  // - Large-scale flooding (multiple districts)
  // - Cyclone landfall
  // - Building collapse (multi-story)
  // - Industrial disaster (gas leak, explosion)
  //
  // Coordination protocol:
  // 1. Agency reports affected travelers to state emergency ops center
  // 2. NDRF team leader coordinates rescue at site
  // 3. Agency provides traveler details, last known location
  // 4. NDRF prioritizes rescue of trapped/injured individuals
  // 5. Agency arranges medical and logistical support post-rescue
}

interface StateEmergencyService {
  state: string;
  emergencyOpsCenter: string;
  emergencyOpsPhone: string;
  disasterManagementAuthority: string;
  tourismDepartmentEmergency: string;
  notes: string;
}

// Key state emergency contacts:
//
// Kerala:  State EOC: 0471-2331826, Tourism: 0471-2321132
//          (Flood-prone, tourist-heavy — critical for travel agencies)
// Rajasthan: State EOC: 0141-2227081, Tourism: 0141-5110605
//          (Desert incidents, heat emergencies)
// Goa:     State EOC: 0832-2420042, Tourism: 0832-2496514
//          (Water sports accidents, tourist safety)
// Himachal: State EOC: 0177-2629917, Tourism: 0177-2625242
//          (Landslides, road accidents, altitude sickness)
// Uttarakhand: State EOC: 0135-2710333, Tourism: 0135-2559898
//          (Char Dham yatra accidents, flash floods, landslides)
// J&K:     State EOC: 0194-2450389, Tourism: 0194-2502270
//          (Security incidents, landslide, avalanche)
// Maharashtra: State EOC: 022-22027990, Tourism: 022-22026726
//          (Mumbai urban emergencies, monsoon flooding)

interface IndiaInternationalEmergency {
  // For incidents abroad involving Indian citizens

  // MEA (Ministry of External Affairs) Coordination
  mea: {
    helpline24x7: '+91-11-2301 2113';
    tollFreeIndia: '1800-11-3029';
    madadPortal: 'madad.gov.in';
    email: 'cons2@mea.gov.in';         // Consular division
  };

  // Repatriation Protocols
  repatriation: {
    injured: RepatriationProtocol;
    deceased: DeceasedRepatriationProtocol;
  };
}

interface RepatriationProtocol {
  // Medical repatriation (injured traveler):
  // 1. Hospital stabilizes patient
  // 2. Insurance provider arranges medical evacuation
  //    - Air ambulance (critical cases)
  //    - Commercial flight with medical escort (stable cases)
  // 3. Indian embassy assists with documentation if needed
  // 4. Agency coordinates:
  //    - Hospital liaison
  //    - Insurance pre-authorization
  //    - Family communication
  //    - Flight arrangements to India
  //    - Receiving hospital in India
  //    - Ground ambulance at both ends
  //
  // Cost: Air ambulance $10,000-$100,000 depending on distance
  //       Medical escort on commercial: $3,000-$10,000
  //       Covered by: Travel insurance (if evacuation clause included)
}

interface DeceasedRepatriationProtocol {
  // Repatriation of remains (deceased traveler):
  // 1. Local authorities: Post-mortem, death certificate
  // 2. Indian embassy: Attestation of death certificate
  // 3. Embalming and sealing: Local mortuary
  // 4. Airline: Cargo booking for human remains
  // 5. Customs clearance at Indian airport
  // 6. Agency coordinates:
  //    - Local funeral home in destination country
  //    - Indian embassy/consulate documentation
  //    - Airline cargo booking
  //    - Customs agent at Indian airport
  //    - Local funeral home in India for receiving
  //    - Family communication and support
  //
  // Required documents:
  //   [ ] Death certificate (original, translated, notarized)
  //   [ ] Embassy attestation of death certificate
  //   [ ] Embalming certificate
  //   [ ] No-objection certificate from Indian embassy
  //   [ ] Airline booking confirmation (cargo)
  //   [ ] Passport of deceased (for cancellation)
  //   [ ] Police report / FIR (if applicable)
  //
  // Timeline: 3-14 days depending on country and cause of death
  // Cost: $2,000-$15,000 depending on distance
  // Covered by: Travel insurance repatriation clause

  // Note: For Indian citizens, the Indian embassy can provide:
  //   - Emergency travel document for family traveling to claim body
  //   - Attestation of documents
  //   - Liaison with local authorities
  //   - In extreme cases, financial assistance for repatriation
  //   (under Indian Community Welfare Fund - ICWF)
}
```

---

## Open Problems

1. **Incident triage accuracy** — With limited initial information, how do we quickly and accurately classify incident severity? A traveler saying "I need help" could mean anything from lost luggage to a medical emergency. How do we triage effectively?

2. **After-hours response** — Most Indian travel agencies are not 24/7 operations. A critical incident at 3 AM needs response when the assigned agent is asleep. What is the cost-effective model for 24/7 incident response?

3. **Cultural sensitivity in crisis communication** — Telling a family in India that a loved one has been injured abroad requires cultural sensitivity. Language, tone, and communication style matter. How do we train agents and build templates that are culturally appropriate?

4. **Regulatory reporting requirements** — When does an Indian travel agency need to report an incident to regulators (MEA, state tourism department, insurance regulator IRDAI)? What are the reporting thresholds and timelines?

5. **Liability and documentation** — In the Indian legal context, what documentation protects the agency from liability during incidents? What constitutes "reasonable care" in Indian courts?

6. **Multi-agency coordination in mass events** — During events like the 2015 Nepal earthquake (which affected many Indian tourists), coordination between agencies, MEA, NDRF, and insurance companies was chaotic. How do we build a structured multi-agency coordination protocol?

7. **Insurance claim success rate** — Indian travelers often face claim rejection due to documentation gaps or policy fine print. How do we improve claim success rates through better incident documentation and pre-trip policy education?

8. **Psychological support** — Post-incident, travelers and their families may need psychological support. This is not traditionally offered by Indian travel agencies. Should we integrate counseling services?

---

## Next Steps

- [ ] Design incident classification taxonomy with severity definitions and examples
- [ ] Build response playbook templates for top 10 most common incident types
- [ ] Create crisis communication templates for all stakeholder roles
- [ ] Map India-specific emergency coordination contacts (NDRF, state EOCs, MEA)
- [ ] Design post-incident review process and template
- [ ] Build insurance claim documentation checklists by incident type
- [ ] Research IRDAI (insurance regulator) claim processing requirements
- [ ] Design repatriation coordination workflow for international incidents
- [ ] Prototype incident management dashboard for agents
- [ ] Research 24/7 incident response models for mid-size Indian agencies
- [ ] Build MADAD portal integration for pre-filling consular grievances
- [ ] Design automated incident severity triage based on initial report
