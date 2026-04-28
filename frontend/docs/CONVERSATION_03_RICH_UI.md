# Conversation UX — Rich Message Interface & Interactions

> Research document for the message composition, display, and interaction experience.

---

## Current State

The workbench uses plain `<textarea>` elements for customer message and agent notes. No rich text, no formatting, no attachments, no message bubbles, no keyboard shortcuts, and no inline interactions.

---

## Key Questions

1. **Should the message input support rich text, markdown, or both?**
2. **What keyboard shortcuts and productivity features do power-user agents need?**
3. **How do we display structured outputs (itineraries, quotes) inline in the conversation?**
4. **What attachment types should be supported, and how are they rendered?**
5. **How do we handle long messages and collapsible content?**
6. **What's the right message threading model — flat, nested, or linked?**

---

## Research Areas

### Message Composition

```typescript
interface MessageComposer {
  // Input mode
  mode: 'plaintext' | 'markdown' | 'rich_text';
  // Auto-complete / suggestions
  suggestions: SuggestionProvider[];
  // Templates
  templates: MessageTemplate[];
  // Attachments
  attachments: AttachmentSupport;
  // Keyboard shortcuts
  shortcuts: KeyboardShortcut[];
}

interface MessageTemplate {
  templateId: string;
  name: string;
  category: 'greeting' | 'clarification' | 'itinerary' | 'quote' | 'follow_up' | 'closing';
  content: string;
  variables: TemplateVariable[];
  lastUsed?: Date;
  usageCount: number;
}

interface KeyboardShortcut {
  key: string;               // e.g., 'cmd+enter'
  action: string;
  description: string;
  context: 'global' | 'composer' | 'message_list';
}

// Suggested shortcuts:
// Cmd+Enter — Send message
// Cmd+S — Save draft
// Cmd+Shift+M — New message
// Cmd+/ — Show template picker
// Cmd+Shift+F — Search conversations
// Cmd+K — Command palette
// Esc — Cancel / close
```

### Message Display & Rendering

```typescript
interface MessageRenderer {
  // How to render different content types
  renderers: {
    text: TextRenderer;
    markdown: MarkdownRenderer;
    structured: StructuredRenderer;
    itinerary: ItineraryRenderer;
    quote: QuoteRenderer;
    attachment: AttachmentRenderer;
    system: SystemMessageRenderer;
  };
  // Layout options
  layout: 'bubbles' | 'flat' | 'timeline';
  // Grouping
  grouping: 'none' | 'by_date' | 'by_session' | 'by_actor';
  // Collapsibility
  collapsible: CollapsibleConfig;
}

interface CollapsibleConfig {
  maxLength: number;          // Characters before collapse
  defaultExpanded: boolean;
  showPreview: boolean;       // Show first N lines when collapsed
  types: MessageType[];       // Which message types can be collapsed
}

// Inline structured content renderers:
// - Itinerary summary → expandable day cards
// - Quote → price breakdown table
// - Hotel options → card grid with images
// - Flight options → timeline comparison
// - Spine run status → progress indicator with expandable log
```

### Inline Interactions

**Beyond read-only display, messages should be interactive:**

```typescript
type InlineAction =
  | { type: 'copy'; target: string }
  | { type: 'edit'; messageId: string }
  | { type: 'reply'; messageId: string; quotedContent: string }
  | { type: 'react'; messageId: string; emoji: string }
  | { type: 'pin'; messageId: string }
  | { type: 'bookmark'; messageId: string }
  | { type: 'rerun'; spineRunId: string }
  | { type: 'modify_booking'; bookingId: string }
  | { type: 'view_details'; targetId: string; targetType: string }
  | { type: 'download'; documentId: string }
  | { type: 'share'; messageId: string; channel: string };
```

### Attachment Handling

```typescript
interface AttachmentSupport {
  acceptedTypes: MimeType[];
  maxFileSize: number;         // Per file
  maxTotalSize: number;        // Per message
  maxFiles: number;            // Per message
  rendering: AttachmentRendering;
  virusScan: boolean;
  ocrEnabled: boolean;         // Extract text from images/PDFs
}

type MimeType =
  | 'image/*'            // Screenshots, photos
  | 'application/pdf'   // Itineraries, tickets, passports
  | 'text/*'             // Text files
  | 'application/vnd.*'  // Office documents
  | 'audio/*'            // Voice messages
  | 'video/*';           // Video clips

interface AttachmentRendering {
  image: 'inline_thumbnail' | 'gallery' | 'link';
  pdf: 'inline_preview' | 'link';
  document: 'link';
  audio: 'inline_player' | 'link';
  video: 'inline_player' | 'thumbnail';
}
```

**Questions:**
- Should we OCR customer-submitted documents (passport copies, visa PDFs) to extract structured data?
- How to handle large attachments (video files from customers)?
- What's the storage cost model for attachments?

---

## Open Problems

1. **Rich text vs. markdown** — Agents may prefer markdown for speed, but rich text is more WYSIWYG. Supporting both adds complexity. Which to prioritize?

2. **Structured output rendering** — Spine runs produce structured itineraries, quotes, and analysis. Rendering these inline in the conversation stream requires dedicated renderers per output type.

3. **Mobile-responsive messages** — Message bubbles, inline cards, and attachments need to work on mobile. Complex structured content (itinerary cards, comparison tables) is particularly challenging on small screens.

4. **Template management UX** — Agents need to create and manage templates without developer involvement. Template editor UX is its own mini-feature.

5. **Paste handling** — Customers paste WhatsApp messages, email threads, or screenshots. Need smart paste parsing to extract structured trip information.

---

## Next Steps

- [ ] Evaluate rich text editors for React (TipTap, Slate, Lexical, ProseMirror)
- [ ] Research message display patterns in Linear, Slack, Discord
- [ ] Design inline structured content renderers for itinerary, quote, options
- [ ] Study attachment handling in travel platforms (Booking.com message attachments)
- [ ] Prototype message composer with template insertion
- [ ] Design keyboard shortcut schema for power-user agents
