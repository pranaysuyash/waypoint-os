# Customer Self-Service — Support & Communication

> Research document for customer-facing support channels, chat, and communication preferences.

---

## Key Questions

1. **What support channels should the portal offer (chat, email, phone, FAQ)?**
2. **How do we enable direct customer-agent communication through the portal?**
3. **What self-service help resources reduce support ticket volume?**
4. **How do we handle urgent issues (during-trip emergencies) vs. routine questions?**
5. **What's the customer feedback and review submission flow?**

---

## Research Areas

### Support Channel Architecture

```typescript
interface CustomerSupportPortal {
  channels: SupportChannel[];
  faq: FAQSection[];
  chatHistory: ChatMessage[];
  tickets: SupportTicket[];
  escalation: EscalationOption[];
}

type SupportChannel =
  | { type: 'chat'; description: string; availability: string }
  | { type: 'email'; description: string; responseTime: string }
  | { type: 'phone'; description: string; availability: string }
  | { type: 'whatsapp'; description: string; responseTime: string }
  | { type: 'video_call'; description: string; byAppointment: boolean };

// Channel routing:
// Pre-departure questions → Chat or email (non-urgent)
// During-trip issues → Phone or WhatsApp (urgent)
// Post-trip feedback → Email or portal form
// Emergency → Phone (24/7) + emergency hotline
```

### Customer-Agent Chat

```typescript
interface CustomerChat {
  chatId: string;
  tripId: string;
  agentId: string;
  messages: ChatMessage[];
  status: 'active' | 'waiting' | 'resolved';
  createdAt: Date;
  topic?: string;
  priority: 'normal' | 'high' | 'urgent';
}

interface ChatMessage {
  messageId: string;
  sender: 'customer' | 'agent' | 'bot';
  content: string;
  type: 'text' | 'image' | 'document' | 'quick_reply' | 'system';
  timestamp: Date;
  read: boolean;
}

// Chat features:
// - Auto-suggested FAQs based on message content
// - Quick-reply buttons for common questions
// - File/image sharing (passports, receipts, photos)
// - Typing indicator and presence
// - Chat transcript email on closure
// - Resolution confirmation (thumbs up/down)
```

### Self-Service FAQ & Knowledge Base

```typescript
interface CustomerFAQ {
  sections: FAQSection[];
  searchEnabled: boolean;
  contextAware: boolean;           // Show relevant FAQs based on trip
}

interface FAQSection {
  title: string;
  articles: FAQArticle[];
}

interface FAQArticle {
  articleId: string;
  question: string;
  answer: string;
  category: string;
  tags: string[];
  helpful: number;                 // Upvotes
  notHelpful: number;
  relatedArticles: string[];
}

// FAQ sections:
// 1. Before you travel (visas, packing, insurance)
// 2. Managing your booking (changes, cancellations, payments)
// 3. During your trip (emergencies, local info, contacts)
// 4. After your trip (feedback, reviews, documents)
// 5. Account & settings (profile, preferences, privacy)
```

### Feedback & Review Submission

```typescript
interface CustomerFeedback {
  tripId: string;
  overallRating: number;           // 1-5
  categoryRatings: CategoryRating[];
  reviewText: string;
  photos: string[];
  wouldRecommend: boolean;
  submittedAt: Date;
  status: 'draft' | 'submitted' | 'published';
}

interface CategoryRating {
  category: 'agent_service' | 'itinerary_quality' | 'value_for_money' | 'accommodation' | 'transport' | 'activities';
  rating: number;
  comment?: string;
}

// Post-trip feedback flow:
// 1. Automated email 2 days after trip completion
// 2. Portal notification with feedback form
// 3. Reminder after 7 days if not completed
// 4. Thank-you message after submission
// 5. Optional: incentive (discount on next booking)
```

---

## Open Problems

1. **Chat availability** — 24/7 chat requires 24/7 agents. For a small agency, this may mean bot-first triage with agent handoff during business hours.

2. **Escalation transparency** — When a customer issue is escalated, what do they see? "We've escalated this" is vague. Need transparent status updates.

3. **Multi-language support** — Customer portal may need to serve customers in Hindi, Tamil, or other regional languages. FAQ and chat translation adds complexity.

4. **Chat vs. ticket boundary** — When does a chat conversation become a support ticket? Need clear transitions for tracking and SLA purposes.

5. **Self-service vs. revenue** — Fully self-service customers don't need agents, but they also don't generate upsell opportunities. Balance self-service with agent touchpoints.

---

## Next Steps

- [ ] Design customer chat interface for portal
- [ ] Build FAQ structure with context-aware suggestions
- [ ] Design feedback and review submission flow
- [ ] Study customer portal support patterns (Airbnb, Booking.com)
- [ ] Design chatbot triage for 24/7 first-response
