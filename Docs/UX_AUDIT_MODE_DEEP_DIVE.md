# Audit Mode: Direct-to-Consumer Wedge Feature

**Date**: 2026-04-13
**Purpose**: Deep dive into the only direct-to-consumer interaction
**Related**: `UX_AND_USER_EXPERIENCE.md`, `Docs/AUDIT_AND_INTELLIGENCE_ENGINE.md`

---

## What is Audit Mode?

**Audit Mode is a lead generation tool** disguised as a value-added service.

Travelers who have self-booked their trips can upload their itinerary and receive:
1. **Wasted spend analysis** - Money spent on things that won't be enjoyed
2. **Suitability scoring** - How well the trip matches their group composition
3. **Value gap detection** - Where they're overpaying vs. what they're getting
4. **Expert recommendations** - Better alternatives from agency-sourced options

**This is the ONLY mode where travelers interact directly with the system.**

Everything else in Agency OS is B2B2C (agent-mediated). Audit Mode is B2C.

---

## Business Rationale

From `HOLISTIC_PROJECT_ASSESSMENT.md`:

> The most compelling feature is "wasted spend detection":
>
> > Universal Studios for 2 adults, 2 elderly, 1 toddler. Cost: full price for 5.
> > Suitability: Adults 100%, Elderly 30%, Toddler 20%. Verdict: 3/5 people are low-utility.
>
> This is brilliant because:
> 1. **It's immediately legible** — anyone can see the problem
> 2. **It proves value instantly** — no long onboarding required
> 3. **It's a lead-gen tool** — "upload your itinerary, see what you're wasting"
> 4. **It's defensible** — OTAs can't do this because they don't know your group composition

### Conversion Funnel

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AWARENESS                                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Traveler sees:                                                                 │
│  • Instagram ad: "Uploaded your booking? See what you're wasting"              │
│  • Google search: "audit my trip booking"                                      │
│  • Friend referral: "This thing showed me I wasted ₹40K"                       │
│  • QR code at travel agency partner                                            │
│                                                                                  │
│  Landing page: audit.agency-os.com (standalone, no login required)              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  UPLOAD                                                                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Traveler uploads:                                                              │
│  • Screenshot of booking confirmation                                          │
│  • Forwarded booking email                                                     │
│  • Pasted booking details                                                      │
│  • Uploaded PDF from OTA                                                       │
│                                                                                  │
│  System extracts:                                                               │
│  • Destination, dates, hotel, activities                                       │
│  • Total cost breakdown                                                         │
│  • Group composition (if detectable)                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ANALYSIS (30-60 seconds)                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  System computes:                                                               │
│  1. Suitability analysis per person/activity                                    │
│  2. Budget efficiency score                                                     │
│  3. Wasted spend calculation                                                    │
│  4. Alternative options from agency inventory                                  │
│  5. Overall fit score                                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RESULTS DISPLAY                                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Traveler sees:                                                                 │
│  • Wasted spend: "₹45,000 (28% of your trip)"                                  │
│  • Suitability scores by person/activity                                       │
│  • Specific problems identified                                                 │
│  • Better alternatives with pricing                                            │
│  • Overall fit score: 62/100                                                   │
│                                                                                  │
│  Call-to-action:                                                                │
│  • "Get agency quote to fix these issues"                                       │
│  • "Chat with expert"                                                           │
│  • "Share results"                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LEAD CAPTURE                                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│  To see full results or get expert help:                                        │
│  • Name (required)                                                              │
│  • Phone (required - for WhatsApp follow-up)                                   │
│  • Email (optional)                                                             │
│  • Current status: "Already booked" vs "About to book"                          │
│                                                                                  │
│  Lead sent to:                                                                  │
│  • Agency CRM (if partner agency)                                               │
│  • Central lead pool (if direct)                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  NURTURE                                                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  If no immediate action:                                                        │
│  • Day 1: WhatsApp message with summary                                         │
│  • Day 3: "Did you have questions about the audit?"                            │
│  • Day 7: "Special offer: We can fix these issues for 10% less than quoted"    │
│  • Day 14: Last call for the season                                            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Landing Page UX

