# Notification & Messaging — Template Management

> Research document for notification templates, personalization, and content management.

---

## Key Questions

1. **How do we manage templates across channels with different format constraints?**
2. **What personalization variables are available, and how do we handle missing data?**
3. **Who creates and maintains templates — developers, marketers, or agents?**
4. **How do we version templates and track their effectiveness?**
5. **What's the review and approval workflow for customer-facing templates?**

---

## Research Areas

### Template System

```typescript
interface NotificationTemplate {
  templateId: string;
  name: string;
  category: TemplateCategory;
  channelVersions: ChannelTemplate[];
  variables: TemplateVariable[];
  status: TemplateStatus;
  version: number;
  createdAt: Date;
  updatedAt: Date;
  updatedBy: string;
}

type TemplateCategory =
  | 'booking_confirmation'
  | 'booking_modification'
  | 'booking_cancellation'
  | 'payment_receipt'
  | 'payment_reminder'
  | 'itinerary_ready'
  | 'quote_ready'
  | 'travel_reminder'
  | 'check_in_reminder'
  | 'travel_alert'
  | 'feedback_request'
  | 'welcome'
  | 'marketing'
  | 'internal_note';

interface ChannelTemplate {
  channel: NotificationChannel;
  subject?: string;            // For email
  preheader?: string;          // For email
  body: string;                // Template with variable placeholders
  fallbackBody?: string;       // Simplified version for restricted channels
  buttons?: TemplateButton[];
  attachments?: string[];
}

interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'date' | 'currency' | 'object';
  source: 'trip' | 'customer' | 'agent' | 'booking' | 'system';
  required: boolean;
  defaultValue?: string;
  format?: string;             // Date format, currency format
}
```

### Template Editor UX

**Questions:**
- Visual drag-and-drop editor vs. code-based templates?
- Live preview across channels?
- How to handle channel-specific constraints (WhatsApp 1024 char limit, SMS 160 char)?

```typescript
interface TemplateEditor {
  // Edit modes
  modes: ('visual' | 'code')[];
  // Preview
  previewChannels: NotificationChannel[];
  // Validation
  validators: TemplateValidator[];
  // Variable autocomplete
  variableSuggestion: boolean;
}

interface TemplateValidator {
  channel: NotificationChannel;
  rules: ValidationRule[];
}

interface ValidationRule {
  type: 'max_length' | 'required_variable' | 'image_size' | 'link_format';
  config: Record<string, unknown>;
  errorMessage: string;
}
```

### Template Effectiveness Tracking

```typescript
interface TemplateMetrics {
  templateId: string;
  channel: NotificationChannel;
  sent: number;
  delivered: number;
  opened: number;               // Email, in-app
  clicked: number;
  responded: number;
  unsubscribed: number;
  deliveryRate: number;
  openRate: number;
  clickRate: number;
  responseRate: number;
}
```

---

## Open Problems

1. **Multi-channel template synchronization** — The same message needs to be formatted for email (HTML), WhatsApp (text + buttons), SMS (truncated), and push (title + body). Maintaining consistency across channels is challenging.

2. **Conditional content** — Templates may need conditional sections (e.g., "if flight is included, show flight details; otherwise skip"). How to express conditions in templates?

3. **Template testing** — How to test templates with real data without sending to actual customers. Need a sandbox/preview mode.

4. **Localization of templates** — Same template in English, Hindi, and regional languages. How to manage translations without duplicating templates?

5. **Agent-customized templates** — Agents may want to customize templates for their personal style. How to balance consistency with personalization?

---

## Next Steps

- [ ] Design template schema with multi-channel support
- [ ] Research template editors (MJML for email, WhatsApp template format)
- [ ] Create initial template library for top 20 notification types
- [ ] Design template preview and testing workflow
- [ ] Study template effectiveness tracking patterns
