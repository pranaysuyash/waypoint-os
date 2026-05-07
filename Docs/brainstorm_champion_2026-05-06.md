# CHAMPION BRAINSTORM: Waypoint OS — The First-Principles Case

**Date**: 2026-05-06
**Role**: Champion (clear-eyed advocate, fighting for the vision from first principles)

---

## 1. START WITH THE PROBLEM

The fundamental structural problem in Indian travel is not "planning is hard" or "agencies are inefficient." Those are symptoms. The problem is this:

**Information asymmetry between the buyer and the seller is structural, uncorrected, and worsening with every passing year.**

The Indian traveler buying a ₹2-5L trip is making the second-largest financial decision of their year (after rent/EMI). They have zero independent verification. They cannot comparison-shop effectively because no two agency quotes are structured the same way. They cannot assess fit because they don't know if Universal Studios works for a 3-year-old until they're standing at the gate with a crying toddler. They cannot detect hidden costs because the quote is a narrative, not an itemized breakdown, and the missing items (transfers, resort fees, visa charges) only surface after commitment.

Meanwhile, the agency is not malicious — they're structurally incentivized to obscure. Margins are hidden in hotel markups. Activities are chosen by availability and commission, not suitability. The 72-year-old grandmother gets a walking tour because that's what the supplier had in inventory, not because it matches her mobility. The agency's expertise — genuine, hard-won, valuable — is trapped in one person's head and decays with every WhatsApp message that gets buried.

This is not a technology problem. It is a market structure problem. And it has existed since before the internet. Travel agents in the 1990s had it. Travel agents on WhatsApp in 2026 have it. Every "innovation" in Indian travel — MakeMyTrip, Goibibo, TravelTriangle, Cleartrip — solved the *booking* layer or the *discovery* layer. Nobody solved the *verification* layer. Nobody built the thing that sits between "someone showed me a quote" and "I believe this quote is fair and fit."

**Why it gets worse every year:**

- More Indian travelers enter the middle class every year (40M+ new upper-middle-class households since 2020). These are first-time international travelers with no baseline for what "good" looks like. They are the most exploitable segment.
- WhatsApp compressed the sales cycle from days to minutes. Agencies now send quotes as WhatsApp messages — narrative, unstructured, impossible to compare. The format that won for convenience lost for transparency.
- Activity catalogs are exploding. Singapore alone adds 5-8 new attractions per year. Bali adds wellness retreats monthly. No human operator can maintain current suitability knowledge across 10+ destinations, 200+ activities, and every age/mobility/dietary combination.
- The gap between what a good agent knows and what a junior agent knows is widening. As agencies scale from 3 to 14 people, the owner becomes the quality bottleneck — exactly as Rajesh described. His knowledge doesn't transfer. His standards don't scale. Every new hire introduces quality risk.

The problem is not that travel is broken. The problem is that the information architecture of Indian travel is a one-way mirror — the agency sees the traveler clearly, and the traveler sees only what the agency reflects. That asymmetry produces bad trips, wasted money, and eroded trust. Nobody has fixed it because fixing it requires occupying the space between both sides simultaneously. That space is empty.

---

## 2. WHY THIS APPROACH WINS ON FIRST PRINCIPLES

The audit wedge + copilot combination has three structural advantages that no existing solution can replicate. Not incremental advantages. Physics advantages.

### Advantage 1: Position advantage — occupying the moment of doubt

