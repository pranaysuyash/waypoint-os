# Package Tours 02: Search & Discovery

> Finding, filtering, and comparing vacation packages

---

## Document Overview

**Focus:** How customers discover and compare package tours
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Search Parameters
- What are the primary search filters? (Destination, dates, budget?)
- How do customers search differently for packages vs. individual components?
- What about flexible dates?
- How do we handle group size?

### 2. Display & Comparison
- How do we present packages? (Cards, lists, detail view?)
- What information is most important?
- How do we compare packages?
- What about reviews and ratings?

### 3. Pricing Display
- How do we show pricing that may include flights vs. land-only?
- What about per-person vs. total pricing?
- How do we handle price components?
- What about hidden costs?

### 4. Availability
- How do we show availability status?
- What about "guaranteed departure" vs "on request"?
- How do we handle limited seats?
- What about waitlists?

---

## Research Areas

### A. Search Parameters

**Primary Search Inputs:**

| Parameter | Type | Required? | Research Needed |
|-----------|------|-----------|-----------------|
| **Destination** | Text/select | Yes | How structured? |
| **Travel Dates** | Date/range | Yes | Flexible? |
| **Duration** | Range | Optional | Popular ranges? |
| **Budget** | Range | Optional | Price points? |
| **Travelers** | Number | Yes | How affects price? |
| **Package Type** | Select | Optional | Categories? |

**Advanced Filters:**

| Filter | Type | Research Needed |
|--------|------|-----------------|
| **Departure City** | Multi-select | Indian airports? |
| **Activities** | Multi-select | Activity types? |
| **Service Level** | Select | Budget/standard/luxury? |
| **Meal Plan** | Select | Breakfast/all-inclusive? |
| **Accommodation Rating** | Range | Star categories? |
| **Tour Guide** | Boolean | Language options? |
| **Physical Level** | Select | Easy/moderate/hard? |

**Search Patterns:**

| Pattern | Description | Research Needed |
|----------|-------------|-----------------|
| **Inspiration search** | Browse by destination/theme | Popular themes? |
| **Deal search** | Find discounted packages | How to find deals? |
| **Specific search** | Exact dates, destination | Most common? |
| **Flexible search** | Open dates, find best value | How to price? |

### B. Package Display

**Card Information Priority:**

| Element | Priority | Display Notes | Research Needed |
|---------|----------|---------------|-----------------|
| **Package Name** | High | Descriptive title | ? |
| **Destination** | High | Primary location | ? |
| **Duration** | High | Days/nights | ? |
| **Price** | High | Per person/from | ? |
| **Image** | High | Hero image | ? |
| **Dates** | High | Next departure | ? |
| **Highlights** | Medium | 3-5 key features | ? |
| **Inclusions** | Medium | Brief summary | ? |
| **Rating** | Medium | Customer rating | ? |
| **Availability** | Medium | Seats left/status | ? |
| **Operator** | Low | Provider name | ? |

**Comparison View:**

| Attribute | Display As | Research Needed |
|-----------|-----------|-----------------|
| **Price** | Side-by-side | Include taxes? |
| **Duration** | Days | Include travel days? |
| **Inclusions** | Checklist | What to highlight? |
| **Accommodation** | Hotel names | Star rating? |
| **Meals** | Meal plan | Detailed? |
| **Activities** | List | Quantify? |
| **Transport** | Flight details | Airlines/times? |
| **Guide** | Yes/no | Language? |

### C. Pricing Display

**Pricing Complexity:**

| Pricing Type | Description | Display Challenge | Research Needed |
|--------------|-------------|-------------------|-----------------|
| **From Price** | Starting price per person | May not include flights | How to clarify? |
| **Land Only** | Excludes international flights | Cheaper but misleading | Clear labeling? |
| **Air + Land** | Includes flights | Price varies by city | How to show? |
| **Total Price** | All-inclusive | May not include optional items | What's excluded? |

**Price Breakdown:**

| Component | Show? | Notes |
|-----------|-------|-------|
| Base price | Yes | Per person |
| Taxes | Yes | Amount |
| Single supplement | Conditional | If solo |
| Child discount | Conditional | If children |
| Optional add-ons | Optional | Activities, upgrades |

**Research:**
- What are customers most confused about?
- How do competitors display pricing?
- What disclosures are required?

