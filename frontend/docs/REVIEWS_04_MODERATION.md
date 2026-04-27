# Reviews & Ratings 04: Moderation & Response

> Review moderation and provider response management

---

## Document Overview

**Focus:** Review moderation and provider responses
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Moderation Policy
- What content is allowed?
- What gets removed?
- What is the appeals process?
- Who moderates?

### Content Standards
- What are the guidelines?
- How do we enforce them?
- What about borderline content?
- How do we handle disputes?

### Provider Response
- How can providers respond?
- What are the guidelines?
- Can providers dispute reviews?
- What about editing?

### Dispute Resolution
- How do review disputes work?
- What evidence is needed?
- Who decides?
- What are the outcomes?

---

## Research Areas

### A. Moderation Guidelines

**Prohibited Content:**

| Category | Examples | Action | Research Needed |
|----------|----------|--------|-----------------|
| **Hate speech** | Slurs, discrimination | Remove | ? |
| **Personal info** | Names, addresses | Remove/edit | ? |
| **Spam** | Repetitive, promotional | Remove | ? |
| **Fake reviews** | unverifiable, incentivized | Remove | ? |
| **Defamatory** | False, damaging claims | Review | ? |
| **Off-topic** | Not about service | May remove | ? |
| **Profanity** | Excessive | May edit | ? |

**Borderline Content:**

| Type | Consideration | Research Needed |
|------|---------------|-----------------|
| **Negative but fair** | Keep | ? |
| **Exaggerated** | Keep, may add note | ? |
| **Subjective** | Keep | ? |
| **Incomplete** | Keep | ? |

### B. Moderation Process

**Review Workflow:**

```
1. Submission
   → Automated checks
   → Fraud detection

2. Pending
   → If flagged, hold for review
   → Otherwise, publish

3. Flagged
   → User or system flags
   → Queue for moderation

4. Moderation
   → Review content
   → Decision: keep, edit, remove

5. Resolution
   → Notify reviewer
   → Allow appeal
```

**Moderation Sources:**

| Source | Trigger | Research Needed |
|--------|---------|-----------------|
| **Automated** | Keywords, patterns | ? |
| **User reports** | "Report" button | ? |
| **Provider requests** | Dispute form | ? |
| **Manual review** | Spot checks | ? |

### C. Provider Response

**Response Guidelines:**

| Guideline | Description | Research Needed |
|-----------|-------------|-----------------|
| **Professional** | No personal attacks | ? |
| **Helpful** | Address issues | ? |
| **Timely** | Respond within X days | ? |
| **Factual** | Correct errors, don't argue | ? |
| **No solicitation** | Don't ask to change review | ? |

**Response Options:**

| Action | When | Research Needed |
|--------|------|-----------------|
| **Public response** | Standard | ? |
| **Private message** | Personal info | ? |
| **Dispute request** | Factually incorrect | ? |
| **Edit request** | Minor errors | ? |

### D. Dispute Resolution

**Dispute Types:**

| Type | Process | Research Needed |
|------|---------|-----------------|
| **Never stayed** | Verify booking | ? |
| **False claims** | Request evidence | ? |
| **Confusing identity** | Wrong provider | ? |
| **Retaliation** | Prior interaction | ? |

**Resolution Steps:**

```
1. Provider submits dispute
   → Reason
   → Evidence

2. Reviewer notified
   → Given time to respond

3. Evidence review
   → Booking records
   → Communication
   → Other evidence

4. Decision
   → Keep review
   → Edit review
   → Remove review
   → Mark as disputed
```

**Outcomes:**

| Outcome | Effect | Research Needed |
|---------|--------|-----------------|
| **Upheld** | Review stays | ? |
| **Edited** | Changes made | ? |
| **Removed** | Review deleted | ? |
| **Marked disputed** | Note added | ? |

### E. Appeals

**Reviewer Appeals:**

| Trigger | Process | Research Needed |
|---------|---------|-----------------|
| **Removed review** | Appeal form | ? |
| **Edited review** | Request restore | ? |
| **Dispute decision** | Provide counter-evidence | ? |

**Provider Appeals:**

| Trigger | Process | Research Needed |
|---------|---------|-----------------|
| **Dispute rejected** | New evidence | ? |
| **Negative review kept** | Escalation | ? |

---

## Data Model Sketch

```typescript
interface ReviewModeration {
  reviewId: string;

  // Status
  status: ModerationStatus;
  flagged: boolean;
  flagReason?: string;

  // Moderation
  moderatedAt?: Date;
  moderatedBy?: string; // Admin ID
  moderationAction?: ModerationAction;
  moderationNote?: string;

  // Dispute
  disputeActive: boolean;
  disputeDetails?: DisputeDetails;

  // Appeals
  appeals: Appeal[];
}

type ModerationStatus =
  | 'pending'
  | 'approved'
  | 'flagged'
  | 'removed'
  | 'under_review';

type ModerationAction =
  | 'none'
  | 'edited'
  | 'removed'
  | 'restored';

interface DisputeDetails {
  disputedBy: string; // Provider ID
  disputedAt: Date;
  reason: DisputeReason;
  evidence: string[];
  status: DisputeStatus;
  resolvedAt?: Date;
  resolution?: DisputeResolution;
}

type DisputeReason =
  | 'never_booked'
  | 'false_claim'
  | 'wrong_identity'
  | 'retaliation'
  | 'other';

type DisputeStatus =
  | 'pending_reviewer_response'
  | 'under_review'
  | 'resolved';

type DisputeResolution =
  | 'upheld'
  | 'edited'
  | 'removed'
  | 'marked_disputed';

interface ProviderResponse {
  responseId: string;
  reviewId: string;
  providerId: string;

  // Content
  content: string;

  // Status
  status: ResponseStatus;

  // Moderation
  moderated: boolean;
  moderationNote?: string;

  // Timing
  respondedAt: Date;
  editedAt?: Date;
}

type ResponseStatus =
  | 'visible'
  | 'hidden'
  | 'pending';
```

---

## Open Problems

### 1. Subjectivity
**Challenge:** One person's fair review is another's attack

**Options:** Clear guidelines, examples, training

### 2. Resource Constraints
**Challenge:** Manual moderation is expensive

**Options:** Automation, community reporting, prioritization

### 3. Retaliatory Reviews
**Challenge:** Providers punished for enforcing rules

**Options:** Identity protection, review history consideration

### 4. Gaming the System
**Challenge:** Finding loopholes in moderation

**Options:** Continuous improvement, pattern detection

### 5. Legal Liability
**Challenge:** Defamatory content hosted

**Options:** Safe harbor practices, prompt removal, legal review

---

## Next Steps

1. Define moderation guidelines
2. Build moderation workflow
3. Create provider response system
4. Implement dispute resolution

---

**Status:** Research Phase — Moderation patterns unknown

**Last Updated:** 2026-04-27
