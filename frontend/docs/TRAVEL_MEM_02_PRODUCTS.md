# Travel Photography & Memories — Memory Products

> Research document for digital memory books, printed photo albums, highlight reels, social-ready collages, and monetizable memory products for travel agencies.

---

## Key Questions

1. **What memory products can agencies create from trip photos?**
2. **How do we auto-generate memory books and highlight reels?**
3. **What social media-ready content can we produce?**
4. **How do memory products generate agency revenue?**

---

## Research Areas

### Memory Book Generator

```typescript
interface MemoryBook {
  id: string;
  trip_id: string;
  title: string;                        // "Sharma Family — Singapore 2026"

  // Pages
  pages: {
    page_number: number;
    layout: "FULL_PHOTO" | "TWO_PHOTO" | "PHOTO_TEXT" | "COLLAGE" | "TIMELINE" | "MAP" | "TITLE";
    photos: {
      photo_id: string;
      caption: string;
      position: { x: number; y: number; width: number; height: number };
    }[];
    text: {
      heading: string | null;           // "Day 2: Sentosa Adventure"
      body: string | null;              // AI-generated trip summary
      font: string;
      color: string;
    } | null;
  }[];

  // Generation
  auto_generated: boolean;
  edited_by_agent: boolean;
  template_used: string | null;

  // Output formats
  formats: {
    digital_pdf: string | null;         // URL to generated PDF
    print_ready_pdf: string | null;     // high-res for printing
    flipbook_url: string | null;        // interactive web version
    whatsapp_preview: string | null;    // compressed preview image
  };
}

// ── Auto-generated memory book ──
// ┌─────────────────────────────────────────────────────┐
// │  Memory Book: Singapore Family Trip                    │
// │  Auto-generated from 127 photos · 20 selected         │
// │                                                       │
// │  Page 1: Title Page                                   │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  ✈️ Sharma Family                              │   │
// │  │     Singapore Adventure                        │   │
// │  │     June 1-6, 2026                            │   │
// │  │  [Best group photo as background]              │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Page 2: Day 1 — Arrival & Marina Bay                │
// │  ┌───────────────────────────────────────────────┐   │
// │  │  [Full-bleed photo: Marina Bay at night]       │   │
// │  │  "Arrived in Singapore! First glimpse of the   │   │
// │  │   iconic Marina Bay Sands."                    │   │
// │  └───────────────────────────────────────────────┘   │
// │                                                       │
// │  Page 3: Day 2 — Sentosa Fun                         │
// │  ┌──────────┐ ┌──────────┐                          │
// │  │ Universal │ │ Palawan  │                          │
// │  │ Studios   │ │ Beach    │                          │
// │  └──────────┘ └──────────┘                          │
// │  "A full day of thrills at Universal Studios         │
// │   followed by sunset at Palawan Beach."              │
// │                                                       │
// │  Page 4: Day 3-4 — Culture & Nature                  │
// │  ...                                                  │
// │                                                       │
// │  Page 5: Trip Map                                     │
// │  [Static map showing all photo locations + route]     │
// │                                                       │
// │  Page 6: Best Moments (collage)                       │
// │  [Grid of top 12 photos from the trip]               │
// │                                                       │
// │  [Edit Book] [Download PDF] [Print Order] [Share]    │
// └─────────────────────────────────────────────────────┘
```

### Highlight Reel & Video

```typescript
interface HighlightReel {
  trip_id: string;
  duration_seconds: number;             // 30-90 seconds
  format: "VERTICAL_REEL" | "HORIZONTAL_VIDEO" | "STORY_FORMAT";

  // Content
  clips: {
    photo_id: string;
    duration_seconds: number;           // 2-4 seconds per photo
    transition: "FADE" | "SLIDE" | "ZOOM";
    caption_overlay: string | null;
    music_mood: "UPBEAT" | "ROMANTIC" | "ADVENTURE" | "RELAXED";
  }[];

  // Output
  video_url: string;
  thumbnail_url: string;
  shareable_link: string;
}

// ── Highlight reel generation ──
// ┌─────────────────────────────────────────────────────┐
// │  Highlight Reel — Auto-Generated                      │
// │  30 seconds · 15 best photos · Instagram Story format │
// │                                                       │
// │  📸 0:00 — Family at airport (excitement!)           │
// │  📸 0:02 — Marina Bay Sands night view               │
// │  📸 0:04 — Kids at Gardens by the Bay                │
// │  📸 0:06 — Universal Studios group photo             │
// │  📸 0:08 — Sunset at Sentosa                         │
// │  📸 0:10 — Singapore Zoo, kids feeding animals       │
// │  📸 0:12 — Night Safari experience                   │
// │  📸 0:14 — Orchard Road shopping                     │
// │  📸 0:16 — Family dinner at Clarke Quay              │
// │  📸 0:18 — Swimming pool at hotel                    │
// │  📸 0:20 — Cultural show at Chinatown                │
// │  📸 0:22 — Morning breakfast together                │
// │  📸 0:24 — Airport goodbye photo                     │
// │  📸 0:26 — "Until next time! ❤️" (title card)       │
// │  📸 0:28 — Agency branding + contact                 │
// │                                                       │
// │  Music: Upbeat travel vibes 🎵                       │
// │                                                       │
// │  [Edit Reel] [Download] [Share to WhatsApp]           │
// │  [Share to Instagram] [Share to Facebook]             │
// └─────────────────────────────────────────────────────┘
```

