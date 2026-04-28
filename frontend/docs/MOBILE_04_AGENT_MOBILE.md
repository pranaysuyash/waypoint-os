# Mobile Experience — Agent Mobile Tools

> Research document for mobile-specific tools for travel agents in the field.

---

## Key Questions

1. **What agent tasks happen away from the desk (airport pickups, site inspections, events)?**
2. **What mobile-specific capabilities benefit agents (camera, GPS, barcode scanning)?**
3. **How do we design a mobile agent experience that complements (not replaces) desktop?**
4. **What's the agent notification strategy for mobile (urgent vs. informational)?**
5. **How do field agents communicate with the back office?**

---

## Research Areas

### Mobile Agent Capabilities

```typescript
interface AgentMobileFeature {
  feature: string;
  capabilities: MobileCapability[];
  offlineRequired: boolean;
  priority: 'must_have' | 'should_have' | 'nice_to_have';
}

type MobileCapability =
  | 'camera'              // Photo/video capture
  | 'gps'                 // Location tracking
  | 'barcode_qr'          // QR/barcode scanning
  | 'nfc'                 // NFC tag reading
  | 'push'                // Push notifications
  | 'biometric'           // Fingerprint/face auth
  | 'contacts'            // Phone contacts access
  | 'calendar'            // Calendar integration
  | 'offline_maps'        // Map access offline
  | 'voice_recording'     // Voice memo capture
  | 'ar';                 // Augmented reality (future)

// Feature list:
// 1. Trip schedule view (today's + upcoming) — offline, GPS for directions
// 2. Customer document access — offline, QR for verification
// 3. Site inspection tool — camera, GPS tagging, form submission
// 4. Transfer tracking — GPS, real-time ETA updates
// 5. Emergency response — offline contacts, GPS, camera
// 6. Customer communication — push, voice recording
// 7. Expense capture — camera for receipts, GPS for location tagging
// 8. Supplier check-in — QR scan, photo proof, GPS verification
```

### Field Agent Workflows

```typescript
interface FieldWorkflow {
  workflowId: string;
  name: string;
  trigger: string;
  steps: FieldStep[];
  requiresConnectivity: 'always' | 'intermittent' | 'offline_first';
}

interface FieldStep {
  step: string;
  inputType: 'photo' | 'video' | 'gps' | 'form' | 'qr_scan' | 'signature' | 'voice';
  dataCapture: DataCaptureConfig;
  required: boolean;
}

// Workflow: Airport pickup
// 1. GPS: Agent arrives at airport → auto-detect
// 2. Photo: Take photo of welcome board with customer name
// 3. QR scan: Scan customer booking QR code → verify identity
// 4. GPS: Start transfer → track route
// 5. Photo: Drop-off at hotel → photo proof
// 6. Form: Complete pickup report (customer mood, any issues)

// Workflow: Hotel site inspection
// 1. QR scan: Scan hotel barcode → load hotel profile
// 2. GPS: Verify location matches hotel
// 3. Photo: Room photos (standard, accessible, suite)
// 4. Photo: Common areas (lobby, restaurant, pool)
// 5. Form: Quality checklist (cleanliness, amenities, accessibility)
// 6. Voice: Audio notes for observations
// 7. Submit: Upload inspection report

// Workflow: Event coordination
// 1. GPS: Arrive at venue → auto-check-in
// 2. QR scan: Verify venue booking
// 3. Photo: Setup photos for client
// 4. Form: Vendor arrival checklist
// 5. Voice: Running commentary/notes during event
// 6. Photo: Event photos
// 7. Form: Post-event report
```

### Mobile Notification Strategy for Agents

```typescript
interface AgentMobileNotification {
  type: string;
  channel: 'push' | 'sms' | 'whatsapp';
  urgency: 'immediate' | 'within_5_min' | 'within_30_min' | 'digest';
  actionableOnMobile: boolean;
}

// Notification types:
// "Customer arriving in 30 min at Terminal 2" → push, immediate, actionable
// "New trip assigned to you" → push, within 5 min, viewable
// "Booking confirmation received" → push, within 30 min
// "Daily trip summary for tomorrow" → push digest, evening
// "Urgent: Customer medical emergency" → push + SMS, immediate, actionable
// "Price change on your pending quote" → push, within 30 min

// Quiet hours: 10 PM - 7 AM (except critical)
// Critical override: medical emergency, safety alert, VIP customer
```

### Back-Office Communication

```typescript
interface FieldBackofficeComm {
  // Agent can request support from back office
  requestTypes: SupportRequest[];
  // Real-time status sharing
  locationSharing: boolean;
  photoSharing: boolean;
}

type SupportRequest =
  | 'need_alternative_hotel'     // Agent at property, issue found
  | 'customer_wants_change'      // Customer requested modification
  | 'payment_issue'              // Payment declined at venue
  | 'supplier_no_show'           // Supplier didn't show up
  | 'document_verification'      // Need back-office to verify a document
  | 'language_support'           // Need translator on call
  | 'emergency_medical'          // Medical emergency support
  | 'emergency_legal';           // Legal issue support
```

---

## Open Problems

1. **Battery drain** — Constant GPS tracking for transfer monitoring drains battery quickly. Need intelligent location strategies (geofencing vs. continuous tracking).

2. **Data bandwidth** — Field agents may have poor connectivity at tourist locations. Photo uploads need compression and retry logic.

3. **Security on mobile** — Agent's phone contains customer PII (passports, addresses). Device loss is a security incident. Need remote wipe capability.

4. **Work-life boundaries** — Always-on push notifications blur work-life boundaries for agents. Need configurable availability status.

5. ** BYOD management** — Agents may use personal phones. Need MDM (Mobile Device Management) or containerization for work data.

---

## Next Steps

- [ ] Map field agent workflows through interviews/observation
- [ ] Design mobile agent app wireframes for top 3 workflows
- [ ] Study field service mobile apps (Uber driver, delivery apps) for UX patterns
- [ ] Research mobile device management for BYOD scenarios
- [ ] Design battery-efficient location tracking strategy
