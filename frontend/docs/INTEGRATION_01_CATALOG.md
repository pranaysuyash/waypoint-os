# Integration Hub & Connectors — Integration Catalog

> Research document for third-party integrations, connector architecture, and integration management.

---

## Key Questions

1. **What external systems must integrate with the travel platform?**
2. **What's the connector architecture for consistent integrations?**
3. **How do we manage API credentials and secrets?**
4. **What's the integration health monitoring model?**
5. **How do we handle breaking changes from third-party APIs?**

---

## Research Areas

### Integration Landscape

```typescript
type IntegrationCategory =
  | 'supplier_gds'                    // Amadeus, Sabre, Travelport
  | 'supplier_hotel'                  // Hotelbeds, Expedia TAAP, direct chains
  | 'supplier_activity'               // Viator, Klook, GetYourGuide
  | 'supplier_transfer'               // HolidayTaxis, Rome2Rio
  | 'payment_gateway'                 // Razorpay, PayU, Stripe
  | 'accounting'                      // Tally, Zoho Books, QuickBooks
  | 'crm'                             // Zoho CRM, Salesforce, HubSpot
  | 'communication'                   // WhatsApp Business, Twilio, SendGrid
  | 'document'                        // DocuSign, Adobe Sign, Google Docs
  | 'mapping'                         // Google Maps, Mapbox
  | 'weather'                         // OpenWeather, WeatherAPI
  | 'fraud_detection'                 // Signifyd, Riskified
  | 'analytics'                       // Google Analytics, Mixpanel
  | 'storage'                         // AWS S3, Google Cloud Storage
  | 'identity'                        // Aadhaar eKYC, DigiLocker
  | 'government';                     // GST portal, Income Tax, MEA

interface IntegrationCatalog {
  integrations: IntegrationEntry[];
  categories: Record<IntegrationCategory, string[]>;
}

interface IntegrationEntry {
  integrationId: string;
  name: string;
  category: IntegrationCategory;
  provider: string;
  status: 'available' | 'coming_soon' | 'beta' | 'deprecated';
  version: string;
  authType: AuthType;
  rateLimits: RateLimitInfo;
  documentation: string;
  connectorType: 'built_in' | 'marketplace' | 'custom';
}

// Priority integrations for Indian travel market:
// Tier 1 (Must-have): Amadeus GDS, Razorpay, WhatsApp Business, Tally
// Tier 2 (High-value): Hotelbeds, Zoho Books, Google Maps, SendGrid
// Tier 3 (Nice-to-have): Viator, Salesforce, DocuSign, Mixpanel
// Tier 4 (Future): Aadhaar eKYC, GST portal API, DigiLocker
```

### Connector Architecture

```typescript
interface Connector {
  connectorId: string;
  name: string;
  version: string;
  config: ConnectorConfig;
  capabilities: ConnectorCapability[];
  endpoints: ConnectorEndpoint[];
  transforms: DataTransform[];
  healthCheck: HealthCheckConfig;
}

interface ConnectorConfig {
  baseUrl: string;
  auth: AuthConfig;
  timeout: number;
  retryPolicy: RetryPolicy;
  rateLimitHandling: RateLimitHandling;
}

type AuthConfig =
  | { type: 'api_key'; headerName: string }
  | { type: 'oauth2'; tokenUrl: string; scopes: string[] }
  | { type: 'basic_auth' }
  | { type: 'bearer_token' }
  | { type: 'custom'; description: string };

interface ConnectorCapability {
  capability: string;                // 'search', 'book', 'cancel', 'modify', 'status'
  supported: boolean;
  limitations?: string[];
}

// Connector interface (what every connector must implement):
interface IConnector {
  // Authentication
  authenticate(): Promise<AuthResult>;
  refreshToken(): Promise<AuthResult>;

  // Standard operations
  search(params: SearchParams): Promise<SearchResult[]>;
  book(params: BookParams): Promise<BookResult>;
  cancel(params: CancelParams): Promise<CancelResult>;
  getStatus(id: string): Promise<StatusResult>;

  // Health
  healthCheck(): Promise<HealthResult>;
  getRateLimitStatus(): Promise<RateLimitInfo>;
}

// Transform layer:
// External API format → Internal canonical format
// Every connector has transforms for:
// - Request mapping (internal → external format)
// - Response mapping (external → internal format)
// - Error mapping (external error → internal AppError)
// - Webhook mapping (external event → internal event)
```

### Credential Management

```typescript
interface IntegrationCredential {
  credentialId: string;
  integrationId: string;
  agencyId: string;
  credentialType: CredentialType;
  encryptedValues: Record<string, string>;  // Encrypted at rest
  lastRotatedAt?: Date;
  rotationSchedule?: string;
  status: 'active' | 'expired' | 'invalid';
  lastValidatedAt?: Date;
}

type CredentialType =
  | 'api_key'
  | 'oauth2_client'
  | 'username_password'
  | 'certificate'
  | 'custom';

// Credential security:
// 1. All credentials encrypted at rest (AES-256)
// 2. Decrypted only when making API calls (in memory only)
// 3. Never logged, never exported, never shown in full in UI
// 4. UI shows masked version: "sk_live_****1234"
// 5. Rotation reminders for credentials older than 90 days
// 6. Automatic credential validation on save (test API call)
// 7. Audit log for credential access and changes
// 8. Integration-specific: some credentials are per-agency, some are shared

// Credential lifecycle:
// 1. Admin enters credentials in integration settings
// 2. System validates credentials (test API call)
// 3. Credentials encrypted and stored
// 4. Integration becomes available for use
// 5. Periodic validation (weekly) ensures credentials still work
// 6. On expiry → Alert admin to update
// 7. On compromise → Immediate revocation + alert
```

---

## Open Problems

1. **API versioning** — Third-party APIs update frequently (Amadeus v1 → v2). Breaking changes require connector updates. Need version management strategy.

2. **Rate limit diversity** — Every provider has different rate limits (Amadeus: 100/min, Hotelbeds: 200/min). Need per-connector rate limiting.

3. **Sandbox vs. production** — Connectors need to work in both sandbox (testing) and production modes. Switching should be seamless.

4. **Cost tracking** — Every API call may cost money (Amadeus charges per search). Need per-integration cost tracking and budgeting.

5. **Data ownership** — Data from supplier APIs (hotel descriptions, images) — who owns it? What can we cache vs. must we fetch fresh?

---

## Next Steps

- [ ] Design connector interface specification
- [ ] Build credential management with encryption
- [ ] Create integration catalog with provider documentation
- [ ] Design rate limiting per connector
- [ ] Study integration platforms (MuleSoft, Workato, Zapier)
