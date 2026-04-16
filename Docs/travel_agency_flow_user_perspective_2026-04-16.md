# Travel Agency App — Expected vs Actual Flow Analysis

**Date:** 2026-04-16  
**Perspective:** End user (agent operator / agency owner)

---

## The Flow I Expected

### 1. Home Screen — "What's happening right now?"

I land on the home screen. I see how many trips are active, which ones need my attention, and where each trip is in the process. Numbers should be real — if I have 7 trips, don't tell me 12. The stages should match what I see everywhere else in the app. Clicking any trip should take me to that trip, pre-loaded and ready to work.

### 2. Inbox — "What needs my attention?"

I see incoming trip requests sorted by urgency. I should be able to pick one, assign it to myself, and jump straight into working on it. Clicking a trip should take me to that specific trip — the customer message already loaded, the context already filled in, like opening an email and seeing the full thread.

### 3. The Trip Screen — "Let me work on this trip"

I arrive on a trip that's already loaded. The customer's message is there, the context is filled in. I review it, maybe adjust a few settings, and hit "Process Trip." The system analyzes it and fills the results.

After processing, I walk through the results across the sections:
- **First section** — what the system extracted (dates, budget, party size, destination)
- **Second section** — can I send this to the customer? What's blocking me? What follow-up questions do I need to ask?
- **Third section** — here's what I should say to the traveler, and separately what I should know internally as an agent
- **Fourth section** — before I send anything, did we accidentally leak internal jargon or blockers into the customer-facing message?

### 4. Back to Inbox — "Next one"

I go back to Inbox and pick the next trip. The cycle continues. Each trip I open should feel like opening a file — it loads, I work, I move on.

### 5. Pending Reviews — "As an owner, what needs my sign-off?"

I see high-risk or expensive trips that need my approval. I review the context, approve or reject. If I click "View Details" on a review, I should land on that exact trip — the one being reviewed, not a blank slate.

### 6. Team Stats — "How's the team doing?"

I check how the team is performing — where trips are getting stuck, who's overloaded, what's the conversion rate. I change the time range and the numbers update accordingly.

---

## What Actually Happens

### Home Screen

Looks nice. Numbers are fake — always shows "12 Active" regardless of actual trip count. The progress bar shows stages I've never seen anywhere else in the app. If I click any trip from the "Recent Trips" list, I land on the trip screen but nothing loads — it just sits there empty, like walking into a meeting room and nobody knows what meeting this is.

### Inbox

Looks real. I can filter, search, select multiple trips. But clicking a trip card is a dead end — I go to the trip screen and it doesn't know which trip I clicked. It's like opening a patient file and getting a blank chart.

Bulk actions ("Assign to...", "Export") pop up browser alerts instead of actually doing anything.

### The Trip Screen — This is where it falls apart

The first section has text fields. I type a customer message. I hit "Process Trip"... and **nothing happens**. The button shows a spinner briefly but never actually processes anything. The four sections after it all say "No data. Process a trip from the first tab first." But I just did! The system that does the analysis works (someone told me I can test it directly and it gives full results), but the button in the UI isn't connected to it. It's a button-shaped decoration.

The dropdown at the top has 4 trip names that don't match anything else in the app. The same trip has different names in different places. Two different systems, no connection.

### Pending Reviews

Shows 5 trips that never change. I can click "Approve" and the badge turns green, but nothing persists — refresh the page and it resets. If I click "View Details," I land on the trip screen... and again nothing loads. Dead link. The Filters and Bulk Actions buttons at the top don't do anything either.

### Team Stats

All the numbers are baked into the code. Choosing "Last 7 days" vs "Last 90 days" changes nothing. The time range dropdown is cosmetic. The stats say "Total Inquiries: 47" but the trips list only has 7. The suggestions ("Set up automated supplier follow-ups") don't do anything when clicked. The Export button is decorative.

---

## The Core Gap

The analysis engine works — give it a trip request and it produces a full breakdown: what was extracted, what's missing, what to ask the customer, what's safe to send, what to keep internal. But the screens never ask it to run. The "Process Trip" button doesn't call the engine. The Inbox doesn't pass trip data to the trip screen. The Reviews don't link to their trips.

Every page feels like a well-designed form that was never connected to its database. The screens show you the shape of the product — what it would feel like to use — but the substance is missing. It's a product mannequin: it looks right from a distance, but pick it up and there's nothing inside.

The most disorienting moment for a user: typing a detailed customer inquiry, clicking "Process Trip," and watching... nothing. You double-check. You type again. You click again. Still nothing. You start wondering if the app is broken, if your input was wrong, if you missed a step. There's no error message, no loading state that sticks, no feedback at all. Just silence. That's the critical break — the moment where the user loses trust.

