# Communication Hub — Technical Deep Dive

> Part 1 of 4 in Communication Hub Exploration Series

---

## Document Overview

**Series:** Communication Hub
**Part:** 1 — Technical Architecture
**Status:** Complete
**Last Updated:** 2026-04-24

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Channel Integration Layer](#channel-integration-layer)
4. [Unified Message Model](#unified-message-model)
5. [Message Orchestration](#message-orchestration)
6. [Real-Time Communication](#real-time-communication)
7. [Webhook Handling](#webhook-handling)
8. [Data Persistence](#data-persistence)
9. [Security Considerations](#security-considerations)
10. [API Specification](#api-specification)

---

## Executive Summary

The Communication Hub is a unified messaging system that orchestrates communication across multiple channels: WhatsApp, Email, SMS, and in-app messaging. It provides a single interface for agents to send messages, track delivery status, and maintain conversation history regardless of channel.

### Key Technical Capabilities

| Capability | Description |
|------------|-------------|
| **Multi-Channel** | WhatsApp Business API, SendGrid (Email), Twilio (SMS), In-App |
| **Unified Model** | Single message schema across all channels |
| **Orchestration** | Intelligent routing, fallback, and batching |
| **Real-Time** | WebSocket updates for live status |
| **Webhooks** | Event-driven inbound message processing |
| **Templates** | Dynamic, localized message templates |
| **Analytics** | Delivery rates, response times, engagement |

### Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     Communication Hub                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend: React + TypeScript + WebSocket Client               │
│  Backend: Node.js + Express + TypeScript                       │
│  Queue: BullMQ + Redis                                          │
│  Database: PostgreSQL + ClickHouse (analytics)                 │
│  Channels: WhatsApp API, SendGrid, Twilio, In-App              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Message      │  │ Template     │  │ Channel      │  │ Analytics    │   │
│  │ Composer     │  │ Manager      │  │ Selector     │  │ Dashboard    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │           │
│         └─────────────────┴─────────────────┴─────────────────┘           │
│                                    │                                        │
│                            ┌───────▼────────┐                               │
│                            │  WebSocket     │                               │
│                            │  Client        │                               │
│                            └───────┬────────┘                               │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                              API GATEWAY                                    │
│                              ┌──────▼──────┐                                │
│                              │   Express   │                                │
│                              │   Routes    │                                │
│                              └──────┬──────┘                                │
├────────────────────────────────────┼────────────────────────────────────────┤
│                              MESSAGE SERVICE                                │
│  ┌─────────────────────────────────┼─────────────────────────────────┐     │
│  │                                 │                                 │     │
│  │  ┌─────────────┐  ┌────────────┴────────────┐  ┌───────────────┐  │     │
│  │  │ Message     │  │   Orchestration         │  │ Template       │  │     │
│  │  │ Controller  │  │   Engine                │  │ Engine         │  │     │
│  │  └──────┬──────┘  └────────────┬────────────┘  └───────┬───────┘  │     │
│  │         │                       │                       │          │     │
│  └─────────┼───────────────────────┼───────────────────────┼──────────┘     │
│            │                       │                       │                │
├────────────┼───────────────────────┼───────────────────────┼────────────────┤
│            │               ┌───────▼────────┐      ┌───────▼────────┐      │
│            │               │   Message      │      │   Template     │      │
│            │               │   Queue        │      │   Cache        │      │
│            │               │   (BullMQ)     │      │   (Redis)      │      │
│            │               └───────┬────────┘      └────────────────┘      │
│            │                       │                                        │
├────────────┼───────────────────────┼────────────────────────────────────────┤
│            │               ┌───────▼────────────────────────────┐          │
│            │               │     CHANNEL ADAPTERS               │          │
│            │               │  ┌──────────┬──────────┬────────┐  │          │
│            │               │  │WhatsApp  │  Email   │  SMS   │  │          │
│            │               │  │ Adapter  │ Adapter  │Adapter │  │          │
│            │               │  └────┬─────┴────┬─────┴───┬────┘  │          │
│            │               │       │          │         │       │          │
│            │               └───────┼──────────┼─────────┼───────┘          │
├────────────┼───────────────────────┼──────────┼─────────┼────────────────┤
│            │                       │          │         │                │
│  ┌─────────▼─────────┐    ┌───────▼──┐ ┌───▼───┐ ┌──▼──────┐            │
│  │  PostgreSQL      │    │  WhatsApp│ │SendGrid│ │ Twilio  │            │
│  │  Messages Store  │    │  API     │ │  API   │ │  API    │            │
│  └───────────────────┘    └──────────┘ └───────┘ └─────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                         WEBHOOK HANDLERS                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ WhatsApp    │  │ Email       │  │ SMS         │  │ In-App      │       │
│  │ Webhook     │  │ Webhook     │  │ Webhook     │  │ Events      │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                        │
│                           ┌───────▼────────┐                               │
│                           │  Webhook       │                               │
│                           │  Processor     │                               │
│                           └───────┬────────┘                               │
└───────────────────────────────────┼────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────────┐
│                         ANALYTICS LAYER                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │ ClickHouse       │  │  Metrics         │  │  Real-Time       │         │
│  │ Event Store      │  │  Aggregation     │  │  Dashboard       │         │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
CommunicationHub
├── Frontend
│   ├── components/
│   │   ├── MessageComposer/
│   │   ├── ConversationView/
│   │   ├── ChannelSelector/
│   │   └── TemplateManager/
│   ├── hooks/
│   │   ├── useMessageSend.ts
│   │   ├── useConversation.ts
│   │   └── useRealtimeMessages.ts
│   └── services/
│       └── websocket.service.ts
│
├── Backend
│   ├── routes/
│   │   ├── messages.routes.ts
│   │   ├── conversations.routes.ts
│   │   ├── templates.routes.ts
│   │   └── webhooks.routes.ts
│   ├── services/
│   │   ├── message-service.ts
│   │   ├── orchestration-service.ts
│   │   └── template-service.ts
│   ├── channels/
│   │   ├── base-channel.adapter.ts
│   │   ├── whatsapp.adapter.ts
│   │   ├── email.adapter.ts
│   │   └── sms.adapter.ts
│   ├── queue/
│   │   ├── message.queue.ts
│   │   └── workers/
│   │       └── message.worker.ts
│   └── webhooks/
│       ├── webhook-handler.ts
│       └── verification.ts
│
└── Infrastructure
    ├── database/
    │   ├── migrations/
    │   └── seeds/
    └── analytics/
        └── clickhouse.ts
```

---

## Channel Integration Layer

### Channel Adapter Pattern

All channel integrations follow a common interface, enabling consistent message handling and easy addition of new channels.

```typescript
// channels/base-channel.adapter.ts

export interface MessagePayload {
  to: string;
  content: string;
  subject?: string;  // For email
  attachments?: Attachment[];
  metadata?: Record<string, unknown>;
}

export interface MessageDeliveryResult {
  success: boolean;
  messageId: string;
  channelMessageId?: string;
  status: MessageStatus;
  error?: string;
  cost?: number;
}

export interface ChannelConfig {
  enabled: boolean;
  priority: number;
  rateLimit?: {
    maxMessages: number;
    windowMs: number;
  };
  costPerMessage?: number;
}

export enum MessageStatus {
  QUEUED = 'queued',
  SENT = 'sent',
  DELIVERED = 'delivered',
  FAILED = 'failed',
  BOUNCED = 'bounced',
  READ = 'read'
}

/**
 * Base class for all channel adapters
 * Implements common functionality and defines the contract
 */
export abstract class BaseChannelAdapter {
  protected config: ChannelConfig;

  constructor(config: ChannelConfig) {
    this.config = config;
  }

  /**
   * Send a message through this channel
   */
  abstract send(payload: MessagePayload): Promise<MessageDeliveryResult>;

  /**
   * Check if this channel can handle the recipient
   */
  abstract canHandle(recipient: string): boolean;

  /**
   * Get channel-specific metadata
   */
  abstract getChannelMetadata(): {
    name: string;
    type: string;
    supportsAttachments: boolean;
    supportsTemplates: boolean;
    maxMessageLength: number;
  };

  /**
   * Validate message before sending
   */
  protected validatePayload(payload: MessagePayload): void {
    if (!payload.to || !payload.content) {
      throw new Error('Missing required fields: to, content');
    }

    const metadata = this.getChannelMetadata();
    if (payload.content.length > metadata.maxMessageLength) {
      throw new Error(
        `Message exceeds maximum length of ${metadata.maxMessageLength}`
      );
    }
  }

  /**
   * Apply rate limiting if configured
   */
  protected async checkRateLimit(recipient: string): Promise<boolean> {
    if (!this.config.rateLimit) return true;

    // Redis-based rate limiting implementation
    const key = `ratelimit:${this.constructor.name}:${recipient}`;
    const redis = getRedisClient();

    const current = await redis.incr(key);

    if (current === 1) {
      await redis.pexpire(key, this.config.rateLimit.windowMs);
    }

    return current <= this.config.rateLimit.maxMessages;
  }

  /**
   * Get estimated cost for sending message
   */
  getEstimatedCost(): number {
    return this.config.costPerMessage || 0;
  }
}
```

### WhatsApp Business API Adapter

```typescript
// channels/whatsapp.adapter.ts

import { BaseChannelAdapter, MessagePayload, MessageDeliveryResult } from './base-channel.adapter';
import axios from 'axios';

interface WhatsAppConfig {
  phoneNumberId: string;
  accessToken: string;
  businessAccountId: string;
  apiUrl: string;
  wabaId: string;
}

export class WhatsAppAdapter extends BaseChannelAdapter {
  private whatsappConfig: WhatsAppConfig;

  constructor(config: WhatsAppConfig & ChannelConfig) {
    super(config);
    this.whatsappConfig = {
      phoneNumberId: config.phoneNumberId,
      accessToken: config.accessToken,
      businessAccountId: config.businessAccountId,
      apiUrl: config.apiUrl || 'https://graph.facebook.com/v18.0',
      wabaId: config.wabaId
    };
  }

  async send(payload: MessagePayload): Promise<MessageDeliveryResult> {
    this.validatePayload(payload);

    const rateLimitOk = await this.checkRateLimit(payload.to);
    if (!rateLimitOk) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.QUEUED,
        error: 'Rate limit exceeded'
      };
    }

    try {
      const response = await axios.post(
        `${this.whatsappConfig.apiUrl}/${this.whatsappConfig.phoneNumberId}/messages`,
        {
          messaging_product: 'whatsapp',
          to: this.formatPhoneNumber(payload.to),
          type: 'text',
          text: {
            body: payload.content
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${this.whatsappConfig.accessToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return {
        success: true,
        messageId: response.data.messages[0].id,
        channelMessageId: response.data.messages[0].id,
        status: MessageStatus.SENT,
        cost: this.getEstimatedCost()
      };
    } catch (error) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      };
    }
  }

  canHandle(recipient: string): boolean {
    // Check if recipient has a WhatsApp number
    return this.isValidPhoneNumber(recipient) &&
           this.hasWhatsAppAccount(recipient);
  }

  getChannelMetadata() {
    return {
      name: 'WhatsApp',
      type: 'instant_messaging',
      supportsAttachments: true,
      supportsTemplates: true,
      maxMessageLength: 4096
    };
  }

  /**
   * Send template message (required for business-initiated conversations)
   */
  async sendTemplate(
    to: string,
    templateName: string,
    parameters: Record<string, string>
  ): Promise<MessageDeliveryResult> {
    try {
      const response = await axios.post(
        `${this.whatsappConfig.apiUrl}/${this.whatsappConfig.phoneNumberId}/messages`,
        {
          messaging_product: 'whatsapp',
          to: this.formatPhoneNumber(to),
          type: 'template',
          template: {
            name: templateName,
            language: { code: 'en' },
            components: [{
              type: 'body',
              parameters: Object.entries(parameters).map(([key, value]) => ({
                type: 'text',
                text: value
              }))
            }]
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${this.whatsappConfig.accessToken}`
          }
        }
      );

      return {
        success: true,
        messageId: response.data.messages[0].id,
        status: MessageStatus.SENT
      };
    } catch (error) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      };
    }
  }

  /**
   * Send media message (document, image, audio, video)
   */
  async sendMedia(
    to: string,
    mediaType: 'image' | 'document' | 'audio' | 'video',
    mediaUrl: string,
    caption?: string
  ): Promise<MessageDeliveryResult> {
    try {
      const response = await axios.post(
        `${this.whatsappConfig.apiUrl}/${this.whatsappConfig.phoneNumberId}/messages`,
        {
          messaging_product: 'whatsapp',
          to: this.formatPhoneNumber(to),
          type: mediaType,
          [mediaType]: {
            link: mediaUrl,
            caption: caption || ''
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${this.whatsappConfig.accessToken}`
          }
        }
      );

      return {
        success: true,
        messageId: response.data.messages[0].id,
        status: MessageStatus.SENT
      };
    } catch (error) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      };
    }
  }

  private formatPhoneNumber(phone: string): string {
    // Remove all non-numeric characters
    const cleaned = phone.replace(/\D/g, '');

    // Ensure country code is present
    if (!cleaned.startsWith('91')) { // India country code
      return `91${cleaned}`;
    }

    return cleaned;
  }

  private isValidPhoneNumber(phone: string): boolean {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 15;
  }

  private async hasWhatsAppAccount(phone: string): Promise<boolean> {
    // Check against our database of known WhatsApp users
    // This would be cached and updated via webhooks
    return true; // Simplified
  }

  private extractErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
      return error.response?.data?.error?.message || error.message;
    }
    return 'Unknown error';
  }
}
```

### Email Adapter (SendGrid)

```typescript
// channels/email.adapter.ts

import { BaseChannelAdapter, MessagePayload, MessageDeliveryResult } from './base-channel.adapter';
import sgMail from '@sendgrid/mail';

interface EmailConfig {
  apiKey: string;
  fromEmail: string;
  fromName: string;
  replyTo?: string;
}

export class EmailAdapter extends BaseChannelAdapter {
  private emailConfig: EmailConfig;

  constructor(config: EmailConfig & ChannelConfig) {
    super(config);
    this.emailConfig = {
      apiKey: config.apiKey,
      fromEmail: config.fromEmail,
      fromName: config.fromName,
      replyTo: config.replyTo
    };
    sgMail.setApiKey(this.emailConfig.apiKey);
  }

  async send(payload: MessagePayload): Promise<MessageDeliveryResult> {
    this.validatePayload(payload);

    if (!payload.subject) {
      throw new Error('Email requires a subject');
    }

    const rateLimitOk = await this.checkRateLimit(payload.to);
    if (!rateLimitOk) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.QUEUED,
        error: 'Rate limit exceeded'
      };
    }

    try {
      const msg = {
        to: payload.to,
        from: {
          email: this.emailConfig.fromEmail,
          name: this.emailConfig.fromName
        },
        replyTo: this.emailConfig.replyTo || this.emailConfig.fromEmail,
        subject: payload.subject,
        text: this.stripHtml(payload.content),
        html: payload.content,
        attachments: this.formatAttachments(payload.attachments || []),
        customArgs: {
          metadata: JSON.stringify(payload.metadata || {})
        },
        trackingSettings: {
          clickTracking: { enable: true },
          openTracking: { enable: true }
        }
      };

      const response = await sgMail.send(msg);

      return {
        success: true,
        messageId: response[0].headers['x-message-id'],
        channelMessageId: response[0].headers['x-message-id'],
        status: MessageStatus.SENT,
        cost: this.getEstimatedCost()
      };
    } catch (error) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      };
    }
  }

  canHandle(recipient: string): boolean {
    return this.isValidEmail(recipient);
  }

  getChannelMetadata() {
    return {
      name: 'Email',
      type: 'email',
      supportsAttachments: true,
      supportsTemplates: true,
      maxMessageLength: 1000000 // SendGrid limit
    };
  }

  /**
   * Send using SendGrid template
   */
  async sendTemplate(
    to: string,
    templateId: string,
    dynamicData: Record<string, unknown>,
    subject?: string
  ): Promise<MessageDeliveryResult> {
    try {
      const msg = {
        to,
        from: {
          email: this.emailConfig.fromEmail,
          name: this.emailConfig.fromName
        },
        templateId,
        dynamicTemplateData: dynamicData,
        subject,
        trackingSettings: {
          clickTracking: { enable: true },
          openTracking: { enable: true }
        }
      };

      const response = await sgMail.send(msg);

      return {
        success: true,
        messageId: response[0].headers['x-message-id'],
        status: MessageStatus.SENT
      };
    } catch (error) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      };
    }
  }

  /**
   * Send batch emails (up to 1000 at once)
   */
  async sendBatch(
    messages: Array<{ to: string; subject: string; content: string }>
  ): Promise<MessageDeliveryResult[]> {
    const batchMsgs = messages.map(msg => ({
      to: msg.to,
      from: {
        email: this.emailConfig.fromEmail,
        name: this.emailConfig.fromName
      },
      subject: msg.subject,
      html: msg.content
    }));

    try {
      await sgMail.send(batchMsgs);
      return messages.map(() => ({
        success: true,
        messageId: '',
        status: MessageStatus.SENT
      }));
    } catch (error) {
      return messages.map(() => ({
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      }));
    }
  }

  private isValidEmail(email: string): boolean {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  private stripHtml(html: string): string {
    return html.replace(/<[^>]*>/g, '');
  }

  private formatAttachments(attachments: Attachment[]): sgMail.Attachment[] {
    return attachments.map(att => ({
      content: att.content,
      filename: att.filename,
      type: att.contentType,
      disposition: 'attachment'
    }));
  }

  private extractErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    return 'Unknown error';
  }
}
```

### SMS Adapter (Twilio)

```typescript
// channels/sms.adapter.ts

