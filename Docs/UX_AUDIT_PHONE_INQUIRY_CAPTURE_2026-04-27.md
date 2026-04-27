# UX Audit: Phone-Inquiry Data Capture Flow
## Waypoint OS — Real Scenario Test: Ravi / Singapore Trip

**Date:** 2026-04-27
**Tester:** Pranay Suyash (acting as agency owner "Ravi")
**Scenario:** Real phone call from Nov 2024 — Singapore family trip, 5 days, 6 people (couple + toddler + parents)
**Scope:** Document ONLY. No code changes.

---

## 1. The Real Scenario (Recap)

> **Caller (Pranay):** "Hi Ravi, I got your number from my wife who's a colleague of Divya (your wife). We're planning to visit Singapore sometime in Jan or Feb. Tentative dates around 9th to 14th Feb — approx 5 days. Me, my wife, a 1.7 year old kid, and my parents would be going."
>
> **Agency Owner (Ravi):** "Hey, thanks for the call. Will surely look into it. There are lots of things to do in Singapore — Universal Studios we can add, nature parks..."
>
> **Caller:** "We don't want it rushed."
>
> **Agency Owner:** "Sure, let me see. Give me a day or two to get back with a draft."

**Key facts to capture:**
| Fact | Value |
|------|-------|
| Customer name | Pranay Suyash |
| Customer phone | [Ravi would have this] |
| Customer email | [Not exchanged on call] |
| Referral source | Wife's colleague → Divya (Ravi's wife) |
| Destination | Singapore |
| Date window | Jan or Feb 2025 |
| Tentative dates | Feb 9-14 (5 days) |
| Party size | 6 (2 adults + 1 toddler + 2 parents) |
| Budget | Not discussed |
| Pace preference | "Don't want it rushed" |
| Interests mentioned | Universal Studios, nature parks |
| Channel | Phone call |
| Call date | ~Nov 25, 2024 |
| Follow-up promised | Draft itinerary in 1-2 days |

---

## 2. How to Enter This in the App Today (Step-by-Step)

Since there is **no "New Trip" or "New Inquiry" button**, here's the workaround:

### Step 1: Go to Workbench
- Navigate to: `http://localhost:3000/workbench`
- You should see the Intake tab active

### Step 2: Compose the Customer Message
In the **"Customer Message"** textarea, type a summary of the call:

```
Hi Ravi, I got your number from my wife who is a colleague of Divya. 
We are planning to visit Singapore sometime in Jan or Feb 2025. 
Tentative dates: around 9th to 14th Feb, approx 5 days. 
Travelers: me, my wife, our 1.7 year old kid, and my parents (6 people total). 
We don't want it rushed. Interested in Universal Studios and nature parks.
```

### Step 3: Add Agent Notes
In the **"Agent Notes"** textarea, add Ravi's context:

```
- Call received Nov 2024
- Customer is referral from wife's colleague Divya
- 6 pax including elderly parents and toddler — pace must be relaxed
- No budget discussed yet — need to follow up
- Promised draft itinerary in 1-2 days
- Customer explicitly said: "don't want it rushed"
```

### Step 4: Set Stage and Type
- **Stage:** `discovery` (this is a new inquiry)
- **Request Type:** `New Request`

### Step 5: Click "Process Trip"
- The backend will parse the text and extract structured data
- A new trip will be created and appear in the Inbox

### Step 6: Review and Edit Extracted Data
- Go to Inbox → click the new Singapore trip
- In the Intake Panel, verify/correct:
  - Destination: Singapore ✅
  - Type: Family Vacation (change if wrong)
  - Party Size: 6 ✅
  - Dates: "9th to 14th Feb 2025" or "Jan-Feb 2025"
  - Budget: [leave blank — not discussed]

### Step 7: Add Missing Context
Since there's nowhere to put it, add these as notes:
- Referral chain: Pranay → wife → Divya → Ravi
- Pace preference: Relaxed, not rushed
- Toddler considerations: 1.7yo — need stroller-friendly, nap times
- Elderly considerations: Parents — need accessible transport, moderate walking

---

## 3. UX Audit Findings

### 🔴 Critical Gaps (Block real-world usage)

| # | Gap | Impact | Evidence |
|---|-----|--------|----------|
| 1 | **No "New Inquiry" button** | Agency owner must know to go to Workbench and paste text. No guided flow for first-time users. | No create button in Inbox, Overview, or Sidebar |
| 2 | **No customer identity fields** | Cannot capture caller name, phone, email. Cannot call back or send follow-up. | Intake Panel has destination, dates, party — no contact info |
| 3 | **No channel/source tracking** | Cannot distinguish phone vs WhatsApp vs email inquiries. Cannot measure channel effectiveness. | No "Source" dropdown in intake |
| 4 | **No referral tracking** | Cannot capture "wife's colleague → Divya" chain. Cannot reward referrals. | No referral source field |
| 5 | **Single flat text area for conversation** | No way to capture turn-by-turn dialogue. Loses nuance ("don't want it rushed" is buried in text). | Only "Customer Message" + "Agent Notes" textareas |
| 6 | **No date ambiguity handling** | "Jan or Feb" + "tentative" dates cannot be captured. System expects fixed dates. | Dates field is single text input |
| 7 | **No budget uncertainty capture** | "Budget not discussed" is not a first-class state. System expects a number. | Budget is number + currency, no "TBD" option |
| 8 | **No family composition fields** | 6 people = 2 adults + 1 toddler + 2 elderly. Current UI only asks "party size" (number). | Party size is just a number, no age breakdown |
| 9 | **No pace/preference capture** | "Don't want it rushed" is a critical preference. No field for pace, intensity, or style. | No preference fields in intake |
| 10 | **No follow-up tracking** | "Give me a day or two" — promised follow-up date cannot be tracked. | No reminder or follow-up date field |

