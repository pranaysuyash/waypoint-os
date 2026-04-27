# Cruise Booking 02: Search & Discovery

> Finding cruises, selecting cabins, and comparing options

---

## Document Overview

**Focus:** How customers discover and compare cruise options
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Search Parameters
- What are the primary search filters? (Destination, dates, ship?)
- How do customers search differently for cruises vs. other travel?
- What about flexible dates?
- How do we handle cabin preferences?

### 2. Display & Comparison
- How do we present cruises? (Cards, lists, detail view?)
- What information is most important?
- How do we compare ships and itineraries?
- What about deck plans and cabin locations?

### 3. Pricing Display
- How do we show cruise pricing?
- What about per-person vs. total pricing?
- How do we handle price components?
- What about included vs. extra costs?

### 4. Availability
- How do we show availability status?
- What about waitlists?
- How do we handle cabin availability by category?

---

## Research Areas

### A. Search Parameters

**Primary Search Inputs:**

| Parameter | Type | Required? | Research Needed |
|-----------|------|-----------|-----------------|
| **Destination** | Select/region | Yes | How structured? |
| **Departure Date** | Date/range | Yes | Flexible? |
| **Duration** | Range | Optional | Popular ranges? |
| **Cruise Line** | Multi-select | Optional | Popular for Indians? |
| **Ship** | Select | Optional | For enthusiasts? |
| **Departure Port** | Multi-select | Optional | Indian ports? |
| **Cabin Type** | Select | Optional | Preference? |

**Advanced Filters:**

| Filter | Type | Research Needed |
|--------|------|-----------------|
| **Price Range** | Range | Popular price points? |
| **Ship Size** | Select | Preference? |
| **Service Class** | Select | Mass/premium/luxury? |
| **Passengers** | Number | Affects pricing? |
| **Kids/Family** | Boolean | Family-friendly? |
| **Accessible** | Boolean | Accessibility needs? |
| **Solo Friendly** | Boolean | Single cabins? |
| **Dining Style** | Select | Traditional/flexible? |

**Search Patterns:**

| Pattern | Description | Research Needed |
|----------|-------------|-----------------|
| **Destination-based** | "Alaska cruise" | Most common? |
| **Date-based** | "Cruises in December" | Flexible travelers? |
| **Deal-based** | "Cruise under $500" | Bargain hunters? |
| **Ship-based** | "Specific ship/line" | Enthusiasts? |
| **Event-based** | "Christmas markets cruise" | Theme cruises? |

### B. Cruise Display

**Card Information Priority:**

| Element | Priority | Display Notes | Research Needed |
|---------|----------|---------------|-----------------|
| **Ship Name** | High | Primary identifier | Photo important |
| **Itinerary Name** | High | Descriptive title | ? |
| **Destination** | High | Region/ports | Map? |
| **Duration** | High | Nights | Include embarkation? |
| **Price** | High | From price per person | Clarity critical |
| **Departure Date** | High | Next available | Multiple dates? |
| **Departure Port** | Medium | Embarkation city | Flight needed? |
| **Cruise Line** | Medium | Brand recognition | Logo? |
| **Ship Photo** | High | Visual appeal | Required? |
| **Ports of Call** | Medium | Key destinations | Count? |
| **Ship Rating** | Medium | Customer rating | Minimum reviews? |

**Detail View Information:**

| Section | Content | Priority | Research Needed |
|---------|---------|----------|-----------------|
| **Overview** | Ship, itinerary, dates | High | ? |
| **Itinerary Map** | Visual route | High | Interactive? |
| **Ports of Call** | Details, timing, excursions | High | ? |
| **Ship Info** | Amenities, dining, entertainment | High | ? |
| **Cabin Options** | Categories, pricing, availability | High | ? |
| **Pricing** | Breakdown by cabin type | High | Transparency |
| **Reviews** | Customer feedback | Medium | ? |
| **Deck Plans** | Cabin locations | Medium | Interactive? |

### C. Cabin Selection

**Cabin Display Challenges:**

| Challenge | Description | Potential Solution | Research Needed |
|-----------|-------------|---------------------|-----------------|
| **Category complexity** | Many similar categories | Group by type | ? |
| **Location matters** | Same category, different decks | Color-coded pricing | ? |
| **View variations** | Obstructed vs. clear views | Clear labeling | ? |
| **Availability sync** | Real-time changes | Live status or hold | ? |

**Deck Plan Presentation:**

| Method | Description | Pros | Cons | Research Needed |
|--------|-------------|------|------|-----------------|
| **Interactive deck map** | Click to select cabin | Visual, intuitive | Complex to build | ? |
| **Cabin list** | List with details | Simple, clear | Less visual | ? |
| **Category selection** | Select type, assign best | Easy | Can't choose location | ? |
| **Agent-assisted** | Agent picks for customer | Personalized | Higher cost | ? |

**Cabin Comparison:**

| Attribute | Display | Research Needed |
|-----------|---------|-----------------|
| Category | Interior/OV/Balcony/Suite | ? |
| Deck | Deck number | ? |
| Position | Forward/mid/aft | ? |
| Size | Square feet | ? |
| Occupancy | Max passengers | ? |
| View type | Description | ? |
| Price difference | +/- from base | ? |
| Amenities | Special features | ? |

