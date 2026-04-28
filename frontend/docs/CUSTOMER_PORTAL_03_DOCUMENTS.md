# Customer Self-Service — Document Access & Management

> Research document for customer-facing document access, download, and sharing.

---

## Key Questions

1. **What documents does the customer need access to, and when?**
2. **How do we make documents available offline (before travel)?**
3. **What's the document sharing model (traveler, family, agent)?**
4. **How do we handle document updates (revised itinerary)?**
5. **What's the security model for documents containing PII?**

---

## Research Areas

### Customer Document Library

```typescript
interface CustomerDocumentLibrary {
  tripId: string;
  documents: CustomerDocument[];
  categories: DocumentCategory[];
  lastUpdated: Date;
}

interface CustomerDocument {
  documentId: string;
  type: CustomerDocumentType;
  title: string;
  description: string;
  format: 'pdf' | 'image' | 'html';
  url: string;
  size: number;
  version: number;
  generatedAt: Date;
  expiresAt?: Date;
  availableOffline: boolean;
  shareable: boolean;
  status: 'ready' | 'pending' | 'expired';
}

type CustomerDocumentType =
  | 'itinerary'              // Day-by-day itinerary
  | 'booking_confirmation'   // Booking confirmation summary
  | 'hotel_voucher'          // Hotel stay voucher
  | 'flight_ticket'          // E-ticket / boarding pass
  | 'transfer_voucher'       // Transfer service voucher
  | 'activity_voucher'       // Activity/tour voucher
  | 'insurance_policy'       // Insurance policy document
  | 'invoice'                // Tax invoice
  | 'receipt'                // Payment receipt
  | 'visa_letter'            // Visa support letter
  | 'travel_guide'           // Destination guide
  | 'emergency_contacts'     // Emergency numbers and addresses
  | 'terms_conditions';      // Terms and conditions
```

### Offline Document Access

```typescript
interface OfflineDocumentStrategy {
  // Which documents to cache for offline
  priorityDocuments: CustomerDocumentType[];
  // When to prompt download
  downloadTriggers: DownloadTrigger[];
  // Storage management
  maxOfflineStorage: string;        // "50MB per trip"
}

type DownloadTrigger =
  | 'trip_confirmed'                 // Auto-cache when booking confirmed
  | '7_days_before_departure'        // Reminder to download
  | 'manual_download'                // Customer clicks download
  | 'wifi_detected';                 // Auto-download when on WiFi

// Priority for offline:
// 1. Itinerary (always cached)
// 2. Flight tickets / boarding passes
// 3. Hotel vouchers
// 4. Emergency contacts
// 5. Activity vouchers
// 6. Travel guide
```

### Document Sharing

```typescript
interface DocumentSharing {
  documentId: string;
  owner: string;                  // Primary booker
  sharedWith: DocumentShareTarget[];
  shareLink?: ShareLink;
}

interface DocumentShareTarget {
  travelerId: string;
  name: string;
  accessLevel: 'view' | 'download';
  sharedAt: Date;
}

interface ShareLink {
  url: string;
  expiresAt: Date;
  passwordProtected: boolean;
  accessCount: number;
  maxAccess: number;
}

// Sharing rules:
// - Primary booker can share with co-travelers
// - Each traveler gets their own relevant documents
// - Agent always has access to all documents
// - Share links expire after trip completion + 30 days
// - Documents with financial details (invoice) are owner-only
```

### Document Update Notifications

```typescript
interface DocumentUpdateNotification {
  tripId: string;
  updatedDocuments: DocumentUpdate[];
  action: 'view_updated' | 'download_new_version' | 'discard_old';
}

interface DocumentUpdate {
  documentId: string;
  documentType: CustomerDocumentType;
  changeSummary: string;          // "Hotel changed from Hilton to Marriott"
  newVersion: number;
  previousVersion: number;
}

// UX for updates:
// - Show "Updated" badge on document thumbnail
// - Side-by-side diff for significant changes
// - One-click "Download all updated documents"
// - Auto-invalidate cached offline copies
```

---

## Open Problems

1. **Boarding pass timing** — Airlines release boarding passes 24-48 hours before departure. The portal needs to show when they'll be available.

2. **Document version confusion** — Customer has old itinerary saved and new one downloaded. Which is current? Need clear version labeling.

3. **Large document bundles** — A 10-day trip with vouchers for every segment can produce 20+ documents. How to organize for easy access?

4. **Third-party document integration** — Some vouchers link to external systems (airline app for boarding pass). How to bridge between portal and external systems?

5. **Document retention after trip** — Customer may need invoices months later for reimbursement. How long to keep documents accessible?

---

## Next Steps

- [ ] Design customer document library UI
- [ ] Map document types and availability timeline per service
- [ ] Design offline caching strategy for PWA
- [ ] Study document sharing UX in travel apps (Tripit, Google Trips)
- [ ] Design document update notification and diff UI