import { BaseChannelAdapter, MessagePayload, MessageDeliveryResult } from './base-channel.adapter';
import twilio from 'twilio';

interface SMSConfig {
  accountSid: string;
  authToken: string;
  fromNumber: string;
}

export class SMSAdapter extends BaseChannelAdapter {
  private client: twilio.Twilio;
  private smsConfig: SMSConfig;

  constructor(config: SMSConfig & ChannelConfig) {
    super(config);
    this.smsConfig = {
      accountSid: config.accountSid,
      authToken: config.authToken,
      fromNumber: config.fromNumber
    };
    this.client = twilio(config.accountSid, config.authToken);
  }

  async send(payload: MessagePayload): Promise<MessageDeliveryResult> {
    this.validatePayload(payload);

    const rateLimitOk = await this.checkRateLimit(payload.to);
    if (!rateLimitOk) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.QUEUED,
        error: 'Rate limit exceeded'
      };
    }

    try {
      // Truncate if too long (SMS limit is 160 chars per segment)
      const content = payload.content.length > 160
        ? payload.content.substring(0, 157) + '...'
        : payload.content;

      const message = await this.client.messages.create({
        body: content,
        from: this.smsConfig.fromNumber,
        to: this.formatPhoneNumber(payload.to)
      });

      return {
        success: true,
        messageId: message.sid,
        channelMessageId: message.sid,
        status: this.mapTwilioStatus(message.status),
        cost: parseFloat(message.price || '0')
      };
    } catch (error) {
      return {
        success: false,
        messageId: '',
        status: MessageStatus.FAILED,
        error: this.extractErrorMessage(error)
      };
    }
  }

  canHandle(recipient: string): boolean {
    return this.isValidPhoneNumber(recipient);
  }

  getChannelMetadata() {
    return {
      name: 'SMS',
      type: 'sms',
      supportsAttachments: false,
      supportsTemplates: false,
      maxMessageLength: 160
    };
  }

  private formatPhoneNumber(phone: string): string {
    // Ensure E.164 format
    const cleaned = phone.replace(/\D/g, '');

    if (!cleaned.startsWith('+')) {
      return `+${cleaned}`;
    }

    return cleaned;
  }

  private isValidPhoneNumber(phone: string): boolean {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 15;
  }

  private mapTwilioStatus(status: string): MessageStatus {
    const statusMap: Record<string, MessageStatus> = {
      'queued': MessageStatus.QUEUED,
      'sent': MessageStatus.SENT,
      'delivered': MessageStatus.DELIVERED,
      'undelivered': MessageStatus.FAILED,
      'failed': MessageStatus.FAILED
    };
    return statusMap[status] || MessageStatus.QUEUED;
  }

  private extractErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    return 'Unknown error';
  }
}
```

---

## Unified Message Model

### Database Schema

```sql
-- migrations/XXX_create_messages_table.sql

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  trip_id UUID REFERENCES trips(id) ON DELETE SET NULL,

  -- Recipient information
  recipient_type VARCHAR(20) NOT NULL CHECK (recipient_type IN ('customer', 'agent', 'supplier')),
  recipient_id UUID NOT NULL,
  recipient_channel VARCHAR(50) NOT NULL, -- whatsapp, email, sms, in_app

  -- Message content
  subject VARCHAR(500),
  content TEXT NOT NULL,
  message_type VARCHAR(20) NOT NULL DEFAULT 'text' CHECK (message_type IN ('text', 'template', 'media')),
  template_id VARCHAR(255),

  -- Channel information
  channel VARCHAR(20) NOT NULL CHECK (channel IN ('whatsapp', 'email', 'sms', 'in_app')),
  channel_message_id VARCHAR(255), -- External message ID from channel API

  -- Direction and status
  direction VARCHAR(20) NOT NULL CHECK (direction IN ('outbound', 'inbound')),
  status VARCHAR(20) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'delivered', 'read', 'failed', 'bounced')),

  -- Delivery tracking
  sent_at TIMESTAMPTZ,
  delivered_at TIMESTAMPTZ,
  read_at TIMESTAMPTZ,
  failed_at TIMESTAMPTZ,
  error_message TEXT,

  -- Cost tracking
  cost_cents INTEGER DEFAULT 0,

  -- Thread management
  thread_id UUID,
  parent_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
  reply_to_message_id UUID REFERENCES messages(id) ON DELETE SET NULL,

  -- Metadata
  metadata JSONB DEFAULT '{}',
  attachments JSONB DEFAULT '[]',

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_messages_agency_trip ON messages(agency_id, trip_id);
CREATE INDEX idx_messages_recipient ON messages(recipient_type, recipient_id);
CREATE INDEX idx_messages_thread ON messages(thread_id) WHERE thread_id IS NOT NULL;
CREATE INDEX idx_messages_status ON messages(status) WHERE status IN ('queued', 'sent');
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);

