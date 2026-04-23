# Output Panel 13: Complete API Specification

> Comprehensive API specification for bundle generation, delivery, and management

---

## Part 1: API Overview

### 1.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTPUT PANEL API ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FRONTEND LAYER                                                      │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • OutputPanel.tsx (React Component)                                 │   │
│  │  • api-client.ts (HTTP Client)                                       │   │
│  │  • types/api.ts (TypeScript Interfaces)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  API GATEWAY LAYER                                                  │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Authentication (JWT)                                             │   │
│  │  • Rate Limiting                                                    │   │
│  │  • Request Validation                                               │   │
│  │  • Response Formatting                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  BUNDLE GENERATION SERVICE                                          │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  POST /api/bundles/generate                                         │   │
│  │  GET  /api/bundles/:id                                              │   │
│  │  GET  /api/bundles/:id/download                                     │   │
│  │  GET  /api/bundles/:id/status                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TEMPLATE ENGINE                                                     │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Handlebars Compiler                                               │   │
│  │  • Template Resolver                                                 │   │
│  │  • Helper Registry                                                   │   │
│  │  • Component Library                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PDF GENERATION SERVICE                                             │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Puppeteer (Headless Chrome)                                      │   │
│  │  • HTML to PDF Conversion                                           │   │
│  │  • Storage (S3/Local)                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  DELIVERY SERVICE                                                    │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • Email Service (SendGrid/SES)                                     │   │
│  │  • WhatsApp Business API                                            │   │
│  │  • Portal Storage                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Base URL

```
Production:  https://api.travelagency.com/v1
Staging:     https://api-staging.travelagency.com/v1
Development: http://localhost:8000/v1
```

### 1.3 Authentication

```
Authorization: Bearer <JWT_TOKEN>

Header Format:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Part 2: Bundle Generation Endpoints

### 2.1 Generate Bundle

**Endpoint:** `POST /api/bundles/generate`

**Description:** Generate a new bundle document (quote, itinerary, voucher, invoice, etc.)

**Authentication:** Required

**Request Headers:**
```http
Content-Type: application/json
Authorization: Bearer <token>
X-Request-ID: <uuid>
```

**Request Body:**

```typescript
interface GenerateBundleRequest {
  // Bundle specification
  bundleType: BundleType;
  tripId: string;

  // Template options
  template?: {
    variant?: string;           // e.g., "honeymoon", "corporate"
    customTemplateId?: string;  // For one-off customizations
  };

  // Delivery options
  delivery: {
    channels: DeliveryChannel[];
    recipientEmail?: string;
    recipientPhone?: string;
    scheduleAt?: Date;          // For scheduled delivery
    message?: string;           // Custom message for delivery
  };

  // Format options
  format: {
    output: 'PDF' | 'HTML' | 'BOTH';
    pdfOptions?: {
      pageSize?: 'A4' | 'LETTER';
      orientation?: 'PORTRAIT' | 'LANDSCAPE';
      watermark?: boolean;
    };
  };

  // Personalization options
  personalization?: {
    level: 'NONE' | 'BASIC' | 'ADVANCED';
    customerPreferences?: Record<string, any>;
  };
}

type BundleType =
  | 'QUOTE'
  | 'PRE_BOOKING'
  | 'ITINERARY'
  | 'VOUCHER'
  | 'INVOICE'
  | 'E_TICKET'
  | 'VISA_DOCS'
  | 'INSURANCE_CERT'
  | 'TRAVEL_ALERT'
  | 'BOOKING_SHEET'
  | 'COMMISSION_SHEET'
  | 'VENDOR_PO';

