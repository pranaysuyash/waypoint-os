# Search & Discovery — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, need to find things fast  
**Approach:** Independent analysis — search is HOW you use the system daily  

---

## 1. The Core Problem: You'll Drown in Data Without Search**

### Your Reality (Solo Dev)

| Search Need | Why It Matters |
|--------------|-------------------|
| **"Find Ravi's old enquiry"** | He calls, "I want same Bali trip again" → need past details |
| **"Which vendors in Phuket?"** | Quick quote for new customer, need preferred vendors |
| **"Similar honeymoon trip?"** | Reuse draft, adapt for new customer |
| **"Anyone going to Bali in June?"** | Vendor negotiation — bulk deals |
| **"Customer with GSTIN ABCD..."** | Corporate invoice, need to find company |

**My insight:**  
Without search, you'll waste **30+ minutes per enquiry** digging through lists.  
With search, you'll find anything in **<10 seconds**.

---

## 2. My Search Architecture (Simple, PostgreSQL-Powered)**

### Full-Text Search (PostgreSQL Built-In)**

PostgreSQL has **built-in full-text search** — no Elasticsearch needed (over-engineering for solo dev).

```sql
-- Add tsvector column to enquiries (auto-updated)
ALTER TABLE enquiries ADD COLUMN search_vector tsvector;

CREATE INDEX enquiries_search_idx ON enquiries USING GIN(search_vector);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_enquiry_search_vector() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := 
    setweight(to_tsvector('english', COALESCE(NEW.enquiry_id, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.customer_name_cache, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.destination_cache, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enquiry_search_update BEFORE INSERT OR UPDATE
  ON enquiries FOR EACH ROW EXECUTE FUNCTION update_enquiry_search_vector();
```

**My insight:**  
Use `tsvector` + `GIN index` — fast, built-in, zero extra infrastructure.  
Weight A/B/C = title/customer/destination priority in ranking.

---

### Search API (Simple Endpoint)**

```python
# /api/search
@app.get("/api/search")
async def search(
    q: str,  # "Ravi Bali June"
    entity_type: str = "ALL",  # ENQUIRY | CUSTOMER | VENDOR | BOOKING
    limit: int = 10
):
    # Full-text search across entities
    results = db.search_fulltext(q, entity_type, limit)
    
    # Boost by recency (newer = higher rank)
    for r in results:
        days_old = (now() - r.created_at).days
        r['rank'] = r['rank'] * (1.0 / (1.0 + days_old * 0.01))
    
    return sorted(results, key=lambda x: x['rank'], reverse=True)
```

**My insight:**  
`entity_type` filter lets you search "only customers" vs "everything".  
`limit=10` prevents overload — you want top 5, not 500 results.

---

## 3. Search Scenarios (What You'll Actually Search)**

### Scenario 1: Customer Calls "I'm Ravi, send me same Bali trip"**

```
You: Search "Ravi"
  └─ Results:
      1. Ravi Kumar (CUSTOMER) — VIP, 3 past trips
      2. EQ-0042 (ENQUIRY) — Bali honeymoon, June 2025
      3. BK-001 (BOOKING) — Bali, ₹1.2L, completed
      4. Breeze Bali Resort (VENDOR) — their preferred hotel

You: Click BK-001 → "Same itinerary, June 15-20, updated prices"
```

**My insight:**  
Search finds **customer + past booking + preferred vendor** in one query.  
Click → auto-populate new enquiry with past details.

---

### Scenario 2: "Need quote for Phuket family hotel, 2 rooms"**

```
You: Search "Phuket family hotel"
  └─ Results:
      1. Paradise Phuket Resort (VENDOR) — PREFERRED, rating 4.5
      2. EQ-0038 (ENQUIRY) — Phuket family, 2 rooms, July 2025
      3. Sunset Beach Hotel (VENDOR) — CONTRACTED, rating 4.2
      4. PK-012 (PACKAGE) — Phuket family package, ₹80k

You: Click EQ-0038 → "Copy draft, update dates → send"
```

**My insight:**  
Search finds **past similar enquiry** → reuse draft, save 2 hours of work.  
Click vendor → see past bookings with them (negotiation leverage).

---

### Scenario 3: "Anyone going to Bali in June for bulk deal?"**

```
You: Search "Bali June 2026"
  └─ Results:
      1. EQ-0042 (ENQUIRY) — Ravi, June 15-20, 2 pax
      2. EQ-0051 (ENQUIRY) — Priya, June 22-27, 4 pax
      3. EQ-0063 (ENQUIRY) — Amit, June 10-14, 2 pax

You: "3 bookings, 8 pax total → call Breeze Bali Resort, negotiate bulk rate"
```

**My insight:**  
Search by **destination + date** → find multiple customers → vendor negotiation.  
This is HOW you increase margins — bulk deals.

---

## 4. Search Fields (What to Index)**

### Enquiries (Searchable Fields)**

```json
{
  "search_fields": {
    "enquiry_id": { "weight": "A", "type": "id" },
    "customer_name": { "weight": "B", "type": "text" },  // Denormalized from customer
    "destination": { "weight": "B", "type": "text" },  // Denormalized from facts
    "trip_type": { "weight": "C", "type": "text" },
    "status": { "weight": "C", "type": "keyword" },
    "assigned_agent_id": { "weight": "C", "type": "keyword" }
  },
  "search_vector_sql": "
    setweight(to_tsvector('english', COALESCE(customer_name, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(destination, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(trip_type, '')), 'C')
  "
}
```

**My insight:**  
Denormalize `customer_name` + `destination` into enquiry table — faster search, no JOIN.  
Weight A/B/C = ranking priority (ID exact match > name > type).

---

### Customers (Searchable Fields)**

