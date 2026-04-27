# Reviews & Ratings 01: Collection

> Gathering customer feedback and reviews

---

## Document Overview

**Focus:** How we collect reviews
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Collection Methods
- How do we collect reviews?
- When do we ask for reviews?
- What channels do we use?
- How do we maximize response rates?

### Review Content
- What information do we collect?
- How do we structure reviews?
- What are rating categories?
- How do we encourage detailed feedback?

### Incentives
- Should we offer incentives?
- What types of incentives work?
- What are the ethical considerations?
- How do we prevent bias?

### Timing
- When is the best time to ask?
- How many reminders?
- What about post-trip timing?

---

## Research Areas

### A. Collection Channels

| Channel | Timing | Response Rate | Research Needed |
|---------|--------|--------------|-----------------|
| **Email** | 1-7 days post-trip | Medium | ? |
| **App notification** | Post-trip | Medium-high | ? |
| **SMS** | Post-trip | High | ? |
| **In-app prompt** | After service | Medium | ? |
| **Phone** | For high-value | Low | ? |

### B. Review Structure

**Ratings:**

| Category | Scale | Required | Research Needed |
|----------|-------|----------|-----------------|
| **Overall** | 1-5 stars | Yes | ? |
| **Service** | 1-5 stars | Yes | ? |
| **Quality** | 1-5 stars | Yes | ? |
| **Value** | 1-5 stars | Yes | ? |
| **Cleanliness** | 1-5 stars | Sometimes | ? |

**Written Feedback:**

| Field | Required | Research Needed |
|-------|----------|-----------------|
| **Title** | No | ? |
| **Detailed review** | No | ? |
| **Pros** | No | ? |
| **Cons** | No | ? |
| **Recommendation** | Yes/no | ? |

### C. Incentives

| Incentive | Type | Effectiveness | Research Needed |
|-----------|------|--------------|-----------------|
| **Loyalty points** | Future benefit | Medium | ? |
| **Discount** | Next booking | High | ? |
| **Charity donation** | Social good | Medium | ? |
| **Entry to contest** | Gamification | Low | ? |

### D. Timing Strategy

| Timing | Pros | Cons | Research Needed |
|--------|------|------|-----------------|
| **Immediately** | Fresh in memory | May still be traveling | ? |
| **1 day after** | Recent, settled | Too soon for hotel stay | ? |
| **3-7 days after** | Balanced | Optimal? | ? |
| **30 days after** | Full perspective | May forget details | ? |

---

## Data Model Sketch

```typescript
interface Review {
  id: string;
  bookingId: string;
  userId: string;

  // Subject
  subjectType: 'hotel' | 'activity' | 'transport' | 'service';
  subjectId: string;

  // Ratings
  overallRating: number; // 1-5
  categoryRatings: CategoryRatings;

  // Content
  title?: string;
  content?: string;
  pros?: string[];
  cons?: string[];

  // Metadata
  wouldRecommend: boolean;
  response?: string; // From provider

  // Status
  status: ReviewStatus;
  verified: boolean;

  // Timing
  submittedAt: Date;
  tripDate: Date;
}

type ReviewStatus =
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'flagged';

interface CategoryRatings {
  service?: number;
  quality?: number;
  value?: number;
  cleanliness?: number;
  location?: number;
}
```

---

## Open Problems

### 1. Response Rates
**Challenge:** Low response rates

**Options:** Multiple channels, reminders, incentives

### 2. Bias
**Challenge:** Only extremes review

**Options:** Outreach to middle reviewers, sampling

### 3. Fake Reviews
**Challenge:** Inauthentic reviews

**Options:** Verification, reporting, penalties

### 4. Negative Reviews
**Challenge:** Impact on business

**Options:** Response, resolution, context

---

## Next Steps

1. Design review collection flow
2. Build submission forms
3. Implement reminders
4. Create verification system

---

**Status:** Research Phase — Collection patterns unknown

**Last Updated:** 2026-04-27
