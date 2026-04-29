# Customer Segmentation 03: Segment-Based Communication

> Communication cadence, channel preferences, language/tone by segment, and campaign automation

---

## Document Overview

**Focus:** Segment-driven communication strategy and automation
**Status:** Research Exploration
**Last Updated:** 2026-04-28

---

## Key Questions

### Communication Cadence
- How often should we communicate with each segment?
- What is the right cadence — high-touch for premium, automated for budget?
- How do we avoid over-communication while staying top-of-mind?
- What triggers override the default cadence?

### Channel Preferences
- What is the right channel mix for Indian travelers?
- Why WhatsApp-first for India? What are the constraints?
- When should we use email vs. WhatsApp vs. SMS?
- How do NRIs differ in channel preference?

### Message Tone & Language
- What tone is appropriate per segment?
- How do we handle Hinglish for young travelers, formal for corporate, regional languages for pilgrims?
- What about multilingual content management?
- How does tone affect conversion rates?

### Campaign Automation
- How do segment-based triggers drive campaigns?
- What are the key lifecycle triggers for each segment?
- How do we automate without losing the human touch?
- What are the campaign performance benchmarks?

---

## Research Areas

### A. Communication Cadence by Segment

**Cadence Matrix:**

| Segment | Service Model | Proactive Touches/Month | Reactive SLA | Example Touchpoints | Research Needed |
|---------|--------------|------------------------|--------------|---------------------|-----------------|
| **Platinum / Champions** | High-touch (dedicated agent) | 4-6 | < 30 min response | Monthly check-in, birthday, anniversary, exclusive previews | Platinum churn rate by touch frequency? |
| **Gold / Loyal** | Semi-personal | 2-3 | < 2 hour response | Trip suggestions, seasonal offers, booking anniversary | Gold upgrade conversion rate? |
| **Silver / Regular** | Automated + periodic personal | 1-2 | < 4 hour response | Seasonal campaigns, festival offers, trip reminders | Silver engagement rate? |
| **Bronze / Occasional** | Primarily automated | 1-2 | < 8 hour response | Festival deals, price drops, win-back sequences | Bronze reactivation rate? |
| **Prospect** | Automated nurture | 2-3 (initial burst) then 1 | < 4 hour response | Welcome series, destination guides, first-booking incentive | Prospect conversion timeline? |
| **Churned** | Win-back automated | 1 (declining) | Standard | Win-back offer, "we miss you", new feature announcement | Churn reactivation rate? |

**Cadence Rules:**

| Rule | Description | Research Needed |
|------|-------------|-----------------|
| **Max frequency cap** | No more than X messages per week per channel | Optimal cap by channel? |
| **Cooldown after purchase** | No promo for Y days after booking | Cooldown duration by segment? |
| **Engagement-based throttle** | Reduce frequency if low engagement | Engagement threshold definition? |
| **Festival override** | Increase frequency during festival seasons | Festival cadence multiplier? |
| **Do-not-disturb** | Respect DND hours and preferences | DND compliance in India? |
| **Preference-based** | Honor stated frequency preference | Preference collection rate? |

### B. Channel Preferences

**Channel Strategy Matrix:**

| Channel | Primary Use | Segment Fit | Constraint | Research Needed |
|---------|------------|-------------|------------|-----------------|
| **WhatsApp** | Primary communication in India | All Indian segments | Business API costs, template rules, 24-hour window | WhatsApp Business API pricing? |
| **Email** | Detailed itineraries, NRIs, marketing | Corporate, NRI, premium | Spam filters, deliverability | Email open rates by segment? |
| **SMS** | Transactional confirmations, OTPs | All segments | DND regulations, low engagement | SMS delivery rates in India? |
| **Phone call** | Complex bookings, high-value, complaints | Premium, corporate, pilgrim | Agent availability, cost | Call-to-conversion rate? |
| **In-app** | Self-service, trip management | Tech-savvy, adventure, NRI | Adoption rate, push notifications | App DAU by segment? |
| **Social media** | Awareness, inspiration, reviews | Young, adventure, honeymooner | Organic reach declining | Social-to-booking conversion? |

**WhatsApp-First Strategy for India:**

