# Itinerary Builder — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, build ACTUAL itinerary  
**Approach:** Independent analysis — what customer SEES (day-by-day)  

---

## 1. The Core Truth: Customer Sees THE ITINERARY+

### Your Reality (Solo Dev))

| What You Have | What You NEED |
|---------------|----------------|
| ✅ Booking model (DB) | ✅ Itinerary UI (day-by-day) |
| ✅ AI draft (text) | ✅ Visual builder (drag-drop) |
| ✅ Hotel/Blah blah | ✅ Maps + Photos + Day plan |

**My insight:**   
Customer buys **the itinerary**, not the DB model.   
Itinerary = **WHAT THEY SEE** (Day 1: Arrive → Transfer → Check-in). 

---

## 2. My Itinerary Model (Lean, Practical))+

### What Customer Sees (Day-by-Day))+

```json+
{
  "itinerary_id": "itin-001",
  "booking_id": "bk-001",
  "title": "Bali Honeymoon — 5N/6D",
  "currency": "INR",
  "total_price": 120000,
    
  // Day-by-day plan+
  "days": [
    {
      "day_number": 1,
      "date": "2026-06-15",
      "title": "Arrival & Check-in",
      "summary": "Land in Bali, transfer to resort, relax.",
      "items": [
        {
          "item_type": "FLIGHT",
          "time": "14:30",
          "description": "SQ 123 — Chennai → Bali (3h 20m)",
          "location": "Bali Airport (DNPS)",
          "duration_minutes": 200,
          "cost_included": true,
          "notes": "Passport + visa ready"
        },
        {
          "item_type": "TRANSFER",
          "time": "18:00",
          "description": "Private AC transfer → Breeze Bali Resort",
          "from": "Bali Airport",
          "to": "Breeze Bali Resort, Nusa Dua",
          "duration_minutes": 45,
          "cost_included": true
        },
        {
          "item_type": "CHECK_IN",
          "time": "19:00",
          "description": "Breeze Bali Resort — Deluxe Ocean View",
          "location": "Nusa Dua",
          "nights": 5,
          "hotel_details": {
            "name": "Breeze Bali Resort",
            "rating": 4.5,
            "amenities": ["pool", "spa", "beach_access"]
          }
        }
      ]
    },
    {
      "day_number": 2,
      "date": "2026-06-16",
      "title": "Beach & Sunset",
      "summary": "Relax at beach, sunset at Tanah Lot.",
      "items": [
        {
          "item_type": "ACTIVITY",
          "time": "10:00",
          "description": "Nusa Dua Beach — swim & relax",
          "location": "Nusa Dua Beach",
          "duration_minutes": 180,
          "cost_included": false,
          "price": 0,  // Free+
          "notes": "Bring sunscreen"
        },
        {
          "item_type": "TOUR",
          "time": "16:00",
          "description": "Tanah Lot Sunset Tour (shared)",
          "location": "Tanah Lot Temple",
          "duration_minutes": 240,
          "cost_included": true,
          "price": 2500,  // Per couple+
          "booked": true
        }
      ]
    }
  ],
    
  // Maps (optional, later)+
  "map_center": {"lat": -8.4095, "lng": 115.1889},
  "map_markers": [
    {"day": 1, "lat": -8.7445, "lng": 115.1667, "label": "Airport"},
    {"day": 1, "lat": -8.8034, "lng": 115.2250, "label": "Breeze Resort"}
  ],
    
  // Photos (optional, later)+
  "photos": [
    {"day": 1, "url": "https://s3.../beach1.jpg", "caption": "Nusa Dua Beach"}
  ]
}
```

**My insight:**   
Day = **unit of sale**. Customer buys Day 1-6, not "hotel + flight".   
`cost_included` = what they ALREADY paid.

---

## 3. Itinerary Builder UI (Next.js))+

### What YOU Need (Simple)+

