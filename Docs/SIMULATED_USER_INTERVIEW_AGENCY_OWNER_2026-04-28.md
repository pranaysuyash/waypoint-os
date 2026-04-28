# Simulated User Interview: Agency Owner — Multi-Agent Scaling

**Date:** 2026-04-28
**Format:** Simulated depth interview (role-played)
**Duration:** ~55 minutes (simulated)
**Interviewer:** Product Researcher
**Participant:** "Rajesh" — Agency Owner (Persona P2)

---

## 1. Participant Profile

| Attribute | Detail |
|-----------|--------|
| **Name** | Rajesh Kapoor (pseudonym) |
| **Age** | 47 |
| **Location** | Delhi NCR, India |
| **Role** | Founder & Owner, "Kapoor Travels" |
| **Experience** | 18 years in travel; started as an airport counter agent |
| **Team Size** | 14 people — 9 planners, 2 visa specialists, 1 finance, 2 operations |
| **Active Clients** | ~300 per year across the team |
| **Specialization** | Europe, Southeast Asia, Middle East honeymoons |
| **Tech Stack** | Tally for accounting, WhatsApp groups per agent, Excel for tracking, Amadeus GDS |
| **Annual Revenue** | ~₹2.5Cr (growing 15-20% YoY) |
| **Biggest Frustration** | "I can't grow without losing control. Every new hire takes 6 months to become useful." |

---

## 2. Interview Scenario

**Context:** Rajesh has been evaluating the Agency OS product for his team. He tested it personally for a week, then rolled it out to 3 agents (1 senior, 2 juniors) for a 3-week pilot. This interview captures his assessment at the end of the pilot.

---

## 3. Interview Transcript

### Opening: The Scaling Dilemma

**Interviewer:** Rajesh, tell me about the moment you realized you had a scaling problem.

**Rajesh:** It was about two years ago. We had just lost the Oberoi account — a family that had been booking with us for 8 years. They called me directly and said, "Rajesh, your junior sent us a honeymoon itinerary with activities that start at 7 AM. We're honeymooners. We're not waking up at 6:30 on vacation." I was embarrassed. I had personally planned their last 4 trips. But I was traveling myself, so I handed them to a junior. The junior didn't know them. Didn't know that Mrs. Oberoi likes to sleep in. Didn't know they always book suites, never standard rooms.

I realized: every relationship I've built over 18 years lives in my head. My team can't access it. And I can't personally handle 300 clients anymore. I'm the bottleneck AND the single point of failure.

**Interviewer:** What have you tried to solve this?

**Rajesh:** Three things. First, I tried a CRM. Zoho. Spent ₹40,000 and 2 months setting it up. Nobody used it after the first week. Too many fields, too much friction. My agents work on WhatsApp, not in Zoho.

Second, I created WhatsApp groups per client. Agent + me + client. That way I could supervise. But it became chaos — I was in 47 WhatsApp groups. My phone was unusable.

Third, I tried standardizing templates. Every proposal had to follow a format. Every client intake had a checklist. That lasted about a month. Juniors would fill in the template but miss the nuance — they'd check "family trip" but not notice the client mentioned a knee problem in passing that affects the whole itinerary.

The fundamental problem is: I can't be everywhere, and my juniors don't have my experience. I need a way to embed 18 years of knowledge into the system.

---

### Section 1: Quality Control at Scale

**Interviewer:** How do you currently review your agents' work?

**Rajesh:** With great difficulty. *(laughs)*

The ideal process is: agent creates proposal → I review → I approve → it goes to client. Reality: I review maybe 30% of proposals. The rest go directly from agent to client because I simply don't have time. And the 30% I review — I catch things, but I catch them AFTER they're already drafted. The agent has already spent 2-3 hours on it. If I say "this doesn't work," those hours are wasted.

Last month, my junior Ramesh quoted a family a Singapore package. He included Universal Studios for a family with a 2-year-old. A 2-year-old can barely go on any rides. The parents would have paid ₹15,000 in tickets to push a stroller around. I caught it in review, but Ramesh had already spent 3 hours building the proposal. Now I've wasted his time AND my time.

What I really need is the system to catch these things BEFORE the agent starts building. "Hey, this family has a toddler — here are the toddler-suitable activities in Singapore." That's the kind of intelligence I'm looking for.

**Interviewer:** So you need the system to act as a pre-check, not a post-check.

