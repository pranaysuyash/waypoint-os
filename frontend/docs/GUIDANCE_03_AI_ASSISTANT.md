# User Guidance & Helper System — AI-Powered In-App Assistant

> Research document for an AI-powered help assistant that answers questions, suggests actions, explains features, and provides contextual guidance within the application.

---

## Key Questions

1. **How does an AI assistant provide real-time, contextual help within the app?**
2. **What conversational interface supports natural language questions about the platform?**
3. **How does the assistant proactively suggest actions based on context?**
4. **What guardrails prevent the AI from giving incorrect guidance?**
5. **How does the assistant learn from usage patterns to improve?**

---

## Research Areas

### AI Assistant Architecture

```typescript
interface AIHelpAssistant {
  interface: AssistantInterface;
  context: AssistantContext;
  knowledge: KnowledgeBase;
  actions: AssistantActions;
  guardrails: AssistantGuardrails;
}

interface AssistantInterface {
  trigger: AssistantTrigger;
  chat: AssistantChat;
  suggestions: ProactiveSuggestion[];
  voiceInput: VoiceInput;
}

// Assistant trigger methods:
// 1. Floating button: Bottom-right "Ask AI" button (always visible)
// 2. Keyboard shortcut: ctrl+/ or cmd+/
// 3. Help panel: "Ask a Question" input in help panel
// 4. Empty state: "Ask AI for help" on empty states
// 5. Error state: "Ask AI what went wrong" on error messages
// 6. Context menu: Right-click → "Ask AI about this"
//
// Assistant chat interface:
// ┌─────────────────────────────────────────┐
// │  🤖 Waypoint Assistant                   │
// │                                            │
// │  Hi! I can help you with:                 │
// │  • How to use any feature                 │
// │  • Explaining what something does          │
// │  • Finding specific trips or customers     │
// │  • Suggesting next actions for a trip      │
// │                                            │
// │  💡 Based on your current trip:            │
// │  "This Kerala trip is pending. You could   │
// │   confirm it or generate a quote first."   │
// │                                            │
// │  ──────────────────────────────────────── │
// │                                            │
// │  You: How do I generate an itinerary?      │
// │                                            │
// │  🤖 To generate an itinerary:              │
// │  1. Make sure the trip has activities      │
// │  2. Click the Output panel (or press 4)    │
// │  3. Select "Generate Itinerary"            │
// │  4. Choose template and format             │
// │                                            │
// │  [Do it for me] [Show me where]           │
// │                                            │
// │  ──────────────────────────────────────── │
// │  [📎] [Type your question... ]    [Send]  │
// └─────────────────────────────────────────────┘

interface AssistantContext {
  // Rich context fed to the AI:
  currentPage: string;
  currentTrip?: TripSummary;
  currentCustomer?: CustomerSummary;
  activePanel?: string;
  recentActions: string[];             // Last 10 actions
  openModals: string[];
  selectedItems: string[];
  userExperience: ExperienceLevel;
  helpHistory: string[];               // Recent help topics viewed
  errors: ErrorContext[];              // Current error states
}

interface TripSummary {
  id: string;
  destination: string;
  status: string;
  customerName: string;
  daysUntilTravel: number;
  pendingActions: string[];            // ["confirm", "send_itinerary", "collect_payment"]
  alerts: string[];                    // ["visa_deadline_approaching", "hotel_unconfirmed"]
}

// AI assistant capabilities:
//
// QUESTION ANSWERING:
// "What does the decision panel show?"
// → "The Decision Panel shows risk assessment, supplier ratings,
//    and suitability signals for this trip. It helps you evaluate
//    if this booking is appropriate. [Show Decision Panel]"
//
// FEATURE GUIDANCE:
// "How do I create a saved view?"
// → Step-by-step instructions + [Show me] button that highlights UI
//
// TRIP-SPECIFIC ADVICE:
// "What should I do next with this trip?"
// → "This Kerala trip has been pending for 3 days. The customer's
//    last message was 'Can you send the quote?' 2 hours ago.
//    Suggested next steps:
//    1. Generate a quote (you have the pricing ready)
//    2. Send it via WhatsApp
//    [Generate Quote] [Send Message]"
//
// ERROR EXPLANATION:
// "Why can't I confirm this trip?"
// → "This trip is missing required fields:
//    • Customer phone number (required for WhatsApp notifications)
//    • Hotel confirmation number
//    Complete these fields first. [Go to Missing Fields]"
//
// NAVIGATION HELP:
// "Where do I find customer history?"
// → "Customer history is in the CRM section.
//    For this specific customer, click their name in the
//    trip header → 'View Full Profile'. [Take Me There]"
//
// COMPARISON HELP:
// "What's the difference between draft and pending?"
// → "Draft: You're still building the trip, customer hasn't
//    seen it yet. Pending: You've sent a quote, waiting for
//    customer response. [Read Full Article]"
```

### Proactive Suggestions

