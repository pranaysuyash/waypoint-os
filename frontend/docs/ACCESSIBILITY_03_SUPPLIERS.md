# Accessibility — Supplier Discovery & Verification

> Research document for discovering, verifying, and maintaining accessibility information from suppliers.

---

## Key Questions

1. **How do we build an accessibility database for suppliers who don't self-report?**
2. **What third-party accessibility data sources exist?**
3. **How do traveler reviews and feedback contribute to accessibility verification?**
4. **What's the verification workflow — who checks and how often?**
5. **How do we handle accessibility claims that turn out to be inaccurate?**

---

## Research Areas

### Accessibility Data Sources

```typescript
interface AccessibilityDataSource {
  source: string;
  type: 'self_reported' | 'third_party' | 'government' | 'crowdsourced' | 'automated';
  reliability: number;
  coverage: string;
  cost: string;
  updateFrequency: string;
}

// Potential sources:
// 1. Supplier self-reporting (questionnaire during onboarding)
// 2. Booking.com accessibility filters data (via API/partnership)
// 3. Wheel the World (accessible travel database)
// 4. Government accessibility registries (country-specific)
// 5. Traveler crowdsourced reports
// 6. Google Maps accessibility attributes
// 7. TripAdvisor accessibility reviews
// 8. Internal audit team inspections
```

### Supplier Accessibility Questionnaire

**Minimal viable questionnaire during supplier onboarding:**

```typescript
interface AccessibilityQuestionnaire {
  sections: QuestionnaireSection[];
  estimatedCompletionTime: string;   // Target: 10-15 minutes
  incentiveForCompletion: string;    // E.g., higher search ranking
}

interface QuestionnaireSection {
  category: DisabilityCategory;
  questions: AccessibilityQuestion[];
}

interface AccessibilityQuestion {
  id: string;
  question: string;
  type: 'yes_no' | 'yes_no_na' | 'multiple_choice' | 'text' | 'photo_upload';
  options?: string[];
  followUp?: AccessibilityQuestion;   // If yes, ask for details
  required: boolean;
}

// Sample questions:
// Mobility:
// - "Do you have wheelchair-accessible rooms?" → Yes/No
//   → If yes: "Describe the accessible features (roll-in shower, grab bars, etc.)"
// - "Is there ramp or elevator access to all public areas?" → Yes/No/Partial
// - "What is the width of your standard doorway?" → Multiple choice
// - "Upload photos of accessible room and bathroom" → Photo upload
//
// Visual:
// - "Do you have braille signage in rooms and common areas?" → Yes/No/Partial
// - "Are service animals welcome?" → Yes/No
//
// Hearing:
// - "Do rooms have visual fire alarms?" → Yes/No
// - "Is there a TDD/TTY phone available?" → Yes/No
```

### Crowdsourced Verification

```typescript
interface TravelerAccessibilityReport {
  reportId: string;
  tripId: string;
  supplierId: string;
  travelerProfile: DisabilityCategory;
  reportedAt: Date;
  ratings: AccessibilityRating[];
  photos: string[];
  comments: string;
  verified: boolean;
}

interface AccessibilityRating {
  category: DisabilityCategory;
  feature: string;
  rating: 'excellent' | 'good' | 'adequate' | 'poor' | 'not_available';
  details: string;
}
```

### Accuracy & Trust Scoring

```typescript
interface AccessibilityTrustScore {
  supplierId: string;
  overallScore: number;               // 0-100
  dataSources: DataSourceScore[];
  lastVerified: Date;
  disagreementRate: number;            // % of conflicting reports
  travelerConfidence: number;          // Based on traveler feedback
}

interface DataSourceScore {
  source: string;
  contribution: number;                // Weight in overall score
  lastUpdated: Date;
  reliability: number;
}
```

---

## Open Problems

1. **Self-reporting accuracy** — Hotels may overstate accessibility features to avoid losing bookings. How to detect and flag inflated claims?

2. **Coverage at scale** — Manually verifying accessibility for thousands of suppliers is infeasible. Need a tiered approach: self-report → crowdsourced → professional audit.

3. **Accessibility drift** — A hotel renovates and removes accessible features. No one tells us. How to detect changes?

4. **Negative data** — If a supplier doesn't respond to accessibility questions, is that "not accessible" or "unknown"? How to distinguish missing data from confirmed lack of features?

5. **Liability for accessibility claims** — If we say a hotel is "wheelchair accessible" and it turns out not to be, are we liable? Need clear disclaimers and verification tiers.

---

## Next Steps

- [ ] Design supplier accessibility questionnaire (minimal + extended versions)
- [ ] Research third-party accessibility databases for travel
- [ ] Design traveler feedback mechanism for accessibility verification
- [ ] Study liability frameworks for accessibility information
- [ ] Prototype accessibility data integration from Google Maps and Booking.com
