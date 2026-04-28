# Surveys & Feedback Collection — Survey Design & Distribution

> Research document for customer satisfaction surveys, NPS measurement, and feedback collection workflows.

---

## Key Questions

1. **What surveys do we need across the customer journey?**
2. **How do we design surveys that get high response rates?**
3. **What's the survey distribution model — when, how, to whom?**
4. **How do we handle negative feedback and escalation?**
5. **What's the survey analytics and reporting model?**

---

## Research Areas

### Survey Types

```typescript
type SurveyType =
  | 'post_booking'                    // After booking confirmation
  | 'post_trip'                       // After trip completion
  | 'nps'                             // Net Promoter Score (quarterly)
  | 'csat_interaction'                // After customer-agent interaction
  | 'service_quality'                 // Supplier service quality
  | 'agent_feedback'                  // Customer rating of agent service
  | 'feature_feedback'                // Feedback on new platform features
  | 'cancellation_reason'             // Why the customer cancelled
  | 'onboarding_experience'           // New customer onboarding feedback
  | 'brand_perception';               // Annual brand survey

interface Survey {
  surveyId: string;
  name: string;
  type: SurveyType;
  questions: SurveyQuestion[];
  trigger: SurveyTrigger;
  distribution: SurveyDistribution;
  responseTarget: number;
  estimatedMinutes: number;
  active: boolean;
}

interface SurveyQuestion {
  questionId: string;
  text: string;
  type: QuestionType;
  required: boolean;
  options?: string[];
  scaleMax?: number;
  followUpCondition?: FollowUpCondition;
}

type QuestionType =
  | 'rating_5'                        // 1-5 stars
  | 'rating_10'                       // 1-10 (NPS)
  | 'nps_score'                       // 0-10 with promoter/passive/detractor
  | 'yes_no'
  | 'single_choice'
  | 'multiple_choice'
  | 'text_short'                      // One-line text
  | 'text_long'                       // Multi-line text
  | 'emoji_rating'                    // Emoji-based satisfaction
  | 'slider'                          // Continuous scale
  | 'ranking';                        // Rank items in order

// Survey: Post-Trip Experience (main survey)
// Estimated time: 3-4 minutes
// Questions:
// 1. Overall trip rating (1-5 stars) — Required
// 2. How likely are you to recommend us? (0-10 NPS) — Required
// 3. Rate your agent's service (1-5 stars) — Required
// 4. Rate the itinerary quality (1-5 stars) — Required
// 5. Rate value for money (1-5 stars) — Required
// 6. What did you enjoy most? (multiple choice) — Optional
//    - Destinations visited, Activities, Hotel quality, Agent service,
//      Food experiences, Smooth logistics
// 7. What could be improved? (text) — Optional
// 8. Would you book with us again? (yes/no) — Required
// 9. Any additional feedback? (text) — Optional
//
// Conditional follow-ups:
// If NPS <= 6 (detractor): "We're sorry your experience wasn't great.
//   Would you like a callback from our team to discuss?"
// If NPS >= 9 (promoter): "Glad you loved it!
//   Would you like to leave a review on Google?"
```

### Survey Distribution

```typescript
interface SurveyTrigger {
  event: string;
  delayHours: number;                // Delay after triggering event
  conditions?: string[];
}

interface SurveyDistribution {
  channels: DistributionChannel[];
  maxReminders: number;
  reminderIntervalHours: number;
  expiryDays: number;
}

type DistributionChannel =
  | { type: 'whatsapp'; template: string }
  | { type: 'email'; template: string }
  | { type: 'in_app'; placement: string }
  | { type: 'sms'; template: string }
  | { type: 'post_trip_page'; url: string };

// Distribution strategy:
// Post-booking survey:
//   Trigger: Booking confirmed
//   Delay: 2 hours
//   Channel: WhatsApp (with email fallback)
//   Expiry: 7 days
//   Response target: 40%
//
// Post-trip survey:
//   Trigger: Trip completion (last travel date + 2 days)
//   Delay: 48 hours (let customer settle in)
//   Channel: WhatsApp + email
//   Reminder: 1 reminder after 3 days if no response
//   Expiry: 14 days
//   Response target: 30%
//
// NPS survey:
//   Trigger: Quarterly schedule (Jan, Apr, Jul, Oct)
//   Channel: Email (with in-app banner)
//   Expiry: 14 days
//   Response target: 20%
//
// Agent feedback:
//   Trigger: Trip completed
//   Delay: 48 hours
//   Channel: In-app (customer portal)
//   Expiry: 30 days
//   Response target: 25%
//
// Cancellation reason:
//   Trigger: Booking cancelled
//   Delay: Immediate (in cancellation flow)
//   Channel: In-app (mandatory in cancellation form)
//   Response target: 90% (built into cancellation flow)

// Response rate optimization:
// 1. Keep surveys short (3-5 questions, 2-3 minutes)
// 2. Mobile-first design (most responses on phone)
// 3. Use rating scales (faster than typing)
// 4. Send at optimal times (10 AM, not 8 PM)
// 5. One-click rating in WhatsApp (no redirect needed)
// 6. Thank-you message after completion
// 7. Optional incentive (discount on next booking)
```

### Feedback Escalation

```typescript
interface FeedbackEscalation {
  rules: EscalationRule[];
  actions: EscalationAction[];
}

interface EscalationRule {
  condition: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  responseTime: string;
}

// Escalation rules:
// NPS <= 3 (angry detractor):
//   → Critical: Agent calls customer within 4 hours
//   → Owner notified
//
// Rating <= 2 on any category:
//   → High: Team lead reviews within 24 hours
//   → Agent who handled trip is notified
//
// Mentions "refund" or "complaint" in text:
//   → Medium: Flagged for customer service review within 48 hours
//
// Rating 5 + positive text:
//   → Low: Thank you message sent, review request triggered
//
// Agent rating <= 2:
//   → High: HR/team lead notified, performance review flagged

// Feedback-to-action flow:
// 1. Customer submits negative feedback
// 2. System analyzes sentiment and identifies category
// 3. Escalation rule matched → Notification sent to responsible person
// 4. Responsible person reviews feedback and original trip details
// 5. Contacts customer within SLA
// 6. Resolution logged (apology, compensation, process improvement)
// 7. Follow-up survey sent to customer after resolution
```

---

## Open Problems

1. **Survey fatigue** — Too many surveys = low response rates and annoyed customers. Need to limit to 1 survey per customer per trip, maximum.

2. **Response bias** — Only very happy or very unhappy customers respond. The silent majority in the middle doesn't. Need strategies for middle-ground capture.

3. **WhatsApp survey limitations** — WhatsApp has template restrictions and character limits. Can't send long surveys via WhatsApp. Need to balance brevity with depth.

4. **Agent gaming** — Agents may ask customers to give 5-star ratings. Need to detect patterns (all 5-star for one agent) and anonymize survey results.

5. **Negative feedback handling** — A bad review can demoralize agents. Need constructive framing and focus on system improvement, not individual blame.

---

## Next Steps

- [ ] Design survey templates for each customer journey touchpoint
- [ ] Build WhatsApp-native survey flow with one-click ratings
- [ ] Create feedback escalation rules with automated routing
- [ ] Design survey analytics dashboard with NPS tracking
- [ ] Study survey UX (Typeform, Google Forms, Delighted, SurveyMonkey)
