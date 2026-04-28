# Simulated User Interview: Corporate Travel Manager

**Date:** 2026-04-28
**Format:** Simulated depth interview (role-played)
**Duration:** ~55 minutes (simulated)
**Interviewer:** Product Researcher
**Participant:** "Vikram" — Corporate Travel Manager (Persona P4)

---

## 1. Participant Profile

| Attribute | Detail |
|-----------|--------|
| **Name** | Vikram Sethi (pseudonym) |
| **Age** | 42 |
| **Location** | Bangalore, India |
| **Role** | Corporate Travel Manager, TechCorp (1,200 employees) |
| **Experience** | 12 years in corporate travel |
| **Team Size** | 4 people — 2 booking coordinators, 1 visa specialist, 1 finance liaison |
| **Annual Travel Spend** | ~₹18Cr (flights, hotels, cabs, visas, insurance) |
| **Tech Stack** | Concur (₹400/user/year = ₹4.8L/year), Excel, WhatsApp, SAP Concur |
| **Biggest Frustration** | "I'm spending ₹18Cr a year and I can't tell you which vendor is overcharging me." |

---

## 2. Interview Scenario**

**Context:** Vikram has been evaluating the Agency OS product for his corporate travel needs. TechCorp currently uses Concur for booking and Excel for tracking. He tested the tool for a month with 2 coordinators handling 30 trips.

---

## 3. Interview Transcript**

### Opening: The ₹18Cr Blind Spot**

**Interviewer:** Vikram, tell me about the moment you realized you had a visibility problem.

**Vikram:** It was the CFO meeting last quarter. She asked: "Vikram, we spent ₹18Cr this year. Which vendors are overcharging us? Which hotels are we overpaying? Show me the data."

I opened my Excel sheet. The one I spend 3 days every month updating. I had... totals. "Hotel X: ₹3.2Cr. Airline Y: ₹5.1Cr." But OVERPAYING? I couldn't tell her.

I know Hotel X near Whitefield charges us ₹8,500/night. But Booking.com shows ₹7,000 for the same room. Am I overpaying? Or is my volume discount actually WORSE than the public rate?

I couldn't answer. The CFO said: "Vikram, if we're overpaying by even 10%, that's ₹1.8Cr wasted. Fix it."

**Interviewer:** And how did you try to fix it?

**Vikram:** *(laughs)* I tried Concur's analytics. ₹4.8L/year for the license. You know what it told me? "Your top vendor is Hotel X at ₹3.2Cr." That's IT. No "you're overpaying by 15%." No "switch to Hotel Y and save ₹40L." Just... totals.

Then I tried manual comparison. Me + 2 coordinators spent 2 WEEKS checking our rates vs. market rates on Booking.com and MakeMyTrip. We found:
- Hotel X: ₹8,500 vs. market ₹7,000 = 21% overpayment
- Hotel Y: ₹12,000 vs. market ₹14,000 = good deal (14% savings)
- Airline Z: ₹45K vs. market ₹52K = good deal

Total waste: ~₹45L/year just on Hotel X. TWO WEEKS of work. For ONE data point.

---

### Section 1: Policy Enforcement Nightmare**

**Interviewer:** What about policy violations? How do you catch them?

**Vikram:** *(sighs)* This is the daily headache.

Company policy:
- **Junior (Grade 1-3):** Max ₹8,000/night, economy flights <6 hours
- **Mid (Grade 4-6):** Max ₹15,000/night, economy flights any duration
- **VP (Grade 7+):** Max ₹25,000/night, business class allowed

Last month, a Grade 3 engineer booked Taj West End at ₹14,000/night. I found out 2 WEEKS later when the expense report came in.

How did it happen? The coordinator saw "Taj" and thought "preferred vendor." Didn't check the GRADE. The engineer didn't know any better. And the system? No policy check.

I had to call the engineer: "Why did you book Taj at ₹14K?" He said: "It was a preferred hotel, right?" Wrong. Preferred doesn't mean recommended for YOUR grade.

**Interviewer:** What if the tool could catch this?

**Vikram:** That's the DREAM. "Grade 3 + Taj West End ₹14K = POLICY VIOLATION. Suggest: Taj budget hotel ₹7,500 (within policy)."

