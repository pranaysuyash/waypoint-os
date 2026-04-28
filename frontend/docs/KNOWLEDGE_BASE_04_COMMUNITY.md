# Knowledge Base & Internal Wiki — Community & Contributions

> Research document for knowledge contributions, community features, and collaborative knowledge building.

---

## Key Questions

1. **How do we incentivize agents to contribute knowledge?**
2. **What community features foster knowledge sharing?**
3. **How do we ensure contributed content quality?**
4. **What's the moderation model?**
5. **How do we measure knowledge base health?**

---

## Research Areas

### Contribution Model

```typescript
interface KnowledgeContribution {
  contributionId: string;
  contributorId: string;
  type: ContributionType;
  content: string;
  status: ContributionStatus;
  review: ContributionReview;
  rewards: ContributionReward;
}

type ContributionType =
  | 'new_article'                    // Create a new knowledge article
  | 'update_existing'                // Update an existing article
  | 'agent_tip'                      // Quick tip (1-3 sentences)
  | 'destination_review'             // Review/rate a destination
  | 'supplier_review'                // Review/rate a supplier
  | 'trip_story'                     // Story from a completed trip (lessons learned)
  | 'answer_question'                // Answer a community question
  | 'report_issue';                  // Report outdated/incorrect info

type ContributionStatus =
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'revision_requested'
  | 'rejected'
  | 'published';

// Contribution incentives:
// Recognition:
//   - "Knowledge Champion" badge for 50+ contributions
//   - Leaderboard: Top contributors this month
//   - Contributor name shown on published articles
//
// Rewards:
//   - Contribution points toward gamification
//   - Premium feature access for top contributors
//   - Annual "Knowledge Builder" award
//
// Professional development:
//   - Contributions count toward specialist certification
//   - Mentor qualification requires knowledge contributions
//   - Performance review includes knowledge sharing

// Frictionless contribution:
// 1. Quick tip: 1-3 sentences, submitted in <30 seconds
// 2. Article update: Suggest edit button on any article
// 3. Flag outdated: One-click "This is outdated" with optional note
// 4. Trip story: Auto-generated template from completed trip data
```

### Community Features

```typescript
interface KnowledgeCommunity {
  questions: CommunityQuestion[];
  discussions: DiscussionThread[];
  experts: ExpertProfile[];
  events: CommunityEvent[];
}

interface CommunityQuestion {
  questionId: string;
  author: string;
  question: string;
  context: string;                   // Trip context, destination, supplier
  tags: string[];
  answers: CommunityAnswer[];
  status: 'open' | 'answered' | 'resolved';
  bounty?: ContributionReward;       // Extra reward for answering
}

// Community Q&A examples:
// Q: "Has anyone booked the new Bali express visa? How long does it actually take?"
// A: "I did last week. Applied Monday, approved Wednesday. The online portal is faster than VFS."
//
// Q: "Best hotel for a family of 5 in Singapore? Need connecting rooms."
// A: "Resorts World Sentosa has family suites that sleep 6. Book the Beach Villas if budget allows."
//
// Q: "Indigo cancelled my customer's flight. What's the quickest rebooking path?"
// A: "Call their agency helpline (not the regular one). They have a dedicated line for agents."

interface ExpertProfile {
  agentId: string;
  expertise: ExpertiseArea[];
  questionsAnswered: number;
  avgResponseTime: string;
  satisfactionRating: number;
  available: boolean;
}

type ExpertiseArea =
  | { destination: string; tripsBooked: number }
  | { supplier: string; yearsExperience: number }
  | { skill: string; certificationLevel: string };

// Expert matching:
// When a question is posted about "Singapore visa for Pakistani nationals":
// 1. Find agents with Singapore expertise (50+ trips booked)
// 2. Find agents who've handled Pakistani nationality visas
// 3. Notify top 3 experts via in-app notification
// 4. Expert answers → Question resolved → Knowledge base updated
```

