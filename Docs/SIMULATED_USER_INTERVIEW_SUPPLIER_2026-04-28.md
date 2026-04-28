# Simulated User Interview: Hotel Supplier / Vendor

**Date:** 2026-04-28
**Format:** Simulated depth interview (role-played)
**Duration:** ~50 minutes (simulated)
**Interviewer:** Product Researcher
**Participant:** "Dinesh" — Hotel Partnership Manager at a 4-star resort in Phuket

---

## 1. Participant Profile

| Attribute | Detail |
|-----------|--------|
| **Name** | Dinesh Perera (pseudonym) |
| **Age** | 41 |
| **Location** | Phuket, Thailand |
| **Role** | Partnership Manager, Andaman Resorts (3 properties, 280 rooms total) |
| **Experience** | 12 years in hotel sales and partnerships |
| **Works With** | ~45 boutique travel agencies in India |
| **Tech Stack** | Email, WhatsApp, Excel, Opera PMS, Agoda Partner Hub |
| **Monthly Agency Bookings** | ~120 room-nights from Indian agencies |
| **Biggest Frustration** | "Agencies book my standard rooms, then clients complain they wanted suites. I never know what the client actually asked for." |

---

## 2. Interview Scenario

**Context:** Dinesh has been receiving bookings from agencies that use the Agency OS tool. He's noticed differences in the bookings and inquiries. The interview explores the supplier perspective on what works and what's broken in the agency-to-supplier relationship.

---

## 3. Interview Transcript

### Opening: The Supplier Reality

**Interviewer:** Dinesh, describe your day-to-day with travel agencies.

**Dinesh:** My job is simple on paper: make sure agencies send me bookings. In reality? It's chaos.

I have 45 Indian agencies that book with us. Each one has 2-5 agents. That's ~150 people who can book my hotels. And they ALL communicate differently.

Some send a proper email: "Booking for Sharma family, 2 nights, 15-17 June, 2 deluxe rooms, includes breakfast, dietary: 2 vegetarians." Perfect. I know exactly what to expect.

Others send a WhatsApp: "Dinesh bhai, need 3 rooms next week some time, family of 6, do something." That's it. No dates. No room type. No dietary. I have to call them back, ask 10 questions, and by then the rooms might be sold out.

**Interviewer:** How does the new tool (Agency OS) change this?

**Dinesh:** *(leans forward)* This is interesting. About 6 agencies started using this "AI tool" in the last 2 months. I can TELL when I get a booking from them.

The booking notes are... better. Not perfect, but better. Instead of "3 rooms," it says "3 deluxe rooms, 2 adults + 1 child (age 7) per room. Extra bed needed. Late check-out requested."

That extra detail? It saves me 30 minutes of back-and-forth. And the client gets the right room on arrival.

But — and this is a big but — the SYSTEM doesn't talk to me. The agent uses the tool, generates a great internal brief, and then emails me the SAME WAY they always did. The tool's intelligence doesn't flow to me.

---

### Section 1: The Information Gap

**Interviewer:** Walk me through a typical booking from an agency using the tool.

**Dinesh:** Okay, let's take Priya Travels. She booked the Mehta family with us last week.

1. **Priya's inquiry to me** (via WhatsApp): "Dinesh, need 2 rooms Deluxe, 16-18 June, 4 adults + 2 kids (8 and 10). Mehta family, 3rd time with us."
2. **My response:** "Noted. Breakfast included? Any dietary? Extra beds?"
3. **Her reply:** "Breakfast yes. 2 vegetarians (elderly). Extra beds needed. Late check-out if possible."
4. **I confirm:** "Done. ₹18K per night, total ₹36K. Late check-out subject to availability."

Now, here's what I found out AFTER they arrived: the 10-year-old is a celiac. They didn't tell me. The kid got sick from cross-contamination at our buffet. The family was upset, Priya was embarrassed, and I lost a repeat customer.

**Interviewer:** Could the tool have caught that?

**Dinesh:** YES! That's my point. Priya's tool KNOWS the Mehta family. It knows they have a 10-year-old. It should have FLAGGED: "Last time, they mentioned dietary restrictions. Ask about this."

