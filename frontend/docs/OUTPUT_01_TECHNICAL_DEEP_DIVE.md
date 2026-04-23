# Output Panel: Technical Deep Dive

> Architecture, data models, template engine, and generation pipeline

---

## Part 1: System Overview

### The Output Problem

**Current State (Many Agencies):**
```
Manual quote creation:
- Copy-paste from Word templates
- Manually calculate prices
- Format in Excel/Google Docs
- Export to PDF
- Send via WhatsApp/Email
- No version control
- No branding consistency
- Error-prone
```

**Our Solution:**
```
Automated Bundle Generation:
- Template-driven documents
- Real-time pricing data
- One-click PDF generation
- Brand consistency enforced
- Version control built-in
- Multi-format output
- Personalization at scale
```

---

## Part 2: Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      BUNDLE GENERATION SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │
│  │   Workspace     │  │  Template       │  │  Pricing        │        │
│  │   Panel         │  │  Engine         │  │  Service        │        │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘        │
│           │                    │                    │                   │
│           └────────────────────┼────────────────────┘                   │
│                                ↓                                        │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                  Bundle Generation Service                   │      │
│  │                                                               │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │      │
│  │  │ Data        │  │ Template    │  │ Rendering   │         │      │
│  │  │ Collector   │→ │ Resolver    │→ │ Engine      │         │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │      │
│  │                                         ↓                    │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │      │
│  │  │ PDF         │  │ HTML        │  │ WhatsApp    │         │      │
│  │  │ Generator   │  │ Generator   │  │ Formatter   │         │      │
│  │  └─────────────┘  └─────────────┘  └─────────────┘         │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                ↓                                        │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │                    Storage & Delivery                       │      │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │      │
│  │  │ S3      │  │ Email   │  │ WhatsApp│  │ Portal  │       │      │
│  │  │ Storage │  │ Service │  │ API     │  │ Database│       │      │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Core Data Models

### 3.1 Bundle Definition

```typescript
interface Bundle {
  id: string;
  workspace_id: string;
  trip_id: string;
  
  // Bundle identity
  bundle_type: BundleType;
  bundle_subtype?: string;
  version: number;
  status: BundleStatus;
  
  // Template
  template_id: string;
  template_version: string;
  
  // Content
  data: BundleData;
  metadata: BundleMetadata;
  
  // Generated outputs
  outputs: BundleOutput[];
  
  // Delivery
  delivery: BundleDelivery;
  
  // Audit
  created_at: string;
  created_by: string;
  updated_at?: string;
  updated_by?: string;
  generated_at?: string;
}

type BundleType = 
  | 'quote'                    // Price quotation
  | 'proforma_invoice'         // Proforma for international
  | 'itinerary'                // Detailed itinerary
  | 'confirmation'             // Booking confirmation
  | 'voucher'                  // Individual vouchers
  | 'invoice'                  // Final invoice
  | 'receipt'                  // Payment receipt
  | 'contract'                 // Service contract
  | 'custom';                  // Custom document

type BundleStatus = 
  | 'draft'                   // Being edited
  | 'pending_review'          // Awaiting approval
  | 'approved'                // Ready to generate
  | 'generating'              // In progress
  | 'completed'               // Generated successfully
  | 'failed'                  // Generation failed
  | 'delivered'               // Sent to customer
  | 'expired';                // No longer valid
```

### 3.2 Bundle Data Schema

```typescript
interface BundleData {
  // Customer information
  customer: {
    name: string;
    email?: string;
    phone?: string;
    address?: Address;
  };
  
  // Trip information
  trip: {
    destination: string;
    destination_display?: string;
    trip_type?: string;
    dates: {
      departure: string;
      return: string;
      duration_days: number;
    };
    travelers: Traveler[];
    special_requests?: string[];
  };
  
  // Pricing (for quotes/invoices)
  pricing?: {
    currency: string;
    subtotal: number;
    taxes: {
      amount: number;
      breakdown?: TaxBreakdown[];
    };
    total: number;
    breakdown: PricingBreakdown[];
    payment_schedule?: PaymentSchedule[];
    inclusions?: string[];
    exclusions?: string[];
  };
  
  // Itinerary (for itineraries/vouchers)
  itinerary?: {
    days: ItineraryDay[];
    notes?: string[];
    tips?: string[];
  };
  
  // Bookings (for confirmations/vouchers)
  bookings?: Booking[];
  
  // Agency branding
  agency: {
    name: string;
    logo?: string;
    address?: Address;
    contact?: {
      email?: string;
      phone?: string;
      website?: string;
    };
    license_numbers?: string[];
  };
  
  // Terms and conditions
  terms?: {
    cancellation_policy?: string;
    payment_terms?: string;
    general_terms?: string;
    disclaimers?: string[];
  };
  
  // Custom fields
  custom?: Record<string, any>;
}
```