```typescript
interface ProactiveSuggestion {
  id: string;
  trigger: SuggestionTrigger;
  message: string;
  actions: SuggestionAction[];
  priority: 'low' | 'medium' | 'high';
  dismissible: boolean;
}

type SuggestionTrigger =
  | 'idle_on_page'                     // User hasn't acted in X seconds
  | 'incomplete_trip'                  // Trip missing required fields
  | 'unread_message'                   // Customer message not replied to
  | 'approaching_deadline'             // Trip date or payment deadline near
  | 'suboptimal_workflow'              // Detected inefficient approach
  | 'new_feature_available'            // Feature user hasn't tried
  | 'repeated_action'                  // Same action done N times (suggest automation)
  | 'error_recovery';                  // After an error occurred

// Proactive suggestion examples:
//
// IDLE ON TRIP (no action for 3 minutes):
// ┌─────────────────────────────────────────┐
// │  💡 Need help with this trip?            │
// │                                            │
// │  I noticed you've been on this Kerala     │
// │  trip for a while. Here are some          │
// │  things you could do:                     │
// │                                            │
// │  • Generate itinerary (pricing is ready)  │
// │  • Send quote to customer                 │
// │  • Check hotel availability               │
// │                                            │
// │  [Generate Itinerary] [Dismiss]           │
// └─────────────────────────────────────────────┘
//
// INCOMPLETE TRIP:
// ┌─────────────────────────────────────────┐
// │  ⚠️ This trip is missing 3 items          │
// │                                            │
// │  Before confirming, add:                  │
// │  ☐ Customer phone number                  │
// │  ☐ Flight details                         │
// │  ☐ Hotel confirmation                     │
// │                                            │
// │  [Fill Missing Fields] [Dismiss]          │
// └─────────────────────────────────────────────┘
//
// REPEATED ACTION (manually typed 5 similar messages):
// ┌─────────────────────────────────────────┐
// │  💡 Save time with message templates      │
// │                                            │
// │  I noticed you've been typing similar     │
// │  messages. Want me to create a template   │
// │  from your recent messages?               │
// │                                            │
// │  [Create Template] [No Thanks]            │
// └─────────────────────────────────────────────┘
//
// APPROACHING DEADLINE (payment due in 2 days):
// ┌─────────────────────────────────────────┐
// │  ⏰ Payment reminder needed               │
// │                                            │
// │  Balance of ₹35,000 is due in 2 days     │
// │  for Rajesh's Kerala trip.                │
// │                                            │
// │  [Send Payment Reminder] [View Trip]      │
// └─────────────────────────────────────────────┘
//
// Proactive suggestion rules:
// - Max 1 proactive suggestion at a time
// - Never interrupt during typing or active interaction
// - Dismissed suggestions don't repeat for 24 hours
// - Priority: high (deadlines) > medium (workflow) > low (tips)
// - Track which suggestions are acted on vs dismissed

interface SuggestionAction {
  label: string;
  type: 'navigate' | 'execute' | 'tour' | 'article' | 'dismiss';
  target?: string;
}
```

### Knowledge Base Integration

```typescript
interface AssistantKnowledgeBase {
  sources: KnowledgeSource[];
  indexing: KnowledgeIndex;
  retrieval: RetrievalSystem;
  freshness: KnowledgeFreshness;
}

interface KnowledgeSource {
  type: 'help_articles' | 'api_docs' | 'product_docs' | 'changelog'
      | 'faq' | 'training_materials' | 'regional_guides'
      | 'gst_rules' | 'compliance_docs';
  updateFrequency: 'real_time' | 'daily' | 'weekly';
  priority: number;
}

// Knowledge sources for the AI assistant:
//
// 1. HELP ARTICLES (highest priority):
//    Platform feature documentation, updated with each release
//    Source: CMS content authored by product team
//
// 2. API DOCS:
//    Technical documentation for developer-oriented questions
//    Source: OpenAPI spec + markdown docs
//
// 3. PRODUCT CHANGELOG:
//    Recent feature changes and new capabilities
//    Source: Changelog entries in the system
//
// 4. FAQ:
//    Frequently asked questions from all agents
//    Source: Curated from support ticket patterns
//
// 5. TRAINING MATERIALS:
//    Training module content and certification materials
//    Source: LMS content
//
// 6. REGIONAL GUIDES:
//    Destination-specific information for trip planning
//    Source: Destination content management system
//
// 7. GST RULES:
//    Tax rules for travel services (5% vs 18%, TCS, etc.)
//    Source: Updated from government notifications
//
// 8. COMPLIANCE DOCS:
//    DPDP Act, IATA rules, RBI guidelines
//    Source: Legal team maintained documents

// Retrieval and answer generation:
// 1. User asks question
// 2. Classify intent (feature help, navigation, action, explanation)
// 3. Retrieve relevant knowledge sources
// 4. Consider current context (page, trip, experience level)
// 5. Generate response with:
//    a. Direct answer to question
//    b. Step-by-step instructions if applicable
//    c. Action buttons (do it, show me, learn more)
// 6. Include confidence level:
//    - High: Answer from verified documentation
//    - Medium: Answer from patterns/similar questions
//    - Low: Not sure, suggest contacting support

// Answer quality guardrails:
// ┌─────────────────────────────────────────┐
// │  🤖 I'm not 100% sure about this,        │
// │  but based on similar situations...      │
// │                                            │
// │  [answer content]                          │
// │                                            │
// │  ⚠️ This may not apply to your specific   │
// │  situation. [Contact Support] for help.   │
// └─────────────────────────────────────────────┘
//
// When AI cannot answer:
// ┌─────────────────────────────────────────┐
// │  🤖 I don't have enough information to    │
// │  answer that confidently.                 │
// │                                            │
// │  Here's what I can help with instead:     │
// │  • [Search help articles]                 │
// │  • [Start a guided tour]                  │
// │  • [Chat with support team]              │
// │                                            │
// │  Your question has been logged to help    │
// │  us improve.                              │
// └─────────────────────────────────────────────┘
```

