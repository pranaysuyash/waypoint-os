# Detailed User Flows: Screen by Screen

**Date**: 2026-04-14
**Purpose**: Every screen, every interaction, for every persona

---

## Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  USER FLOW MAP                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────┐                                                              │
│  │  LANDING PAGE  │ ──▶ Sign Up / Login                                        │
│  └────────────────┘                                                              │
│           │                                                                       │
│           ▼                                                                       │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐                │
│  │  ONBOARDING    │ ──▶  DASHBOARD      │ ──▶ NEW TRIP       │                │
│  └────────────────┘    └────────────────┘    └────────────────┘                │
│           │                    │                      │                         │
│           ▼                    ▼                      ▼                         │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐                │
│  │ FIRST SUCCESS  │    │  TRIP LIST     │    │  INTAKE        │                │
│  └────────────────┘    └────────────────┘    └────────────────┘                │
│                                                      │                         │
│                        ┌────────────────────────────┼─────────────────┐         │
│                        ▼                            ▼                 ▼         │
│                 ┌─────────────┐           ┌─────────────┐   ┌─────────────┐  │
│                 │  REVIEW     │           │  OPTIONS    │   │  ASK        │  │
│                 │  BRIEF      │           │  GENERATED │   │  FOLLOWUP   │  │
│                 └─────────────┘           └─────────────┘   └─────────────┘  │
│                        │                            │                             │
│                        ▼                            ▼                             │
│                 ┌─────────────┐           ┌─────────────┐                      │
│                 │  EDIT       │           │  PRESENT    │                      │
│                 │  OPTIONS    │           │  TO CLIENT  │                      │
│                 └─────────────┘           └─────────────┘                      │
│                                                                                  │
│  ADMIN FLOWS (Agency Owner)                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                          │
│  │ TEAM VIEW   │ │  ANALYTICS   │ │  SETTINGS   │                          │
│  └─────────────┘   └─────────────┘   └─────────────┘                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Flow 1: New User Onboarding

### Screen 1: Landing Page

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Agency OS                                                                      │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ╔════════════════════════════════════════════════════════════════════════════╗│
│  ║                                                                            ║│
│  ║    The AI Assistant for Travel Agents                                       ║│
│  ║                                                                            ║│
│  ║    Turn messy client messages into organized trip options —                 ║│
│  ║    in minutes, not hours.                                                    ║│
│  ║                                                                            ║│
│  ║    [Watch 2-min demo]                                                         ║│
│  ║                                                                            ║│
│  ╚════════════════════════════════════════════════════════════════════════════╝│
│                                                                                  │
│  ✅ Extract intent from freeform messages                                        │
│  ✅ Flag contradictions and blockers                                            │
│  ✅ Generate 2-3 ranked options with rationale                                  │
│  ✅ Learn your agency's preferences over time                                    │
│                                                                                  │
│  [Get Started Free]   [See How It Works]                                        │
│                                                                                  │
│  Trusted by 200+ travel agencies                                                │
│  [Testimonial carousel]                                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Elements**:
- Clear value prop (AI assistant for agents)
- Social proof (testimonials, agency count)
- Single CTA (reduce friction)
- Demo video for curious visitors

---

### Screen 2: Sign Up

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Create your agency workspace                                                    │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Agency Name*                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Priya Travels                                                              │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Your Name*                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Priya Sharma                                                               │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Email*                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ priya@priyatravels.com                                                      │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Password*                                                                       │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ ••••••••                                                                    │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [ ] I agree to the [Terms] and [Privacy Policy]                                │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                              Create Account                                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Or continue with [Google]  [Microsoft]                                         │
│                                                                                  │
│  Already have an account? [Sign in]                                             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Elements**:
- Minimal fields (reduce friction)
- Social login option
- Clear link to terms/privacy

---