If the system auto-rejects policy violations BEFORE booking? That saves me ₹45L/year in overpayments AND the headache of chasing people after the fact.

---

### Section 2: The Concur Cost Pain**

**Interviewer:** You mentioned Concur costs ₹4.8L/year. Is it worth it?

**Vikram:** *(hesitates)* No. Not really.

Let me break it down:
- **License:** ₹400/user/month × 1,200 employees = ₹4.8L/year
- **What we get:** Booking platform (clunky), expense integration (okay), analytics (useless)
- **What we DON'T get:** Real-time policy enforcement, vendor rate comparison, predictive analytics

I pay ₹4.8L for... what exactly? My coordinators still use WhatsApp for 60% of bookings because Concur is "too slow for urgent trips."

If this Agency OS tool can do policy enforcement + vendor rate comparison + analytics for ₹50-75K/year? That's 6x cheaper than Concur.

**Interviewer:** Would you switch from Concur?

**Vikram:** For the RIGHT tool? In a heartbeat.

But — and this is big — Concur does ONE thing well: expense integration. When an employee books through Concur, it automatically creates the expense entry in SAP.

If I switch to Agency OS, I need:
1. Policy enforcement ✓ (this is why I switch)
2. Vendor rate comparison ✓ (save ₹45L/year)
3. **Expense integration** — can it push to SAP?
4. **Approval workflows** — managers approve trips >₹50K

If it has 1, 2, 3, 4? I'd switch 1,200 employees tomorrow.

---

### Section 3: Duty of Care Concerns**

**Interviewer:** Tell me about "Duty of Care." How do you track where employees are?

**Vikram:** *(pause)* With great difficulty.

We have 1,200 employees. On any given day, maybe 80 are traveling. Where? Which cities? Which countries? Do they have valid visas? Is the destination safe?

Last year, we had a coup in Country X. Three of our employees were there. I found out from THEIR EMAILS: "Vikram, there's a coup here, what do we do?"

I didn't KNOW they were there. My "system" is a WhatsApp group: "Who's traveling to Country X next week? Reply with dates."

**Interviewer:** What would the ideal tool do?

**Vikram:** A "Duty of Care" dashboard:
- **Live view:** 80 employees traveling today. Where? Which hotel? Emergency contact?
- **Visa alerts:** "5 employees traveling to China next week. 2 don't have Chinese visas."
- **Safety alerts:** "Coup in Country X. 3 employees there. Auto-alert: 'Book earliest flight home?'"
- **Insurance check:** "12 employees traveling next week. 3 don't have travel insurance."

This isn't just convenience. It's LEGAL liability. If an employee gets stuck in a coup and we didn't know they were there? That's negligence.

---

### Section 4: The CFO Reporting Pain**

**Interviewer:** Walk me through a typical CFO report.

**Vikram:** Once a quarter, the CFO asks: "Show me the travel spend. Where, why, and how to reduce it."

I spend 3-4 DAYS building a PowerPoint:
- Slide 1: Total spend ₹18Cr (breakdown: flights 40%, hotels 35%, cabs 15%, other 10%)
- Slide 2: Top 10 vendors (Hotel X ₹3.2Cr, Airline Y ₹5.1Cr...)
- Slide 3: Policy violations (12 this quarter, total ₹8L wasted)
- Slide 4: Savings opportunities (switch Hotel X → Y = ₹45L saved)

It's 4 days of Excel hell. And then the CFO asks: "Why did Hotel X costs go up 15% this quarter?" I have to go BACK to Excel. 2 more days.

**Interviewer:** What if the tool generated this automatically?

**Vikram:** *(long pause)* I'd pay ₹1L/month for that. Seriously.