### Moderation Model

```typescript
interface ModerationSystem {
  moderators: Moderator[];
  rules: ModerationRule[];
  queue: ModerationQueue;
}

interface ModerationRule {
  ruleType: ModerationRuleType;
  action: ModerationAction;
  threshold: number;
}

type ModerationRuleType =
  | 'new_article'                    // All new articles need review
  | 'article_update'                 // Updates need review if > 50% changed
  | 'agent_tip'                      // Tips auto-publish, flagged if 2+ downvotes
  | 'question'                       // Questions auto-publish
  | 'answer'                         // Answers auto-publish
  | 'report';                        // Reports need review

type ModerationAction =
  | 'auto_publish'
  | 'require_review'
  | 'require_approval'
  | 'auto_reject';

// Moderation queue priority:
// 1. Reported content (potential misinformation) — Immediate review
// 2. New articles from new contributors — Review within 4 hours
// 3. Updates to popular articles — Review within 24 hours
// 4. New articles from trusted contributors — Auto-publish with spot-check
// 5. Minor updates (typos, formatting) — Auto-publish

// Quality criteria for moderators:
// 1. Factually accurate (verify claims against sources)
// 2. Not duplicating existing content
// 3. Written clearly and concisely
// 4. Not promoting a specific supplier unfairly
// 5. Follows content guidelines (no offensive content, no competitor pricing)
```

### Knowledge Base Health Metrics

```typescript
interface KnowledgeBaseHealth {
  // Coverage metrics
  totalArticles: number;
  destinationsCovered: number;
  suppliersCovered: number;
  coverageGaps: CoverageGap[];

  // Quality metrics
  avgArticleRating: number;
  outdatedArticleCount: number;
  unreviewedArticleCount: number;

  // Engagement metrics
  monthlyViews: number;
  monthlyContributions: number;
  monthlyQuestions: number;
  avgAnswerTime: string;

  // Community metrics
  activeContributors: number;
  expertCoverage: number;            // % of topics with identified experts
  contributorRetention: number;      // % who contribute again after first contribution
}

interface CoverageGap {
  type: 'destination' | 'supplier' | 'procedure' | 'topic';
  description: string;
  demand: number;                    // How often this is searched/requested
  priority: 'high' | 'medium' | 'low';
}

// Health score:
// Coverage: 40% (How much of what agents need is documented)
// Quality: 85% (How good is what we have)
// Engagement: 70% (How much agents use and contribute)
// Freshness: 60% (How current is the content)
// Overall: 65/100 → Target: 80/100

// Monthly health report:
// "Knowledge Base Health Report — April 2026
//  Coverage: Added 15 new destination guides (now 85/100 major destinations)
//  Quality: 3 articles flagged as outdated, 2 corrected
//  Engagement: 120 contributions this month (up 15% from March)
//  Top contributor: Agent Priya (22 contributions, 18 verified)
//  Gaps: 10 destinations still missing guides, prioritized by booking volume"
```

---

## Open Problems

1. **Knowledge hoarding** — Some agents view their knowledge as competitive advantage and won't share. Need cultural change, not just incentives.

2. **Quality vs. quantity** — Gamified contributions may lead to low-quality content for points. Need quality-weighted rewards.

3. **Moderation bottleneck** — As contributions grow, moderation becomes a bottleneck. Need community moderation (trusted contributors review content).

4. **Knowledge conflicts** — Two agents give contradictory tips about the same supplier. Need resolution mechanism and clear attribution.

5. **Attribution and credit** — If an agent's tip becomes part of an official guide, they should get credit. Need attribution tracking.

---

## Next Steps

- [ ] Design knowledge contribution model with incentives
- [ ] Build community Q&A system with expert matching
- [ ] Create moderation queue with quality criteria
- [ ] Design knowledge base health dashboard
- [ ] Study community knowledge platforms (Stack Overflow, Reddit, Quora)
