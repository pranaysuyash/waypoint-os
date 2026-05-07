# PRE-MORTEM: Waypoint OS — Operator UX & Trust

**Role:** Customer Advocate
**Emotional Register:** Protective anger — the operator deserved better
**Scope:** Failure modes where operators can't understand AI decisions, the UI hides critical information, or trust erodes through opacity
**Date:** 2026-05-05

---

## FAILURE MODE 1: Bulk Assign Silently Does Nothing

1. WHAT GOES WRONG:
   Selecting trips and clicking "Assign to... [Agent]" clears the selection but never assigns the trips. The trips remain unassigned and the operator has no idea.

2. CHAIN OF EVENTS:
   Operator selects 5 unassigned trips in the inbox → clicks "Assign to..." → picks "Sarah" from dropdown → selection visually clears → operator assumes assignment worked → trips remain Unassigned → hours pass → SLA breaches → operator discovers trips were never assigned when the customer calls complaining about no response.

3. USER EXPERIENCE:
   The UI gives every signal of success: the dropdown closes, the selection clears, the checkboxes disappear. There is no error, no loading state, no toast, no confirmation. The operator's mental model is "I assigned those." The system's reality is "nothing happened."

4. EMOTIONAL IMPACT:
   Betrayal. The operator trusted the tool to do the one thing they asked. When they discover the trips were never assigned, it's not frustration — it's a betrayal narrative. "I did my job, the software lied to me." This is the kind of incident that makes someone say "I don't trust this system with anything important."

5. WHY TEAM MISSES IT:
   The bug is in `handleBulkAssign` (inbox/page.tsx, lines 264-266): it calls `handleClearSelection()` but never calls `assignTrips`. The `agentId` parameter is received but completely unused. It's a wiring bug in a callback — the kind of thing code review catches only if someone traces the full call chain. Team tests that the dropdown renders, not that the network call fires. No integration test covers bulk assign end-to-end.

6. LIKELIHOOD x IMPACT:
   Likelihood: CERTAIN (bug exists in production code right now). Impact: HIGH (busted core workflow, SLA misses, lost revenue).

7. TRUST DAMAGE:
   9/10. This is not a missing feature or a confusing label. This is a silent action failure with a false success signal. Trust does not recover from this without an explicit repair gesture.

8. RECOVERABILITY:
   Low once discovered. The operator can manually re-assign one by one, but the lost hours are gone. There's no audit trail of "attempted bulk assign at 2pm" to retroactively fix.

9. EARLIEST SIGNAL:
   Within 30 minutes of any beta agency using bulk assign for the first time. Trips won't move. But if the operator doesn't cross-reference, they may not notice for a full SLA cycle.

10. VERIFY BY:
    Select 2+ trips in inbox → click "Assign to..." → pick an agent → check network tab for PATCH/POST to assignment endpoint → observe none fires. Then check trip data — still unassigned.

---

## FAILURE MODE 2: Confidence Scores Without Reasoning Chains

1. WHAT GOES WRONG:
   The DecisionTab displays "Overall Confidence: 72%" as a single number with no explanation of how it was derived, what inputs drove it, or what would change it.

2. CHAIN OF EVENTS:
   Operator processes a $15,000 Kenya family safari → AI returns "PROCEED_INTERNAL_DRAFT" with 72% confidence → operator needs to decide whether to quote now or gather more info → the 72% tells them nothing about what's risky → they either quote blindly (and miss that the budget is borderline) or waste time gathering info the AI already considered adequate → either way, they can't make an informed decision.

3. USER EXPERIENCE:
   "Overall Confidence: 72%" sits there like a grade on a test no one explained the rubric for. The Rationale section lists "Feasibility: feasible" and a confidence number, but doesn't connect specific inputs to specific risk weights. The ConfidenceScorecard type has `data_quality`, `judgment_confidence`, and `commercial_confidence` sub-scores — but the DecisionTab only shows `overall`. The operator sees a number that demands trust without earning it.

4. EMOTIONAL IMPACT:
   Anxiety and resentment. The operator is being asked to stake their professional reputation on a number they can't audit. When things go wrong, they can't explain to their boss or their client why they trusted "72%." This creates a "just ignore the AI" defense mechanism that defeats the entire product.