### Assistant Analytics & Learning

```typescript
interface AssistantAnalytics {
  usage: AssistantUsageMetrics;
  quality: AnswerQualityMetrics;
  learning: ContinuousLearning;
}

interface AssistantUsageMetrics {
  totalQueries: number;
  queriesByDay: Record<string, number>;
  avgQueriesPerSession: number;
  avgResponseTime: number;             // Seconds
  topQuestions: RankedQuestion[];
  queriesByCategory: Record<string, number>;
  usersByExperienceLevel: Record<string, number>;
}

interface AnswerQualityMetrics {
  helpfulRate: number;                 // % marked as helpful
  actionRate: number;                  // % where user followed suggested action
  escalationRate: number;              // % that led to support contact
  clarificationRate: number;           // % where user asked follow-up
  unresolvedRate: number;              // % where AI couldn't answer
}

// Quality tracking:
// After each AI response, show:
// "Was this helpful? [👍] [👎]"
// If thumbs down: "What would have been more helpful? [text input]"
//
// Weekly quality report:
// - Top 10 most asked questions
// - Questions with lowest helpful rate (need better answers)
// - New questions not in knowledge base (content gaps)
// - Response time by question type
// - Escalation reasons breakdown

interface ContinuousLearning {
  // The assistant improves over time:
  //
  // 1. QUESTION CLUSTERING:
  //    Group similar questions to identify patterns
  //    "How to send invoice" and "Where is invoice button"
  //    → Both need invoice generation documentation
  //
  // 2. ANSWER IMPROVEMENT:
  //    For low-rated answers:
  //    - Flag for content team review
  //    - Auto-suggest improved answer from successful similar answers
  //    - A/B test new answer versions
  //
  // 3. KNOWLEDGE GAP DETECTION:
  //    Questions the AI can't answer → New help article needed
  //    Track: question, frequency, user impact
  //    Auto-generate article drafts for content team
  //
  // 4. PERSONALIZATION:
  //    Learn per-user patterns:
  //    - This agent always asks about GST → Proactively show GST info
  //    - This agent never uses keyboard shortcuts → Suggest more
  //    - This agent specializes in Kerala → Tailor destination help
  //
  // 5. WORKFLOW DISCOVERY:
  //    Detect common workflows from questions:
  //    "Users often ask about confirming → generating → sending"
  //    → Create a workflow tour for this sequence
}
```

---

## Open Problems

1. **AI hallucination risk** — The assistant must never give incorrect guidance about features, pricing rules, or compliance. A confident wrong answer about GST rates or cancellation policies could cause real financial harm. Strict grounding in verified documentation is essential.

2. **Context window limits** — The assistant needs rich context (current trip, customer, page state, recent actions) but LLM context windows are finite. Prioritizing which context to include and which to summarize is a design challenge.

3. **Proactive suggestion annoyance** — Too many proactive suggestions feel like Clippy ("It looks like you're writing a letter!"). The balance between helpful and intrusive depends heavily on timing, frequency, and relevance — all hard to get right.

4. **Multi-language support** — The assistant needs to handle questions in English, Hindi, and Hinglish (Romanized Hindi). Understanding "kaise kare trip confirm" requires multilingual intent classification.

5. **Privacy in context** — The assistant has access to trip details, customer information, and agent behavior. Clear boundaries on what the AI can reference (and what it shouldn't repeat) are needed, especially in shared workspaces.

---

## Next Steps

- [ ] Design AI assistant interface with floating chat, contextual awareness, and action buttons
- [ ] Build knowledge retrieval system grounded in verified platform documentation
- [ ] Implement proactive suggestion engine with frequency controls and priority ranking
- [ ] Create answer quality tracking and continuous learning pipeline
- [ ] Study AI assistants (GitHub Copilot Chat, Notion AI, Intercom Fin, Ada, Zendesk AI)
