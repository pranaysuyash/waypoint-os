# Accessibility — Accessible Trip Planning Tools

> Research document for building trip planning features that serve travelers with disabilities.

---

## Key Questions

1. **What disability types must we accommodate (mobility, visual, hearing, cognitive, dietary)?**
2. **How do travelers with disabilities currently research and book accessible travel?**
3. **What accessibility data do we need from suppliers that we don't currently capture?**
4. **How do we present accessibility information without stigmatizing or overwhelming?**
5. **What's the accessibility matching algorithm — how to match traveler needs to supplier capabilities?**

---

## Research Areas

### Accessibility Need Profiles

```typescript
interface AccessibilityProfile {
  profileId: string;
  travelerId: string;
  disabilities: Disability[];
  accommodationNeeds: AccommodationNeed[];
  equipmentNeeds: EquipmentNeed[];
  assistanceNeeds: AssistanceNeed[];
  communicationPreferences: CommunicationPreference[];
}

type DisabilityCategory =
  | 'mobility'          // Wheelchair, limited walking, stair difficulty
  | 'visual'            // Blind, low vision, color blind
  | 'hearing'           // Deaf, hard of hearing
  | 'cognitive'         // Autism, ADHD, learning disabilities, dementia
  | 'medical'           // Chronic illness, allergies, dialysis needs
  | 'senior'            // Age-related mobility, vision, hearing
  | 'temporary';        // Injury, pregnancy, post-surgery

interface AccommodationNeed {
  category: DisabilityCategory;
  specificNeeds: string[];
  severity: 'mild' | 'moderate' | 'severe';
  mustHave: boolean;
}

// Examples:
// Mobility: "wheelchair_accessible_room", "roll_in_shower", "grab_bars"
// Visual: "braille_signage", "audio_description", "guide_dog_friendly"
// Hearing: "visual_fire_alarm", "tdd_phone", "sign_language_interpreter"
// Medical: "refrigerator_for_medication", "hypoallergenic bedding", "dialysis_nearby"
// Dietary: "gluten_free", "nut_free", "diabetic_friendly", "pure_veg"
```

### Supplier Accessibility Data Model

```typescript
interface SupplierAccessibility {
  supplierId: string;
  selfReported: AccessibilitySelfReport;
  verifiedBy: AccessibilityVerification[];
  certifications: AccessibilityCertification[];
  lastAuditDate?: Date;
}

interface AccessibilitySelfReport {
  completedAt: Date;
  completedBy: string;
  features: AccessibilityFeature[];
  limitations: string[];
  photos: AccessibilityPhoto[];
}

interface AccessibilityFeature {
  category: DisabilityCategory;
  feature: string;
  details: string;
  location: string;             // Where in the property
  photos: string[];
}

interface AccessibilityVerification {
  verifiedBy: 'internal_audit' | 'third_party' | 'government' | 'traveler_report';
  verifiedAt: Date;
  findings: string[];
  rating: 'fully_accessible' | 'partially_accessible' | 'not_accessible';
}
```

### Accessibility-Aware Search & Matching

```typescript
interface AccessibilitySearch {
  travelerProfile: AccessibilityProfile;
  destination: string;
  dates: DateRange;
  // Filter results by accessibility compatibility
  compatibilityThreshold: 'exact' | 'high' | 'moderate';
  // Sort by accessibility match quality
  sortByAccessibility: boolean;
}

interface AccessibilityMatch {
  supplierId: string;
  overallCompatibility: number;     // 0-1 score
  mustHaveMatch: boolean;           // All must-have needs met
  featureMatches: FeatureMatch[];
  warnings: AccessibilityWarning[];
  alternatives: AlternativeSuggestion[];
}

interface FeatureMatch {
  need: string;
  available: boolean;
  verified: boolean;
  notes: string;
}
```

### Trip Itinerary Accessibility Check

**Automated validation that the full itinerary is accessible end-to-end:**

```typescript
interface ItineraryAccessibilityCheck {
  tripId: string;
  travelerProfile: AccessibilityProfile;
  segmentChecks: SegmentAccessibilityCheck[];
  transferChecks: TransferAccessibilityCheck[];
  overallVerdict: 'fully_accessible' | 'accessible_with_notes' | 'partially_accessible' | 'not_accessible';
  recommendations: string[];
}

interface SegmentAccessibilityCheck {
  segmentId: string;
  type: 'flight' | 'hotel' | 'activity' | 'transfer';
  accessibility: 'verified_accessible' | 'reported_accessible' | 'unknown' | 'not_accessible';
  issues: string[];
  alternatives: string[];
}

interface TransferAccessibilityCheck {
  fromSegment: string;
  toSegment: string;
  accessibleRoute: boolean;
  distance: number;
  terrain: 'flat' | 'inclined' | 'stairs' | 'uneven';
  vehicleAccessibility: boolean;
}
```

---

## Open Problems

1. **Supplier accessibility data gap** — Most hotels and activity providers don't self-report accessibility features. Relying on self-reporting gives incomplete data. Third-party audit is expensive.

2. **Standardization** — No universal standard for what "wheelchair accessible" means. One hotel's "accessible" room may not meet another traveler's needs.

3. **Transfer accessibility** — Getting from airport to hotel is often the hardest part. Taxi accessibility, train station elevators, sidewalk conditions — all outside our control.

4. **Dynamic conditions** — Accessibility features may change (elevator under maintenance, ramp removed). How to keep data current?

5. **Privacy balance** — Collecting detailed disability information is sensitive. How to ask for enough to plan properly without violating privacy or making travelers uncomfortable?

---

## Next Steps

- [ ] Research accessible travel platforms (Sage Traveling, Accessible Journeys, Wheel the World)
- [ ] Design accessibility profile creation UX for travelers
- [ ] Create supplier accessibility questionnaire template
- [ ] Study accessibility data standards (EN 17210, ISO 21902)
- [ ] Design accessibility matching algorithm
- [ ] Prototype itinerary accessibility checker