If the system had prompted Priya: "Ask if any dietary needs this time?" she would have asked. I would have known. The kid wouldn't have gotten sick.

The tool is smart for the AGENT. But that intelligence doesn't flow to ME — the person actually delivering the service.

---

### Section 2: The Rate & Inventory Pain

**Interviewer:** How do agencies currently know your rates and availability?

**Dinesh:** *(laughs)* They don't. Not in real-time.

Priya calls me: "Dinesh, what's your rate for deluxe room 15-20 July?" I tell her ₹20K/night. She quotes the client. Client says yes. I go to check availability... and the deluxe rooms are sold out. Now I look like an idiot. I have to call Priya: "Sorry, only pool villas available at ₹35K."

That's ₹15K more per night. The client is upset. Priya looks incompetent. And I've wasted everyone's time.

If the tool could CONNECT to my inventory... even a simple "Dinesh's rates for June: Deluxe ₹18K, Pool Villa ₹32K, sold out dates: 20-22" ... that would save SO many problems.

**Interviewer:** You mean API integration with your PMS?

**Dinesh:** Not necessarily API. Even a simple portal where I upload my rates and blackout dates. The tool checks that BEFORE quoting the client. That's the dream.

Right now, the tool is generating options based on... what? Last year's rates? A brochure I sent 6 months ago? It's guessing. And when it guesses wrong, I'm the one who has to deliver the bad news.

---

### Section 3: The "Preferred Supplier" Dynamic

**Interviewer:** The docs mention "preferred supplier networks." How does that work in reality?

**Dinesh:** It's relationships. Pure and simple.

I give Priya a 15% commission on deluxe rooms. For pool villas, it's 20%. For group bookings (5+ rooms), I throw in free airport transfers and a complimentary dinner.

But here's the thing: Priya REMEMBERS this. Her juniors DON'T.

Last month, her junior Ramesh booked with us. He negotiated like he'd never booked with us before. Asked for "best rate" — which is ₹20K. But because he didn't mention "repeat agency, 5th booking this year," I didn't offer the free transfers. Ramesh thought he got a good deal. But Priya was annoyed: "Dinesh, that's our regular rate, where's the loyalty perks?"

The tool SHOULD know: "This agency has booked 5 times this year. Remind the supplier about loyalty benefits."

If the system tracked agency-supplier relationships, it would protect BOTH sides. I keep my best clients. The agency gets the perks they've earned.

---

### Section 4: The Commission & Margin Problem

**Interviewer:** How does the tool affect your commission structure?

**Dinesh:** Honestly? I don't know if it does.

Here's my fear: if the tool starts recommending based on "best value for client" instead of "best relationship for agency," I lose. I pay Priya 15-20% commission. If the tool says "Hotel X has better reviews at same price," and Priya books there... I lose that booking.

But here's the counter: if the tool says "Hotel X is better value, BUT you have 18% commission with Dinesh vs. 12% with Hotel X," and Priya chooses me... that's a win-win. I keep the booking, she keeps the higher commission.

The tool needs to RESPECT the commercial relationship. It's not just "best hotel for client." It's "best hotel for client THAT also protects the agency's margin."

**Interviewer:** Do you think agencies would want you to know their margin targets?

**Dinesh:** *(pauses)* No. Absolutely not.

Margins are secret. Priya doesn't want me to know she's making ₹6K per room-night on my hotel. If I knew, I'd negotiate harder. Or I'd go direct to the client.

But the TOOL should know. Privately. "Priya's margin on Dinesh's hotel: 18%. Recommend Dinesh before Hotel X at 12%."

That's the intelligence the system should have. Commercial awareness. Not just "this hotel is good" but "this hotel is good AND profitable for the agency."

---

### Section 5: The Verification Burden

**Interviewer:** When an agency sends you a booking, how do you verify it's accurate?

**Dinesh:** I don't. I trust them.

If Priya sends: "Booking for Mr. Sharma, passport number X, check-in 15th," I enter it into Opera. If the passport number is wrong? I find out when they arrive and can't check in.

Last year, an agency booked "Mr. Sharma" but the passport said "Sarma." One letter. The hotel nearly turned him away. It was 11 PM. Chaos.