### Social Media Content Pack

```typescript
interface SocialContentPack {
  trip_id: string;
  generated: {
    // Instagram Story (9 slides)
    instagram_story: {
      slides: {
        photo_id: string;
        overlay_text: string;           // "Day 1: Hello Singapore! ✈️"
        sticker: string | null;         // location tag, temperature
      }[];
    };

    // WhatsApp status (5 images)
    whatsapp_status: {
      images: {
        photo_id: string;
        caption: string;
        agency_watermark: boolean;
      }[];
    };

    // Facebook album (20 photos)
    facebook_album: {
      title: string;
      description: string;
      photos: string[];
    };

    // Single post image (collage)
    collage_post: {
      layout: "3-photo" | "4-photo" | "6-photo" | "9-photo";
      photos: string[];
      caption: string;
      hashtags: string[];
    };
  };
}

// ── Social content pack ──
// ┌─────────────────────────────────────────────────────┐
// │  Social Media Content Pack                             │
// │  Generated from: Singapore Family Trip                │
// │                                                       │
// │  📱 Instagram Story (9 slides)                        │
// │     "Singapore Diaries — Day 1 to 5"                 │
// │     [Preview] [Download] [Post to Instagram]          │
// │                                                       │
// │  💬 WhatsApp Status (5 images)                        │
// │     Best photos with agency watermark                 │
// │     [Preview] [Share to WhatsApp]                     │
// │                                                       │
// │  🖼️ Collage Post (6-photo grid)                      │
// │     Caption: "5 days, 4 travelers, 1 unforgettable   │
// │     Singapore trip! Book yours with @WaypointOS"     │
// │     #SingaporeTravel #FamilyTrip #WaypointOS          │
// │     [Preview] [Download] [Share]                      │
// │                                                       │
// │  🎬 Highlight Reel (30s video)                       │
// │     Ready for Instagram Reels / YouTube Shorts        │
// │     [Preview] [Download]                              │
// │                                                       │
// │  💰 Agency value:                                     │
// │  • Branded content shared by happy customers         │
// │  • Social proof for prospective customers            │
// │  • Referral attribution from social shares           │
// └─────────────────────────────────────────────────────┘
```

### Revenue from Memory Products

```typescript
// ── Monetization model ──
// ┌─────────────────────────────────────────────────────┐
// │  Memory Products — Revenue Model                      │
// │                                                       │
// │  Free tier (included with trip):                      │
// │  • Digital memory book (PDF download)                │
// │  • 30-second highlight reel (watermarked)            │
// │  • Social media content pack                         │
// │                                                       │
// │  Premium products (paid add-ons):                     │
// │  • Printed photo book (₹1,500-3,000)                │
// │     20-page hardcover, premium paper                 │
// │  • Extended video (2-3 min, ₹500)                   │
// │     Professional quality, no watermark               │
// │  • Framed photo collage (₹800-2,000)                │
// │     Best 12 photos, framed, delivered               │
// │  • Canvas prints (₹1,200-3,500)                     │
// │     Large format, best single photo                  │
// │                                                       │
// │  Agency margin:                                       │
// │  • Digital products: 90% margin (cost is compute)    │
// │  • Printed products: 40% margin (vendor cost)        │
// │  • Average per trip: ₹400-800 add-on revenue         │
// │                                                       │
// │  Bundling:                                            │
// │  • Premium trip packages include printed memory book │
// │  • Group trips get group memory video included       │
// │  • Corporate trips get professional photo report     │
// └─────────────────────────────────────────────────────┘
```

---

## Open Problems

1. **Photo quality from mobile** — Mobile photos vary wildly in quality. AI enhancement (denoising, sharpening) before memory book generation is essential.

2. **Music licensing** — Background music for highlight reels needs royalty-free licensing. India-specific music preferences (Bollywood instrumentals) matter.

3. **Print vendor integration** — Printed products need print vendor partnerships in India. Quality control and delivery timelines are critical.

4. **Customer consent for agency branding** — Social content with agency watermark needs customer consent. Opt-in flow required.

---

## Next Steps

- [ ] Build auto memory book generator with template system
- [ ] Create highlight reel video generator
- [ ] Design social media content pack generator
- [ ] Implement print order integration for physical products
