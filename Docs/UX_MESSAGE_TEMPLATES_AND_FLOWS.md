# UX Message Templates and Conversation Flows

**Date**: 2026-04-13
**Purpose**: Document actual messages travelers receive and conversation patterns
**Related**: `UX_AND_USER_EXPERIENCE.md` (overview), `NB02_V02_SPEC.md` (decision logic)

---

## Core Philosophy

Every traveler-facing message must be:
1. **Human-sounding**: Not robotic or templated despite being system-generated
2. **Context-aware**: References previous conversation, remembers details
3. **Action-oriented**: Clear next step, not open-ended
4. **Positive-framed**: Solutions first, problems second
5. **Brief**: WhatsApp messages should be scannable

**Anti-patterns to avoid**:
- "Our system indicates..." (never mention the system)
- "I am unable to..." (negative framing)
- "Please provide..." (sounds bureaucratic)
- Long paragraphs (hard to read on phone)

---

## Message Template Library

### Template Categories

| Category | Purpose | Tone | Decision State |
|----------|---------|------|----------------|
| **Acknowledgment** | Confirm receipt, set expectations | Warm + efficient | All |
| **Clarification** | Resolve blockers/ambiguities | Curious, helpful | ASK_FOLLOWUP |
| **Proposal** | Present options with rationale | Expert, confident | PROCEED_TRAVELER_SAFE |
| **Urgency** | Fast-track when time-critical | Calm but pressing | All (urgency=high) |
| **Crisis** | Emergency situations | Reassuring + action | STOP_NEEDS_REVIEW |
| **Closing** | Move toward decision | Gentle pressure | All |
| **Document Request** | Collect requirements | Respectful, clear | ASK_FOLLOWUP |
| **Post-Booking** | Confirm, reassure, prepare | Detailed, organized | Post-booking |

---

## 1. Acknowledgment Templates

### New Customer Inquiry

```
Hi [Name]! Thanks for reaching out.

I'd love to help plan your [destination if known, else "upcoming trip"].

Quick questions to find the best options:
1. Where are you thinking of going? (or: "I see you mentioned [X] - is that confirmed?")
2. How many people, and ages of any kids?
3. Travel dates (even approximate is fine to start)
4. Budget range (so I don't suggest options that don't work)

I'll start researching while you reply!
```

### Repeat Customer Recognition

```
Hi [Name]! Great to hear from you again!

I remember your [destination] trip in [month/year] - you loved [specific detail from past trip].

For this new trip, are you thinking of something similar or different this time?
```

### After Hours / Weekend

```
Hi [Name]! Thanks for your message.

I received this outside office hours. I'll review and get back to you by
[specific time, e.g., "10 AM tomorrow"] with options.

If this is urgent, please call me at [number]. Otherwise, I'll be in touch soon!
```

---

## 2. Clarification Templates (ASK_FOLLOWUP)

### Destination Ambiguity

```
Quick question about [destination candidates]:

You mentioned "[A] or [B]" - both are great but quite different!

[A] is better for: [key differentiator]
[B] is better for: [key differentiator]

Any preference, or should I research both and send comparisons?
```

### Budget Clarification

```
About the budget - you mentioned [amount]. Just to confirm:
  • Is this per person or total for [party_size] people?
  • Does this include flights or just land package?

This helps me suggest options that actually work - don't want to waste your
time with things that don't fit!
```

### Party Size Ambiguity

```
You mentioned "[party description]" - can you confirm the exact number
and ages?

This affects:
  • Hotel room requirements (connecting rooms vs. separate)
  • Activity suitability (kids vs. adults)
  • Pricing (child rates vs. adult rates)
```

### Date Window

```
For dates, you said "[date range or description]":

A few options I'm seeing:
  • [Option 1]: [dates] - [pros/cons]
  • [Option 2]: [dates] - [pros/cons]

Any preference, or should I check what's available for both windows?
```

---

## 3. Proposal Templates (PROCEED_TRAVELER_SAFE)

### Three-Option Format

```
Great! Based on what you've shared, here are 3 options for [destination]:

🥉 BUDGET-FRIENDLY ([price])
• [Hotel/Resort name]
• Great for: [who this suits]
• Trade-offs: [what you give up for lower price]

🥈 RECOMMENDED ([price]) ⭐
• [Hotel/Resort name]
• Great for: [who this suits]
• Why I recommend this: [specific rationale]

🥇 LUXURY ([price])
• [Hotel/Resort name]
• Great for: [who this suits]
• Best for: [special occasion or unique value]

All options include:
→ [Inclusions list]

I can hold [option] for [timeframe] while you decide.
Which would you like to know more about?
```

### Single Recommendation (When Clear Preference)