### 3.3 Template System

```typescript
interface Template {
  id: string;
  agency_id?: string;          // null = system default
  name: string;
  description?: string;
  
  // Template classification
  bundle_type: BundleType;
  bundle_subtype?: string;
  category: string;            // 'domestic', 'international', 'honeymoon', etc.
  
  // Template definition
  template_type: 'html' | 'markdown' | 'wysiwyg';
  content: TemplateContent;
  
  // Template configuration
  config: TemplateConfig;
  
  // Versioning
  version: string;
  parent_template_id?: string;  // For inheritance
  is_active: boolean;
  
  // Access control
  access: {
    is_public?: boolean;        // Available to all agencies?
    allowed_agencies?: string[]; // Specific agencies
  };
  
  // Audit
  created_at: string;
  created_by: string;
  updated_at?: string;
  updated_by?: string;
}

interface TemplateContent {
  // For HTML templates
  html?: string;
  
  // For Markdown templates
  markdown?: string;
  
  // For WYSIWYG
  blocks?: TemplateBlock[];
  
  // Common sections
  styles?: string;              // CSS
  header?: string;
  footer?: string;
  
  // Components (for modular templates)
  components?: {
    header?: string;
    pricing?: string;
    itinerary?: string;
    terms?: string;
    footer?: string;
  };
}

interface TemplateConfig {
  // Variables allowed in template
  variables?: TemplateVariable[];
  
  // Conditional sections
  conditionals?: TemplateConditional[];
  
  // Loops/repeatable sections
  loops?: TemplateLoop[];
  
  // PDF generation settings
  pdf?: {
    page_size?: 'A4' | 'letter';
    orientation?: 'portrait' | 'landscape';
    margins?: {
      top?: number;
      bottom?: number;
      left?: number;
      right?: number;
    };
    header_footer?: boolean;
    page_numbers?: boolean;
  };
  
  // Branding
  branding?: {
    primary_color?: string;
    secondary_color?: string;
    font_family?: string;
  };
}
```

### 3.4 Bundle Output

```typescript
interface BundleOutput {
  id: string;
  bundle_id: string;
  
  // Output format
  format: 'pdf' | 'html' | 'markdown' | 'json';
  
  // Storage
  storage: {
    type: 's3' | 'local' | 'cdn';
    location: string;
    url?: string;
    expires_at?: string;
  };
  
  // Metadata
  metadata: {
    size_bytes?: number;
    pages?: number;
    generated_at: string;
    generation_time_ms?: number;
  };
  
  // Preview (for HTML)
  preview?: {
    thumbnail_url?: string;
    first_page_url?: string;
  };
}
```

---

## Part 4: Database Schema

### 4.1 Bundles Table

```sql
CREATE TABLE bundles (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relations
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    
    -- Bundle identity
    bundle_type VARCHAR(50) NOT NULL,
    bundle_subtype VARCHAR(100),
    version INTEGER NOT NULL DEFAULT 1,
    status bundle_status NOT NULL DEFAULT 'draft',
    
    -- Template
    template_id UUID NOT NULL REFERENCES templates(id),
    template_version VARCHAR(20) NOT NULL,
    
    -- Content (JSONB for flexibility)
    data JSONB NOT NULL,
    metadata JSONB,
    
    -- Delivery tracking
    delivery JSONB,
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    updated_by UUID REFERENCES users(id),
    generated_at TIMESTAMPTZ,
    
    -- Indexes
    CONSTRAINT bundles_unique_version UNIQUE (trip_id, bundle_type, version)
);

-- Indexes
CREATE INDEX idx_bundles_workspace ON bundles(workspace_id);
CREATE INDEX idx_bundles_trip ON bundles(trip_id);
CREATE INDEX idx_bundles_type_status ON bundles(bundle_type, status);
CREATE INDEX idx_bundles_created ON bundles(created_at DESC);

-- GIN index for JSONB queries
CREATE INDEX idx_bundles_data ON bundles USING GIN (data);
CREATE INDEX idx_bundles_metadata ON bundles USING GIN (metadata);
```