-- Full-text search on content
CREATE INDEX idx_messages_content_fts ON messages USING gin(to_tsvector('english', content));

-- Thread table for conversation grouping
CREATE TABLE message_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  trip_id UUID REFERENCES trips(id) ON DELETE SET NULL,

  -- Thread participants
  participant_customer_id UUID,
  participant_agent_id UUID,

  -- Thread metadata
  channel VARCHAR(20) NOT NULL,
  subject VARCHAR(500),
  last_message_at TIMESTAMPTZ,
  message_count INTEGER DEFAULT 0,

  -- Status
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'closed')),

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_message_threads_agency ON message_threads(agency_id, last_message_at DESC);
CREATE INDEX idx_message_threads_trip ON message_threads(trip_id);

-- Template table
CREATE TABLE message_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_id UUID NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,

  -- Template identification
  name VARCHAR(255) NOT NULL,
  code VARCHAR(100) NOT NULL,
  category VARCHAR(100), -- booking, payment, itinerary, etc.

  -- Template content
  subject_template VARCHAR(500),
  content_template TEXT NOT NULL,

  -- Channel specificity
  channel VARCHAR(20) NOT NULL CHECK (channel IN ('whatsapp', 'email', 'sms', 'in_app')),

  -- Localization
  language VARCHAR(10) DEFAULT 'en',

  -- Template variables (for validation)
  variables JSONB DEFAULT '[]',

  -- Status
  is_active BOOLEAN DEFAULT true,
  version INTEGER DEFAULT 1,

  -- Timestamps
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(agency_id, code, language, version)
);

CREATE INDEX idx_message_templates_agency ON message_templates(agency_id, is_active);
```

### TypeScript Interfaces

```typescript
// types/message.types.ts

export interface Message {
  id: string;
  agencyId: string;
  tripId?: string;
  recipientType: RecipientType;
  recipientId: string;
  recipientChannel: string;
  subject?: string;
  content: string;
  messageType: MessageType;
  templateId?: string;
  channel: Channel;
  channelMessageId?: string;
  direction: MessageDirection;
  status: MessageStatus;
  sentAt?: Date;
  deliveredAt?: Date;
  readAt?: Date;
  failedAt?: Date;
  errorMessage?: string;
  costCents: number;
  threadId?: string;
  parentMessageId?: string;
  replyToMessageId?: string;
  metadata: Record<string, unknown>;
  attachments: MessageAttachment[];
  createdAt: Date;
  updatedAt: Date;
}

export enum RecipientType {
  CUSTOMER = 'customer',
  AGENT = 'agent',
  SUPPLIER = 'supplier'
}

export enum MessageType {
  TEXT = 'text',
  TEMPLATE = 'template',
  MEDIA = 'media'
}

export enum Channel {
  WHATSAPP = 'whatsapp',
  EMAIL = 'email',
  SMS = 'sms',
  IN_APP = 'in_app'
}

export enum MessageDirection {
  OUTBOUND = 'outbound',
  INBOUND = 'inbound'
}

