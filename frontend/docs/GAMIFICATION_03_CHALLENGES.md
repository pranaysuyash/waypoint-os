# Gamification — Challenges & Quests

> Research document for time-limited challenges, team competitions, and quest-based learning.

---

## Key Questions

1. **What types of challenges drive the right behaviors?**
2. **How long should challenges run (daily, weekly, monthly)?**
3. **How do we design team challenges that don't create free-rider problems?**
4. **What rewards are appropriate (recognition, privileges, tangible)?**
5. **How do quests tie into agent training and skill development?**

---

## Research Areas

### Challenge Types

```typescript
interface Challenge {
  challengeId: string;
  name: string;
  description: string;
  type: ChallengeType;
  duration: ChallengeDuration;
  goal: ChallengeGoal;
  participants: ChallengeParticipant[];
  rewards: ChallengeReward[];
  status: 'upcoming' | 'active' | 'completed';
}

type ChallengeType =
  | 'individual_daily'          // Quick daily goals
  | 'individual_weekly'         // Weekly targets
  | 'individual_monthly'        // Monthly objectives
  | 'team_weekly'               // Team-based competition
  | 'team_vs_team'              // Inter-team competition
  | 'company_wide'              // Everyone participates
  | 'learning_quest';           // Skill development path

interface ChallengeGoal {
  metric: string;
  target: number;
  currentValues: Record<string, number>;  // Per participant
  unit: string;
}

// Example challenges:
// Daily: "Respond to all inquiries within 10 minutes today"
// Weekly: "Achieve 4.5+ CSAT on all bookings this week"
// Monthly: "Complete your destination specialization certification"
// Team: "Team Alpha: Close ₹20L in bookings this week"
// Team vs Team: "Highest team conversion rate this month"
// Learning quest: "Master Southeast Asia destinations" (5 modules)
```

### Quest System

```typescript
interface Quest {
  questId: string;
  name: string;
  description: string;
  theme: string;                    // "Southeast Asia Expert"
  steps: QuestStep[];
  totalEstimatedTime: string;
  reward: QuestReward;
  prerequisites?: string[];         // Must complete these quests first
}

interface QuestStep {
  stepId: string;
  title: string;
  type: 'learn' | 'practice' | 'demonstrate';
  content?: string;                 // Learning material
  task?: string;                    // What to do
  verification: VerificationMethod;
  points: number;
  completedAt?: Date;
}

type VerificationMethod =
  | 'quiz_score'                  // Pass a quiz
  | 'booking_completion'          // Complete a real booking
  | 'peer_review'                 // Reviewed by senior agent
  | 'mentor_signoff'              // Mentor confirms competence
  | 'simulation_pass';            // Complete a simulation

// Quest example: "Singapore Specialist"
// Step 1: Learn — Read Singapore destination guide (15 min)
// Step 2: Learn — Study top 10 Singapore hotels (20 min)
// Step 3: Practice — Complete Singapore booking simulation
// Step 4: Demonstrate — Book 3 real Singapore trips with 4.5+ CSAT
// Step 5: Learn — Pass Singapore specialist quiz (80%+ score)
// Reward: "Singapore Specialist" badge + higher commission rate on SG bookings
```

### Team Challenges

```typescript
interface TeamChallenge {
  challengeId: string;
  teams: ChallengeTeam[];
  scoring: TeamScoring;
  duration: string;
  rewards: TeamReward[];
}

interface ChallengeTeam {
  teamId: string;
  teamName: string;
  members: string[];
  score: number;
  rank: number;
}

type TeamScoring =
  | 'total_combined'             // Sum of individual scores
  | 'average_per_member'         // Average score per team member
  | 'all_must_contribute';       // Every member must participate

// Anti free-rider:
// - "All must contribute" mode requires every team member to meet minimum threshold
// - Individual contribution visible to team lead
// - Bonus points for helping struggling teammates
```

### Rewards

```typescript
type ChallengeReward =
  // Recognition (free, scalable)
  | { type: 'badge'; badgeId: string }
  | { type: 'title'; title: string }              // "Agent of the Month"
  | { type: 'profile_highlight'; duration: string }
  | { type: 'announcement'; channel: string }
  // Privileges (low cost, high perceived value)
  | { type: 'first_pick'; description: string }   // First choice of leads
  | { type: 'flexible_hours'; duration: string }
  | { type: 'training_budget'; amount: number }
  | { type: 'conference_attendance' }
  // Tangible (budget required)
  | { type: 'gift_card'; amount: number }
  | { type: 'team_lunch'; budget: number }
  | { type: 'extra_day_off' }
  | { type: 'device_upgrade' };
```

---

## Open Problems

1. **Challenge fatigue** — Too many concurrent challenges overwhelm agents. Need a calendar that spaces challenges appropriately.

2. **Reward budget** — Tangible rewards cost money. Need to balance gamification budget against ROI from improved performance.

3. **Quest content creation** — Learning quests need quality content (destination guides, quizzes, simulations). Content creation is a significant investment.

4. **Fair team composition** — Random team assignment may stack top performers on one team. Need balanced team creation.

5. **Challenge alignment** — Challenges must align with business goals. A "most bookings" challenge may not serve the customer experience goal.

---

## Next Steps

- [ ] Design monthly challenge calendar for next quarter
- [ ] Create 5 learning quest outlines for top destinations
- [ ] Design team challenge with anti-free-rider mechanics
- [ ] Study challenge design in Duolingo, Strava, Salesforce
- [ ] Pilot weekly challenge with one team