```
+-------------------------------------------------------+
|              WhatsApp Communication Flow               |
+-------------------------------------------------------+
|                                                         |
|  [Initial Contact]                                      |
|     |  "Hi! I'm your travel assistant at [Agency]"     |
|     v                                                   |
|  [Quick Menu]                                           |
|     |  1. Plan a trip                                   |
|     |  2. Check my booking                               |
|     |  3. Special offers                                 |
|     |  4. Talk to agent                                  |
|     v                                                   |
|  [Personalized Path]                                    |
|     |  Based on segment + history                        |
|     v                                                   |
|  [Rich Interaction]                                     |
|     |  Cards, images, quick replies, buttons            |
|     v                                                   |
|  [Handoff to Agent] if needed                           |
|     |  Full context passed seamlessly                    |
|     v                                                   |
|  [Follow-up]                                            |
|     |  Booking confirmation, itinerary, reminders        |
|                                                         |
+-------------------------------------------------------+
```

**Channel Selection by Interaction Type:**

| Interaction | Primary Channel | Fallback | Segment Override | Research Needed |
|-------------|----------------|----------|------------------|-----------------|
| **Trip inquiry** | WhatsApp | Phone | Corporate: Email | Channel preference accuracy? |
| **Quote delivery** | WhatsApp (card) | Email (PDF) | Premium: Phone call | Quote acceptance by channel? |
| **Booking confirmation** | WhatsApp + SMS | Email | All: WhatsApp | Confirmation delivery rate? |
| **Itinerary delivery** | WhatsApp + Email | In-app | All: Dual delivery | Itinerary open rate by channel? |
| **Payment reminder** | WhatsApp | SMS | — | Reminder-to-payment conversion? |
| **Travel alerts** | SMS + WhatsApp | Phone | Premium: Phone call | Alert delivery speed? |
| **Post-trip feedback** | WhatsApp | Email | — | Feedback response rate? |
| **Win-back offer** | Email | WhatsApp | Churned: Both channels | Win-back channel effectiveness? |
| **Festival promo** | WhatsApp | Email + SMS | Segment-dependent | Festival promo conversion by channel? |

### C. Message Tone & Language by Segment

**Tone Matrix:**

| Segment | Tone | Formality | Language | Example Greeting | Research Needed |
|---------|------|-----------|----------|-----------------|-----------------|
| **Budget Family** | Warm, helpful | Semi-formal | Hindi/Hinglish | "Sharma ji, aapke liye special summer offer hai!" | Hinglish comprehension rate? |
| **Luxury Honeymooner** | Elegant, aspirational | Formal | English | "Your dream honeymoon awaits — curated just for you" | English vs. Hinglish preference? |
| **Corporate Exec** | Professional, concise | Formal | English | "Hi Mr. Kapoor, your Bengaluru itinerary is ready" | Corporate language preference? |
| **Pilgrim** | Respectful, devotional | Formal | Hindi/Regional | "Prabhu ke saath aapki yatra sukhad ho" | Regional language support needed? |
| **Adventure Seeker** | Energetic, casual | Casual | Hinglish/English | "Hey! Ready for your next adventure? Ladakh calling!" | Casual tone conversion rate? |
| **NRI** | Warm, nostalgic | Semi-formal | English | "Welcome home! Plan your India visit with special NRI packages" | NRI nostalgia messaging effectiveness? |

**Language Distribution:**

| Language | Primary Regions | Segments | % of Customer Base (Est.) | Research Needed |
|----------|----------------|----------|--------------------------|-----------------|
| **Hindi** | North, Central | Budget Family, Pilgrim | 35-40% | Hindi message templates? |
| **Hinglish** | Pan-India (young) | Adventure, Young families | 25-30% | Hinglish tone guidelines? |
| **English** | Metro, Corporate | Corporate, Luxury, NRI | 20-25% | English variant (Indian/Global)? |
| **Tamil** | Tamil Nadu | Regional pilgrim, family | 5-8% | Tamil template availability? |
| **Telugu** | Andhra/Telangana | Regional pilgrim, family | 4-6% | Telugu template availability? |
| **Kannada** | Karnataka | Regional segments | 3-4% | Kannada template availability? |
| **Malayalam** | Kerala | Regional segments | 3-4% | Malayalam template availability? |
| **Bengali** | West Bengal | Regional family | 4-5% | Bengali template availability? |
| **Marathi** | Maharashtra | Regional family | 4-5% | Marathi template availability? |
| **Gujarati** | Gujarat | Business, family | 3-5% | Gujarati template availability? |

**Tone Guidelines:**