### Hero Section

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  [Logo] Agency OS AUDIT                                                        │
│                                                                                  │
│  ✓ Upload Your Booking                                                           │
│  ✓ See What You're Wasting                                                      │
│  ✓ Get Better Options                                                           │
│                                                                                  │
│  ████████████████████░░░░  78% of travelers overpay for things they won't use   │
│                                                                                  │
│  [START FREE AUDIT]                                                              │
│  No signup required • Results in 60 seconds                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ "This showed me I wasted ₹45K on activities my parents couldn't do!"        ││
│  │                                                     — Meera S., Mumbai     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### How It Works Section

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HOW IT WORKS                                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐              │
│  │ 1. UPLOAD     │  →   │ 2. WE ANALYZE │  →   │ 3. SEE SAVINGS│              │
│  │               │      │               │      │               │              │
│  │ Screenshot or │      │ Suitability,  │      │ Wasted spend, │              │
│  │ forwarded     │      │ value gap,    │      │ better        │              │
│  │ booking email │      │ alternatives  │      │ options       │              │
│  └───────────────┘      └───────────────┘      └───────────────┘              │
│      10 seconds              45 seconds              Instant                      │
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────── │
│  What we check:                                                                  │
│  ✓ Activity suitability for each person (age, mobility, interests)               │
│  ✓ Hotel fit vs. price (location, amenities, room type)                         │
│  ✓ Seasonality (are you paying peak prices for off-peak experiences?)            │
│  ✓ Group composition (is everyone going to enjoy everything?)                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Example Results (Before Upload)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  WHAT YOU'LL SEE                                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ YOUR AUDIT RESULTS                                                           ││
│  │ ───────────────────────────────────────────────────────────────────────────││
│  │                                                                              ││
│  │ 💰 WASTED SPEND: ₹45,000 (28% of your trip)                                 ││
│  │                                                                              ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ Universal Studios Singapore                                           │  ││
│  │ │ Your cost: ₹24,000 for 5 people                                       │  ││
│  │ │ Problem: 3/5 people get low value                                     │  ││
│  │ │   • Adults (2): 100% fit ✓                                            │  ││
│  │ │   • Elderly (1): 30% fit - limited mobility, can't do rides           │  ││
│  │ │   • Toddler (1): 20% fit - too young for most attractions             │  ││
│  │ │                                                                        │  ││
│  │ │ 💡 BETTER: Singapore Zoo + River Wonders (₹12,000)                    │  ││
│  │ │    Everyone enjoys, 50% savings, same duration                        │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                              ││
│  │ 📊 OVERALL FIT SCORE: 62/100                                                ││
│  │                                                                              ││
│  │ Your trip has some great choices but significant optimization potential.      ││
│  │                                                                              ││
│  │ [Get agency quote to optimize] [Chat with expert] [Share results]            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Upload Experience

### Upload Options

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AUDIT YOUR BOOKING                                                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Choose how to share your booking:                                              │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ [📸 Upload Screenshot]                                                      ││
│  │ Take a photo or upload an image of your booking confirmation               ││
│  │ Supported: PNG, JPG, HEIC                                                   ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ [📧 Forward Booking Email]                                                 ││
│  │ Send your booking confirmation to:                                         ││
│  │ audit@agency-os.com                                                         ││
│  │ We'll extract details automatically                                         ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ [✍️ Paste Booking Details]                                                 ││
│  │ Copy-paste from your booking email or confirmation page                    ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ [Paste text here...]                                                   │  ││
│  │ │                                                                        │  ││
│  │ │                                                                        │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────── │
│  What we need from your booking:                                                │
│  • Destination(s)                                                               │
│  • Hotel name and details                                                        │
│  • Activities or attractions booked                                              │
│  • Total cost (breakdown if available)                                           │
│  • Travel dates                                                                  │
│  • Number of people (and ages if kids)                                          │
│                                                                                  │
│  [Cancel] [Start Audit →]                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Processing Screen

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ANALYZING YOUR BOOKING...                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  [Spinner animation]                                                             │
│                                                                                  │
│  Extracting booking details... ✓                                                 │
│  Identifying activities and attractions... ✓                                     │
│  Analyzing group composition...                                                   │
│  Calculating suitability scores...                                               │
│  Checking budget efficiency...                                                   │
│  Finding better alternatives...                                                  │
│                                                                                  │
│  This usually takes 30-60 seconds.                                               │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ DID YOU KNOW?                                                                ││
│  │ Families with young children and elderly travelers waste an average of      ││
│  │ 35% on activities that don't suit everyone.                                 ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## The Results Page