### Screen 3: Welcome / Choose Your Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Welcome to Agency OS, Priya! 🎉                                               │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Let's get you set up. What describes you best?                                  │
│                                                                                  │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐│
│  │                                     │  │                                     ││
│  │  📱 I have a trip to work on NOW   │  │  🎓 I want to see how it works     ││
│  │                                     │  │                                     ││
│  │  Jump right in with a real trip    │  │  Show me an example trip first      ││
│  │                                     │  │                                     ││
│  │              [Start Here]           │  │              [Show Example]         ││
│  │                                     │  │                                     ││
│  └─────────────────────────────────────┘  └─────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────┐                                        │
│  │                                     │                                        │
│  │  📤 I have past trips to upload    │                                        │
│  │                                     │                                        │
│  │  See how Agency OS handles your     │                                        │
│  │  real historical data               │                                        │
│  │                                     │                                        │
│  │              [Upload]               │                                        │
│  │                                     │                                        │
│  └─────────────────────────────────────┘                                        │
│                                                                                  │
│  You can change this anytime.                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Design principle**: Meet users where they are — some have urgent work, some want to learn first.

---

### Screen 4: Quick Setup (Skippable)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Quick setup (takes 1 minute) — [Skip for now]                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  What's your primary market?                                                     │
│  ○ Domestic (India)                                                              │
│  ○ International (outbound from India)                                           │
│  ● Both                                                                         │
│                                                                                  │
│  What's your typical trip budget range?                                         │
│  ○ Budget (₹50K - ₹1L per person)                                                │
│  ● Mid-range (₹1L - ₹3L per person)                                             │
│  ○ Premium (₹3L+ per person)                                                    │
│                                                                                  │
│  Any destinations you specialize in? (optional)                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Europe, Southeast Asia                                                      │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  This helps us give better suggestions. You can change this in Settings.        │
│                                                                                  │
│  [Continue]                                                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Flow 2: New Trip (The Core Flow)

### Screen 1: Dashboard (Starting Point)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Agency OS    🔔           [Priya Sharma ▼]        [⚙️]                        │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │              │  │              │  │              │  │              │       │
│  │    12        │  │     47       │  │    18 min    │  │     4.8★     │       │
│  │  Active      │  │  Trips this  │  │  Avg time    │  │  Satisfaction │       │
│  │  trips       │  │  month       │  │  to options  │  │              │       │
│  │              │  │              │  │              │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ [+ New Trip]                                     [Search trips...]         │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ACTIVE TRIPS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ Sharma Family Europe  │ New  │ Just now  │ [→ Continue]                   ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ Mehta Family Thailand │ Intake sent │ 2 hours ago │ [→ Continue]           ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ Patel Honeymoon    │ Options sent │ Yesterday │ [→ Continue]              ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ Gupta Family Dubai │ Booked │ 3 days ago │ [→ View]                       ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  [View all trips]                                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 2: New Trip — Intake

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                            [Save as Draft]                 │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  New Trip: Intake                                                                │
│  ─────────────────────                                                           │
│                                                                                  │
│  Trip Name*                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Sharma Family Europe                                                        │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Client Name*                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ Raj Sharma                                                                 │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Client Contact*                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │ raj.sharma@email.com  │ WhatsApp: +91 98765 43210                         │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  How is the client reaching you?                                                 │
│  ● WhatsApp message  ○ Email  ○ Phone call  ○ In-person                        │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Paste their message here (or type a summary):                                   │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │ Hi Priya, we want to go to Europe sometime in June maybe? Family of 4,    │ │
│  │ kids are 7 and 10. Not sure about budget yet, maybe around 3-4 lakhs?    │ │
│  │ We like beaches but also culture. Can you suggest something?              │ │
│  │                                                                            │ │
│  │                                                                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  📎 [Attach screenshot]  [Add another message]                                  │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  [Clear & Start Over]                                                            │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Process with AI →                                │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key elements**:
- Client info for tracking
- Source channel (for learning)
- Freeform text input (no structured form — the AI handles it)
- Attachment option for screenshots