```
Based on what you've told me, I'm recommending [specific option]:

[Why this fits their specific needs]
[What makes it special]
[Price and what's included]

[Alternative if this doesn't work]

Shall I proceed with checking availability?
```

### Comparison Format (When Destinations Unclear)

```
You asked about [A] vs [B]. Both great, here's how they compare:

[A] - [key characteristics]
  • Better if you want: [X]
  • Budget: [range]
  • Best time to go: [when]

[B] - [key characteristics]
  • Better if you want: [Y]
  • Budget: [range]
  • Best time to go: [when]

Based on your preference for [their stated preference], I'd lean toward
[recommendation].

Would you like me to send detailed options for [recommendation]?
```

---

## 4. Urgency Templates (High Urgency Mode)

### Last-Minute Booking

```
Since you're looking at [dates - less than 3 weeks away], let's move fast:

Good news: I found [number] options that work.
Challenge: [specific urgency factor - e.g., "flights getting expensive"]

To lock this in:
1. [Immediate action needed - e.g., "Confirm by 5 PM today for best rates"]
2. [Quick decision point - e.g., "Option A or B?"]

I'll hold these while you decide. What questions can I answer right away?
```

### Passport/Visa Urgency

```
Quick heads up: For [destination], we need [document requirement].

Your travel date is [date], which means [time constraint].

Options:
1. [Fastest path with risk assessment]
2. [Safer alternative if time permits]

Let me know which direction you'd like to take. I can't proceed to booking
until we resolve this.
```

### Peak Season Warning

```
Just so you're aware: [dates] is peak season for [destination].

This means:
  • Good options book fast (some already gone)
  • Prices are higher than [off-season comparison]
  • [specific challenge for their dates]

I've found [number] options that still work. Ready to share when you are.
```

---

## 5. Crisis Templates (STOP_NEEDS_REVIEW)

### Visa Problem

```
I need to discuss something important about your booking.

[Issue description - e.g., "Passport expiry is too close to travel date"]

This affects: [what's at risk]

I'm going to call you in [timeframe] to discuss options.
[If urgent] Please pick a time: [time options]

We can solve this, but we need to act quickly.
```

### Booking Complications

```
Quick update on your [destination] booking:

[Issue - e.g., "Hotel is suddenly unavailable for your dates"]

Here's what I'm doing:
1. [Alternative being secured]
2. [Backup plan if needed]
3. [Any impact on price or experience]

I'll have a confirmed update for you by [time].

Want me to call once I have details?
```

### Medical/Emergency During Trip

```
[Automated response when emergency keyword detected]

We received your message. Emergency protocol activated.

[Name] will call you in [minutes].

Meanwhile:
• [Immediate safety instructions]
• [Insurance coverage if applicable]
• [What not to do]

Stay where you are. Help is on the way.
```

---

## 6. Closing Templates

### Gentle Close (No Pressure)

```
No rush on this! Take your time to think it over.

I'll hold these options for [timeframe]. If you have any questions
or want to adjust anything, just let me know.

[If relevant]: "If I don't hear back by [date], I'll check in with you."
```

### Time-Sensitive Close

```
Just a heads up: This option [time constraint - e.g., "sale ends tomorrow" / "only 2 rooms left"]

I'd recommend deciding by [specific time] to avoid missing out.

If you need more time to think, I can check if [alternative] works too.
```

### Decision Prompt

```
So, where are we leaning?

[Option A]: [brief recap]
[Option B]: [brief recap]
[Option C]: [brief recap]

Or should I adjust something based on what you've seen?

Happy to go in whatever direction works for you!
```

### Follow-Up After Silence

```
Hi [Name]! Just checking in on your [destination] trip.

Any thoughts on the options I sent? Or would you like me to adjust
something based on:

[Their stated preferences recap]

No pressure - just want to make sure I'm being helpful.
If you've gone in a different direction, no worries either way!
```

---

## 7. Document Request Templates

### Passport Collection (Group Trip)

```
Quick update: We're at the document collection stage for [destination] trip.

[Progress indicator: e.g., "3 of 5 families have submitted"]

Still need passports from: [list of who's missing]

[Each person gets a direct link]
[Family member name]: [personalized upload link]

[Deadline]: Need all by [date] to proceed with booking.

Once everyone's in, I'll confirm everything. Thanks for your help!
```

### Gentle Reminder

```
Hi [Name]! Just a friendly reminder about [document needed].

Link here: [upload link]

Takes 2 minutes. Let me know if you have any trouble with the upload!

Need by: [deadline]
```

### Final Reminder (Firm but Polite)

```
Final reminder: We're [timeframe] away from needing to confirm your booking.

Still missing: [document list]

[Deadline]: [specific date/time]

After this date, I can't guarantee the [option/price/availability] we discussed.

Please upload by [deadline] so we don't lose this option.

[Link]
```

