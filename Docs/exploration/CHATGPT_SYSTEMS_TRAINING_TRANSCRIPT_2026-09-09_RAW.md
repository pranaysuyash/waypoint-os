# ChatGPT Systems-Training Session — RAW TRANSCRIPT (2026-09-09)

**Provenance:** pasted verbatim by the owner on 2026-09-09 from a ChatGPT tutoring session on Waypoint/systems design (continuation of the TPM training thread; see `Docs/exploration/TPM_SYSTEMS_LEARNINGS_PROMOTION_2026-09-01.md`). Full-fidelity raw record per documentation doctrine — no paraphrasing; the distilled findings register lives in `CHATGPT_SYSTEMS_TRAINING_SESSION_FINDINGS_2026-09-09.md`.

Good starting point. You understand the business flow, but right now you are still describing what the travel business does, not yet how the system behaves.

That distinction is exactly what we need to train.

Your current level on this exercise: 6/10.

Area	Your answer	What’s missing
Input	Good	Need to think in terms of raw messages, attachments, voice notes, links, dates, names, partial bookings
State	Partly right	State is not just past customer history. It is the current structured truth of the trip
Decision	Too high-level	“Final itinerary” is an outcome. The decision layer decides what the system should do next
Action	Good direction	Need to distinguish researching, proposing, holding, booking, messaging, escalating
Validation	Good instinct	Needs much stronger checks around feasibility, source freshness, contradictions, permissions
Output	Too narrow	There may be operator-facing and traveler-facing outputs
Feedback	Good	Need explicit corrections, implicit signals, outcomes, and memory update rules
Failure	Business-focused	Need system failures too
Deterministic	Strong instinct	Need finer separation between hard rules and subjective choices
Scale worry	Too shallow	Load is only one of many problems

The biggest conceptual correction is this:

State

You said:

do we know from past history of the customer or are they new

That is memory, which is only one part of state.

State is closer to:

“What does Waypoint currently believe to be true about this trip?”

For example:

Travelers: 4
Adults: 2
Children: 2
Origin: Bengaluru
Destination: Tokyo
Dates: 5–12 October
Budget: ₹4 lakh
Hotel preference: 4-star
Disney: requested
Visa: unknown
Flights: not booked
Hotel: not booked
Passport expiry: missing
Dietary requirements: vegetarian
Open questions:
  - exact child ages
  - passport details
  - Disney date

That object changes over time.

Customer memory could then enrich it:

Previous preference:
- avoids early morning flights
- prefers Marriott
- usually chooses aisle seats

This separation is important:

Trip state = what is true now.

Customer memory = what may help us make better decisions.

Do not mix them.

Decision

You wrote:

based on budget/duration/no and type of people what is the final itinerary

This is the biggest gap.

The decision layer isn't the itinerary.

It answers:

What should happen next?

For example:

We don't know child ages.
→ Ask customer.

Flights are 35% above the expected budget.
→ Search alternate dates.

Visa lead time is 21 days but departure is in 16 days.
→ Escalate feasibility risk.

Disney tickets are available on two dates.
→ Compare both against itinerary constraints.

Everything is complete.
→ Generate proposed itinerary.

Customer approved.
→ Move eligible items toward booking.

Now you're thinking like a system designer.

A useful pattern:

Observe state → detect gap/problem → choose next action.

That is much closer to what an agent actually does.

Action

Your answer:

get flight booking, visa, hotels, identify missing items and flag

Mostly right, but separate recommendation from execution.

A travel system may be allowed to:

search_flights()
search_hotels()
check_visa_requirements()
calculate_trip_cost()
generate_itinerary()
ask_customer_question()

But:

book_flight()
pay_for_hotel()
submit_visa()
cancel_booking()

should probably require much stronger authorization.

This is an important agent principle:

The cost of a mistake should determine the autonomy level.

Searching flights is reversible.

Charging ₹2 lakh to a card is not.

So Waypoint should have different permission levels.