```typescript+
// components/ItineraryBuilder.tsx+
import { useState } from "react";

export function ItineraryBuilder({ bookingId }: { bookingId: string }) {
  const [days, setDays] = useState<Day[]>([]);
  const [selectedDay, setSelectedDay] = useState<number>(1);
    
  // Add day+
  const addDay = () => {
    setDays([
      ...days,
      {
        day_number: days.length + 1,
        date: calculateDate(booking.start_date, days.length),
        title: `Day ${days.length + 1}`,
        items: []
      }
    ]);
  };
    
  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1>Itinerary Builder+</h1>
      
      {/* Day tabs */}      
      <div className="flex gap-2 mb-6">
        {days.map((day) => (
          <button
            key={day.day_number}
            className={selectedDay === day.day_number ? "bg-blue-600 text-white" : "bg-gray-200"}
            onClick={() => setSelectedDay(day.day_number)}
          >
            Day {day.day_number}+
          </button>
        ))}
        <button onClick={addDay}>+</button>
      </div>
      
      {/* Selected day */}      
      <DayView
        day={days.find((d) => d.day_number === selectedDay)!}
        onUpdate={(updated) => {
          setDays(days.map((d) => (d.day_number === selectedDay ? updated : d)));
        }}
      />
    </div>
  );
}
```

**My insight:**   
Day tabs = **quick navigation**.   
Add day = itinerary grows.

---

### Day View (Edit Items))+

```typescript+
// components/DayView.tsx+
import { useState } from "react";

export function DayView({ day, onUpdate }: { day: Day; onUpdate: (d: Day) => void }) {
  const [items, setItems] = useState<ItineraryItem[]>(day.items);
    
  const addItem = (type: ItemType) => {
    setItems([
      ...items,
      {
        item_type: type,
        time: "09:00",
        description: "",
        location: "",
        duration_minutes: 60,
        cost_included: true
      }
    ]);
  };
    
  return (
    <div className="border p-4 rounded">
      <h2>Day {day.day_number}: {day.title}+</h2>
      <p>{day.date} — {day.summary}</p>
      
      {/* Items */}      
      {items.map((item, index) => (
        <div key={index} className="border-b py-2 flex justify-between">
          <div>
            <strong>{item.time}</strong> — {item.description}+
            <div className="text-sm text-gray-500">{item.location}</div>
          </div>
          <div>
            {item.cost_included ? "✅ Included" : `₹{item.price}`}
            <button onClick={() => {
              setItems(items.filter((_, i) => i !== index));
              onUpdate({ ...day, items });
            }}>
              🗑
            </button>
          </div>
        </div>
      ))}
      
      {/* Add item */}      
      <div className="flex gap-2 mt-4">
        <button onClick={() => addItem("FLIGHT")}>Add Flight+</button>
        <button onClick={() => addItem("HOTEL")}>Add Hotel+</button>
        <button onClick={() => addItem("ACTIVITY")}>Add Activity+</button>
        <button onClick={() => addItem("TRANSFER")}>Add Transfer+</button>
      </div>
    </div>
  );
}
```

**My insight:**   
Click "Add Flight" → fills form.   
Save = auto-save to DB (React Query mutation).

---

## 4. Maps Integration (Optional, Later))+

### What YOU See (Visual)+

| Feature | Provider | Cost |
|---------|----------|------|
| **Static map** | Google Maps Static | FREE (1k/day) |
| **Interactive map** | Google Maps JS | FREE (28k/month) |
| **Markers** | Your markers | ₹0 |

**My recommendation:**   
Static map = **FREE**, good enough.   
Show map on itinerary PDF (customer love it).

---

### Static Map (Simple))+

