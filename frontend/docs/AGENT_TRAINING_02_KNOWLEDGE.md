# Agent Training — Knowledge Base & Assessment

> Research document for agent knowledge management, continuous learning, and skill assessment.

---

## Key Questions

1. **What knowledge domains must agents master (destinations, suppliers, policies, systems)?**
2. **How do we keep knowledge current in a fast-changing travel landscape?**
3. **What assessment formats effectively measure practical competence?**
4. **How do we surface relevant knowledge in-context during active bookings?**
5. **What's the knowledge contribution workflow — who writes, reviews, publishes?**

---

## Research Areas

### Knowledge Domain Model

```typescript
type KnowledgeDomain =
  | 'destinations'         // Geography, attractions, culture, customs
  | 'products'             // Hotels, flights, activities — features and pricing
  | 'suppliers'            // Supplier capabilities, booking processes, contacts
  | 'policies'             // Cancellation, refund, change policies
  | 'systems'              // Platform tools, GDS, booking engines
  | 'compliance'           // Visa, insurance, regulatory requirements
  | 'sales'                // Selling techniques, objection handling, upselling
  | 'customer_service'     // Communication, conflict resolution, empathy
  | 'finance'              // Pricing, margins, payment processing
  | 'operations';          // Booking workflows, escalation procedures

interface KnowledgeArticle {
  articleId: string;
  domain: KnowledgeDomain;
  subdomain: string;
  title: string;
  content: string;
  format: 'article' | 'faq' | 'how_to' | 'video' | 'interactive';
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  lastReviewed: Date;
  nextReview: Date;
  author: string;
  reviewers: string[];
  version: number;
  views: number;
  helpfulness: number;        // Upvote/downvote ratio
  relatedArticles: string[];
  linkedAssessments: string[];
}
```

### Assessment Framework

```typescript
interface Assessment {
  assessmentId: string;
  title: string;
  domain: KnowledgeDomain;
  type: AssessmentType;
  questions: AssessmentQuestion[];
  passingScore: number;
  timeLimit: number;             // Minutes
  attempts: AttemptPolicy;
  validFor: string;              // How long certification lasts
}

type AssessmentType =
  | 'multiple_choice'          // Standard MCQ
  | 'scenario_based'           // "Customer asks X, what do you do?"
  | 'practical'                // Complete a booking in sandbox
  | 'oral'                     // Verbal assessment with trainer
  | 'peer_review';             // Reviewed by senior agent

interface AssessmentQuestion {
  questionId: string;
  text: string;
  type: 'single_choice' | 'multi_choice' | 'true_false' | 'short_answer' | 'ordering';
  options?: string[];
  correctAnswer: string | string[];
  explanation: string;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
}

interface AttemptPolicy {
  maxAttempts: number;
  cooldownBetweenAttempts: string;
  showCorrectAnswers: 'always' | 'after_pass' | 'never';
  randomizeQuestions: boolean;
  randomizeOptions: boolean;
}
```

### In-Context Knowledge Surfacing

```typescript
interface ContextualKnowledge {
  // During a booking, suggest relevant knowledge
  trigger: KnowledgeTrigger;
  suggestions: KnowledgeSuggestion[];
}

type KnowledgeTrigger =
  | { type: 'destination'; destination: string }
  | { type: 'supplier'; supplierId: string }
  | { type: 'booking_type'; bookingType: string }
  | { type: 'customer_question'; keywords: string[] }
  | { type: 'error'; errorCode: string }
  | { type: 'policy'; policyType: string };

interface KnowledgeSuggestion {
  articleId: string;
  title: string;
  relevanceScore: number;
  snippet: string;               // First 2 lines
  whyShown: string;              // "Related to Bangkok destination"
}
```

---

## Open Problems

1. **Knowledge freshness** — Hotel policies, visa rules, and flight schedules change constantly. How to detect and update stale articles?

2. **Subjective knowledge** — "Best time to visit Bali" has different answers for different travelers. How to handle subjective content?

3. **Assessment gaming** — Agents may memorize answers without understanding. Scenario-based assessments are harder to game but more expensive to create.

4. **Knowledge silos** — Experienced agents have undocumented knowledge. How to incentivize knowledge sharing?

5. **Search relevance** — An agent in the middle of a booking needs instant, relevant results. Knowledge base search must be fast and contextually accurate.

---

## Next Steps

- [ ] Design knowledge base architecture and content types
- [ ] Build initial article library for top 5 knowledge domains
- [ ] Research knowledge management platforms (Confluence, GitBook, Notion)
- [ ] Design assessment authoring tool for training managers
- [ ] Prototype in-context knowledge suggestions during booking flow