That is the kind of answer that sounds senior in an interview.

Validation

You already have the right idea:

check if constraints have been met

Now make it concrete.

Suppose the proposed itinerary is:

Flight lands: 10:40 AM
Disney booking: 11:00 AM
Travel time airport → Disney: 70 minutes

The model may happily generate that.

A validator should reject it.

Other validation examples:

Total cost <= approved budget
Arrival occurs before hotel check-in requirement
Passport validity satisfies destination rule
No two bookings overlap
Traveler count matches tickets
Child age rules match fare/product
Flight connection time >= minimum
Hotel occupancy supports party size
Visa requirement source is current
Prices were checked recently enough

Notice something important:

Most of these should not require an LLM.

They are rules, calculations, database checks or external tool lookups.

This is a foundational idea:

Use AI for ambiguity. Use deterministic software for truth you can calculate or verify.

Your deterministic answer was actually one of the strongest parts

You said:

flights/durations/no. of people/pricing, any time limit/constraint

Correct direction.

But split flight handling:

Deterministic:

flight departure time
arrival time
duration
price
baggage allowance
number of stops
seat availability
connection time

Potentially AI/ranking based:

Which of these 18 flights is best for this family?

Because “best” involves preferences and trade-offs.

For example:

Flight A: ₹86k, 2 AM departure
Flight B: ₹96k, 9 AM departure

There is no mathematically correct answer unless customer preferences establish one.

That is where reasoning/ranking can help.

Failure modes

Your answer focused on customer behaviour:

customer stops responding
last-minute changes
decides to drop

Those are legitimate business/workflow failures.

But technical systems also fail.

Imagine this:

Customer: "Book the 9 AM Indigo flight."

Agent calls booking API.

API times out.

Did booking happen?

If the system simply retries:

book()
book()

the customer might now own two tickets.

This introduces an extremely important systems concept:

Idempotency

An operation should be designed so retrying it does not accidentally create duplicate effects.

You'll encounter this everywhere:

payments, bookings, emails, inventory, orders.

Other Waypoint failure modes:

flight API unavailable
stale hotel pricing
currency conversion outdated
LLM misunderstands "next Friday"
two agents update the same trip simultaneously
customer changes dates while itinerary generation is running
visa website changes its rules
incorrect traveler identity mapping
duplicate bookings
tool returns incomplete data
model invents an unavailable flight
memory from another customer leaks into this trip
booking succeeds but state update fails

Those are the failures a technical interviewer will care about.

At one million trips/month

You said:

load, no learning from mistakes

Both matter, but “load” is too generic.

I would worry about these categories:

State consistency

What happens when several things change the same trip at once?

Customer sends WhatsApp update.

Operator edits dashboard.

Flight gets cancelled.

Agent is simultaneously replanning.

Which state wins?

External providers

Airlines, GDSs, hotels, visa providers, maps and payment APIs all have rate limits and outages.

Your system could scale perfectly while dependencies fail.

Cost

One million trips × hundreds of LLM/tool calls can become enormous.

You need:

routing
caching
smaller models
deterministic preprocessing
batching
budgets

Observability

You need to know:

Why did this itinerary fail?
Which tool caused it?
Which model version?
Which prompt?
Which state did the agent see?
Which rule rejected it?

Privacy

Passport numbers, payment data, phone numbers, addresses and travel plans are highly sensitive.

Auditability

Who decided what?

Customer?
Agent?
Human operator?
Rule engine?
Supplier?

Reliability

What happens when one dependency is down at 2 AM?

Model drift/regressions

A new model version may suddenly make different itinerary choices.

This is why evals matter.

Now rebuild Waypoint using the system model

Here is the architecture I want you to start seeing mentally:

MESSY CUSTOMER INPUT
        ↓
PARSE + NORMALIZE
        ↓
STRUCTURED TRIP STATE
        ↓
GAP / CONSTRAINT DETECTION
        ↓