---

### Screen 3: Processing State

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                  │
│                                                                                  │
│                                                                                  │
│              ╔═══════════════════════════════════════════╗                        │
│              ║                                         ║                        │
│              ║         ✨ Understanding intent...       ║                        │
│              ║                                         ║                        │
│              ╚═══════════════════════════════════════════╝                        │
│                                                                                  │
│                                                                                  │
│            Analyzing message...                                                  │
│            Extracting constraints...                                             │
│            Checking feasibility...                                               │
│            Preparing questions...                                                │
│                                                                                  │
│                                                                                  │
│              This takes about 30 seconds                                         │
│                                                                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Design note**: Show progress so user knows something is happening. Don't just show a spinner.

---

### Screen 4: Intake Review — The Core Screen

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back                              [Save]                    [Generate Options]  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ✅ Intent Extracted                                                             │
│  ───────────────────                                                           │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ DETECTED:                                                                    ││
│  │                                                                             ││
│  │ 📍 Destination: Europe (multiple countries possible)                        ││
│  │ 📅 Dates: June 2025 (flexible, specific dates TBD)                          ││
│  │ 👥 Travelers: 2 adults, 2 children (ages 7, 10)                             ││
│  │ 💰 Budget: ₹3-4L (₹75K-100K/person)                                          ││
│  │ 🎯 Preferences: Beaches + culture, family-friendly                           ││
│  │                                                                             ││
│  │ ⚠️ CONFIDENCE: Medium (needs clarification)                                  ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ⚠️ Questions to Ask Client                                                      │
│  ───────────────────────────                                                     │
│                                                                                  │
│  Before generating options, we recommend asking:                                 │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 1. 📅 Specific dates in June? (School holidays impact pricing)              ││
│  │                                                                             ││
│  │ 2. 🌍 Any countries definitely in or out?                                  ││
│  │                                                                             ││
│  │ 3. ⚖️ Beach vs. culture balance preference? (50-50? 70-30?)                ││
│  │                                                                             ││
│  │ 4. 🚗 Any mobility constraints? (Kids' walking ability, elderly?)          ││
│  │                                                                             ││
│  │ 5. 🎪 Anything you definitely want to do or avoid?                         ││
│  │                                                                             ││
│  │ [Copy all questions]  [Customize before sending]                            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ✅ Feasibility: POSSIBLE (with clarification)                                   │
│  🔴 Blockers: None                                                               │
│  🟡 Considerations: June is peak season — ₹4L may be tight for 4 people         │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  [Generate Anyway]  [Send Questions to Client]  [I'll Update Myself]            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**This is the KEY screen** — where the value is obvious. Clear, organized, actionable.

---

### Screen 5: Questions Sent (Waiting State)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                                            │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ⏳ Waiting for Client Response                                                  │
│  ─────────────────────────────                                                   │
│                                                                                  │
│  Trip: Sharma Family Europe                                                      │
│  Client: Raj Sharma                                                              │
│                                                                                  │
│  Questions sent: 2 hours ago                                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ What we asked:                                                              ││
│  │                                                                             ││
│  │ • Specific dates in June?                                                  ││
│  │ • Any countries in/out?                                                     ││
│  │ • Beach vs. culture preference?                                             ││
│  │ • Mobility constraints?                                                    ││
│  │ • Definite must-haves or avoid?                                            ││
│  │                                                                             ││
│  │ [View sent message]                                                         ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Client replied via WhatsApp? Paste their response here:                        │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                                                                            │ │
│  │ [Paste response here...]                                                    │ │
│  │                                                                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  [Update Brief]  [Generate with Current Info]                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 6: Updated Brief

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back                              [Save]                    [Generate Options]  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ✅ Brief Updated                                                                │
│  ───────────────────                                                           │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ CONFIRMED:                                                                   ││
│  │                                                                             ││
│  │ 📍 Destination: France + Italy                                               ││
│  │ 📅 Dates: June 15-25, 2025                                                   ││
│  │ 👥 Travelers: 2 adults, 2 children (ages 7, 10)                             ││
│  │ 💰 Budget: ₹4L (₹100K/person)                                                ││
│  │ 🎯 Preferences: 60% culture, 40% beach, moderate pace                        ││
│  │ 🚫 Avoid: Too much walking, very early starts                                ││
│  │                                                                             ││
│  │ ⚠️ CONFIDENCE: High                                                          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  🟡 Flagged Considerations                                                       │
│  ───────────────────────────                                                     │
│                                                                                  │
│  ⚠️ June is peak season in Europe — expect premium pricing                       │
│  💡 ₹4L budget may be tight for France+Italy — consider Greece or Spain for bet. │
│  ⚠️ Kids ages 7-10: Limit museums to 1-2 hours/day                               │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ✅ Feasibility: FEASIBLE (with recommendations)                                  │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Generate Options →                                │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 7: Options Generated

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back                    [Edit]    [Download PDF]         [Present to Client] │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Trip Options: Sharma Family Europe                                              │
│  ─────────────────────────────────────                                           │
│                                                                                  │
│  ╔════════════════════════════════════════════════════════════════════════════╗│
│  ║                              OPTION 1: FRANCE FOCUS                         ║│
│  ╠════════════════════════════════════════════════════════════════════════════╣│
│  ║                                                                            ║│
│  ║  ⭐ WHY THIS FITS YOUR CLIENT                                              ║│
│  ║  • Classic Europe intro, perfect for first-timers                         ║│
│  ║  • Paris (culture) + Nice (beach) — ideal balance                         ║│
│  ║  • Kid-friendly: easy logistics, familiar food options                     ║│
│  ║  • No 6 AM starts, moderate walking                                        ║│
│  ║                                                                            ║│
│  ║  💰 BUDGET: ₹4.2L (slightly over — consider extending or reducing days)   ║│
│  ║  ⚖️ TRADE-OFF: Less beach time, more city culture                          ║│
│  ║                                                                            ║│
│  ║  🗓️ ITINERARY:                                                             ║│
│  ║  Days 1-4: Paris (Louvre, Eiffel Tower, day trip to Disneyland)            ║│
│  ║  Days 5-6: Lyon (culture + food, shorter travel day)                       ║│
│  ║  Days 7-10: Nice/French Riviera (beach relaxation, day trip to Monaco)     ║│
│  ║                                                                            ║│
│  ║  📊 ESTIMATED PACE: Moderate (2 major activities/day)                       ║│
│  ║                                                                            ║│
│  ╚════════════════════════════════════════════════════════════════════════════╝│
│                                                                                  │
│  ╔════════════════════════════════════════════════════════════════════════════╗│
│  ║                              OPTION 2: ITALY FOCUS                          ║│
│  ╠════════════════════════════════════════════════════════════════════════════╣│
│  ║                                                                            ║│
│  ║  ⭐ WHY THIS FITS YOUR CLIENT                                              ║│
│  ║  • Best culture + beach combo in Europe                                   ║│
│  ║  • Rome (history) + Amalfi Coast (beach)                                   ║│
│  ║  • Family-friendly, great food, memorable experiences                      ║│
│  ║  • Flexible pace options                                                    ║│
│  ║                                                                            ║│
│  ║  💰 BUDGET: ₹3.8L (within budget!)                                         ║│
│  ║  ⚖️ TRADE-OFF: More walking, some hilly terrain in Amalfi                  ║│
│  ║                                                                            ║│
│  ║  🗓️ ITINERARY:                                                             ║│
│  ║  Days 1-4: Rome (Colosseum, Vatican, food tours)                           ║│
│  ║  Days 5-6: Florence (art, day trip to Pisa)                                ║│
│  ║  Days 7-10: Amalfi Coast (beaches, boat trips, relaxed)                    ║│
│  ║                                                                            ║│
│  ║  📊 ESTIMATED PACE: Moderate to Active (walking required)                    ║│
│  ║                                                                            ║│
│  ╚════════════════════════════════════════════════════════════════════════════╝│
│                                                                                  │
│  ╔════════════════════════════════════════════════════════════════════════════╗│
│  ║                              OPTION 3: GREECE FOCUS                          ║│
│  ╠════════════════════════════════════════════════════════════════════════════╣│
│  ║                                                                            ║│
│  ║  ⭐ WHY THIS FITS YOUR CLIENT                                              ║│
│  ║  • Best VALUE — under budget with room for upgrades                        ║│
│  ║  • Athens (history) + Islands (beaches)                                     ║│
│  ║  • Easy pace, family-friendly, great for kids                              ║│
│  ║  • Less crowded than France/Italy in June                                   ║│
│  ║                                                                            ║│
│  ║  💰 BUDGET: ₹3.5L (under budget — ₹50K for upgrades/extras)                ║│
│  ║  ⚖️ TRADE-OFF: Less "classic Europe" feel, more relaxed                    ║│
│  ║                                                                            ║│
│  ║  🗓️ ITINERARY:                                                             ║│
│  ║  Days 1-3: Athens (Acropolis, Plaka, day trip to Delphi)                    ║│
│  ║  Days 4-6: Naxos (beaches, villages, kid-friendly)                         ║│
│  ║  Days 7-10: Santorini (iconic views, beaches, boat trips)                  ║│
│  ║                                                                            ║│
│  ║  📊 ESTIMATED PACE: Relaxed (1 major activity/day)                          ║│
│  ║                                                                            ║│
│  ╚════════════════════════════════════════════════════════════════════════════╝│
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  💡 PRO TIP: Italy offers the best balance of culture+beach within budget.      │
│  Greece is the best value if budget flexibility exists.                          │
│                                                                                  │
│  [Edit Options]  [Regenerate]  [Present to Client]                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Key elements**:
- Each option has clear "Why this fits"
- Budget is explicit
- Trade-offs are called out
- Rationale is transparent
- Comparison is easy

---

### Screen 8: Present to Client

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ← Back                                                                         │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Present to Client                                                               │
│  ───────────────────                                                             │
│                                                                                  │
│  How would you like to share these options?                                      │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                                                                             ││
│  │  🔗 Share Link (Recommended)                                                ││
│  │                                                                             ││
│  │  Client sees a beautiful web page with options.                             ││
│  │  You'll be notified when they view it.                                      ││
│  │                                                                             ││
│  │  ┌──────────────────────────────────────────────────────────────────────┐  ││
│  │  │ agency-os.com/priya-travels/trip/sharma-europe                       │  ││
│  │  └──────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                             ││
│  │  [Copy Link]  [Customize message]                                          ││
│  │                                                                             ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                             ││
│  │  📧 Email as PDF                                                             ││
│  │                                                                             ││
│  │  Send as attached PDF. Client can reply with questions.                    ││
│  │                                                                             ││
│  │  [Send via Email]                                                           ││
│  │                                                                             ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │                                                                             ││
│  │  📱 Copy to WhatsApp                                                         ││
│  │                                                                             ││
│  │  Copy options text to paste in WhatsApp.                                    ││
│  │                                                                             ││
│  │  [Copy for WhatsApp]                                                         ││
│  │                                                                             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  Client: Raj Sharma (raj.sharma@email.com)                                       │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                          Share via Link →                                  │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

### Screen 9: Client View (What Traveler Sees)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Agency OS 🧭                                                                   │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ╔════════════════════════════════════════════════════════════════════════════╗│
│  ║                                                                            ║│
│  ║         Your Europe Family Trip                                              ║│
│  ║                                                                            ║│
│  ║         from Priya Travels                                                  ║│
│  ║                                                                            ║│
│  ╚════════════════════════════════════════════════════════════════════════════╝│
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Hi Sharma Family! 👋                                                            │
│                                                                                  │
│  Based on what you shared, I've prepared 3 options for your Europe trip.         │
│  Each balances culture, beaches, and family time differently.                   │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │  [OPTION 1: FRANCE]  [OPTION 2: ITALY]  [OPTION 3: GREECE]                  ││
│  │                                                                             ││
│  │  Tap an option to see details                                               ││
│  │                                                                             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Quick comparison:                                                               │
│  ┌──────────────────┬──────────────┬──────────────┬──────────────┐              │
│  │                  │ France      │ Italy        │ Greece       │              │
│  ├──────────────────┼──────────────┼──────────────┼──────────────┤              │
│  │ Budget           │ ₹4.2L       │ ₹3.8L       │ ₹3.5L       │              │
│  │ Culture          │ ★★★★☆      │ ★★★★★      │ ★★★☆☆      │              │
│  │ Beaches          │ ★★★☆☆      │ ★★★★☆      │ ★★★★★      │              │
│  │ Kid-friendly     │ ★★★★★      │ ★★★★☆      │ ★★★★★      │              │
│  │ Pace             │ Moderate    │ Active      │ Relaxed    │              │
│  └──────────────────┴──────────────┴──────────────┴──────────────┘              │
│                                                                                  │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Questions? Exclusions? Things to add?                                          │
│                                                                                  │
│  [WhatsApp Priya]  [Reply via Email]                                            │
│                                                                                  │
│  Powered by Agency OS | Privacy                                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Traveler view is simpler** — no backend, no complexity. Just the information they need.

---

## Flow 3: Agency Owner Dashboard

### Screen: Agency Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Agency OS    🔔           [Rajesh ▼]                  [⚙️]                    │
│  ───────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│  Rajesh's Travels                                                               │
│  ───────────────────                                                           │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    12        │  │     47       │  │    18 min    │  │     4.8★     │       │
│  │  Agents      │  │  Trips this  │  │  Avg time    │  │  Satisfaction │       │
│  │              │  │  month       │  │  to options  │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                                                  │
│  ═════════════════════════════════════════════════════════════════════════════   │
│                                                                                  │
│  TEAM PERFORMANCE                                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ Agent           │ Trips │ Avg Time │ Rating │ Status                      ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ Priya S.       │   15  │  15 min  │  4.9★  │ ● Active                    ││
│  │ Amit K.        │   12  │  22 min  │  4.5★  │ ● Active                    ││
│  │ Sneha M.      │    8  │  18 min  │  4.7★  │ ● Active                    ││
│  │ Rahul P.      │    5  │  35 min  │  4.2★  | ⚠️ Needs attention          ││
│  │ Neha S.       │    7  │  20 min  │  4.6★  │ ● Active                    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ═════════════════════════════════════════════════════════════════════════════   │
│                                                                                  │
│  RECENT TRIPS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ Sharma Family Europe │ Priya S. │ Options sent │ 2 hours ago │ [View]     ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ Mehta Thailand    │ Amit K.  │ Review      │ 5 hours ago │ [View]     ││
│  ├─────────────────────────────────────────────────────────────────────────────┤│
│  │ Patel Honeymoon   │ Sneha M. │ Booked      │ Yesterday  │ [View]     ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ═════════════════════════════════════════════════════════════════════════════   │
│                                                                                  │
│  [View All Trips]  [Manage Team]  [Analytics]  [Settings]                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Flow Design Principles

| Principle | Application |
|-----------|--------------|
| **Clear CTAs** | One primary action per screen |
| **Progressive disclosure** | Show complexity only when needed |
| **Always show "why"** | Rationale, reasoning, trade-offs |
| **Respect the human** | Agent always has final control |
| **Transparent AI** | Show confidence, flags, limitations |
| **Mobile-first** | Most agents work from phones |
| **Fast feedback** | Show progress, don't make them wait |
| **Easy reversal** | Undo, edit, go back always available |