type DeliveryChannel = 'EMAIL' | 'WHATSAPP' | 'PORTAL' | 'SMS';
```

**Example Request:**

```json
{
  "bundleType": "ITINERARY",
  "tripId": "trip_abc123",
  "template": {
    "variant": "honeymoon"
  },
  "delivery": {
    "channels": ["WHATSAPP", "EMAIL", "PORTAL"],
    "recipientEmail": "customer@example.com",
    "recipientPhone": "+919876543210",
    "message": "Your travel itinerary is ready!"
  },
  "format": {
    "output": "BOTH",
    "pdfOptions": {
      "pageSize": "A4",
      "orientation": "PORTRAIT"
    }
  },
  "personalization": {
    "level": "ADVANCED"
  }
}
```

**Response (200 OK):**

```typescript
interface GenerateBundleResponse {
  success: true;
  data: {
    bundleId: string;
    bundleNumber: string;
    bundleType: BundleType;
    status: 'GENERATING' | 'COMPLETED' | 'FAILED';
    downloadUrls: {
      pdf?: string;
      html?: string;
    };
    deliveryStatus: {
      [channel: string]: {
        status: 'PENDING' | 'SENT' | 'DELIVERED' | 'FAILED';
        messageId?: string;
        error?: string;
      };
    };
    metadata: {
      generatedAt: Date;
      expiresAt?: Date;
      size: {
        pdfBytes?: number;
        htmlBytes?: number;
      };
    };
  };
}
```

**Example Response:**

```json
{
  "success": true,
  "data": {
    "bundleId": "bun_345def678",
    "bundleNumber": "ITIN-2024-001234",
    "bundleType": "ITINERARY",
    "status": "COMPLETED",
    "downloadUrls": {
      "pdf": "https://cdn.travelagency.com/bundles/bun_345def678.pdf",
      "html": "https://portal.travelagency.com/bundles/bun_345def678"
    },
    "deliveryStatus": {
      "WHATSAPP": {
        "status": "SENT",
        "messageId": "wamid.xxx"
      },
      "EMAIL": {
        "status": "SENT",
        "messageId": "msg_abc123"
      },
      "PORTAL": {
        "status": "DELIVERED"
      }
    },
    "metadata": {
      "generatedAt": "2024-12-15T10:30:00Z",
      "expiresAt": "2025-01-25T23:59:59Z",
      "size": {
        "pdfBytes": 245760,
        "htmlBytes": 45678
      }
    }
  }
}
```

**Error Responses:**

| Code | Description | Response |
|------|-------------|----------|
| 400 | Bad Request | Invalid request body |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Trip not found |
| 422 | Unprocessable Entity | Trip data incomplete |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Generation failed |

---

### 2.2 Get Bundle Status

**Endpoint:** `GET /api/bundles/:bundleId/status`

**Description:** Check the generation and delivery status of a bundle

**Authentication:** Required

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| bundleId | string | Bundle identifier |

**Response (200 OK):**

```typescript
interface BundleStatusResponse {
  success: true;
  data: {
    bundleId: string;
    bundleNumber: string;
    bundleType: BundleType;
    status: 'GENERATING' | 'COMPLETED' | 'FAILED' | 'EXPIRED';
    progress: {
      current: number;
      total: number;
      percentage: number;
      currentStep: string;
    };
    generation: {
      startedAt: Date;
      completedAt?: Date;
      error?: string;
    };
    delivery: {
      [channel: string]: {
        status: 'PENDING' | 'QUEUED' | 'SENDING' | 'SENT' | 'DELIVERED' | 'FAILED';
        sentAt?: Date;
        deliveredAt?: Date;
        error?: string;
        metrics?: {
          opened?: boolean;
          openedAt?: Date;
          clicked?: boolean;
        };
      };
    };
  };
}
```

---

### 2.3 Get Bundle Details

**Endpoint:** `GET /api/bundles/:bundleId`

**Description:** Retrieve complete bundle details including metadata

**Authentication:** Required

**Response (200 OK):**

```typescript
interface BundleDetailsResponse {
  success: true;
  data: {
    bundle: {
      id: string;
      number: string;
      type: BundleType;
      status: string;
      tripId: string;
      tripReference: string;
    };
    template: {
      id: string;
      name: string;
      variant?: string;
    };
    generation: {
      generatedAt: Date;
      generatedBy: string;
      expiresAt?: Date;
    };
    delivery: {
      channels: DeliveryChannel[];
      recipients: {
        email?: string;
        phone?: string;
      };
      history: DeliveryEvent[];
    };
    files: {
      pdf?: {
        url: string;
        size: number;
        hash: string;
      };
      html?: {
        url: string;
        size: number;
      };
    };
    personalization: {
      level: string;
      applied: string[];
    };
  };
}

