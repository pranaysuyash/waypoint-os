# Travel Photography & Memories — Photo Capture & Management

> Research document for trip photo capture, AI-powered photo organization, shared albums, and photo storage for travel agencies.

---

## Key Questions

1. **How do we capture and organize trip photos?**
2. **What AI-powered photo management features are needed?**
3. **How do shared albums work for group trips?**
4. **What storage and privacy considerations apply?**

---

## Research Areas

### Trip Photo Management

```typescript
interface TripPhotoAlbum {
  trip_id: string;
  album_id: string;
  name: string;                         // "Singapore Family Trip — Jun 2026"

  // Photo metadata
  photos: {
    id: string;
    uploaded_by: string;                // traveler or agent
    uploaded_at: string;
    source: "APP_UPLOAD" | "WHATSAPP" | "AGENT_UPLOAD" | "VENDOR_SHARE";

    // AI-extracted metadata
    ai_tags: string[];                  // ["Marina Bay Sands", "family photo", "sunset"]
    location: GeoLocation | null;       // GPS from EXIF or AI estimation
    date_taken: string | null;          // from EXIF
    people_detected: string[];          // face cluster labels (opt-in)
    scene_type: "LANDMARK" | "FOOD" | "GROUP" | "SELFIE" | "ACTIVITY" | "HOTEL" | "TRANSPORT" | "NATURE" | "OTHER";
    quality_score: number;              // 1-10, for highlighting best photos
    destination_detected: string | null;

    // Photo details
    file_size_kb: number;
    dimensions: { width: number; height: number };
    caption: string | null;             // AI-generated or manual
  }[];

  // Album stats
  total_photos: number;
  total_size_mb: number;
  date_range: { from: string; to: string };
  destinations_covered: string[];
}

// ── Photo album view ──
// ┌─────────────────────────────────────────────────────┐
// │  Singapore Family Trip — Jun 2026                     │
// │  127 photos · 482MB · 4 destinations                 │
// │                                                       │
// │  [All] [Best Of ✨] [By Day] [By Place] [People]     │
// │                                                       │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │      │ │      │ │      │ │      │               │
// │  │ Day 1│ │ Day 1│ │ Day 2│ │ Day 2│               │
// │  │Marina│ │Gardens│ │Sentosa│ │ Zoo  │               │
// │  │ Bay  │ │ByBay │ │      │ │      │               │
// │  │ ★9.2 │ │ ★8.5 │ │ ★7.8 │ │ ★8.1 │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
// │  │ Day 3│ │ Day 3│ │ Day 4│ │ Day 5│               │
// │  │Orchard│ │Family│ │ Night│ │Airport│              │
// │  │Road  │ │Group │ │Safari│ │      │               │
// │  │ ★6.5 │ │ ★9.8 │ │ ★8.0 │ │ ★5.2 │               │
// │  └──────┘ └──────┘ └──────┘ └──────┘               │
// │                                                       │
// │  [Upload Photos] [Create Memory Book] [Share]         │
// └─────────────────────────────────────────────────────┘
```

### AI-Powered Photo Organization

```typescript
interface PhotoAIOrganizer {
  // Auto-organize photos by day and location
  organizeByTimeline(photos: TripPhoto[]): DayGroup[];

  // Find the best photos (for memory books, sharing)
  selectBestPhotos(photos: TripPhoto[], count: number): TripPhoto[];

  // Auto-caption photos
  generateCaption(photo: TripPhoto): string;

  // Detect and group by person (opt-in only)
  groupByPerson(photos: TripPhoto[]): PersonGroup[];

  // Create destination highlights
  createHighlights(photos: TripPhoto[]): DestinationHighlight[];
}

// ── AI photo features ──
// ┌─────────────────────────────────────────────────────┐
// │  AI Photo Intelligence                                │
// │                                                       │
// │  Auto-organization:                                   │
// │  • Group by day (using EXIF date + timezone)         │
// │  • Group by location (GPS + landmark detection)      │
// │  • Group by activity (beach, sightseeing, dining)    │
// │  • Timeline reconstruction (even without timestamps) │
// │                                                       │
// │  Best-of selection:                                    │
// │  • Score based on: sharpness, composition, lighting  │
// │  • Prefer: landmarks, group photos, golden hour      │
// │  • Filter out: duplicates, blurry, screenshots       │
// │  • Result: 20-30 best photos from a 100+ album       │
// │                                                       │
// │  Auto-captioning:                                      │
// │  • "Family photo at Marina Bay Sands, Singapore"     │
// │  • "Sunset dinner at Clarke Quay"                    │
// │  • "Kids at Singapore Zoo, Day 4"                    │
// │  • Supports Hindi + English captions                  │
// │                                                       │
// │  Privacy features:                                     │
// │  • Face detection OFF by default (opt-in per album)  │
// │  • Location data stripped on share unless opted in   │
// │  • Agency cannot see traveler photos without consent │
// └─────────────────────────────────────────────────────┘
```

### Shared Albums for Group Trips

```typescript
interface SharedAlbum {
  album_id: string;
  trip_id: string;

  // Contributors
  contributors: {
    traveler_id: string;
    name: string;
    photo_count: number;
    role: "OWNER" | "CONTRIBUTOR" | "VIEWER";
  }[];

  // Sharing
  share_link: string | null;            // expiring link
  share_expiry: string | null;
  whatsapp_group_linked: boolean;

  // Collection modes
  mode: "INDIVIDUAL" | "COLLABORATIVE";
  // INDIVIDUAL: each traveler has their own album
  // COLLABORATIVE: everyone adds to same album
}

// ── Group trip photo collection ──
// ┌─────────────────────────────────────────────────────┐
// │  Group Trip Photo Collection — Family Reunion Goa     │
// │  15 travelers · 3 families · 342 photos total        │
// │                                                       │
// │  Contributions:                                       │
// │  Sharma family:  128 photos (Rajesh: 85, Priya: 43) │
// │  Gupta family:   112 photos (Amit: 78, Sunita: 34)  │
// │  Patel family:   102 photos (Ravi: 60, Meena: 42)   │
// │                                                       │
// │  [All Photos] [By Family] [Best Of] [Timeline View]  │
// │                                                       │
// │  AI-generated highlights:                             │
// │  🌅 Best sunset: Gupta family at Palolem Beach       │
// │  👨‍👩‍👧‍👦 Best group: All 15 at Aguada Fort              │
// │  🍽️ Best food: Sharma family dinner at Martin's      │
// │  🏖️ Best beach: Kids playing at Baga Beach           │
// │                                                       │
// │  [Create Memory Book] [Download All] [Share Link]    │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Photo upload bandwidth** — Travelers upload photos from mobile in destinations with poor connectivity. Need compression, resumable uploads, and background upload.

2. **Face recognition privacy** — India DPDP Act requires explicit consent for biometric processing. Face detection must be opt-in with clear consent flow.

3. **Storage cost** — 100 photos × 5MB average × 1000 trips/year = 500GB/year. Need tiered storage with compression and thumbnail generation.

4. **Copyright and vendor photos** — Vendor-shared photos (hotel, activity photos) may have licensing restrictions. Need attribution and rights tracking.

---

## Next Steps

- [ ] Build trip photo album with upload and AI organization
- [ ] Create shared album system for group trips
- [ ] Implement AI-powered best-of selection and auto-captioning
- [ ] Design privacy-first photo management with consent flows