---

## What Needs to Be True (Priority Order)

1. **"Process Trip" must actually do the analysis.** This is the product's core action. Without it, nothing else matters.

2. **Clicking a trip anywhere (Inbox, Home, Reviews) must open that trip.** The user should feel like they "opened a file" — context appears, not a blank form.

3. **The results must fill in after processing.** The four sections after the input — extracted details, blockers and follow-ups, what to say vs what to know, and the safety check — these are the payoff. The user processed the trip to see these results.

4. **Numbers on the Home screen and Team Stats page must be real.** Fake numbers erode trust immediately. If it says "12 Active" and I can only see 7, I stop believing anything the app tells me.

5. **Pending Reviews must open the actual trip.** An owner clicking "View Details" on an expensive trip review expects to see that trip's full context, not a blank screen.

6. **Time range, filters, and exports must work.** Every button that doesn't respond teaches the user "this app doesn't really work."

---

*Companion document: `travel_agency_flow_audit_2026-04-16.md` (technical breakdown with file paths, HTTP status codes, and fix suggestions)*

---

## Appendix: UI Jargon to Plain Language Mapping

This table shows what needs to change in the frontend code:

| Current UI Label | File Location | Plain Language Replacement |
|------------------|---------------|---------------------------|
| "Intake" (tab) | `workbench/WorkbenchTab.tsx:15` | "New Inquiry" |
| "Packet" (tab) | `workbench/WorkbenchTab.tsx:16` | "Trip Details" |
| "Decision" (tab) | `workbench/WorkbenchTab.tsx` | "Ready to Quote?" |
| "Strategy" (tab) | `workbench/WorkbenchTab.tsx` | "Build Options" |
| "Safety" (tab) | `workbench/WorkbenchTab.tsx` | "Final Review" |
| "Trip Pipeline" | `workbench/page.tsx:68` | "Trip Workspace" |
| "Trip Pipeline" (nav) | `Shell.tsx:36`, `design-system.ts:39` | "Workbench" |
| "Workbench" (nav) | `page.tsx:389` | "Trip Workspace" |
| "Process Trip" | `workbench/page.tsx:94` | "Analyze Trip" or "Generate Quote" |
| "Operating Mode" | `IntakeTab.tsx:145` | "Mode" or "Request Type" |
| "Normal Intake" | `IntakeTab.tsx:37` | "New Request" or "First-Time Inquiry" |
| "Leakage Status" | `SafetyTab.tsx:48` | "Content Review" |
| "No Leakage Detected" | `SafetyTab.tsx:53` | "Customer-Safe — Ready to Send" |
| "Leakage Detected" | `SafetyTab.tsx:63` | "Internal Jargon Found" |
| "STRICT MODE FAILURE" | `SafetyTab.tsx:75` | "NOT SAFE TO SEND" |
| "Traveler bundle" | `SafetyTab.tsx:78` | "Customer message" |
| "Traveler-Safe Bundle" | `SafetyTab.tsx:100` | "Customer-Facing Message" |
| "Internal Bundle (Reference)" | `SafetyTab.tsx:149` | "Agent-Only Notes" |
| "Internal vs Traveler-Safe" | `StrategyTab.tsx:110` | "Agent View vs Customer View" |
| "Internal Agent View" | `StrategyTab.tsx:114` | "For You (Agent)" |
| "Traveler-Safe View" | `StrategyTab.tsx:155` | "For Customer" |
| "Raw JSON" toggle | `SafetyTab.tsx:195` etc. | "Show Raw Data" or "Show Technical JSON" |
| "NB01", "NB02", "NB03" | `workspace/*/page.tsx` | Remove entirely (internal codes) |
| "Normal intake handling" | `workspace/intake/page.tsx:5` | "Ask follow-up questions, set stage and mode" |
| "Leakage checks + sanitization" | `workspace/safety/page.tsx:5` | "Check for internal jargon before sending" |
| "Traveler-safe proposal preview" | `workspace/output/page.tsx:5` | "Preview message to customer" |
| "internal/traveler split" | `workspace/strategy/page.tsx:5` | "Separate agent notes from customer message" |
| "API Connected" | `IntakeTab.tsx:170` | Remove or "System Ready" |
| "Pipeline" | `page.tsx:133` etc. | "Progress" or "Stages" |
| "Pipeline Value" | `insights/page.tsx:310` | "Total Value in Progress" |
| "Pipeline Velocity" | `insights/page.tsx:324` | "Average Time to Complete" |

**Note:** The existing work in `PipelineFlow.tsx` already renames these correctly for the visual flow diagram, but the actual tab component and navigation still use the old jargon labels.