**Rajesh:** Exactly. I don't want to review proposals. I want proposals to be good enough that I don't need to review them. And for the ones that do need review, I want the system to flag them — "This one needs owner attention because X, Y, Z." Right now I'm either reviewing everything (no time) or reviewing nothing (quality suffers). I need the machine to triage for me.

---

### Section 2: Junior Training and Ramp-Up

**Interviewer:** How long does it take a new hire to become productive?

**Rajesh:** Six months to be barely useful. One year to be independent. Two years to be good. That's the honest answer.

The first month, they shadow me or a senior. Second month, they handle very simple requests — domestic trips, fixed packages. By month three, they start handling international inquiries, but I review everything. Month six, they can handle maybe 40% of inquiries independently. By month twelve, maybe 70%.

But here's the thing — most juniors quit within 18 months. The job is harder than they expected. They get frustrated. They feel stupid because they keep making mistakes. I invest a year training someone, and they leave. That's the real cost.

**Interviewer:** What if the tool could accelerate that?

**Rajesh:** That's what sold me on trying this. If the system can guide a junior through the right questions, flag common mistakes before they happen, and show them WHY something is wrong — not just "this is wrong" — then maybe I can get someone to 70% independence in 4 months instead of 12.

But here's what I observed in the pilot. Amit — one of my juniors — used the tool for 3 weeks. His intake quality improved immediately. He was asking better questions. His proposals were... okay. Better than before, but still not senior-level. The gap is in the details. He can ask the right questions, but he doesn't know what to DO with the answers yet.

**Interviewer:** Can you give an example?

**Rajesh:** Sure. Client says: "We want to go to Bali, family of 4, budget ₹3.5 lakh." The tool correctly extracts the intent and asks follow-ups. Client clarifies: "Kids are 5 and 8, we want a pool villa, we're vegetarians." Amit now has all the right information. But here's where the experience gap shows:

A senior knows that in Bali, "vegetarian" often means different things to Indonesian restaurants vs. Indian tourists. A senior knows that pool villas in Seminyak are amazing but the beach there has a dangerous rip current — not great for a 5-year-old. A senior knows that ₹3.5L for a pool villa family trip to Bali is tight in peak season but great value in shoulder season.

The tool gave Amit the right questions. It didn't give him the judgment to evaluate the answers. That's the harder problem.

---

### Section 3: Commercial Visibility

**Interviewer:** Let's talk about money. How do you track margins?

**Rajesh:** *(long pause)* In Tally. And in my head.

Here's how it works. When a trip is booked, my finance person enters the cost and the selling price into Tally. But Tally doesn't tell me margins in real-time. It tells me at the end of the month, when the P&L is ready.

By then, it's too late. If Ramesh gave away a 20% discount on 5 trips this month, I find out 3 weeks later. I can't un-discount. The money is gone.

And there's a bigger problem. My agents don't know the actual cost of things. They know the selling price. But they don't know what I pay the hotel, what the DMC charges me, what the net margin is. I keep that information close because I don't want agents to start their own agencies and take my clients. *(laughs)* That's the reality of this business.

So when an agent discounts, they don't know if they're discounting into my margin or into their commission. They can't make good pricing decisions because they don't have pricing data.

**Interviewer:** What would ideal commercial visibility look like?

**Rajesh:** Three levels. Level one: I see a dashboard that says "this month's trips, expected margin per trip, flag if any trip is below your minimum margin." Level two: the system alerts the agent BEFORE they discount — "You're about to go below 12% margin on this trip. Owner approval required." Level three: over time, the system learns which destinations, which hotel categories, which trip types are most profitable and recommends those first.

But — and this is important — my agents should NOT see the actual cost numbers. They should see "margin health: green/yellow/red." I need the intelligence without exposing the supply chain.

---

### Section 4: Agent Workload and Assignment

**Interviewer:** How do you assign leads to agents today?

**Rajesh:** Gut feel. Whoever is least busy when the inquiry comes in. Or if I know the client, I assign to the agent who handled them before. But often, the inquiry comes in on WhatsApp at 10 PM and whoever sees it first picks it up.

This leads to two problems. One: workload imbalance. Priya — my best agent — always has 20+ active trips. New agents have 3. Priya is burning out, and new agents aren't getting enough reps to improve. Two: mismatch. A Europe specialist gets a Bali inquiry and takes twice as long because they're not familiar with the destination.

**Interviewer:** What would intelligent routing look like?

**Rajesh:** The system should know: this is a Europe family trip with a ₹5L budget. Who in my team handles Europe family trips? Who has capacity? Who has handled this specific client before? Route it there.