interface DeliveryEvent {
  timestamp: Date;
  channel: DeliveryChannel;
  event: 'QUEUED' | 'SENT' | 'DELIVERED' | 'OPENED' | 'FAILED';
  details?: string;
}
```

---

### 2.4 Download Bundle

**Endpoint:** `GET /api/bundles/:bundleId/download`

**Description:** Download bundle file (PDF or HTML)

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | No | `pdf` or `html` (default: `pdf`) |

**Response (200 OK):**
- Content-Type: `application/pdf` (for PDF)
- Content-Type: `text/html` (for HTML)
- Content-Disposition: `attachment; filename="<filename>"`

---

### 2.5 List Bundles

**Endpoint:** `GET /api/bundles`

**Description:** List bundles with filtering and pagination

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tripId | string | No | Filter by trip |
| bundleType | string | No | Filter by bundle type |
| status | string | No | Filter by status |
| fromDate | date | No | Filter generated after |
| toDate | date | No | Filter generated before |
| page | number | No | Page number (default: 1) |
| limit | number | No | Items per page (default: 20, max: 100) |
| sortBy | string | No | Sort field (default: `generatedAt`) |
| sortOrder | string | No | `asc` or `desc` (default: `desc`) |

**Response (200 OK):**

```typescript
interface ListBundlesResponse {
  success: true;
  data: {
    bundles: BundleSummary[];
    pagination: {
      page: number;
      limit: number;
      total: number;
      totalPages: number;
      hasNext: boolean;
      hasPrev: boolean;
    };
  };
}

interface BundleSummary {
  id: string;
  number: string;
  type: BundleType;
  status: string;
  tripId: string;
  destination: string;
  travelDates: {
    from: Date;
    to: Date;
  };
  generatedAt: Date;
  expiresAt?: Date;
  deliveryStatus: Record<string, string>;
}
```

---

### 2.6 Regenerate Bundle

**Endpoint:** `POST /api/bundles/:bundleId/regenerate`

**Description:** Regenerate an existing bundle with current trip data

**Authentication:** Required

**Request Body:**

```typescript
interface RegenerateBundleRequest {
  reason?: string;              // Optional reason for regeneration
  force?: boolean;              // Override if recently generated
  delivery?: {
    channels?: DeliveryChannel[];
    message?: string;
  };
}
```

**Response (200 OK):** Same as GenerateBundleResponse

---

### 2.7 Cancel Bundle Delivery

**Endpoint:** `POST /api/bundles/:bundleId/cancel`

**Description:** Cancel pending delivery of a bundle

**Authentication:** Required

**Request Body:**

```typescript
interface CancelBundleRequest {
  reason: string;
  channels?: DeliveryChannel[]; // Specific channels to cancel
}
```

**Response (200 OK):**

```typescript
interface CancelBundleResponse {
  success: true;
  data: {
    bundleId: string;
    cancelledAt: Date;
    channels: DeliveryChannel[];
    status: 'CANCELLED';
  };
}
```

---

### 2.8 Resend Bundle

**Endpoint:** `POST /api/bundles/:bundleId/resend`

**Description:** Resend a bundle to specified channels

**Authentication:** Required

**Request Body:**

```typescript
interface ResendBundleRequest {
  channels: DeliveryChannel[];
  recipients?: {
    email?: string;
    phone?: string;
  };
  message?: string;
}
```

**Response (200 OK):** Same as GenerateBundleResponse

---

## Part 3: Template Management Endpoints

### 3.1 List Templates

**Endpoint:** `GET /api/templates`

**Description:** List available templates

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| bundleType | string | No | Filter by bundle type |
| category | string | No | Filter by category |
| agency | boolean | No | Include agency templates |

**Response (200 OK):**

```typescript
interface ListTemplatesResponse {
  success: true;
  data: {
    templates: TemplateSummary[];
  };
}

