# Voice & Conversational AI — Agent Assist & Call Intelligence

> Research document for real-time call transcription, agent prompts, call analytics, and AI-powered call assistance.

---

## Key Questions

1. **How do we provide real-time assistance to agents during calls?**
2. **What AI prompts and suggestions improve call quality?**
3. **How do we analyze call recordings for quality and training?**
4. **What's the post-call automation workflow?**
5. **How do we measure and improve agent voice performance?**

---

## Research Areas

### Real-Time Call Assistance

```typescript
interface AgentAssist {
  callId: string;
  agentId: string;
  transcription: RealTimeTranscription;
  prompts: AgentPrompt[];
  knowledge: InCallKnowledge;
  actions: SuggestedAction[];
}

interface RealTimeTranscription {
  enabled: boolean;
  language: string;
  segments: TranscriptSegment[];
  latency: string;                    // "< 500ms" target
}

// Real-time transcription display:
// ┌──────────────────────────────────────────┐
// │  Call: Rajesh Sharma (+91 98765 43210)    │
// │  Duration: 03:45                          │
// │                                          │
// │  Live Transcript:                         │
// │  Customer: "I want to plan a trip to      │
// │    Kerala, around December second week"   │
// │  Agent: "Kerala is beautiful in December!  │
// │    Let me get some details..."            │
// │  Customer: "It's for me and my wife,      │
// │    5 nights, maybe houseboat"             │
// │                                          │
// │  AI Suggestions:                          │
// │  ┌────────────────────────────────────┐  │
// │  │ 📋 Detected: Kerala, Dec 8-14,     │  │
// │  │    2 adults, 5 nights, houseboat   │  │
// │  │                                    │  │
// │  │ 💡 Ask about: Budget range         │  │
// │  │ 💡 Mention: Honeymoon packages     │  │
// │  │ 💡 Cross-sell: Travel insurance    │  │
// │  │                                    │  │
// │  │ 🔍 Quick Search:                   │  │
// │  │ [Search Kerala Trips]              │  │
// │  └────────────────────────────────────┘  │
// └──────────────────────────────────────────┘

interface AgentPrompt {
  type: PromptType;
  content: string;
  priority: number;
  triggeredBy: string;                // What triggered this prompt
}

type PromptType =
  | 'information_capture'             // "Customer mentioned 2 adults — confirm?"
  | 'next_question'                   // "Ask about budget range"
  | 'cross_sell'                      // "Suggest travel insurance"
  | 'up_sell'                         // "Premium houseboat available for ₹3,000 more"
  | 'objection_handling'              // Customer said "too expensive"
  | 'compliance'                      // "Inform customer about cancellation policy"
  | 'knowledge'                       // "Kerala weather in December: 25-30°C"
  | 'sentiment_alert'                 // "Customer sounds frustrated — be empathetic"
  | 'fact_check';                     // "Don't promise visa-on-arrival — it's e-visa"

// Prompt timing:
// Information capture: Immediate (as entity detected)
// Next question: After agent finishes speaking
// Cross-sell: After trip selection, before payment
// Up-sell: During trip presentation
// Objection handling: When customer expresses concern
// Compliance: Before confirming booking (mandatory prompts)
// Knowledge: When destination/topic mentioned
// Sentiment: When negative sentiment detected
// Fact check: When agent makes a claim that might be incorrect

interface InCallKnowledge {
  destination?: DestinationQuickFact[];
  hotel?: HotelQuickFact[];
  visa?: VisaQuickFact[];
  policy?: PolicyQuickFact[];
}

// In-call knowledge cards (auto-surfaced based on conversation):
//
// When "Kerala" mentioned:
// ┌────────────────────────────────────┐
// │  Kerala Quick Facts                │
// │  Best time: Sep-Mar                │
// │  Weather Dec: 25-32°C, pleasant   │
// │  Top experiences: Backwaters,      │
// │    Munnar, Periyar, Kochi          │
// │  Avg budget: ₹15-30K per person   │
// │  Visa: Not needed (domestic)       │
// │  [Open Full Guide]                 │
// └────────────────────────────────────┘
//
// When customer asks about visa for Thailand:
// ┌────────────────────────────────────┐
// │  Thailand Visa for Indians         │
// │  Type: Visa on Arrival             │
// │  Fee: ₹2,000 (THB 2,000)         │
// │  Duration: 15 days                 │
// │  Documents: Passport (6mo valid),  │
// │    return ticket, hotel booking    │
// │  Processing: On arrival at airport │
// │  Note: Can also apply e-Visa       │
// │  [Open Full Visa Guide]            │
// └────────────────────────────────────┘
```