5. WHY TEAM MISSES IT:
   The data model (`ConfidenceScorecard` in spine.ts) already has the sub-scores. Someone built the type with the right structure. But the DecisionTab UI only surfaces the overall. The team shipped the data plumbing and moved on — the sub-scores are "available via Show Technical Data" (the JSON toggle), which no operator will ever click. The team sees the data as "there" because it's in the API response. The operator sees it as "not there" because it's behind a debug toggle.

6. LIKELIHOOD x IMPACT:
   Likelihood: HIGH (every single decision shows only overall confidence). Impact: MEDIUM-HIGH (accumulates into systematic distrust — the "boy who cried 72%" effect).

7. TRUST DAMAGE:
   7/10. Not a shock event, but a slow erosion. Every time an operator can't explain the AI's recommendation to a client or partner, the product becomes slightly less valuable. Over weeks, they learn to treat the confidence score as decoration.

8. RECOVERABILITY:
   Medium — showing the scorecard breakdown would help, but the deeper problem is that confidence without provenance (which input changed it? what would raise it?) is inherently untrustworthy. Full recovery requires showing how each input factored into the score.

9. EARLIEST SIGNAL:
   Watch for operators consistently ignoring the confidence score and re-deriving their own assessment from the raw data. If they read the "Hard Blockers" section but never mention the confidence number in their decision-making, the score has become noise.

10. VERIFY BY:
    User testing: give 5 operators a trip with 72% confidence and ask them what they'd do differently at 52% vs 92%. If they can't articulate a difference, the number is meaningless to them.

---

## FAILURE MODE 3: Pipeline Says "Ready to Quote?" But There's No Tab For It

1. WHAT GOES WRONG:
   The PipelineFlow shows 5 stages (Inquiry → Details → Quote? → Options → Review), but the workbench only has 3 visible tabs (New Inquiry, Safety Review, Ops). When the pipeline advances to "packet" or "decision", the user can't click the pipeline to navigate — they must know which tab corresponds to which pipeline stage.

2. CHAIN OF EVENTS:
   Operator clicks "Process Inquiry" → pipeline animates forward → lands on step 3 "Ready to Quote?" → operator wants to see the quote-readiness assessment → looks at tabs: "New Inquiry", "Safety Review", "Ops" — none of these obviously maps to "Ready to Quote?" → operator stays on Intake tab → misses that decision data is available in a hidden tab → re-processes the trip thinking it didn't work → creates a duplicate draft.

3. USER EXPERIENCE:
   The pipeline breadcrumb says "You are here: Ready to Quote?" but the navigation says "Your options are: New Inquiry, Safety Review, Ops." This is two different maps for the same territory. The operator feels lost in their own tool. The pipeline says go right, the tabs say go left.

4. EMOTIONAL IMPACT:
   Disorientation that turns to contempt. "Even the app can't agree on where I am." This is the UX equivalent of a building where the floor numbers in the elevator don't match the numbers on the doors. It's not confusing — it's insulting. You feel like no one cared enough to finish the signposting.

5. WHY TEAM MISSES IT:
   The pipeline is derived from data presence (`getPipelineStageForWorkbench` checks `store.result_decision`), and the tabs are a fixed set. They were built by different people at different times. The pipeline was added as a "nice to have" progress indicator. Tabs were the actual navigation. No one reconciled them. The packet/decision/strategy tabs are loaded via dynamic imports but only used in the old `workspaceTabs` — the current `workspaceTabs` (line 69-73) is hardcoded to 3 entries. The pipeline has 5 stops, the tabs have 3 stops. Nobody noticed the mismatch because developers navigate by URL params, not by clicking tabs.

6. LIKELIHOOD x IMPACT:
   Likelihood: HIGH (every workbench session has this mismatch). Impact: MEDIUM (operators find workarounds — they learn the hidden tabs via URL params or coworker tips — but new operators are lost for days).

7. TRUST DAMAGE:
   6/10. Not catastrophic, but it makes the product feel unfinished and amateur. In a B2B context where agencies are evaluating whether to trust a solo-founder startup with their workflow, this mismatch screams "not ready."