And I want to see the balance. "Priya has 22 active trips. Ramesh has 4. Suggest routing the next 5 leads to Ramesh unless they're high-value." That kind of thing.

---

### Section 5: The Pilot Assessment

**Interviewer:** After the 3-week pilot, what's your honest verdict?

**Rajesh:** The intake and questioning part is genuinely good. My juniors ask better questions. My seniors save time on the initial analysis. That's real value.

But for my specific problem — scaling quality across a team — it's not enough yet. Here's what I need that I don't have:

1. **Quality gates before client delivery.** The system should flag "this proposal has a 90% confidence score — send directly" or "this one is 60% confidence — needs senior review." That's my scaling bottleneck.

2. **Commercial guardrails.** If an agent is about to quote below my minimum margin, stop them. Require my approval. That's my revenue protection.

3. **Workload dashboard.** Who has how many trips? What stage are they in? Who needs help? That's my operational visibility.

4. **Agent performance over time.** How is each agent improving? Which types of trips do they handle well? Where do they need training? That's my management tool.

5. **Knowledge transfer.** When Priya goes on leave, can another agent pick up her 15 active trips with full context? Today, that's a 2-hour handoff meeting per trip. I need the system to BE the handoff.

**Interviewer:** Would you pay for the current product?

**Rajesh:** Not at team scale. For a solo agent? Yes, the ₹1,500 price point makes sense. For my team of 14? I'd need the features I just described. If you build those, I'd pay ₹15,000-25,000 per month. Because the ROI is obvious: if I can get juniors productive in 4 months instead of 12, that's ₹2-3L saved per hire in training costs. If I prevent 5 margin-leak incidents per month, that's ₹50K-1L saved. If I can take on 50 more clients per year without hiring, that's ₹10-15L additional revenue.

But I won't pay for potential. I'll pay for results.

---

### Section 6: The Dealbreaker Question

**Interviewer:** What would make you rip this out and go back to spreadsheets?

**Rajesh:** One thing. If my agents start relying on it and it gives wrong information. If the system says "no visa needed for Vietnam for Indian passport holders" — which is wrong, you need an e-visa — and one of my clients gets turned away at the airport? That's not a bug. That's a lawsuit. That's my reputation destroyed.

I need to trust the system more than I trust my most junior agent. And my most junior agent still checks Google when they're unsure. The system needs to be more reliable than Google, not less.

The second thing — if my clients ever feel like they're talking to a machine. I've built 18 years of relationships on trust and personality. If the system makes my agents sound robotic or generic, that kills the personal touch that differentiates us from MakeMyTrip.

---

### Section 7: Dream Feature

**Interviewer:** Your magic wand feature?

**Rajesh:** A "Shadow Rajesh" mode. The system watches every decision I make — which hotels I pick and why, which ones I reject and why, how I handle difficult clients, how I price tricky situations. Over time, it builds a model of MY judgment. Then, when a junior is handling a similar situation, it doesn't just give generic guidance — it says "Rajesh would probably suggest X because Y." My expertise, available 24/7, without me being in 47 WhatsApp groups.

That's the real OS. Everything else is just a tool. This would be a force multiplier for my entire team.

---

## 4. Key Findings

### Finding 1: The Buying Decision Is Different for Owners vs. Agents

Solo agents buy for personal productivity. Agency owners buy for team leverage. Rajesh doesn't need to save his own time — he needs his 14 people to be 20% better. The value proposition must speak to team-level ROI, not individual productivity.

**Implication:** Enterprise/team pricing tier needs its own narrative: "Make your juniors productive in 4 months instead of 12" — not "Save 2 hours per day."

### Finding 2: Quality Gates Are the Scaling Prerequisite

Rajesh can't scale because he can't delegate quality control. He needs automated pre-checks (confidence scores, suitability warnings, margin guards) more than he needs better intake. Intake is solved; quality assurance is the bottleneck.

**Implication:** Implement confidence-gated approval workflow. Trips above threshold go direct; trips below threshold route to owner/senior review. This is the single highest-value feature for the team tier.

### Finding 3: Commercial Opacity Is Intentional — Design Around It

Rajesh deliberately keeps cost/margin data hidden from agents. The system must respect this information asymmetry. "Margin health: green/yellow/red" for agents; full P&L for owners only. Role-based data access is a trust requirement.

**Implication:** Role-based access control isn't just a nice feature — it's a business requirement. Agents see "margin health," owners see actual numbers. This must be designed from day one for the team product.

### Finding 4: Knowledge Transfer Is the Hidden Crisis

