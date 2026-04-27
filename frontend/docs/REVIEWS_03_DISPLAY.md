# Reviews & Ratings 03: Display & Presentation

> How reviews and ratings are shown to users

---

## Document Overview

**Focus:** Review display and presentation
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions

### Display Strategy
- How do we display ratings?
- What information is most important?
- How do we handle negative reviews?
- What about filtering and sorting?

### Visual Design
- How do we show star ratings?
- What about verified badges?
- How do we display review content?
- What about photos and media?

### Placement
- Where do reviews appear?
- How many reviews to show?
- What about on search results?
- What about on provider pages?

### Trust Signals
- How do we build trust?
- What signals matter most?
- How do we handle fake reviews?
- What about response from providers?

---

## Research Areas

### A. Rating Display

**Summary Rating:**

| Format | Description | Research Needed |
|--------|-------------|-----------------|
| **Stars only** | Simple 1-5 stars | ? |
| **Stars + count** | "4.5 (123 reviews)" | ? |
| **Distribution** | Bar chart of ratings | ? |
| **Breakdown** | By category | ? |

**Category Ratings:**

| Category | Display | Research Needed |
|----------|---------|-----------------|
| **Overall** | Prominent | ? |
| **Service** | Secondary | ? |
| **Quality** | Secondary | ? |
| **Value** | Secondary | ? |
| **Cleanliness** | Contextual | ? |

### B. Review Content Display

**Content Structure:**

| Element | Display | Research Needed |
|---------|---------|-----------------|
| **Title** | Bold, prominent | ? |
| **Rating** | Stars, visible | ? |
| **Date** | Small, below | ? |
| **Verified badge** | If verified | ? |
| **Content** | Full or truncated | ? |
| **Pros/Cons** | Structured list | ? |
| **Photos** | Thumbnail gallery | ? |
| **Provider response** | Highlighted | ? |

**Truncation:**

| Approach | Description | Research Needed |
|----------|-------------|-----------------|
| **Full text** | Show everything | ? |
| **3 lines + "more"** | Common pattern | ? |
| **Character limit** | Fixed length | ? |
| **Smart summary** | AI summary | ? |

### C. Filtering & Sorting

**Sort Options:**

| Option | Use Case | Research Needed |
|--------|----------|-----------------|
| **Most recent** | Current opinions | ? |
| **Highest rated** | Best experiences | ? |
| **Lowest rated** | Pain points | ? |
| **Most helpful** | Community rated | ? |
| **Verified only** | Trust filter | ? |

**Filter Options:**

| Filter | Options | Research Needed |
|--------|---------|-----------------|
| **Rating** | 1-5 stars | ? |
| **Verified** | Yes/No | ? |
| **With photos** | Yes/No | ? |
| **With response** | Yes/No | ? |
| **Date range** | Custom | ? |
| **Travel type** | Family, business, etc. | ? |

### D. Placement Strategy

**Search Results:**

| Placement | Content | Research Needed |
|----------|---------|-----------------|
| **Next to name** | Stars + count | ? |
| **Snippet** | One recent review | ? |
| **Badge** | "Excellent" etc. | ? |

**Provider Page:**

| Section | Content | Research Needed |
|---------|---------|-----------------|
| **Hero** | Summary rating | ? |
| **Summary box** | Distribution, categories | ? |
| **Review list** | Full reviews | ? |
| **Sidebar** | Quick stats | ? |

### E. Trust Signals

**Visual Indicators:**

| Signal | Display | Research Needed |
|--------|---------|-----------------|
| **Verified badge** | Checkmark icon | ? |
| **"Confirmed stay"** | Text label | ? |
| **Booking ID** | Partial, for trust | ? |
| **Multiple reviews** | "X reviews from Y" | ? |
| **Provider response** | Highlighted | ? |

**Anti-Fraud Signals:**

| Signal | Display | Research Needed |
|--------|---------|-----------------|
| **Flagged count** | Hidden, for moderation | ? |
| **Removed reviews** | "X reviews removed" | ? |
| **Report option** | Report button | ? |

---

## Data Model Sketch

```typescript
interface ReviewDisplay {
  reviewId: string;

  // Display config
  showFullContent: boolean;
  showVerifiedBadge: boolean;
  showProviderResponse: boolean;

  // Metrics
  helpfulCount: number;
  notHelpfulCount: number;
  reportCount: number;

  // Status
  displayStatus: 'visible' | 'hidden' | 'pending';
}

interface RatingDisplay {
  subjectId: string;
  subjectType: SubjectType;

  // Summary
  averageRating: number;
  totalReviews: number;
  distribution: RatingDistribution;

  // Breakdown
  categoryAverages: CategoryAverages;

  // Trust
  verifiedCount: number;
  verifiedPercentage: number;
}

interface RatingDistribution {
  oneStar: number;
  twoStars: number;
  threeStars: number;
  fourStars: number;
  fiveStars: number;
}

interface CategoryAverages {
  service?: number;
  quality?: number;
  value?: number;
  cleanliness?: number;
  location?: number;
}
```

---

## Open Problems

### 1. Review Bombing
**Challenge:** Coordinated negative reviews

**Options:** Detection, temporary hiding, investigation

### 2. Fake Reviews
**Challenge:** Inauthentic reviews appearing genuine

**Options:** Better verification, community reporting, penalties

### 3. Selection Bias
**Challenge:** Only extremes review

**Options:** Outreach to middle, sampling, incentives

### 4. Outdated Reviews
**Challenge:** Old reviews no longer relevant

**Options:** Weighting by recency, expiration, date warnings

### 5. Response Quality
**Challenge:** Generic or defensive provider responses

**Options:** Response guidelines, rating responses

---

## Next Steps

1. Design rating display components
2. Build review list with filters
3. Implement trust signals
4. Create provider response system

---

**Status:** Research Phase — Display patterns unknown

**Last Updated:** 2026-04-27