```
+-----------------------------------------------------------+
|                  TONE SPECTRUM                             |
+-----------------------------------------------------------+
|                                                           |
|  FORMAL              SEMI-FORMAL          CASUAL          |
|  |----------------------|-------------------|             |
|  |                      |                   |             |
|  Corporate  Pilgrim   Family   NRI    Adventure          |
|  Luxury                                    Honeymooner    |
|                                                           |
|  FEATURES BY TONE:                                        |
|                                                           |
|  FORMAL:                                                  |
|  - Use "Mr./Ms." + surname                               |
|  - Complete sentences                                     |
|  - Professional vocabulary                                |
|  - No emojis                                              |
|                                                           |
|  SEMI-FORMAL:                                             |
|  - First name or "ji" honorific                          |
|  - Conversational sentences                               |
|  - Warm vocabulary                                        |
|  - Selective emojis                                       |
|                                                           |
|  CASUAL:                                                  |
|  - First name only                                        |
|  - Short sentences, exclamation marks                     |
|  - Trendy vocabulary                                      |
|  - Generous emojis                                        |
|                                                           |
+-----------------------------------------------------------+
```

### D. Campaign Automation with Segment Triggers

**Lifecycle Triggers:**

| Trigger | Timing | Segment Target | Action | Channel | Research Needed |
|---------|--------|---------------|--------|---------|-----------------|
| **New inquiry** | Immediate | Prospect | Welcome message + agent assignment | WhatsApp | Welcome message conversion? |
| **First booking** | On confirmation | First-timer | Congratulations + what-to-expect | WhatsApp + Email | First-timer satisfaction? |
| **Trip completed** | Day after return | All | Feedback request + photo share prompt | WhatsApp | Feedback response rate? |
| **7 days post-trip** | After trip | First-timer | "Plan your next trip" + recommendation | WhatsApp | Repeat booking window? |
| **30 days post-trip** | After trip | All | Review request + referral ask | Email | Review/referral conversion? |
| **Booking anniversary** | 1 year from first booking | Loyal | Anniversary message + special offer | WhatsApp + Email | Anniversary campaign ROI? |
| **Birthday** | On date | All | Birthday greeting + travel gift voucher | WhatsApp | Birthday offer redemption? |
| **RFM score drop** | On re-evaluation | At-risk | Win-back campaign trigger | Segment-dependent | Win-back effectiveness? |
| **Inactivity 90 days** | After 90 days no interaction | Churned | Re-engagement sequence | Email + WhatsApp | Reactivation rate? |

**Festival Triggers:**

| Trigger | Timing | Segment Target | Campaign | Research Needed |
|---------|--------|---------------|----------|-----------------|
| **Summer vacation approaching** | 90 days before | BUD_FAM, families | Summer family package campaign | Booking lead time for summer? |
| **Diwali approaching** | 60 days before | All domestic | Diwali getaway packages | Diwali travel propensity? |
| **Wedding season starts** | 90 days before | LUX_HNY, families | Honeymoon + destination wedding | Honeymoon booking lead time? |
| **Pilgrimage season** | Per religious calendar | PIL_SPIR | Pilgrimage group bookings | Pilgrim booking advance time? |
| **Long weekend coming** | 30 days before | ADV_SEEK, young | Weekend getaway flash sale | Long weekend conversion rate? |
| **NRI homecoming season** | 120 days before | NRI_HOME | India visit early-bird packages | NRI booking lead time? |

**Automation Flow:**

```
[Trigger Event]
       |
       v
[Segment Check] -----> Customer in target segment?
       |                        |
       | Yes                    | No
       v                        v
[Consent Check]          [Skip or Log]
       |
       v
[Channel Preference Check]
       |
       v
[Tone & Language Lookup]
       |
       v
[Template Selection]
       |
       v
[Personalization Injection] ---> Dynamic blocks filled
       |
       v
[Frequency Cap Check] -----> Within limits?
       |                        |
       | Yes                    | No
       v                        v
[Send Message]            [Defer to next window]
       |
       v
[Track Delivery + Engagement]
       |
       v
[Update Engagement Score]
       |
       v
[Re-evaluate Segment if needed]
```

---

## Data Model Sketch

