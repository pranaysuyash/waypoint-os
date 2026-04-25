# CUSTOMER_PORTAL_02: UX/UI Deep Dive

> Customer Portal — Interface Design, User Experience, and Visual Design

---

## Table of Contents

1. [Overview](#overview)
2. [Design Philosophy](#design-philosophy)
3. [Information Architecture](#information-architecture)
4. [Layout System](#layout-system)
5. [Component Library](#component-library)
6. [Mobile Experience](#mobile-experience)
7. [Accessibility](#accessibility)
8. [Branding and White-Labeling](#branding-and-white-labeling)

---

## Overview

The Customer Portal UX prioritizes simplicity, clarity, and reassurance. Customers should feel confident about their trip without being overwhelmed by operational complexity.

### Design Goals

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER PORTAL DESIGN GOALS                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  1. IMMEDIATE ORIENTATION                                                 │
│     "Where's my trip? What's the status? What do I need to do?"           │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Answer the 3 core questions above the fold                   │  │
│     │ • Clear visual hierarchy with trip status prominent             │  │
│     │ • Action buttons for next steps clearly visible                │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  2. ANXIETY REDUCTION                                                     │
│     "Am I missing something? Is everything confirmed?"                    │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Show confirmation status visually                             │  │
│     │ • Clear document checklist                                     │  │
│     │ • Countdown to departure                                       │  │
│     │ • Reassuring copy for waiting states                           │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  3. MOBILE-FIRST                                                          │
│     "I need to check my trip on the go"                                   │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Optimized for smartphones (primary use case)                  │  │
│     │ • Touch-friendly targets (44px minimum)                        │  │
│     │ • Progressive Web App capabilities                             │  │
│     │ • Offline access to key documents                              │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  4. AGENCY CONNECTION                                                     │
│     "I can reach my agent if I need to"                                   │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Agent photo and name visible                                  │  │
│     │ • Quick message button                                         │  │
│     │ • Expected response time shown                                 │  │
│     │ • Agency branding prominent                                    │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  5. SELF-SERVICE CONFIDENCE                                               │
│     "I can find what I need without calling"                              │
│     ┌─────────────────────────────────────────────────────────────────┐  │
│     │ • Documents easy to find and download                           │  │
│     │ • Payment links accessible                                     │  │
│     │ • Itinerary clear and printable                                │  │
│     │ • Preferences manageable                                       │  │
│     └─────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Philosophy

### Core UX Principles

| Principle | Description | Application |
|-----------|-------------|-------------|
| **Progressive Disclosure** | Show essential info first, details on demand | Trip card shows status + key dates, expand for full itinerary |
| **Visual Hierarchy** | Guide attention to what matters most | Status badges, countdown timers, action buttons stand out |
| **Familiar Patterns** | Use conventions users already know | Bottom nav on mobile, hamburger menu, standard icons |
| **Forgiving Interactions** | Easy to undo, hard to make mistakes | Confirmation dialogs, clear back buttons |
| **Positive Language** | Frame actions positively | "Get documents" vs "Download forms", "Contact agent" vs "Report issue" |

### Anti-Patterns to Avoid

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           DESIGN ANTI-PATTERNS                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ❌ DON'T: Show operational details to customers                          │
│     • Priority scores, assignment queues, internal notes                  │
│     • WHY: Confusing, not actionable, creates anxiety                     │
│                                                                            │
│  ❌ DON'T: Use technical jargon                                            │
│     • "PNR status", "GDS queue", "Merchant category code"                 │
│     • WHY: Customers don't understand travel industry terminology          │
│                                                                            │
│  ❌ DON'T: Hide important info behind clicks                               │
│     • Trip status buried in itinerary, payment balance hidden             │
│     • WHY: Customers need reassurance, not discovery                      │
│                                                                            │
│  ❌ DON'T: Editable fields for trip details                                │
│     • Change destination, modify dates directly                           │
│     • WHY: Creates data inconsistency, requires agent review anyway       │
│                                                                            │
│  ❌ DON'T: Generic "contact support"                                       │
│     • Faceless support email, no agent assignment                        │
│     • WHY: Undermines agency relationship, customers want THEIR agent     │
│                                                                            │
│  ✅ INSTEAD: Show trip status prominently with action buttons             │
│  ✅ INSTEAD: Use plain language ("Your flight is confirmed")              │
│  ✅ INSTEAD: Key info visible, details expandable                        │
│  ✅ INSTEAD: "Request change" button that messages agent                 │
│  ✅ INSTEAD: Agent card with photo, name, response time                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Information Architecture

### Site Map

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         CUSTOMER PORTAL SITE MAP                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  / (Home/Dashboard)                                                 │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │ • Active trips summary (cards)                              │   │  │
│  │  │ • Quick actions (message agent, view documents)             │   │  │
│  │  │ • Outstanding balance alert (if any)                        │   │  │
│  │  │ • Upcoming departure countdown                              │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                  │                                         │
│          ┌───────────────────────┼───────────────────────┐               │
│          ▼                       ▼                       ▼               │
│  ┌───────────────┐       ┌───────────────┐       ┌───────────────┐       │
│  │  /trips       │       │  /documents   │       │  /messages    │       │
│  │  /trips/:id   │       │  /documents/:id│      │  /messages/:id│       │
│  │               │       │               │       │               │       │
│  │ • Trip list   │       │ • All docs    │       │ • Thread view │       │
│  │ • Trip detail │       │ • Download    │       │ • Compose     │       │
│  │ • Itinerary   │       │ • Filter      │       │ • History     │       │
│  │ • Timeline    │       │               │       │               │       │
│  │ • Documents   │       │               │       │               │       │
│  │ • Messages    │       │               │       │               │       │
│  └───────────────┘       └───────────────┘       └───────────────┘       │
│                                                                            │
│  ┌───────────────┐       ┌───────────────┐       ┌───────────────┐       │
│  │  /payments    │       │  /profile     │       │  /help        │       │
│  │               │       │               │       │               │       │
│  │ • Payment     │       │ • Personal    │       │ • FAQ         │       │
│  │   history     │       │ • Traveler    │       │ • Contact     │       │
│  │ • Make        │       │ • Passport    │       │ • Guides      │       │
│  │   payment     │       │ • Preferences │       │               │       │
│  │ • Invoices    │       │ • Settings    │       │               │       │
│  └───────────────┘       └───────────────┘       └───────────────┘       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Patterns

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        NAVIGATION PATTERNS                                 │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  DESKTOP (> 768px):                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  [Agency Logo]        My Trips  Documents  Messages  [Agent Card]   │  │
│  │ ─────────────────────────────────────────────────────────────────── │  │
│  │                                                                      │  │
│  │  Main Content Area                                                  │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  MOBILE (< 768px):                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  [Agency Logo]                                    [☰]               │  │
│  │ ─────────────────────────────────────────────────────────────────── │  │
│  │                                                                      │  │
│  │  Main Content Area                                                  │  │
│  │                                                                      │  │
│  │ ─────────────────────────────────────────────────────────────────── │  │
│  │  [Trips] [Docs] [Messages] [Payments] [Profile]                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  TAB BAR ITEMS:                                                            │
│  • Trips — Active trip count badge                                       │
│  • Docs — Outstanding items badge                                        │
│  • Messages — Unread count badge                                         │
│  • Payments — Due amount badge (if any)                                  │
│  • Profile — No badge                                                     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Layout System

### Responsive Breakpoints

```typescript
// styles/breakpoints.ts
export const breakpoints = {
  xs: '375px',   // Small phones
  sm: '640px',   // Large phones
  md: '768px',   // Tablets (portrait)
  lg: '1024px',  // Tablets (landscape), small laptops
  xl: '1280px',  // Desktops
  '2xl': '1536px', // Large desktops
} as const;

export type Breakpoint = keyof typeof breakpoints;
```

### Grid System

```typescript
// styles/grid.ts
export const gridConfig = {
  columns: {
    mobile: 4,   // 4 columns on mobile
    tablet: 8,   // 8 columns on tablet
    desktop: 12, // 12 columns on desktop
  },
  gutters: {
    mobile: '16px',
    tablet: '24px',
    desktop: '32px',
  },
  containers: {
    mobile: '100%',
    tablet: '640px',
    desktop: '1024px',
    xl: '1280px',
  },
};

// Usage example
export const tripCardLayout = {
  // Mobile: 1 column
  mobile: 'grid-cols-1',
  // Tablet: 2 columns
  tablet: 'md:grid-cols-2',
  // Desktop: 3 columns
  desktop: 'lg:grid-cols-3',
};
```

### Spacing Scale

```typescript
// styles/spacing.ts
export const spacing = {
  0: '0',
  px: '1px',
  0.5: '2px',
  1: '4px',
  1.5: '6px',
  2: '8px',
  2.5: '10px',
  3: '12px',
  3.5: '14px',
  4: '16px',
  5: '20px',
  6: '24px',
  7: '28px',
  8: '32px',
  9: '36px',
  10: '40px',
  11: '44px',
  12: '48px',
  14: '56px',
  16: '64px',
  20: '80px',
  24: '96px',
  28: '112px',
  32: '128px',
  36: '144px',
  40: '160px',
  44: '176px',
  48: '192px',
  52: '208px',
  56: '224px',
  60: '240px',
  64: '256px',
  72: '288px',
  80: '320px',
  96: '384px',
} as const;
```

---

## Component Library

### Trip Card Component

```typescript
// components/customer/TripCard.tsx
import { Link } from '@/components/ui/link';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Countdown } from './Countdown';
import { TripStatusBadge } from './TripStatusBadge';
import { TripProgress } from './TripProgress';

interface TripCardProps {
  trip: CustomerTripView;
  agency: AgencyInfo;
}

export function TripCard({ trip, agency }: TripCardProps) {
  const daysUntilDeparture = Math.ceil(
    (new Date(trip.departureDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );

  return (
    <Link href={`/trips/${trip.id}`} className="block group">
      <article className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
        {/* Header Image */}
        {trip.destination.heroImage && (
          <div className="relative h-48 bg-gray-100">
            <img
              src={trip.destination.heroImage}
              alt={trip.destination.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <div className="absolute top-3 right-3">
              <TripStatusBadge status={trip.status} size="lg" />
            </div>
            {daysUntilDeparture <= 30 && daysUntilDeparture >= 0 && (
              <div className="absolute top-3 left-3">
                <Countdown date={trip.departureDate} />
              </div>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-4 sm:p-6">
          {/* Destination and Dates */}
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {trip.destination.name}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {formatDateRange(trip.departureDate, trip.returnDate)}
              </p>
              <p className="text-sm text-gray-500">
                {trip.travelers.length} {pluralize('traveler', trip.travelers.length)}
              </p>
            </div>

            {/* Price (if visible) */}
            {trip.totalAmount && (
              <div className="text-right">
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-lg font-semibold text-gray-900">
                  {formatCurrency(trip.totalAmount, trip.currency)}
                </p>
                {trip.paidAmount && trip.paidAmount < trip.totalAmount && (
                  <p className="text-xs text-amber-600">
                    {formatCurrency(trip.totalAmount - trip.paidAmount, trip.currency)} due
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Progress Bar */}
          <TripProgress trip={trip} className="mt-4" />

          {/* Quick Actions */}
          <div className="flex items-center gap-2 mt-4">
            {trip.status === 'quoted' && (
              <Button size="sm" variant="primary" className="flex-1">
                Review Quote
              </Button>
            )}
            {trip.status === 'confirmed' && (
              <Button size="sm" variant="outline" className="flex-1">
                View Itinerary
              </Button>
            )}
            {trip.documents.some(d => d.required && !d.completed) && (
              <Button size="sm" variant="ghost" className="flex-1">
                Documents Needed
              </Button>
            )}
          </div>

          {/* Agent Card (Compact) */}
          {trip.agent && (
            <div className="flex items-center gap-3 mt-4 pt-4 border-t border-gray-100">
              <img
                src={trip.agent.photo || '/default-avatar.png'}
                alt={trip.agent.name}
                className="w-8 h-8 rounded-full"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {trip.agent.name}
                </p>
                <p className="text-xs text-gray-500">
                  Your travel agent
                </p>
              </div>
              <Button size="sm" variant="ghost" asChild>
                <Link href={`/messages/${trip.id}`}>
                  <MessageIcon className="w-4 h-4" />
                </Link>
              </Button>
            </div>
          )}
        </div>
      </article>
    </Link>
  );
}

// Status Badge Component
export function TripStatusBadge({ status, size = 'md' }: { status: TripStatus; size?: 'sm' | 'md' | 'lg' }) {
  const config = {
    new: { label: 'New Request', color: 'blue' },
    quoted: { label: 'Quote Ready', color: 'amber' },
    confirmed: { label: 'Confirmed', color: 'green' },
    partially_paid: { label: 'Deposit Paid', color: 'blue' },
    paid: { label: 'Fully Paid', color: 'green' },
    in_progress: { label: 'Upcoming', color: 'blue' },
    active: { label: 'Traveling Now', color: 'purple' },
    completed: { label: 'Completed', color: 'gray' },
    cancelled: { label: 'Cancelled', color: 'red' },
  }[status];

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-sm',
  };

  const colorClasses = {
    blue: 'bg-blue-100 text-blue-800',
    amber: 'bg-amber-100 text-amber-800',
    green: 'bg-green-100 text-green-800',
    purple: 'bg-purple-100 text-purple-800',
    gray: 'bg-gray-100 text-gray-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <Badge className={`${sizeClasses[size]} ${colorClasses[config.color]}`}>
      {config.label}
    </Badge>
  );
}

// Countdown Component
export function Countdown({ date }: { date: Date }) {
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
  });

  useEffect(() => {
    const calculate = () => {
      const now = Date.now();
      const target = new Date(date).getTime();
      const diff = Math.max(0, target - now);

      setTimeLeft({
        days: Math.floor(diff / (1000 * 60 * 60 * 24)),
        hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
      });
    };

    calculate();
    const interval = setInterval(calculate, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [date]);

  if (timeLeft.days === 0 && timeLeft.hours === 0 && timeLeft.minutes === 0) {
    return null;
  }

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-full px-3 py-1.5 shadow-sm">
      <p className="text-xs font-medium text-gray-900">
        {timeLeft.days > 0 && `${timeLeft.days}d `}
        {timeLeft.hours > 0 && `${timeLeft.hours}h `}
        {timeLeft.days === 0 && `${timeLeft.minutes}m`}
      </p>
    </div>
  );
}

// Trip Progress Component
export function TripProgress({ trip, className }: { trip: CustomerTripView; className?: string }) {
  const steps = [
    { key: 'quoted', label: 'Quote', completed: ['quoted', 'confirmed', 'paid', 'completed'].includes(trip.status) },
    { key: 'confirmed', label: 'Confirmed', completed: ['confirmed', 'paid', 'completed'].includes(trip.status) },
    { key: 'documents', label: 'Documents', completed: trip.documents?.every(d => d.completed) ?? false },
    { key: 'paid', label: 'Paid', completed: trip.paidAmount >= trip.totalAmount },
  ];

  const currentStep = steps.findIndex(s => !s.completed);

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-2">
        {steps.map((step, index) => (
          <React.Fragment key={step.key}>
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${step.completed
                    ? 'bg-green-500 text-white'
                    : index === currentStep
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-500'
                  }
                `}
              >
                {step.completed ? '✓' : index + 1}
              </div>
              <p className="text-xs text-gray-600 mt-1">{step.label}</p>
            </div>
            {index < steps.length - 1 && (
              <div
                className={`
                  flex-1 h-0.5 mx-2
                  ${steps[index + 1].completed ? 'bg-green-500' : 'bg-gray-200'}
                `}
              />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
```

### Document List Component

```typescript
// components/customer/DocumentList.tsx
import { DocumentCard } from './DocumentCard';
import { EmptyState } from './EmptyState';

interface DocumentListProps {
  documents: CustomerDocumentView[];
  tripId?: string;
  filter?: DocumentCategory;
}

export function DocumentList({ documents, tripId, filter }: DocumentListProps) {
  const filtered = filter
    ? documents.filter(d => d.category === filter)
    : documents;

  const grouped = filtered.reduce((acc, doc) => {
    const category = doc.category || 'other';
    acc[category] = acc[category] || [];
    acc[category].push(doc);
    return acc;
  }, {} as Record<string, CustomerDocumentView[]>);

  if (filtered.length === 0) {
    return (
      <EmptyState
        icon={DocumentIcon}
        title="No documents yet"
        description={
          filter
            ? `No ${filter} documents available for this trip.`
            : "Documents will appear here as your trip is confirmed."
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([category, docs]) => (
        <div key={category}>
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide mb-3">
            {formatCategory(category)}
          </h3>
          <div className="space-y-2">
            {docs.map(doc => (
              <DocumentCard key={doc.id} document={doc} tripId={tripId} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function DocumentCard({ document, tripId }: { document: CustomerDocumentView; tripId?: string }) {
  const [downloading, setDownloading] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const response = await fetch(`/api/v1/customer/documents/${document.id}/download`);
      const data = await response.json();

      // Open download URL in new tab
      window.open(data.downloadUrl, '_blank');
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setDownloading(false);
    }
  };

  const icon = {
    invoice: ReceiptIcon,
    itinerary: CalendarIcon,
    ticket: TicketIcon,
    visa: PassportIcon,
    passport: PassportIcon,
    other: DocumentIcon,
  }[document.type] || DocumentIcon;

  return (
    <div className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
          <icon className="w-5 h-5 text-gray-600" />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">
          {document.name}
        </p>
        <p className="text-xs text-gray-500">
          {formatDate(document.createdAt)}
        </p>
      </div>

      <Button
        size="sm"
        variant="ghost"
        onClick={handleDownload}
        disabled={downloading}
        loading={downloading}
      >
        <DownloadIcon className="w-4 h-4" />
      </Button>
    </div>
  );
}
```

### Message Thread Component

```typescript
// components/customer/MessageThread.tsx
import { useMessages } from '@/hooks/useMessages';
import { MessageBubble } from './MessageBubble';
import { MessageInput } from './MessageInput';

interface MessageThreadProps {
  tripId: string;
}

export function MessageThread({ tripId }: MessageThreadProps) {
  const { messages, loading, sendMessage } = useMessages(tripId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Spinner />
          </div>
        ) : messages.length === 0 ? (
          <EmptyState
            icon={ChatIcon}
            title="Start a conversation"
            description="Message your agent with any questions about your trip."
          />
        ) : (
          <>
            {messages.map(message => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <MessageInput
          onSend={(content, attachments) => sendMessage({ content, attachments })}
          disabled={loading}
        />
      </div>
    </div>
  );
}

export function MessageBubble({ message }: { message: CustomerMessageView }) {
  const isCustomer = message.sender.role === 'customer';

  return (
    <div className={`flex ${isCustomer ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isCustomer ? 'order-2' : ''}`}>
        {/* Sender Name */}
        {!isCustomer && (
          <p className="text-xs text-gray-500 mb-1 ml-1">
            {message.sender.name}
          </p>
        )}

        {/* Message Content */}
        <div
          className={`
            rounded-2xl px-4 py-2
            ${isCustomer
              ? 'bg-blue-500 text-white rounded-br-sm'
              : 'bg-gray-100 text-gray-900 rounded-bl-sm'
            }
          `}
        >
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.content}
          </p>

          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 space-y-1">
              {message.attachments.map(attachment => (
                <AttachmentCard key={attachment.id} attachment={attachment} />
              ))}
            </div>
          )}
        </div>

        {/* Timestamp */}
        <p className={`text-xs text-gray-400 mt-1 ${isCustomer ? 'text-right mr-1' : 'ml-1'}`}>
          {formatTime(message.sentAt)}
          {message.readAt && ' • Read'}
        </p>
      </div>
    </div>
  );
}

export function MessageInput({ onSend, disabled }: { onSend: (content: string, attachments?: string[]) => void; disabled?: boolean }) {
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!content.trim() || sending) return;

    setSending(true);
    try {
      await onSend(content, attachments);
      setContent('');
      setAttachments([]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-2">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {attachments.map(url => (
            <div key={url} className="relative flex-shrink-0">
              <img src={url} alt="" className="h-16 rounded-lg" />
              <Button
                size="sm"
                variant="ghost"
                className="absolute -top-2 -right-2 h-6 w-6 p-0 bg-red-500 text-white rounded-full"
                onClick={() => setAttachments(a => a.filter(u => u !== url))}
              >
                <XIcon className="w-3 h-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex items-end gap-2">
        <Button
          size="sm"
          variant="ghost"
          className="flex-shrink-0"
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <PaperclipIcon className="w-5 h-5" />
        </Button>
        <input
          id="file-input"
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            // Upload files and get URLs
            Promise.all(files.map(uploadFile)).then(urls => {
              setAttachments(a => [...a, ...urls]);
            });
          }}
        />

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Type a message..."
          rows={1}
          className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={disabled}
        />

        <Button
          size="sm"
          variant="primary"
          onClick={handleSend}
          disabled={!content.trim() || sending}
        >
          <SendIcon className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
```

---

## Mobile Experience

### Mobile Layout Structure

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          MOBILE LAYOUT (375x812)                          │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  STATUS BAR (44px)                                                  │  │
│  │  9:41  ━━━━  📶  📡  🔋                                            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  HEADER (56px)                                                      │  │
│  │  ┌─────────────────────────────┐  ┌──────────┐                     │  │
│  │  │ [Agency Logo]  My Trips     │  │   [☰]    │                     │  │
│  │  └─────────────────────────────┘  └──────────┘                     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  MAIN CONTENT (scrollable)                                          │  │
│  │                                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │  ┌───────────────────────────────────────────────────────┐  │   │  │
│  │  │  │  [Trip Photo]                          [Confirmed]    │  │   │  │
│  │  │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │   │  │
│  │  │  │  Paris, France                                          │  │   │  │
│  │  │  │  Jun 15 - Jun 22, 2026                                   │  │   │  │
│  │  │  │  2 travelers  |  $4,500                                  │  │   │  │
│  │  │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │  │   │  │
│  │  │  │  ●──────●──────○──────○  Documents  View Itinerary      │  │   │  │
│  │  │  └───────────────────────────────────────────────────────┘  │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │  [Similar Trip Card]                                         │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  BOTTOM NAVIGATION (56px + safe area)                               │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │  │
│  │  │ 📋     │ │ 📄     │ │ 💬     │ │ 💳     │ │ 👤     │            │  │
│  │  │ Trips   │ │ Docs   │ │ Msgs   │ │ Pay    │ │ Profile│            │  │
│  │  │   (2)   │ │   (1)  │ │        │ │        │ │        │            │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  HOME INDICATOR (safe area)                                         │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Touch Target Minimum: 44x44px
Font Size (Body): 16px minimum
Line Height: 1.5 for readability
```

### Mobile-Specific Components

```typescript
// components/customer/MobilePullToRefresh.tsx
export function MobilePullToRefresh({ onRefresh, refreshing }: { onRefresh: () => void; refreshing: boolean }) {
  const [touching, setTouching] = useState(false);
  const [touchY, setTouchY] = useState(0);
  const [translateY, setTranslateY] = useState(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      setTouching(true);
      setTouchY(e.touches[0].clientY);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touching) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - touchY;

    if (diff > 0) {
      setTranslateY(Math.min(diff * 0.5, 120)); // Max 120px pull
    }
  };

  const handleTouchEnd = () => {
    if (translateY > 80 && !refreshing) {
      onRefresh();
    }
    setTouching(false);
    setTranslateY(0);
  };

  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      style={{ transform: `translateY(${translateY}px)` }}
      className="transition-transform duration-200"
    >
      {translateY > 40 && (
        <div className="flex items-center justify-center py-4">
          <Spinner size="sm" />
          <p className="ml-2 text-sm text-gray-600">
            {refreshing ? 'Refreshing...' : 'Pull to refresh'}
          </p>
        </div>
      )}
    </div>
  );
}

// components/customer/MobileSwipeActions.tsx
export function MobileSwipeActions({ children, actions }: {
  children: React.ReactNode;
  actions: Array<{
    icon: React.ReactNode;
    label: string;
    color: string;
    onPress: () => void;
  }>;
}) {
  const [translateX, setTranslateX] = useState(0);
  const [startX, setStartX] = useState(0);
  const actionWidth = 80;

  const handleTouchStart = (e: React.TouchEvent) => {
    setStartX(e.touches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    const diff = e.touches[0].clientX - startX;
    const maxSwipe = -(actions.length * actionWidth);
    setTranslateX(Math.max(maxSwipe, Math.min(0, diff)));
  };

  const handleTouchEnd = () => {
    // Snap to action or close
    const actionIndex = Math.round(Math.abs(translateX) / actionWidth);

    if (actionIndex > 0 && actionIndex <= actions.length) {
      setTranslateX(-(actionIndex * actionWidth));
      actions[actionIndex - 1].onPress();
    } else {
      setTranslateX(0);
    }
  };

  return (
    <div className="relative overflow-hidden">
      {/* Actions Background */}
      <div
        className="absolute inset-y-0 right-0 flex items-center"
        style={{ width: `${actions.length * actionWidth}px`, left: '100%' }}
      >
        {actions.map((action, i) => (
          <button
            key={i}
            onClick={action.onPress}
            className={`
              h-full flex flex-col items-center justify-center gap-1
              ${action.color}
            `}
            style={{ width: actionWidth }}
          >
            {action.icon}
            <span className="text-xs font-medium">{action.label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <div
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{ transform: `translateX(${translateX}px)` }}
        className="bg-white transition-transform duration-200"
      >
        {children}
      </div>
    </div>
  );
}

// Usage example
<MobileSwipeActions
  actions={[
    {
      icon: <ArchiveIcon className="w-5 h-5" />,
      label: 'Archive',
      color: 'bg-gray-500 text-white',
      onPress: () => console.log('Archive'),
    },
    {
      icon: <MessageIcon className="w-5 h-5" />,
      label: 'Message',
      color: 'bg-blue-500 text-white',
      onPress: () => console.log('Message'),
    },
  ]}
>
  <TripCard trip={trip} />
</MobileSwipeActions>
```

### PWA Configuration

```typescript
// public/manifest.json
{
  "name": "Travel Portal",
  "short_name": "Travel",
  "description": "Access your trips anywhere",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "orientation": "portrait",
  "scope": "/",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/maskable-icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "categories": ["travel", "business"],
  "shortcuts": [
    {
      "name": "My Trips",
      "short_name": "Trips",
      "description": "View your upcoming trips",
      "url": "/trips",
      "icons": [{ "src": "/icons/trips-shortcut.png", "sizes": "96x96" }]
    },
    {
      "name": "Documents",
      "short_name": "Docs",
      "description": "Access travel documents",
      "url": "/documents",
      "icons": [{ "src": "/icons/docs-shortcut.png", "sizes": "96x96" }]
    }
  ]
}
```

---

## Accessibility

### WCAG 2.1 Compliance

```typescript
// components/AccessibleTripCard.tsx
export function AccessibleTripCard({ trip }: { trip: CustomerTripView }) {
  return (
    <article
      aria-labelledby={`trip-${trip.id}-name`}
      aria-describedby={`trip-${trip.id}-status`}
    >
      {/* Trip Name - Heading for screen readers */}
      <h2 id={`trip-${trip.id}-name`} className="sr-only">
        Trip to {trip.destination.name}
      </h2>

      {/* Visual Card */}
      <Link
        href={`/trips/${trip.id}`}
        className="block group focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-2xl"
      >
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {/* Hero Image with Alt Text */}
          {trip.destination.heroImage && (
            <div className="relative h-48">
              <img
                src={trip.destination.heroImage}
                alt={`Scenic view of ${trip.destination.name}`}
                className="w-full h-full object-cover"
              />
              {/* Status - Accessible badge */}
              <div
                id={`trip-${trip.id}-status`}
                className="absolute top-3 right-3"
                role="status"
                aria-live="polite"
              >
                <TripStatusBadge status={trip.status} />
              </div>
            </div>
          )}

          {/* Trip Details */}
          <div className="p-4">
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-semibold">
                {trip.destination.name}
              </h3>
              <span className="text-gray-400" aria-hidden="true">•</span>
              <time dateTime={trip.departureDate}>
                {formatDate(trip.departureDate)}
              </time>
            </div>
            <p className="text-sm text-gray-600">
              {trip.travelers.length} {pluralize('traveler', trip.travelers.length)}
            </p>
          </div>
        </div>
      </Link>
    </article>
  );
}

// Accessible Button Component
export function AccessibleButton({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  loadingText = 'Loading...',
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        buttonVariants({ variant, size }),
        className
      )}
      aria-busy={loading}
      aria-disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <>
          <Spinner className="mr-2" aria-hidden="true" />
          <span className="sr-only">{loadingText}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}

// Accessible Form Component
export function AccessibleInput({
  label,
  error,
  hint,
  required,
  id,
  ...props
}: InputProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  const describedBy = [
    hint ? hintId : null,
    error ? errorId : null,
  ].filter(Boolean).join(' ');

  return (
    <div className="space-y-1">
      <label
        htmlFor={id}
        className="block text-sm font-medium text-gray-700"
      >
        {label}
        {required && (
          <span className="text-red-500" aria-label="required">
            *
          </span>
        )}
      </label>

      <input
        id={id}
        required={required}
        aria-invalid={!!error}
        aria-describedby={describedBy || undefined}
        className={cn(
          'block w-full rounded-md border-gray-300 shadow-sm',
          'focus:border-blue-500 focus:ring-blue-500',
          error && 'border-red-500 focus:border-red-500 focus:ring-red-500'
        )}
        {...props}
      />

      {hint && (
        <p id={hintId} className="text-sm text-gray-500">
          {hint}
        </p>
      )}

      {error && (
        <p id={errorId} className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
```

### Keyboard Navigation

```typescript
// hooks/useKeyboardNavigation.ts
export function useKeyboardNavigation(items: Array<{ id: string; ref: React.RefObject<HTMLElement> }>) {
  const [focusedIndex, setFocusedIndex] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          e.preventDefault();
          setFocusedIndex(i => Math.min(i + 1, items.length - 1));
          break;
        case 'ArrowUp':
        case 'ArrowLeft':
          e.preventDefault();
          setFocusedIndex(i => Math.max(i - 1, 0));
          break;
        case 'Home':
          e.preventDefault();
          setFocusedIndex(0);
          break;
        case 'End':
          e.preventDefault();
          setFocusedIndex(items.length - 1);
          break;
        case 'Enter':
        case ' ':
          e.preventDefault();
          items[focusedIndex].ref.current?.click();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [items, focusedIndex]);

  // Focus the current item
  useEffect(() => {
    items[focusedIndex]?.ref.current?.focus();
  }, [focusedIndex, items]);

  return { focusedIndex, setFocusedIndex };
}

// Usage in trip list
export function TripList({ trips }: { trips: CustomerTripView[] }) {
  const itemRefs = trips.map(() => useRef<HTMLAnchorElement>(null));
  const items = trips.map((trip, i) => ({ id: trip.id, ref: itemRefs[i] }));
  const { focusedIndex } = useKeyboardNavigation(items);

  return (
    <div role="listbox" aria-label="Your trips">
      {trips.map((trip, i) => (
        <Link
          key={trip.id}
          ref={itemRefs[i]}
          href={`/trips/${trip.id}`}
          role="option"
          aria-selected={i === focusedIndex}
          tabIndex={i === 0 ? 0 : -1}
          className={cn(
            'block p-4 rounded-lg',
            i === focusedIndex && 'ring-2 ring-blue-500'
          )}
        >
          <TripCard trip={trip} />
        </Link>
      ))}
    </div>
  );
}
```

### Screen Reader Announcements

```typescript
// components/Announcer.tsx
// Live region for screen reader announcements
export function Announcer() {
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    const handleAnnouncement = (e: CustomEvent<string>) => {
      setAnnouncement(e.detail);
      setTimeout(() => setAnnouncement(''), 1000);
    };

    window.addEventListener('announce', handleAnnouncement as EventListener);
    return () => window.removeEventListener('announce', handleAnnouncement as EventListener);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      aria-atomic="true"
      className="sr-only"
    >
      {announcement}
    </div>
  );
}

// Usage
const announce = (message: string) => {
  window.dispatchEvent(new CustomEvent('announce', { detail: message }));
};

// In components
announce('Trip status updated to Confirmed');
announce('Document downloaded');
announce('Message sent');
```

---

## Branding and White-Labeling

### Theme Configuration

```typescript
// styles/agency-theme.ts
interface AgencyTheme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
  };
  typography: {
    fontFamily: string;
    heading: {
      fontFamily?: string;
      fontWeight: number;
    };
    body: {
      fontSize: number;
      lineHeight: number;
    };
  };
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
  logo: {
    url: string;
    height: number;
    width?: number;
  };
}

export const defaultTheme: AgencyTheme = {
  colors: {
    primary: '#3b82f6',
    secondary: '#6366f1',
    accent: '#f59e0b',
    background: '#ffffff',
    surface: '#f9fafb',
    text: {
      primary: '#111827',
      secondary: '#6b7280',
      disabled: '#9ca3af',
    },
  },
  typography: {
    fontFamily: 'Inter, system-ui, sans-serif',
    heading: {
      fontWeight: 700,
    },
    body: {
      fontSize: 16,
      lineHeight: 1.5,
    },
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '1rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
  },
  logo: {
    url: '/logo.svg',
    height: 40,
  },
};

// Hook to use agency theme
export function useAgencyTheme() {
  const { data: agency } = useAgency();

  return useMemo(() => {
    if (!agency?.theme) return defaultTheme;

    // Merge agency theme with defaults
    return deepMerge(defaultTheme, agency.theme);
  }, [agency]);
}

// Apply theme to document
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useAgencyTheme();

  useEffect(() => {
    const root = document.documentElement;

    // Apply CSS variables
    root.style.setProperty('--color-primary', theme.colors.primary);
    root.style.setProperty('--color-secondary', theme.colors.secondary);
    root.style.setProperty('--color-accent', theme.colors.accent);
    root.style.setProperty('--color-background', theme.colors.background);
    root.style.setProperty('--color-surface', theme.colors.surface);
    root.style.setProperty('--color-text-primary', theme.colors.text.primary);
    root.style.setProperty('--color-text-secondary', theme.colors.text.secondary);

    root.style.setProperty('--font-family', theme.typography.fontFamily);
    root.style.setProperty('--border-radius-sm', theme.borderRadius.sm);
    root.style.setProperty('--border-radius-md', theme.borderRadius.md);
    root.style.setProperty('--border-radius-lg', theme.borderRadius.lg);
  }, [theme]);

  return <>{children}</>;
}
```

### Agency Logo Component

```typescript
// components/agency/AgencyLogo.tsx
export function AgencyLogo({ variant = 'full', className }: { variant?: 'full' | 'icon' | 'wordmark'; className?: string }) {
  const { agency } = useAgency();

  const logoUrl = agency?.logo?.url || '/default-logo.svg';
  const logoHeight = agency?.logo?.height || 40;

  if (variant === 'icon') {
    return (
      <img
        src={agency?.logo?.iconUrl || logoUrl}
        alt={agency?.name || 'Travel Agency'}
        className={className}
        height={32}
        width={32}
      />
    );
  }

  if (variant === 'wordmark') {
    return (
      <div className={className}>
        <span className="text-xl font-semibold" style={{ color: agency?.theme?.colors?.primary }}>
          {agency?.name || 'Travel Agency'}
        </span>
      </div>
    );
  }

  return (
    <img
      src={logoUrl}
      alt={agency?.name || 'Travel Agency'}
      className={className}
      height={logoHeight}
    />
  );
}
```

---

**Next:** [CUSTOMER_PORTAL_03_BUSINESS_VALUE_DEEP_DIVE](./CUSTOMER_PORTAL_03_BUSINESS_VALUE_DEEP_DIVE.md) — Customer retention and business value analysis