### 4.2 Templates Table

```sql
CREATE TABLE templates (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Ownership
    agency_id UUID REFERENCES agencies(id) ON DELETE SET NULL,
    
    -- Template identity
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Classification
    bundle_type VARCHAR(50) NOT NULL,
    bundle_subtype VARCHAR(100),
    category VARCHAR(100),
    
    -- Template definition
    template_type VARCHAR(20) NOT NULL, -- 'html', 'markdown', 'wysiwyg'
    content JSONB NOT NULL,
    config JSONB,
    
    -- Versioning
    version VARCHAR(20) NOT NULL DEFAULT '1.0',
    parent_template_id UUID REFERENCES templates(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Access control
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    allowed_agencies UUID[],
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ,
    updated_by UUID REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT templates_unique_version UNIQUE (agency_id, bundle_type, version)
);

-- Indexes
CREATE INDEX idx_templates_agency ON templates(agency_id);
CREATE INDEX idx_templates_type ON templates(bundle_type);
CREATE INDEX idx_templates_active ON templates(is_active) WHERE is_active = TRUE;
```

### 4.3 Bundle Outputs Table

```sql
CREATE TABLE bundle_outputs (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relation
    bundle_id UUID NOT NULL REFERENCES bundles(id) ON DELETE CASCADE,
    
    -- Output format
    format VARCHAR(20) NOT NULL,
    
    -- Storage
    storage_type VARCHAR(20) NOT NULL,
    storage_location TEXT NOT NULL,
    storage_url TEXT,
    expires_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_bundle_outputs_bundle ON bundle_outputs(bundle_id);
CREATE INDEX idx_bundle_outputs_format ON bundle_outputs(format);
```

### 4.4 Bundle Deliveries Table

```sql
CREATE TABLE bundle_deliveries (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relation
    bundle_id UUID NOT NULL REFERENCES bundles(id) ON DELETE CASCADE,
    
    -- Delivery method
    delivery_method VARCHAR(20) NOT NULL, -- 'email', 'whatsapp', 'portal', 'download'
    
    -- Delivery details
    recipient_type VARCHAR(20) NOT NULL, -- 'customer', 'agent', 'other'
    recipient_info JSONB,
    
    -- Status
    status delivery_status NOT NULL DEFAULT 'pending',
    
    -- Tracking
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    
    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamp
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_bundle_deliveries_bundle ON bundle_deliveries(bundle_id);
CREATE INDEX idx_bundle_deliveries_status ON bundle_deliveries(status);
```

---

## Part 5: Template Engine Architecture

### 5.1 Template Resolution

```typescript
class TemplateResolver {
  async resolveTemplate(
    bundle_type: BundleType,
    agency_id: string,
    context: {
      destination?: string;
      trip_type?: string;
      custom_fields?: Record<string, any>;
    }
  ): Promise<Template> {
    // Priority order:
    // 1. Agency-specific template with matching category
    // 2. Agency-specific template (general)
    // 3. System template with matching category
    // 4. System default template
    
    const templates = await db.query(`
      SELECT * FROM templates
      WHERE bundle_type = $1
        AND is_active = true
      ORDER BY
        (agency_id = $2) DESC,
        category = $3 DESC,
        is_public DESC
      LIMIT 1
    `, [bundle_type, agency_id, context.category]);
    
    if (!templates[0]) {
      throw new TemplateNotFoundError(bundle_type, agency_id);
    }
    
    // If template has parent, merge with parent
    return await this.mergeWithParent(templates[0]);
  }
  
  private async mergeWithParent(template: Template): Promise<Template> {
    if (!template.parent_template_id) {
      return template;
    }
    
    const parent = await db.query(
      'SELECT * FROM templates WHERE id = $1',
      [template.parent_template_id]
    );
    
    if (!parent[0]) {
      return template;
    }
    
    // Merge content and config
    return {
      ...template,
      content: this.mergeContent(parent[0].content, template.content),
      config: {
        ...parent[0].config,
        ...template.config
      }
    };
  }
}
```