### Post-Call Automation

```typescript
interface PostCallAutomation {
  callId: string;
  summary: CallSummary;
  actions: PostCallAction[];
  followUp: FollowUpSchedule;
  training: TrainingInsight;
}

interface CallSummary {
  duration: string;
  type: CallType;
  outcome: CallOutcome;
  customerIntent: string;
  keyTopics: string[];
  entities: ExtractedEntities;
  actionItems: string[];
  sentiment: CallSentiment;
  bookingCreated: boolean;
  bookingId?: string;
  nextSteps: string;
}

// Auto-generated call summary (appears in Workbench after call):
// ┌──────────────────────────────────────────┐
// │  Call Summary — Rajesh Sharma             │
// │  Duration: 7:23 · Outcome: Booking Created│
// │                                          │
// │  Intent: Kerala trip inquiry              │
// │  Destination: Kerala (Alleppey, Munnar)  │
// │  Dates: Dec 10-15, 2026                  │
// │  Travelers: 2 adults                     │
// │  Budget: ₹25-30K per person              │
// │                                          │
// │  Booking: TRV-45678 — ₹55,000            │
// │  Payment: ₹16,500 advance (link sent)    │
// │  Balance: ₹38,500 due by Nov 25          │
// │                                          │
// │  Action Items:                            │
// │  □ Confirm hotel availability             │
// │  □ Send detailed itinerary                │
// │  □ Follow up on payment (if not done)     │
// │                                          │
// │  Sentiment: Positive (8/10)              │
// │  Cross-sell opportunity: Travel insurance │
// │                                          │
// │  [View Full Transcript] [Send Follow-up] │
// └──────────────────────────────────────────┘

interface PostCallAction {
  action: string;
  type: 'auto' | 'manual';
  status: 'pending' | 'completed';
  deadline?: Date;
}

// Automated post-call actions:
// 1. Create booking in Workbench (auto, if booking made)
// 2. Send WhatsApp confirmation (auto)
// 3. Send email with itinerary summary (auto)
// 4. Send payment link (auto, if payment pending)
// 5. Schedule follow-up reminder (auto, per policy)
// 6. Update customer profile with call notes (auto)
// 7. Log call recording and transcript (auto)
// 8. Trigger NPS survey (auto, 1 hour after call)
//
// Manual follow-up:
// - Confirm hotel availability (within 4 hours)
// - Send detailed itinerary PDF (within 24 hours)
// - Follow up on payment (if not completed within 24 hours)
// - Send pre-departure guide (7 days before trip)
```

### Call Quality Analytics

```typescript
interface CallQualityAnalytics {
  callScoring: CallScore[];
  complianceChecks: ComplianceCheck[];
  agentMetrics: AgentCallMetrics;
  coaching: CoachingInsight[];
}

interface CallScore {
  callId: string;
  agentId: string;
  overallScore: number;               // 0-100
  dimensions: ScoreDimension[];
  highlights: string[];
  improvements: string[];
}

interface ScoreDimension {
  dimension: string;
  score: number;
  weight: number;
  examples: string[];
}

// Call quality dimensions:
// 1. Greeting & Introduction (10%)
//    - Did agent greet professionally?
//    - Did agent identify themselves and the agency?
//    - Did agent ask how they could help?
//
// 2. Needs Discovery (20%)
//    - Did agent ask about destination, dates, travelers?
//    - Did agent ask about budget?
//    - Did agent ask about preferences and special needs?
//    - Did agent listen without interrupting?
//
// 3. Product Knowledge (20%)
//    - Did agent provide accurate destination information?
//    - Did agent present suitable options?
//    - Did agent explain inclusions and exclusions?
//    - Did agent answer questions accurately?
//
// 4. Sales Technique (15%)
//    - Did agent present options enthusiastically?
//    - Did agent address objections professionally?
//    - Did agent suggest relevant add-ons (insurance, transfers)?
//    - Did agent create urgency without being pushy?
//
// 5. Communication Skills (15%)
//    - Was agent clear and articulate?
//    - Was agent's tone warm and professional?
//    - Did agent use appropriate pace (not too fast/slow)?
//    - Did agent avoid jargon?
//
// 6. Closing & Follow-up (10%)
//    - Did agent summarize next steps?
//    - Did agent confirm customer understanding?
//    - Did agent provide booking reference?
//    - Did agent end professionally?
//
// 7. Compliance (10%)
//    - Did agent inform about call recording?
//    - Did agent state cancellation policy?
//    - Did agent not make unverifiable claims?
//    - Did agent follow payment compliance?

interface ComplianceCheck {
  check: string;
  passed: boolean;
  severity: 'mandatory' | 'recommended';
  evidence: string;                   // Transcript excerpt
}

// Mandatory compliance checks:
// - Call recording disclosure at start of call
// - Cancellation policy mentioned before booking
// - Total price stated clearly (no hidden charges)
// - Payment terms explained
// - Customer verbal consent recorded
// - No promises of visa guarantee (legal issue)
// - No discriminatory language
// - Customer data handled per DPDP Act
//
// AI-powered compliance monitoring:
// Real-time: Flag mandatory disclosures that haven't been made
// Post-call: Score compliance, flag violations
// Monthly: Compliance report per agent
```