DECISION / PLANNING LAYER
        ↓
TOOLS
Flights / Hotels / Visa / Maps / Pricing
        ↓
PROPOSED ACTIONS
        ↓
DETERMINISTIC VALIDATION
        ↓
HUMAN APPROVAL where required
        ↓
EXECUTION
        ↓
TRAVELER + OPERATOR OUTPUTS
        ↓
FEEDBACK / STATE UPDATE / MEMORY

That is already a much stronger Waypoint architecture than:

customer asks → AI makes itinerary.

One more important correction

Your original input answer was:

messy inbound for a travel itinerary

Good.

But don't rush to turn that into one prompt.

Suppose the conversation is:

Customer:
Planning Dubai around Diwali.

Customer:
4 of us.

Customer:
Kids are 6 and 11.

Customer:
Maybe 5 nights.

Customer:
Budget around 2.5.

Customer:
Actually wife wants Abu Dhabi too.

[uploads screenshot]

Customer:
Something like this hotel.

The first system problem is not itinerary generation.

It is turning messy communication into reliable structured state without silently losing information.

That is a serious applied-AI problem by itself.

And this is why Waypoint is a good project for your training.

Next exercise

Now answer just this scenario, without researching:

A customer tells Waypoint:

“We are 4 people, me, my wife and two kids. Bangalore to Japan around Oct 5 for about a week. Budget maybe 4L. Kids want Disney. We also want Kyoto. Prefer decent hotels, nothing crazy expensive.”

Waypoint knows nothing else.

Tell me:

A. What should the system extract into structured trip state?

B. What information is still missing?

C. Which missing information must be asked immediately, and which can wait?

D. What should Waypoint do before calling any LLM again?

E. Which tools would you call and in what order?

Do not try to get it “right.” I care more about your reasoning.

After your answer I'll introduce you to state machines, orchestration and agent loops, because this exact example gives us a clean path into all three.

Yes, and your “e-visa” answer was fine. I misread it as an assumption rather than your answer to part E.

This attempt is stronger: 8/10. You are now reasoning about dependencies, sources of truth, and AI-vs-deterministic boundaries rather than just describing travel operations.

The next improvement is to stop treating every useful prerequisite as a hard dependency. A lot of these can run provisionally in parallel.

Action	Your reasoning	Correction
1. Entry requirements	Mostly right	Government source is authoritative. Customer provides passport/nationality facts. But this can run in parallel with exploratory flight/Disney searches once basic traveler data is known.
2. Flights	Good hybrid thinking	Visa approval does not need to be complete before searching flights. Food preference is not needed for initial flight search. Seat availability is output from the provider, not an input dependency.
3. Hotels	Good	Hotels don't require visa or flights to be confirmed. The real hard dependencies are city/date ranges, traveler count/ages, room needs. Exact flight timing is a soft dependency for first/last-night optimization.
4. Disney	Too dependent	You don't need visa or confirmed flights merely to check availability. Date window + ages/product rules are enough for exploratory availability.
5. Route design	Underestimated dependencies	It definitely depends on duration, must-visit cities, arrival/departure assumptions, traveler profile and geography. Exact optimization may later depend on flights/hotels.
6. Final proposal	Correct	It combines everything, but “system data” is too vague. The proposal must retain provenance to the authoritative source behind each important fact.

The recurring mistake is this:

“We need to know X eventually” ≠ “X must be completed before we can do Y.”

That distinction is fundamental in both system architecture and TPM planning.

Look at flight search more precisely

You said its dependencies include visa requirements being fulfilled.

Not for search.

Imagine:

Customer has Indian passports.
Japan visa status unknown.
Travel dates ~Oct 5.
Budget ₹4L.

Waypoint can still ask a flight provider:

BLR → Tokyo/Osaka
Oct 3–7 departure
~7-day return
2 adults + 2 children

Why do that before visa completion?

Because if flights are ₹3.5L, we have discovered a major feasibility problem immediately.

