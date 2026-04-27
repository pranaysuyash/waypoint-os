# Visa & Documentation 03: Compliance & Monitoring

> Tracking requirements, monitoring changes, and ensuring compliance

---

## Document Overview

**Focus:** Ongoing monitoring of travel documentation requirements
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Requirement Monitoring
- How do we track changing visa requirements?
- What sources do we monitor?
- How frequently do we check for changes?
- How do we validate data accuracy?

### 2. Customer Notifications
- When do we notify customers of requirements?
- How do we send reminders?
- What happens if requirements change after booking?
- How do we handle urgency?

### 3. Compliance Checking
- How do we verify customers have valid documents?
- What checks do we perform?
- When do we perform checks?
- What do we do if non-compliant?

### 4. Record Keeping
- What documentation records must we keep?
- How long do we retain records?
- What about privacy regulations?
- How do we handle document storage?

---

## Research Areas

### A. Change Detection

**Monitoring Strategy:**

| Source | Check Frequency | Method |
|--------|-----------------|--------|
| **Official government** | Daily/Weekly | Web scraping, RSS |
| **API providers** | Real-time | Webhooks, polling |
| **News sources** | Daily | News scraping |
| **Industry updates** | Weekly | Newsletter monitoring |

**Types of Changes to Detect:**

| Change Type | Impact | Urgency |
|-------------|--------|---------|
| **New visa requirement** | High | Critical |
| **Removed visa requirement** | Medium | Low |
| **Processing time change** | Medium | Medium |
| **Cost change** | Low | Low |
| **Document requirement change** | High | High |
| **Political situation** | Variable | Variable |

**Research:**
- What tools can help with monitoring?
- How do we prioritize changes?
- What is the cost of missing a change?

### B. Notification Strategy

**Notification Triggers:**

| Trigger | Timing | Channel | Urgency |
|---------|--------|---------|---------|
| **Trip booked** | Immediately | Email, app | Medium |
| **30 days before** | 30 days prior | Email, SMS | Medium |
| **14 days before** | 14 days prior | Email, SMS | High |
| **7 days before** | 7 days prior | Email, SMS | Critical |
| **Rules changed** | Immediately | Email, SMS, app | Critical |
| **Visa not received** | Based on processing time | Email, SMS, call | Critical |

**Notification Content:**

| Field | Description |
|-------|-------------|
| **Destination** | Country name |
| **Requirements** | Visa, passport validity, etc. |
| **Deadline** | When to complete by |
| **Action items** | What customer needs to do |
| **Links** | Where to get more info |

**Research:**
- How many notifications are too many?
- What channels work best?
- How do we handle timezone differences?

### C. Compliance Checks

**Check Points:**

| Check Point | What We Check | Action If Failed |
|-------------|---------------|------------------|
| **At booking** | Basic requirements | Warning, allow booking |
| **Before payment** | All requirements | Block if critical |
| **Before departure** | Documents obtained | Alert if not |
| **At check-in** | Documents valid | Cannot travel if not |

**Checks:**

| Check | Method | Notes |
|-------|--------|-------|
| **Passport expiry** | Date calculation | Auto-check |
| **Visa requirement** | Rules lookup | Auto-check |
| **Visa obtained** | Customer confirmation | Self-reported |
| **Blank pages** | Not checkable | Customer responsibility |
| **Passport condition** | Not checkable | Customer responsibility |

**Research:**
- What can we automate?
- What requires customer input?
- How do we handle edge cases?

### D. Document Storage

**Storage Considerations:**

| Consideration | Requirement |
|---------------|-------------|
| **Security** | Encryption, access controls |
| **Privacy** | GDPR, data protection laws |
| **Retention** | Keep for required period, then delete |
| **Access** | Customer and authorized staff only |

**Privacy Regulations:**

| Regulation | Requirements | Research Needed |
|------------|---------------|-----------------|
| **GDPR** | EU citizen data | ? |
| **India DPDP Act** | Indian citizen data | ? |
| **Other** | Varies by region | ? |

**Research:**
- What are the requirements?
- How do we comply?
- What are the penalties?

---

## Monitoring Data Model

```typescript
// Research-level model - not final

interface RequirementMonitoring {
  requirementId: string;
  destinationCountry: string;
  citizenship: string;

  // Current state
  currentRequirement: VisaRequirement;
  lastChecked: Date;
  lastChanged: Date;

  // Monitoring
  sources: MonitoringSource[];
  nextCheck: Date;
  changeHistory: RequirementChange[];

  // Alerts
  alertThreshold: AlertThreshold;
  alertContacts: string[];
}

interface RequirementChange {
  detectedAt: Date;
  changeType: ChangeType;
  description: string;
  previousState: VisaRequirement;
  newState: VisaRequirement;
  impact: ImpactAssessment;
}

type ChangeType =
  | 'visa_added'
  | 'visa_removed'
  | 'processing_time_changed'
  | 'cost_changed'
  | 'document_added'
  | 'document_removed'
  | 'restriction_added'
  | 'restriction_removed';
```

---

## Customer Compliance Tracking

```typescript
interface CustomerCompliance {
  customerId: string;
  tripId: string;

  // Requirements
  requirements: DocumentRequirement[];

  // Status per requirement
  status: ComplianceStatus[];

  // Notifications sent
  notifications: ComplianceNotification[];

  // Alerts
  alerts: ComplianceAlert[];
}

interface ComplianceStatus {
  requirement: DocumentRequirement;
  status: 'pending' | 'in_progress' | 'complete' | 'failed';
  dueDate: Date;
  completedAt?: Date;
  documents?: string[];  // Uploaded documents
}
```

---

## Open Problems

### 1. False Confidence
**Challenge:** Customer relies on our info, but it's wrong or incomplete

**Questions:**
- What disclaimers are needed?
- How do we minimize this risk?
- What is our liability?

### 2. Timing Pressure
**Challenge:** Customer realizes too late that they need a visa

**Options:**
- Expedited processing
- Trip cancellation
- Rebooking

**Research:** How do we handle this?

### 3. Document Verification
**Challenge:** We can't actually verify documents are valid

**Options:**
- Trust customer confirmation
- Use verification services
- Manual review

**Research:** What is practical?

### 4. Cross-Border Trips
**Challenge:** Multi-country trips have complex requirements

**Questions:**
- How do we check all requirements?
- What about transit visas?
- How do we present this clearly?

---

## Competitor Research Needed

| Competitor | Compliance Approach | Notable Patterns |
|------------|---------------------|------------------|
| **Expedia** | ? | ? |
| **Booking.com** | ? | ? |
| **Airlines** | ? | ? |

---

## Experiments to Run

1. **Change detection test:** Can we detect rule changes?
2. **Notification effectiveness:** Do customers act on reminders?
3. **Compliance rate:** What percentage are compliant by departure?
4. **Accuracy study:** How accurate is our data?

---

## References

- [Safety Systems](./SAFETY_DEEP_DIVE_MASTER_INDEX.md) — Risk monitoring
- [Timeline](./TIMELINE_DEEP_DIVE_MASTER_INDEX.md) — Event tracking

---

## Next Steps

1. Build requirements database
2. Implement change monitoring
3. Design notification system
4. Create compliance dashboard
5. Test with real trips

---

**Status:** Research Phase — Compliance patterns unknown

**Last Updated:** 2026-04-27
