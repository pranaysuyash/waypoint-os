# Simulated Customer Interviews — 27 April 2026

## Purpose

This document contains simulated customer interviews grounded in the repository's existing product strategy, persona definitions, and UX research artifacts. The goal is to convert the current product assumptions into realistic persona-driven interview outputs that can guide product decisions, priorities, and messaging.

> Note: These are simulated interviews based on repo evidence, not raw transcribed customer calls.

## Sources Used

- `Docs/PRODUCT_VISION_AND_MODEL.md`
- `Docs/UX_DASHBOARDS_BY_PERSONA.md`
- `README.md`
- `frontend/src/app/page.tsx` marketing persona copy
- `memory/HOLISTIC_PROJECT_ASSESSMENT.md`
- `Docs/GTM_AND_DATA_NETWORK_EFFECTS.md`

---

## Persona 1 — Priya Patel, Solo Agent

**Role:** Solo Advisor / Owner-Operator

**Company:** Boutique travel consultancy, 2 people total

**Primary Job to Be Done:** Convert messy inquiry threads into a clear proposal fast, while preserving margin and avoiding follow-up churn.

**Interview Summary**

Priya runs the agency alone most of the day. She wants to spend less time reading WhatsApp notes and more time writing proposals that feel personal. She is constantly worried that she will miss a requirement because the lead was unclear.

### Excerpted Interview

**Interviewer:** "Walk me through your day when a new client reaches out."

**Priya:** "Usually it starts with a screenshot of a WhatsApp chat, or a forwarded email. I have to dig through the thread, pull out the dates, the budget, the family mix, and then I still feel like I am guessing. If I miss the fact that the father has knee pain, I will propose a walking-heavy plan and have to rework it later."

**Interviewer:** "What frustrates you the most in that process?"

**Priya:** "The stupid, repetitive stuff. I already know the rules: kids need a slower pace, maybe a pool near the room, don't book that exact train if the arrival is after 10pm. But I have to rebuild that context every time. I wish the system would just say: `This lead looks like a family with kids + elderly parent. Ask: 1) exact party makeup, 2) walking tolerance, 3) preferred meal style.`"

### Top Pain Points

1. **Messy lead intake** — WhatsApp/email threads are inconsistent, and key details are hidden inside conversation noise.
2. **Rebuilding context every time** — product preferences, repeat-customer history, and service constraints are not captured reliably.
3. **Late blockers** — surprises like visa issues, budget mismatch, or pacing problems surface after the proposal is already drafted.

### Desired Outcomes

- A clean brief from the first inquiry
- Automatic question prompts for missing but mission-critical constraints
- Proposal options that feel personalized without manual repetition
- Faster first response time

### Language and Quotes

- "I want the system to *read my lead for me*, not make me do the reading."
- "My job is not just booking; it's making sure the client doesn't regret the trip."
- "I need something that knows my suppliers and my preferred packages."

### Product Implications

- Prioritize the **Intake / Discovery** workflow for solo agents
- Show **hard blockers** early and let them ask follow-up questions quickly
- Surface **repeat-customer memory** and previous trip snippets
- Keep the workspace fast and customer-context-first

---

## Persona 2 — Arjun Rao, Agency Owner

**Role:** Agency Owner / Operations Lead

**Company:** Small agency with 8–12 staff

**Primary Job to Be Done:** Maintain quality across the team, spot risky deals before they hit the customer, and ensure the agency earns the right margin.

**Interview Summary**

Arjun does not work every trip himself. His job is to make sure the team does not lose money or reputation. He needs visibility into the pipeline, quick signals for when deals need review, and a way to limit junior mistakes without micromanaging.

### Excerpted Interview

**Interviewer:** "What keeps you up at night about the business?"

**Arjun:** "I worry about the junior team doing the right thing. They can write a nice itinerary, but if they don't catch a visa rule, or if they plan a 10-hour road trip with kids, I am the one answering the complaint. I need to know which trips need my eyes before they go to the customer."

**Interviewer:** "What do you expect from a system like this?"

**Arjun:** "Not magic. Discipline. Give me the trips that are risky or high-value, not every single email. I want a dashboard that says: `Review these 5 trips -- family with seniors, post-COVID visa risk, peak-season budget gap.` Then I can sign off quickly."

### Top Pain Points

1. **Quality drift** — junior agents proposal details vary widely.
2. **Risk visibility** — problems only appear after bookings are sent.
3. **Margin leakage** — good-looking options that leave no business for the agency.

### Desired Outcomes

- A **pipeline summary** that highlights risk and owner review items
- A way to **surface exceptions** rather than review every file
- Confidence that the system is using the agency’s preferred suppliers first
- Alignment across team on what “good enough” looks like

### Language and Quotes

- "I don't want to read every itinerary; I want to see exceptions."
- "The system should think like my best agent, not like a generic travel search engine."
- "If a trip is complicated, I want the rationale, not just a pretty PDF."

### Product Implications

