# Domain, Hosting & Legal — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, going live soon+  
**Approach:** Independent analysis — minimum viable launch setup  

---

## 1. The Core Truth: You Need a URL People Can Remember+

### Your Checklist (Minimum to Go Live))

| Item | Status | Cost/Year |
|------|--------|-----------|
| **Domain name** | ❌ NOT bought | ~₹800-1200 ($10-15) |
| **Hosting** | ❌ NOT live | ~₹500-2000/month ($6-24) |
| **SSL certificate** | ❌ NOT installed | FREE (Let's Encrypt) |
| **Business registration** | ❌ NOT done | ~₹2000-5000 ($24-60) |
| **GST registration** | ❌ NOT done | FREE (gov.in) |
| **Terms of Service** | ❌ NOT written | YOU write it |

**My insight:**   
As solo dev, **domain + hosting = ₹2000/month**.+   
GST registration = **mandatory** for Indian travel agencies (₹20L+ revenue).

---

## 2. My Domain & Hosting Model (Lean, Practical))

### Domain Name (What to Choose))

| Option | Example | Why Pick It? | Cost/Year |
|--------|---------|--------------|-----------|
| **Brand name** | `ravi-travels.com` | Personal, memorable | ~₹1000 |
| **Generic** | `bali-trip-expert.com` | SEO, location-based | ~₹800 |
| **Agency name** | `paradise-travels.com` | Professional | ~₹1000 |
| **.in TLD** | `travelagency.in` | Indian customers trust | ~₹600 |

**My recommendation:**   
`yourname-travels.com` — personal brand, you ARE the agency.+   
If Bali-focused: `bali-paradise-travels.com` (SEO boost for Bali).

---

### Hosting (Where Code Lives))

| Provider | Cost/Month | Why Pick It? |
|----------|------------|--------------|
| **Vercel** | FREE (hobby) / $20 | Next.js-native, zero config |
| **AWS Lightsail** | $5-10 | Cheap VPS, you manage |
| **DigitalOcean** | $6-12 | Similar to AWS, simpler |
| **Railway** | $5+ | Easy deploys, JS-friendly |
| **Local server** | ₹0 (you have it) | ❌ NO — if house burns, offline |

**My recommendation:**   
**Vercel FREE** (frontend) + **Railway $5** (backend) = ₹400/month.+   
Why? Zero ops, auto-scaling, you focus on business.

---

### Architecture (Live))

```
┌───────────────────────────────────┐
│                    VERCEL (frontend)                 │
│  Next.js app → https://your-agency.vercel.app  │
│  (later: https://yourname-travels.com)        │
└──────────────┬───────────────────────────────┘
               │ HTTPS (Let's Encrypt auto)
┌──────────────┴───────────────────────────────┐
│                    RAILWAY (backend)                    │
│  FastAPI → https://your-agency.up.railway.app │
│  PostgreSQL included (1GB free)                │
└──────────────┬───────────────────────────────┘
               │
┌──────────────┴───────────────────────────────┐
│                    S3 (Backups)                        │
│  Backups → s3://your-agency-backups/          │
└─────────────────────────────────────────────┘
```

**My insight:**   
Vercel + Railway = **zero server management**.+   
If you outgrow: Vercel Pro $20 → AWS EC2 $10.

---

## 3. SSL Certificates (HTTPS is Mandatory))

### Why You Need HTTPS)

| Without HTTPS | With HTTPS |
|---------------|---------------|
| ❌ Browser warns "NOT SECURE" | ✅ Green lock, trust |
| ❌ WhatsApp API won't work | ✅ Webhooks work |
| ❌ GDPR violation (PII in clear) | ✅ Encrypted in transit |
| ❌ Google de-ranks you | ✅ SEO boost |

### My Lean SSL Model+

| Provider | Cost | Automation |
|----------|------|-------------|
| **Let's Encrypt** | FREE | Auto-renewal (Vercel/Railway built-in) |
| **Cloudflare** | FREE | Proxy + CDN + SSL bundle |
| **DigiCert** | ₹5000/year | ❌ Overkill for solo dev |

**My recommendation:**   
**Let's Encrypt** (auto) — Vercel/Railway handles it.+   
Add **Cloudflare FREE** later for CDN + DDoS protection.

---

## 4. Legal Setup (India-Specific, Mandatory))

### What You MUST Do (Legal Checklist))

| Item | Mandatory? | Cost | Timeline |
|------|------------|------|----------|
| **Sole Proprietorship** | ✅ YES | ₹2000-5000 | 7-15 days |
| **GST Registration** | ✅ YES (if >₹20L) | FREE | 3-7 days |
| **Shop & Establishment** | 🟡 MAYBE | ₹1000-3000 | 15-30 days |
| **IATA License** | ❌ NO (not needed) | ₹5L+ | 6+ months |
| **TDP Certificate** | ❌ NO (not needed) | ₹10k+ | 3+ months |

**My insight:**   
Sole Prop = **simplest** (just PAN + bank account).+   
GST = mandatory if revenue >₹20L (you'll hit it in year 2).

---

### GST for Travel Agencies (Special Rules))

```json
{
  "gst_applicable": {
    "threshold": 2000000,  // ₹20 Lakhs
    "gst_rate": 18,  // 18% on commission
    "hsn_code": "998559",  // Tour operator services
    "gst_state": "YOUR_STATE",  // Karnataka, Maharashtra, etc.
    
    // Invoicing (mandatory)
    "invoice_format": {
      "gstin": "22AAAAA0000A1Z5",  // Your GSTIN
      "place_of_supply": "Karnataka",  // Where service provided
      "cgst": 9,  // Central GST (9%)
      "sgst": 9,  // State GST (9%)
      "igst": 18  // Integrated GST (inter-state)
    },
    
    // TDS (if paying vendors)
    "section_194j": {
      "applicable": true,  // Commission payments
      "tds_rate": 10,  // 10% TDS on commission
      "threshold": 30000  // ₹30k in a year
    }
  }
}
```

**My insight:**   
HSN 998559 = Tour operator services. GST on **commission only**, not customer's total.+   
TDS 194J = 10% on commission paid to vendors (if >₹30k/year).

---

## 5. Terms of Service (Minimum Viable))

### What to Include (YOU Write It, 2 Pages Max))

```markdown
# Terms of Service — [Your Agency Name]

## 1. Booking & Payments
- Full payment required 7 days before travel.
- EMI available via Bajaj/HDfC (you arrange).
- Cancellation: >30 days = full refund, 15-30 days = 50%, <15 days = no refund.

## 2. Vendor Responsibility
- We coordinate with vendors, but hotel/airline issues = vendor liability.
- We're not liable for airline delays, hotel overbooking (vendor's job).

## 3. Data Privacy (DPDP Act)
- We store your passport, visa, medical data for booking.
- You can ask to delete data (except tax records, kept 7 years).
- WhatsApp messages are logged for dispute resolution.

## 4. Limitation of Liability
- Our maximum liability = commission earned (not total booking value).
- Not liable for force majeure (natural disasters, pandemics).

## 5. Governing Law
- Governed by Indian law, jurisdiction: [Your City] courts.

## 6. Contact
- WhatsApp: +91 98765 43210
- Email: hello@[your-agency].com
```

**My insight:**   
Limit liability to **commission only** (not total booking value).+   
Mention DPDP Act = shows you're compliant.

---

## 6. Privacy Policy (DPDP Act Compliance))

### What to Include (YOU Write It, 1 Page Max))

```markdown
# Privacy Policy — [Your Agency Name]

## 1. Data We Collect
- Passport number, visa documents, medical conditions (for booking).
- Phone number, WhatsApp chats (for communication).
- Payment proofs (for accounting).

## 2. How We Use It
- Process your booking with vendors.
- Send confirmations via WhatsApp.
- Comply with tax laws (7-year retention).

## 3. Data Sharing
- Vendors (hotels, airlines) — only what they need.
- Government (visa processing) — only passport/visa data.
- NO third-party marketing (unless you consent).

## 4. Your Rights (DPDP Act)
- Access: Ask what data we have.
- Correct: Fix wrong passport number.
- Delete: Remove PII (except tax records).

## 5. Contact
- WhatsApp: +91 98765 43210
- Email: privacy@[your-agency].com
```

**My insight:**   
Mention **DPDP Act** specifically (new law, shows compliance).+   
"NO third-party marketing" = trust builder.

---

## 7. Current State vs Launch Model+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Domain | None | `yourname-travels.com` (~₹1000/year) |
| Hosting | Local only | Vercel FREE + Railway $5/month |
| SSL | None | Let's Encrypt (auto, FREE) |
| Business reg | None | Sole Prop (~₹3000) |
| GST | None | If >₹20L revenue |
| Terms/Privacy | None | YOU write (2+1 pages) |

---

## 8. Decisions Needed (Solo Dev Reality))

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Domain TLD? | .com / .in / .co.in | **.com** — global, memorable |
| Hosting? | Vercel / Railway / AWS | **Vercel + Railway** — zero ops |
| SSL? | Let's Encrypt / Cloudflare | **Let's Encrypt** (auto) |
| Business reg? | Now / Later | **Now** — before first booking |
| GST? | Now / When >₹20L | **When >₹20L** — mandatory |
| Terms? | Lawyer / YOU write | **YOU write** — 2 pages max |

---

## 9. Next Discussion: Marketing & SEO+

Now that we know **WHERE the system lives**, we need to discuss: **How do customers find you?**

Key questions for next discussion:
1. **SEO** — Google ranking, keywords "Bali trip", "Phuket honeymoon"?
2. **Google My Business** — local SEO, maps listing?
3. **Social media** — Instagram, Facebook, TikTok ads?
4. **Referral program** — customers bring friends, get ₹1000 off?
5. **Content marketing** — blog "Bali vs Phuket: Which is better?"
6. **Solo dev reality** — what's the MINIMUM marketing to get first 10 customers?

---

**Next file:** `Docs/discussions/marketing_seo_2026-04-29.md`
