# Local Recommendations 04: Contribution & Feedback

> How users contribute and improve recommendations

---

## Document Overview

**Focus:** User contributions to recommendations
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Contribution Types
- How can users contribute?
- What content do we accept?
- How do we verify contributions?
- What about spam and abuse?

### Incentives
- Why would users contribute?
- What incentives work?
- How do we encourage quality?
- What about gamification?

### Quality Control
- How do we ensure quality?
- What is the moderation process?
- How do we handle disputes?
- What about editing?

### Recognition
- How do we recognize contributors?
- What about attribution?
- How do we build community?
- What about expert status?

---

## Research Areas

### A. Contribution Types

**Content Contributions:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **New places** | Add missing places | ? |
| **Photos** | Upload photos | ? |
| **Reviews** | Write reviews | ? |
| **Tips** | Quick advice | ? |
| **Corrections** | Fix wrong info | ? |
| **Hours updates** | Update hours | ? |
| **Tags/labels** | Add categories | ? |

**Feedback Types:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Upvote/Downvote** | Simple feedback | ? |
| **Visited** | Mark as visited | ? |
| **Wishlist** | Save for later | ? |
| **Not interested** | Negative signal | ? |
| **Report issue** | Flag problems | ? |

### B. Contribution Workflow

**Adding New Places:**

```
1. User submits place
   → Name, location, category
   → Basic details

2. Verification
   → Does it exist?
   → Is it duplicate?
   → Basic validation

3. Moderation
   → Quick review
   → Approve/request changes

4. Publication
   → Added to database
   → Attribution to contributor
```

**Updating Existing:**

```
1. User suggests edit
   → What to change
   → Evidence/reason

2. Validation
   → Check against current
   → Cross-reference

3. Review
   → Accept/Reject/Request more

4. Update
   → Apply changes
   → Version history
```

### C. Quality Assurance

**Validation Checks:**

| Check | Description | Research Needed |
|-------|-------------|-----------------|
| **Duplicate detection** | Already exists? | ? |
| **Location verification** | Is location valid? | ? |
| **Format validation** | Required fields | ? |
| **Spam detection** | Bot patterns | ? |
| **Adult content** | Inappropriate material | ? |

**Moderation Tiers:**

| Tier | Trigger | Process | Research Needed |
|------|---------|---------|-----------------|
| **Auto-approved** | Trusted contributors | Automatic | ? |
| **Quick review** | New contributors | Fast check | ? |
| **Full review** | Flagged content | Detailed review | ? |
| **Community vote** | Disputed | Peer review | ? |

### D. Incentives

**Recognition Types:**

| Type | Description | Research Needed |
|------|-------------|-----------------|
| **Attribution** | Name on contribution | ? |
| **Badges** | Achievement badges | ? |
| **Points** | Contribution points | ? |
| **Levels** | Contributor status | ? |
| **Leaderboards** | Top contributors | ? |
| **Expert status** | Topic expert | ? |

**Extrinsic Rewards:**

| Reward | Description | Research Needed |
|--------|-------------|-----------------|
| **Loyalty points** | Redeemable | ? |
| **Discounts** | On bookings | ? |
| **Premium features** | Access to more | ? |
| **Early access** | New features | ? |

**Intrinsic Motivations:**

| Motivator | Description | Research Needed |
|-----------|-------------|-----------------|
| **Helping others** | Altruism | ? |
| **Sharing passion** | Love for local | ? |
| **Recognition** | Social status | ? |
| **Improving platform** | Investment | ? |

### E. Trust & Reputation

**Contributor Reputation:**

| Factor | Weight | Research Needed |
|--------|--------|-----------------|
| **Contribution count** | Volume | ? |
| **Acceptance rate** | Quality | ? |
| **Community votes** | Peer validation | ? |
| **Account age** | Longevity | ? |
| **Reports received** | Trust issues | ? |

**Reputation Levels:**

| Level | Requirements | Privileges | Research Needed |
|-------|--------------|------------|-----------------|
| **New** | 0-5 contributions | Standard | ? |
| **Contributor** | 5+ contributions, good quality | Skip some checks | ? |
| **Trusted** | 20+ contributions, high quality | Auto-approve | ? |
| **Expert** | Topic specialist | Category authority | ? |
| **Moderator** | Selected | Review powers | ? |

---

## Data Model Sketch

```typescript
interface Contribution {
  contributionId: string;
  contributorId: string;

  // Content
  type: ContributionType;
  itemId?: string; // For updates
  data: ContributionData;

  // Status
  status: ContributionStatus;
  reviewedAt?: Date;
  reviewedBy?: string;

  // Feedback
  rejectionReason?: string;
  requestedChanges?: string[];

  // Metadata
  submittedAt: Date;
  version: number;
}

type ContributionType =
  | 'new_place'
  | 'photo_upload'
  | 'review'
  | 'tip'
  | 'correction'
  | 'hours_update'
  | 'category_tag';

type ContributionStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'changes_requested';

interface ContributorProfile {
  userId: string;

  // Stats
  totalContributions: number;
  approvedContributions: number;
  rejectedContributions: number;
  pendingContributions: number;

  // Reputation
  reputationScore: number; // 0-100
  level: ContributorLevel;
  badges: Badge[];

  // Expertise
  expertise: ExpertiseArea[];

  // Trust
  trustScore: number; // 0-1
  reportsReceived: number;

  // Recognition
  totalUpvotes: number;
  totalViews: number;
}

type ContributorLevel =
  | 'new'
  | 'contributor'
  | 'trusted'
  | 'expert'
  | 'moderator';

interface ExpertiseArea {
  category: string;
  location?: string;
  score: number; // 0-100
  contributions: number;
}

interface Badge {
  badgeId: string;
  name: string;
  description: string;
  earnedAt: Date;
  level?: number; // For multi-level badges
}
```

---

## Open Problems

### 1. Quality vs. Quantity
**Challenge:** Many low-quality contributions

**Options:** Review thresholds, reputation gates, quality rewards

### 2. Vandalism
**Challenge:** Malicious edits

**Options:** Revert, ban, verification, trusted editors

### 3. Bias
**Challenge:** Contributors promoting own interests

**Options:** Disclosure, conflict detection, moderation

### 4. Stale Data
**Challenge:** Contributions become outdated

**Options:** Expiration, verification prompts, community updates

### 5. Participation Rate
**Challenge:** Few contributors

**Options:** Lower friction, better incentives, targeted outreach

---

## Next Steps

1. Design contribution workflow
2. Build reputation system
3. Create moderation tools
4. Implement recognition features

---

**Status:** Research Phase — Contribution patterns unknown

**Last Updated:** 2026-04-27