Every purchase journey has a moment where the buyer is uncertain. In travel, that moment is specifically when they're holding a quote and deciding whether to commit. This is the highest-value emotional real estate in the entire purchase path — higher than discovery (they're browsing, low intent), higher than booking (they've already decided), higher than post-trip review (too late).

The free audit tool captures this moment. It does not try to generate demand. It does not try to redirect the traveler. It answers the one question that exists at this exact moment: "Is this quote good for me?"

No OTA can do this. OTAs want you to book *their* inventory. Their incentive is not to verify someone else's quote — it's to replace it. No CRM can do this. CRMs sit on the agency side and never see the traveler's original quote from a competitor. No travel community forum can do this — they produce opinions, not structured analysis.

Waypoint occupies the only honest position in the market: "I don't sell you anything. I tell you what's wrong with what someone else is selling you." That position is structurally trustworthy because it has no commercial reason to lie. Credit bureaus don't lend money. Underwriters don't build houses. The audit does not book trips.

### Advantage 2: Asymmetry advantage — seeing both sides of the market simultaneously

A CRM sees what one agency does. An OTA sees what travelers book. Waypoint sees what agencies quote *and* what travelers received. It sits in the structural gap between intent and execution — the place where the quote exists but the booking hasn't happened yet.

This is not a features advantage. It's a physics advantage. You cannot replicate "seeing both sides" from one side. TravelTriangle has 500K trip planning requests — but they're all from the traveler side. They never see what the competing agency quoted. MakeMyTrip has real-time booking pricing — but they never see the agency competitor's quote that the traveler is comparing against. Waypoint's audit tool sees the competitor's quote. The copilot sees the agency's execution. After 12 months of two-sided flow, you have something no single-sided player can build: a corpus of mismatch data — the gap between what was quoted and what was deliverable, across agencies, across destinations, across traveler profiles.

This is the data moat that actually matters, and it's moated not by quantity but by position. It's not "more data than anyone else." It's "data from a position nobody else occupies."

### Advantage 3: The flywheel is real if the audit is real

The skeptic identified that the flywheel is untested. Correct. The executioner rated its compound probability at under 15%. Also correct — for the full vision as described.

But strip it to first principles and the flywheel logic is sound:

1. Traveler uploads quote → this is labeled data (real quote, real destination, real group, real price)
2. Audit generates → this is analysis (suitability, pricing, risk)
3. Traveler clicks "fix this" → this is intent + pre-qualified lead
4. Agency receives pre-qualified lead with audit attached → this is a warm lead with 90% of intake already done
5. Agency delivers better quote → this is commercial value
6. Agency pays for Product A because Product B leads convert → this is revenue
7. More audits make the intelligence better → this makes every subsequent audit more credible → this produces more clicks → loop

Every link in this chain is individually plausible. The question is whether they compound. That's an empirical question, not a logical one. The logic works. The test is whether reality cooperates. But the structural advantage — that the audit tool occupies a position no one else can, that it produces data no one else sees, that it creates warm leads no one else can generate — this is not speculative. This is positional.

---

## 3. WHY THIS FOUNDER

I'll be specific, not generic.

**The founder has operator DNA in Indian travel.** This is not a tech founder who "discovered" the travel vertical. The pre-mortem reveals detailed knowledge of how boutique agencies actually work — the morning triage, the WhatsApp scramble, the ghost window, the quality bottleneck in the owner's head. The Rajesh interview reads like it was conducted by someone who has been in that office. That knowledge is not researchable in a weekend. It comes from proximity.

**The founder can build.** Product A is 70% built with real architecture — multi-agent runtime, extraction pipeline, decision engine, override system, audit trail. This is not a Figma prototype. There's working code. There are edge cases handled (wrong Paris pricing, contradictory toddler cutoffs). The existence of 38 known issues is actually evidence of depth — someone who was building cosmetics wouldn't have found those issues. The founder built enough to discover where the breaks are. That's a builder, not a dreamer.

**The founder has market access.** 50 LinkedIn messages sent, 7-10 calls booked, 14% response rate on cold outreach. The skeptic called this "thin." But 14% on cold B2B outreach in Indian travel — an industry where the default is "we don't take cold calls" — is not thin. It's a signal. More importantly, the founder knows *which* agencies to call. The stratification (3-20 staff, 50-300 trips/month, boutique) is precise. That specificity comes from knowing the market, not from a TAM spreadsheet.

**The specific combination that matters: operator experience × builder skill × Indian market access.** Most Indian travel founders are operators who can't code. Most Indian tech founders building for travel can't navigate a supplier WhatsApp group to save their lives. The founder sits at the intersection of both — they can build the system *and* they can sit in the agency's office and watch it get used. That combination is rare and it's the only combination that can build a product that works for the operator's actual workflow, not the workflow the founder imagines.

Let me be honest about where the founder is weak: B2B sales at scale, consumer marketing, and content curation are all unproven. The 50 LinkedIn messages are a start, not a sales motion. There is no evidence of repeatable customer acquisition. But the first 6 months of this strategy do not require sales at scale — they require the Singapore wedge and 2-5 beta agencies. The founder's demonstrated skills (build, iterate, talk to operators one at a time) are sufficient for the test. The skills the founder lacks matter at scale. Scale comes later.

---

## 4. THE REAL MOAT

The Skeptic says the data moat is a story. The Strategist says it's the strategy. Here is the honest answer: **both are right, at different times.**

The Skeptic is right today. The data moat does not exist. You have 18 hardcoded activities and 8 budget tables. That is not a moat. That is a wiki. TravelTriangle has 500K trip requests. MakeMyTrip has real transaction data. Google has live fares. On data volume, you lose. On data recency, you lose. On data validation, you lose.

The Strategist is right at month 18+. The moat that matters is not volume — it's *positional*. The data moat is real only if you define it correctly:

**The moat is the mismatch corpus.** Not "we have 10,000 itineraries." Everyone has itineraries. The moat is "we have 10,000 pairs — a traveler's received quote AND the audit showing where it was wrong." That pairing — the gap between what was sold and what was deliverable — is data that only exists if you sit between both sides. No CRM has it (they only see the agency's final quote). No OTA has it (they only see what was booked, not what was compared against). The mismatch corpus is the thing no competitor can replicate from their current position.

But this moat only becomes real if:
1. Sufficient volume of audits exists (thousands, not dozens)
2. A feedback loop validates the audits (travelers confirm the audit was accurate, agencies confirm the budget bracket was correct)
3. The data stays current (pricing decays in 30 days; the corpus needs a refresh mechanism)

The Skeptic's critique of the feedback loop is the most dangerous one. Without labeled feedback, each audit is a data point, not a training signal. The honest response: in v1, the feedback loop is manual. The founder reads audit results, calls agencies, asks travelers. This doesn't scale, but it works for the first 500 audits. The feedback loop becomes automated when you add "was this helpful?" to the audit output and track whether Product B referrals convert to bookings. That's a product feature, not a physics impossibility.

**The real moat, in order of construction:**

1. **Month 1-6: Distribution moat.** You are the first tool that travelers use to verify a quote. That position — "the free second opinion" — is a brand position, not a data position. It's fragile but it's real and it's first-mover in a category that doesn't exist yet.
2. **Month 6-12: Workflow moat.** Agencies that adopt Product A build muscle memory, override history, and pipeline data inside it. Switching costs are real. This is the SaaS moat — standard and defensible but not unique.
3. **Month 12-24: Mismatch corpus moat.** After thousands of audit-agency pairs, you have data about pricing gaps, suitability errors, and hidden-cost patterns that no one-sided player can replicate. This is the structural moat. It compounds. It's the one that matters most.
4. **Month 24+: Standards moat.** The Future Self brainstorm saw this clearly: agencies that self-audit adopt your quality rubric as their own. You are no longer competing on features. You are the standard. Standards don't get displaced by the next shiny app.

The honest answer: the moat at month 6 is thin. The moat at month 24 is real. The founder has to survive the gap.

---

## 5. WHY NOW

Three things have changed in the last 2-3 years that make this possible when it wasn't before:

### 1. LLM extraction is now good enough

Two years ago, you could not build Product B. Parsing a travel quote — an unstructured WhatsApp message, a PDF, a screenshot with line items in mixed Hindi-English — required either rigid templates (break on every format change) or manual data entry. LLMs have crossed the extraction threshold. They can pull destination, dates, budget, activities, and group composition from an unstructured quote with 85-90% accuracy today. That accuracy is good enough for a free tool (the traveler can correct the few misses). It was not good enough 2 years ago. The extraction pipeline that would have required months of engineering now works with a well-prompted LLM call and a validation layer.

### 2. Indian traveler behavior has shifted

Three behavioral changes that matter:

- **Price verification is now a social behavior.** Indian travelers don't just ask "is this a good price?" They post it. They share quotes in WhatsApp family groups. They screenshot and ask "is this worth it?" on travel forums. The audit tool fits an existing behavioral pattern — it just makes the verification structured instead of anecdotal.
- **WhatsApp is the operating system.** In 2020, agencies were still partly on email. By 2026, WhatsApp is the entire sales channel for agencies under 20 staff. Product B's intake via WhatsApp-forward or screenshot is not a new workflow. It's the existing workflow, formalized.
- **First-time international travelers are the fastest-growing segment.** 40M+ new upper-middle-class households since 2020. These travelers have no baseline. They've never been to Singapore. They don't know what ₹45K should include. They are the most motivated users of a verification tool because they have the most to lose.

### 3. Agency readiness has reached a tipping point

The Rajesh interview is not an outlier. Boutique agency owners are watching their juniors make mistakes, watching their margins erode, watching their competitors adopt faster tools. The pandemic killed the bottom third of agencies. The survivors are tech-curious but tech-cautious. They will not adopt a CRM (too generic, too much setup). They will not adopt an OTA partnership (they lose the client relationship). But they will try a tool that:
- Makes their existing workflow faster (copilot, not replacement)
- Brings them pre-qualified leads (Product B referrals)
- Doesn't require them to change how they sell (WhatsApp still works)

The window is open because the pandemic forced digital adoption, the survivors are ready for tools, and no current tool serves their specific workflow. That window closes when a well-funded CRM adds AI features and captures this segment by default. That clock is running.

### 4. Regulatory pressure is coming

India's Consumer Protection Act is getting stricter on opaque pricing. The government is pushing for standardized, itemized billing across services. A tool that surface hidden costs and pricing opacity isn't just useful — it's aligned with regulatory direction. This isn't a regulatory moat (anyone can build this), but it means the tailwind is real. The market is moving toward transparency. The audit tool is early, not contrarian.

---

## 6. THE CRITICAL ASSUMPTION

If this fails, it will be because this single assumption was wrong:

**Travelers who are suspicious enough to upload a quote are also motivated enough to switch agencies when the audit confirms their suspicion.**

Everything else is secondary. The extraction works. The intelligence improves. The agencies would adopt if leads came. The flywheel would spin if clicks converted. The entire strategy rests on the behavioral jump from "I know something is wrong with my quote" to "I want a different agency to fix it."

The Skeptic's strongest argument is that this jump doesn't happen — that the traveler uses the audit as negotiation leverage with their existing agent, not as a switching trigger. The 60-70% estimate for "screenshot-and-negotiate" behavior is probably right for the initial cohort.

But here's the case for why the assumption holds *for the right subset*:

- Not every traveler will switch. You don't need every traveler. You need the subset that is genuinely comparison-shopping — the 10-20% who are already evaluating alternatives. For them, the audit isn't leverage; it's ammunition for the switch they were already considering.
- First-time travelers with no existing agent relationship have no one to negotiate with. They are receiving their first quote. The audit is their only second opinion. This is the highest-conversion segment, and it's the fastest-growing segment in Indian travel.
- The emotional arc matters. The audit doesn't just inform — it creates the feeling of "I was right to doubt this." That feeling (recognition, not education, as the Trickster identified) is more motivating than information alone. People act on feelings, not spreadsheets.

The critical assumption is testable. Build the Singapore wedge. Watch what travelers do after the audit. If 5+ out of 200 click "fix this," the assumption has preliminary support. If 0 click, it's wrong. The test is 2 weeks of work and 6 weeks of observation. This is not a faith-based assumption. It's a falsifiable hypothesis. That's the strongest thing that can be said for it.

---

## 7. THE HARD TRUTH

The thing the founder doesn't want to hear but needs to:

**Product A as currently built is not the product agencies will pay for.**

Rajesh said it: "I won't pay for potential. I'll pay for results." His real pain isn't intake — it's quality assurance, margin protection, and operator performance tracking. Product A does intake. Intake is 15% of the job. The other 85% — quality gates, margin guards, workload dashboards, agent performance — isn't built.

The founder has spent months building an intake tool that solves the operator's morning problem (triage) but not the owner's existential problem (quality escaping the business when the owner isn't watching). The owner pays. The operator doesn't. Product A is optimized for the operator. It needs to be optimized for the owner.

This doesn't mean rebuild. It means reframe and extend. Product A's intake automation is the wedge *into* the agency — it proves the AI is competent. But the subscription renewal comes from the owner features: margin leak alerts, quality scorecards, ghost window recovery prompts, junior operator decision audit trails. Those features are not in the 30% remaining on the Product A build list. They're in the 70% that hasn't been scoped yet.

The harder truth: **building Product B might be the fastest path to discovering what Product A should actually be.** Every audit that surfaces "this quote has ₹12K in hidden costs" is telling you what the agency owner needs to see about their own quotes. The audit data defines the quality gate. Build the quality gate from the audit data, not from assumptions about what agencies need. Product B doesn't just acquire travelers — it discovers the owner's real pain by showing what their quotes get wrong.

---

## THE THING MOST PEOPLE MISS ABOUT THIS

**The audit is not a feature. The audit is a category.**

Every person who looks at this product frames it as "a copilot for agencies with a free audit tool for acquisition." That framing makes the audit subservient to the copilot. It makes Product B a funnel, Product A the product.

Flip it. The audit is the category. The copilot is the monetization of the category.

Credit bureaus don't exist to help banks. They exist to verify borrowers. Banks pay for that verification because it reduces their risk. The credit bureau is the central entity. The bank is the customer.

The audit verifies travel quotes. Agencies pay for that verification because it reduces their risk (fewer bad quotes go out, fewer angry clients come back, fewer margin leaks go undetected) and because it brings them leads (travelers who already know what's wrong with their current quote). The audit is the central entity. The agency is the customer.

If the audit becomes the de facto second opinion for travelers — "check your quote before you commit" — it becomes the verification layer of a global $1T+ travel market. Verification layers become standards. Standards become infrastructure. Infrastructure doesn't get displaced by the next shiny app. Nobody displaces the credit bureau by building a better bank.

The copilot matters. It's the revenue engine. But the audit is the gravity well. Every quote in travel eventually passes through a moment of doubt. Capture that moment, and everything else — travelers, agencies, data, intelligence, revenue — orbits you. Miss it, and you're just another CRM competing on feature checklists in a crowded market.

The question is not "should this exist?" The question is "will the founder commit to the narrowest possible test — one destination, one agency, one question — and let the answer determine what comes next?" If yes, this has a real shot. If no, the vision stays a vision.

---

## Addendum: Corrections and Refinements (2026-05-06 Discussion)

### Day-1 Global, Not Deeply Indian
The entire Champion doc frames the opportunity around Indian travel — Indian Consumer Protection Act, Indian middle-class growth, WhatsApp in India, the Indian regulator pushing for transparency, first-time Indian international travelers as the primary segment. The structural analysis (information asymmetry, position advantage, verification layer as category) is market-agnostic. The same dynamics apply to a UK traveler comparing Spain quotes, an Australian comparing Bali quotes, a Canadian comparing Japan quotes. The audit's physics advantage ("I don't sell you anything") holds in every language and currency. The examples and the "why now" section should explicitly acknowledge global applicability while noting that the founder's existing market access (50 LinkedIn messages, 7-10 calls) is India-specific and should be leveraged there first.

### The Flywheel Does Not Route Through Agency's Inbox
The Champion's flywheel in Section 2 (step 3: traveler clicks "fix this" → step 4: "agency receives pre-qualified lead with audit attached") assumes a handoff architecture where Product B routes directly into Product A's dispatch board. This does not exist in the actual model. The correct path: Product B arms the traveler → traveler takes the audit to their existing agent (via "Share with your agent" CTA) → agent either fixes it (without Product A) or sees the Waypoint branding and begins the Product A conversation. The flywheel is B2B2C, not B2C2B. The Champion's Step 4 should read: "Agency sees the audit through the traveler's screenshot → becomes aware of Waypoint → self-audits their own quotes to match the standard → eventually adopts Product A to do this at scale."

### The Feedback Loop Exists — The Champion Didn't Know About It
Section 4 says the feedback loop in v1 is "manual — founder reads audit results, calls agencies." The override system in Product A already provides an automated labeled feedback mechanism. Every time an operator overrides an audit recommendation, that is a labeled data point. The override store is built, tested, and ready. The Champion's honest admission about manual feedback is technically about the consumer side (does the traveler confirm the audit was accurate?), but the agency-side loop is already automated.

### The Credit Bureau Analogy Should Anchor the Synthesis
The Champion's closing framing — audit as category, copilot as monetization, credit bureau as precedent — is the best articulation of the product's structural position across all 8 roles. It should be the organizing thesis of any synthesis artifact. The Skeptic says "the flywheel is untested" and is right. The Executioner says "test the narrow wedge" and is right. But the Champion provides the reason to run the test: because the structural position validates the theory even if the execution is unproven. A credit bureau doesn't prove its model by running a pilot with 3 banks and 200 borrowers — it proves it by occupying a position nobody else can. That's what the audit does.

---

## Round 2: What I Learned

**Date**: 2026-05-07
**After reading**: All 8 role docs + addendums

### What changed or strengthened my position

**1. The flywheel is B2B2C, not B2C2B — and this strengthens the structural position argument.**

My original flywheel (Section 2, Advantage 3) assumed: traveler clicks "fix this" → agency receives pre-qualified lead in Product A inbox. The actual model is: traveler shares audit with their existing agent → agent sees Waypoint branding → agent adopts Product A. This is a stronger structural position, not a weaker one. In the B2C2B model, the traveler has to trust a stranger (a new agency they've never met). In the B2B2C model, the traveler trusts their existing agent — and the agent is the one who encounters the Waypoint brand. The credit bureau analogy holds even better here: credit bureaus don't route borrowers to specific banks. They give borrowers a credit score that any bank can use. The audit gives travelers a quality score that any agent can see. The audit doesn't need a routing mechanism to generate value. It needs a sharing mechanism. And sharing is a behavior travelers already do (screenshots, WhatsApp forwards). The structural position isn't "we connect travelers to agencies." It's "we give travelers a document that makes every agency they share it with aware of our standard." That's the credit bureau position.

**2. Freeform text input is a force multiplier for the "moment of doubt" advantage.**

My Advantage 1 said the audit captures "the moment of doubt" — when the traveler is holding a quote and deciding whether to commit. Freeform text input extends this: the moment of doubt now includes the planning phase, before any quote exists. The traveler thinking "is Universal Studios right for my 2-year-old?" is already in a moment of doubt — they just don't have a quote to upload yet. Freeform text lets them express that doubt immediately, without the friction of finding and uploading a document. This expands the addressable market from "people who received a quote" to "people planning a trip." The position advantage doesn't change — we still occupy the verification layer — but the funnel entrance widens significantly.

**3. The override store validates the feedback loop that the Skeptic said didn't exist.**

Section 4 of my doc was honest: the feedback loop in v1 is manual. The addendum corrected this: Product A's override store is an automated labeled feedback mechanism. Every override is a labeled correction. Every acceptance is implicit validation. The Skeptic's Assumption 5 (intelligence can't compound without labeled feedback) is partially answered: the agency-side feedback loop exists architecturally. The traveler-side feedback (was the audit accurate?) remains unsolved. But half a feedback loop is better than none, and it's substantially better than I originally claimed. The moat construction timeline in Section 4 is now more plausible at month 6 than I originally argued — not because the moat exists, but because the wiring for the moat exists.

### Does my position shift?

**The structural position argument is stronger. The timing argument is more honest.**

The credit bureau analogy, the audit-as-category thesis, the verification-layer positioning — these are all reinforced by the B2B2C model and freeform text input. The product occupies the same structural position I described, but the path to that position is more gradual and less dependent on traveler switching behavior. However, the convergent verdict — abandon the grand vision as a planning framework, test the narrow wedge — means I need to stop selling the 24-month moat and start selling the 2-week test. The Champion's job is to argue FOR the vision. The Round 2 Champion argues for the vision as the reason to run the test, not as the plan for what comes after. The structural position justifies the test. The test justifies the next 3 months. The next 3 months justify (or falsify) the vision.

### One thing another role got wrong that I still disagree with

**The Executioner's revised Kill Argument 2 dropped from 8/10 to 3/10 because "negotiation behavior is the intended mechanism." This overcorrects.**

The B2B2C path is the correct model. But the Executioner concluded that because the traveler sharing the audit with their existing agent is the intended behavior, the risk of this behavior has dropped from 8/10 to 3/10. I'd put it at 5/10. Here's why: the B2B2C path removes the switching problem but introduces a new one — will the agent who sees the Waypoint-branded audit actually do anything about it? Agents receive screenshots from clients all the time (MakeMyTrip comparisons, TripAdvisor reviews, competitor quotes). Most screenshots get a quick response and are forgotten. The Waypoint audit screenshot has to do something the others don't: it has to make the agent feel that their current workflow is inadequate without Product A. That's a conversion event, not a brand impression. The Skeptic's worry about whether the audit creates switching motivation was correct for the original B2C2B model. The equivalent worry for the B2B2C model is: does the shared audit create ADOPTION motivation? I'm not as confident as the Executioner's 3/10 rating suggests. The test will tell us. But don't declare victory on Kill Argument 2 just because we reframed the mechanism. The behavioral question at the end of the loop is still open.