interface TemplateSummary {
  id: string;
  name: string;
  bundleType: BundleType;
  category: 'SYSTEM' | 'AGENCY' | 'CUSTOM';
  variant?: string;
  description?: string;
  preview?: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

---

### 3.2 Get Template Details

**Endpoint:** `GET /api/templates/:templateId`

**Description:** Get template details and source

**Authentication:** Required

**Response (200 OK):**

```typescript
interface TemplateDetailsResponse {
  success: true;
  data: {
    template: {
      id: string;
      name: string;
      bundleType: BundleType;
      category: string;
      variant?: string;
      description?: string;
      source: {
        html: string;
        css?: string;
      };
      variables: TemplateVariable[];
      components: string[];
      dependencies: string[];
      version: number;
      isActive: boolean;
    };
  };
}

interface TemplateVariable {
  name: string;
  type: 'string' | 'number' | 'date' | 'boolean' | 'array' | 'object';
  required: boolean;
  description?: string;
  defaultValue?: any;
}
```

---

### 3.3 Create Custom Template

**Endpoint:** `POST /api/templates`

**Description:** Create a custom template for an agency

**Authentication:** Required (Admin/Agency Owner only)

**Request Body:**

```typescript
interface CreateTemplateRequest {
  name: string;
  bundleType: BundleType;
  variant?: string;
  description?: string;
  source: {
    html: string;
    css?: string;
  };
  isActive?: boolean;
}
```

**Response (201 Created):**

```typescript
interface CreateTemplateResponse {
  success: true;
  data: {
    template: TemplateDetailsResponse['data']['template'];
  };
}
```

---

### 3.4 Update Template

**Endpoint:** `PUT /api/templates/:templateId`

**Description:** Update an existing template

**Authentication:** Required (Admin/Agency Owner only)

**Request Body:** Same as CreateTemplateRequest

**Response (200 OK):** Same as CreateTemplateResponse

---

### 3.5 Delete Template

**Endpoint:** `DELETE /api/templates/:templateId`

**Description:** Delete a custom template

**Authentication:** Required (Admin/Agency Owner only)

**Response (200 OK):**

```typescript
interface DeleteTemplateResponse {
  success: true;
  data: {
    deletedId: string;
    deletedAt: Date;
  };
}
```

---

## Part 4: Delivery Endpoints

### 4.1 Send to WhatsApp

**Endpoint:** `POST /api/delivery/whatsapp`

**Description:** Send bundle via WhatsApp Business API

**Authentication:** Required

**Request Body:**

```typescript
interface WhatsAppDeliveryRequest {
  bundleId: string;
  recipientPhone: string;       // E.164 format
  message?: string;
  mediaType?: 'DOCUMENT' | 'IMAGE';
}

interface WhatsAppDeliveryResponse {
  success: true;
  data: {
    messageId: string;
    status: 'QUEUED' | 'SENT';
    deliveredAt?: Date;
  };
}
```

---

### 4.2 Send to Email

**Endpoint:** `POST /api/delivery/email`

**Description:** Send bundle via email

**Authentication:** Required

**Request Body:**

```typescript
interface EmailDeliveryRequest {
  bundleId: string;
  recipientEmail: string;
  subject?: string;
  message?: string;
  attachments?: {
    includePdf: boolean;
    includeHtml: boolean;
  };
  cc?: string[];
  bcc?: string[];
}

interface EmailDeliveryResponse {
  success: true;
  data: {
    messageId: string;
    status: 'QUEUED' | 'SENT';
  };
}
```

---

### 4.3 Get Delivery Status

**Endpoint:** `GET /api/delivery/:messageId/status`

**Description:** Check delivery status of a specific message

**Authentication:** Required

**Response (200 OK):**

```typescript
interface DeliveryStatusResponse {
  success: true;
  data: {
    messageId: string;
    channel: DeliveryChannel;
    status: 'QUEUED' | 'SENT' | 'DELIVERED' | 'OPENED' | 'FAILED';
    sentAt?: Date;
    deliveredAt?: Date;
    openedAt?: Date;
    error?: string;
    metrics?: {
      opens?: number;
      clicks?: number;
    };
  };
}
```

---

## Part 5: Webhook Endpoints

### 5.1 Register Webhook

**Endpoint:** `POST /api/webhooks`

**Description:** Register a webhook for bundle events

**Authentication:** Required (Admin only)

**Request Body:**

```typescript
interface RegisterWebhookRequest {
  url: string;
  events: WebhookEvent[];
  secret?: string;
  isActive?: boolean;
}

type WebhookEvent =
  | 'bundle.generated'
  | 'bundle.delivered'
  | 'bundle.opened'
  | 'bundle.failed'
  | 'delivery.sent'
  | 'delivery.delivered'
  | 'delivery.failed';
```

**Response (201 Created):**

```typescript
interface RegisterWebhookResponse {
  success: true;
  data: {
    webhook: {
      id: string;
      url: string;
      events: WebhookEvent[];
      secret: string;
      isActive: boolean;
      createdAt: Date;
    };
  };
}
```

---

### 5.2 List Webhooks

**Endpoint:** `GET /api/webhooks`

**Description:** List registered webhooks

**Authentication:** Required (Admin only)

**Response (200 OK):**

```typescript
interface ListWebhooksResponse {
  success: true;
  data: {
    webhooks: WebhookSummary[];
  };
}

interface WebhookSummary {
  id: string;
  url: string;
  events: WebhookEvent[];
  isActive: boolean;
  createdAt: Date;
  lastTriggered?: Date;
}
```

---

### 5.3 Delete Webhook

**Endpoint:** `DELETE /api/webhooks/:webhookId`

**Description:** Delete a webhook

**Authentication:** Required (Admin only)

**Response (200 OK):**

```typescript
interface DeleteWebhookResponse {
  success: true;
  data: {
    deletedId: string;
    deletedAt: Date;
  };
}
```

---

### 5.4 Webhook Payload Format

```typescript
interface WebhookPayload {
  eventId: string;
  event: WebhookEvent;
  timestamp: Date;
  data: {
    bundleId: string;
    bundleType: BundleType;
    tripId: string;
    status: string;
    [key: string]: any;
  };
}
```

**Example Webhook Payload:**

```json
{
  "eventId": "evt_abc123",
  "event": "bundle.delivered",
  "timestamp": "2024-12-15T10:35:00Z",
  "data": {
    "bundleId": "bun_345def678",
    "bundleType": "ITINERARY",
    "tripId": "trip_abc123",
    "status": "DELIVERED",
    "channel": "WHATSAPP",
    "recipient": "+919876543210",
    "deliveredAt": "2024-12-15T10:35:00Z"
  }
}
```

---

## Part 6: Analytics Endpoints

### 6.1 Get Bundle Analytics

**Endpoint:** `GET /api/analytics/bundles`

**Description:** Get aggregate statistics for bundles

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| fromDate | date | No | Start date |
| toDate | date | No | End date |
| bundleType | string | No | Filter by type |
| groupBy | string | No | Group results by field |

**Response (200 OK):**

```typescript
interface BundleAnalyticsResponse {
  success: true;
  data: {
    summary: {
      total: number;
      byType: Record<BundleType, number>;
      byStatus: Record<string, number>;
    };
    delivery: {
      byChannel: Record<string, {
        sent: number;
        delivered: number;
        failed: number;
        deliveryRate: number;
      }>;
    };
    engagement: {
      totalOpens: number;
      openRate: number;
      totalClicks: number;
      clickRate: number;
    };
    timing: {
      avgGenerationTime: number; // milliseconds
      avgDeliveryTime: number;
    };
  };
}
```

---

### 6.2 Get Bundle Funnel

**Endpoint:** `GET /api/analytics/bundles/funnel`

**Description:** Get conversion funnel for bundles

**Authentication:** Required

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| bundleType | string | No | Filter by type |
| period | string | No | `day`, `week`, `month` |

**Response (200 OK):**

```typescript
interface BundleFunnelResponse {
  success: true;
  data: {
    funnel: {
      generated: number;
      sent: number;
      delivered: number;
      opened: number;
      clicked: number;
    };
    conversionRates: {
      sentToGenerated: number;
      deliveredToSent: number;
      openedToDelivered: number;
      clickedToOpened: number;
    };
    timeline: FunnelTimelinePoint[];
  };
}

interface FunnelTimelinePoint {
  date: Date;
  generated: number;
  sent: number;
  delivered: number;
  opened: number;
}
```

---

## Part 7: Rate Limiting

### 7.1 Rate Limits

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RATE LIMITING TIERS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  FREE TIER                                                           │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • 100 requests/minute                                              │   │
│  │  • 1,000 requests/day                                               │   │
│  │  • 10,000 requests/month                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  PROFESSIONAL TIER                                                   │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • 500 requests/minute                                              │   │
│  │  • 10,000 requests/day                                              │   │
│  │  • 100,000 requests/month                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ENTERPRISE TIER                                                     │   │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │   │
│  │  • 2,000 requests/minute                                            │   │
│  │  • 50,000 requests/day                                              │   │
│  │  • 1,000,000 requests/month                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Rate Limit Headers

```http
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 497
X-RateLimit-Reset: 1702657200
```

### 7.3 Rate Limit Error Response

```http
HTTP/1.1 429 Too Many Requests

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "retryAfter": 60
  }
}
```

---

## Part 8: Error Codes Reference

### 8.1 Standard Error Codes

| Code | Name | Description |
|------|------|-------------|
| `INVALID_REQUEST` | 400 | Request body is invalid |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `UNPROCESSABLE_ENTITY` | 422 | Validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### 8.2 Bundle-Specific Error Codes

| Code | Description |
|------|-------------|
| `BUNDLE_TYPE_INVALID` | Invalid bundle type specified |
| `BUNDLE_TRIP_NOT_FOUND` | Trip not found |
| `BUNDLE_DATA_INCOMPLETE` | Trip data incomplete for generation |
| `BUNDLE_TEMPLATE_NOT_FOUND` | Template not found |
| `BUNDLE_GENERATION_FAILED` | Generation failed |
| `BUNDLE_DELIVERY_FAILED` | Delivery failed |
| `BUNDLE_EXPIRED` | Bundle has expired |
| `BUNDLE_ALREADY_EXISTS` | Bundle already exists with same parameters |

### 8.3 Template-Specific Error Codes

| Code | Description |
|------|-------------|
| `TEMPLATE_SYNTAX_ERROR` | Template has syntax errors |
| `TEMPLATE_COMPILE_ERROR` | Template compilation failed |
| `TEMPLATE_INVALID_VARIANT` | Invalid template variant |
| `TEMPLATE_DEPENDENCY_MISSING` | Required dependency missing |
| `TEMPLATE_VERSION_CONFLICT` | Version conflict detected |

### 8.4 Delivery-Specific Error Codes

| Code | Description |
|------|-------------|
| `DELIVERY_CHANNEL_INVALID` | Invalid delivery channel |
| `DELIVERY_RECIPIENT_INVALID` | Invalid recipient |
| `DELIVERY_QUOTA_EXCEEDED` | Delivery quota exceeded |
| `DELIVERY_PROVIDER_ERROR` | Provider error |
| `DELIVERY_MESSAGE_FAILED` | Message send failed |

---

## Part 9: Response Format

### 9.1 Success Response

```typescript
interface SuccessResponse<T> {
  success: true;
  data: T;
  metadata?: {
    requestId: string;
    timestamp: Date;
    version: string;
  };
}
```

### 9.2 Error Response

```typescript
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
    stack?: string; // Only in development
  };
  metadata?: {
    requestId: string;
    timestamp: Date;
  };
}
```

### 9.3 Pagination Response

```typescript
interface PaginatedResponse<T> {
  success: true;
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
    nextPage?: string;
    prevPage?: string;
  };
}
```

---

## Part 10: Client SDK Reference

### 10.1 JavaScript/TypeScript Client

```typescript
// Installation
// npm install @travelagency/output-client

import { OutputClient } from '@travelagency/output-client';

// Initialize client
const client = new OutputClient({
  apiKey: process.env.OUTPUT_API_KEY,
  baseURL: 'https://api.travelagency.com/v1',
  timeout: 30000,
});

// Generate bundle
const bundle = await client.bundles.generate({
  bundleType: 'ITINERARY',
  tripId: 'trip_abc123',
  delivery: {
    channels: ['WHATSAPP', 'EMAIL'],
    recipientEmail: 'customer@example.com',
    recipientPhone: '+919876543210',
  },
  format: {
    output: 'PDF',
  },
});

// Check status
const status = await client.bundles.getStatus(bundle.data.bundleId);

// Download
const pdf = await client.bundles.download(bundle.data.bundleId, 'pdf');

// List bundles
const bundles = await client.bundles.list({
  tripId: 'trip_abc123',
  bundleType: 'ITINERARY',
  page: 1,
  limit: 20,
});
```

### 10.2 React Hooks

```typescript
import { useBundleGenerate, useBundleStatus } from '@travelagency/output-react';

function GenerateItineraryButton({ tripId }: { tripId: string }) {
  const { generate, isLoading, error, data } = useBundleGenerate();

  const handleGenerate = async () => {
    await generate({
      bundleType: 'ITINERARY',
      tripId,
      delivery: {
        channels: ['PORTAL'],
      },
    });
  };

  return (
    <button onClick={handleGenerate} disabled={isLoading}>
      {isLoading ? 'Generating...' : 'Generate Itinerary'}
    </button>
  );
}

function BundleStatus({ bundleId }: { bundleId: string }) {
  const { status, isLoading } = useBundleStatus(bundleId);

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <p>Status: {status?.data.status}</p>
      <p>Progress: {status?.data.progress.percentage}%</p>
    </div>
  );
}
```

---

## Summary

This API specification provides:

1. **API Overview** — Architecture, base URL, authentication
2. **Bundle Generation** — Generate, status, details, download, list, regenerate, cancel, resend
3. **Template Management** — List, get details, create, update, delete templates
4. **Delivery** — WhatsApp, email, status check
5. **Webhooks** — Register, list, delete webhooks, payload format
6. **Analytics** — Bundle stats, funnel metrics
7. **Rate Limiting** — Tiers, headers, error handling
8. **Error Codes** — Standard, bundle-specific, template, delivery codes
9. **Response Format** — Success, error, pagination formats
10. **Client SDK** — JavaScript client and React hooks

**Next Document**: OUTPUT_14_TESTING_SCENARIOS_COMPLETE.md — Complete testing scenarios and test cases

---

**Document**: OUTPUT_13_API_SPECIFICATION_COMPLETE.md
**Series**: Output Panel & Bundle Generation Deep Dive
**Status**: ✅ Complete
**Last Updated**: 2026-04-23