---

## 8. Post-Booking Templates

### Confirmation Message

```
Great news! Your [destination] trip is confirmed! 🎉

Here's what you need:

✅ BOOKING CONFIRMED
   • Reference: [booking ID]
   • Dates: [dates]
   • Destination: [destination]

📱 YOUR DOCUMENTS
   [Links to tickets, vouchers, insurance]

⏰ IMPORTANT
   • [Time-sensitive action - e.g., "Check in 48 hours before flight"]
   • [Pre-trip deadline - e.g., "Special meal requests by [date]"]
   • [Pickup details if applicable]

I'll send a reminder message [timeframe] before your trip with all
the details you'll need.

Any questions before then, just reply here. Excited for you!
```

### Pre-Trip Reminder (3 Days Before)

```
Hi [Name]! Your [destination] trip is in 3 days! 🌴

✅ CONFIRMED
   • [Flight details with times and seats]
   • [Hotel details with check-in time]
   • [Any transfers or pickups]

📱 DOCUMENTS
   [Links to tickets, vouchers, insurance]

⏰ REMINDERS
   • [Airport arrival time]
   • [Weather forecast - pack accordingly]
   • [Anything special to know]

❓ QUESTIONS?
Reply here - I'm monitoring messages and will respond within [timeframe].

Have an amazing trip! 
```

### Post-Trip Check-In

```
Welcome back from [destination]! 🎉

Hope you had an amazing time. Would love to hear:

1. What was the highlight of your trip?
2. Anything that didn't go as expected?
3. Should we do things differently next time?

[If applicable]: "Your review would mean a lot: [link]"

Already thinking about your next adventure? Just say the word! 😊
```

---

## Conversation Flow Maps

### Golden Path Flow (Simple Case)

```
[Customer] Initial inquiry
         ↓
[System] NB01 extracts facts
         ↓
[System] NB02: ASK_FOLLOWUP (1-2 blockers)
         ↓
[Agent] Sends clarification questions (Template: Clarification)
         ↓
[Customer] Replies with details
         ↓
[System] NB01 updates packet, NB02: PROCEED_TRAVELER_SAFE
         ↓
[Agent] Sends 3-option proposal (Template: Three-Option)
         ↓
[Customer] Chooses option or asks for adjustment
         ↓
[Agent] Sends document request (Template: Document Request)
         ↓
[Customer] Provides documents
         ↓
[System] NB02: PROCEED_TRAVELER_SAFE (booking stage)
         ↓
[Agent] Sends payment link and confirmation (Template: Confirmation)
         ↓
[System] Post-booking: Schedule reminders
         ↓
[Customer] Receives pre-trip reminder (Template: Pre-Trip)
         ↓
[Customer] Travels
         ↓
[Agent] Sends post-trip check-in (Template: Post-Trip)
```

### Complex Flow (Multiple Revisions)

```
[Customer] Initial inquiry
         ↓
[System] NB01→NB02: ASK_FOLLOWUP
         ↓
[Agent] Clarification questions
         ↓
[Customer] Replies
         ↓
[System] PROPOSE → Customer requests change
         ↓
[System] NB02: Detects revision, tracks count
         ↓
[Agent] "Sure, let me adjust..." (revision 1)
         ↓
[Customer] Another change request
         ↓
[System] Revision count = 2, flags: "approaching limit"
         ↓
[Agent] Sends revised quote + gentle boundary
         ↓
[Customer] Third change request
         ↓
[System] Revision count = 3, flags: "scope creep detected"
         ↓
[Agent] "Happy to help, but we've done 3 versions. Before I spend more
         time, are you pretty serious about booking? This helps me
         prioritize for customers who are ready to move forward."
         ↓
[Customer] Commits or walks away
```

### Emergency Flow

```
[Customer] Sends emergency message (keyword detected: "stuck", "cancelled",
                                     "emergency", "help")
         ↓
[System] Detects emergency keyword, mode: EMERGENCY
         ↓
[System] NB02: STOP_NEEDS_REVIEW
         ↓
[Automated] Immediate response: "Received. Agent calling in 10 min.
                                Meanwhile: [safety instructions]"
         ↓
[Agent] Calls customer (escalated treatment)
         ↓
[Agent] Resolves crisis (rebooking, refund, support)
         ↓
[Agent] Follow-up message: "Crisis resolved. Here's what happened..."
         ↓
[System] Logs incident, updates customer profile with learnings
```

---

## Tone Guidelines by Scenario

### Warm/Friendly (Most interactions)
- Use emojis sparingly (1-2 per message max)
- Conversational language ("Quick question" not "I require clarification")
- Show enthusiasm for their trip
- Remember personal details

