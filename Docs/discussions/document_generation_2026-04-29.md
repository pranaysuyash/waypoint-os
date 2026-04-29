# Document Generation — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, generate PDFs+  
**Approach:** Independent analysis — vouchers, invoices, tickets  

---

## 1. The Core Truth: Customers Need Paper+

### Your Reality (Solo Dev))

| Document | Why Needed | Frequency |
|-----------|-------------|-----------|
| **Hotel Voucher** | Customer shows at check-in | Every booking |
| **Flight Ticket** | Customer boards flight | Every flight |
| **Invoice** | Customer paid ₹1.2L | Every booking |
| **Visa Invitation** | Embassy requires it | Sometimes |
| **Insurance Policy** | Customer travels | Optional |

**My insight:**   
Vouchers = **trust builder** (customer feels secure).   
Generate once, reuse for similar trips.

---

## 2. My Document Generation Model (Lean, Practical))+

### What You Actually Need (Simple))+

```json+
{
  "document_templates": {
    "hotel_voucher": {
      "file": "templates/hotel_voucher.pdf",
      "fields": ["customer_name", "hotel_name", "check_in", "nights"],
      "generated_count": 45
    },
    "flight_ticket": {
      "file": "templates/flight_ticket.pdf",
      "fields": ["customer_name", "flight_no", "date", "seat"],
      "generated_count": 30
    },
    "invoice": {
      "file": "templates/invoice.pdf",
      "fields": ["invoice_no", "items", "total", "gst"],
      "generated_count": 40
    }
  }
}
```

**My insight:**   
Templates = **reuse**. Update once, all future docs updated. 

---

### PDF Generation (ReportLab — 5 Mins))+

```python+
# spine_api/services/document_gen.py+
from reportlab.lib.pagesizes import A4+
from reportlab.pdfgen import canvas+
from datetime import datetime+

def generate_hotel_voucher(booking_item: dict, customer: dict) -> str:
    """Generate hotel voucher PDF."""
    filename = f"/tmp/voucher_{booking_item['id']}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4+
    
    # Header+
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, booking_item['description'])
    
    # Customer+
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Guest: {customer['first_name']} {customer['last_name']}")
    c.drawString(50, height - 100, f"Booking Ref: {booking_item['booking_reference']}")
    
    # Hotel details+
    c.drawString(50, height - 140, f"Hotel: {booking_item['hotel_name']}")
    c.drawString(50, height - 160, f"Check-in: {booking_item['check_in']}")
    c.drawString(50, height - 180, f"Nights: {booking_item['nights']}")
    
    # Footer+
    c.setFont("Helvetica", 10)
    c.drawString(50, 30, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
    
    c.save()
    return upload_to_s3(filename)
```

**My insight:**   
`upload_to_s3` = customer downloads anytime.   
ReportLab = **FREE**, built-in to Python. 

---

## 3. Invoice Generation (GST Compliant))+

### What MUST Be Included))+

| Field | Why |
|-------|-----|
| **GSTIN** | Legal requirement (yours) |
| **Invoice No.** | Sequential, unique |
| **HSN Code** | 998559 (tour operator) |
| **CGST + SGST** | 9% + 9% = 18% |
| **Customer GSTIN** | If they have it |

### Invoice PDF (10 Mins))+

```python+
def generate_invoice(booking: dict, customer: dict) -> str:
    """Generate GST-compliant invoice."""
    filename = f"/tmp/invoice_{booking['invoice_number']}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4+
    
    # Header - YOUR details+
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Ravi's Travels")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "GSTIN: 22AAAAA0000A1Z5")
    c.drawString(50, height - 90, "Bangalore, Karnataka")
    
    # Invoice details+
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, height - 50, f"Invoice: {booking['invoice_number']}")
    c.setFont("Helvetica", 10)
    c.drawString(400, height - 70, f"Date: {booking['created_at']}")
    
    # Customer+
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 140, "Bill To:")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 160, f"{customer['first_name']} {customer['last_name']}")
    if customer.get('gstin'):
        c.drawString(50, height - 180, f"GSTIN: {customer['gstin']}")
    
    # Items table+
    y = height - 240
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Description")
    c.drawString(300, y, "HSN")
    c.drawString(400, y, "Amount")
    
    y -= 20
    c.setFont("Helvetica", 10)
    for item in booking['items']:
        c.drawString(50, y, item['description'])
        c.drawString(300, y, "998559")
        c.drawString(400, y, f"₹{item['price']}")
        y -= 20
    
    # GST+
    gst = booking['total'] * 0.18
    c.drawString(300, y - 20, f"CGST (9%): ₹{gst/2}")
    c.drawString(300, y - 40, f"SGST (9%): ₹{gst/2}")
    c.drawString(300, y - 70, f"Total: ₹{booking['total']}")
    
    c.save()
    return upload_to_s3(filename)
```