```typescript
// Research-level model — not final

interface CommunicationStrategy {
  strategyId: string;
  agencyId: string;
  segmentCode: string;

  // Cadence
  maxMessagesPerWeek: number;
  maxMessagesPerMonth: number;
  cooldownAfterBooking: number; // days
  preferredChannel: ChannelType;
  fallbackChannel: ChannelType;

  // Tone
  tone: CommunicationTone;
  language: CommunicationLanguage;
  formality: FormalityLevel;

  // Hours
  allowedHours: TimeWindow[];   // When messages can be sent
  timezone: string;

  // Service
  serviceModel: ServiceModel;
  responseSLA: number; // minutes
}

type CommunicationTone =
  | 'warm_helpful'       // Budget Family
  | 'elegant_aspirational' // Luxury Honeymooner
  | 'professional_concise' // Corporate Exec
  | 'respectful_devotional' // Pilgrim
  | 'energetic_casual'   // Adventure Seeker
  | 'warm_nostalgic';    // NRI

type CommunicationLanguage =
  | 'en'     // English
  | 'hi'     // Hindi
  | 'hinglish' // Hindi-English mix
  | 'ta'     // Tamil
  | 'te'     // Telugu
  | 'kn'     // Kannada
  | 'ml'     // Malayalam
  | 'bn'     // Bengali
  | 'mr'     // Marathi
  | 'gu';    // Gujarati

type FormalityLevel = 'formal' | 'semi_formal' | 'casual';

type ServiceModel =
  | 'dedicated_agent'    // Platinum/Premium
  | 'shared_agent'       // Gold
  | 'automated_plus_periodic' // Silver
  | 'primarily_automated' // Bronze
  | 'self_service';      // Prospect

interface TimeWindow {
  dayOfWeek: number; // 0-6
  startHour: number; // 0-23
  endHour: number;   // 0-23
}

// --- Campaign Automation ---

interface AutomatedCampaign {
  campaignId: string;
  agencyId: string;
  name: string;

  // Trigger
  trigger: CampaignTrigger;

  // Targeting
  targetSegments: string[];
  targetPersonas: string[];
  exclusionRules: ExclusionRule[];

  // Content
  steps: CampaignStep[];

  // Scheduling
  schedule?: CampaignSchedule;

  // Status
  status: CampaignStatus;
  metrics: CampaignMetrics;
}

interface CampaignTrigger {
  type: TriggerType;
  event?: string;
  delay?: number; // minutes after trigger
  conditions?: TriggerCondition[];
}

type TriggerType =
  | 'lifecycle_event'   // Booking, trip completion, etc.
  | 'festival'          // Indian festival calendar
  | 'rfm_change'        // RFM score crossed threshold
  | 'inactivity'        // No interaction for X days
  | 'segment_change'    // Customer changed segment
  | 'behavioral'        // Specific customer action
  | 'scheduled'         // Time-based (recurring)
  | 'manual';           // Agent-initiated

interface TriggerCondition {
  field: string;
  operator: string;
  value: any;
}

interface CampaignStep {
  stepId: string;
  order: number;

  // Channel
  channel: ChannelType;

  // Content
  templateId: string;
  dynamicBlocks: DynamicContentBlock[];

  // Timing
  delayFromPrevious: number; // minutes
  sendWindow?: TimeWindow;

  // Logic
  conditions?: StepCondition[]; // Conditional branching
  onPositive?: string; // Next step if engaged
  onNegative?: string; // Next step if not engaged

  // Tracking
  trackingEnabled: boolean;
}

interface DynamicContentBlock {
  blockName: string;
  field: string;
  fallback: string;
  segmentOverrides?: Record<string, string>;
  personaOverrides?: Record<string, string>;
}

interface ExclusionRule {
  type: 'already_received' | 'recently_booked' | 'do_not_disturb' | 'custom';
  campaignId?: string;
  daysSinceLastBooking?: number;
  customCondition?: TriggerCondition;
}

type CampaignStatus =
  | 'draft'
  | 'active'
  | 'paused'
  | 'completed'
  | 'archived';

interface CampaignMetrics {
  totalSent: number;
  totalDelivered: number;
  totalOpened: number;
  totalClicked: number;
  totalConverted: number; // Booking or desired action
  totalRevenue: number;

  openRate: number;
  clickRate: number;
  conversionRate: number;
  unsubscribeRate: number;

  bySegment: Record<string, SegmentMetrics>;
  byChannel: Record<string, ChannelMetrics>;
}

interface SegmentMetrics {
  segmentCode: string;
  sent: number;
  opened: number;
  clicked: number;
  converted: number;
  revenue: number;
}

// --- Message Template ---

interface MessageTemplate {
  templateId: string;
  agencyId: string;
  name: string;
  channel: ChannelType;

  // Content
  subject?: string;       // For email
  header?: string;        // For WhatsApp
  body: string;
  footer?: string;

  // Localization
  language: CommunicationLanguage;
  tone: CommunicationTone;
  formality: FormalityLevel;

  // Variables
  variables: TemplateVariable[];

  // WhatsApp-specific
  whatsappCategory?: 'utility' | 'marketing' | 'authentication';
  whatsappTemplateId?: string; // Meta-approved template ID

  // Version
  version: number;
  active: boolean;
}

interface TemplateVariable {
  name: string;
  type: 'text' | 'image' | 'date' | 'currency' | 'link';
  required: boolean;
  defaultValue?: string;
  personalizationSource?: string; // Field path from profile
}

// --- Communication Log ---

interface CommunicationLog {
  logId: string;
  customerId: string;
  agencyId: string;

  // Message
  campaignId?: string;
  stepId?: string;
  templateId: string;
  channel: ChannelType;

  // Content
  renderedContent: string;
  language: CommunicationLanguage;

  // Delivery
  status: DeliveryStatus;
  sentAt?: Date;
  deliveredAt?: Date;
  openedAt?: Date;
  clickedAt?: Date;

  // Context
  segmentCodeAtSend: string;
  personaCodeAtSend: string;
  personalizationLevel: ConsentLevel;

  // Engagement
  responseReceived?: boolean;
  responseContent?: string;
  ledToBooking?: boolean;
  bookingId?: string;
}

type DeliveryStatus =
  | 'queued'
  | 'sent'
  | 'delivered'
  | 'opened'
  | 'clicked'
  | 'bounced'
  | 'failed'
  | 'opted_out';
```