export enum MessageStatus {
  QUEUED = 'queued',
  SENT = 'sent',
  DELIVERED = 'delivered',
  READ = 'read',
  FAILED = 'failed',
  BOUNCED = 'bounced'
}

export interface MessageAttachment {
  filename: string;
  contentType: string;
  size: number;
  url: string;
}

export interface MessageThread {
  id: string;
  agencyId: string;
  tripId?: string;
  participantCustomerId?: string;
  participantAgentId?: string;
  channel: Channel;
  subject?: string;
  lastMessageAt?: Date;
  messageCount: number;
  status: ThreadStatus;
  createdAt: Date;
  updatedAt: Date;
}

export enum ThreadStatus {
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  CLOSED = 'closed'
}

export interface MessageTemplate {
  id: string;
  agencyId: string;
  name: string;
  code: string;
  category?: string;
  subjectTemplate?: string;
  contentTemplate: string;
  channel: Channel;
  language: string;
  variables: TemplateVariable[];
  isActive: boolean;
  version: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'array';
  required: boolean;
  defaultValue?: unknown;
  description?: string;
}

export interface SendMessageRequest {
  recipientId: string;
  recipientType: RecipientType;
  channel?: Channel; // Auto-detect if not specified
  subject?: string;
  content: string;
  messageType?: MessageType;
  templateId?: string;
  templateVariables?: Record<string, unknown>;
  tripId?: string;
  threadId?: string;
  attachments?: MessageAttachment[];
  metadata?: Record<string, unknown>;
  scheduledFor?: Date;
}

export interface SendMessageResponse {
  messageId: string;
  status: MessageStatus;
  estimatedDelivery?: Date;
  cost?: number;
}

export interface MessageListFilters {
  tripId?: string;
  recipientId?: string;
  recipientType?: RecipientType;
  channel?: Channel;
  status?: MessageStatus;
  direction?: MessageDirection;
  threadId?: string;
  startDate?: Date;
  endDate?: Date;
  search?: string;
}

export interface MessageAnalytics {
  totalSent: number;
  totalDelivered: number;
  totalFailed: number;
  deliveryRate: number;
  averageDeliveryTime: number; // seconds
  totalCost: number;
  byChannel: Record<Channel, ChannelAnalytics>;
  byDate: Array<{
    date: string;
    sent: number;
    delivered: number;
    failed: number;
  }>;
}

export interface ChannelAnalytics {
  sent: number;
  delivered: number;
  failed: number;
  deliveryRate: number;
  averageCost: number;
}
```

---

## Message Orchestration

### Orchestration Service

```typescript
// services/orchestration-service.ts

import { BaseChannelAdapter } from '../channels/base-channel.adapter';
import { WhatsAppAdapter } from '../channels/whatsapp.adapter';
import { EmailAdapter } from '../channels/email.adapter';
import { SMSAdapter } from '../channels/sms.adapter';
import { InAppAdapter } from '../channels/in-app.adapter';
import {
  SendMessageRequest,
  Message,
  Channel,
  MessageStatus,
  RecipientType
} from '../types/message.types';
import { messageQueue } from '../queue/message.queue';
import { db } from '../database';

export class OrchestrationService {
  private channels: Map<Channel, BaseChannelAdapter>;
  private channelPreferences: Map<string, Channel[]>;

  constructor() {
    this.channels = new Map();
    this.channelPreferences = new Map();
    this.initializeChannels();
  }

  private initializeChannels(): void {
    // Initialize channel adapters with their configs
    this.channels.set(
      Channel.WHATSAPP,
      new WhatsAppAdapter({
        enabled: true,
        priority: 1,
        costPerMessage: 0.005,
        phoneNumberId: process.env.WHATSAPP_PHONE_ID!,
        accessToken: process.env.WHATSAPP_ACCESS_TOKEN!,
        businessAccountId: process.env.WHATSAPP_BUSINESS_ID!,
        wabaId: process.env.WHATSAPP_WABA_ID!
      })
    );

    this.channels.set(
      Channel.EMAIL,
      new EmailAdapter({
        enabled: true,
        priority: 2,
        costPerMessage: 0.001,
        apiKey: process.env.SENDGRID_API_KEY!,
        fromEmail: process.env.EMAIL_FROM!,
        fromName: process.env.EMAIL_FROM_NAME!
      })
    );

    this.channels.set(
      Channel.SMS,
      new SMSAdapter({
        enabled: true,
        priority: 3,
        costPerMessage: 0.05,
        accountSid: process.env.TWILIO_ACCOUNT_SID!,
        authToken: process.env.TWILIO_AUTH_TOKEN!,
        fromNumber: process.env.TWILIO_FROM_NUMBER!
      })
    );

    this.channels.set(
      Channel.IN_APP,
      new InAppAdapter({
        enabled: true,
        priority: 0 // Highest priority (free)
      })
    );
  }

  /**
   * Send a message with intelligent channel selection
   */
  async sendMessage(request: SendMessageRequest): Promise<Message> {
    // 1. Determine best channel
    const channel = request.channel || await this.selectBestChannel(request);

    // 2. Get channel adapter
    const adapter = this.channels.get(channel);
    if (!adapter || !this.isChannelEnabled(adapter)) {
      throw new Error(`Channel ${channel} is not available`);
    }

    // 3. Create message record
    const message = await this.createMessageRecord(request, channel);

    // 4. Process template if needed
    let content = request.content;
    let subject = request.subject;

    if (request.templateId) {
      const rendered = await this.renderTemplate(
        request.templateId,
        request.templateVariables || {}
      );
      content = rendered.content;
      subject = rendered.subject;
    }

    // 5. Add to queue for delivery
    await messageQueue.add('send-message', {
      messageId: message.id,
      recipient: await this.getRecipientAddress(request.recipientId, channel),
      content,
      subject,
      attachments: request.attachments,
      channel,
      metadata: request.metadata
    }, {
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 2000
      },
      delay: request.scheduledFor
        ? Math.max(0, request.scheduledFor.getTime() - Date.now())
        : 0
    });