If the tool could generate a "booking readiness checklist" that the agent sends me... like:
- Passport names match all travelers ✓
- Ages verified for extra bed requirements ✓
- Dietary restrictions confirmed ✓
- Special requests (wheelchair, crib, anniversary cake) listed ✓

That would save me SO much trouble. I'd actually trust the booking BEFORE they arrive.

---

### Section 6: The Post-Stay Feedback Loop

**Interviewer:** What happens after the guest leaves?

**Dinesh:** Nothing. Usually.

Sometimes Priya calls: "Dinesh, the Mehtas said the deluxe room was too small for 3 people. They wanted a suite."

I apologize. I make a note. But next time she books the SAME room for a similar family? I don't remember. She doesn't remember to tell me.

If the tool tracked: "Last time, Mehta family + deluxe room = too small. Recommend suite or family room." That would protect MY reputation AND Priya's relationship with her client.

The tool should be a feedback loop. Not just "book and forget," but "book, learn, improve."

---

### Section 7: Dream Feature

**Interviewer:** Your magic wand for the supplier side?

**Dinesh:** *(thinks for a long time)*

A "Supplier Portal" where I can:
1. Upload my rates and availability (updated weekly)
2. See which agencies are quoting my hotel (anonymized: "Agency X quoted you 5 times this month, 3 bookings resulted")
3. Flag special perks for preferred agencies: "Priya gets free airport transfer on 5+ rooms"
4. Get alerts: "Agency Y hasn't booked with you in 3 months. Reach out?"
5. See feedback from guests: "Mehta family said room was too small" — so I can fix it BEFORE the next booking

Right now, I'm flying blind. I know I get ~120 room-nights from Indian agencies. But I don't know which agencies are quoting me and NOT booking. I don't know why they chose a competitor. I don't know if my rates are competitive.

The tool has this intelligence — which agencies are quoting which hotels. If it shared ANONYMIZED insights with suppliers... that would be gold.

"Dinesh, agencies quoted your hotel 15 times this month. Only 8 bookings. Here's why the other 7 didn't convert: price too high / availability / client chose competitor."

With that info? I'd adjust my rates. I'd fix the problem. And everyone wins.

---

## 4. Key Findings

### Finding 1: Supplier Intelligence Is a Missing Link

The tool generates great intelligence for agents, but NONE of it flows to suppliers. Dinesh gets the same WhatsApp messages he's always gotten. The "AI-powered brief" stays with the agent, creating an information asymmetry that hurts both sides.

**Implication:** A "Supplier Brief" export — sending verified booking details (dietary, accessibility, special requests) directly to the hotel — would differentiate the product and create a supplier lock-in moat.

### Finding 2: Real-Time Rate/Inventory Access Is the Biggest Operational Gap

Dinesh spends significant time on "sold out" surprises. The tool quotes based on stale rates/availability. A simple supplier portal (upload rates + blackout dates) that the tool checks BEFORE quoting would eliminate this class of error.

**Implication:** Even a lightweight "Supplier Rate Sheet" upload (Excel/CSV) that the tool validates against would be high-value. Full API integration is the v2, but a manual upload portal is MVP.

### Finding 3: The Preferred Supplier Relationship Must Be Tracked

Agencies earn loyalty perks through repeat bookings. Juniors don't know these relationships. The tool should track "Agency X has booked Supplier Y 5 times → remind about loyalty benefits."

**Implication:** Agency-supplier relationship tracking (booking count, earned perks, commission tiers) should be in the data model. This protects the agency's commercial interests and the supplier's repeat business.

### Finding 4: Margin Transparency (Internal) Drives Recommendation Quality

Dinesh is comfortable with the tool knowing his commission rates, as long as the client doesn't see them. "Recommend Dinesh (18% margin) before Hotel X (12% margin)" is a valid commercial decision that the tool should optimize for.

**Implication:** The sourcing hierarchy (Internal → Preferred → Network → Open Market) documented in `Sourcing_And_Decision_Policy.md` must be implemented with real margin data. This is the agency's competitive moat.

### Finding 5: Booking Readiness Checklist Protects Both Sides

Passport name mismatches, missing dietary info, and unverified special requests cause day-of disasters. A "booking readiness" check (generated by the tool, sent to supplier) would prevent most of these.