### 🟡 Major Friction (Annoying but workaroundable)

| # | Issue | Impact |
|---|-------|--------|
| 11 | **Workbench is a pipeline tool, not a capture tool** | The UI is designed for processing existing text, not for live note-taking during a call. |
| 12 | **No live call mode** | Cannot take notes while on a call. Must remember everything and type afterward. |
| 13 | **No transcript upload** | If call is recorded/transcribed, no place to attach or paste transcript. |
| 14 | **Timeline shows processing steps, not conversation history** | The "Timeline" tab shows AI pipeline stages, not the actual call history or notes. |
| 15 | **Overview shows 0 stats for new agency** | Real user sees all zeros — no guidance on what to do next. |

### 🟢 What Works Well

| # | Positive | Evidence |
|---|----------|----------|
| 1 | **Workbench text processing is powerful** | Paste free text, get structured extraction |
| 2 | **Stage/config selectors are clear** | Discovery/Shortlist/Proposal/Booking — intuitive |
| 3 | **Intake panel editing is inline and fast** | Click field, edit, save — no page reloads |
| 4 | **Trip cards in Inbox are informative** | Destination, type, priority, SLA all visible |
| 5 | **Agency scoping works** | Real user sees 0 trips, test user sees 484 — no cross-contamination |

---

## 4. Recommended Capture Flow (Future State)

For a phone-inquiry scenario like this, the ideal flow would be:

```
[Inbox] → [+ New Inquiry] → Modal opens

New Inquiry Modal:
├── Channel: [Phone | WhatsApp | Email | Walk-in | Referral] *
├── Caller Name: [Pranay Suyash] *
├── Phone: [+91...] *
├── Email: [optional]
├── Referral Source: [Wife's colleague → Divya]
├── Call Date/Time: [Nov 25, 2024, 3:00 PM] (auto-filled)
├── Call Notes (real-time textarea):
│   ├── Turn-by-turn or free-form
│   ├── Auto-saved every 5 seconds
│   └── Tagged: [Interest], [Constraint], [Follow-up], [Budget]
├── Extracted Facts (auto-populated from notes):
│   ├── Destination: Singapore
│   ├── Dates: Jan-Feb 2025 (tentative, Feb 9-14)
│   ├── Party: 6 (2 adults, 1 toddler, 2 elderly)
│   ├── Pace: Relaxed
│   ├── Budget: TBD
│   └── Interests: Universal Studios, nature parks
├── Follow-up:
│   ├── Promised by: [Ravi]
│   ├── Due date: [Nov 27, 2024]
│   └── Reminder: [1 day before]
└── [Save Draft] [Process Trip] [Cancel]
```

---

## 5. Immediate Workarounds (For Testing Today)

Until the UI is improved, use these workarounds:

### Workaround 1: Structured Customer Message
Always include these sections in the Customer Message:
```
CALLER: [Name]
PHONE: [Number]
SOURCE: [How they found you]
DESTINATION: [Place]
DATES: [Window]
TRAVELERS: [Number + composition]
BUDGET: [Amount or "Not discussed"]
PREFERENCES: [Pace, interests, constraints]
FOLLOW-UP: [What you promised and when]
```

### Workaround 2: Agent Notes as CRM
Use Agent Notes to capture everything the system doesn't have fields for:
- Contact details
- Referral chain
- Family composition (ages, special needs)
- Pace/preferences
- Follow-up promises
- Internal reminders

### Workaround 3: Use Workbench for Every Call
Make `/workbench` the default landing page after login. Process the trip immediately after the call while memory is fresh.

---

## 6. Questions for Ravi (The Agency Owner)

To validate how real agencies work, ask:

1. **How do you currently take notes during a call?** (Pen & paper? Notes app? Memory?)
2. **What information do you ALWAYS capture?** (Name, phone, dates, budget — in what order?)
3. **How do you track follow-ups?** (Calendar? WhatsApp reminders? Memory?)
4. **Do you record calls or take transcripts?** (If yes, where do they go?)
5. **How do you handle uncertain dates?** ("Jan or Feb" — what do you put in your current system?)
6. **How do you handle budget discussions?** (Do you ask directly? Wait for them to offer?)
7. **What makes you forget to follow up?** (No reminder? Too busy? Lost in notes?)
8. **How do you share the draft itinerary?** (Email? WhatsApp? Phone call?)

---

## 7. Definition of Done (For This Audit)

- [x] Scenario documented in full
- [x] Step-by-step entry instructions written
- [x] Critical gaps catalogued (10 items)
- [x] Major friction catalogued (5 items)
- [x] Positive aspects catalogued (5 items)
- [x] Future-state flow designed
- [x] Immediate workarounds documented
- [x] Interview questions for agency owner prepared

**Next step:** Pranay tests the step-by-step entry (Section 2) and reports back on what breaks, confuses, or works.

---

**Document version:** 1.0
**Created:** 2026-04-27
**File:** `Docs/UX_AUDIT_PHONE_INQUIRY_CAPTURE_2026-04-27.md`