### Professional/Firm (Deadlines, payments)
- Clear and direct
- No ambiguity about what's needed
- Specific times/dates
- Explain consequences without threatening

### Reassuring (Crisis, problems)
- "We can solve this" not "This is a problem"
- "I'm handling it" not "I need to check"
- Specific next steps
- Timeline for resolution

### Efficient (Urgency, busy customers)
- Get to the point quickly
- Bullet points for readability
- Clear action items
- Respect their time

---

## Common Edge Cases

### Edge Case 1: Customer Asks "Is This the Best Price?"

```
[Customer]: "Can you do any better on the price?"

[Agent response]:
"This is the best price for these specific options. Here's why it costs
what it does:
• [Break down major cost components]
• [Explain any premiums - season, room category, etc.]

If you'd like to explore alternatives to fit [target budget]:
• [Option that costs less]
• [What you'd give up for the savings]

What's most important to you - staying at this price point or adjusting
for something lower?"
```

### Edge Case 2: Customer Compares to MakeMyTrip/Booking.com

```
[Customer]: "MakeMyTrip shows this hotel for ₹10k less"

[Agent response]:
"Good catch! A few things to consider:
• MakeMyTrip price might be [explain difference - room only vs. with breakfast,
  cancelable vs. non-refundable, etc.]
• What I'm quoting includes: [list inclusions]
• [If applicable]: I can match that price if you'd like to book just the hotel

Would you like me to break down what's included so we're comparing apples
to apples? Or would you prefer to book accommodation separately and I
handle just the activities/transfers?"
```

### Edge Case 3: Customer Goes Silent After Quote

```
[Day 1 after quote - no action]

[Day 3]: Gentle check-in (Template: Follow-Up After Silence)

[Day 7]: "Hi! Just checking in - are you still interested in [destination],
or should I close this out?"

[Day 14]: System marks as "ghost customer", changes to LEAD_FOLLOWUP mode
```

### Edge Case 4: Customer Says "I'll Get Back to You" (Indefinite)

```
[Agent response]:
"Sounds good! I'll hold these options until [date].

Just so you know: [time sensitivity - e.g., "These rates are valid until [date]"]

If you need more time, no problem. Just give me a heads up if you're
still interested so I know to keep looking out for you.

[If relevant]: "If I find something even better, should I let you know?""
```

### Edge Case 5: Customer Wants Details for Competitor Quote

```
[Customer]: "Send me the full itinerary with all hotel names and prices"

[Agent response - detect price shopping]:
"Happy to share details once we're moving forward with booking.

For now, here's what I can share without confirming:
• [Destination overview]
• [Hotel categories and areas - not specific names]
• [Rough itinerary structure]

Specific hotel names and exact pricing I share once we've confirmed
you're interested in booking. This protects the work I put into
researching these options.

Fair?"
```

---

## Personalization Variables

Every template should support these variables:

| Variable | Source | Example |
|----------|--------|---------|
| `{customer_name}` | packet.facts.customer_id lookup | "Mrs. Sharma" |
| `{destination}` | packet.facts.destination_candidates | "Switzerland" |
| `{dates}` | packet.facts.date_window | "June 15-25" |
| `{party_size}` | packet.facts.party_size | "5 people" |
| `{past_trip}` | packet.facts.past_trips | "your 2024 Singapore trip" |
| `{past_preference}` | packet.facts.past_trips preferences | "loved Gardens by the Bay" |
| `{budget}` | packet.facts.budget_min | "4-5L" |
| `{urgency_level}` | derived_signals.urgency | "High" |
| `{option_name}` | NB03 generated proposal | "Adaaran Club" |
| `{option_price}` | NB03 generated proposal | "₹3.5L" |

---

## Anti-Patterns: What NOT to Say

| Don't Say | Why | Better Alternative |
|-----------|-----|-------------------|
| "Our system shows..." | Breaks human facade | "I noticed..." |
| "I am unable to..." | Negative framing | "Here's what we can do..." |
| "Please provide..." | Bureaucratic | "Quick question..." |
| "As per your request..." | Robotic | "Great idea!" |
| "We regret to inform..." | Formal, alarming | "Quick update..." |
| "Policy states that..." | Rigid | "Here's how this works..." |
| Long paragraphs | Hard to read on phone | Bullet points |
| Multiple messages in quick succession | Overwhelming | One consolidated message |

---

## Related Documentation

- `UX_AND_USER_EXPERIENCE.md` - Overall UX architecture
- `notebooks/NB02_V02_SPEC.md` - Decision logic that determines templates
- `Docs/personas_scenarios/` - Scenario-specific messaging needs

---

*All templates should be A/B tested for conversion. Track which messages get responses and which get ignored.*