### 5.2 Template Rendering Engine

```typescript
interface TemplateRenderer {
  render(template: Template, data: BundleData): Promise<string>;
}

class HtmlTemplateRenderer implements TemplateRenderer {
  async render(template: Template, data: BundleData): Promise<string> {
    // Use Handlebars for HTML templates
    const handlebars = require('handlebars');
    
    // Register custom helpers
    this.registerHelpers(handlebars);
    
    // Compile template
    const compiled = handlebars.compile(template.content.html);
    
    // Render with data
    return compiled(data);
  }
  
  private registerHelpers(handlebars: any) {
    // Date formatting
    handlebars.registerHelper('formatDate', (date, format) => {
      return moment(date).format(format);
    });
    
    // Currency formatting
    handlebars.registerHelper('formatCurrency', (amount, currency) => {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency
      }).format(amount);
    });
    
    // Number formatting
    handlebars.registerHelper('formatNumber', (number, decimals = 0) => {
      return number.toLocaleString('en-IN', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      });
    });
    
    // Conditional display
    handlebars.registerHelper('ifEquals', (a, b, options) => {
      return a === b ? options.fn(this) : options.inverse(this);
    });
    
    // List joining
    handlebars.registerHelper('join', (array, separator) => {
      return array.join(separator);
    });
    
    // Pluralization
    handlebars.registerHelper('pluralize', (count, singular, plural) => {
      return count === 1 ? singular : plural;
    });
  }
}
```

---

## Part 6: PDF Generation

### 6.1 PDF Generation Pipeline

```typescript
class PDFGenerator {
  async generate(
    html: string,
    config: PDFConfig
  ): Promise<Buffer> {
    // Use Puppeteer for server-side PDF generation
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    // Set content
    await page.setContent(html, {
      waitUntil: 'networkidle0'
    });
    
    // Generate PDF
    const pdf = await page.pdf({
      format: config.page_size || 'A4',
      orientation: config.orientation || 'portrait',
      margin: {
        top: config.margins?.top || '20px',
        bottom: config.margins?.bottom || '20px',
        left: config.margins?.left || '20px',
        right: config.margins?.right || '20px'
      },
      printBackground: true,
      displayHeaderFooter: config.header_footer || false
    });
    
    await browser.close();
    
    return pdf;
  }
  
  async generateWithWatermark(
    html: string,
    config: PDFConfig,
    watermark: {
      text: string;
      opacity?: number;
      rotation?: number;
    }
  ): Promise<Buffer> {
    // Inject watermark CSS
    const watermarkCSS = `
      .watermark {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(${watermark.rotation || -45}deg);
        font-size: 100px;
        color: rgba(0, 0, 0, ${watermark.opacity || 0.1});
        pointer-events: none;
        z-index: -1;
        white-space: nowrap;
      }
    `;
    
    const htmlWithWatermark = html.replace(
      '</head>',
      `<style>${watermarkCSS}</style></head>`
    ).replace(
      '<body>',
      `<body><div class="watermark">${watermark.text}</div>`
    );
    
    return this.generate(htmlWithWatermark, config);
  }
}
```

### 6.2 PDF Optimization