    return message;
  }

  /**
   * Send bulk messages
   */
  async sendBulkMessages(
    requests: SendMessageRequest[]
  ): Promise<{ success: number; failed: number; messageIds: string[] }> {
    const results = await Promise.allSettled(
      requests.map(req => this.sendMessage(req))
    );

    const success = results.filter(r => r.status === 'fulfilled').length;
    const failed = results.filter(r => r.status === 'rejected').length;
    const messageIds = results
      .filter((r): r is PromiseFulfilledResult<Message> => r.status === 'fulfilled')
      .map(r => r.value.id);

    return { success, failed, messageIds };
  }

  /**
   * Select best channel based on recipient preferences and message type
   */
  private async selectBestChannel(request: SendMessageRequest): Promise<Channel> {
    const { recipientId, recipientType } = request;

    // Check recipient's channel preferences
    const preferences = await this.getRecipientChannelPreferences(recipientId, recipientType);

    // Filter to enabled channels
    const availablePreferences = preferences.filter(ch => {
      const adapter = this.channels.get(ch);
      return adapter && this.isChannelEnabled(adapter);
    });

    if (availablePreferences.length > 0) {
      return availablePreferences[0]; // Return most preferred
    }

    // Default to WhatsApp for customers, Email for agents/suppliers
    if (recipientType === RecipientType.CUSTOMER) {
      return Channel.WHATSAPP;
    }

    return Channel.EMAIL;
  }

  /**
   * Get recipient's channel preferences
   */
  private async getRecipientChannelPreferences(
    recipientId: string,
    recipientType: RecipientType
  ): Promise<Channel[]> {
    const cacheKey = `channel_prefs:${recipientType}:${recipientId}`;

    // Check cache
    const cached = await this.channelPreferences.get(cacheKey);
    if (cached) {
      return cached;
    }

    // Query database
    const result = await db.query(`
      SELECT channel_preferences
      FROM ${recipientType}s
      WHERE id = $1
    `, [recipientId]);

    const preferences = result.rows[0]?.channel_preferences || [];

    return preferences;
  }

  /**
   * Get recipient's address for specific channel
   */
  private async getRecipientAddress(
    recipientId: string,
    channel: Channel
  ): Promise<string> {
    switch (channel) {
      case Channel.WHATSAPP:
      case Channel.SMS:
        // Get phone number
        const phoneResult = await db.query(`
          SELECT phone_number FROM customers WHERE id = $1
          UNION
          SELECT phone_number FROM agents WHERE id = $1
        `, [recipientId]);
        return phoneResult.rows[0]?.phone_number || '';

      case Channel.EMAIL:
        // Get email
        const emailResult = await db.query(`
          SELECT email FROM customers WHERE id = $1
          UNION
          SELECT email FROM agents WHERE id = $1
        `, [recipientId]);
        return emailResult.rows[0]?.email || '';

      case Channel.IN_APP:
        return recipientId; // In-app uses user ID
    }
  }

  /**
   * Create message record in database
   */
  private async createMessageRecord(
    request: SendMessageRequest,
    channel: Channel
  ): Promise<Message> {
    const result = await db.query(`
      INSERT INTO messages (
        agency_id,
        trip_id,
        recipient_type,
        recipient_id,
        recipient_channel,
        subject,
        content,
        message_type,
        template_id,
        channel,
        direction,
        status,
        thread_id,
        metadata,
        attachments
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
      )
      RETURNING *
    `, [
      request.agencyId, // Would be extracted from context
      request.tripId,
      request.recipientType,
      request.recipientId,
      channel,
      request.subject,
      request.content,
      request.messageType || 'text',
      request.templateId,
      channel,
      'outbound',
      MessageStatus.QUEUED,
      request.threadId,
      JSON.stringify(request.metadata || {}),
      JSON.stringify(request.attachments || [])
    ]);

    return result.rows[0];
  }

  /**
   * Render template with variables
   */
  private async renderTemplate(
    templateId: string,
    variables: Record<string, unknown>
  ): Promise<{ subject?: string; content: string }> {
    const result = await db.query(`
      SELECT subject_template, content_template, variables
      FROM message_templates
      WHERE id = $1 AND is_active = true
    `, [templateId]);

    if (result.rows.length === 0) {
      throw new Error(`Template ${templateId} not found`);
    }

    const template = result.rows[0];

    // Validate required variables
    const requiredVars = (template.variables as TemplateVariable[])
      .filter(v => v.required)
      .map(v => v.name);

    for (const required of requiredVars) {
      if (!(required in variables)) {
        throw new Error(`Missing required variable: ${required}`);
      }
    }

    // Render using simple template engine
    const render = (str: string) => {
      return str.replace(/\{\{(\w+)\}\}/g, (_, key) => {
        return String(variables[key] || '');
      });
    };

    return {
      subject: template.subject_template ? render(template.subject_template) : undefined,
      content: render(template.content_template)
    };
  }

  /**
   * Check if channel adapter is enabled
   */
  private isChannelEnabled(adapter: BaseChannelAdapter): boolean {
    return adapter['config']?.enabled === true;
  }

  /**
   * Send with fallback to next best channel
   */
  async sendMessageWithFallback(
    request: SendMessageRequest,
    attemptedChannels: Set<Channel> = new Set()
  ): Promise<Message> {
    const channel = await this.selectBestChannel(request);

    if (attemptedChannels.has(channel)) {
      // All channels attempted, fail
      throw new Error('All available channels failed');
    }

    attemptedChannels.add(channel);

    try {
      return await this.sendMessage({ ...request, channel });
    } catch (error) {
      // Try next channel
      return await this.sendMessageWithFallback(request, attemptedChannels);
    }
  }

  /**
   * Update message status from webhook
   */
  async updateMessageStatus(
    channelMessageId: string,
    status: MessageStatus,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    await db.query(`
      UPDATE messages
      SET
        status = $1,
        ${status === MessageStatus.DELIVERED ? 'delivered_at = NOW()' : ''}
        ${status === MessageStatus.READ ? 'read_at = NOW()' : ''}
        ${status === MessageStatus.FAILED ? 'failed_at = NOW()' : ''},
        metadata = COALESCE(metadata, '{}') || $2::jsonb,
        updated_at = NOW()
      WHERE channel_message_id = $3
    `, [status, JSON.stringify(metadata || {}), channelMessageId]);
  }
}
```

### Message Queue and Workers

```typescript
// queue/message.queue.ts

import { Queue, Worker, Job } from 'bullmq';
import { Redis } from 'ioredis';
import { OrchestrationService } from '../services/orchestration-service';

const connection = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  maxRetriesPerRequest: null
});

export const messageQueue = new Queue('messages', {
  connection,
  defaultJobOptions: {
    removeOnComplete: 1000,
    removeOnFail: 5000
  }
});

export interface SendMessageJob {
  messageId: string;
  recipient: string;
  content: string;
  subject?: string;
  attachments?: any[];
  channel: Channel;
  metadata?: Record<string, unknown>;
}

// Worker for processing messages
const worker = new Worker(
  'messages',
  async (job: Job<SendMessageJob>) => {
    const { messageId, recipient, content, subject, attachments, channel, metadata } = job.data;

    const orchestration = new OrchestrationService();
    const adapter = orchestration['channels'].get(channel);

    if (!adapter) {
      throw new Error(`No adapter found for channel: ${channel}`);
    }

    // Send through channel
    const result = await adapter.send({
      to: recipient,
      content,
      subject,
      attachments,
      metadata
    });

    // Update message status
    await orchestration.updateMessageStatus(
      messageId,
      result.status,
      { channelMessageId: result.channelMessageId }
    );

    return result;
  },
  {
    connection,
    concurrency: 10,
    limiter: {
      max: 100, // Max 100 jobs per interval
      duration: 1000 // 1 second
    }
  }
);

worker.on('completed', (job) => {
  console.log(`Message ${job.data.messageId} sent successfully`);
});

worker.on('failed', (job, err) => {
  console.error(`Message ${job?.data.messageId} failed:`, err);
});

// Schedule queue for delayed/scheduled messages
export const scheduleQueue = new Queue('scheduled-messages', {
  connection
});

// Worker to move scheduled messages to main queue
new Worker('scheduled-messages', async (job) => {
  await messageQueue.add('send-message', job.data);
}, { connection });
```

---

## Real-Time Communication

### WebSocket Server

```typescript
// websocket/message-websocket.server.ts

import WebSocket, { WebSocketServer } from 'ws';
import jwt from 'jsonwebtoken';
import { Redis } from 'ioredis';

interface WSClient {
  ws: WebSocket;
  userId: string;
  agencyId: string;
  subscriptions: Set<string>;
}

export class MessageWebSocketServer {
  private wss: WebSocketServer;
  private clients: Map<string, WSClient> = new Map();
  private redis: Redis;
  private redisSubscriber: Redis;

  constructor(port: number) {
    this.wss = new WebSocketServer({ port });
    this.redis = new Redis();
    this.redisSubscriber = new Redis();

    this.setupRedisPubSub();
    this.setupWebSocketServer();
  }

  private setupWebSocketServer(): void {
    this.wss.on('connection', (ws: WebSocket, req) => {
      // Authenticate via token
      const token = this.extractToken(req);

      try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET!) as {
          userId: string;
          agencyId: string;
        };

        const clientId = `${decoded.agencyId}:${decoded.userId}`;

        const client: WSClient = {
          ws,
          userId: decoded.userId,
          agencyId: decoded.agencyId,
          subscriptions: new Set()
        };

        this.clients.set(clientId, client);

        // Send initial connection success
        this.send(client, {
          type: 'connected',
          data: { clientId }
        });

        // Handle incoming messages
        ws.on('message', async (data) => {
          try {
            const message = JSON.parse(data.toString());
            await this.handleClientMessage(client, message);
          } catch (error) {
            this.sendError(client, 'Invalid message format');
          }
        });

        // Handle disconnect
        ws.on('close', () => {
          this.clients.delete(clientId);
          // Unsubscribe from Redis
          client.subscriptions.forEach(sub => {
            this.redisSubscriber.unsubscribe(sub);
          });
        });

      } catch (error) {
        ws.close();
      }
    });
  }

  private setupRedisPubSub(): void {
    // Subscribe to message events
    this.redisSubscriber.subscribe('message:created', 'message:updated');

    this.redisSubscriber.on('message', (channel, message) => {
      const event = JSON.parse(message);

      // Broadcast to relevant clients
      this.broadcastToAgency(event.agencyId, {
        type: channel,
        data: event
      });
    });
  }

  private async handleClientMessage(
    client: WSClient,
    message: { type: string; data?: unknown }
  ): Promise<void> {
    switch (message.type) {
      case 'subscribe':
        // Subscribe to specific trip/thread
        const { tripId, threadId } = message.data as { tripId?: string; threadId?: string };

        if (tripId) {
          const channel = `trip:${tripId}`;
          client.subscriptions.add(channel);
          await this.redisSubscriber.subscribe(channel);
        }

        if (threadId) {
          const channel = `thread:${threadId}`;
          client.subscriptions.add(channel);
          await this.redisSubscriber.subscribe(channel);
        }

        this.send(client, {
          type: 'subscribed',
          data: { tripId, threadId }
        });
        break;

      case 'unsubscribe':
        const unsubTrip = (message.data as any).tripId;
        const unsubThread = (message.data as any).threadId;

        if (unsubTrip) {
          const channel = `trip:${unsubTrip}`;
          client.subscriptions.delete(channel);
          await this.redisSubscriber.unsubscribe(channel);
        }

        if (unsubThread) {
          const channel = `thread:${unsubThread}`;
          client.subscriptions.delete(channel);
          await this.redisSubscriber.unsubscribe(channel);
        }
        break;

      case 'ping':
        this.send(client, { type: 'pong' });
        break;

      default:
        this.sendError(client, 'Unknown message type');
    }
  }

  /**
   * Broadcast message to all clients in an agency
   */
  private broadcastToAgency(agencyId: string, message: unknown): void {
    for (const [clientId, client] of this.clients) {
      if (client.agencyId === agencyId) {
        this.send(client, message);
      }
    }
  }

  /**
   * Send message to specific client
   */
  private send(client: WSClient, message: unknown): void {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(JSON.stringify(message));
    }
  }

  private sendError(client: WSClient, error: string): void {
    this.send(client, {
      type: 'error',
      data: { error }
    });
  }

  private extractToken(req: any): string {
    return req.url?.split('token=')[1] || '';
  }

  /**
   * Publish message event to Redis
   */
  async publishMessageEvent(event: {
    type: string;
    agencyId: string;
    data: unknown;
  }): Promise<void> {
    await this.redis.publish(event.type, JSON.stringify(event));
  }
}
```

### Client-Side WebSocket Hook

```typescript
// frontend/hooks/useRealtimeMessages.ts