8. RECOVERABILITY:
   High — making pipeline stages clickable to navigate to the right tab, or aligning tab labels with pipeline labels, would fix the cognitive mismatch. But the deeper signal is that nobody walked the full operator journey end-to-end before shipping.

9. EARLIEST SIGNAL:
   New beta operators asking "Where do I see the decision?" or "How do I get to step 3?" in onboarding. If they ask within the first 10 minutes, the pipeline-tab mismatch is already failing.

10. VERIFY BY:
    Give a new operator a processed trip and time how long it takes them to find the decision output. If it takes >30 seconds, the navigation is broken.

---

## FAILURE MODE 4: Flags Without Provenance in the Inbox

1. WHAT GOES WRONG:
   TripCard in the inbox shows AI-generated flags as amber badges (e.g., "elderly_mobility_risk", "budget_borderline") but provides no explanation of what the flag means, how confident the AI is, or what the operator should do about it.

2. CHAIN OF EVENTS:
   Inbox shows a Kyoto trip with flag badge "elderly_mobility_risk" → operator has no idea what this means — is the elderly traveler at risk? Is the destination risky for elderly? Is this about accessibility? → operator clicks the trip card, goes to workbench → there's no obvious place where this flag is explained → flags in the workbench DecisionTab show `SuitabilityFlagData` with severity, confidence, and reason — but getting there requires navigating to a specific sub-tab and scrolling → operator gives up, ignores the flag → books a trip where the 78-year-old client has mobility issues in a city with steep terrain → client has a bad experience → agency gets a complaint.

3. USER EXPERIENCE:
   You see a warning label that says "CAUTION" with no other text. That's what flags feel like. They demand attention but offer no information. The `FlagBadge` component renders the flag string with a 10px font and an amber background — it's designed to be noticed but not understood. The `getMicroLabel` function may or may not have a human-readable entry for any given flag. Many flags render as raw machine identifiers.

4. EMOTIONAL IMPACT:
   Anxiety without agency. The flag says "something is wrong" but doesn't say what or what to do. This is the worst kind of alert — one that activates the operator's threat detection without giving them any action to take. Over time, operators learn to ignore amber badges entirely (alert fatigue), which means the flags that DO matter get missed.

5. WHY TEAM MISSES IT:
   The flag system has a rich backend model (`SuitabilityFlag` with `confidence`, `tier`, `reason`, `details`, `affected_travelers`). But the inbox TripCard only gets the `flags: string[]` array from `InboxTrip`. The depth was lost at the API boundary — the inbox query returns flat flag names, not the full objects. The team sees flags as "signals for triage" but the operator sees them as "mysterious warnings I can't act on." The `shouldShowMicroLabels()` function tries to help but only provides short labels, not the confidence/reason/action chain.

6. LIKELIHOOD x IMPACT:
   Likelihood: HIGH (every trip with suitability flags shows opaque badges). Impact: MEDIUM-HIGH (alert fatigue means real risks get ignored; worst case: safety incident that a human flag would have prevented).

7. TRUST DAMAGE:
   7/10. When a flag that mattered gets ignored because the UI trained operators to dismiss amber badges, the operator blames the product. "The system warned me but didn't tell me what to do" is worse than no warning at all — it transfers liability to the operator without giving them the tools to act.

8. RECOVERABILITY:
   Medium — tooltip on hover showing the flag reason and confidence would help. But the deeper fix is surfacing flag details inline or making flags actionable (e.g., "click to see what this means and what to do").

9. EARLIEST SIGNAL:
    Operators clicking on flag badges expecting detail (and getting nothing). Or operators asking "what does [flag_name] mean?" in Slack/support. If multiple operators ask about the same flag, the UI is failing.

10. VERIFY BY:
    Show an operator a TripCard with 3 flags and ask: "Which of these flags requires immediate action?" If they can't answer in <5 seconds, the flags are decorative, not functional.

---

## FAILURE MODE 5: "System Ready" Is A Lie

1. WHAT GOES WRONG:
   IntakeTab (line 201-207) displays a static green dot labeled "System Ready" that never changes regardless of backend status, queue depth, API health, or any actual system state.