So we should distinguish:

flight feasibility search
        ↓
flight recommendation
        ↓
flight booking

Each requires progressively stronger certainty.

For feasibility search, rough dates and traveler counts may suffice.

For recommendation, we need better dates, preferences, baggage needs, route, budget.

For booking, we need exact identities, DOBs, passport details, approvals, fresh fare, payment etc.

That's a powerful systems pattern:

Progressively increase validation as the consequence of the action increases.

You'll see this everywhere in AI systems.

Disney is another good example

You made:

visa + flights confirmed

dependencies for Disney.

They aren't necessary for availability research.

If we know:

Tokyo likely
Oct 5 ± 3 days
children ages known

we can already query:

Disney availability
ticket rules
opening hours
age categories
closures

This can run simultaneously with entry checks and flight searches.

Only when we buy the tickets do we need much greater confidence in the overall trip.

So:

CHECK availability ≠ RESERVE ≠ PURCHASE

Same external service, radically different risk.

Route design deserves more attention

You wrote:

A - nothing

This is the weakest part of your answer.

An itinerary route is actually constrained by a lot:

trip duration
must-visit locations
arrival airport
departure airport
customer pace
children's ages
travel times
attraction opening days
budget

Suppose Waypoint knows:

7 days
Tokyo
Kyoto
Disney
2 young children

Even before exact flights, it can generate candidate structures:

Option A
Tokyo: 4 nights
Kyoto: 3 nights

Option B
Tokyo: 3 nights
Kyoto: 4 nights

But when flight results arrive:

Arrival: Tokyo 10 AM
Return flight: Osaka 11 PM

the route can improve dramatically:

Tokyo → Kyoto → Osaka departure

instead of wasting time returning to Tokyo.

So the route has:

hard dependencies: cities, approximate dates/duration, party.

soft dependencies: exact flights, hotels, attraction availability.

You should start seeing systems as something that can refine incrementally, not as a single calculation that waits for every input.

Your AI-vs-deterministic answers are getting strong

Your flight example:

tool call for details, AI for best route/plan

Correct.

Let's make the layers explicit.

Deterministic/tool layer
Flight A
₹81,000
1 stop
14h 20m
2:20 AM departure

Flight B
₹94,000
direct
8h 15m
10:15 AM departure

Flight C
₹76,000
2 stops
21h

These facts must come from providers.

AI/ranking layer

Now ask:

Which one best fits two adults, two children, ₹4L total budget and a week-long Japan holiday?

There isn't necessarily one objectively correct answer.

AI can reason:

B costs ₹13k more but saves six hours and avoids a connection with children.

But AI must never alter:

₹94,000
8h 15m
10:15 AM

Those remain provider facts.

This creates another very reusable architecture:

AUTHORITATIVE DATA
        ↓
DETERMINISTIC FILTERING
        ↓
AI RANKING / REASONING
        ↓
DETERMINISTIC VALIDATION

That's a good applied-AI architecture.

Now we're ready for orchestration

You've already unknowingly designed a dependency graph.

Simplifying your corrected model:

                  ┌→ ENTRY CHECK ─────────────┐
TRIP STATE ───────┼→ FLIGHT FEASIBILITY ──────┤
                  └→ DISNEY AVAILABILITY ─────┤
                                               ↓
                                     CANDIDATE ROUTE
                                               ↓
                                        HOTEL SEARCH
                                               ↓
                                      OPTIMISE OPTIONS
                                               ↓
                                         VALIDATE
                                               ↓
                                     CUSTOMER APPROVAL
                                               ↓
                                    FRESHNESS RECHECK
                                               ↓
                                         EXECUTION

But even this isn't completely linear.

The system may discover:

Hotel prices too high
        ↓
change Tokyo/Kyoto split
        ↓
search hotels again

Or:

Disney unavailable Oct 7
        ↓
move Disney to Oct 8
        ↓
re-evaluate route

So Waypoint isn't merely a pipeline.