import { useEffect, useState, useCallback } from 'react';
import { Message, MessageStatus } from '../types/message.types';

interface MessageEvent {
  type: 'message:created' | 'message:updated' | 'message:delivered' | 'message:read';
  data: Message;
}

interface UseRealtimeMessagesOptions {
  tripId?: string;
  threadId?: string;
  onNewMessage?: (message: Message) => void;
  onMessageUpdate?: (message: Message) => void;
}

export function useRealtimeMessages(options: UseRealtimeMessagesOptions = {}) {
  const [connected, setConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const wsUrl = `${process.env.WS_URL}/messages?token=${token}`;

    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      setConnected(true);

      // Subscribe to trip/thread
      const subscriptions: any = {};
      if (options.tripId) subscriptions.tripId = options.tripId;
      if (options.threadId) subscriptions.threadId = options.threadId;

      if (Object.keys(subscriptions).length > 0) {
        websocket.send(JSON.stringify({
          type: 'subscribe',
          data: subscriptions
        }));
      }
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data) as MessageEvent;

      switch (message.type) {
        case 'message:created':
          options.onNewMessage?.(message.data);
          break;

        case 'message:updated':
          options.onMessageUpdate?.(message.data);
          break;

        case 'connected':
          console.log('WebSocket connected:', message.data);
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    };

    websocket.onclose = () => {
      setConnected(false);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    setWs(websocket);

    // Ping to keep connection alive
    const pingInterval = setInterval(() => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      websocket.close();
    };
  }, [options.tripId, options.threadId]);

  const sendMessage = useCallback((content: string, recipientId: string) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'send_message',
        data: { content, recipientId }
      }));
    }
  }, [ws]);

  return {
    connected,
    sendMessage
  };
}
```

---

## Webhook Handling

### Webhook Handler

```typescript
// webhooks/webhook-handler.ts

import express from 'express';
import crypto from 'crypto';
import { OrchestrationService } from '../services/orchestration-service';

const router = express.Router();
const orchestration = new OrchestrationService();

/**
 * Verify webhook signature for security
 */
function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload);
  const digest = hmac.digest('base64');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
}

/**
 * WhatsApp webhook handler
 */
router.post('/whatsapp', express.raw({ type: 'application/json' }), async (req, res) => {
  const signature = req.headers['x-hub-signature-256'] as string;

  // Verify webhook
  if (!verifyWebhookSignature(
    req.body,
    signature,
    process.env.WHATSAPP_APP_SECRET!
  )) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const body = JSON.parse(req.body.toString());

  try {
    // Handle different webhook types
    for (const entry of body.entry || []) {
      for (const change of entry.changes || []) {
        await handleWhatsAppChange(change);
      }
    }

    res.status(200).send('OK');
  } catch (error) {
    console.error('WhatsApp webhook error:', error);
    res.status(500).send('ERROR');
  }
});

async function handleWhatsAppChange(change: any): Promise<void> {
  const value = change.value;

  // Handle messages
  if (value.messages) {
    for (const message of value.messages) {
      await handleWhatsAppMessage(message, value.metadata);
    }
  }

  // Handle message status updates
  if (value.statuses) {
    for (const status of value.statuses) {
      await handleWhatsAppStatus(status);
    }
  }
}

async function handleWhatsAppMessage(message: any, metadata: any): Promise<void> {
  const { from, id, timestamp, type } = message;

  // Get conversation info
  const conversation = await db.query(`
    SELECT customer_id, trip_id, agency_id
    FROM conversations
    WHERE whatsapp_number = $1
    ORDER BY created_at DESC
    LIMIT 1
  `, [from]);

  if (conversation.rows.length === 0) {
    // Unknown number - could create new conversation
    return;
  }

  const { customer_id, trip_id, agency_id } = conversation.rows[0];

  // Extract content based on type
  let content = '';
  let attachments = [];

  switch (type) {
    case 'text':
      content = message.text.body;
      break;

    case 'image':
      content = message.image.caption || '';
      attachments.push({
        type: 'image',
        url: message.image.url,
        mime_type: 'image/jpeg'
      });
      break;

    case 'document':
      content = message.document.caption || '';
      attachments.push({
        type: 'document',
        url: message.document.url,
        filename: message.document.filename,
        mime_type: message.document.mime_type
      });
      break;

    case 'audio':
      attachments.push({
        type: 'audio',
        url: message.audio.url,
        mime_type: message.audio.mime_type
      });
      break;
  }

  // Create inbound message record
  await db.query(`
    INSERT INTO messages (
      agency_id,
      trip_id,
      recipient_type,
      recipient_id,
      recipient_channel,
      content,
      message_type,
      channel,
      channel_message_id,
      direction,
      status,
      sent_at,
      attachments,
      metadata
    ) VALUES (
      $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
    )
  `, [
    agency_id,
    trip_id,
    'customer',
    customer_id,
    'whatsapp',
    content,
    type === 'text' ? 'text' : 'media',
    'whatsapp',
    id,
    'inbound',
    'delivered',
    new Date(parseInt(timestamp) * 1000),
    JSON.stringify(attachments),
    JSON.stringify({ metadata })
  ]);

  // Publish real-time update
  await orchestration['redis']?.publish('message:created', JSON.stringify({
    agencyId: agency_id,
    tripId: trip_id,
    customerId: customer_id
  }));
}

async function handleWhatsAppStatus(status: any): Promise<void> {
  const { id, status: statusValue, timestamp } = status;

  // Map WhatsApp status to our status
  const statusMap: Record<string, MessageStatus> = {
    'sent': MessageStatus.SENT,
    'delivered': MessageStatus.DELIVERED,
    'read': MessageStatus.READ,
    'failed': MessageStatus.FAILED
  };

  await orchestration.updateMessageStatus(
    id,
    statusMap[statusValue] || MessageStatus.SENT,
    { whatsappStatus: statusValue }
  );
}

/**
 * SendGrid webhook handler (email events)
 */
router.post('/email', async (req, res) => {
  const signature = req.headers['x-twilio-email-event-webhook-signature'] as string;
  const timestamp = req.headers['x-twilio-email-event-webhook-timestamp'] as string;

  // Verify SendGrid signature
  const payload = timestamp + req.body;
  const expectedSignature = crypto
    .createHmac('sha256', process.env.SENDGRID_WEBHOOK_SECRET!)
    .update(payload)
    .digest('base64');

  if (signature !== expectedSignature) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const events = req.body;

  try {
    for (const event of events) {
      await handleEmailEvent(event);
    }

    res.status(200).send('OK');
  } catch (error) {
    console.error('Email webhook error:', error);
    res.status(500).send('ERROR');
  }
});