2. CHAIN OF EVENTS:
   Spine backend goes down during peak hours → operator opens workbench → sees green dot "System Ready" → pastes customer message → clicks "Process Inquiry" → waits 30 seconds → gets generic error "Processing failed. Please try again" → tries again → same error → wastes 10 minutes retrying → calls support → support says "yeah the backend is down" → operator wonders why the app said "System Ready" if the backend wasn't ready.

3. USER EXPERIENCE:
   The green dot is a decorative element that looks like a status indicator. It is not. It's a `<div className='w-2 h-2 rounded-full bg-[#3fb950]'></div>` — a hardcoded green circle. Every other industry ( healthcare, aviation, manufacturing) treats status indicators as sacred. If the green light is on, the system is up. Waypoint OS breaks this covenant.

4. EMOTIONAL IMPACT:
   When the operator discovers the green dot is fake, they don't just distrust the dot — they distrust every indicator in the system. The SLA badge? Maybe that's fake too. The "Saved" confirmation? Maybe not. Once you catch a UI lying, you assume everything might be a lie. This is corrosive.

5. WHY TEAM MISSES IT:
   It was probably added as a visual filler during early prototyping and never replaced with a real health check. The `HealthResponse` type exists in spine.ts, and the `useIntegrityIssues` hook exists for the Integrity Monitor. But nobody connected backend health to the intake page. The green dot is a placeholder that shipped. The team sees it as ambient UI chrome. The operator sees it as a status indicator.

6. LIKELIHOOD x IMPACT:
   Likelihood: HIGH (backend will go down at some point; the green dot will always be green). Impact: MEDIUM (wasted time + trust damage; no data loss, but operator frustration compounds).

7. TRUST DAMAGE:
   8/10. This is a lie built into the UI. It's not a missing feature — it's an active deception. When someone discovers it, the reaction is "what else is fake?" This is the kind of thing that appears in a负面 review: "The status indicator is a hardcoded green dot."

8. RECOVERABILITY:
   Easy to fix technically (wire to HealthResponse). Hard to fix reputationally — operators who discovered the lie will never fully trust a status indicator again, even after it's real.

9. EARLIEST SIGNAL:
    The first time the backend goes down and an operator wastes time retrying. They'll say "the system said it was ready." Support will discover the green dot.

10. VERIFY BY:
    Kill the spine backend process → load the workbench → observe the green dot → it still says "System Ready." That's all the verification you need.

---

## FAILURE MODE 6: Recovery Mode Without Recovery Context

1. WHAT GOES WRONG:
   When `feedback_reopen` or `recovery_status === 'IN_RECOVERY'` is active, the workbench displays a red "Recovery Mode: Critical Feedback Detected" banner with a "Mark Resolved" button — but shows zero information about what the feedback was, who gave it, or what needs fixing.

2. CHAIN OF EVENTS:
   A client complains about their itinerary via the feedback channel → the trip flips to IN_RECOVERY → the assigned operator opens the workbench → sees red banner "Critical Feedback Detected" → clicks "Mark Resolved" because there's nothing else to do — they can't see the feedback → the complaint is marked resolved without being addressed → the client follows up angrier → the agency loses the account.

3. USER EXPERIENCE:
   Imagine your car's check engine light comes on, and when you take it to the mechanic, the only option on the diagnostic screen is "Clear Light." That's Recovery Mode. The banner tells you something is wrong, gives you exactly one button, and that button makes the warning go away without fixing the problem. The `handleResolve` callback sends a generic message: "Recovery completed. Feedback addressed." — a lie the system tells on the operator's behalf.

4. EMOTIONAL IMPACT:
   The operator feels set up to fail. The system created a high-urgency alert but gave them no tools to address it. "Mark Resolved" is a trap — it's the only action available, so they'll take it, but they know they're just dismissing a problem they don't understand. This breeds a specific kind of helplessness that makes operators hate their tools.

5. WHY TEAM MISSES IT:
   The recovery mode was likely built as a state machine feature (trip enters recovery state → UI must show it → add a banner + resolve action). The feedback content is probably stored in a separate model/endoint that wasn't wired into the workbench view. The team completed the state transition UI without building the context UI. The `handleResolve` sends a hardcoded string because there was no place to input an actual resolution.

6. LIKELIHOOD x IMPACT:
   Likelihood: MEDIUM (recovery mode only triggers on feedback reopens, which are infrequent but inevitable). Impact: HIGH (resolving without understanding can escalate client complaints into account losses).

7. TRUST DAMAGE:
   8/10. The operator is being asked to "resolve" something they can't see. This is the system treating the operator as a button-pusher, not a professional. When the client follows up and the operator has to say "I marked it resolved but I never saw your feedback," the operator will blame the tool — and they'll be right.

8. RECOVERABILITY:
   Low — once an operator "resolves" a recovery without addressing the feedback, the damage is done. There's no "un-resolve" flow visible in the UI. The client's complaint was acknowledged and dismissed.

9. EARLIEST SIGNAL:
   Any recovery-mode trip where the operator clicks "Mark Resolved" within seconds of opening the workbench. If they resolved it faster than they could have possibly read and addressed feedback, the system gave them no useful information.

10. VERIFY BY:
    Put a trip into recovery mode → open the workbench → count the information elements visible about what triggered recovery. If it's <3 (what, who, when, what to fix), the banner is a trap.

---

## FAILURE MODE 7: Auto-Save Without Undo Creates Data Loss Anxiety

1. WHAT GOES WRONG:
   The workbench auto-saves after 5 seconds of inactivity, silently overwriting the previous draft version with no way to browse or restore prior versions.

2. CHAIN OF EVENTS:
   Operator opens an existing trip's workbench → accidentally selects-all and deletes the customer message textarea → before they can undo (Ctrl+Z), browser loses focus or they click elsewhere → 5 seconds pass → auto-save fires with empty customer message → the previous message is overwritten → operator notices the textarea is empty → Ctrl+Z doesn't work because React re-rendered → the original message is gone → they have to re-paste from their email or ask the client to resend.

3. USER EXPERIENCE:
   Auto-save is supposed to be a safety net. Instead, it's a trap. Every keystroke is committed to the server within 5 seconds. There's version tracking (`draft_version` increments), but no UI to browse versions, diff them, or restore a previous one. The `Save conflict` state exists for concurrent edits, but there's no self-conflict recovery (I accidentally deleted my own data and the system saved my mistake for me).

4. EMOTIONAL IMPACT:
   Fear. The operator learns that any mistake they make in the workbench is permanent within 5 seconds. This makes the input fields feel dangerous — like editing a document with no undo. Every paste or edit carries the weight of "if I mess up, it's saved instantly." This is the opposite of what auto-save should feel like.

5. WHY TEAM MISSES IT:
   Auto-save was built to prevent data loss (browser crashes, tab closes). It succeeds at that goal. But it creates a new failure mode: the system is so eager to save that it saves mistakes too. The team sees the version counter incrementing (lines 498-500, 622-628) and considers versioning "done." But a version counter without a version browser is like a backup system without a restore button — technically correct, practically useless.

6. LIKELIHOOD x IMPACT:
   Likelihood: MEDIUM (accidental deletion happens, but not daily). Impact: MEDIUM (data loss is recoverable via email/external sources, but it wastes time and breaks confidence).

7. TRUST DAMAGE:
   6/10. Not catastrophic, but it makes the workbench feel hostile. Operators will start composing in external editors (Notepad, Google Docs) and pasting in, which defeats the purpose of the workbench entirely. When operators work around your tool instead of in it, trust is already gone.

8. RECOVERABILITY:
   Medium — if the backend stores version history, a "Restore previous version" button would help. But the current UI gives no access to history, so the data might as well not exist.

9. EARLIEST SIGNAL:
   Operators copying text out of the workbench before editing it. If you see operators pasting into the workbench from external editors, they don't trust auto-save.

10. VERIFY BY:
    Delete the contents of the customer message textarea → wait 6 seconds → observe auto-save fires → check draft API → previous message is gone. Then check: is there any UI to get it back?

---

## FAILURE MODE 8: Decision Tab Shows Blockers But Not What to Do About Them

1. WHAT GOES WRONG:
   The DecisionTab lists hard blockers, soft blockers, contradictions, and risk flags as text strings, but provides no indication of what action resolves each item, whether the operator can override it, or what the consequence of proceeding despite a blocker would be.

2. CHAIN OF EVENTS:
   AI returns "STOP_NEEDS_REVIEW" with hard blocker: "no_travel_dates" → operator sees the blocker listed in the DecisionTab → they already have the dates from a phone call but forgot to type them → the UI doesn't say "Add travel dates in the Intake tab to resolve this blocker" → it just says "no_travel_dates" → operator doesn't connect the blocker to a fix → they reprocess the trip hoping it works → same result → they give up and handle it manually outside the system.

3. USER EXPERIENCE:
   The blockers section reads like an error log, not like a task list. "Hard Blockers: no_travel_dates, budget_unspecified" tells the operator WHAT is missing but not WHERE to add it or HOW. The validation banner (lines 752-795) partially addresses this — it has "Fix in Intake" and "View Details" buttons. But the DecisionTab, where operators spend most of their review time, just lists blockers as inert text. No links, no actions, no next steps.

4. EMOTIONAL IMPACT:
   Helplessness dressed up as information. The operator is told what's wrong but not how to make it right. It's like a doctor saying "you have a condition" without prescribing treatment. The operator has all the anxiety of a problem with none of the agency of a solution. This specific combination — information without action — creates the worst kind of UX: informed helplessness.

5. WHY TEAM MISSES IT:
   The team built the validation banner as the primary fix-pathway ("Fix in Intake" button), and the DecisionTab as the review/audit view. But operators organically end up in the DecisionTab first (it's where the AI's conclusion is). The blocker resolution path is routed through a different UI element that the operator may not see. The team's mental model is "banner → fix → reprocess." The operator's mental model is "DecisionTab → see what happened → ???"

6. LIKELIHOOD x IMPACT:
   Likelihood: HIGH (every blocked trip creates this experience). Impact: MEDIUM (operators find workarounds but the product feels unfinished; each blocker without a fix-path is a dead end that erodes perceived value).

7. TRUST DAMAGE:
   6/10. The operator doesn't lose data or miss an SLA — they just lose faith that the system is designed for their workflow. Each dead end is a small vote of "this wasn't built for me." Accumulate enough of those, and the operator stops recommending the product.

8. RECOVERABILITY:
   High — linking each blocker to the specific input field that would resolve it ("Add travel dates → Intake tab → Dates field") would transform blockers from error messages into task items. The `ValidationReport` type already has field-level error objects with `field` and `message` — the data is there to generate these links.

9. EARLIEST SIGNAL:
   Operators reprocessing trips without changing anything (the "try again and hope" pattern). If you see reprocess attempts with identical inputs, it means the operator doesn't know what to change.

10. VERIFY BY:
    Give an operator a trip with hard_blockers: ["no_travel_dates"] but don't tell them the dates. Time how long until they add dates to the intake. If they reprocess first (without changing anything), the UI failed to connect blocker to action.

---

## The failure nobody wants to talk about:

The entire product is built around the promise of AI-powered decisions, but the UI treats the operator as a consumer of conclusions, not a partner in reasoning. Every screen shows the WHAT (confidence: 72%, state: PROCEED_INTERNAL_DRAFT, blocker: no_travel_dates, flag: elderly_mobility_risk) and almost nothing shows the WHY or the WHAT NEXT. The operator is given verdicts without evidence, warnings without context, and blockers without remediation paths. The systemtalks AT the operator, never WITH them.

The deepest trust failure isn't any single bug or missing feature. It's the architecture of the relationship the UI creates: the AI is the expert, the operator is the clerk. The operator's job is reduced to clicking "Process Inquiry," reading the result, and clicking "Mark Resolved." When the AI is wrong — and it will be wrong — the operator has no tools to understand why, to debug it, or to correct course. They can only retry or override, both of which are blunt instruments that teach the operator nothing and improve the system nothing.

Until Waypoint OS treats the operator as an auditor who needs a full reasoning chain — not a consumer who needs a dashboard of verdicts — trust will erode with every processed trip. The operators won't churn dramatically. They'll just slowly stop using the features that matter. They'll process the trip in Waypoint, but do the actual thinking in their head, in an email draft, or on a notepad. The AI copilot becomes an expensive data entry clerk. That's not the product anyone set out to build, but it's the product the UX is designing.