It has loops.

And once you have loops, decisions, waiting states, failures and retries, you start needing an orchestrator.

State machine

This is your next major concept.

Instead of thinking only about data such as:

travelers = 4
budget = 400000

we also need to know:

Where is this trip in its lifecycle?

For example:

NEW
↓
COLLECTING_REQUIREMENTS
↓
FEASIBILITY_CHECK
↓
PLANNING
↓
AWAITING_CUSTOMER_APPROVAL
↓
BOOKING
↓
BOOKED
↓
IN_TRIP
↓
COMPLETED

Those are states.

Events cause transitions:

customer_added_details
COLLECTING_REQUIREMENTS → FEASIBILITY_CHECK

feasibility_failed
FEASIBILITY_CHECK → NEEDS_REVISION

proposal_ready
PLANNING → AWAITING_CUSTOMER_APPROVAL

customer_rejected
AWAITING_CUSTOMER_APPROVAL → PLANNING

customer_approved
AWAITING_CUSTOMER_APPROVAL → BOOKING

This is a state machine.

Why is it useful?

Because instead of asking an LLM:

“What should we do with this trip?”

every single time, the system already knows:

Current state = AWAITING_CUSTOMER_APPROVAL
Allowed next actions =
- remind customer
- accept changes
- approve proposal
- reject proposal

Not allowed =
- book hotel automatically

That reduces AI freedom and therefore reduces errors.

This is a general principle you'll use repeatedly:

Constrain AI inside a deterministic operating envelope.

Your next exercise

Design the Waypoint trip lifecycle yourself.

Don't worry about formal names.

Start at:

customer first contacts us

and end at:

trip completed.

Give me roughly 8–12 states.

For each state, just tell me:

State → what must happen before it can move forward.

Also include at least:

one state where we're waiting for the customer,
one where something failed,
one where the customer changes their mind after approval.

That last one matters because real systems don't move neatly left-to-right.

After that we'll use your state machine to introduce events, queues, retries and idempotency, and you'll see why these four concepts fit together.

Entry requirementsMostly rightGovernment source is authoritative. Customer provides passport/nationality facts. But this can run in parallel with exploratory flight/Disney searches once basic traveler data is known.

my assumtion- like you said earlier i was referring to the single transaction and not as a general rule - so although yes it can run in parallel but for e.g. for this case we checked visa and know its not possible so we dont do the rest and save on work?

Yes. Your assumption is valid, and this is an important distinction I should have made more clearly.

You were reasoning about this particular transaction, not claiming that flight search fundamentally depends on visa approval in the abstract.

Those are different questions:

Can these tasks run in parallel?
versus
Should we run them in parallel for this request?

For this Japan request, if the entry check is cheap, fast, authoritative, and capable of killing the whole trip, then doing it first can absolutely be the better system design.

Your reasoning becomes:
Check entry feasibility
        ↓
   Can travel?
    /      \
  NO       YES
   ↓        ↓
STOP /     fan out:
explain    flights
options    Disney
           route
           hotels

This is called a gate.

The visa/entry check becomes a feasibility gate before we spend resources downstream.

That is better than blindly doing:

visa check ────────┐
flight search ─────┤
hotel search ──────┤
Disney search ─────┤
route planning ────┘

only to discover:

the traveler cannot make this trip anyway.

You have correctly identified wasted computation/work.

But now comes the senior-level part

“Parallelize everything possible” is not the rule.

The rule is:

Parallelize independent work when the expected benefit of lower latency exceeds the expected cost of wasted work.

Consider two cases.

Case 1: entry check takes 2 seconds

Flights + hotels + Disney together cost API money and 10 seconds of processing.

Do:

entry check
↓
if valid → parallel searches

Makes sense.

Case 2: entry check takes 3 minutes

Flight feasibility costs almost nothing and returns in 2 seconds.

Then waiting three minutes before even estimating whether the trip fits ₹4L may produce terrible UX.