- Build the owner view around **pipeline + risk signals**
- Make **review queues** explicit and easy to triage
- Encode the preferred-supplier hierarchy and margin-aware sourcing logic
- Provide an audit trail or reason summary for owner approvals

---

## Persona 3 — Nisha Mehta, Junior Agent

**Role:** Junior Agent / Trainee

**Company:** Growing boutique agency with 15 staff

**Primary Job to Be Done:** Learn agency judgment while handling inquiries safely, and deliver proposals without needing senior intervention for every case.

**Interview Summary**

Nisha is still learning the agency playbook. She wants guidance, not hand-holding. She needs the system to tell her what to ask, what to avoid, and where she should escalate.

### Excerpted Interview

**Interviewer:** "What do you need support with when you are working on a trip?"

**Nisha:** "I know the basics, but I still get confused when the ask is vague. Last week I got an inquiry asking for 'something nice near the beach' for a family of 6 and I didn't know whether to push for Sri Lanka or Goa. I also worry that I am missing service-level expectations."

**Interviewer:** "How would you like the tool to help you?"

**Nisha:** "Show me the gaps. Say: `Missing: exact party mix, preferred travel style, medical constraints, budget realism.` Then give me the follow-up text I can send. Also, if I choose an itinerary, tell me why this is the safest choice for this client."

### Top Pain Points

1. **Unclear briefing** — leads are not structured enough for confident first drafts.
2. **Lack of guardrails** — unsure when to escalate or when something is okay.
3. **Learning by doing** — needs feedback built into the workflow.

### Desired Outcomes

- A **guided intake** and question prompt list
- Clear escalation triggers and “safe/unsafe” signals
- Explanations of why recommendations were chosen
- Faster independent work with less senior review workload

### Language and Quotes

- "I need the tool to teach me while I work."
- "If it can say `This is high risk because...`, I can learn faster." 
- "I don't want to guess margins or supplier reliability."

### Product Implications

- Include coaching language in the workbench for junior agents
- Surface **why** a trip is flagged or safe, not just what to do
- Build escalation heuristics and review handoff flows
- Keep the workspace accessible while preserving owner controls

---

## Persona 4 — Sunita Sharma, Traveler

**Role:** End Customer of the agency

**Profile:** Family trip planner for a 4-person family, 35–45 years old

**Primary Job to Be Done:** Get a reliable, comfortable vacation plan without having to manage the details herself.

**Interview Summary**

Sunita is not the buyer of the SaaS product, but she is the ultimate customer whose needs the agency must satisfy. Her trust depends on the agency producing a clean, accurate itinerary and handling the paperwork.

### Excerpted Interview

**Interviewer:** "What do you worry about when booking through a travel agent?"

**Sunita:** "I worry that the agent will forget that my father needs lower walking, or that they will propose hotels too far from the main attractions. I also don't want to get messages from five different vendors. I want someone to make it easy."

**Interviewer:** "What makes you recommend an agent to a friend?"

**Sunita:** "If they send a plan that feels like it was made for us: right dates, right pace, right budget, and they don't ask ten times for the same thing. If the first draft is good, I feel confident."

### Top Pain Points

1. **Unclear communication** — too many follow-up questions frustrate her.
2. **Mismatch of trip style** — proposals that look generic or too luxury/too cheap.
3. **Operational chaos** — multiple confirmations from different vendors make her anxious.

### Desired Outcomes

- A smooth proposal with clear options and rationale
- Minimal back-and-forth once the brief is set
- Confidence that the agency knows their family and constraints

### Language and Quotes

- "I want the agent to feel like they understand my family."
- "Please don't ask me again for the budget, I already told you."
- "I want one plan, not three random ideas."

### Product Implications

- Ensure traveler-facing output is clean, polished, and avoids internal uncertainty
- Keep the agency workflow from leaking operational details to the traveler
- Support a handoff that surfaces only what the traveler needs to know

---

## Cross-Persona Findings

### Common Themes

- **Messy intake is the root cause.** All three agent personas suffer when the first inquiry is not structured.
- **Visibility and review are different problems.** Solo agents need rapid action; owners need risk filters; juniors need coaching.
- **Trust is built on predictable operational fit.** The product must prioritize preferred supplier logic and agency playbook compliance.
- **Traveler confidence comes from clarity.** The internal system can be complex, but traveler output must remain simple.

### Opportunity Areas

1. **Intake assistant** — prioritize smart follow-up question generation and hard blocker surfacing.
2. **Owner review queue** — a focused pipeline view showing only trips that require escalation.
3. **Junior agent coaching** — embed rationale and safe/unsafe signals into the workbench.
4. **Traveler-safe output guardrails** — keep the end-customer experience polished while preserving internal judgment.

---

## Recommended Research Next Steps

1. Validate these simulated interviews with 3 real agency owners, 3 solo agents, and 2 junior agents.
2. Record actual verbatim language for the highest-priority themes above.
3. Compare the proposed interview notes against the repo’s existing persona scenarios and adjust the product assumptions where they diverge.
4. Build a small research artifact in `Docs/personas_scenarios/` capturing real interview quotes and priority gaps.