```typescript
class PDFOptimizer {
  async optimize(pdf: Buffer): Promise<Buffer> {
    // Step 1: Compress images
    const compressed = await this.compressImages(pdf);
    
    // Step 2: Subset fonts
    const subsetting = await this.subsetFonts(compressed);
    
    // Step 3: Remove unused objects
    const cleaned = await this.removeUnusedObjects(subsetting);
    
    return cleaned;
  }
  
  private async compressImages(pdf: Buffer): Promise<Buffer> {
    // Extract images
    const images = await this.extractImages(pdf);
    
    // Compress each image
    const compressed = await Promise.all(
      images.map(async (img) => {
        return sharp(img.data)
          .jpeg({ quality: 80 })
          .toBuffer();
      })
    );
    
    // Replace images in PDF
    return this.replaceImages(pdf, images, compressed);
  }
}
```

---

## Part 7: WhatsApp Formatting

### 7.1 Message Formatter

```typescript
class WhatsAppMessageFormatter {
  formatForWhatsApp(bundle: Bundle, maxLength: number = 4096): string {
    const lines: string[] = [];
    
    // Header
    lines.push(this.formatHeader(bundle));
    lines.push(''); // Empty line
    
    // Trip details
    if (bundle.data.trip) {
      lines.push(this.formatTripDetails(bundle.data.trip));
      lines.push('');
    }
    
    // Pricing (if quote)
    if (bundle.data.pricing) {
      lines.push(this.formatPricing(bundle.data.pricing));
      lines.push('');
    }
    
    // Call to action
    lines.push(this.formatCTA(bundle));
    
    const message = lines.join('\n');
    
    // Truncate if too long
    if (message.length > maxLength) {
      return message.substring(0, maxLength - 3) + '...';
    }
    
    return message;
  }
  
  private formatHeader(bundle: Bundle): string {
    const stars = '✨';
    return `${stars} ${bundle.data.agency.name} ${stars}`;
  }
  
  private formatTripDetails(trip: any): string {
    const lines = [
      `📍 *${trip.destination_display || trip.destination}*`,
      `📅 ${this.formatDateRange(trip.dates)}`,
      `👥 ${trip.travelers.length} Traveler${trip.travelers.length > 1 ? 's' : ''}`
    ];
    
    return lines.join('\n');
  }
  
  private formatPricing(pricing: any): string {
    const lines = [
      '*💰 Pricing Details*',
      '',
      `Total: ${this.formatCurrency(pricing.total, pricing.currency)}`
    ];
    
    if (pricing.inclusions) {
      lines.push('');
      lines.push('*Includes:*');
      pricing.inclusions.forEach((inc: string) => {
        lines.push(`✓ ${inc}`);
      });
    }
    
    return lines.join('\n');
  }
}
```

---

## Part 8: Generation Pipeline

### 8.1 End-to-End Pipeline

```typescript
class BundleGenerationPipeline {
  async generate(request: GenerateBundleRequest): Promise<Bundle> {
    // Step 1: Resolve template
    const template = await this.templateResolver.resolve(
      request.bundle_type,
      request.agency_id,
      request.context
    );
    
    // Step 2: Collect data
    const data = await this.dataCollector.collect(request.trip_id);
    
    // Step 3: Merge with custom data
    const finalData = {
      ...data,
      ...request.custom_data
    };
    
    // Step 4: Create bundle record
    const bundle = await this.createBundle({
      workspace_id: request.workspace_id,
      trip_id: request.trip_id,
      bundle_type: request.bundle_type,
      template_id: template.id,
      template_version: template.version,
      data: finalData,
      status: 'generating'
    });
    
    // Step 5: Render template
    const rendered = await this.templateRenderer.render(template, finalData);
    
    // Step 6: Generate outputs
    const outputs = await this.generateOutputs(rendered, request.outputs);
    
    // Step 7: Update bundle
    await this.updateBundle(bundle.id, {
      outputs: outputs,
      status: 'completed',
      generated_at: new Date()
    });
    
    // Step 8: Deliver if requested
    if (request.delivery) {
      await this.deliver(bundle.id, request.delivery);
    }
    
    return bundle;
  }
  
  private async generateOutputs(
    rendered: string,
    formats: GenerateOutputRequest[]
  ): Promise<BundleOutput[]> {
    const outputs: BundleOutput[] = [];
    
    for (const format of formats) {
      switch (format.format) {
        case 'pdf':
          const pdf = await this.pdfGenerator.generate(rendered, format.config);
          const url = await this.storage.upload(pdf, 'application/pdf');
          outputs.push({
            id: generateId(),
            format: 'pdf',
            storage: { type: 's3', location: url.key, url: url.url },
            metadata: {
              size_bytes: pdf.length,
              generated_at: new Date().toISOString()
            }
          });
          break;
          
        case 'html':
          const htmlUrl = await this.storage.upload(
            Buffer.from(rendered),
            'text/html'
          );
          outputs.push({
            id: generateId(),
            format: 'html',
            storage: { type: 's3', location: htmlUrl.key, url: htmlUrl.url },
            metadata: { generated_at: new Date().toISOString() }
          });
          break;
      }
    }
    
    return outputs;
  }
}
```