---

## Open Problems

### 1. WhatsApp Business API Limitations
**Challenge:** Template approval process, per-message costs, 24-hour conversation window

**Options:**
- Pre-approve templates for each segment and use case
- Use interactive messages for engagement within conversation window
- Hybrid approach: WhatsApp for engagement, SMS for transactional
- Budget for API costs in communication plan

**Research:** What is the cost-per-engagement for WhatsApp vs. SMS vs. email in India?

### 2. Regional Language Support at Scale
**Challenge:** Supporting 10+ Indian languages for content and templates

**Options:**
- Start with top 3-4 languages (Hindi, English, Tamil, Telugu)
- Use translation APIs with human review for quality
- Segment-based language preference with manual override
- Transliteration for Hinglish (Devanagari Hindi + English mix)

**Research:** What is the quality of machine translation for travel content in Indian languages?

### 3. DND (Do Not Disturb) Compliance
**Challenge:** India's TRAI DND regulations restrict promotional messaging

**Options:**
- Strict DND check before any promotional message
- Transactional vs. promotional classification for every message
- Consent-based communication preferences
- DND registry API integration

**Research:** How do travel agencies classify trip recommendations (transactional vs. promotional)?

### 4. Over-Communication Risk
**Challenge:** Multiple automated campaigns may overlap, causing message fatigue

**Options:**
- Global frequency cap across all campaigns
- Priority queue: only highest-priority message sent if cap reached
- Communication calendar for visual overlap detection
- Customer preference center for frequency control

**Research:** What is the unsubscribe rate by frequency level?

### 5. Tone Consistency Across Agents
**Challenge:** Different agents may use different tones with the same customer

**Options:**
- Agent-facing tone guidelines per segment
- AI-assisted message drafting with tone checking
- Template-based responses for common scenarios
- Agent training on segment-specific communication

**Research:** How much tone variation is acceptable vs. confusing?

### 6. Measuring Communication Effectiveness
**Challenge:** Attribution — did the WhatsApp message or the email drive the booking?

**Options:**
- Multi-touch attribution model
- Last-click attribution (simpler)
- Incremental testing (holdout groups)
- Customer-level attribution surveys

**Research:** Which attribution model works best for travel agency context?

---

## Next Steps

1. Map current agency communication channels and frequency
2. Design WhatsApp template library for top 10 use cases
3. Build segment-tone-language configuration matrix
4. Implement frequency cap service
5. Create communication calendar with festival overlay
6. Prototype automated campaign engine for lifecycle triggers
7. Design agent-facing tone guidelines document
8. Set up DND compliance check service
9. Build communication analytics dashboard
10. Test regional language message templates with focus groups

---

**Series:** [Customer Segmentation & Personalization](./SEGMENT_MASTER_INDEX.md)
**Previous:** [SEGMENT_02_PERSONALIZATION.md](./SEGMENT_02_PERSONALIZATION.md) — Personalization Engine
**Next:** [SEGMENT_04_RETENTION.md](./SEGMENT_04_RETENTION.md) — Customer Retention
