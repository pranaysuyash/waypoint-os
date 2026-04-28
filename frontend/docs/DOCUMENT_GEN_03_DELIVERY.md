# Document Generation — Delivery & Distribution

> Research document for delivering generated documents through multiple channels.

---

## Key Questions

1. **What delivery channels do we need (email, WhatsApp, download, print, portal)?**
2. **How do we track document delivery, opens, and downloads?**
3. **What's the document packaging strategy for multi-document trips (itinerary + vouchers + tickets)?**
4. **How do we handle document updates (itinerary changed after delivery)?**
5. **What security and access control applies to documents containing PII?**

---

## Research Areas

### Delivery Channel Matrix

| Channel | Format | Max Size | Tracking | Best For |
|---------|--------|----------|----------|----------|
| Email attachment | PDF | 10-25MB | Open/click tracking | All documents |
| WhatsApp | PDF | 100MB | Delivery/read receipt | Vouchers, tickets, quick itineraries |
| Download link | PDF/HTML | Unlimited | Download count | Large documents, archives |
| Customer portal | PDF/HTML | Unlimited | View count | Self-service access |
| Print (agent) | PDF | N/A | Print log | Customer requests physical copy |
| SMS link | URL | N/A | Click tracking | Quick access to voucher |

### Document Package Model

```typescript
interface DocumentPackage {
  packageId: string;
  tripId: string;
  name: string;                    // "Singapore Trip Documents"
  documents: PackagedDocument[];
  deliveryStatus: DeliveryStatus;
  tracking: PackageTracking;
}

interface PackagedDocument {
  documentId: string;
  type: DocumentType;
  title: string;
  url: string;                     // Signed download URL
  fileSize: number;
  version: number;
  generatedAt: Date;
}

interface PackageDelivery {
  packageId: string;
  channels: DeliveryAttempt[];
  status: 'pending' | 'delivered' | 'partially_delivered' | 'failed';
}

interface DeliveryAttempt {
  channel: NotificationChannel;
  recipientId: string;
  sentAt: Date;
  deliveredAt?: Date;
  openedAt?: Date;
  downloadedAt?: Date;
  status: 'sent' | 'delivered' | 'opened' | 'downloaded' | 'bounced' | 'failed';
}
```

### Document Update & Redelivery

```typescript
interface DocumentUpdate {
  updateId: string;
  tripId: string;
  trigger: 'itinerary_change' | 'booking_change' | 'schedule_change' | 'manual';
  documentsAffected: DocumentType[];
  previousVersion: number;
  newVersion: number;
  changesSummary: string;
  autoRedeliver: boolean;
  redeliveryChannels: NotificationChannel[];
  suppressIfMinor: boolean;       // Don't redeliver for trivial changes
}
```

### Security & Access Control

```typescript
interface DocumentSecurity {
  // Access control
  accessLevel: 'public' | 'authenticated' | 'trip_participant' | 'named_recipient';
  // Download link security
  linkExpiry: number;             // Hours until link expires
  maxDownloads: number;           // Max times the link can be used
  passwordProtection: boolean;
  // PII handling
  containsPII: boolean;
  piiTypes: ('passport' | 'name' | 'email' | 'phone' | 'address')[];
  retentionPeriod: string;
  autoDeleteAfter: Date;
}
```

---

## Open Problems

1. **Document staleness** — A customer has a printed itinerary from 2 weeks ago, but the hotel changed. How to communicate that the physical copy is outdated?

2. **Offline access** — Travelers need documents while abroad without internet. Need to encourage download before departure.

3. **Document version confusion** — Multiple versions of the same itinerary in a customer's email. Which is the latest? Need clear version labeling.

4. **PII in transit** — Passports, addresses, and payment info in PDFs sent via email/WhatsApp. Encryption and secure delivery are essential.

5. **Regulatory document retention** — Invoices and contracts have mandatory retention periods. Leisure documents don't. Need per-type retention policies.

---

## Next Steps

- [ ] Design document delivery orchestration service
- [ ] Research secure document sharing (expiring links, password protection)
- [ ] Create document packaging strategy for multi-document trips
- [ ] Design document update notification and redelivery workflow
- [ ] Study WhatsApp document delivery API capabilities and limits
