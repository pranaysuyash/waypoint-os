# Onboarding & First-Run Experience — Help System & Guides

> Research document for in-app help, contextual guidance, tooltips, and self-service support.

---

## Key Questions

1. **How do we provide help without cluttering the interface?**
2. **What's the contextual help model — when does help appear?**
3. **How do we build a searchable knowledge base within the app?**
4. **What's the tooltip and guidance system architecture?**
5. **How do we measure help content effectiveness?**

---

## Research Areas

### Help System Architecture

```typescript
interface HelpSystem {
  contextualHelp: ContextualHelpEntry[];
  tooltipSystem: TooltipConfig[];
  knowledgeBase: KnowledgeBaseConfig;
  search: HelpSearchConfig;
  feedback: HelpFeedbackConfig;
}

interface ContextualHelpEntry {
  helpId: string;
  context: HelpContext;
  content: HelpContent;
  trigger: HelpTrigger;
  audience: string[];
}

type HelpContext =
  | { type: 'page'; page: string }
  | { type: 'component'; component: string }
  | { type: 'field'; field: string }
  | { type: 'action'; action: string }
  | { type: 'error'; errorCode: string }
  | { type: 'workflow'; workflowName: string; step: number };

type HelpTrigger =
  | 'always_visible'                 // "?" icon always shown
  | 'on_hover'                       // Show on hover over "?"
  | 'on_first_visit'                 // Show first time user visits page
  | 'on_error'                       // Show when error occurs
  | 'on_idle'                        // Show after 10s of inactivity
  | 'on_demand';                     // User clicks help button

interface HelpContent {
  title: string;
  summary: string;                   // 1-2 sentences
  detail?: string;                   // Full explanation (markdown)
  videoUrl?: string;
  relatedArticles: string[];
  relatedActions: string[];
}

// Contextual help examples:
// Intake panel (first visit):
//   "This is where extracted customer data appears. Review and correct
//    any highlighted fields, then proceed to the Trip Builder."
//   [Watch 2-min video] [Read full guide]
//
// Pricing section (on hover):
//   "Adjust margins and markups here. The platform automatically
//    calculates the final price based on supplier rates + your margin."
//
// Error: Spine run timeout:
//   "The AI processing took too long. Try again or edit the input
//    data manually. If this persists, contact support."
//   [Retry] [Edit Manually] [Contact Support]
```

### Tooltip System

```typescript
interface TooltipConfig {
  targetElement: string;
  content: string;
  placement: 'top' | 'bottom' | 'left' | 'right';
  trigger: 'hover' | 'click' | 'focus';
  showOnce: boolean;                 // Only show on first encounter
  delay: number;                     // Ms before showing
  maxWidth: number;
  dismissible: boolean;
  priority: number;                  // Higher priority tooltips shown first
}

// Tooltip types:
// 1. Field labels: Hover over a field to see what it means
//    "Customer Segment: Categorize as Budget, Mid-range, Premium, or Luxury"
//
// 2. Status indicators: Explain what a status means
//    "Extraction Confirmed: AI extracted data with >95% confidence"
//
// 3. Action hints: Guide next action
//    "Click here to send the quote to the customer via WhatsApp"
//
// 4. Warning tooltips: Explain potential issues
//    "This price is below cost. Margin will be negative."
//
// 5. Feature discovery: Highlight new features
//    "NEW: You can now compare prices across suppliers here"

// Tooltip priority (shown first when multiple are queued):
// 1. Error/warning tooltips (immediate)
// 2. Required action tooltips (high)
// 3. Feature discovery tooltips (medium)
// 4. Educational tooltips (low)
// 5. Enhancement tips (very low)
```

### In-App Knowledge Base

```typescript
interface InAppKnowledgeBase {
  articles: HelpArticle[];
  categories: HelpCategory[];
  searchIndex: SearchIndex;
  recentArticles: string[];
  bookmarkedArticles: string[];
}

interface HelpArticle {
  articleId: string;
  title: string;
  category: string;
  tags: string[];
  content: string;                   // Markdown
  estimatedReadTime: number;         // Minutes
  relatedArticles: string[];
  lastUpdated: Date;
  views: number;
  helpfulVotes: number;
  notHelpfulVotes: number;
}

// Knowledge base structure:
// Getting Started
//   - Creating your first trip
//   - Understanding the workbench layout
//   - Setting up your profile
//
// Trip Management
//   - Intake and extraction
//   - Building an itinerary
//   - Pricing and margins
//   - Generating quotes and documents
//
// Bookings & Payments
//   - Booking workflow
//   - Payment processing
//   - Invoicing and receipts
//   - Cancellations and refunds
//
// Communication
//   - WhatsApp integration
//   - Email templates
//   - Customer meeting scheduling
//
// Advanced Features
//   - Spine pipeline configuration
//   - Workflow automation
//   - Custom reports
//   - API access
//
// Administration
//   - Agency settings
//   - Team management
//   - Integration setup
//   - Billing and subscription

// Search capabilities:
// 1. Full-text search across all articles
// 2. Autocomplete suggestions
// 3. Context-aware: Show articles relevant to current page
// 4. Error-aware: When error occurs, show relevant troubleshooting
// 5. Keyboard shortcut: "/" to focus search
```

### Help Feedback Loop

```typescript
interface HelpFeedback {
  feedbackType: 'article_helpful' | 'article_not_helpful' | 'missing_content' | 'bug_report';
  context: string;
  articleId?: string;
  comment?: string;
  submittedAt: Date;
  submittedBy: string;
}

// Help content analytics:
// - Most viewed articles (what agents need most help with)
// - "Not helpful" articles (content that needs improvement)
// - Search queries with no results (missing content)
// - Time spent on help articles (engagement)
// - Help-to-resolution rate (did the help article solve the problem?)

// Content improvement cycle:
// 1. Track "not helpful" feedback
// 2. Review top "not helpful" articles monthly
// 3. Rewrite or expand flagged articles
// 4. Track improvement in helpfulness score
// 5. Add new articles based on search queries with no results
```

---

## Open Problems

1. **Help content maintenance** — Documentation rots quickly. UI changes make screenshots outdated. Need low-maintenance help content strategy.

2. **Context relevance** — Help shown out of context is noise. Need precise context matching so help is always relevant.

3. **Multilingual help** — Hindi-speaking agents may prefer help content in Hindi. Translating all help content is expensive.

4. **Video vs. text** — Some agents prefer video tutorials, others prefer text. Need both formats for key articles.

5. **Help during outages** — If the help system is part of the platform, it's unavailable during outages. Need offline help or external knowledge base.

---

## Next Steps

- [ ] Design contextual help system with trigger rules
- [ ] Build tooltip framework with priority and show-once logic
- [ ] Create in-app knowledge base with search
- [ ] Design help feedback and content improvement loop
- [ ] Study help UX (Intercom, Zendesk Guide, GitBook)
