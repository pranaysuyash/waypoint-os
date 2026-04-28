# Offline & Low-Connectivity Mode — Traveler Tools

> Research document for customer-facing offline features — offline itinerary access, document storage, emergency information, and trip companion tools.

---

## Key Questions

1. **What offline features do travelers need most?**
2. **How do we deliver itineraries that work without internet?**
3. **What emergency information must be available offline?**
4. **How do travelers communicate with agents when connectivity is limited?**
5. **What's the offline travel companion UX?**

---

## Research Areas

### Offline Itinerary Access

```typescript
interface OfflineTravelerTools {
  itinerary: OfflineItinerary;
  documents: OfflineDocuments;
  emergency: OfflineEmergency;
  communication: OfflineCommunication;
  companion: TripCompanion;
}

interface OfflineItinerary {
  download: ItineraryDownload;
  viewing: OfflineItineraryView;
  navigation: OfflineNavigation;
  updates: ItineraryUpdateSync;
}

// Itinerary download trigger:
// When trip is confirmed → Auto-generate offline package:
// - Full itinerary (day-by-day with all details)
// - All booking confirmations (hotel, flight, activity vouchers)
// - Emergency contacts and embassy information
// - Destination guide summary (key phrases, transport info)
// - Maps for all destinations (static map images)
// - All reservation numbers and confirmation codes
//
// Download package contents:
// Size estimate: 5-15 MB per trip (text + compressed images)
// Format: Progressive Web App cached data + standalone HTML
//
// Auto-download triggers:
// 1. Trip confirmed: Download immediately
// 2. 48 hours before departure: Refresh package
// 3. Customer opens itinerary page: Download if not cached
// 4. Agent shares itinerary: Download on customer device
//
// Offline itinerary view:
// ┌─────────────────────────────────────────┐
// │  Kerala Trip · Dec 15-20                  │
// │  📴 Offline mode · Last updated 2h ago    │
// │                                            │
// │  Day 1 — Dec 15 (Monday)                  │
// │  ┌───────────────────────────────────┐    │
// │  │ ✈️ Flight AI-123                   │    │
// │  │ Delhi (DEL) → Kochi (COK)         │    │
// │  │ Depart 08:00 · Arrive 11:00       │    │
// │  │ Confirmed · Booking: ABC123       │    │
// │  │ [View Boarding Pass]              │    │
// │  └───────────────────────────────────┘    │
// │                                            │
// │  ┌───────────────────────────────────┐    │
// │  │ 🏨 Taj Malabar, Kochi              │    │
// │  │ Check-in: Dec 15 · 2 nights       │    │
// │  │ Deluxe Sea View Room              │    │
// │  │ Confirmation: TAJ-2026-45678      │    │
// │  │ 📞 +91-484-266-1234               │    │
// │  │ 📍 Willingdon Island, Kochi        │    │
// │  │ [Show on Map] [Call Hotel]        │    │
// │  └───────────────────────────────────┘    │
// │                                            │
// │  Day 2 — Dec 16 (Tuesday)                 │
// │  Day 3 — Dec 17 (Wednesday)               │
// │  Day 4 — Dec 18 (Thursday)                │
// │  Day 5 — Dec 19 (Friday)                  │
// │  Day 6 — Dec 20 (Saturday) — Return       │
// │                                            │
// │  📞 Emergency: [Agent Name] +91-98765...  │
// │  🔴 SOS: Emergency assistance              │
// └─────────────────────────────────────────────┘

// Offline navigation:
// - Pre-downloaded static map images for each destination
// - No turn-by-turn navigation offline (too data-heavy)
// - Hotel address in local language + English
// - Landmark-based directions ("Near Fort Kochi beach, behind St. Francis Church")
// - GPS coordinates for all stops (works with offline maps app)
// - "Open in Maps" button launches Google Maps offline (if area downloaded)
//
// Itinerary update sync:
// If agent makes changes while customer is traveling:
// 1. Change saved on server
// 2. Push notification sent to customer
// 3. If online: Auto-refresh itinerary
// 4. If offline: Notification queued, refreshes when connected
// 5. Visual indicator: "Updated 30 min ago — new hotel for Day 3"
// 6. Customer can view change history (what changed, when, why)

// Offline documents:
interface OfflineDocuments {
  vouchers: OfflineVoucher[];
  boarding: OfflineBoardingPass;
  insurance: OfflineInsurance;
  passport: OfflinePassportCopy;
}

// Voucher management:
// Each booking generates a downloadable voucher:
// - Hotel voucher: Confirmation number, dates, room type, hotel contact
// - Activity voucher: Booking reference, date, time, meeting point
// - Transfer voucher: Driver name, phone, vehicle number, pickup location
// - Flight e-ticket: PNR, flight number, times, seat (if assigned)
//
// Voucher format: PDF (printable) + HTML (viewable offline)
// Auto-downloaded when trip confirmed
// Available in "My Documents" section (sorted by date)
// Each document has: Download date, file size, offline expiry
//
// Boarding pass:
// Web check-in generates mobile boarding pass
// Format: Apple Wallet (.pkpass) + Google Pay (.json)
// Also available as PDF with QR/barcode
// Offline accessible from wallet or document library
//
// Insurance:
// Policy document downloaded at purchase
// Emergency numbers and policy number always available offline
// "Show to hospital" summary card (one page, key details)
//
// Passport copy:
// Encrypted copy stored locally (Level 4 security)
// Accessible only with device authentication (fingerprint/face)
// Auto-delete 24 hours after trip completion
// Purpose: Emergency replacement if passport lost

// Offline emergency information:
interface OfflineEmergency {
  contacts: EmergencyContact[];
  embassy: EmbassyInfo[];
  medical: MedicalInfo;
  localEmergency: LocalEmergencyInfo;
  sos: SOSFeature;
}

// Emergency contacts (always available offline):
// 1. Travel agent: Direct phone + WhatsApp
// 2. Agency emergency hotline: 24/7 number
// 3. Travel insurance: Emergency assistance number + policy number
// 4. Next of kin: Emergency contact from profile
// 5. Hotel front desk: For current accommodation
//
// Embassy/consulate information:
// For international trips, pre-load:
// - Indian embassy/consulate in destination country
// - Address, phone, email, working hours
// - Emergency after-hours number
// - Services available (passport replacement, emergency certificate)
//
// Medical information:
// - Nearest hospital to each hotel (name, address, phone)
// - Pharmacy locations
// - Traveler's medical conditions (from profile, with consent)
// - Blood group (if provided)
// - Medication list (if provided)
// - Allergy information
//
// Local emergency numbers:
// Police, ambulance, fire for each destination country
// India: 100 (police), 108 (ambulance), 101 (fire)
// Singapore: 999 (police), 995 (ambulance)
// Thailand: 191 (police), 1669 (ambulance)
// UAE: 999 (all emergencies)
//
// SOS feature:
// One-tap SOS button on itinerary page
// Actions:
// 1. Show emergency contacts with one-tap call
// 2. Send SMS to agent with GPS location (if signal available)
// 3. Show nearest hospital on map
// 4. Show embassy contact
// 5. Show insurance emergency number
// Works offline: Contacts and local info always available
// Requires signal: SMS and GPS location

// Offline communication:
interface OfflineCommunication {
  compose: OfflineCompose;
  autoRetries: AutoRetry;
  emergencyChannel: EmergencyChannel;
}

// Message composition while offline:
// Customer can compose messages to agent while offline
// Messages queued in local outbox
// Auto-send when connectivity restored
// Shows "Will send when connected" status
//
// Priority messages:
// "My flight is cancelled" → Critical priority
// "Hotel room has issues" → High priority
// "Where is the restaurant?" → Normal priority
// "Thanks for the great trip!" → Low priority
//
// Auto-retry logic:
// Compose message → Queue → Attempt send
// If fail → Retry in 30 seconds
// If fail again → Retry in 2 minutes
// If fail again → Retry in 10 minutes
// If fail again → Notify user "Message not sent, tap to retry"
//
// Emergency channel:
// If internet unavailable but SMS/call available:
// 1. Send SMS to agent with trip ID + brief message
// 2. Agent receives SMS, can respond via SMS
// 3. Platform links SMS conversation to trip thread
// 4. All messages logged for trip record
//
// WhatsApp offline mode:
// If WhatsApp installed: Messages go through WhatsApp
// (WhatsApp handles its own offline queue)
// If no WhatsApp: Fall back to SMS
// If no signal: Queue in platform, send when connected

// Trip companion features:
interface TripCompanion {
  checklists: TripChecklist;
  journal: TripJournal;
  sharing: TripSharing;
  translator: OfflineTranslator;
  currency: OfflineCurrencyConverter;
}

// Trip checklist:
// Pre-populated based on destination and trip type:
// ☐ Passport (valid 6+ months)
// ☐ Visa (for destination country)
// ☐ Travel insurance certificate
// ☐ Hotel confirmation printout
// ☐ Flight boarding pass
// ☐ Credit/debit cards (notify bank of travel)
// ☐ Local currency (₹X recommended for [destination])
// ☐ Phone charger + adapter ([plug type] for [country])
// ☐ Medications (with prescription copies)
// ☐ Copies of important documents (stored offline)
//
// Traveler can add custom items, check off completed ones
// Synced with account (available across devices)

// Trip journal:
// Traveler can record daily notes and photos
// Stored locally, synced when online
// Private by default, can share with agent
// Agent can add notes too (travel tips, recommendations)
//
// Offline translator:
// Pre-download language pack for destination
// Basic phrase book (English → local language):
// - Greetings: "Hello" → "Namaste" (Hindi), "Sawasdee" (Thai)
// - Directions: "Where is...?" → "Where is hotel?" → local script
// - Emergency: "Help!", "I need a doctor", "Call police"
// - Food: "I am vegetarian", "No spicy", "Bill please"
// - Common: "Thank you", "Sorry", "How much?"
//
// Offline currency converter:
// Pre-load exchange rate at time of trip
// Basic conversion: ₹ ↔ local currency
// Not real-time (uses rate at last sync)
// Shows: "₹1 = 0.016 SGD (rate from Apr 26)"
```

---

## Open Problems

1. **Offline map limitations** — Full offline maps (Google Maps offline download) require 1-2 GB per region. Most travelers won't download these proactively. Static map images are lightweight but not interactive.

2. **Translation quality offline** — On-device translation models (Google ML Kit) support common languages but may not cover regional Indian languages or less-common destinations. Phrase-book approach is reliable but limited.

3. **Document security on device** — Travel documents (passport copies, insurance) stored on a phone are vulnerable if the device is lost or stolen during the trip. Device encryption and auto-delete mitigate but don't eliminate this risk.

4. **SOS without connectivity** — The most critical offline feature is emergency communication, but SMS is the only reliable fallback. SMS delivery isn't guaranteed internationally, and roaming SMS can be expensive.

5. **User awareness of offline features** — Travelers may not know the app works offline. Proactive communication ("Your itinerary is available offline — no internet needed!") before departure is essential but easy to miss.

---

## Next Steps

- [ ] Build offline itinerary package generator with auto-download
- [ ] Create offline document vault with encrypted storage
- [ ] Implement SOS feature with emergency contacts and offline info
- [ ] Design trip companion tools (checklist, journal, translator, currency)
- [ ] Study offline travel apps (TripIt Offline, Google Trips, Sygic Travel, Maps.me)