### Full Results Display

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOUR AUDIT RESULTS                                                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Trip: Universal Studios Singapore + Marina Bay Sands, 5 people, 5 nights       │
│  [Share] [Download PDF]                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 💰 WASTED SPEND DETECTED: ₹45,000 (28% of your trip)                        ││
│  │                                                                              ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ Universal Studios Singapore                                           │  ││
│  │ │ Your cost: ₹24,000 for 5 people                                       │  ││
│  │ │ Suitability by person:                                                │  ││
│  │ │                                                                        │  ││
│  │ │  ADULT (35M)  ████████████████████ 100% ✓                             │  ││
│  │ │  ADULT (32F)  ████████████████████ 100% ✓                             │  ││
│  │ │  ELDERLY (68M) ████████░░░░░░░░░░░░  30% ⚠️                            │  ││
│  │ │    → Limited mobility, can't do most rides                             │  ││
│  │ │    → Long queues in heat are difficult                                │  ││
│  │ │  CHILD (8M)   ██░░░░░░░░░░░░░░░░░░░  20% ⚠️                            │  ││
│  │ │    → Too young for thrill rides                                        │  ││
│  │ │    → Height restrictions on most attractions                           │  ││
│  │ │  CHILD (4F)   █░░░░░░░░░░░░░░░░░░░░  10% ⚠️                            │  ││
│  │ │    → Too young for almost everything                                   │  ││
│  │ │    → Stroller access limited in some areas                             │  ││
│  │ │                                                                        │  ││
│  │ │ UTILIZATION SCORE: 52/100 (Less than half of tickets will be used!)    │  ││
│  │ │                                                                        │  ││
│  │ │ 💡 BETTER: Singapore Zoo + River Wonders (₹12,000)                    │  ││
│  │ │    • Everyone enjoys: 95%+ suitability for all ages                    │  ││
│  │ │    • Same duration: Full day activity                                 │  ││
│  │ │    • Savings: ₹12,000 (50% cheaper)                                   │  ││
│  │ │    • Bonus: Night Safari available for adults                         │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🏨 HOTEL ANALYSIS: Marina Bay Sands                                         ││
│  │ Your cost: ₹45,000 for 3 nights                                           ││
│  │                                                                              ││
│  │ SUITABILITY SCORE: 60/100 ⚠️                                                 ││
│  │                                                                              ││
│  │ Issues found:                                                                ││
│  │ • You wanted: "Relaxing family trip"                                       ││
│  │ • MBS reality: Busy, clubby, crowded pool                                 ││
│  │ • Pool requires booking (queues up to 2 hours)                             ││
│  │ • Infinity pool view: ₹15K/night premium you'll rarely enjoy                ││
│  │ • Location: Great for Marina Bay, less convenient for attractions           ││
│  │                                                                              ││
│  │ 💡 BETTER: Shangri-La Singapore (₹28,000)                                  ││
│  │    • Family-friendly pools (no booking needed)                             ││
│  │    • Garden access (quiet, relaxing)                                       ││
│  │    • Savings: ₹17,000 (38% cheaper)                                        ││
│  │    • Better location for Universal Studios/Zoo                             ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📊 OVERALL TRIP SCORE: 62/100                                               ││
│  │                                                                              ││
│  │ Your trip has some solid choices but significant room for improvement.      ││
│  │                                                                              ││
│  │ BREAKDOWN:                                                                   ││
│  │ • Value for money: 55/100 (Overpaying for unsuitable activities)            ││
│  │ • Group fit: 60/100 (Not everyone will enjoy equally)                       ││
│  │ • Location efficiency: 70/100 (Some travel time inefficiencies)              ││
│  │ • Seasonality: 75/100 (Good time to visit, not peak pricing)                ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 💡 WHAT WE COULD IMPROVE                                                    ││
│  │                                                                              ││
│  │ With agency adjustments, you could:                                         ││
│  │ • Save ₹45,000 (28% of current cost)                                        ││
│  │ • Increase suitability from 62% to 90%+                                    ││
│  │ • Add activities everyone enjoys                                           ││
│  │ • Get better room location for your needs                                   ││
│  │                                                                              ││
│  │ AGENCY BENEFITS:                                                             ││
│  │ ✓ Better prices through supplier contracts                                 ││
│  │ ✓ Expert guidance on group composition                                      ││
│  │ ✓ Free changes/cancellation support                                          ││
│  │ ✓ 24/7 emergency support during trip                                        ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  [Get Agency Quote] [Chat with Expert] [Share Results]                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Lead Capture Flow

