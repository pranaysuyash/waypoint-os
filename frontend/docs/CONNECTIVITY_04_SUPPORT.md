# SIM Cards & Connectivity 04: Support & Troubleshooting

> Handling issues, refunds, and customer support

---

## Document Overview

**Focus:** Post-purchase support for connectivity services
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Common Issues
- What are the most common problems?
- How do we troubleshoot activation failures?
- What about slow data or no service?
- How do we handle device incompatibility?

### 2. Support Escalation
- What can we handle vs. provider issues?
- How do we escalate to providers?
- What is our liability?
- How do we handle complaints?

### 3. Refunds & Cancellations
- What is the refund policy?
- How do we handle partial usage?
- What about expired plans?
- How do we process refunds?

### 4. Top-Ups & Changes
- Can customers modify plans?
- How do top-ups work?
- What about extending validity?
- Can plans be transferred?

---

## Research Areas

### A. Common Issues & Solutions

| Issue | Cause | Solution | Escalation |
|-------|-------|----------|------------|
| **Can't scan QR** | Camera, screen, lighting | Manual LPA entry | Provider |
| **eSIM not supported** | Device, region | Refund, physical SIM | Us |
| **No data** | APN, coverage, activation | Settings check | Provider |
| **Slow data** | Network congestion | Explain, alternative | None |
| **Plan expired** | Validity period | Buy new plan | Us |
| **Wrong region** | Customer error | Refund, correct plan | Us |
| **Used all data** | Data limit | Top-up, new plan | Us |

**Research:**
- What are the actual failure rates?
- Which issues can we resolve?
- How do we measure resolution time?

### B. Troubleshooting Guides

**eSIM Issues:**

| Symptom | Steps | When to Escalate |
|---------|-------|-----------------|
| **QR won't scan** | 1. Check brightness 2. Clean screen 3. Try different angle 4. Use LPA string | After LPA fails |
| **No eSIM option** | 1. Check device compatibility 2. Update iOS/Android 3. Check carrier lock | If device compatible |
| **Activation failed** | 1. Restart phone 2. Check internet 3. Re-scan QR 4. Contact provider | After restart fails |

**Data Issues:**

| Symptom | Steps | When to Escalate |
|---------|-------|-----------------|
| **No data connection** | 1. Check data roaming on 2. Check APN 3. Toggle airplane mode 4. Restart phone | If nothing works |
| **Slow data** | 1. Speed test 2. Check network type 3. Move location | If < 1Mbps consistently |
| **Can't send SMS** | 1. Check SMSC 2. Check plan includes SMS | If plan includes SMS |

### C. Refund Policy

**Refund Scenarios:**

| Scenario | Refund | Reason |
|----------|--------|--------|
| **Device incompatible** | Full | Our fault for not checking |
| **Never activated** | Full | Unused service |
| **Activated, issues** | Case by case | Provider dependent |
| **Used some data** | Partial | Pro-rated? |
| **Plan expired** | None | Validity passed |
| **Wrong destination** | Case by case | Customer error? |

**Research:**
- What are provider refund policies?
- How do we handle edge cases?
- What is our refund window?

### D. Top-Ups & Extensions

**Modification Options:**

| Action | Allowed? | How |
|--------|----------|-----|
| **Top-up data** | Sometimes | New plan or provider feature |
| **Extend validity** | Rarely | New plan |
| **Change plan** | Before activation | Cancel and reorder |
| **Transfer plan** | Never | eSIM is locked to device |

**Research:**
- Which providers allow top-ups?
- How do we handle modifications?
- What are the fees?

---

## Support Data Model

```typescript
interface ConnectivitySupportIssue {
  id: string;
  orderId: string;
  customerId: string;

  // Issue
  type: IssueType;
  severity: 'low' | 'medium' | 'high';
  status: IssueStatus;
  reportedAt: Date;

  // Details
  description: string;
  deviceInfo?: DeviceInfo;
  screenshots?: string[];

  // Resolution
  attemptedSolutions: string[];
  escalatedTo?: 'provider' | 'technical';
  resolvedAt?: Date;
  resolution?: string;

  // Financial
  refundIssued?: Money;
  creditIssued?: Money;
}

type IssueType =
  | 'activation_failed'
  | 'no_data'
  | 'slow_data'
  | 'wrong_region'
  | 'device_incompatible'
  | 'qr_scan_failed'
  | 'plan_expired'
  | 'other';

type IssueStatus =
  | 'open'
  | 'investigating'
  | 'awaiting_customer'
  | 'awaiting_provider'
  | 'resolved'
  | 'refunded'
  | 'closed';
```

---

## Support Playbook

**Tier 1: Self-Service**

| Issue | Resource |
|-------|----------|
| Activation | FAQ, video guides |
| Device compatibility | Compatibility checker |
| Settings | APN configuration guides |

**Tier 2: Our Support**

| Issue | Action |
|-------|--------|
| QR scan issues | Provide LPA string |
| Basic troubleshooting | Guide through steps |
| Refund requests | Process within policy |

**Tier 3: Provider Escalation**

| Issue | Action |
|-------|--------|
| eSIM profile issues | Provider technical support |
| Network outages | Provider status |
| Special cases | Provider customer service |

---

## Open Problems

### 1. Liability Boundaries
**Challenge:** Customer says data doesn't work, provider says it does

**Questions:**
- How do we verify?
- Who do we believe?
- What is our refund obligation?

### 2. "It's Too Slow"
**Challenge:** Customer expects 5G, gets 3G

**Options:**
- Explain expectations
- Offer refund if materially different
- Caveat emptor

**Research:** What did we promise?

### 3. Refund Processing
**Challenge:** Provider won't refund, customer demands it

**Options:**
- Absorb cost
- Fight customer
- Split difference

**Research:** What is the customer lifetime value?

### 4. Support Cost
**Challenge:** Connectivity support is high-volume

**Questions:**
- How do we minimize support?
- What can be automated?
- What is the cost per ticket?

---

## Competitor Research Needed

| Competitor | Support Approach | Notable Patterns |
|------------|------------------|------------------|
| **Airalo** | ? | ? |
| **Nomad** | ? | ? |
| **Carrier support** | ? | ? |

---

## Experiments to Run

1. **Issue categorization:** What are the common issues?
2. **Self-service test:** Can customers self-resolve?
3. **Refund analysis:** What is the refund rate?
4. **Support cost study:** What does each ticket cost?

---

## References

- [Activities - Operations](./ACTIVITIES_04_OPERATIONS.md) — Similar support patterns
- [Communication Hub](./COMM_HUB_DEEP_DIVE_MASTER_INDEX.md) — Support channels

---

## Next Steps

1. Build troubleshooting guides
2. Implement self-service resources
3. Define refund policy
4. Set up provider escalation
5. Measure support metrics

---

**Status:** Research Phase — Support patterns unknown

**Last Updated:** 2026-04-27
