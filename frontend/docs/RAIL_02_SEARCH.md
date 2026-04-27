# Rail Integration 02: Search & Pricing

> Finding trains, checking availability, and comparing options

---

## Document Overview

**Focus:** How customers search and compare rail options
**Status:** Research Exploration
**Last Updated:** 2026-04-27

---

## Key Questions to Answer

### 1. Search Parameters
- What are the primary search filters? (Origin, destination, date?)
- How does rail search differ from flight search?
- What about flexible dates?
- How do we handle multiple train types?

### 2. Availability Display
- How do we show seat availability?
- What about waitlist positions?
- How do we display RAC status?
- What about quota availability?

### 3. Pricing Display
- How do we show dynamic pricing?
- What about different classes?
- How do we handle Tatkal pricing?
- What about rail pass pricing?

### 4. Comparison
- How do customers compare train options?
- What are the key differentiators?
- How do we show duration vs. price tradeoffs?

---

## Research Areas

### A. Search Parameters

**Primary Search Inputs:**

| Parameter | Type | Required? | Research Needed |
|-----------|------|-----------|-----------------|
| **Origin** | Station/city | Yes | Autocomplete? |
| **Destination** | Station/city | Yes | Route validation? |
| **Date** | Date | Yes | Flexible options? |
| **Class** | Select | Optional | Default? |
| **Quota** | Select | Optional | Default to general? |

**Advanced Filters (Indian Railways):**

| Filter | Type | Research Needed |
|--------|------|-----------------|
| **Train type** | Select | Express, Superfast, Rajdhani? |
| **Departure time** | Range | Morning, afternoon, evening? |
| **Arrival time** | Range | Preferences? |
| **Available only** | Boolean | Exclude WL? |
| **Quota type** | Select | General, Tatkal, Ladies? |

**Advanced Filters (International):**

| Filter | Type | Research Needed |
|--------|------|-----------------|
| **Train type** | Select | High-speed, regional? |
| **Stops** | Max number | Direct vs. with changes? |
| **Duration** | Max hours | ? |
| **Price** | Range | ? |
| **Amenities** | Multi-select | WiFi, food, power? |

**Search Patterns:**

| Pattern | Description | Research Needed |
|----------|-------------|-----------------|
| **Point-to-point** | Direct train search | Most common? |
| **Multi-city** | Multiple segments | Complex routing? |
| **Pass-based** | Using rail pass | Different search? |
| **Flexible date** | Find cheapest/best | Price variation? |

### B. Availability Display

**Indian Railways Status Codes:**

| Code | Meaning | Display | Color | Research Needed |
|------|---------|---------|-------|-----------------|
| **CNF** | Confirmed | "Confirmed" | Green | ? |
| **RAC** | Reservation Against Cumulative | "RAC - Seat confirmed" | Yellow | Show number? |
| **WL** | Waitlist | "WL 23/WL 45" | Red | Show current/limit? |
| **REGRET** | No seats | "Waitlist Full" | Grey | ? |
| **AVAILABLE** | Seats available | "45 Available" | Green | Exact number? |

**Availability by Class:**

| Class | Typical Availability | Research Needed |
|-------|---------------------|-----------------|
| **1A** | Limited, fills fast | ? |
| **2A** | Good availability | ? |
| **3A** | Good availability | ? |
| **CC** | Good for day trains | ? |
| **SL** | Good, but can fill | ? |

**International Availability:**

| Status | Meaning | Display | Research Needed |
|--------|---------|---------|-----------------|
| **Available** | Seats for booking | "Book now" | ? |
| **Limited** | Few seats left | "3 left" | ? |
| **Sold Out** | No seats | "Sold out" | Waitlist? |

**RAC Considerations:**

| Aspect | Details | Customer Communication | Research Needed |
|--------|---------|------------------------|-----------------|
| **Meaning** | Seat guaranteed, berth not | "You have a seat, berth may be assigned" | ? |
| **Confirmation chance** | High, especially near departure | Show probability? | ? |
| **Boarding** | Can board with RAC ticket | Explain process | ? |

### C. Pricing Display

**Indian Railways Pricing:**

| Component | Description | Display | Research Needed |
|-----------|-------------|---------|-----------------|
| **Base fare** | Distance-based | Show | ? |
| **Reservation fee** | Per passenger | Show | ? |
| **Superfast charge** | For superfast trains | Show | ? |
| **Service tax** | Government tax | Show | ? |
| **Catering** | For Rajdhani/Duronto | Included | ? |

**Dynamic Pricing (Premium Tatkal):**

| Scenario | Pricing | Display | Research Needed |
|----------|----------|---------|-----------------|
| **General quota** | Fixed | Show total | ? |
| **Tatkal** | Fixed + charges | Show Tatkal price | ? |
| **Premium Tatkal** | Dynamic | Show "from" | ? |

**Class Pricing Comparison:**

