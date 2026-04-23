# Intake Channel Integration Deep Dive

> Comprehensive integration patterns for WhatsApp, Email, Web, and Phone channels

**Document:** INTAKE_03_CHANNEL_INTEGRATION_DEEP_DIVE.md
**Series:** Intake / Packet Processing Deep Dive
**Status:** ✅ Complete
**Last Updated:** 2026-04-23
**Related:** [INTAKE_01_TECHNICAL_DEEP_DIVE.md](./INTAKE_01_TECHNICAL_DEEP_DIVE.md)

---

## Table of Contents

1. [Channel Architecture](#channel-architecture)
2. [WhatsApp Integration](#whatsapp-integration)
3. [Email Integration](#email-integration)
4. [Web Form Integration](#web-form-integration)
5. [Phone/VoIP Integration](#phonevoip-integration)
6. [Message Normalization](#message-normalization)
7. [Media Processing](#media-processing)
8. [Channel-Specific Features](#channel-specific-features)
9. [Implementation Reference](#implementation-reference)

---

## 1. Channel Architecture

### Unified Channel Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        UNIFIED CHANNEL ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        CHANNEL AGGREGATOR                             │   │
│  │  Normalizes all inbound messages to common format                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│           ┌────────────────────────┼────────────────────────┐              │
│           │                        │                        │              │
│           ▼                        ▼                        ▼              │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│  │  WHATSAPP    │      │    EMAIL     │      │     WEB      │          │
│  │  INTEGRATION │      │ INTEGRATION  │      │  INTEGRATION │          │
│  │  (Twilio)    │      │  (SendGrid)  │      │   (Custom)   │          │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘          │
│         │                     │                     │                    │
│         └─────────────────────┴─────────────────────┘                    │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         MESSAGE BUS (Kafka)                          │   │
│  │  Topic: inbound-messages                                            │   │
│  │  Partition key: customer_id (for message ordering)                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      INGESTION SERVICE                               │   │
│  │  • Deduplication                                                    │   │
│  │  • Thread grouping                                                  │   │
│  │  • Attachment extraction                                            │   │
│  │  • Customer linking                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    EXTRACTION PIPELINE                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Channel Metrics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHANNEL DISTRIBUTION & METRICS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CHANNEL VOLUME:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  WhatsApp  ████████████████████████████████ 60%                     │   │
│  │  Email     ████████████████ 25%                                    │   │
│  │  Web       ████ 10%                                                 │   │
│  │  Phone     ██ 5%                                                    │   │
│  │                                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHANNEL CHARACTERISTICS:                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Channel    │ Volume │ Response Rate │ Avg Response Time │ Features │   │
│  ├────────────┼────────┼───────────────┼──────────────────┼──────────┤   │
│  │ WhatsApp   │ 60%    │ 95%           │ 2 hours           │ Media,  │   │
│  │            │        │               │                   │ Quick    │   │
│  │ Email      │ 25%    │ 70%           │ 24 hours          │ Thread, │   │
│  │            │        │               │                   │ Attach.  │   │
│  │ Web        │ 10%    │ 85%           │ 4 hours           │ Struct.  │   │
│  │ Phone      │ 5%     │ 90%           │ 1 hour            │ Voice,   │   │
│  │            │        │               │                   │ IVR      │   │
│  └────────────┴────────┴───────────────┴──────────────────┴──────────┘   │
│                                                                             │
│  CHANNEL PRIORITIZATION:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Priority │ Reason                        │ SLA                     │   │   │
│  │──────────┼───────────────────────────────┼─────────────────────────│   │   │
│  │ P0       │ VIP WhatsApp                  │ < 30 min               │   │   │
│  │ P1       │ Phone (urgent)               │ < 1 hour               │   │   │
│  │ P2       │ Standard WhatsApp/Email       │ < 4 hours              │   │   │
│  │ P3       │ Web forms                    │ < 8 hours              │   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. WhatsApp Integration

### Technical Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        WHATSAPP INTEGRATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROVIDER: Twilio API for WhatsApp Business                                 │
│                                                                             │
│  WEBHOOK ENDPOINT: POST /webhooks/whatsapp                                  │
│                                                                             │
│  FLOW:                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐│
│  │  CUSTOMER   │ ──▶ │  TWILIO    │ ──▶ │   WEBHOOK  │ ──▶ │   KAFKA   ││
│  │  SENDS     │     │  WEBHOOK   │     │  HANDLER   │     │   TOPIC   ││
│  │  MESSAGE   │     │            │     │            │     │           ││
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────────┘│
│                                                                             │
│  INCOMING WEBHOOK PAYLOAD:                                                 │
│  {                                                                         │
│    "AccountSid": "ACxxx",                                                  │
│    "MessageSid": "SMxxx",                                                 │
│    "From": "whatsapp:+919876543210",                                       │
│    "To": "whatsapp:+14155238886",                                          │
│    "Body": "Planning trip to Goa in May. 4 adults...",                     │
│    "NumMedia": "2",                                                       │
│    "MediaUrl0": "https://...",                                            │
│    "MediaUrl1": "https://...",                                            │
│    "MediaContentType0": "image/jpeg",                                      │
│    "MediaContentType1": "audio/mpeg"                                       │
│  }                                                                         │
│                                                                             │
│  OUTGOING MESSAGE API:                                                      │
│  POST https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages.json │
│  {                                                                         │
│    "From": "whatsapp:+14155238886",                                        │
│    "To": "whatsapp:+919876543210",                                         │
│    "Body": "Hi! Thanks for reaching out...",                               │
│    "MediaUrl": ["https://.../itinerary.pdf"]                               │
│  }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### WhatsApp Message Handler

```typescript
// WhatsApp Webhook Handler
import { Twilio } from 'twilio';
import { Producer } from 'kafkajs';

interface WhatsAppWebhookPayload {
  AccountSid: string;
  MessageSid: string;
  From: string;
  To: string;
  Body: string;
  NumMedia: string;
  MediaUrl0?: string;
  MediaUrl1?: string;
  MediaContentType0?: string;
  MediaContentType1?: string;
}

class WhatsAppHandler {
  private twilio: Twilio;
  private kafkaProducer: Producer;
  private phoneNumber: string;

  constructor() {
    this.twilio = new Twilio(
      process.env.TWILIO_ACCOUNT_SID,
      process.env.TWILIO_AUTH_TOKEN
    );
    this.kafkaProducer = createKafkaProducer();
    this.phoneNumber = process.env.WHATSAPP_BUSINESS_NUMBER;
  }

  async handleWebhook(payload: WhatsAppWebhookPayload): Promise<void> {
    // 1. Validate webhook
    if (!this.isValidSignature(payload)) {
      throw new Error('Invalid webhook signature');
    }

    // 2. Extract customer phone
    const customerPhone = this.normalizePhone(payload.From);

    // 3. Download media if present
    const attachments: Attachment[] = [];
    if (parseInt(payload.NumMedia) > 0) {
      for (let i = 0; i < parseInt(payload.NumMedia); i++) {
        const mediaUrl = payload[`MediaUrl${i}`];
        const contentType = payload[`MediaContentType${i}`];
        const attachment = await this.downloadMedia(mediaUrl, contentType);
        attachments.push(attachment);
      }
    }

    // 4. Detect language
    const language = this.detectLanguage(payload.Body);

    // 5. Create normalized message
    const normalizedMessage: NormalizedMessage = {
      id: payload.MessageSid,
      channel: 'whatsapp',
      timestamp: new Date(),
      customer: { phone: customerPhone },
      text: payload.Body,
      language,
      attachments,
      channelMetadata: {
        whatsapp: {
          from: customerPhone,
          messageSid: payload.MessageSid
        }
      },
      processing: {
        receivedAt: new Date(),
        normalizedAt: new Date()
      }
    };

    // 6. Publish to Kafka
    await this.kafkaProducer.send({
      topic: 'inbound-messages',
      messages: [{
        key: customerPhone,
        value: JSON.stringify(normalizedMessage),
        headers: {
          channel: 'whatsapp',
          contentType: 'application/json'
        }
      }]
    });

    // 7. Send immediate acknowledgement (optional)
    // await this.sendAcknowledgement(customerPhone);
  }

  async sendMessage(
    to: string,
    body: string,
    mediaUrls?: string[]
  ): Promise<string> {
    const message = await this.twilio.messages.create({
      from: `whatsapp:${this.phoneNumber}`,
      to: `whatsapp:${this.normalizePhone(to)}`,
      body,
      mediaUrl: mediaUrls
    });

    return message.sid;
  }

  async sendTemplateMessage(
    to: string,
    templateName: string,
    params: Record<string, string>
  ): Promise<string> {
    // WhatsApp template message (pre-approved by WhatsApp)
    const message = await this.twilio.messages.create({
      from: `whatsapp:${this.phoneNumber}`,
      to: `whatsapp:${this.normalizePhone(to)}`,
      body: this.buildTemplateMessage(templateName, params)
    });

    return message.sid;
  }

  async sendQuickReplies(
    to: string,
    body: string,
    quickReplies: string[]
  ): Promise<string> {
    // WhatsApp interactive list message
    const message = await this.twilio.messages.create({
      from: `whatsapp:${this.phoneNumber}`,
      to: `whatsapp:${this.normalizePhone(to)}`,
      body,
      interactiveContent: {
        type: 'list',
        header: {
          type: 'text',
          text: 'Please select an option'
        },
        body: {
          text: body
        },
        action: {
          button: 'Options',
          sections: [{
            title: 'Choose',
            rows: quickReplies.map((reply, idx) => ({
              id: `option_${idx}`,
              title: reply,
              description: ''
            }))
          }]
        }
      }
    } as any);

    return message.sid;
  }

  private normalizePhone(phone: string): string {
    // Convert WhatsApp format to standard E.164
    return phone.replace('whatsapp:', '+');
  }

  private detectLanguage(text: string): string {
    // Simple detection (in production, use fastText or similar)
    const hasHindi = /[ऀ-ॿ]/.test(text);
    return hasHindi ? 'hi' : 'en';
  }

  private async downloadMedia(
    url: string,
    contentType: string
  ): Promise<Attachment> {
    const response = await fetch(url);
    const buffer = await response.arrayBuffer();

    // Upload to S3
    const s3Key = `whatsapp/${Date.now()}_${this.generateFilename()}`;
    await uploadToS3(s3Key, Buffer.from(buffer), contentType);

    return {
      id: generateId(),
      type: this.getMediaType(contentType),
      mimeType: contentType,
      url: getS3Url(s3Key)
    };
  }

  private getMediaType(contentType: string): 'image' | 'audio' | 'video' | 'document' {
    if (contentType.startsWith('image/')) return 'image';
    if (contentType.startsWith('audio/')) return 'audio';
    if (contentType.startsWith('video/')) return 'video';
    return 'document';
  }
}
```

### WhatsApp Templates

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WHATSAPP MESSAGE TEMPLATES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TEMPLATE 1: TRIP INQUIRY ACKNOWLEDGEMENT                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Name: trip_inquiry_ack                                              │   │
│  │ Category: inquiry_response                                          │   │
│  │ Status: Approved by WhatsApp                                        │   │
│  │                                                                     │   │
│  │ Content:                                                            │   │
│  │ "Hi {{1}}! 👋 Thanks for reaching out to {{2}} Travel.              │   │
│  │  We're excited to help plan your trip! 🌴                           │   │
│  │                                                                     │   │
│  │  Our team will review your inquiry and get back to you              │   │
│  │  within {{3}} hours.                                                │   │
│  │                                                                     │   │
│  │  Need immediate help? Call us at {{4}}"                             │   │
│  │                                                                     │   │
│  │ Parameters:                                                         │   │
│  │   {{1}} = Customer name (optional, defaults to "there")             │   │
│  │   {{2}} = Agency name                                               │   │
│  │   {{3}} = Response time hours                                       │   │
│  │   {{4}} = Phone number                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TEMPLATE 2: INFORMATION REQUEST                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Name: info_request                                                 │   │
│  │ Category: inquiry_response                                          │   │
│  │                                                                     │   │
│  │ "Hi {{1}}! To help us plan your perfect trip, we need:             │   │
│  │  {{2}}                                                            │   │
│  │  Please reply when convenient! 😊"                                 │   │
│  │                                                                     │   │
│  │ Parameters:                                                         │   │
│  │   {{1}} = Customer name                                             │   │
│  │   {{2}} = List of missing information                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TEMPLATE 3: QUOTE SENT                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Name: quote_sent                                                    │   │
│  │ Category: agent_message                                             │   │
│  │                                                                     │   │
│  │ "Hi {{1}}! 🎉 Your quote for {{2}} is ready!                       │   │
│  │                                                                     │   │
│  │  {{3}} nights for {{4}} travelers                                  │   │
│  │  Total: {{5}}                                                      │   │
│  │                                                                     │   │
│  │  View full details: {{6}}"                                         │   │
│  │                                                                     │   │
│  │ Parameters:                                                         │   │
│  │   {{1}} = Customer name                                             │   │
│  │   {{2}} = Destination                                              │   │
│  │   {{3}} = Number of nights                                         │   │
│  │   {{4}} = Number of travelers                                      │   │
│  │   {{5}} = Total amount                                             │   │
│  │   {{6}} = Quote link                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  QUICK REPLY BUTTONS:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ "Yes, 2025" │ "No, 2026" │ "Budget flexible" │ "Fixed budget"    │   │
│  │ "Call me"   │ "Email details" │ "Not interested"                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Email Integration

### Technical Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EMAIL INTEGRATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROVIDER: SendGrid Inbound Parse Webhook                                   │
│                                                                             │
│  DNS CONFIGURATION:                                                         │
│  MX record: inbound@yourdomain.com → mx.sendgrid.net                        │
│                                                                             │
│  WEBHOOK ENDPOINT: POST /webhooks/email                                     │
│                                                                             │
│  FLOW:                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐│
│  │  CUSTOMER   │ ──▶ │  SENDGRID  │ ──▶ │   WEBHOOK  │ ──▶ │   KAFKA   ││
│  │  SENDS     │     │  PARSE     │     │  HANDLER   │     │   TOPIC   ││
│  │  EMAIL     │     │            │     │            │     │           ││
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────────┘│
│                                                                             │
│  INCOMING EMAIL STRUCTURE:                                                  │
│  {                                                                         │
│    "headers": "DKIM-Signature, Received, ...",                            │
│    "from": "customer@example.com",                                         │
│    "to": "inquiry@yourdomain.com",                                         │
│    "subject": "Planning trip to Goa - May 2025",                          │
│    "text": "Planning trip to Goa...",                                     │
│    "html": "<html>...</html>",                                            │
│    "attachments": [                                                        │
│      {                                                                     │
│        "filename": "requirements.pdf",                                     │
│        "type": "application/pdf",                                         │
│        "content-id": "abc123",                                            │
│        "size": 12345                                                      │
│      }                                                                     │
│    ],                                                                      │
│    "charsets": {                                                           │
│      "to": "UTF-8",                                                       │
│      "subject": "UTF-8",                                                  │
│      "from": "UTF-8",                                                     │
│      "text": "UTF-8"                                                      │
│    },                                                                      │
│    "spam_score": 1.2,                                                      │
│    "spam_report": "SPAM_PASS..."                                          │
│  }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Email Message Handler

```typescript
// Email Webhook Handler
import { simpleParser } from 'mailparser';

interface EmailWebhookPayload {
  headers: string;
  from: string;
  to: string;
  subject: string;
  text: string;
  html: string;
  attachments: Array<{
    filename: string;
    type: string;
    contentId: string;
    size: number;
  }>;
  charsets: Record<string, string>;
  spam_score: number;
  spam_report: string;
}

class EmailHandler {
  private kafkaProducer: Producer;

  constructor() {
    this.kafkaProducer = createKafkaProducer();
  }

  async handleWebhook(payload: EmailWebhookPayload): Promise<void> {
    // 1. Parse email headers
    const headers = this.parseHeaders(payload.headers);
    const threadId = this.getThreadId(headers);
    const isForward = this.checkIfForward(payload.subject, payload.text);

    // 2. Extract email body
    const { text, html } = this.extractBody(payload);
    const cleanText = this.removeQuotedReplies(text);
    const signatureRemoved = this.removeSignature(cleanText);

    // 3. Process attachments
    const attachments: Attachment[] = [];
    for (const att of payload.attachments) {
      const attachment = await this.processAttachment(att);
      attachments.push(attachment);
    }

    // 4. Extract customer info
    const customerEmail = this.normalizeEmail(payload.from);
    const customerName = this.extractName(payload.from);

    // 5. Detect language
    const language = this.detectLanguage(signatureRemoved);

    // 6. Create normalized message
    const normalizedMessage: NormalizedMessage = {
      id: generateId(),
      channel: 'email',
      timestamp: new Date(),
      customer: { email: customerEmail, name: customerName },
      text: signatureRemoved,
      html,
      language,
      attachments,
      channelMetadata: {
        email: {
          from: payload.from,
          subject: payload.subject,
          threadId,
          isForward
        }
      },
      processing: {
        receivedAt: new Date(headers.date),
        normalizedAt: new Date()
      }
    };

    // 7. Publish to Kafka
    await this.kafkaProducer.send({
      topic: 'inbound-messages',
      messages: [{
        key: customerEmail,
        value: JSON.stringify(normalizedMessage),
        headers: {
          channel: 'email',
          threadId,
          contentType: 'application/json'
        }
      }]
    });
  }

  async sendEmail(
    to: string,
    subject: string,
    body: string,
    attachments?: Array<{ filename: string; content: Buffer }>
  ): Promise<string> {
    // Use SendGrid API to send email
    const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.SENDGRID_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        personalizations: [{
          to: [{ email: to }],
          subject
        }],
        from: { email: 'inquiry@yourdomain.com', name: 'Your Travel Agency' },
        content: [{
          type: 'text/html',
          value: body
        }],
        attachments: attachments?.map(att => ({
          content: att.content.toString('base64'),
          filename: att.filename,
          type: 'application/pdf',
          disposition: 'attachment'
        }))
      })
    });

    return response.headers.get('X-Message-Id') || '';
  }

  async replyToThread(
    threadId: string,
    to: string,
    subject: string,
    body: string
  ): Promise<string> {
    // Send reply that maintains thread
    const response = await this.sendEmail(to, subject, body);
    return response;
  }

  private parseHeaders(headersString: string): Record<string, string> {
    const headers: Record<string, string> = {};
    const lines = headersString.split('\n');

    for (const line of lines) {
      const match = line.match(/^([^:]+):\s*(.+)$/);
      if (match) {
        headers[match[1].trim()] = match[2].trim();
      }
    }

    return headers;
  }

  private getThreadId(headers: Record<string, string>): string | undefined {
    // Try to extract thread ID from various headers
    return (
      headers['Message-ID'] ||
      headers['In-Reply-To'] ||
      headers['References']?.split(' ')[0]
    );
  }

  private checkIfForward(subject: string, text: string): boolean {
    const fwdPatterns = [
      /^fwd:/i,
      /^forward:/i,
      /---------- forwarded message ---------/i
    ];
    return fwdPatterns.some(pattern =>
      pattern.test(subject) || pattern.test(text)
    );
  }

  private removeQuotedReplies(text: string): string {
    // Remove quoted reply text
    const patterns = [
      /On .+ wrote:.+[\s\S]+/gm,  // "On X wrote:"
      /^>.*$/gm,                   // Lines starting with >
      /-----Original Message-----[\s\S]+$/gm  // Everything after this marker
    ];

    let cleaned = text;
    for (const pattern of patterns) {
      cleaned = cleaned.replace(pattern, '');
    }

    return cleaned.trim();
  }

  private removeSignature(text: string): string {
    // Common signature patterns
    const patterns = [
      /--\s*[\s\S]+$/,  // Everything after "--"
      /Best regards,[\s\S]+$/i,
      /Thanks,[\s\S]+$/i,
      /Sent from my[\s\S]+$/i
    ];

    let cleaned = text;
    for (const pattern of patterns) {
      cleaned = cleaned.replace(pattern, '');
    }

    return cleaned.trim();
  }

  private extractName(from: string): string | null {
    // Extract name from "Name <email>" format
    const match = from.match(/^"?([^"<>]+)"?\s*<[^<>]+>$/);
    return match ? match[1].trim() : null;
  }

  private normalizeEmail(email: string): string {
    // Extract email from "Name <email>" format
    const match = email.match(/<([^<>]+)>/);
    return match ? match[1] : email.toLowerCase().trim();
  }

  private async processAttachment(attachment: any): Promise<Attachment> {
    // Download attachment from SendGrid
    const content = Buffer.from(attachment.content, 'base64');

    // Upload to S3
    const s3Key = `email/${Date.now()}_${attachment.filename}`;
    await uploadToS3(s3Key, content, attachment.type);

    // Extract text if PDF
    let extractedText;
    if (attachment.type === 'application/pdf') {
      extractedText = await extractTextFromPDF(content);
    }

    return {
      id: generateId(),
      type: this.getMediaType(attachment.type),
      mimeType: attachment.type,
      url: getS3Url(s3Key),
      extractedText,
      metadata: {
        filename: attachment.filename,
        size: attachment.size
      }
    };
  }

  private getMediaType(mimeType: string): 'image' | 'document' | 'audio' | 'video' {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.startsWith('video/')) return 'video';
    return 'document';
  }
}
```

---

## 4. Web Form Integration

### Technical Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEB FORM INTEGRATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRONTEND: React Form Component                                             │
│  BACKEND: FastAPI /api/v1/inquiries/web                                    │
│                                                                             │
│  FLOW:                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐│
│  │  CUSTOMER   │ ──▶ │   REACT    │ ──▶ │   API      │ ──▶ │   KAFKA   ││
│  │  FILLS     │     │   FORM     │     │  ENDPOINT  │     │   TOPIC   ││
│  │  FORM      │     │            │     │            │     │           ││
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────────┘│
│                                                                             │
│  FORM SCHEMA:                                                               │
│  {                                                                         │
│    "destination": { "type": "text", "required": true },                    │
│    "startDate": { "type": "date", "required": true },                      │
│    "endDate": { "type": "date", "required": true },                        │
│    "travelersAdults": { "type": "number", "default": 2 },                 │
│    "travelersChildren": { "type": "number", "default": 0 },               │
│    "budget": { "type": "number", "required": false },                     │
│    "budgetCurrency": { "type": "select", "options": ["INR", "USD"] },     │
│    "tripType": {                                                          │
│      "type": "select",                                                    │
│      "options": ["leisure", "honeymoon", "family", "group", "adventure"]  │
│    },                                                                      │
│    "preferences": { "type": "textarea" },                                 │
│    "customerName": { "type": "text", "required": true },                   │
│    "customerPhone": { "type": "tel", "required": true },                  │
│    "customerEmail": { "type": "email", "required": true }                 │
│  }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Web Form Handler

```typescript
// Web Form API Endpoint
import { Router } from 'express';

const router = Router();

interface WebInquirySubmission {
  destination: string;
  startDate?: string;
  endDate?: string;
  travelersAdults?: number;
  travelersChildren?: number;
  budget?: number;
  budgetCurrency?: string;
  tripType?: string;
  preferences?: string;
  customerName: string;
  customerPhone: string;
  customerEmail: string;
  recaptchaToken?: string;
}

router.post('/api/v1/inquiries/web',
  validateRecaptcha,
  validateWebInquiry,
  async (req, res) => {
    const submission: WebInquirySubmission = req.body;

    // 1. Validate reCAPTCHA
    const validCaptcha = await verifyRecaptcha(submission.recaptchaToken);
    if (!validCaptcha) {
      return res.status(400).json({ error: 'Invalid captcha' });
    }

    // 2. Server-side validation
    const validation = validateWebSubmission(submission);
    if (!validation.isValid) {
      return res.status(400).json({ errors: validation.errors });
    }

    // 3. Create structured data
    const extractedFields: TripFields = {
      destination: submission.destination,
      destinationType: getDestinationType(submission.destination),
      startDate: submission.startDate ? new Date(submission.startDate) : null,
      endDate: submission.endDate ? new Date(submission.endDate) : null,
      datesFlexible: !submission.startDate || !submission.endDate,
      travelersAdults: submission.travelersAdults || 2,
      travelersChildren: submission.travelersChildren || 0,
      totalTravelers: (submission.travelersAdults || 2) + (submission.travelersChildren || 0),
      budgetAmount: submission.budget || null,
      budgetCurrency: submission.budgetCurrency || 'INR',
      tripType: submission.tripType as TripType || null,
      preferences: submission.preferences ? {
        special: [submission.preferences]
      } : null,
      customerName: submission.customerName,
      customerPhone: submission.customerPhone,
      customerEmail: submission.customerEmail
    };

    // 4. Create normalized message
    const normalizedMessage: NormalizedMessage = {
      id: generateId(),
      channel: 'web',
      timestamp: new Date(),
      customer: {
        email: submission.customerEmail,
        phone: submission.customerPhone,
        name: submission.customerName
      },
      text: `Web inquiry for ${submission.destination}`,
      language: 'en',
      attachments: [],
      channelMetadata: {
        web: {
          userAgent: req.headers['user-agent'],
          referrer: req.headers['referer']
        }
      },
      processing: {
        receivedAt: new Date(),
        normalizedAt: new Date()
      }
    };

    // 5. Create packet with pre-extracted data
    const packet: TripPacket = {
      id: generateId(),
      customerId: null,
      inquiryId: normalizedMessage.id,
      source: {
        channel: 'web',
        messageId: normalizedMessage.id,
        receivedAt: new Date()
      },
      extracted: {
        fields: extractedFields,
        confidence: {
          overall: 0.95,  // High confidence from structured form
          perField: {
            destination: { score: 1.0, method: 'explicit', source: 'form' },
            // ... other fields
          },
          sourceAgreement: 1.0
        },
        metadata: {
          extractedAt: new Date(),
          extractionMethod: 'form',
          processingTimeMs: 0
        },
        notes: {}
      },
      validated: {
        fields: extractedFields,
        status: 'valid',
        missingFields: [],
        inconsistentFields: [],
        warnings: []
      },
      enriched: {
        customer: null,
        history: null,
        destination: null,
        seasonal: null,
        similarTrips: null
      },
      triage: {
        urgency: 'normal',
        complexity: 'simple',
        value: 'medium',
        priority: 'p2',
        routing: {
          queue: 'general',
          reason: 'Web form submission'
        }
      },
      state: 'validated',
      stateHistory: [],
      audit: {
        createdAt: new Date(),
        updatedAt: new Date(),
        updatedBy: null,
        version: 1,
        changes: []
      },
      metadata: {
        processingTimeMs: 100,
        confidence: 0.95,
        priority: 'p2'
      }
    };

    // 6. Save packet
    await savePacket(packet);

    // 7. Publish to Kafka
    await kafkaProducer.send({
      topic: 'inbound-messages',
      messages: [{
        key: normalizedMessage.id,
        value: JSON.stringify({ message: normalizedMessage, packet }),
        headers: {
          channel: 'web',
          contentType: 'application/json'
        }
      }]
    });

    // 8. Send confirmation
    await sendEmailConfirmation(submission.customerEmail, packet.id);

    // 9. Return response
    return res.status(201).json({
      inquiryId: packet.id,
      message: 'Inquiry received successfully',
      estimatedResponseTime: '4 hours'
    });
  }
);

// Validation middleware
function validateWebInquiry(req, res, next) {
  const schema = {
    destination: { required: true, type: 'string', minLength: 2 },
    customerName: { required: true, type: 'string', minLength: 2 },
    customerPhone: { required: true, type: 'string', pattern: /^[\d\s\+]+$/ },
    customerEmail: { required: true, type: 'string', format: 'email' }
  };

  const errors = validate(req.body, schema);
  if (errors.length > 0) {
    return res.status(400).json({ errors });
  }

  next();
}
```

### React Form Component

```typescript
// React Web Form Component
import { useForm } from 'react-hook-form';

interface WebInquiryFormProps {
  onSuccess: (inquiryId: string) => void;
}

export function WebInquiryForm({ onSuccess }: WebInquiryFormProps) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<WebInquirySubmission>();

  const onSubmit = async (data: WebInquirySubmission) => {
    try {
      const response = await fetch('/api/v1/inquiries/web', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...data,
          recaptchaToken: await executeRecaptcha()
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Submission failed');
      }

      const result = await response.json();
      onSuccess(result.inquiryId);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="inquiry-form">
      {/* Trip Details Section */}
      <Section title="Trip Details">
        <Input
          label="Destination"
          {...register('destination', { required: 'Destination is required' })}
          error={errors.destination?.message}
          placeholder="e.g., Goa, Kerala, Thailand"
        />

        <DateRangePicker
          startDateProps={{
            label: 'Start Date',
            ...register('startDate')
          }}
          endDateProps={{
            label: 'End Date',
            ...register('endDate')
          }}
        />

        <TravelerCounter
          adultsProps={register('travelersAdults', { valueAsNumber: true })}
          childrenProps={register('travelersChildren', { valueAsNumber: true })}
        />

        <BudgetInput
          amountProps={register('budget', { valueAsNumber: true })}
          currencyProps={register('budgetCurrency')}
        />

        <Select
          label="Trip Type"
          {...register('tripType')}
          options={[
            { value: 'leisure', label: 'Leisure' },
            { value: 'honeymoon', label: 'Honeymoon' },
            { value: 'family', label: 'Family Vacation' },
            { value: 'group', label: 'Group Trip' },
            { value: 'adventure', label: 'Adventure' }
          ]}
        />

        <Textarea
          label="Preferences (optional)"
          {...register('preferences')}
          placeholder="Tell us about your preferences..."
          rows={4}
        />
      </Section>

      {/* Contact Details Section */}
      <Section title="Contact Details">
        <Input
          label="Your Name"
          {...register('customerName', { required: 'Name is required' })}
          error={errors.customerName?.message}
        />

        <Input
          label="Phone Number"
          type="tel"
          {...register('customerPhone', {
            required: 'Phone number is required',
            pattern: /^[\d\s\+]+$/
          })}
          error={errors.customerPhone?.message}
          placeholder="+91 XXXXX XXXXX"
        />

        <Input
          label="Email"
          type="email"
          {...register('customerEmail', {
            required: 'Email is required',
            pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          })}
          error={errors.customerEmail?.message}
        />
      </Section>

      {/* Submit */}
      <div className="form-actions">
        <Reaptcha />
        <Button
          type="submit"
          disabled={isSubmitting}
          loading={isSubmitting}
        >
          Submit Inquiry
        </Button>
      </div>

      <p className="form-notice">
        We'll get back to you within 4 hours during business hours.
      </p>
    </form>
  );
}
```

---

## 5. Phone/VoIP Integration

### Technical Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHONE/VOIP INTEGRATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PROVIDER: Exotel / Twilio                                                  │
│                                                                             │
│  TWO MODES:                                                                 │
│  1. INBOUND CALLS → IVR → AGENT                                           │
│  2. AGENT CALL NOTES → POST-CALL DATA ENTRY                                │
│                                                                             │
│  MODE 1: INBOUND CALL FLOW                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────────┐│
│  │  CUSTOMER   │ ──▶ │    IVR     │ ──▶ │   AGENT    │ ──▶ │   NOTES   ││
│  │  CALLS      │     │  SYSTEM    │     │  RECEIVES  │     │ ENTERED   ││
│  │             │     │            │     │  CALL      │     │           ││
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────────┘│
│                                                                             │
│  IVR FLOW:                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  "Welcome to XYZ Travel! To help us serve you better..."           │   │
│  │                                                                     │   │
│  │  Press 1 for new inquiry                                           │   │
│  │  Press 2 for existing booking                                       │   │
│  │  Press 3 for support                                               │   │
│  │                                                                     │   │
│  │  [For new inquiry]                                                  │   │
│  │  "Please tell us: Where would you like to travel?"                 │   │
│  │  [Record customer response]                                        │   │
│  │                                                                     │   │
│  │  "When are you planning to travel?"                                 │   │
│  │  [Record customer response]                                        │   │
│  │                                                                     │   │
│  │  "How many people will be traveling?"                               │   │
│  │  [Record customer response]                                        │   │
│  │                                                                     │   │
│  │  [Route to agent with collected data]                              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MODE 2: AGENT CALL NOTES                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  After call, agent enters notes into quick-entry form:             │   │
│  │                                                                     │   │
│  │  Call Summary:                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │ Destination: [Dropdown + Text]                               │   │   │
│  │  │ Dates: [Date picker]                                          │   │   │
│  │  │ Travelers: [Number input]                                     │   │   │
│  │  │ Budget: [Number input]                                        │   │   │
│  │  │ Notes: [Textarea]                                             │   │   │
│  │  │                                                             │   │   │
│  │  │ ☑ Call recording attached (auto-transcribe)                  │   │   │
│  │  │                                                             │   │   │
│  │  │ [Create Inquiry] [Attach to Existing]                         │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phone Call Handler

```typescript
// Phone/VoIP Handler
interface CallWebhookPayload {
  CallSid: string;
  From: string;
  To: string;
  CallStatus: string;
  Direction: string;
  StartTime?: string;
  EndTime?: string;
  Duration?: string;
  RecordingUrl?: string;
  transcription?: string;
}

class PhoneHandler {
  private kafkaProducer: Producer;
  private speechToText: SpeechToTextService;

  constructor() {
    this.kafkaProducer = createKafkaProducer();
    this.speechToText = new SpeechToTextService();
  }

  async handleCallStatusChange(payload: CallWebhookPayload): Promise<void> {
    if (payload.CallStatus !== 'completed') {
      return; // Only process completed calls
    }

    // 1. Download recording if available
    let transcription = payload.transcription;
    if (payload.RecordingUrl && !transcription) {
      transcription = await this.transcribeRecording(payload.RecordingUrl);
    }

    // 2. Extract customer phone
    const customerPhone = this.normalizePhone(payload.From);

    // 3. Create normalized message
    const normalizedMessage: NormalizedMessage = {
      id: payload.CallSid,
      channel: 'phone',
      timestamp: new Date(),
      customer: { phone: customerPhone },
      text: transcription || 'Phone call (no transcription available)',
      language: this.detectLanguage(transcription),
      attachments: payload.RecordingUrl ? [{
        id: generateId(),
        type: 'audio',
        mimeType: 'audio/mpeg',
        url: payload.RecordingUrl,
        extractedText: transcription
      }] : [],
      channelMetadata: {
        phone: {
          from: customerPhone,
          recordingUrl: payload.RecordingUrl,
          duration: payload.Duration
        }
      },
      processing: {
        receivedAt: new Date(payload.StartTime || Date.now()),
        normalizedAt: new Date()
      }
    };

    // 4. Publish to Kafka
    await this.kafkaProducer.send({
      topic: 'inbound-messages',
      messages: [{
        key: customerPhone,
        value: JSON.stringify(normalizedMessage),
        headers: {
          channel: 'phone',
          contentType: 'application/json'
        }
      }]
    });
  }

  async handleIVRInputs(inputs: Record<string, string>): Promise<void> {
    // Process IVR-collected data
    const ivrData: IVRData = {
      destination: inputs.destination || null,
      dates: inputs.dates || null,
      travelers: parseInt(inputs.travelers) || null,
      budget: inputs.budget ? parseFloat(inputs.budget) : null
    };

    // Create pre-extracted packet from IVR data
    // ... similar to web form handler
  }

  private async transcribeRecording(recordingUrl: string): Promise<string> {
    // Download recording
    const audioBuffer = await fetch(recordingUrl).then(r => r.arrayBuffer());

    // Use speech-to-text service
    const transcription = await this.speechToText.transcribe(
      Buffer.from(audioBuffer),
      { language: 'auto' }
    );

    return transcription.text;
  }

  private normalizePhone(phone: string): string {
    return phone.replace(/\D/g, ''); // Remove non-digits
  }

  private detectLanguage(text?: string): string {
    if (!text) return 'en';
    const hasHindi = /[ऀ-ॿ]/.test(text);
    return hasHindi ? 'hi' : 'en';
  }
}

// Speech-to-Text Service
class SpeechToTextService {
  // Use OpenAI Whisper, Google Speech-to-Text, or similar
  async transcribe(audio: Buffer, options: { language: string }): Promise<{
    text: string;
    confidence: number;
  }> {
    // Implementation depends on chosen service
    // Example with OpenAI Whisper:
    const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'multipart/form-data'
      },
      body: createFormData(audio, options)
    });

    return await response.json();
  }
}
```

---

## 6. Message Normalization

### Unified Message Format

```typescript
// All channels normalize to this common format
interface NormalizedMessage {
  // Identity
  id: string;
  channel: MessageChannel;
  timestamp: Date;

  // Customer identification
  customer: CustomerIdentifier;

  // Content
  text: string;
  html?: string;                     // For email
  language: string;

  // Attachments
  attachments: Attachment[];

  // Channel-specific metadata
  channelMetadata: ChannelMetadata;

  // Processing metadata
  processing: {
    receivedAt: Date;
    normalizedAt: Date;
    deduplicationKey?: string;
  };
}

type MessageChannel = 'whatsapp' | 'email' | 'web' | 'phone';

interface CustomerIdentifier {
  phone?: string;
  email?: string;
  name?: string;
  id?: string;                       // If known customer
}

interface ChannelMetadata {
  whatsapp?: {
    from: string;
    messageSid: string;
  };
  email?: {
    from: string;
    subject: string;
    threadId?: string;
    isForward?: boolean;
    signature?: string;
  };
  web?: {
    userAgent: string;
    referrer?: string;
  };
  phone?: {
    from: string;
    recordingUrl?: string;
    duration?: string;
    ivrInputs?: Record<string, string>;
  };
}
```

### Deduplication Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEDUPLICATION STRATEGY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DEDUPLICATION DIMENSIONS:                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. CUSTOMER + CONTENT HASH                                           │   │
│  │    Same customer sending similar content = duplicate                 │   │
│  │    Window: 1 hour                                                   │   │
│  │                                                                     │   │
│  │ 2. CHANNEL MESSAGE ID                                               │   │
│  │    Same message ID from webhook = exact duplicate                   │   │
│  │    Window: 24 hours                                                │   │
│  │                                                                     │   │
│  │ 3. THREAD CONTEXT (Email)                                           │   │
│  │    Messages in same thread within 30 minutes = related              │   │
│  │    Window: 30 minutes                                              │   │
│  │                                                                     │   │
│  │ 4. CROSS-CHANNEL DEDUPLICATION                                      │   │
│  │    Customer sent WhatsApp AND email with same inquiry               │   │
│  │    Window: 2 hours                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  HANDLING STRATEGIES:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Exact Duplicate:                                                    │   │
│  │  → Ignore, log as duplicate                                         │   │
│  │                                                                     │   │
│  │ Near Duplicate (similar content, same customer):                     │   │
│  │  → Link to original, append as follow-up                            │   │
│  │  → Don't create new packet                                           │   │
│  │                                                                     │   │
│  │ Related (same thread/conversation):                                  │   │
│  │  → Append to existing packet as additional info                     │   │
│  │  → Update timestamp and state                                        │   │
│  │                                                                     │   │
│  │ New Message:                                                         │   │
│  │  → Create new packet                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Media Processing

### Attachment Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       MEDIA PROCESSING PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INCOMING ATTACHMENT → DOWNLOAD → ANALYZE → EXTRACT → STORE                 │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│  │  ATTACHMENT │ ──▶ │  DOWNLOAD   │ ──▶ │  ANALYZE   │                 │
│  │  (Any type) │     │  FROM URL   │     │  TYPE      │                 │
│  └─────────────┘     └─────────────┘     └──────┬──────┘                 │
│                                                  │                         │
│                    ┌─────────────────────────────┼──────────────┐         │
│                    │                             │              │         │
│                    ▼                             ▼              ▼         │
│            ┌─────────────┐             ┌─────────────┐  ┌─────────────┐   │
│            │    IMAGE   │             │   DOCUMENT  │  │    AUDIO    │   │
│            │  PROCESSOR │             │  PROCESSOR  │  │  PROCESSOR  │   │
│            └─────┬───────┘             └─────┬───────┘  └─────┬───────┘   │
│                  │                         │                 │             │
│                  ▼                         ▼                 ▼             │
│            ┌─────────────┐             ┌─────────────┐  ┌─────────────┐   │
│            │    OCR     │             │   PDF       │  │  SPEECH-2-  │   │
│            │  (Tesseract)│             │   TEXT      │  │   TEXT     │   │
│            └─────┬───────┘             │   EXTRACT   │  │ (Whisper)  │   │
│                  │                     └─────┬───────┘  └─────┬───────┘   │
│                  │                           │                 │             │
│                  └───────────────────────────┴─────────────────┘             │
│                                    │                                       │
│                                    ▼                                       │
│                          ┌─────────────────────┐                           │
│                          │  EXTRACTED TEXT     │                           │
│                          │  (Added to message)  │                           │
│                          └─────────────────────┘                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Media Processing Implementation

```typescript
// Media Processing Service
class MediaProcessor {
  private s3Client: S3Client;
  private ocrEngine: OCREngine;
  private pdfExtractor: PDFExtractor;
  private speechToText: SpeechToTextService;

  async processAttachment(
    url: string,
    mimeType: string,
    filename?: string
  ): Promise<Attachment> {
    // 1. Download
    const buffer = await this.downloadMedia(url);

    // 2. Store in S3
    const s3Key = `${this.getMediaType(mimeType)}/${Date.now()}_${filename || 'file'}`;
    await this.uploadToS3(s3Key, buffer, mimeType);

    // 3. Extract text based on type
    let extractedText: string | undefined;
    switch (this.getMediaType(mimeType)) {
      case 'image':
        extractedText = await this.extractImageText(buffer);
        break;
      case 'document':
        extractedText = await this.extractDocumentText(buffer, mimeType);
        break;
      case 'audio':
        extractedText = await this.extractAudioText(buffer);
        break;
    }

    return {
      id: generateId(),
      type: this.getMediaType(mimeType),
      mimeType,
      url: getS3Url(s3Key),
      extractedText,
      metadata: {
        filename,
        size: buffer.length
      }
    };
  }

  private async extractImageText(buffer: Buffer): Promise<string> {
    // Use Tesseract.js or cloud OCR service
    const { data } = await Tesseract.recognize(buffer, 'eng+hin', {
      logger: m => console.log(m)
    });
    return data.text;
  }

  private async extractDocumentText(buffer: Buffer, mimeType: string): Promise<string> {
    if (mimeType === 'application/pdf') {
      // Extract text from PDF
      return await this.pdfExtractor.extractText(buffer);
    }
    // For other document types, use appropriate extractor
    return '';
  }

  private async extractAudioText(buffer: Buffer): Promise<string> {
    // Use Whisper or similar speech-to-text
    const result = await this.speechToText.transcribe(buffer, {
      language: 'auto'
    });
    return result.text;
  }

  private getMediaType(mimeType: string): 'image' | 'document' | 'audio' | 'video' {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.startsWith('video/')) return 'video';
    return 'document';
  }

  private async downloadMedia(url: string): Promise<Buffer> {
    const response = await fetch(url);
    return Buffer.from(await response.arrayBuffer());
  }

  private async uploadToS3(key: string, buffer: Buffer, contentType: string): Promise<void> {
    await this.s3Client.putObject({
      Bucket: process.env.S3_BUCKET,
      Key: key,
      Body: buffer,
      ContentType: contentType
    });
  }
}
```

---

## 8. Channel-Specific Features

### Feature Comparison Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CHANNEL FEATURE COMPARISON                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Feature           │ WhatsApp │ Email  │ Web   │ Phone               │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ Text messages     │    ✓     │   ✓    │   ✓   │  Transcript         │   │
│  │ Media (images)    │    ✓     │   ✓    │   ✓   │  ✗                 │   │
│  │ Media (audio)     │    ✓     │   ✗    │   ✗   │  Recording          │   │
│  │ Media (documents) │    ✓     │   ✓    │   ✓   │  ✗                 │   │
│  │ Quick replies     │    ✓     │   ✗    │   ✗   │  ✗                 │   │
│  │ Thread tracking   │    ✗     │   ✓    │   ✗   │  ✗                 │   │
│  │ Structured input  │    ✗     │   ✗    │   ✓   │  IVR               │   │
│  │ Real-time         │    ✓     │   ✗    │   ✓   │  ✓                 │   │
│  │ Async             │    ✓     │   ✓    │   ✓   │  ✗                 │   │
│  │ Read receipts      │    ✓     │   ✗    │   ✗   │  ✗                 │   │
│  │ Emojis/tones      │    ✓     │   Limited│  ✗   │  Voice tone         │   │
│  │ Template msgs     │    ✓     │   ✓    │   ✗   │  ✗                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  CHANNEL-SPECIFIC CAPABILITIES:                                            │
│                                                                             │
│  WHATSAPP:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Quick reply buttons for faster customer responses                │   │
│  │ • List messages for structured options                              │   │
│  │ • Location sharing for destination context                           │   │
│  │ • Catalog messages for package options                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  EMAIL:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Thread grouping for conversation history                          │   │
│  │ • Rich HTML formatting for itineraries                              │   │
│  │ • PDF attachments for detailed quotes                               │   │
│  │ • Signature detection and removal                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WEB:                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • Pre-validated structured input                                    │   │
│  │ • Progressive form with validation                                 │   │
│  │ • Real-time availability display                                   │   │
│  │ • Calendar integration for date selection                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PHONE:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ • IVR for basic data collection                                     │   │
│  │ • Call recording for quality assurance                              │   │
│  │ • Transcription for record-keeping                                 │   │
│  │ • Agent notes for post-call data entry                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Implementation Reference

### Channel Handler Factory

```typescript
// Channel Handler Factory
class ChannelHandlerFactory {
  private handlers: Map<MessageChannel, ChannelHandler>;

  constructor() {
    this.handlers = new Map([
      ['whatsapp', new WhatsAppHandler()],
      ['email', new EmailHandler()],
      ['web', new WebHandler()],
      ['phone', new PhoneHandler()]
    ]);
  }

  getHandler(channel: MessageChannel): ChannelHandler {
    const handler = this.handlers.get(channel);
    if (!handler) {
      throw new Error(`No handler for channel: ${channel}`);
    }
    return handler;
  }

  async handleMessage(
    channel: MessageChannel,
    payload: unknown
  ): Promise<NormalizedMessage> {
    const handler = this.getHandler(channel);
    return await handler.handle(payload);
  }
}

// Generic Channel Handler Interface
interface ChannelHandler {
  handle(payload: unknown): Promise<NormalizedMessage>;
  sendMessage(to: string, content: MessageContent): Promise<string>;
}

// Unified Webhook Handler
async function handleChannelWebhook(
  req: Request,
  res: Response
): Promise<void> {
  const channel = req.params.channel as MessageChannel;
  const factory = new ChannelHandlerFactory();

  try {
    const normalizedMessage = await factory.handleMessage(channel, req.body);

    // Publish to Kafka
    await kafkaProducer.send({
      topic: 'inbound-messages',
      messages: [{
        key: normalizedMessage.customer.email || normalizedMessage.customer.phone,
        value: JSON.stringify(normalizedMessage),
        headers: {
          channel,
          contentType: 'application/json'
        }
      }]
    });

    res.status(200).json({ success: true, messageId: normalizedMessage.id });
  } catch (error) {
    console.error('Channel webhook error:', error);
    res.status(500).json({ error: 'Processing failed' });
  }
}

// Route setup
const app = express();
app.post('/webhooks/:channel', handleChannelWebhook);

// Routes:
// POST /webhooks/whatsapp - Twilio webhook
// POST /webhooks/email    - SendGrid webhook
// POST /webhooks/phone    - Exotel webhook
// (Web forms go to /api/v1/inquiries/web)
```

---

## Summary

Channel integration enables customers to reach out through their preferred medium:

1. **WhatsApp (60%)**: Real-time, media-rich, high engagement, quick replies
2. **Email (25%)**: Threaded conversations, detailed attachments, formal documentation
3. **Web (10%)**: Structured input, pre-validated, fastest processing path
4. **Phone (5%)**: Personal touch, IVR data collection, call recording

**Key Integration Points**:
- Unified message format across all channels
- Kafka message bus for reliable processing
- Media processing (OCR, STT, PDF extraction)
- Deduplication and thread detection
- Channel-specific optimizations (templates, quick replies)

**Success Metrics**:
- Message processing latency: <5 seconds
- Channel uptime: >99.5%
- Media extraction accuracy: >90%
- Deduplication accuracy: >95%

---

**Next Document:** INTAKE_04_EXTRACTION_QUALITY_DEEP_DIVE.md — Extraction accuracy, error patterns, and continuous improvement