You might instead do:

entry check ───────────────┐
                           │
rough flight feasibility ──┤
                           ↓
                  combine results

So orchestration depends on:

latency
monetary/API cost
probability the gate fails
consequence of doing unnecessary work
whether downstream results are reusable
user experience

This is exactly the kind of trade-off a TPM/system designer should recognize.

There's a name for another version of this: short-circuiting

Suppose validation has five checks:

passport valid?
visa possible?
budget plausible?
dates possible?
availability exists?

If:

passport expired

there may be no reason to immediately perform expensive downstream checks.

The system can short-circuit.

You'll see the same pattern everywhere:

Payments

card valid?
↓
fraud check
↓
inventory reservation
↓
payment

AI document processing

file readable?
↓
supported format?
↓
OCR
↓
LLM extraction

Don't spend ₹2 on an LLM if the PDF is corrupt.

AdShot

product truth sufficient?
↓
policy/compliance valid?
↓
generate expensive creative assets

Don't run expensive image/video generation if required product data is missing.

So this mental model generalizes very well.

There's one more nuance: hard stop vs recoverable gate

Imagine the result is:

Visa cannot be obtained before October 5.

Should Waypoint terminate everything?

Not necessarily.

The current plan may be infeasible, but the customer goal may still be achievable.

The decision layer could say:

Current plan infeasible
↓
Can dates move?
    ↓ yes
Search later dates

or:

Japan infeasible
↓
Does customer want alternatives?

So distinguish:

Request failure

This exact configuration won't work.

from

Goal failure

There is no acceptable way to satisfy what the customer wants.

That distinction is very important in agentic systems.

Your original reasoning was therefore good. A cleaner way to state it in a design discussion would be:

“Flight search does not logically depend on visa eligibility, so the tasks are parallelizable. But for this workflow I'd consider entry eligibility an early gating check because it's cheap, authoritative, and may invalidate the whole trip. If that check were slow, I'd consider speculative parallel feasibility searches and cancel downstream work if the gate fails.”

That is a very strong technical-program answer.

And you've just encountered three useful concepts from one correction:

dependency = B cannot happen without A
gate = we intentionally make B wait for A because A determines whether B is worth doing
parallelizable = A and B technically do not depend on each other

Those are not the same thing.

ok now on the next exercise - Waypoint trip lifecycle
customer contacts us - data enters a draft stage - 
normalize - extract/parse into structured vs rest - is the data parseable or needs ocr like was it a screenshot or did they share url which needs a tool call - missing customer details

i think i need help on this lifecycle and state thing



Yes. Your instinct is right, but you’re currently mixing lifecycle states with processing steps. That is the main thing to fix.

The clean mental model is:

State = where the trip currently is.
Action/task = work being performed while it is in that state.
Event = something that happened.
Transition = the event moves the trip from one state to another.

So in what you wrote:

customer contacts us → data enters draft stage

That is a valid lifecycle state.

But:

normalize → extract/parse → OCR screenshot → fetch URL

Those are mostly actions inside the intake state, not separate lifecycle states.

How to tell whether something deserves to be a state

Ask:

“Could the trip meaningfully remain here for some time, and would different rules/actions apply while it is here?”

If yes, it is probably a state.

For example:

AWAITING_CUSTOMER_INFO is definitely a state because the system might remain there for two days, send reminders, accept new messages, and prevent booking.

But:

OCR_IN_PROGRESS is usually just a processing task. It might last five seconds and does not define the business lifecycle of the trip.

That distinction is important.

Let's build Waypoint properly

Start with your first idea.

1. DRAFT / INTAKE

Customer has contacted us, but Waypoint does not yet have a reliable structured trip brief.

Inside this state the system might:

receive WhatsApp messages
receive screenshots
receive PDFs
receive URLs
receive voice notes

↓
detect input type

text → parse
image → OCR / vision
PDF → extract
URL → fetch
voice → transcribe

↓
normalize

