# Multi-Brand & White Label — Architecture & Strategy

> Research document for white-label platform architecture, multi-brand management, and platform extensibility.

---

## Key Questions

1. **What's the white-label platform architecture?**
2. **What's configurable vs. fixed in a white-label deployment?**
3. **How do we manage multiple brands on a single codebase?**
4. **What's the tenant isolation model?**
5. **How do we handle custom domains and branding?**

---

## Research Areas

### White-Label Model

```typescript
interface WhiteLabelConfig {
  brandId: string;
  brandName: string;
  domain: string;                    // custom.agency.com or agency.travelapp.com
  branding: BrandingConfig;
  features: FeatureConfig;
  customization: CustomizationConfig;
  integrations: IntegrationConfig;
  limits: UsageLimits;
}

interface BrandingConfig {
  logo: string;                      // Primary logo (light/dark variants)
  favicon: string;
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  borderRadius: 'none' | 'small' | 'medium' | 'large' | 'pill';
  emailTemplates: {
    header: string;                  // Custom email header HTML
    footer: string;
    senderName: string;
    senderEmail: string;
  };
  documentTemplates: {
    header: string;                  // Itinerary/quote header
    footer: string;
    watermark?: string;
  };
  loginPage: {
    backgroundImage?: string;
    welcomeText: string;
    supportEmail: string;
    supportPhone: string;
  };
}

// What's configurable (white-label):
// - Branding: Logo, colors, fonts, icons
// - Domain: Custom domain or subdomain
// - Email: Sender name, email templates, signatures
// - Documents: Itinerary headers, quote formatting, invoice layout
// - Features: Enable/disable platform features
// - Workflows: Custom approval flows, pricing rules
// - Integrations: Choose which supplier APIs to connect
// - Support: Contact details, help center URL
//
// What's fixed (platform):
// - Core architecture (Next.js + Python spine)
// - Database schema (shared structure, isolated data)
// - Security model (authentication, encryption)
// - API structure (same endpoints, branded responses)
// - Updates and maintenance (platform-managed)
```

### Multi-Tenant Architecture

```typescript
interface TenantModel {
  isolation: TenantIsolation;
  database: DatabaseStrategy;
  storage: StorageStrategy;
  caching: CacheStrategy;
}

type TenantIsolation =
  | 'schema_per_tenant'              // Separate DB schema per agency
  | 'database_per_tenant'            // Separate DB instance per agency
  | 'shared_with_row_level';         // Shared DB, tenant_id on every row

// Recommended: shared_with_row_level security (RLS)
// Pros: Lower cost, easier maintenance, simpler backups
// Cons: Requires strict row-level security
// Suitable for: SaaS platform with many small-to-medium agencies

// Alternative: schema_per_tenant
// Pros: Stronger isolation, per-tenant backups
// Cons: Higher cost, migration complexity
// Suitable for: Enterprise agencies with compliance requirements

// Tenant context propagation:
// Every request carries tenant_id:
// - JWT token contains tenant_id
// - API middleware injects tenant_id into all queries
// - Database queries automatically filtered by tenant_id
// - File storage namespaced by tenant_id
// - Cache keys prefixed with tenant_id

// Custom domain handling:
// 1. Agency registers custom domain (travel.acme.com)
//   2. DNS CNAME points to platform (travel.acme.com → platform.travelapp.com)
// 3. SSL certificate provisioned (Let's Encrypt auto-renewal)
// 4. Brand config loaded based on domain
// 5. All URLs, emails, documents use custom domain

// Feature flags per tenant:
interface FeatureConfig {
  enabledModules: string[];          // ['flights', 'hotels', 'activities', 'visa']
  enabledFeatures: Record<string, boolean>;
  customFeatures: Record<string, unknown>;
}

// Feature tiers:
// Starter: Basic trip building, WhatsApp, invoices (₹5,000/month)
// Professional: Full features, integrations, analytics (₹15,000/month)
// Enterprise: White-label, custom integrations, SLA (₹50,000/month)
```

### Usage Limits & Billing

```typescript
interface UsageLimits {
  agents: number;
  trips: number;                     // Per month
  storage: string;                   // "10GB"
  apiCalls: number;                  // Per month
  documents: number;                 // Per month
  customDomain: boolean;
  whiteLabel: boolean;
  supportLevel: 'email' | 'chat' | 'dedicated';
}

// Usage tracking:
interface UsageMetric {
  metric: string;
  current: number;
  limit: number;
  utilizationPercent: number;
  resetDate: Date;
}

// Billing model:
// Subscription: Monthly or annual (discount for annual)
// Per-agent pricing: ₹X per agent per month
// Per-trip pricing: ₹Y per completed trip
// Add-ons: Custom domain (₹2,000/mo), White label (₹10,000/mo)
// Overage: ₹Z per trip beyond plan limit

// Usage alerts:
// 80% utilization → Email notification
// 95% utilization → Dashboard warning, restrict new bookings
// 100% utilization → Block new bookings until upgrade or reset
```

---

## Open Problems

1. **Customization depth** — How much should agencies be able to customize? Deep customization = divergent codebases. Shallow customization = limited value.

2. **Data migration between tenants** — An agency wants to move from one white-label to another (or from hosted to self-hosted). Data portability across tenants is complex.

3. **Feature parity** — The platform adds a new feature. Does every tenant get it immediately, or do tenants opt-in? Breaking changes need careful rollout.

4. **Multi-language white-label** — An agency in Gujarat wants the platform in Gujarati. Translating the entire UI per tenant is expensive.

5. **Support scalability** — Supporting 100 white-label agencies is different from supporting 1 agency. Need self-service support and tiered SLAs.

---

## Next Steps

- [ ] Design white-label configuration model
- [ ] Build multi-tenant architecture with row-level security
- [ ] Create custom domain provisioning pipeline
- [ ] Design usage tracking and billing integration
- [ ] Study white-label platforms (Shopify Plus, HubSpot, WordPress multisite)