### Email Capture (Before Full Results)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  YOUR AUDIT IS READY!                                                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  We found ₹45,000 in potential savings!                                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ See your full results and expert recommendations:                           ││
│  │                                                                              ││
│  │ ┌────────────────────────────────────────────────────────────────────────┐  ││
│  │ │ Name                                    [________________]              │  ││
│  │ │                                                                        │  ││
│  │ │ Phone (for WhatsApp follow-up)            [________________]              │  ││
│  │ │                                                                        │  ││
│  │ │ Email (optional)                        [________________]              │  ││
│  │ │                                                                        │  ││
│  │ │ Booking status:                                                         │  ││
│  │ │ ○ Already booked                                                       │  ││
│  │ │ ● About to book (best time to adjust!)                                 │  ││
│  │ │ ○ Still researching                                                    │  ││
│  │ │                                                                        │  ││
│  │ │ [ ] I agree to receive expert recommendations via WhatsApp/email       │  ││
│  │ └────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                              ││
│  │                                    [Show Full Results →]                    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  We'll send your results to WhatsApp for easy reference.                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Implementation

### Extraction Pipeline

```python
# src/services/audit_service.py

class AuditRequest(BaseModel):
    booking_data: str  # Raw text or OCR result
    source_type: str  # "screenshot", "email", "paste", "pdf"

class AuditAnalysis(BaseModel):
    trip_summary: TripSummary
    wasted_spend: List[WastedSpendItem]
    suitability_scores: List[SuitabilityScore]
    alternatives: List[AlternativeOption]
    overall_score: int
    potential_savings: int

def analyze_booking(request: AuditRequest) -> AuditAnalysis:
    """
    Extract booking details and run audit analysis
    """
    # Step 1: Extract structured data
    booking = extract_booking(request.booking_data, request.source_type)

    # Step 2: Analyze each component
    activities = booking.activities
    hotel = booking.hotel
    group = booking.group_composition

    # Step 3: Calculate suitability scores
    suitability_scores = []
    for activity in activities:
        for person in group.people:
            score = calculate_suitability(activity, person)
            suitability_scores.append(score)

    # Step 4: Identify wasted spend
    wasted_items = identify_waste(activities, hotel, group)

    # Step 5: Find alternatives
    alternatives = find_alternatives(booking, suitability_scores)

    # Step 6: Calculate overall score
    overall_score = calculate_overall_score(suitability_scores, wasted_items)

    # Step 7: Calculate potential savings
    potential_savings = sum(item.waste_amount for item in wasted_items)

    return AuditAnalysis(
        trip_summary=booking.summary,
        wasted_spend=wasted_items,
        suitability_scores=suitability_scores,
        alternatives=alternatives,
        overall_score=overall_score,
        potential_savings=potential_savings
    )

def calculate_suitability(activity: Activity, person: Person) -> SuitabilityScore:
    """
    Score 0-100 for how well activity suits person
    """
    score = 100

    # Age-based penalties
    if activity.min_age and person.age < activity.min_age:
        score -= 50
    if activity.max_age and person.age > activity.max_age:
        score -= 30

    # Mobility-based penalties
    if activity.mobility_required == "high" and person.mobility == "low":
        score -= 40

    # Interest alignment
    if activity.categories:
        person_interests = person.interests or []
        matching_interests = set(activity.categories) & set(person_interests)
        if not matching_interests:
            score -= 20
        else:
            score += len(matching_interests) * 5

    return max(0, min(100, score))

def identify_waste(activities, hotel, group) -> List[WastedSpendItem]:
    """
    Identify spending with low utilization
    """
    wasted = []

    for activity in activities:
        total_utility = sum(
            calculate_suitability(activity, person)
            for person in group.people
        )

        avg_utility = total_utility / len(group.people)

        if avg_utility < 50:
            waste_amount = activity.cost * (1 - avg_utility / 100)
            wasted.append(WastedSpendItem(
                item=activity.name,
                cost=activity.cost,
                avg_utility=avg_utility,
                waste_amount=waste_amount,
                reason=f"Only {avg_utility:.0f}% suitability on average"
            ))

    # Check hotel for overpricing
    hotel_fit = calculate_hotel_fit(hotel, group)
    if hotel_fit.score < 60:
        market_rate = get_market_rate(hotel.name, hotel.dates)
        if hotel.price > market_rate * 1.2:
            wasted.append(WastedSpendItem(
                item=hotel.name,
                cost=hotel.price,
                avg_utility=hotel_fit.score,
                waste_amount=hotel.price - market_rate,
                reason=f"Over market rate by {((hotel.price/market_rate - 1) * 100):.0f}%"
            ))

    return wasted
```