"B'lore" → Bengaluru
"4L" → ₹400,000
"around Oct 5" → approximate date constraint

↓
merge into trip state

Those are actions.

The trip is still in:

INTAKE

until the system has enough usable information to decide what to do next.

Now imagine intake finishes

Suppose Waypoint extracts:

4 travelers
Bengaluru → Japan
~Oct 5
~7 days
~₹4L
Kyoto required
Disney wanted

But child ages and passport details are missing.

The system should not remain in generic INTAKE.

It transitions to:

2. NEEDS_INFORMATION

Why?

Because the system now understands the request, but cannot safely continue.

State:

NEEDS_INFORMATION

Reason:

missing:
- child ages
- passport nationality
- visa status
- flight budget inclusion

Allowed actions might be:

ask customer
receive response
send reminder
operator manually fill field

Not allowed:

book flight
book hotel

Now you can see why a state matters.

Event → transition

Suppose customer replies:

Kids are 7 and 11, Indian passports, no visa yet, and ₹4L includes flights.

That is an event:

CUSTOMER_DETAILS_RECEIVED

The system updates trip state.

If all blocking information is now available:

NEEDS_INFORMATION
        ↓
READY_FOR_FEASIBILITY

That arrow is the transition.

3. FEASIBILITY_CHECK

Now the system asks:

Can this trip plausibly work at all?

Actions:

check entry requirements
check visa lead time
rough flight feasibility
rough hotel feasibility
check major date constraints
check Disney availability

This is where your earlier gate discussion fits perfectly.

Possible result:

Feasible
FEASIBILITY_CHECK
        ↓
PLANNING
Not feasible, but recoverable

Maybe visa timing fails.

FEASIBILITY_CHECK
        ↓
NEEDS_REVISION

The system could tell the customer:

October 5 is unlikely to work because of visa timing. Would October 20 work?

Fundamentally impossible / manual attention
FEASIBILITY_CHECK
        ↓
ESCALATED
4. PLANNING

Now the trip is feasible.

The system can actually optimize:

flight options
Tokyo/Kyoto sequencing
hotel options
Disney day
intercity transport
budget allocation

Notice what changed:

During feasibility, we ask:

“Can this work?”

During planning, we ask:

“Which version is best?”

Those are different states because the objectives are different.

Planning might produce:

Option A
₹3.65L
Direct flight
4 nights Tokyo
3 nights Kyoto

Option B
₹3.31L
1-stop flight
3 nights Tokyo
4 nights Kyoto

Once a complete proposal exists:

PLANNING
    ↓
AWAITING_CUSTOMER_APPROVAL
5. AWAITING_CUSTOMER_APPROVAL

This is an obvious state.

Waypoint is waiting.

Allowed:

customer accepts
customer rejects
customer asks questions
customer changes constraints
send reminder
operator discusses options

Not allowed:

charge card
book non-refundable tickets

Then three things can happen.

Customer approves
AWAITING_CUSTOMER_APPROVAL
            ↓
APPROVED
Customer rejects
AWAITING_CUSTOMER_APPROVAL
            ↓
PLANNING
Customer changes the request

For example:

Actually my parents are joining too.

Now the old plan is invalid.

AWAITING_CUSTOMER_APPROVAL
            ↓
NEEDS_REVISION
6. APPROVED / PRE-EXECUTION

This state is important and easy to miss.

Why not immediately book?

Because between proposal and approval:

flight prices may change
rooms may sell out
Disney availability may change
exchange rates may move

So we need a freshness recheck.

Customer approved ₹90k flight
        ↓
provider now says ₹1.18L

You cannot silently book it.

So:

APPROVED
    ↓
recheck prices / inventory / rules

If everything remains within approved bounds:

APPROVED
    ↓
BOOKING

If materially changed:

APPROVED
    ↓
AWAITING_CUSTOMER_APPROVAL

with updated information.

Very important state.

7. BOOKING_IN_PROGRESS

