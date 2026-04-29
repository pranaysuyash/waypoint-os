# Pricing Engine — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, calculate quotes  
**Approach:** Independent analysis — HOW do you price a trip?  

---

## 1. The Core Truth: You Need to Calculate Quotes+

### Your Reality (Solo Dev))

| Input | How to Calculate |
|-------|-------------------|
| **Hotel ₹50k** | + Markup 10% = ₹55k |
| **Flight ₹30k** | + Markup 10% = ₹33k |
| **Meals ₹20k** | + Markup 15% = ₹23k |
| **Total** | ₹50k + ₹30k + ₹20k = ₹100k → **YOU CHARGE ₹113k** |

**My insight:**   
Markup = **your profit**. Track it separately.   
Customer sees ₹113k (not your cost + profit separately).

---

## 2. My Pricing Model (Lean, Practical))+

### What You Actually Need (Simple))+

```json+
{
  "pricing_config": {
    "default_markup_percent": 10.0,  // 10% on everything+
    "markup_by_type": {
      "hotel": 10.0,
      "flight": 10.0,
      "transfer": 15.0,  // Higher risk, higher markup+
      "activity": 20.0  // High touch, high markup+
    },
    "service_fee_flat": 2000,  // ₹2000 per booking+
    "service_fee_min": 1000,  // Minimum+
    "service_fee_max": 10000,  // Maximum+
    
    // Discounts+
    "early_bird_percent": 5.0,  // Book 60+ days ahead+
    "volume_discount": {
      "3+_pax": 2.0,  // 2% off+
      "6+_pax": 5.0,
      "10+_pax": 10.0
    },
    
    // Taxes+
    "gst_percent": 18.0,  // GST on commission only+
    "tds_percent": 10.0  // TDS on vendor payments+
  }
}
```

**My insight:**   
`service_fee_flat` = **your salary per booking**.   
`markup_by_type` = higher for risky items (transfers = 15%).

---

### Booking Item Pricing (EXAMPLE))+

```json+
{
  "booking_item_id": "item-001",
  "item_type": "HOTEL",
  "description": "Deluxe Ocean View Room, 2 nights",
  
  // Vendor cost (what hotel charges you)+
  "vendor_cost": 50000,  // ₹50k+
  "vendor_currency": "INR",
  
  // Your markup+
  "markup_percent": 10.0,  // From config+
  "markup_amount": 5000,  // ₹50k * 10%+
    
  // Final price to customer+
  "customer_price": 55000,  // ₹50k + ₹5k+
  "currency": "INR",
    
  // Commission (what you keep)+
  "your_commission": 5000,  // Same as markup (simple model)+
  "gst_on_commission": 900,  // 18% GST+
  "your_commission_post_tax": 4100  // ₹5000 - ₹900 GST+
}
```

**My insight:**   
Customer sees ₹55k (not ₹50k + ₹5k breakdown).   
You keep ₹4100 (after GST).

---

## 3. Quote Calculation (API))+

### How to Calculate (Pricing API))+

```python+
# spine_api/services/pricing.py+
def calculate_quote(booking_items: list, booking_data: dict) -> dict:
    """Calculate final quote for customer."""
    config = load_pricing_config()
    
    total_customer_price = 0.0
    total_your_commission = 0.0
    breakdown = []
    
    for item in booking_items:
        # 1. Get vendor cost+
        vendor_cost = item['vendor_cost']
        
        # 2. Apply markup+
        markup_pct = config['markup_by_type'].get(
            item['item_type'], 
            config['default_markup_percent']
        )
        markup_amount = vendor_cost * (markup_pct / 100.0)
        customer_price = vendor_cost + markup_amount
        
        # 3. Your commission+
        your_commission = markup_amount  # Simple: markup = commission+
        gst_on_commission = your_commission * (config['gst_percent'] / 100.0)
        
        total_customer_price += customer_price
        total_your_commission += (your_commission - gst_on_commission)
        
        breakdown.append({
            "item_type": item['item_type'],
            "description": item['description'],
            "vendor_cost": vendor_cost,
            "markup_percent": markup_pct,
            "customer_price": customer_price,
            "your_commission": your_commission - gst_on_commission
        })
    
    # 4. Add service fee+
    service_fee = config['service_fee_flat']
    if total_customer_price > 200000:
        service_fee = min(service_fee * 2, config['service_fee_max'])
    total_customer_price += service_fee
    
    # 5. Apply discounts+
    discount = 0.0
    days_until_travel = (booking_data['start_date'] - date.today()).days
    if days_until_travel > 60:
        discount = total_customer_price * (config['early_bird_percent'] / 100.0)
    total_customer_price -= discount
    
    return {
        "total_customer_price": total_customer_price,
        "currency": "INR",
        "service_fee": service_fee,
        "discount": discount,
        "your_total_commission": total_your_commission,
        "breakdown": breakdown
    }
```