### Frontend Components

```typescript
// Components for audit mode landing page

// AuditUpload.tsx
function AuditUpload() {
  const [uploadMethod, setUploadMethod] = useState<"screenshot" | "email" | "paste">();
  const [processing, setProcessing] = useState(false);

  const handleUpload = async (data: any) => {
    setProcessing(true);
    const result = await analyzeBooking(data);
    setProcessing(false);
    navigate("/results", { state: result });
  };

  return (
    <div className="audit-upload">
      <UploadMethodSelector
        selected={uploadMethod}
        onChange={setUploadMethod}
      />

      {uploadMethod === "screenshot" && <ScreenshotUpload onUpload={handleUpload} />}
      {uploadMethod === "email" && <EmailInstructions />}
      {uploadMethod === "paste" && <TextInput onSubmit={handleUpload} />}

      {processing && <ProcessingScreen />}
    </div>
  );
}

// AuditResults.tsx
function AuditResults() {
  const { analysis } = useLocation();
  const [showLeadCapture, setShowLeadCapture] = useState(true);

  return (
    <div className="audit-results">
      <WastedSpendCard wasted={analysis.wasted_spend} />
      <SuitabilityBreakdown scores={analysis.suitability_scores} />
      <HotelAnalysis hotel={analysis.hotel_analysis} />
      <AlternativesList alternatives={analysis.alternatives} />
      <OverallScore score={analysis.overall_score} />

      {showLeadCapture && (
        <LeadCaptureModal
          onClose={() => setShowLeadCapture(false)}
          analysis={analysis}
        />
      )}
    </div>
  );
}
```

---

## Conversion Optimization

### A/B Test Ideas

| Element | Variant A | Variant B | Metric |
|---------|-----------|-----------|--------|
| Hero CTA | "Upload Booking" | "See What You're Wasting" | Click-through |
| Results timing | Show immediately | Capture lead first | Lead quality |
| Savings format | "₹45,000" | "₹45,000 (28%)" | Comprehension |
| Alternatives | Show 1 alternative | Show 3 alternatives | Engagement |
| CTA placement | Top only | Top + bottom | Conversion |

### Key Metrics

| Metric | Target | Why |
|--------|--------|-----|
| Upload completion rate | > 60% | Easy upload process |
| Analysis time | < 60 seconds | Don't lose people |
| Lead capture rate | > 40% | Balance value vs. gating |
| CTR to "Get Quote" | > 15% | Main conversion goal |
| Share rate | > 10% | Viral coefficient |
| Return visits | > 20% | Nurture effectiveness |

---

## Privacy & Trust

### What We Do With Data

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PRIVACY COMMITMENT                                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ✓ Your booking data is processed securely and deleted after 30 days            │
│  ✓ We never share your details with third parties                               │
│  ✓ Results are stored only if you choose to save them                          │
│  ✓ You can request deletion at any time                                        │
│  ✓ We use data only to:                                                         │
│    • Generate your audit results                                                │
│    • Send expert recommendations (if you opt in)                                │
│    • Improve our analysis (anonymized data only)                                │
│                                                                                  │
│  Questions? privacy@agency-os.com                                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Future Enhancements

### Phase 2 Features

1. **Flight Analysis** - Audit flight bookings for routing, timing, price
2. **Multi-Destination Trips** - Handle complex itineraries
3. **Real-Time Pricing** - Live price comparison vs. OTA
4. **Social Proof** - "523 people audited Singapore trips this week"
5. **Video Explanation** - Short video walking through results
6. **Book Now Integration** - One-click to booking with partner agencies

### Phase 3 Features

1. **Historical Audit** - "I went to Bali last year, how did I do?"
2. **Planning Mode** - "I'm planning a trip, audit my proposed itinerary"
3. **Group Collaboration** - Share audit with fellow travelers for input
4. **Multi-Channel Upload** - WhatsApp, Instagram DM, in-person scan

---

## Related Documentation

- `Docs/AUDIT_AND_INTELLIGENCE_ENGINE.md` - Original spec for audit mode
- `UX_AND_USER_EXPERIENCE.md` - Overall UX context
- `UX_MESSAGE_TEMPLATES_AND_FLOWS.md` - Nurture messaging for audit leads
- `UX_TECHNICAL_ARCHITECTURE.md` - How to build the audit pipeline

---

*Audit Mode is the wedge feature - the fastest path to proving value and acquiring leads. It should be built before the full agent dashboard.*