Now actual side effects occur.

reserve flight
book hotel
buy attraction ticket
process payment
record confirmations

This state matters because failures become dangerous.

Example:

flight booked successfully
hotel API fails

The trip is neither fully booked nor unbooked.

So the system must know:

flight: CONFIRMED
hotel: FAILED
Disney: NOT_STARTED

This is where concepts like retries and idempotency will become relevant.

8. BOOKED

All required components are confirmed.

Now the system changes behaviour again.

It should no longer behave like a sales/planning agent.

It becomes more like a trip-management system:

monitor changes
send documents
remind visa/check-in
surface disruptions
handle changes
9. CHANGE_REQUESTED

You explicitly needed a state where the customer changes their mind after approval.

Suppose everything is booked and they say:

Add one more night in Kyoto.

Do not mutate the original trip invisibly.

Enter:

CHANGE_REQUESTED

Now calculate:

what bookings are affected?
what penalties?
what price differences?
what downstream dependencies?

Then:

CHANGE_REQUESTED
        ↓
REPLANNING
        ↓
AWAITING_CHANGE_APPROVAL

If accepted, execute changes.

This preserves auditability.

10. IN_TRIP

Travel has started.

Different concerns now:

flight delay
missed connection
hotel issue
weather
local transport
emergency assistance

You wouldn't want Waypoint running the same workflow as pre-trip planning.

Therefore it deserves its own state.

11. COMPLETED

Trip is over.

Now:

collect feedback
record outcomes
resolve refunds/claims
extract reusable preferences
close unresolved tasks
update customer memory

Then the operational lifecycle ends.

Special state: ESCALATED / EXCEPTION

I would not necessarily place this as a normal linear step.

It can be entered from many places.

INTAKE ────────────────┐
FEASIBILITY ───────────┤
PLANNING ──────────────┤
BOOKING ───────────────┼→ ESCALATED
IN_TRIP ───────────────┘

Examples:

passport details contradictory
provider APIs disagree
payment repeatedly fails
customer disputes booking
AI confidence too low
visa case requires specialist review

Human operator takes control.

Once resolved, the trip can return to the relevant state.

The full lifecycle

Now compress everything:

CUSTOMER CONTACT
      ↓
INTAKE
      ↓
NEEDS_INFORMATION ←──────┐
      ↓                   │
FEASIBILITY_CHECK         │
      ↓                   │
PLANNING ←────────────────┤
      ↓                   │
AWAITING_APPROVAL         │
      ↓                   │
APPROVED / RECHECK        │
      ↓                   │
BOOKING_IN_PROGRESS       │
      ↓                   │
BOOKED                    │
      ↓                   │
CHANGE_REQUESTED ─────────┘
      ↓
IN_TRIP
      ↓
COMPLETED

With:

ESCALATED

available as an exception path from several states.

Your original thinking now has a place

You started with:

normalize
extract/parse
screenshot OCR
URL tool call

Keep all of that.

Just put it inside INTAKE:

STATE: INTAKE

tasks:
  ingest
  classify source
  OCR/transcribe/fetch
  extract
  normalize
  validate schema
  merge into trip state
  detect missing information

exit conditions:
  enough data → FEASIBILITY
  blocking gaps → NEEDS_INFORMATION
  processing problem → ESCALATED

That's a much cleaner design.

One pattern I want you to remember

For any state, write four things:

Question	Example
What is true?	Customer request understood but child ages missing
What can happen?	Ask customer / receive response
What cannot happen?	Booking
What moves us out?	Required information received

That is the core of state-machine thinking.

You do not need fancy notation yet.

Your next exercise

Take just NEEDS_INFORMATION and BOOKING_IN_PROGRESS.

For each, answer:

1. What is true while the trip is in this state?
2. What actions are allowed?
3. What actions should be forbidden?
4. What events can happen?
5. Which state does each event move us to?

These two states are deliberately very different. If you can model both correctly, state machines will start feeling much more natural.