---

## Part 9: Caching Strategy

### 9.1 Template Caching

```typescript
class TemplateCache {
  private cache: Map<string, { template: Template; expiresAt: number }>;
  
  async get(key: string): Promise<Template | null> {
    const cached = this.cache.get(key);
    
    if (!cached) {
      return null;
    }
    
    if (Date.now() > cached.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.template;
  }
  
  async set(key: string, template: Template, ttl: number = 3600000): Promise<void> {
    this.cache.set(key, {
      template,
      expiresAt: Date.now() + ttl
    });
  }
  
  invalidate(agency_id: string): void {
    for (const [key, cached] of this.cache.entries()) {
      if (cached.template.agency_id === agency_id) {
        this.cache.delete(key);
      }
    }
  }
}
```

### 9.2 Rendered Content Caching

```typescript
class RenderCache {
  private redis: Redis;
  
  async get(cacheKey: string): Promise<string | null> {
    return await this.redis.get(`render:${cacheKey}`);
  }
  
  async set(
    cacheKey: string,
    content: string,
    ttl: number = 3600
  ): Promise<void> {
    await this.redis.setex(`render:${cacheKey}`, ttl, content);
  }
  
  async invalidate(bundleId: string): Promise<void> {
    // Invalidate all cached renders for this bundle
    const pattern = `render:bundle:${bundleId}:*`;
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}
```

---

## Part 10: Performance Optimization

### 10.1 Generation Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Template resolution | <50ms | Time to fetch template |
| Data collection | <200ms | Time to collect trip data |
| Template rendering | <500ms | Time to render template |
| PDF generation | <2s | Time to generate PDF |
| Total generation | <3s | End-to-end time |

### 10.2 Optimization Techniques

```typescript
class BundleOptimizer {
  // 1. Parallel output generation
  async generateOutputsParallel(
    rendered: string,
    formats: GenerateOutputRequest[]
  ): Promise<BundleOutput[]> {
    return Promise.all(
      formats.map(format => this.generateOutput(rendered, format))
    );
  }
  
  // 2. Streaming for large documents
  async generateStream(
    template: Template,
    data: BundleData
  ): AsyncIterable<Buffer> {
    // For very large documents (100+ pages)
    // Generate page by page
  }
  
  // 3. Pre-rendering common sections
  async preRenderCommonSections(): Promise<void> {
    // Cache header, footer, terms sections
  }
}
```

---

## Summary

**Technical Architecture Summary:**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Template Engine** | Handlebars | Flexible templating |
| **PDF Generation** | Puppeteer | Server-side PDF |
| **Storage** | S3 | Document storage |
| **Cache** | Redis | Template & render cache |
| **Queue** | RedisMQ | Async generation |

**Key Design Decisions:**

1. **JSONB for flexible data** — accommodates varying bundle types
2. **Template inheritance** — agency customization on top of system defaults
3. **Async generation** — don't block user workflow
4. **Multiple output formats** — PDF, HTML, WhatsApp
5. **Version control** — track all bundle versions

**Scaling Considerations:**

| Scale | Strategy |
|-------|----------|
| 1000 bundles/day | Single server, synchronous |
| 10,000 bundles/day | Queue + worker pool |
| 100,000 bundles/day | Distributed generation, CDN |

---

**Status:** Technical deep dive complete.
**Version:** 1.0
**Last Updated:** 2026-04-23

**Next:** UX/UI Deep Dive (OUTPUT_02)