### D. Availability & Status

**Availability States:**

| Status | Meaning | Display | Research Needed |
|--------|---------|---------|-----------------|
| **Available** | Seats available | Book now | ? |
| **Limited** | Few seats left | Urgency indicator | ? |
| **Guaranteed** | Trip will run | Confidence badge | ? |
| **On Request** | Needs confirmation | Contact us | ? |
| **Waitlist** | Full but waitlist available | Join waitlist | ? |
| **Sold Out** | No seats | Notify me | ? |

**Minimum Departure:**

| State | Minimum | Display | Action |
|-------|---------|---------|--------|
| **Not met** | Below min | X more needed | Share to unlock? |
| **Almost met** | Close to min | Last X spots | Urgency |
| **Guaranteed** | Minimum met | Guaranteed departure | Book confidently |

**Research:**
- How do minimums work?
- What happens if trip doesn't run?
- How do we communicate this?

---

## Search UX Flow

**Basic Search Flow:**

```
1. Customer enters:
   - Destination (or "I'm flexible")
   - Dates (or "Flexible +/- 3 days")
   - Travelers
   - Budget (optional)

2. System presents:
   - Matching packages
   - Sorted by relevance/popularity/price
   - Key filters available

3. Customer refines:
   - Apply filters
   - Compare packages
   - View details

4. Customer selects:
   - View package details
   - Check availability
   - Proceed to booking
```

**Flexible Search:**

```
1. Customer enters:
   - "Anywhere in Europe"
   - "June, 2 weeks"
   - Budget range

2. System suggests:
   - Best value options
   - Trending destinations
   - Alternative dates

3. Customer explores:
   - Compare destinations
   - See what's included
   - View departure dates
```

---

## Sort & Ranking

**Sort Options:**

| Option | Algorithm | Research Needed |
|--------|-----------|-----------------|
| **Popularity** | Bookings + ratings | Weighting? |
| **Price: Low to High** | Base price | Include taxes? |
| **Price: High to Low** | Base price | Luxury bias? |
| **Duration** | Shortest to longest | ? |
| **Departure Date** | Soonest first | ? |
| **Rating** | Customer reviews | Minimum reviews? |

**Relevance Scoring:**

| Factor | Weight | Notes |
|--------|--------|-------|
| Exact match | High | Destination, dates |
| Price fit | Medium | Within budget |
| Availability | Medium | Actually bookable |
| Popularity | Low | Social proof |
| Commission | Low | Business priority |

---

## Open Problems

### 1. Package Complexity
**Challenge:** Packages have many components, hard to compare

**Options:**
- Standardize display format
- Key highlights only
- Detailed comparison view
- "Best for" labels

### 2. Price Transparency
**Challenge:** "From" pricing can be misleading

**Options:**
- Show realistic price
- Price calculator
- Breakdown view
- Total price upfront

### 3. Availability Accuracy
**Challenge:** Real-time availability may not be available

**Options:**
- Show "check availability"
- Sync frequently
- Accept some inaccuracy
- Hold seats on search

### 4. Discovery Overload
**Challenge:** Too many packages, hard to choose

**Options:**
- Curated collections
- Editor's picks
- Personalized recommendations
- Guided discovery

---

## Competitor Research Needed

| Competitor | Search UX | Notable Patterns |
|------------|-----------|------------------|
| **MakeMyTrip** | ? | ? |
| **Yatra** | ? | ? |
| **TravelTriangle** | ? | Custom quotes? |
| **TourRadar** | ? | International packages? |

---

## Experiments to Run

1. **Search usability test:** How do customers find packages?
2. **Pricing clarity test:** Do customers understand pricing?
3. **Comparison effectiveness:** Can customers compare packages?
4. **Filter usage:** What filters are most used?

---

## References

- [Package Tours - Providers](./PACKAGE_TOURS_01_PROVIDERS.md) — Product types
- [Trip Builder - Itinerary Assembly](./TRIP_BUILDER_02_ITINERARY_ASSEMBLY.md) — Similar patterns

---

## Next Steps

1. Design search interface
2. Implement filtering logic
3. Build comparison view
4. Test pricing display
5. Measure search effectiveness

---

**Status:** Research Phase — Search patterns unknown

**Last Updated:** 2026-04-27
