# Communication Hub — UX/UI Deep Dive

> Part 2 of 4 in Communication Hub Exploration Series

---

## Document Overview

**Series:** Communication Hub
**Part:** 2 — UX/UI Design
**Status:** Complete
**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Design Philosophy](#design-philosophy)
2. [Information Architecture](#information-architecture)
3. [Component Library](#component-library)
4. [Key Screens](#key-screens)
5. [Interaction Patterns](#interaction-patterns)
6. [Responsive Design](#responsive-design)
7. [Accessibility](#accessibility)
8. [Animation & Micro-interactions](#animation--micro-interactions)

---

## Design Philosophy

### Core Principles

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMMUNICATION HUB DESIGN                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CONVERSATION FIRST                                                      │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Threaded view that feels like familiar chat apps                │    │
│     │ Context from trip/customer always visible                       │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  2. CHANNEL TRANSPARENCY                                                   │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Always know which channel you're using                          │    │
│     │ Visual distinction between WhatsApp, Email, SMS, In-App         │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  3. EFFICIENT COMPOSITION                                                  │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Quick message sending with smart defaults                       │    │
│     │ Template insertion without breaking flow                        │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  4. STATUS VISIBILITY                                                      │
│     ┌─────────────────────────────────────────────────────────────────┐    │
│     │ Real-time delivery status always visible                        │    │
│     │ Clear indication of read/unread states                          │    │
│     └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Visual Language

| Element | Specification | Rationale |
|---------|---------------|-----------|
| **Primary Color** | `#00A884` (WhatsApp Green) | Familiar messaging color |
| **Secondary Color** | `#6366F1` (Indigo) | Brand distinction |
| **Background** | `#F9FAFB` (Light Gray) | Reduced eye strain |
| **Surface** | `#FFFFFF` (White) | Clean, readable |
| **Border** | `#E5E7EB` (Gray 200) | Subtle separation |
| **Text Primary** | `#111827` (Gray 900) | High contrast |
| **Text Secondary** | `#6B7280` (Gray 500) | Hierarchy |
| **Success** | `#10B981` (Green 500) | Delivery confirmation |
| **Warning** | `#F59E0B` (Amber 500) | Pending status |
| **Error** | `#EF4444` (Red 500) | Failed delivery |

---

## Information Architecture

### Site Map

```
Communication Hub
├── /messages
│   ├── /inbox (default)
│   ├── /sent
│   ├── /scheduled
│   └── /templates
│
├── /messages/:threadId
│   ├── Thread view
│   └── Message composer
│
├── /messages/new
│   └── New message composer
│
└── /messages/analytics
    ├── Overview dashboard
    ├── Delivery metrics
    └── Channel performance
```

### Navigation Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Logo   │  │   Messages   │  │   Templates  │  │  Search [        ]  │ │
│  └─────────┘  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────────────┐
│                              │                                              │
│  ┌───────────────────────────▼────────────────────────────────────────┐    │
│  │                          Secondary Nav                             │    │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐   │    │
│  │  │ Inbox  │ │  Sent  │ │Scheduled │ │ Templates  │ │ Analytics  │   │    │
│  │  └────────┘ └────────┘ └──────────┘ └────────────┘ └────────────┘   │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Library

### MessageThreadList Component

```typescript
// components/messages/MessageThreadList.tsx

interface MessageThreadListProps {
  threads: MessageThread[];
  selectedThreadId?: string;
  onThreadSelect: (threadId: string) => void;
  filters: ThreadListFilters;
  onFiltersChange: (filters: ThreadListFilters) => void;
  loading?: boolean;
}

/**
 * Thread list with filtering and real-time updates
 *
 * Features:
 * - Virtual scrolling for large lists
 * - Real-time status updates via WebSocket
 * - Filter by channel, status, date range
 * - Mark as read/unread
 * - Bulk actions (archive, delete)
 */
export const MessageThreadList: React.FC<MessageThreadListProps> = ({
  threads,
  selectedThreadId,
  onThreadSelect,
  filters,
  onFiltersChange,
  loading
}) => {
  const [virtualItems, setVirtualItems] = useState<VirtualItem[]>([]);

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Header with filters */}
      <ThreadListHeader
        filters={filters}
        onFiltersChange={onFiltersChange}
        threadCount={threads.length}
      />

      {/* Thread items */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <ThreadListSkeleton />
        ) : (
          <VirtualList
            items={threads}
            renderItem={(thread) => (
              <ThreadListItem
                key={thread.id}
                thread={thread}
                selected={thread.id === selectedThreadId}
                onClick={() => onThreadSelect(thread.id)}
              />
            )}
          />
        )}
      </div>

      {/* Bulk actions bar */}
      <BulkActionsBar />
    </div>
  );
};

/**
 * Individual thread item with status indicators
 */
const ThreadListItem: React.FC<{
  thread: MessageThread;
  selected: boolean;
  onClick: () => void;
}> = ({ thread, selected, onClick }) => {
  const lastMessage = thread.lastMessage;
  const unreadCount = thread.unreadCount || 0;

  return (
    <div
      className={cn(
        "flex items-center gap-3 p-4 cursor-pointer transition-colors",
        selected ? "bg-indigo-50 border-l-4 border-indigo-600" : "hover:bg-gray-50",
        unreadCount > 0 && "font-semibold"
      )}
      onClick={onClick}
    >
      {/* Channel indicator */}
      <ChannelIcon channel={thread.channel} size="md" />

      {/* Avatar */}
      <Avatar
        src={thread.participantAvatar}
        name={thread.participantName}
        size="md"
      />

      {/* Thread info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <h3 className="text-sm truncate">{thread.participantName}</h3>
          <span className="text-xs text-gray-500">
            {formatRelativeTime(thread.lastMessageAt)}
          </span>
        </div>

        <p className="text-sm text-gray-600 truncate">
          {lastMessage?.content}
        </p>

        {/* Trip badge */}
        {thread.tripId && (
          <TripBadge tripId={thread.tripId} size="sm" />
        )}
      </div>

      {/* Status indicators */}
      <div className="flex items-center gap-2">
        {unreadCount > 0 && (
          <Badge count={unreadCount} color="indigo" />
        )}

        <DeliveryStatusIcon
          status={lastMessage?.status}
          channel={thread.channel}
        />
      </div>
    </div>
  );
};
```

### MessageComposer Component

```typescript
// components/messages/MessageComposer.tsx

interface MessageComposerProps {
  recipientId?: string;
  recipientType?: RecipientType;
  channelId?: string;
  threadId?: string;
  tripId?: string;
  onSend: (message: SendMessageRequest) => Promise<void>;
  disabled?: boolean;
}

/**
 * Rich message composer with template support
 *
 * Features:
 * - Multi-channel support with auto-detection
 * - Template insertion and variable filling
 * - File attachments
 * - Emoji picker
 * - Save as draft
 * - Schedule message
 */
export const MessageComposer: React.FC<MessageComposerProps> = ({
  recipientId,
  recipientType = RecipientType.CUSTOMER,
  channelId,
  threadId,
  tripId,
  onSend,
  disabled = false
}) => {
  const [content, setContent] = useState('');
  const [subject, setSubject] = useState('');
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [showTemplatePicker, setShowTemplatePicker] = useState(false);
  const [showSchedulePicker, setShowSchedulePicker] = useState(false);
  const [scheduledFor, setScheduledFor] = useState<Date | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [draftKey, setDraftKey] = useState(() => generateDraftKey());

  // Auto-save draft
  useEffect(() => {
    const timer = setTimeout(() => {
      saveDraft(draftKey, { content, subject, channelId: selectedChannel });
    }, 1000);

    return () => clearTimeout(timer);
  }, [content, subject, selectedChannel, draftKey]);

  // Load draft on mount
  useEffect(() => {
    const draft = loadDraft(draftKey);
    if (draft) {
      setContent(draft.content || '');
      setSubject(draft.subject || '');
      setSelectedChannel(draft.channelId || null);
    }
  }, [draftKey]);

  const handleSend = async () => {
    if (!content.trim() || isSending) return;

    setIsSending(true);

    try {
      await onSend({
        recipientId: recipientId!,
        recipientType,
        channel: selectedChannel || undefined,
        subject: selectedChannel === Channel.EMAIL ? subject : undefined,
        content,
        attachments: await uploadAttachments(attachments),
        threadId,
        tripId,
        scheduledFor: scheduledFor || undefined
      });

      // Clear and save empty draft
      setContent('');
      setSubject('');
      setAttachments([]);
      setScheduledFor(null);
      saveDraft(draftKey, { content: '', subject: '' });

    } catch (error) {
      toast.error('Failed to send message', {
        description: error.message
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleTemplateSelect = (template: MessageTemplate) => {
    setContent(template.contentTemplate);
    if (template.subjectTemplate) {
      setSubject(template.subjectTemplate);
    }
    setSelectedChannel(template.channel);
    setShowTemplatePicker(false);

    // Focus on first variable
    const firstVar = template.variables.find(v => v.required);
    if (firstVar) {
      // Would highlight variable for user to fill
    }
  };

  const availableChannels = useAvailableChannels(recipientType, recipientId);

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Composer toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100">
        {/* Channel selector */}
        <ChannelSelector
          value={selectedChannel}
          onChange={setSelectedChannel}
          availableChannels={availableChannels}
          disabled={disabled}
        />

        {/* Template button */}
        <Tooltip content="Insert template">
          <Button
            variant="ghost"
            size="sm"
            icon={<TemplateIcon />}
            onClick={() => setShowTemplatePicker(true)}
            disabled={disabled}
          >
            Template
          </Button>
        </Tooltip>

        {/* Attachment button */}
        <Tooltip content="Attach file">
          <Button
            variant="ghost"
            size="sm"
            icon={<PaperclipIcon />}
            onClick={() => document.getElementById('file-input')?.click()}
            disabled={disabled}
          />
        </Tooltip>
        <input
          id="file-input"
          type="file"
          multiple
          className="hidden"
          onChange={(e) => setAttachments(Array.from(e.target.files || []))}
        />

        {/* Schedule button */}
        <Tooltip content="Schedule message">
          <Button
            variant="ghost"
            size="sm"
            icon={<ClockIcon />}
            onClick={() => setShowSchedulePicker(true)}
            disabled={disabled}
          />
        </Tooltip>

        <div className="flex-1" />

        {/* Character count for SMS */}
        {selectedChannel === Channel.SMS && (
          <span className={cn(
            "text-xs",
            content.length > 160 ? "text-red-500" : "text-gray-500"
          )}>
            {content.length}/160
          </span>
        )}
      </div>

      {/* Email subject field */}
      {selectedChannel === Channel.EMAIL && (
        <div className="px-4 py-2 border-b border-gray-100">
          <Input
            placeholder="Subject"
            value={subject}
            onChange={setSubject}
            disabled={disabled}
          />
        </div>
      )}

      {/* Message content */}
      <div className="px-4 py-3">
        <Textarea
          placeholder="Type your message..."
          value={content}
          onChange={setContent}
          disabled={disabled}
          rows={4}
          maxLength={selectedChannel === Channel.SMS ? 160 : undefined}
          autoFocus
        />
      </div>

      {/* Attachments preview */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2 px-4 pb-2">
          {attachments.map((file, i) => (
            <AttachmentPreview
              key={i}
              file={file}
              onRemove={() => setAttachments(a => a.filter((_, j) => j !== i))}
            />
          ))}
        </div>
      )}

      {/* Scheduled indicator */}
      {scheduledFor && (
        <div className="px-4 pb-2">
          <Badge variant="info" icon={<ClockIcon />}>
            Scheduled for {formatDateTime(scheduledFor)}
          </Badge>
        </div>
      )}

      {/* Footer with send button */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => saveDraft(draftKey, { content, subject })}
        >
          Save Draft
        </Button>

        <Button
          variant="primary"
          size="md"
          icon={isSending ? <Spinner /> : <SendIcon />}
          onClick={handleSend}
          disabled={!content.trim() || disabled || isSending}
        >
          {isSending ? 'Sending...' : scheduledFor ? 'Schedule' : 'Send'}
        </Button>
      </div>

      {/* Template picker modal */}
      {showTemplatePicker && (
        <TemplatePickerModal
          onSelect={handleTemplateSelect}
          onClose={() => setShowTemplatePicker(false)}
        />
      )}

      {/* Schedule picker modal */}
      {showSchedulePicker && (
        <SchedulePickerModal
          onSelect={setScheduledFor}
          onClose={() => setShowSchedulePicker(false)}
        />
      )}
    </div>
  );
};
```

### ConversationView Component

```typescript
// components/messages/ConversationView.tsx

interface ConversationViewProps {
  threadId: string;
  messages: Message[];
  loading?: boolean;
  onSendMessage: (content: string) => void;
  onRetryMessage?: (messageId: string) => void;
}

/**
 * Threaded conversation view with real-time updates
 *
 * Features:
 * - Message grouping by date
 * - Inbound/outbound visual distinction
 * - Delivery status indicators
 * - Message actions (retry, forward, delete)
 * - Auto-scroll to new messages
 * - Typing indicators
 */
export const ConversationView: React.FC<ConversationViewProps> = ({
  threadId,
  messages,
  loading,
  onSendMessage,
  onRetryMessage
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [replyToMessage, setReplyToMessage] = useState<Message | null>(null);
  const { connected } = useRealtimeMessages({ threadId });

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Group messages by date
  const groupedMessages = useMemo(() => {
    const groups: Record<string, Message[]> = {};

    for (const message of messages) {
      const dateKey = format(message.createdAt, 'yyyy-MM-dd');
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(message);
    }

    return groups;
  }, [messages]);

  if (loading) {
    return <ConversationSkeleton />;
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Thread header */}
      <ThreadHeader threadId={threadId} />

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        {Object.entries(groupedMessages).map(([dateKey, dateMessages]) => (
          <div key={dateKey}>
            {/* Date separator */}
            <DateSeparator date={new Date(dateKey)} />

            {/* Messages for this date */}
            {dateMessages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOutbound={message.direction === 'outbound'}
                replyTo={replyToMessage}
                onReply={() => setReplyToMessage(message)}
                onRetry={onRetryMessage}
              />
            ))}
          </div>
        ))}

        {/* Connection status indicator */}
        {!connected && (
          <div className="fixed bottom-4 right-4">
            <Badge variant="warning">
              Reconnecting...
            </Badge>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Reply preview */}
      {replyToMessage && (
        <div className="px-4 py-2 bg-indigo-50 border-t border-indigo-100 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-indigo-700">
            <ReplyIcon size="sm" />
            <span>Replying to: {replyToMessage.content.substring(0, 50)}...</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon={<XIcon />}
            onClick={() => setReplyToMessage(null)}
          />
        </div>
      )}

      {/* Message composer */}
      <MessageComposer
        threadId={threadId}
        onSend={onSendMessage}
        replyToMessageId={replyToMessage?.id}
      />
    </div>
  );
};

/**
 * Individual message bubble
 */
const MessageBubble: React.FC<{
  message: Message;
  isOutbound: boolean;
  replyTo?: Message | null;
  onReply?: () => void;
  onRetry?: (messageId: string) => void;
}> = ({ message, isOutbound, replyTo, onReply, onRetry }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <div
      className={cn(
        "flex mb-4",
        isOutbound ? "justify-end" : "justify-start"
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={cn("max-w-[70%]", !isOutbound && "flex gap-3")}>
        {/* Avatar for inbound messages */}
        {!isOutbound && (
          <Avatar
            src={message.senderAvatar}
            name={message.senderName}
            size="sm"
          />
        )}

        <div>
          {/* Reply preview */}
          {replyTo && (
            <div className="text-xs text-gray-500 mb-1 px-2 py-1 bg-gray-100 rounded">
              <ReplyIcon size="xs" className="inline mr-1" />
              {replyTo.content.substring(0, 30)}...
            </div>
          )}

          {/* Message bubble */}
          <div
            className={cn(
              "rounded-2xl px-4 py-2",
              isOutbound
                ? "bg-indigo-600 text-white rounded-br-sm"
                : "bg-white text-gray-900 rounded-bl-sm shadow-sm"
            )}
          >
            {/* Channel indicator for cross-channel messages */}
            {message.channel !== message.recipientChannel && (
              <div className="flex items-center gap-1 text-xs opacity-70 mb-1">
                <ChannelIcon channel={message.channel} size="xs" />
                <span>via {message.channel}</span>
              </div>
            )}

            {/* Subject for email */}
            {message.subject && (
              <div className="font-semibold mb-1">{message.subject}</div>
            )}

            {/* Content */}
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>

            {/* Attachments */}
            {message.attachments.length > 0 && (
              <div className="mt-2 space-y-1">
                {message.attachments.map((att, i) => (
                  <AttachmentCard key={i} attachment={att} />
                ))}
              </div>
            )}
          </div>

          {/* Metadata row */}
          <div className={cn(
            "flex items-center gap-2 mt-1 text-xs text-gray-500",
            isOutbound ? "justify-end" : "justify-start"
          )}>
            <span>{format(message.createdAt, 'HH:mm')}</span>

            {/* Delivery status for outbound */}
            {isOutbound && (
              <DeliveryStatusIcon
                status={message.status}
                channel={message.channel}
                showLabel
              />
            )}

            {/* Read receipt */}
            {isOutbound && message.status === MessageStatus.READ && (
              <span className="text-indigo-600">Read</span>
            )}
          </div>

          {/* Error message */}
          {message.status === MessageStatus.FAILED && message.errorMessage && (
            <div className="mt-1 text-xs text-red-500 flex items-center gap-1">
              <AlertCircleIcon size="xs" />
              {message.errorMessage}
            </div>
          )}

          {/* Action buttons */}
          {showActions && (
            <div className={cn(
              "flex gap-1 mt-1",
              isOutbound ? "justify-end" : "justify-start"
            )}>
              <Button
                variant="ghost"
                size="xs"
                icon={<ReplyIcon />}
                onClick={onReply}
              >
                Reply
              </Button>

              {message.status === MessageStatus.FAILED && onRetry && (
                <Button
                  variant="ghost"
                  size="xs"
                  icon={<RefreshIcon />}
                  onClick={() => onRetry(message.id)}
                >
                  Retry
                </Button>
              )}

              <Button
                variant="ghost"
                size="xs"
                icon={<ForwardIcon />}
              >
                Forward
              </Button>

              <Button
                variant="ghost"
                size="xs"
                icon={<TrashIcon />}
                className="text-red-500"
              >
                Delete
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
```

### ChannelSelector Component

```typescript
// components/messages/ChannelSelector.tsx

interface ChannelSelectorProps {
  value: Channel | null;
  onChange: (channel: Channel) => void;
  availableChannels: Channel[];
  disabled?: boolean;
}

/**
 * Channel selection dropdown with visual indicators
 */
export const ChannelSelector: React.FC<ChannelSelectorProps> = ({
  value,
  onChange,
  availableChannels,
  disabled
}) => {
  const [open, setOpen] = useState(false);

  const channelInfo: Record<Channel, {
    icon: React.ReactNode;
    label: string;
    color: string;
    description: string;
  }> = {
    [Channel.WHATSAPP]: {
      icon: <WhatsAppIcon />,
      label: 'WhatsApp',
      color: '#25D366',
      description: 'Instant messaging'
    },
    [Channel.EMAIL]: {
      icon: <MailIcon />,
      label: 'Email',
      color: '#6366F1',
      description: 'Email message'
    },
    [Channel.SMS]: {
      icon: <SMSIcon />,
      label: 'SMS',
      color: '#F59E0B',
      description: 'Text message (160 chars)'
    },
    [Channel.IN_APP]: {
      icon: <BellIcon />,
      label: 'In-App',
      color: '#10B981',
      description: 'App notification'
    }
  };

  const selected = value ? channelInfo[value] : null;

  return (
    <Dropdown open={open} onOpenChange={setOpen}>
      <DropdownTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          className="gap-2"
        >
          {selected ? (
            <>
              <span style={{ color: selected.color }}>
                {selected.icon}
              </span>
              <span>{selected.label}</span>
            </>
          ) : (
            <>
              <ChannelIcon size="sm" />
              <span>Select channel</span>
            </>
          )}
          <ChevronDownIcon size="sm" />
        </Button>
      </DropdownTrigger>

      <DropdownContent align="start" className="w-56">
        {availableChannels.map((channel) => {
          const info = channelInfo[channel];
          return (
            <DropdownItem
              key={channel}
              onClick={() => {
                onChange(channel);
                setOpen(false);
              }}
              className="flex items-center gap-3"
            >
              <span style={{ color: info.color }}>
                {info.icon}
              </span>
              <div className="flex-1">
                <div className="font-medium">{info.label}</div>
                <div className="text-xs text-gray-500">
                  {info.description}
                </div>
              </div>
              {value === channel && (
                <CheckIcon size="sm" className="text-indigo-600" />
              )}
            </DropdownItem>
          );
        })}

        {availableChannels.length === 0 && (
          <div className="px-3 py-2 text-sm text-gray-500">
            No channels available for this recipient
          </div>
        )}
      </DropdownContent>
    </Dropdown>
  );
};
```

### DeliveryStatusIcon Component

```typescript
// components/messages/DeliveryStatusIcon.tsx

interface DeliveryStatusIconProps {
  status: MessageStatus;
  channel: Channel;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

/**
 * Visual indicator for message delivery status
 *
 * Status meanings:
 * - queued: Message is in queue, waiting to be sent
 * - sent: Message has been sent to the channel
 * - delivered: Message has been delivered to recipient
 * - read: Message has been read by recipient
 * - failed: Message delivery failed
 * - bounced: Message bounced (email)
 */
export const DeliveryStatusIcon: React.FC<DeliveryStatusIconProps> = ({
  status,
  channel,
  showLabel = false,
  size = 'sm'
}) => {
  const statusConfig: Record<MessageStatus, {
    icon: React.ReactNode;
    color: string;
    label: string;
    animate?: boolean;
  }> = {
    [MessageStatus.QUEUED]: {
      icon: <ClockIcon />,
      color: 'text-gray-400',
      label: 'Queued',
      animate: false
    },
    [MessageStatus.SENT]: {
      icon: <PaperPlaneIcon />,
      color: 'text-blue-500',
      label: 'Sent',
      animate: false
    },
    [MessageStatus.DELIVERED]: {
      icon: <DoubleCheckIcon />,
      color: 'text-green-500',
      label: 'Delivered',
      animate: false
    },
    [MessageStatus.READ]: {
      icon: <DoubleCheckIcon />,
      color: 'text-indigo-600',
      label: 'Read',
      animate: false
    },
    [MessageStatus.FAILED]: {
      icon: <AlertCircleIcon />,
      color: 'text-red-500',
      label: 'Failed',
      animate: false
    },
    [MessageStatus.BOUNCED]: {
      icon: <BouncedIcon />,
      color: 'text-orange-500',
      label: 'Bounced',
      animate: false
    }
  };

  const config = statusConfig[status];

  // WhatsApp-style checkmarks
  if (channel === Channel.WHATSAPP) {
    return (
      <div className={cn("flex items-center gap-0.5", config.color)}>
        <CheckIcon size={size} />
        {status === MessageStatus.DELIVERED && (
          <CheckIcon size={size} className="-ml-2.5" />
        )}
        {status === MessageStatus.READ && (
          <CheckIcon size={size} className="-ml-2.5 text-blue-500" />
        )}
        {showLabel && (
          <span className="ml-1 text-xs">{config.label}</span>
        )}
      </div>
    );
  }

  // Generic status for other channels
  return (
    <div className={cn("flex items-center gap-1", config.color)}>
      <span className={config.animate && 'animate-pulse'}>
        {config.icon}
      </span>
      {showLabel && (
        <span className="text-xs">{config.label}</span>
      )}
    </div>
  );
};
```

---

## Key Screens

### Inbox Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────┐  Messages  ┌──────────────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ Logo│  ▼ Filters │  Search threads  │  │ Templates│  │  + New Message │  │
│  └─────┘            └──────────────────┘  └──────────┘  └────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Inbox │ Sent │ Scheduled │ Archived                                    12  │
├───────┬─────────────────────────────────────────────────────────────────────┤
│       │  ┌──────────────────────────────────────────────────────────────┐  │
│       │  │ 📱 │ 👤 John Doe                              🔴  2  ✓✓  │  │
│  Filt │  │    │ Hey, when should we...           2m ago               │  │
│  ers  │  │    │ 🏷️ Goa Trip - March 2026                              │  │
│       │  ├──────────────────────────────────────────────────────────────┤  │
│       │  │ ✉️ │ 👤 Jane Smith                           ✓   5m ago  │  │
│       │  │    │ Booking confirmation for...                           │  │
│       │  │    │ 🏷️ Kerala Package                                     │  │
│       │  ├──────────────────────────────────────────────────────────────┤  │
│       │  │ 📱 │ 👤 Raj Kumar                             ✓   1h ago  │  │
│       │  │    │ Payment received! Thank you...                         │  │
│       │  ├──────────────────────────────────────────────────────────────┤  │
│       │  │ ✉️ │ 👤 Travel Agency                       ✓✓  Yesterday│  │
│       │  │    │ Re: Supplier invoice for...                            │  │
│       │  └──────────────────────────────────────────────────────────────┘  │
├───────┴─────────────────────────────────────────────────────────────────────┤
│  ← → Reply │ Forward │ Archive │ Delete │ Mark Read │ More...              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Conversation Detail Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Inbox │ John Doe │ 📱 WhatsApp │ 🏷️ Goa Trip - March 2026        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ──────────────────────────────────── Today ─────────────────────────────   │
│                                                                              │
│  👤 John Doe                                      14:23                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Hi! I'm interested in the Goa trip. When is the                        │ │
│  │ best time to visit? Also, what's included in the package?              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                        ✓✓                                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ │ You                                              14:25              │ │
│  │ └────────────────────────────────────────────────────────────────────┘ │
│  │ Hi John! March-April is ideal for Goa. The package includes:            │
│  │ - Flights                                                               │
│  │ - 4-star accommodation                                                  │
│  │ - Breakfast                                                              │
│  │ - Sightseeing                                                           │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                        ✓✓                                    │
│                                                                              │
│  👤 John Doe                                      14:30                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Great! Can you send me the detailed itinerary?                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                        ✓                                     │
│                                                                              │
│  ─────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ │ 💬 Reply to John Doe...                                    📎 📷  │ │
│  │ └────────────────────────────────────────────────────────────────────┘ │
│  │                                                                          │ │
│  │ 📋 Template │ 📎 Attach │ 📅 Schedule │ 💾 Save Draft    [Send →]      │ │
│  └──────────────────────────────────────────────────────────────────────────┘
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Template Picker Modal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Select Template                                              [×]           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────┐  ┌──────────────────────────────┐ │
│  │ 🔍 Search templates...              │  │  Channel: [All ▼]           │ │
│  └──────────────────────────────────────┘  └──────────────────────────────┘ │
│                                                                              │
│  Categories:  [All] [Booking] [Payment] [Itinerary] [Promotional]           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ 📱 Booking Confirmation                                          WhatsApp│ │
│  │    Hello {{customerName}}, your booking to {{destination}} is...       │ │
│  │    [Variables: customerName, destination, dates, totalPrice]           │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │ ✉️ Payment Reminder                                                Email  │ │
│  │    Dear {{customerName}}, this is a reminder that your payment...     │ │
│  │    [Variables: customerName, amount, dueDate, paymentLink]            │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │ 📱 Itinerary Ready                                                WhatsApp│ │
│  │    Excited to share your {{destination}} itinerary! 🌴                 │ │
│  │    [Variables: customerName, destination, itineraryLink]               │ │
│  ├────────────────────────────────────────────────────────────────────────┤ │
│  │ ✉️ Thank You                                                      Email  │ │
│  │    Thank you for choosing us! Here's a summary of your trip...         │ │
│  │    [Variables: customerName, tripSummary, feedbackLink]                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  [+ Create New Template]                        [Cancel]  [Select Template]  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Schedule Message Modal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Schedule Message                                              [×]           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Your message will be sent at the scheduled time.                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  📅 Date & Time                                                        │ │
│  │  ┌────────────────┐  ┌────────────────────────────────────────────┐   │ │
│  │  │ 📅 April 25,   │  │   🕐 10:30 AM                               │   │ │
│  │  │    2026        │  │                                             │   │ │
│  │  └────────────────┘  └────────────────────────────────────────────┘   │ │
│  │                                                                          │ │
│  │  Timezone: India Standard Time (IST) UTC+5:30                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  🌍 Recipient's Timezone                                               │ │
│  │  New York, USA (EST) - April 25, 2026 at 1:00 AM                      │ │
│  │  ⚠️ Recipient will receive this message late at night.                 │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  📋 Quick Schedule Options                                             │ │
│  │  [Tomorrow 9 AM] [Next Monday 10 AM] [Custom...]                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ⏰ Send at optimal time                                               │ │
│  │  AI will determine the best time based on recipient's engagement       │ │
│  │  [Learn more about smart scheduling]                                    │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│                                    [Cancel]  [Schedule Message]              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Interaction Patterns

### Sending Messages Flow

```
┌──────────────┐
│ User clicks  │
│ "New Message"│
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ Recipient selector   │
│ (with autocomplete)  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Channel auto-detect  │
│ based on recipient   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Message composer     │
│ with template picker │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐     ┌──────────────────┐
│ User clicks "Send"   │────▶│ Show "Sent"      │
└──────────────────────┘     │ status           │
                             │ with delivery    │
                             │ progress         │
                             └──────────────────┘
                                  │
                                  ▼
                             ┌──────────────────┐
                             │ Real-time update │
                             │ when delivered   │
                             └──────────────────┘
```

### Template Insertion Flow

```
┌──────────────────┐
│ User clicks      │
│ "Template"       │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ Template picker modal    │
│ with search & filters    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ User selects template    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Variables highlighted    │
│ in message body          │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ User fills variables     │
│ or leaves defaults       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Template inserted,       │
│ ready to edit/send       │
└──────────────────────────┘
```

### Message Retry Flow

```
┌──────────────────────────┐
│ Message shows as failed  │
│ with error message       │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ User hovers over message │
│ → "Retry" button appears │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ User clicks "Retry"      │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ System attempts resend   │
│ with fallback channel    │
└────────┬─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│Success│ │  Failed  │
└───────┘ └─────┬────┘
               │
               ▼
        ┌──────────────────┐
        │ Show error,      │
        │ suggest alt      │
        │ channel          │
        └──────────────────┘
```

---

## Responsive Design

### Breakpoints

```css
/* Communication Hub responsive breakpoints */

/* Mobile: 320px - 639px */
@media (max-width: 639px) {
  /* Single column layout */
  /* Thread list takes full width */
  /* Conversation view slides in */
}

/* Tablet: 640px - 1023px */
@media (min-width: 640px) and (max-width: 1023px) {
  /* Split view: 40% thread list, 60% conversation */
  /* Collapsible sidebar */
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  /* Full split view: 350px thread list, rest conversation */
  /* Persistent sidebar */
}
```

### Mobile Layout

```
┌─────────────────────────────┐
│ ☰  Messages    [+ New]     │  ← Header
├─────────────────────────────┤
│                             │
│  ┌───────────────────────┐ │
│  │ John Doe              │ │
│  │ Hey, when should...   │ │  ← Thread list
│  │ 🔴 2  ✓✓  2m ago    │ │     (full width)
│  └───────────────────────┘ │
│  ┌───────────────────────┐ │
│  │ Jane Smith            │ │
│  │ Booking confirm...    │ │
│  │ ✓  5m ago            │ │
│  └───────────────────────┘ │
│                             │
└─────────────────────────────┘

         [TAP THREAD]

┌─────────────────────────────┐
│ ← John Doe      [⋮]         │  ← Back to list
├─────────────────────────────┤
│                             │
│  Today                      │
│  ┌───────────────────────┐ │
│  │ Hi! I'm interested... │ │  ← Conversation
│  └───────────────────────┘ │     (slides in)
│  ┌─────────────────────┐  │
│  │Hi John! March...    │  │
│  └─────────────────────┘  │
│                             │
│  ┌─────────────────────┐  │
│  │[Type message...]    │  │  ← Composer
│  │                     │  │     (fixed bottom)
│  │               [Send]│  │
│  └─────────────────────┘  │
│                             │
└─────────────────────────────┘
```

### Tablet Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ☰  Messages    [Search]                      [+ New]    │
├───────────────┬─────────────────────────────────────────────────────────────┤
│               │                                                             │
│  ┌─────────┐ │  ┌───────────────────────────────────────────────────────┐ │
│  │ John    │ │  │ Today                                               │ │
│  │ Doe     │ │  │ ┌─────────────────────────────────────────────────┐ │ │
│  │Hey,     │ │ │  │ Hi! I'm interested in the Goa trip...           │ │ │
│  │when...  │ │ │  └─────────────────────────────────────────────────┘ │ │
│  │🔴2 ✓✓ 2m│ │ │                                                      │ │
│  ├─────────┤ │ │  ┌─────────────────────────────────────────────────┐ │ │
│  │ Jane    │ │ │  │ Hi John! March-April is ideal...                │ │
│  │ Smith   │ │ │  └─────────────────────────────────────────────────┘ │ │
│  │Booking  │ │ │                                                      │ │
│  │confirm. │ │ │  ┌─────────────────────────────────────────────────┐ │ │
│  │✓ 5m ago│ │ │  │ Great! Can you send me the detailed itinerary?  │ │ │
│  ├─────────┤ │ │  └─────────────────────────────────────────────────┘ │ │
│  │ Raj     │ │ │                                                      │ │
│  │Kumar    │ │ │  ┌─────────────────────────────────────────────────┐ │ │
│  │Payment  │ │ │  │ [Type your message...]               [Send →]  │ │ │
│  │received!│ │ │  └─────────────────────────────────────────────────┘ │ │
│  │✓✓ 1h    │ │ │                                                      │ │
│  └─────────┘ │ └───────────────────────────────────────────────────────┘ │
│               │                                                             │
│ 40% Thread    │                   60% Conversation                         │
│    List       │                      View                                 │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

---

## Accessibility

### WCAG 2.1 Compliance

| Guideline | Implementation |
|-----------|----------------|
| **1.1 Text Alternatives** | All icons have `aria-label`, channel indicators have text |
| **1.3 Adaptable** | Semantic HTML, proper heading hierarchy |
| **1.4 Distinguishable** | 4.5:1 contrast ratio for text, visual indicators beyond color |
| **2.1 Keyboard Accessible** | Full keyboard navigation, visible focus indicators |
| **2.2 Enough Time** | No auto-dismissing modals without user control |
| **2.3 Seizures** | No flashing content, smooth animations |
| **2.4 Navigable** | Skip links, clear page titles |
| **3.1 Readable** | Clear language, consistent terminology |
| **3.2 Predictable** | Consistent layout, focus doesn't change unexpectedly |
| **3.3 Input Assistance** | Error suggestions, clear labels |
| **4.1 Compatible** | Proper ARIA attributes, valid HTML |

### Keyboard Navigation

```typescript
// Keyboard shortcuts for Communication Hub

const keyboardShortcuts = {
  // Navigation
  'Cmd+K': 'Focus search',
  'Cmd+N': 'New message',
  'Cmd+I': 'Go to inbox',
  'Cmd+T': 'Open template picker',

  // Thread navigation
  'J / ↓': 'Next thread',
  'K / ↑': 'Previous thread',
  'Enter': 'Open selected thread',
  'Escape': 'Close thread / modal',

  // Message actions
  'R': 'Reply to message',
  'F': 'Forward message',
  'Cmd+Enter': 'Send message',
  'Esc': 'Cancel compose',

  // Selection
  'X': 'Select thread',
  'Shift+X': 'Select multiple',
  'Cmd+A': 'Select all'
};
```

### ARIA Labels

```tsx
{/* Example of accessible message bubble */}
<div
  role="listitem"
  aria-label={`Message from ${message.senderName}, ${formatRelativeTime(message.createdAt)}`}
  aria-setsize={totalMessages}
  aria-posinset={messageIndex}
>
  <div
    className={bubbleClass}
    role="article"
    aria-label={isOutbound ? 'Your message' : `Message from ${message.senderName}`}
  >
    {message.content}
  </div>

  <div
    className="flex items-center gap-2"
    role="status"
    aria-live="polite"
  >
    <time>{format(message.createdAt, 'HH:mm')}</time>
    <DeliveryStatusIcon
      status={message.status}
      channel={message.channel}
      aria-label={`Delivery status: ${message.status}`}
    />
  </div>
</div>
```

---

## Animation & Micro-interactions

### Message Send Animation

```css
@keyframes messageSend {
  0% {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message-bubble.outbound.sending {
  animation: messageSend 0.2s ease-out forwards;
}
```

### Delivery Status Animation

```css
@keyframes deliveryPulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.delivery-status.sending {
  animation: deliveryPulse 1s ease-in-out infinite;
}

@keyframes deliveredCheck {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.delivery-status.delivered svg {
  animation: deliveredCheck 0.3s ease-out;
}
```

### Typing Indicator

```css
@keyframes typingBounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-4px);
  }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #9CA3AF;
  animation: typingBounce 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}
```

### Thread Item Hover Effect

```css
.thread-item {
  transition: all 0.15s ease;
}

.thread-item:hover {
  background-color: #F9FAFB;
  transform: translateX(2px);
}

.thread-item.selected {
  background-color: #EEF2FF;
  border-left-color: #4F46E5;
}
```

---

## Summary

The Communication Hub UX/UI design provides:

1. **Familiar Chat Experience**: Patterned after popular messaging apps
2. **Multi-Channel Clarity**: Always aware of which channel you're using
3. **Efficient Composition**: Quick sending with templates and smart defaults
4. **Real-Time Feedback**: Live delivery status and typing indicators
5. **Responsive Design**: Seamless experience across mobile, tablet, and desktop
6. **Accessibility First**: WCAG 2.1 AA compliant with full keyboard navigation

---

**Next:** Communication Hub Template System Deep Dive (COMM_HUB_03) — template engine architecture, variable system, and localization