async function handleEmailEvent(event: any): Promise<void> {
  const { sg_message_id, event: eventType, timestamp } = event;

  // Map SendGrid events to our status
  const statusMap: Record<string, MessageStatus> = {
    'delivered': MessageStatus.DELIVERED,
    'open': MessageStatus.READ,
    'click': MessageStatus.READ,
    'bounce': MessageStatus.BOUNCED,
    'dropped': MessageStatus.FAILED,
    'spamreport': MessageStatus.FAILED
  };

  const status = statusMap[eventType];
  if (status) {
    await orchestration.updateMessageStatus(
      sg_message_id,
      status,
      { emailEvent: eventType }
    );
  }
}

/**
 * Twilio webhook handler (SMS events)
 */
router.post('/sms', async (req, res) => {
  const signature = req.headers['x-twilio-signature'] as string;
  const url = `${req.protocol}://${req.headers.host}${req.originalUrl}`;

  // Verify Twilio signature
  const expectedSignature = crypto
    .createHmac('sha1', process.env.TWILIO_AUTH_TOKEN!)
    .update(Buffer.from(url, 'utf-8'))
    .digest('base64');

  if (signature !== expectedSignature) {
    return res.status(401).send('Invalid signature');
  }

  const { MessageSid, MessageStatus, From, To, Body } = req.body;

  try {
    // Handle status callback
    if (MessageStatus) {
      const statusMap: Record<string, MessageStatus> = {
        'queued': MessageStatus.QUEUED,
        'sent': MessageStatus.SENT,
        'delivered': MessageStatus.DELIVERED,
        'undelivered': MessageStatus.FAILED,
        'failed': MessageStatus.FAILED
      };

      await orchestration.updateMessageStatus(
        MessageSid,
        statusMap[MessageStatus] || MessageStatus.QUEUED
      );
    }

    // Handle incoming SMS
    if (Body && From) {
      await handleIncomingSMS(MessageSid, From, To, Body);
    }

    res.status(200).type('text/xml').send('<?xml version="1.0"?><Response></Response>');
  } catch (error) {
    console.error('SMS webhook error:', error);
    res.status(500).send('ERROR');
  }
}

async function handleIncomingSMS(
  messageSid: string,
  from: string,
  to: string,
  body: string
): Promise<void> {
  // Find conversation by phone number
  const conversation = await db.query(`
    SELECT customer_id, trip_id, agency_id
    FROM conversations
    WHERE sms_number = $1
    ORDER BY created_at DESC
    LIMIT 1
  `, [from]);

  if (conversation.rows.length === 0) {
    return;
  }

  const { customer_id, trip_id, agency_id } = conversation.rows[0];

  await db.query(`
    INSERT INTO messages (
      agency_id,
      trip_id,
      recipient_type,
      recipient_id,
      recipient_channel,
      content,
      message_type,
      channel,
      channel_message_id,
      direction,
      status,
      sent_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
  `, [
    agency_id,
    trip_id,
    'customer',
    customer_id,
    'sms',
    body,
    'text',
    'sms',
    messageSid,
    'inbound',
    'delivered',
    new Date()
  ]);
}

/**
 * Webhook verification endpoint
 */
router.get('/whatsapp/verify', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];

  if (mode === 'subscribe' && token === process.env.WHATSAPP_VERIFY_TOKEN) {
    res.status(200).send(challenge);
  } else {
    res.sendStatus(403);
  }
});

export default router;
```

---

## Data Persistence

### Repository Pattern

```typescript
// repositories/message.repository.ts

import { Pool } from 'pg';
import {
  Message,
  MessageThread,
  MessageTemplate,
  MessageListFilters,
  MessageAnalytics
} from '../types/message.types';

export class MessageRepository {
  constructor(private db: Pool) {}

  /**
   * Get message by ID
   */
  async findById(id: string): Promise<Message | null> {
    const result = await this.db.query(`
      SELECT * FROM messages WHERE id = $1
    `, [id]);

    return result.rows[0] || null;
  }

  /**
   * List messages with filters
   */
  async list(filters: MessageListFilters, pagination: {
    limit: number;
    offset: number;
  }): Promise<{ messages: Message[]; total: number }> {
    const conditions: string[] = [];
    const params: any[] = [];
    let paramIndex = 1;

    if (filters.tripId) {
      conditions.push(`trip_id = $${paramIndex++}`);
      params.push(filters.tripId);
    }

    if (filters.recipientId) {
      conditions.push(`recipient_id = $${paramIndex++}`);
      params.push(filters.recipientId);
    }

    if (filters.recipientType) {
      conditions.push(`recipient_type = $${paramIndex++}`);
      params.push(filters.recipientType);
    }

    if (filters.channel) {
      conditions.push(`channel = $${paramIndex++}`);
      params.push(filters.channel);
    }

    if (filters.status) {
      conditions.push(`status = $${paramIndex++}`);
      params.push(filters.status);
    }

    if (filters.direction) {
      conditions.push(`direction = $${paramIndex++}`);
      params.push(filters.direction);
    }

    if (filters.threadId) {
      conditions.push(`thread_id = $${paramIndex++}`);
      params.push(filters.threadId);
    }

    if (filters.startDate) {
      conditions.push(`created_at >= $${paramIndex++}`);
      params.push(filters.startDate);
    }

    if (filters.endDate) {
      conditions.push(`created_at <= $${paramIndex++}`);
      params.push(filters.endDate);
    }

    if (filters.search) {
      conditions.push(`to_tsvector('english', content) @@ plainto_tsquery($${paramIndex++})`);
      params.push(filters.search);
    }

    const whereClause = conditions.length > 0
      ? `WHERE ${conditions.join(' AND ')}`
      : '';

    // Get total count
    const countResult = await this.db.query(`
      SELECT COUNT(*) FROM messages ${whereClause}
    `, params);

    const total = parseInt(countResult.rows[0].count);

    // Get paginated results
    params.push(pagination.limit, pagination.offset);

    const messagesResult = await this.db.query(`
      SELECT * FROM messages
      ${whereClause}
      ORDER BY created_at DESC
      LIMIT $${paramIndex++} OFFSET $${paramIndex++}
    `, params);

    return {
      messages: messagesResult.rows,
      total
    };
  }

  /**
   * Get conversation thread
   */
  async getThread(threadId: string): Promise<Message[]> {
    const result = await this.db.query(`
      SELECT * FROM messages
      WHERE thread_id = $1
      ORDER BY created_at ASC
    `, [threadId]);

    return result.rows;
  }

  /**
   * Get or create thread for trip
   */
  async getOrCreateThread(
    agencyId: string,
    tripId: string,
    customerId: string,
    channel: string
  ): Promise<MessageThread> {
    // Try to find existing thread
    const existingResult = await this.db.query(`
      SELECT * FROM message_threads
      WHERE trip_id = $1 AND channel = $2 AND status = 'active'
      ORDER BY last_message_at DESC
      LIMIT 1
    `, [tripId, channel]);

    if (existingResult.rows.length > 0) {
      return existingResult.rows[0];
    }

    // Create new thread
    const createResult = await this.db.query(`
      INSERT INTO message_threads (
        agency_id, trip_id, participant_customer_id, channel
      ) VALUES ($1, $2, $3, $4)
      RETURNING *
    `, [agencyId, tripId, customerId, channel]);

    return createResult.rows[0];
  }

  /**
   * Get message analytics
   */
  async getAnalytics(
    agencyId: string,
    startDate: Date,
    endDate: Date
  ): Promise<MessageAnalytics> {
    const result = await this.db.query(`
      SELECT
        COUNT(*) FILTER (WHERE direction = 'outbound') as total_sent,
        COUNT(*) FILTER (WHERE status = 'delivered') as total_delivered,
        COUNT(*) FILTER (WHERE status = 'failed') as total_failed,
        SUM(cost_cents) FILTER (WHERE direction = 'outbound') as total_cost
      FROM messages
      WHERE agency_id = $1
        AND created_at BETWEEN $2 AND $3
    `, [agencyId, startDate, endDate]);

    const row = result.rows[0];

    const byChannelResult = await this.db.query(`
      SELECT
        channel,
        COUNT(*) FILTER (WHERE direction = 'outbound') as sent,
        COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        AVG(cost_cents) FILTER (WHERE direction = 'outbound') as avg_cost
      FROM messages
      WHERE agency_id = $1
        AND created_at BETWEEN $2 AND $3
      GROUP BY channel
    `, [agencyId, startDate, endDate]);

    const byChannel: Record<string, any> = {};
    for (const row of byChannelResult.rows) {
      byChannel[row.channel] = {
        sent: parseInt(row.sent),
        delivered: parseInt(row.delivered),
        failed: parseInt(row.failed),
        deliveryRate: row.sent > 0 ? parseInt(row.delivered) / parseInt(row.sent) : 0,
        averageCost: parseFloat(row.avg_cost) || 0
      };
    }

    const byDateResult = await this.db.query(`
      SELECT
        DATE(created_at) as date,
        COUNT(*) FILTER (WHERE direction = 'outbound') as sent,
        COUNT(*) FILTER (WHERE status = 'delivered') as delivered,
        COUNT(*) FILTER (WHERE status = 'failed') as failed
      FROM messages
      WHERE agency_id = $1
        AND created_at BETWEEN $2 AND $3
      GROUP BY DATE(created_at)
      ORDER BY date
    `, [agencyId, startDate, endDate]);

    return {
      totalSent: parseInt(row.total_sent) || 0,
      totalDelivered: parseInt(row.total_delivered) || 0,
      totalFailed: parseInt(row.total_failed) || 0,
      deliveryRate: row.total_sent > 0
        ? parseInt(row.total_delivered) / parseInt(row.total_sent)
        : 0,
      averageDeliveryTime: 0, // Would need timestamps to calculate
      totalCost: parseInt(row.total_cost) || 0,
      byChannel,
      byDate: byDateResult.rows.map(r => ({
        date: r.date.toISOString().split('T')[0],
        sent: parseInt(r.sent),
        delivered: parseInt(r.delivered),
        failed: parseInt(r.failed)
      }))
    };
  }