**My insight:**   
`service_fee` = double for high-value bookings (₹2L+).   
`early_bird` = incentive to book early.

---

### API Endpoint (5 Minutes))+

```python+
# spine_api/routers/pricing.py+
from fastapi import APIRouter+

router = APIRouter()

@router.post("/api/pricing/calculate")
async def calculate_quote_endpoint(payload: PricingCalculate):
    """Calculate quote for booking items."""
    result = calculate_quote(payload.items, payload.booking_data)
    return {"status": "ok", "quote": result}

# Usage:
# POST /api/pricing/calculate+
# Body: { "items": [...], "booking_data": {...} }
# Returns: { "quote": { "total_customer_price": 113000, ... } }
```

**My insight:**   
POST + calculate = **stateless**. No DB needed.

---

## 4. AI-Powered Pricing (Smart))+

### What AI Can Do (Assist))+

| Task | Without AI | With AI |
|------|-------------|---------|
| **Suggest markup** | ❌ Fixed 10% | ✅ "Bali in June = peak, try 15%" |
| **Discount suggestion** | ❌ Manual | ✅ "Customer is VIP, give 5% off" |
| **Upsell** | ❌ Forget | ✅ "Add airport transfer? Only ₹2000 more" |
| **Competitor check** | ❌ Manual | ✅ "Similar trip on MakemyTrip = ₹120k" |

**My recommendation:**   
AI pricing = **later** (Month 6+).   
Start with **fixed markup** (10%).

---

### AI Pricing Suggestion (Later, 5 Mins Setup))+

```python+
# Later: in AI draft+
def suggest_pricing(enquiry_id: str) -> dict:
    """AI suggests pricing strategy."""
    enquiry = db.get_enquiry(enquiry_id)
    destination = enquiry.facts['destination_candidates']['value'][0]
    travel_date = enquiry.facts['date_window']['value']
    
    # AI prompt+
    prompt = f"""
    Customer wants {destination} on {travel_date}.
    Base markup is 10%.
    Peak season? Suggest higher markup.
    VIP customer? Suggest discount.
    Return JSON: {{"suggested_markup": %, "reason": "..."}}
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(response.choices[0].message.content)
```

**My insight:**   
AI = **smart suggestions**. You decide final.   
`peak season` = June Bali = higher markup.

---

## 5. Current State vs Pricing Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Pricing config | None | `pricing_config.json` (commit) |
| Quote calculation | None | `calculate_quote()` (5 mins) |
| Markup by type | None | `markup_by_type` (hotel 10%, transfer 15%) |
| Service fee | None | `service_fee_flat: ₹2000` |
| Discounts | None | `early_bird: 5%` |
| AI pricing | None | LATER (Month 6+) |

---

## 6. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Pricing now? | Yes / Later | **NOW** — 5 mins, needed for quotes |
| Markup model? | Fixed % / AI dynamic | **Fixed %** — start simple |
| Service fee? | ₹2000 / ₹5000 / None | **₹2000** — your salary |
| AI pricing? | Now / Later | **LATER** — Month 6+ |
| GST on commission? | Yes / No | **YES** — 18% mandatory |

---

## 7. Next Discussion: Itinerary Builder+

Now that we know **HOW to price**, we need to discuss: **HOW to build the actual itinerary?**

Key questions for next discussion:
1. **Day-by-day builder** — Day 1: Arrive → Transfer → Check-in → Dinner?
2. **Maps integration** — show hotel location, attractions?
3. **Photos** — pull from vendor, upload yours?
4. **Activities per day** — drag-drop interface?
5. **Solo dev reality** — what's the MINIMUM itinerary builder? |

---

**Next file:** `Docs/discussions/itinerary_builder_2026-04-29.md`