### Agent Coaching & Training

```typescript
interface AgentCoaching {
  agentId: string;
  scorecard: AgentScorecard;
  recommendedTraining: TrainingRecommendation[];
  topCalls: TopCallReference[];
  weeklyInsights: WeeklyInsight[];
}

interface AgentScorecard {
  overallScore: number;
  callsThisWeek: number;
  bookingsThisWeek: number;
  conversionRate: number;
  avgCallDuration: string;
  customerSatisfaction: number;
  improvementAreas: string[];
}

// Weekly coaching report (auto-generated):
// ┌──────────────────────────────────────────┐
// │  Agent Performance — Week of Apr 21      │
// │                                          │
// │  Score: 78/100 (↑ 3 from last week)     │
// │                                          │
// │  Calls: 42  Bookings: 11 (26% conv.)    │
// │  Avg Duration: 6.5 min                   │
// │  CSAT: 4.2/5.0                           │
// │                                          │
// │  Strengths:                              │
// │  ✅ Excellent product knowledge          │
// │  ✅ Good at handling objections           │
// │  ✅ Warm and professional tone            │
// │                                          │
// │  Improve:                                │
// │  ⚠️ Ask about budget earlier in call     │
// │  ⚠️ Mention insurance more consistently  │
// │  ⚠️ Don't interrupt customers            │
// │                                          │
// │  Recommended Training:                   │
// │  📚 "Budget Discovery Techniques"        │
// │  📚 "Cross-Selling Insurance"            │
// │                                          │
// │  [Listen to Top Call] [Start Training]   │
// └──────────────────────────────────────────┘

// Call coaching insights (LLM-powered):
// "Your conversion rate on international packages is 32%,
//  compared to 18% on domestic. Consider applying the same
//  consultative approach (asking about preferences before
//  presenting options) to domestic inquiries."
//
// "On 3 calls this week, customers asked about visa processing
//  and you had to put them on hold to check. Consider reviewing
//  the Thailand and Singapore visa guides to answer confidently."
//
// "Your average handle time is 8.2 minutes — above the team
//  average of 6.5. The extra time is mostly on pricing
//  explanations. Try using the comparison view to show prices
//  visually while explaining on the call."
```

---

## Open Problems

1. **Transcription latency** — Real-time transcription with <500ms latency is challenging on Indian telephony (8kHz audio). Need edge processing or optimized models.

2. **Agent adoption** — Agents may find real-time prompts distracting or feel micromanaged. Need to design non-intrusive assistance that agents welcome.

3. **Privacy concerns** — Call recording and AI analysis may worry agents about surveillance. Need transparent policies and agent benefit framing.

4. **Multilingual coaching** — Coaching insights for Hindi calls require Hindi NLP. Most call analytics tools are English-first.

5. **Cost-benefit balance** — Full call analytics (transcription + scoring + coaching) costs ₹10-20/call. For 100 calls/day, that's ₹30-60K/month. Need ROI justification.

---

## Next Steps

- [ ] Build real-time call transcription with agent assist panel
- [ ] Design post-call automation with summary and action items
- [ ] Create call quality scoring with automated compliance checks
- [ ] Build agent coaching system with weekly insights and training recommendations
- [ ] Study call analytics platforms (Gong, Chorus.ai, Observe.ai, Convoso)