  /**
   * Save message
   */
  async save(message: Partial<Message>): Promise<Message> {
    if (message.id) {
      // Update
      const result = await this.db.query(`
        UPDATE messages SET
          status = COALESCE($1, status),
          sent_at = COALESCE($2, sent_at),
          delivered_at = COALESCE($3, delivered_at),
          read_at = COALESCE($4, read_at),
          failed_at = COALESCE($5, failed_at),
          error_message = COALESCE($6, error_message),
          channel_message_id = COALESCE($7, channel_message_id),
          updated_at = NOW()
        WHERE id = $8
        RETURNING *
      `, [
        message.status,
        message.sentAt,
        message.deliveredAt,
        message.readAt,
        message.failedAt,
        message.errorMessage,
        message.channelMessageId,
        message.id
      ]);

      return result.rows[0];
    } else {
      // Create
      const result = await this.db.query(`
        INSERT INTO messages (
          agency_id, trip_id, recipient_type, recipient_id,
          recipient_channel, subject, content, message_type,
          template_id, channel, channel_message_id, direction,
          status, thread_id, parent_message_id, metadata,
          attachments, cost_cents
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
        )
        RETURNING *
      `, [
        message.agencyId,
        message.tripId,
        message.recipientType,
        message.recipientId,
        message.recipientChannel,
        message.subject,
        message.content,
        message.messageType,
        message.templateId,
        message.channel,
        message.channelMessageId,
        message.direction,
        message.status,
        message.threadId,
        message.parentMessageId,
        JSON.stringify(message.metadata || {}),
        JSON.stringify(message.attachments || []),
        message.costCents || 0
      ]);

      return result.rows[0];
    }
  }
}
```

---

## Security Considerations

### 1. Webhook Security

- **Signature Verification**: All webhooks verify HMAC signatures
- **Timestamp Validation**: Reject stale webhook deliveries
- **Replay Attack Prevention**: Use nonce/timestamp combination

### 2. Data Protection

- **PII Redaction**: Sensitive data logged only in hashed form
- **Encryption at Rest**: Message content encrypted in database
- **Encryption in Transit**: TLS 1.3 for all external communications

### 3. Rate Limiting

```typescript
// middleware/rate-limiter.ts

import rateLimit from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';

export const webhookRateLimit = rateLimit({
  store: new RedisStore({
    client: getRedisClient(),
    prefix: 'rl:webhook:'
  }),
  windowMs: 60 * 1000, // 1 minute
  max: 100, // 100 requests per minute per IP
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    res.status(429).json({ error: 'Too many requests' });
  }
});
```

### 4. Access Control

```typescript
// middleware/message-auth.ts

export async function canAccessMessage(
  userId: string,
  agencyId: string,
  messageId: string
): Promise<boolean> {
  const result = await db.query(`
    SELECT 1 FROM messages m
    JOIN agencies a ON a.id = m.agency_id
    JOIN agency_agents aa ON aa.agency_id = a.id
    WHERE m.id = $1
      AND aa.agent_id = $2
      AND a.id = $3
  `, [messageId, userId, agencyId]);

  return result.rows.length > 0;
}

export async function canSendMessageToRecipient(
  userId: string,
  recipientId: string,
  recipientType: string
): Promise<boolean> {
  // Check if user has permission to message this recipient
  const result = await db.query(`
    SELECT 1 FROM agency_agents aa
    JOIN agencies a ON a.id = aa.agency_id
    LEFT JOIN trips t ON t.agency_id = a.id
    WHERE aa.agent_id = $1
      AND (
        (t.customer_id = $2 AND $3 = 'customer')
        OR (aa.agent_id = $2 AND $3 = 'agent')
      )
  `, [userId, recipientId, recipientType]);

  return result.rows.length > 0;
}
```

---

## API Specification

### POST /api/messages/send

Send a new message.

**Request:**
```json
{
  "recipientId": "uuid",
  "recipientType": "customer",
  "channel": "whatsapp",
  "subject": "Your booking confirmation",
  "content": "Hello! Your trip to Goa has been confirmed...",
  "tripId": "uuid",
  "templateId": "optional-template-id",
  "templateVariables": {
    "customerName": "John",
    "destination": "Goa"
  },
  "attachments": [],
  "scheduledFor": "2026-04-25T10:00:00Z"
}
```

**Response:**
```json
{
  "messageId": "uuid",
  "status": "queued",
  "estimatedDelivery": "2026-04-24T14:05:23Z",
  "cost": 0.5
}
```

### GET /api/messages

List messages with filters.

**Query Parameters:**
- `tripId`: Filter by trip
- `recipientId`: Filter by recipient
- `channel`: Filter by channel
- `status`: Filter by status
- `threadId`: Filter by thread
- `search`: Full-text search
- `limit`: Pagination limit (default 50)
- `offset`: Pagination offset

**Response:**
```json
{
  "messages": [...],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### GET /api/messages/:id

Get message details.

**Response:**
```json
{
  "id": "uuid",
  "agencyId": "uuid",
  "tripId": "uuid",
  "recipientType": "customer",
  "recipientId": "uuid",
  "channel": "whatsapp",
  "content": "...",
  "status": "delivered",
  "sentAt": "2026-04-24T14:00:00Z",
  "deliveredAt": "2026-04-24T14:00:05Z",
  "costCents": 50
}
```

### GET /api/messages/analytics

Get message analytics.

**Query Parameters:**
- `startDate`: Start date
- `endDate`: End date

**Response:**
```json
{
  "totalSent": 1500,
  "totalDelivered": 1425,
  "totalFailed": 75,
  "deliveryRate": 0.95,
  "averageDeliveryTime": 3.2,
  "totalCost": 750,
  "byChannel": {...},
  "byDate": [...]
}
```

### GET /api/threads

List conversation threads.

**Response:**
```json
{
  "threads": [
    {
      "id": "uuid",
      "tripId": "uuid",
      "channel": "whatsapp",
      "subject": "Goa Trip - March 2026",
      "lastMessageAt": "2026-04-24T14:00:00Z",
      "messageCount": 15,
      "status": "active"
    }
  ]
}
```

### GET /api/threads/:id/messages

Get messages in a thread.

**Response:**
```json
{
  "messages": [...]
}
```

### POST /api/templates

Create a message template.

**Request:**
```json
{
  "name": "Booking Confirmation",
  "code": "booking_confirmation",
  "category": "booking",
  "subjectTemplate": "Booking Confirmed: {{destination}}",
  "contentTemplate": "Hello {{customerName}}, your booking to {{destination}} is confirmed!",
  "channel": "whatsapp",
  "language": "en",
  "variables": [
    {
      "name": "customerName",
      "type": "string",
      "required": true
    },
    {
      "name": "destination",
      "type": "string",
      "required": true
    }
  ]
}
```

---

## Summary

The Communication Hub technical architecture provides:

1. **Unified Multi-Channel Messaging**: Single interface for WhatsApp, Email, SMS, and In-App
2. **Intelligent Orchestration**: Automatic channel selection, fallback, and batching
3. **Real-Time Updates**: WebSocket-based live message status
4. **Webhook Integration**: Event-driven processing of inbound messages
5. **Template System**: Dynamic, localized message templates
6. **Analytics**: Comprehensive delivery tracking and insights

---

**Next:** Communication Hub UX/UI Deep Dive (COMM_HUB_02) — interface design for message composer, conversation view, and template manager