```typescript+
// utils/maps.ts+
export function getStaticMapUrl(center: { lat: number; lng: number }, markers: Marker[]) {
  const base = "https://maps.googleapis.com/maps/api/staticmap";
  const key = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY!;
  
  // Center+
  let url = `${base}?center=${center.lat},${center.lng}&zoom=10&size=600x300&key=${key}`;
  
  // Markers+
  markers.forEach((m, i) => {
    url += `&markers=color:red|label:${m.label}|${m.lat},${m.lng}`;
  });
  
  return url;
}

// Usage in ItineraryBuilder+
<img
  src={getStaticMapUrl(itinerary.map_center, itinerary.map_markers)}
  alt="Bali Trip Map"
  className="w-full rounded"
/>
```

**My insight:**   
`size=600x300` = perfect for PDF.   
FREE = 1000/day (enough for you).

---

## 5. Photo Gallery (Optional, Later))+

### What Customer Sees (Visual)+

```typescript+
// components/PhotoGallery.tsx+
export function PhotoGallery({ photos }: { photos: Photo[] }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      {photos.map((photo, i) => (
        <div key={i} className="relative">
          <img
            src={photo.url}
            alt={photo.caption}
            className="w-full h-32 object-cover rounded"
          />
          <p className="text-xs text-center">{photo.caption}</p>
        </div>
      ))}
    </div>
  );
}
```

**My insight:**   
Photos = **social proof** (Instagram-style).   
Store in S3: `s3://bucket/itineraries/itin-001/beach1.jpg`.

---

## 6. PDF Generation (Itinerary for Customer))+

### What Customer Gets (Download))+

| Format | Tool | Why |
|--------|------|-----|
| **PDF** | `reportlab` (Python) | Customer downloads |
| **WhatsApp** | Send link | Instant |
| **Print** | Browser print | Backup |

**My recommendation:**   
PDF = **customer-ready**.   
WhatsApp = send link: "Your itinerary: http://...".

---

### PDF Generator (reportlab))+

```python+
# spine_api/services/itinerary_pdf.py+
from reportlab.lib.pagesizes import A4+
from reportlab.pdfgen import canvas+

def generate_itinerary_pdf(itinerary: dict) -> str:
    """Generate PDF itinerary for customer."""
    filename = f"/tmp/itin_{itinerary['itinerary_id']}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4+
    
    # Title+
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, itinerary['title'])
    
    # Days+
    y = height - 100
    for day in itinerary['days']:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Day {day['day_number']}: {day['title']}")
        y -= 20+
        
        c.setFont("Helvetica", 10)
        for item in day['items']:
            c.drawString(60, y, f"{item['time']} — {item['description']}")
            y -= 15+
        
        y -= 10+
    
    c.save()
    return upload_to_s3(filename)
```

**My insight:**   
PDF = **₹0** (`reportlab` is free).   
Upload to S3 = customer downloads anytime.

---

## 7. Current State vs Itinerary Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Itinerary builder | None | Day-by-day UI (Next.js) |
| Day plan | None | `days[]` array (items per day) |
| Maps | None | Google Static Map (FREE) |
| Photos | None | S3 storage + gallery |
| PDF generation | None | `reportlab` (FREE) |
| WhatsApp share | None | Send link to PDF |

---

## 8. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Itinerary builder? | Now / Later | **NOW** — customer buys THIS |
| Maps? | Google / None | **Google Static** — FREE |
| Photos? | Now / Later | **LATER** — S3 storage |
| PDF now? | Yes / No | **YES** — customer expects it |
| Drag-drop UI? | Yes / No | **NO** — simple list = enough |

---

## 9. Next Discussion: Document Generation+

Now that we know **HOW to build itinerary**, we need to discuss: **HOW to generate vouchers, invoices, tickets?**

Key questions for next discussion:
1. **Voucher PDF** — hotel confirmation, flight ticket?
2. **Invoice PDF** — for customer (already discussed)?
3. **Visa invitation letter** — for customer (if needed)?
4. **Templates** — reuse design (header, footer, logo)?
5. **Solo dev reality** — what's the MINIMUM generation needed?

---

**Next file:** `Docs/discussions/document_generation_2026-04-29.md`