| Route | 1A | 2A | 3A | SL | Research Needed |
|-------|-----|-----|-----|-----|-----------------|
| **Delhi-Mumbai** | ~2x 2A | Base | ~0.6x 2A | ~0.4x 2A | ? |
| **Chennai-Bangalore** | ? | ? | ? | ? | Actual ratios? |

**International Pricing:**

| Factor | Impact | Research Needed |
|--------|--------|-----------------|
| **Advance purchase** | Cheaper earlier | How much? |
| **Time of day** | Peak vs. off-peak | Price difference? |
| **Class** | First vs. standard | Multiple? |
| **Reservation** | Optional vs. mandatory | Additional cost? |

**Rail Pass Pricing:**

| Pass Type | Duration | Adult Price | Youth/Senior | Research Needed |
|-----------|----------|-------------|--------------|-----------------|
| **Eurail Global** | 15 days | ? | ? | ? |
| **Eurail Global** | 1 month | ? | ? | ? |
| **JR Pass** | 7 days | ? | ? | ? |
| **BritRail** | 8 days | ? | ? | ? |

### D. Train Comparison

**Comparison Factors:**

| Factor | Importance | Display | Research Needed |
|--------|------------|---------|-----------------|
| **Duration** | High | Show hours | ? |
| **Departure time** | High | Show time | ? |
| **Arrival time** | High | Show time | ? |
| **Price** | High | Show by class | ? |
| **Availability** | Critical | Show status | ? |
| **Train type** | Medium | Express/Passenger | ? |
| **Amenities** | Medium | WiFi, food | ? |

**Sorting Options:**

| Option | Algorithm | Research Needed |
|--------|-----------|-----------------|
| **Departure time** | Earliest first | Most popular? |
| **Duration** | Fastest first | ? |
| **Price** | Lowest first | By class? |
| **Arrival time** | Earliest first | ? |
| **Popularity** | Most booked | ? |

---

## Search UX Flow

**Basic Search Flow (Indian Railways):**

```
1. Customer enters:
   - From station (or city)
   - To station (or city)
   - Date of journey
   - Class preference (optional)
   - Quota type (optional, default General)

2. System presents:
   - Available trains
   - Sort by departure time
   - Show availability by class
   - Show pricing

3. Customer refines:
   - Filter by train type
   - Filter by departure time
   - Filter by availability status

4. Customer selects:
   - View train details
   - Check availability for class
   - Proceed to booking
```

**Tatkal Search Flow:**

```
1. Customer selects Tatkal quota
   - Only shows trains with Tatkal quota
   - Shows Premium Tatkal pricing (dynamic)
   - Warning about high demand

2. System presents:
   - Tatkal availability
   - Dynamic pricing (Premium Tatkal)
   - Booking window timing

3. Customer acts quickly:
   - Tatkal seats sell fast
   - Auto-refresh availability
   - Quick booking flow
```

**Rail Pass Search Flow:**

```
1. Customer enters:
   - Countries to visit
   - Duration of travel
   - Number of travel days
   - Class preference

2. System presents:
   - Matching rail passes
   - Pricing by age
   - Coverage details
   - Reservation requirements

3. Customer compares:
   - Pass types (Global vs. Select vs. One Country)
   - Duration options
   - Pricing

4. Customer selects:
   - View pass details
   - Add to cart
   - Checkout for voucher
```

---

## Open Problems

### 1. Station Name Ambiguity
**Challenge:** Multiple stations in a city

**Options:**
- Show all stations with distance
- Ask for specific station
- Default to main station
- Show map

### 2. Waitlist Transparency
**Challenge:** Customers don't understand waitlist probabilities

**Options:**
- Show historical confirmation rate
- Show current position vs. limit
- Suggest alternatives
- Clear explanations

### 3. Dynamic Pricing Display
**Challenge:** Premium Tatkal prices change constantly

**Options:**
- Show "from" pricing
- Real-time updates
- Price range indication
- Explain pricing model

### 4. Cross-Border Routing
**Challenge:** Best route may involve multiple operators

**Options:**
- Show single-operator options first
- Show multi-operator with warnings
- Calculate total price
- Show connection times

---

## Competitor Research Needed

| Competitor | Search UX | Availability Display | Notable Patterns |
|------------|-----------|---------------------|------------------|
| **IRCTC** | ? | ? | ? |
| **MakeMyTrip** | ? | ? | ? |
| **Trainline** | ? | ? | ? |
| **Omio** | ? | ? | ? |

---

## Experiments to Run

1. **Search usability test:** How do customers find trains?
2. **Waitlist perception test:** Do customers understand WL?
3. **Pricing clarity test:** Do customers understand total price?
4. **Station selection test:** How do customers choose stations?

---

## References

- [Rail - Providers](./RAIL_01_PROVIDERS.md) — Quota and class types
- [Flight Integration - Search](./FLIGHT_INTEGRATION_02_SEARCH.md) — Similar search patterns

---

## Next Steps

1. Design search interface
2. Implement filtering logic
3. Build availability display
4. Create comparison view
5. Test pricing transparency

---

**Status:** Research Phase — Search patterns unknown

**Last Updated:** 2026-04-27