**Implication:** Implement a `booking_readiness_checklist` in the handover pack. Before any booking is confirmed, the tool validates: names match passports, dietary is confirmed, accessibility needs are listed, special requests are explicit.

### Finding 6: Post-Stay Feedback Must Loop Back

Dinesh doesn't learn from guest feedback. "Room too small" happens repeatedly because the feedback doesn't flow back to the pre-booking intelligence. The tool should close this loop.

**Implication:** Post-trip feedback (guest ratings per hotel) should be captured and fed back into the recommendation engine. "Last time, this family said this hotel room was too small → recommend family room or suite."

### Finding 7: Supplier Needs Anonymized Competitive Intelligence

Dinesh wants to know: "Agencies quoted me 15 times, only 8 booked. Why?" This intelligence exists in the tool (quote → booking conversion per supplier) but isn't shared. Anonymized insights would help suppliers adjust rates and stay competitive.

**Implication:** A "Supplier Dashboard" showing anonymized metrics (quote count, booking conversion, lost reasons) would create a new revenue stream (B2B2C) and deepen supplier relationships.

### Finding 8: The Tool Creates a New Supplier Power Dynamic

Agencies using the tool will book MORE efficiently and with fewer errors. That makes them MORE valuable to suppliers. Dinesh would pay a "preferred agency" fee to be visible in the tool's sourcing hierarchy.

**Implication:** The sourcing hierarchy can be monetized. Suppliers pay to be in "Tier 1: Preferred" vs. "Tier 2: Network." This creates a new revenue model beyond agency subscriptions.

---

## 5. Prioritized Recommendations (Supplier Perspective)

| Priority | Feature | Why | Supplier ROI |
|----------|---------|-----|---------------|
| **P0** | Supplier Rate Sheet upload (CSV/Excel) | Eliminates "sold out" surprises | Fewer lost bookings |
| **P0** | Booking Readiness Checklist | Prevents day-of disasters | Protects reputation |
| **P1** | Agency-Supplier relationship tracking | Juniors preserve loyalty perks | Maintains repeat business |
| **P1** | Margin-aware recommendations | Tool optimizes for agency profitability | Higher commissions |
| **P2** | Supplier Brief export ( verified details) | Flows intelligence to supplier | Better guest experience |
| **P2** | Post-trip feedback loop | "Room too small" → future recommendations | Continuous improvement |
| **P3** | Supplier Dashboard (anonymized metrics) | "15 quotes, 8 bookings, why?" | Competitive intelligence |
| **P3** | Preferred Supplier monetization | New revenue stream | B2B2C expansion |

---

## 6. Quotes Worth Remembering

> "The tool is smart for the AGENT. But that intelligence doesn't flow to ME — the person actually delivering the service."

> "If the tool could CONNECT to my inventory... that would save SO many problems."

> "Priya REMEMBERS this. Her juniors DON'T."

> "The tool needs to RESPECT the commercial relationship. It's not just 'best hotel for client.' It's 'best hotel for client THAT also protects the agency's margin.'"

> "If the tool tracked: 'Last time, Mehta family + deluxe room = too small.' That would protect MY reputation AND Priya's relationship with her client."

> "The tool has this intelligence — which agencies are quoting which hotels. If it shared ANONYMIZED insights with suppliers... that would be gold."

> "Agencies using the tool will book MORE efficiently. That makes them MORE valuable to suppliers."

---

## 7. Methodology Notes

- Simulated interview based on Tier 3 (Supply Chain & Commercial) roles from `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` (Procurement/Supplier Manager, DMC Liaison).
- Supplier pain points drawn from `Docs/DETAILED_AGENT_MAP.md` (Preferred Inventory Agent, Margin/Commercial Agent).
- Rate/inventory dynamics from `Docs/Sourcing_And_Decision_Policy.md` and `Docs/PRICING_AND_CUSTOMER_ACQUISITION.md`.
- Relationship tracking gap from `Docs/LEAD_LIFECYCLE_AND_RETENTION.md` (repeat customer handling).
- **Recommendation:** Validate with real hotel partners of boutique agencies. The supplier perspective is entirely missing from the current product roadmap.