**My insight:**   
HSN 998559 = tour operator services.   
GST = **mandatory** if revenue > ₹20L. 

---

## 4. WhatsApp: Send Document+)-

### How Customer Gets It (Instant))+

```python+
# spine_api/routers/documents.py+

router = APIRouter()

@router.post("/api/documents/voucher/{booking_item_id}")
async def send_voucher(booking_item_id: str, customer_id: str):
    """Generate + send voucher via WhatsApp."""
    booking_item = db.get_booking_item(booking_item_id)
    customer = db.get_customer(customer_id)
    
    # 1. Generate PDF+
    pdf_url = generate_hotel_voucher(booking_item, customer)
    
    # 2. Send via WhatsApp+
    message = f"🎫 Your hotel voucher is ready!\nDownload: {pdf_url}\nShow at check-in ✅"
    await send_whatsapp(customer['phone_primary'], message)
    
    # 3. Log+
    db.create_communication({
        "enquiry_id": booking_item['enquiry_id'],
        "type": "VOUCHER_SENT",
        "document_url": pdf_url
    })
    
    return {"status": "ok", "download_url": pdf_url}
```

**My insight:**   
Send via **WhatsApp** = instant delivery.   
`VOUCHER_SENT` = audit trail. 

---

## 5. Bulk Generation (For Accountant))+

### Excel Export (Already Discussed) vs PDFs))+

| Format | Use Case | Tool |
|--------|----------|------|
| **PDF** | Customer voucher/ticket | ReportLab |
| **Excel** | Accountant books | openpyxl |
| **JSON** | GDPR export | Built-in |

**My recommendation:**   
PDF = **customer-facing**.   
Excel = **accountant-facing**. 

---

### Bulk Invoices (Month-End))+

```python+
@router.post("/api/documents/bulk-invoices")
async def bulk_generate_invoices(month: str):  # "2026-04"
    """Generate ALL invoices for a month."""
    bookings = db.get_bookings_by_month(month)
    invoice_urls = []
    
    for b in bookings:
        if b['invoice_url']:
            continue  # Already generated+
        pdf_url = generate_invoice(b, b['customer'])
        invoice_urls.append(pdf_url)
    
    return {"count": len(invoice_urls), "urls": invoice_urls}
```

**My insight:**   
Bulk = **month-end** (send to accountant).   
Skip already generated = idempotent. 

---

## 6. Current State vs Document Model)+-

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Voucher PDF | None | ReportLab (FREE) |
| Invoice PDF | None | GST-compliant (HSN 998559) |
| Ticket PDF | None | ReportLab (flight details) |
| Bulk generation | None | Month-end for accountant |
| WhatsApp delivery | None | Send link instantly |
| Template storage | None | `templates/` folder |

---

## 7. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| Vouchers now? | Yes / No | **YES** — customer expects it |
| Invoice now? | Yes / Later | **YES** — GST requirement |
| Templates? | DB / Files | **Files** — easy to edit |
| Bulk gen? | Now / Later | **LATER** — month-end |
| ReportLab? | Now / Later | **NOW** — 5 mins setup |

---

## 8. Next Discussion: Dashboard/Homepage UI+

Now that we know **HOW to generate docs**, we need to discuss: **What does agent see on login?**

Key questions for next discussion:
1. **Quick stats** — this month's revenue? (₹1.2L)
2. **Today's tasks** — reply to Ravi, send voucher to Priya?
3. **Alerts summary** — 2 EMI overdue, 1 VIP message?
4. **Recent enquiries** — 5 latest?
5. **Solo dev reality** — what's the MINIMUM homepage needed?

---

**Next file:** `Docs/discussions/dashboard_homepage_2026-04-29.md`