### D. Pricing Display

**Pricing Complexity:**

| Pricing Component | Description | Display Challenge | Research Needed |
|-------------------|-------------|-------------------|-----------------|
| **Fare** | Base cruise fare | Varies by cabin | Clear baseline |
| **Taxes & Fees** | Port charges, taxes | Significant addition | Breakdown? |
| **Gratuities** | Tips for crew | Often extra | Daily amount? |
| **Specialty Dining** | Extra-cost restaurants | Optional | Show options? |
| **Excursions** | Shore activities | Optional | Average cost? |
| **Beverage Package** | Drinks | Optional | Show options? |
| **Wi-Fi** | Internet access | Often extra | Daily cost? |
| **Flight to Port** | Not included | Major hidden cost | Estimate? |

**Price Display Options:**

| Display Type | Description | Pros | Cons | Research Needed |
|--------------|-------------|------|------|-----------------|
| **Per person, from** | Lowest price per person | Looks attractive | Misleading | ? |
| **Per person, realistic** | Common cabin price | More accurate | Still partial | ? |
| **Total price** | All-in for cabin | Transparent | Sticker shock | ? |
| **Price calculator** | Add components as selected | Accurate | Complex | ? |

**Included vs. Extra:**

| Item | Usually Included | Often Extra | Research Needed |
|------|------------------|-------------|-----------------|
| Meals | Main dining | Specialty | ? |
| Activities | Most | Spa, some excursions | ? |
| Entertainment | Shows | Reserved seating | ? |
| Drinks | Water, coffee | Alcohol, soda | ? |
| Wi-Fi | Rarely | Usually extra | ? |
| Fitness | Gym | Classes | ? |
| Kids Club | Yes | After-hours | ? |

---

## Search UX Flow

**Basic Search Flow:**

```
1. Customer enters:
   - Destination (or "I'm flexible")
   - Departure month or dates
   - Duration preference
   - Number of passengers

2. System presents:
   - Matching cruises
   - Sorted by relevance/popularity/price
   - Key filters available

3. Customer refines:
   - Apply filters (line, ship, cabin type)
   - Compare options
   - View details

4. Customer selects:
   - View cruise details
   - View itinerary
   - Select cabin category
   - Proceed to booking
```

**Cabin Selection Flow:**

```
1. Customer views cabin categories:
   - Interior, Ocean View, Balcony, Suite
   - Prices shown

2. Customer selects category:
   - View available cabins
   - See deck plan
   - Compare locations

3. Customer chooses cabin:
   - View specific cabin details
   - See exact location
   - Proceed to booking
```

---

## Sort & Ranking

**Sort Options:**

| Option | Algorithm | Research Needed |
|--------|-----------|-----------------|
| **Popularity** | Bookings + ratings | Weighting? |
| **Price: Low to High** | Lowest cabin price | Include taxes? |
| **Price: High to Low** | Highest cabin price | Luxury bias? |
| **Duration** | Shortest to longest | ? |
| **Departure Date** | Soonest first | ? |
| **Ship Size** | Smallest to largest | Preference? |
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

### 1. Cabin Complexity
**Challenge:** Too many cabin options, hard to choose

**Options:**
- Simplify to main categories
- Recommend based on preferences
- Show "best value" cabin
- Agent assistance

### 2. Price Transparency
**Challenge:** Advertised price not reflective of total cost

**Options:**
- Show "total with taxes"
- Price calculator with all options
- Display "average passenger spends"
- Clear disclosure

### 3. Deck Plan Usability
**Challenge:** Deck plans are complex, hard to understand

**Options:**
- Interactive, zoomable maps
- Color-code by availability
- Highlight selected cabin
- Simplified views

### 4. Itinerary Understanding
**Challenge:** Customers don't know ports of call

**Options:**
- Rich port descriptions
- Photos and videos
- Shore excursion previews
- Day-by-day breakdown

---

## Competitor Research Needed

| Competitor | Search UX | Cabin Selection | Notable Patterns |
|------------|-----------|-----------------|------------------|
| **Expedia Cruises** | ? | ? | ? |
| **CruiseDirect** | ? | ? | ? |
| **CruiseLineDirect** | ? | ? | ? |

---

## Experiments to Run

1. **Search usability test:** How do customers find cruises?
2. **Cabin selection test:** Can customers choose cabins confidently?
3. **Pricing clarity test:** Do customers understand total cost?
4. **Deck plan usability:** Can customers find cabins on deck plans?

---

## References

- [Cruise - Providers](./CRUISE_01_PROVIDERS.md) — Ship and cabin types
- [Package Tours - Search](./PACKAGE_TOURS_02_SEARCH.md) — Similar search patterns

---

## Next Steps

1. Design search interface
2. Implement filtering logic
3. Build cabin selection UX
4. Create deck plan visualization
5. Test pricing transparency

---

**Status:** Research Phase — Search patterns unknown

**Last Updated:** 2026-04-27