"CFO Dashboard" — auto-generated every quarter:
- Total spend + breakdown
- Vendor performance (who's overcharging?)
- Policy violations (auto-detected)
- Savings opportunities (AI-recommended switches)
- Trend analysis: "Hotel X costs up 15% — renegotiate or switch"

If I could generate that in 5 minutes instead of 4 days? That's ₹50-75K value per quarter. ₹2-3L/year.

---

### Section 5: The Approval Workflow Problem**

**Interviewer:** How do trip approvals work today?

**Vikram:** Chaos.

An employee books a trip. If it's <₹50K, auto-approved. If >₹50K, manager approval needed. If >₹2L, VP approval needed.

But here's the problem: the coordinator sees the booking AFTER it's made. "Oops, this is ₹3L, needs VP approval." Now we're asking the employee: "Can you cancel and rebook?"

The tool should check BEFORE booking: "This is ₹3L, Grade 3. VP approval required. Block until approved."

And the manager/VP should get an email: "Approve or reject." Not a WhatsApp: "Sir, please approve this trip."

---

### Section 6: The "Preferred Vendor" Myth**

**Interviewer:** You mentioned preferred vendors. How do you track if they're actually preferred?

**Vikram:** *(laughs)* It's a list in Excel. "Preferred Hotels: Taj, IHG, Marriot." That's it.

I don't know:
- Which agencies are ACTUALLY booking them? (maybe 40% use Leela instead)
- Which ones are overcharging us? (Taj corporate rate ₹8.5K, but we're paying ₹9.5K because coordinators don't know the rate)
- Which ones have complaints? (Taj Whitefield had 8 complaintes this quarter — dirty rooms, slow wifi)

The tool should track: "Agency X booked Taj 15 times. Average rate: ₹9.2K. Your corporate rate: ₹8.5K. You're overpaying ₹7K/night = ₹1.05L wasted."

That's the intelligence I need.

---

### Section 7: Dream Feature**

**Interviewer:** Your magic wand, Vikram?

**Vikram:** *(thinks for a long time)*

A "Corporate Command Center" that shows me:

1. **Live map:** Where are my 80 traveling employees RIGHT NOW? (integrated with airline data)
2. **Policy engine:** Auto-reject bookings that violate grade limits
3. **Vendor intelligence:** "Hotel X overcharging by 21%. Switch to Y, save ₹45L/year"
4. **CFO Dashboard:** Auto-generated quarterly reports with savings opportunities
5. **Duty of Care:** "3 employees in coup-affected Country X. Evacuate?"
6. **Approval workflow:** Manager/VP auto-notified for >₹50K trips

But here's the key: it needs to integrate with SAP. The expense entry should be AUTOMATIC. If I have to manually enter 1,200 expense reports? No thanks.

If this tool does all 6 things for ₹1L/month? I'd switch 1,200 employees TOMORROW. That's ₹12L/year vs. ₹4.8L for Concur. But the VALUE? 10x.

---

## 4. Key Findings**

### Finding 1: The CFO Reporting Burden Is Enormous**

Vikram spends 3-4 DAYS per quarter building travel spend reports in Excel. The CFO asks follow-ups that add 2 more days. Total: 12-16 days/year on reporting alone.

**Implication:** Auto-generated CFO dashboards (quarterly spend, vendor performance, savings opportunities) would save 12-16 days/year and justify ₹1L/month pricing.

### Finding 2: Policy Enforcement Is the #1 Buying Trigger**

Vikram would switch from Concur specifically for real-time policy enforcement: "Grade 3 + ₹14K hotel = BLOCK." This prevents ₹45L/year in policy violations.

**Implication:** Policy engine (grade-based limits, auto-reject, escalation workflow) is the #1 feature for corporate adoption. Build this first.

### Finding 3: Concur's Cost Is the Comparator**

Concur charges ₹4.8L/year for 1,200 users. Vikram would switch for ₹12L/year IF the tool includes: policy enforcement, vendor intelligence, CFO dashboards, duty of care, AND SAP expense integration.

**Implication:** Pricing for enterprise: ₹1-1.5L/month for 1,000+ employee companies. Break the cost down: "6x cheaper than Concur, 10x better intelligence."

### Finding 4: Duty of Care Is a Legal Liability**

Tracking 80 traveling employees during a coup/aandemic/natural disaster is currently done via WhatsApp. Vikram didn't know 3 employees were in a coup zone until they emailed him.

**Implication:** "Duty of Care" dashboard (live traveler map, visa alerts, safety alerts, insurance checks) is a compliance feature, not just nice-to-have. Legal departments will mandate this.

### Finding 5: Vendor Rate Comparison Drives ROI**

Manual comparison (2 weeks, 3 people) found ₹45L/year overpayment to Hotel X. The tool should do this in 5 seconds: "You're paying ₹8.5K, market rate ₹7K, switch and save ₹45L."

**Implication:** Vendor rate comparison engine (your rate vs. market rate) is the highest-ROI feature. ₹45L savings for a ₹1L/month tool = 45x ROI.

### Finding 6: Expense Integration Is the Gating Factor**

Vikram won't switch from Concur unless the tool pushes expense entries to SAP automatically. Manual expense entry for 1,200 employees is a non-starter.

**Implication:** SAP/ERP integration (or at minimum, bulk CSV export for finance teams) is a gating requirement for enterprise adoption. No integration = no enterprise sales.

### Finding 7: Preferred Vendor Tracking Is Broken**

"Preferred vendors" is an Excel list. No tracking of ACTUAL usage, overpayment vs. corporate rates, or complaint trends. The tool should provide vendor intelligence: "You're overpaying Taj by 21%, 8 complaints this quarter."

**Implication:** Vendor performance scoring (rate compliance, complaint trends, usage tracking) is a differentiator vs. Concur's static vendor lists.

### Finding 8: Approval Workflow Must Be Pre-Booking**

Current process: book first, check policy later. This causes cancellations and rebookings. The tool should BLOCK non-compliant bookings BEFORE they happen.

**Implication:** Pre-booking approval workflow: "₹3L trip, Grade 3 → VP approval required. Block until approved." This prevents the "oops, cancel and rebook" waste.

---

## 5. Prioritized Recommendations (Corporate Perspective)**

| Priority | Feature | Why | Corporate ROI |
|----------|---------|-----|---------------|
| **P0** | Policy engine (grade-based limits) | Prevents ₹45L/year in violations | 45x ROI |
| **P0** | Vendor rate comparison (your rate vs. market) | Found ₹45L overpayment in 2 weeks | 45x ROI |
| **P1** | CFO Dashboard (auto-generated quarterly) | Saves 12-16 days/year on reporting | ₹2-3L/year in time saved |
| **P1** | Duty of Care (live traveler map + alerts) | Legal compliance, negligence prevention | Priceless (liability) |
| **P1** | Approval workflow (pre-booking) | Prevents cancellations/rebookings | ₹8L/year in waste |
| **P2** | SAP/ERP expense integration | Gating factor for Concur switch | Required for enterprise |
| **P2** | Vendor performance scoring | "Taj: 8 complaints, 21% overpayment" | Smarter negotiations |
| **P3** | Traveler mobile app (self-book, policy check) | Reduces coordinator workload | 2x team capacity |

---

## 6. Quotes Worth Remembering**

> "I'm spending ₹18Cr a year and I can't tell you which vendor is overcharging me."

> "Concur costs ₹4.8L/year. You know what it told me? 'Your top vendor is Hotel X at ₹3.2Cr.' That's IT."

> "If the system auto-rejects policy violations BEFORE booking? That saves me ₹45L/year."

> "I pay ₹4.8L for Concur... for WHAT EXACTLY? My coordinators still use WhatsApp for 60% of bookings."

> "If an employee gets stuck in a coup and we didn't know they were there? That's negligence."

> "I'd pay ₹1L/month for that [CFO Dashboard]. Seriously."

> "If this tool does all 6 things for ₹1L/month? I'd switch 1,200 employees TOMORROW."

---

## 7. Methodology Notes**

- Simulated interview based on Persona P4 (Corporate Travel Manager) created earlier in `Docs/personas/PERSONA_CORPORATE_TRAVEL_MANAGER.md`.
- Corporate travel dynamics drawn from `Docs/INDUSTRY_ROLES_AND_AI_AGENT_MAPPING.md` (Tier 2: Corporate Travel Manager, lines 130-170).
- Concur pricing (₹400/user/year) validated against real enterprise SaaS benchmarks.
- Policy engine concept inspired by gaps in current system: no grade-based limits, no approval workflows.
- **Validation:** Check with real corporate travel managers at 500-5,000 employee companies. Their ₹5-50Cr annual spend creates acute pain that SMEs don't face.
- **Next Step:** Create scenarios P4-S4 through P4-S8 as separate files.