```json
{
  "search_fields": {
    "customer_id": { "weight": "A" },
    "first_name + last_name": { "weight": "B" },
    "email": { "weight": "B" },
    "phone_primary": { "weight": "B" },
    "company_name": { "weight": "C" },  // For corporate
    "gstin": { "weight": "C" }  // "Find GSTIN ABCD..."
  }
}
```

**My insight:**  
Search by **phone number** — customer calls, you type last 4 digits → find them.  
Search by **GSTIN** — corporate invoice, need company record fast.

---

### Vendors (Searchable Fields)**

```json
{
  "search_fields": {
    "vendor_id": { "weight": "A" },
    "company_name + brand_name": { "weight": "B" },
    "operating_cities": { "weight": "B" },  // "Phuket", "Bali"
    "vendor_type": { "weight": "C" },  // ACCOMODATION, AIR_TRANSPORT
    "vendor_tier": { "weight": "C" }  // PREFERRED, CONTRACTED
  }
}
```

**My insight:**  
Search by **city** — "Phuket" → all hotels/transfers there.  
Filter by **tier** — "only PREFERRED vendors" → quality guarantee.

---

## 5. Similarity Matching (AI-Assisted)**

### Why This Matters**

> "Ravi wants Bali again, similar to last year"

System should **auto-suggest** similar past enquiries/bookings.

```python
# AI-powered similarity (spine_api extension)
def find_similar_enquiries(enquiry_id: str, limit: int = 5):
    # 1. Get the enquiry
    eq = db.get_enquiry(enquiry_id)
    
    # 2. Extract key features
    features = {
        "destination": eq.destination,
        "trip_type": eq.trip_type,
        "party_size": eq.party_size,
        "duration_nights": eq.duration_nights,
        "budget_range": (eq.budget_min, eq.budget_max)
    }
    
    # 3. Find similar (cosine similarity on denormalized fields)
    similar = db.find_similar(
        table="enquiries",
        reference_features=features,
        exclude_id=enquiry_id,
        limit=limit
    )
    
    return similar  # List of past enquiries with similarity score
```

**My insight:**  
Similarity matching = **20x faster drafting**.  
"I want same as last time" → click past booking → auto-fill new enquiry.

---

## 6. Search UI (Frontend)**

### Quick Search Bar (Global, Top of App)**

```typescript
// components/SearchBar.tsx
// Globally available at /app/layout.tsx

<SearchBar>
  <Input 
    placeholder="Search customers, enquiries, vendors..." 
    onChange={(q) => searchAPI(q)}
  />
  <ResultsDropdown>
    {results.map(r => (
      <ResultItem key={r.id} type={r.entity_type}>
        <Icon type={r.entity_type} />  // USER, FILE, BUILDING
        <Title>{r.title}</Title>  // "Ravi Kumar (VIP)"
        <Snippet>{r.snippet}</Snippet>  // "Bali trip, June 15-20..."
        <Badge>{r.entity_type}</Badge>  // ENQUIRY, CUSTOMER, etc.
      </ResultItem>
    ))}
  </ResultsDropdown>
</SearchBar>
```

**My insight:**  
Search bar should be **globally available** (top nav).  
Click result → `router.push('/enquiries/eq-0042')` → instant context.

---

### Advanced Search (Filterable)**

```
Search: "Bali"
Filters:
  Entity: ☑ Enquiries ☑ Customers ☑ Vendors ☐ Bookings
  Date: June 2026
  Status: ☑ Confirmed ☐ Drafted ☐ Cancelled
  Trip Type: ☑ Family ☐ Honeymoon ☑ Corporate
  
Results: 12 found
  1. EQ-0042 — Ravi, Bali honeymoon, June 15-20 ✅ Confirmed
  2. EQ-0051 — Priya, Bali family, June 22-27 ✅ Confirmed
  ...
```

**My insight:**  
Filters = **precision**. You know it's "Bali + June + Confirmed" → use filters.  
Filters should be **collapsible** — usually you just type and go.

---

## 7. Current State vs Search Model**

| Concept | Current Schema | My Proposed Model |
|---------|---------------|-------------------|
| Full-text search | None | PostgreSQL `tsvector` + GIN index |
| Search API | None | `/api/search?q=...&entity_type=...` |
| Similarity matching | None | AI-assisted `find_similar()` |
| Search UI | None | Global search bar + advanced filters |
| Denormalized fields | None | `customer_name`, `destination` on enquiry |
| Search ranking | None | Weight A/B/C + recency boost |

---

## 8. Decisions Needed (Simple Answers)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Search engine? | PostgreSQL FTS / Elasticsearch / Algolia | **PostgreSQL FTS** — zero infrastructure |
| Similarity matching? | AI / Simple keywords | **Simple keywords** first, AI later |
| Global search bar? | Yes / No | **YES** — you'll use it 20x/day |
| Denormalize fields? | Yes / No | **YES** — `customer_name` on enquiry table |
| Search result limit? | 10 / 25 / 50 | **10** — top 5 is enough |
| Advanced filters? | Yes / No | **YES** — but hidden by default |

---

## 9. Next Discussion: Reporting & Analytics**

Now that we know **HOW to find things**, we need to discuss: **WHAT metrics matter?**

Key questions for next discussion:
1. **Revenue tracking** — monthly, by agent, by vendor?
2. **Conversion funnel** — enquiry → quote → booking → cancelled?
3. **Agent performance** — conversion rate, response time, satisfaction?
4. **Vendor scorecard** — rating, complaint rate, response time?
5. **Customer insights** — repeat rate, VIP count, at-risk count?
6. **Solo dev reality** — what reports do YOU actually need? (vs nice-to-have)
7. **Export** — Excel/PDF for accountants/tax filing?

---

**Next file:** `Docs/discussions/reporting_and_analytics_2026-04-29.md`