When a senior agent goes on leave or quits, the agency faces catastrophic knowledge loss. The system needs to be the institutional memory — not just trip data, but decision patterns, client preferences, and judgment heuristics.

**Implication:** "Shadow Mode" (learning from senior decisions) should be prioritized as a differentiating feature. Even a simple version (log what the senior changes in proposals and why) would be valuable.

### Finding 5: Factual Accuracy Is Non-Negotiable — It's Existential Risk

A wrong visa requirement or an incorrect hotel recommendation isn't a "bug" — it's a potential lawsuit and reputation destroyer. The tolerance for factual errors in this domain is zero.

**Implication:** Every factual claim generated by the system (visa rules, hotel status, pricing) must have a confidence indicator and human-in-the-loop verification for anything below 95% confidence.

### Finding 6: The Pricing Model Must Be Tiered by Team Size

Rajesh won't pay solo-agent pricing for 14 seats, and he won't pay enterprise pricing for features he doesn't use. He needs a middle tier: ₹15-25K/month for teams of 5-20, with owner-specific features (commercial dashboards, quality gates, agent performance).

**Implication:** Three-tier pricing: Solo (₹1-1.5K), Small Team (₹5-8K for up to 5 agents), Agency (₹15-25K for up to 20 agents with owner features).

### Finding 7: Intelligent Lead Routing Is Undervalued in Current Roadmap

The current product treats all leads equally. But for multi-agent teams, WHO handles a lead matters as much as HOW it's handled. Routing by specialization, capacity, and client history would immediately improve both quality and agent satisfaction.

**Implication:** Agent assignment model should be designed early — even if the initial implementation is manual assignment, the data model needs to support it from day one.

### Finding 8: The "Shadow Owner" Concept Is the Moat Feature

Rajesh's dream of a system that learns his judgment patterns and makes that expertise available to juniors is the single most compelling feature for the team/agency tier. It addresses the core scaling problem (knowledge trapped in one person's head) directly.

**Implication:** Design and prototype a "Decision Capture" system: every owner edit/suggestion on a proposal is logged with rationale. Over time, this becomes a training corpus for the "Shadow Owner" mode.

---

## 5. Prioritized Recommendations (Owner/Team Perspective)

| Priority | Feature | Why | Owner ROI |
|----------|---------|-----|-----------|
| **P0** | Confidence-gated approval workflow | Scales quality control without scaling Rajesh's time | 10+ hours/week saved on review |
| **P0** | Role-based access (agent vs. owner views) | Protects commercial data while enabling agents | Revenue protection |
| **P1** | Margin health dashboard (owner only) | Revenue leakage visibility | ₹50K-1L/month saved |
| **P1** | Agent performance tracking | Training ROI visibility | Faster junior ramp-up |
| **P1** | Workload distribution view | Balanced utilization | Prevents burnout, better client coverage |
| **P2** | Intelligent lead routing | Better specialization match | Higher conversion per lead |
| **P2** | Decision capture / "Shadow Owner" mode | Institutional knowledge preservation | Reduced key-person dependency |
| **P3** | Knowledge transfer on agent leave/exit | Business continuity | Prevents client churn on turnover |

---

## 6. Quotes Worth Remembering

> "Every relationship I've built over 18 years lives in my head. My team can't access it. And I can't personally handle 300 clients anymore."

> "I don't want to review proposals. I want proposals to be good enough that I don't need to review them."

> "The tool gave Amit the right questions. It didn't give him the judgment to evaluate the answers. That's the harder problem."

> "I won't pay for potential. I'll pay for results."

> "If the system says 'no visa needed' and my client gets turned away at the airport? That's not a bug. That's a lawsuit."

> "A 'Shadow Rajesh' mode — my expertise, available 24/7, without me being in 47 WhatsApp groups."

---

## 7. Methodology Notes

- Simulated interview based on Persona P2 (Agency Owner) from `Docs/PERSONA_PROCESS_GAP_ANALYSIS_2026-04-16.md` and Journey 2 in `Docs/UX_USER_JOURNEYS_AND_AHA_MOMENTS.md`.
- Commercial dynamics drawn from `Docs/PRICING_AND_CUSTOMER_ACQUISITION.md` and `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` (R01: Agency Owner).
- Pilot testing scenario extrapolated from the product's current capabilities (intake/extraction/decision) vs. documented gaps.
- **Recommendation:** Validate with real agency owners who manage teams of 5+ agents. The multi-agent dynamics described here (workload imbalance, information asymmetry, key-person risk) are universal but the specific tolerances may vary.
