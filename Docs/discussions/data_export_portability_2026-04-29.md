# Data Export & Portability — First Principles Analysis+

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, GDPR/DPDP compliance+  
**Approach:** Independent analysis — what data to export, in what format  

---

## 1. The Core Truth: Customers Have Rights+

### Your Legal Obligations (GDPR + DPDP Act 2023)+

| Customer Right | What You Must Do | Timeline |
|---------------|-------------------|----------|
| **Access** | Export ALL their data | Within 30 days |
| **Portability** | Machine-readable (JSON) | Within 30 days |
| **Rectification** | Fix wrong data | Within 30 days |
| **Deletion** | Delete PII (not tax data) | Within 30 days |

**My insight:**   
GDPR = **EU customers** (even one German tourist).   
DPDP Act = **All Indian customers**.   
30 days = legal deadline, YOU must meet it.

---

## 2. My Export Model (3 Formats))+

### What Customers Can Request+

| Format | Use Case | Why |
|--------|----------|-----|
| **JSON** | GDPR portability | Machine-readable, standard |
| **PDF** | Customer view | Human-readable, screenshot-proof |
| **Excel** | Accountant/CA | Easy to open, sort, calculate |

**My recommendation:**   
**JSON + PDF** for customers.   
**Excel** for YOUR accountant (not customer request).

---

### JSON Export (GDPR Portability))+

```python+
# /api/export/customer/{customer_id}+
from fastapi.responses import JSONResponse+

@app.get("/api/export/customer/{customer_id}")
async def export_customer_data(customer_id: str, format: str = "json"):
    """Export all customer data (GDPR Article 20)."""
    
    customer = db.get_customer(customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    
    # 1. Gather ALL data+
    export_data = {
        "export_date": datetime.now().isoformat(),
        "export_format": "GDPR_PORTABLE",
        "customer": {
            "customer_id": customer.id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "phone_primary": customer.phone_primary,  # Will mask later
            "acquisition_source": customer.acquisition_source,
            "created_at": customer.created_at.isoformat()
        },
        
        # 2. Enquiries (public data only)+
        "enquiries": db.get_enquiries_for_export(customer_id),
        
        # 3. Bookings (no PII of others)+
        "bookings": db.get_bookings_for_export(customer_id),
        
        # 4. Communications (their messages only)+
        "communications": db.get_communications_for_export(customer_id),
        
        # 5. Consent records+
        "consents": db.get_consents_for_export(customer_id)
    }
    
    # 3. Mask PII (phone = "+91 987******10")+
    export_data = mask_pii_in_export(export_data)
    
    if format == "json":
        return JSONResponse(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=customer_{customer_id}_export.json'"
            }
        )
    
    elif format == "pdf":
        pdf_url = generate_pdf_export(export_data)
        return {"download_url": pdf_url}
```

**My insight:**   
Mask phone = `"+91 987******10"` (keep format, hide digits).   
JSON = **machine-readable** (GDPR standard).

---

### Excel Export (For Accountant))+

```python+
# /api/export/accountant/{period}+
@app.get("/api/export/accountant/{period}")
async def export_for_accountant(period: str):  # "2026-04"
    """Export financial data for CA."""
    
    # 1. Query bookings for period+
    bookings = db.get_bookings_by_period(period)
    
    # 2. Format for Excel+
    rows = []
    for b in bookings:
        rows.append({
            "Booking ID": b.booking_reference,
            "Customer Name": b.customer_name_cache,
            "Travel Date": f"{b.start_date} to {b.end_date}",
            "Destination": b.destination_cache,
            "Total Value (INR)": b.total_value,
            "Commission (INR)": b.commission_earned,
            "GST Collected": b.gst_collected,
            "TDS Deducted": b.tds_deducted,
            "Payment Status": b.payment_status
        })
    
    # 3. Generate Excel (using openpyxl)+
    from openpyxl import Workbook+
    wb = Workbook()
    ws = wb.active
    ws.title = f"Bookings {period}"
    
    # Headers+
    for col, header in enumerate(rows[0].keys(), 1):
        ws.cell(row=1, column=col, value=header)
    
    # Data+
    for row_idx, row in enumerate(rows, 2):
        for col_idx, value in enumerate(row.values(), 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Save+
    filename = f"/tmp/bookings_{period}.xlsx"
    wb.save(filename)
    
    return {"download_url": upload_to_s3(filename)}
```

**My insight:**   
CA wants **Excel**, not PDF.   
`openpyxl` = FREE library, simple.

---

### PDF Export (Human-Readable))+

```python+
# utils/pdf_export.py+
from reportlab.lib.pagesizes import letter+
from reportlab.pdfgen import canvas+

def generate_pdf_export(export_data: dict) -> str:
    """Generate human-readable PDF for customer."""
    
    filename = f"/tmp/export_{export_data['customer']['customer_id']}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Title+
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, f"Data Export for {export_data['customer']['first_name']}")
    
    # Customer info+
    c.setFont("Helvetica", 12)
    y = 700
    c.drawString(100, y, f"Name: {export_data['customer']['first_name']} {export_data['customer']['last_name']}")
    y -= 20
    c.drawString(100, y, f"Email: {export_data['customer']['email']}")
    y -= 20
    c.drawString(100, y, f"Phone: {export_data['customer']['phone_primary']}")  # Masked
    
    # Enquiries count+
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, y, "Enquiries")
    y -= 20
    c.setFont("Helvetica", 12)
    for eq in export_data['enquiries']:
        c.drawString(110, y, f"- {eq['destination']} ({eq['status']})")
        y -= 15
        if y < 50:  # New page+
            c.showPage()
            y = 750
    
    # Save+
    c.save()
    return upload_to_s3(filename)
```

**My insight:**   
PDF = **screenshot-proof** (customer can't edit).   
`reportlab` = FREE, built-in to Python.

---

## 3. What to Include/Exclude in Export)+

### Include (Mandatory for GDPR))+

| Data Type | Why Include |
|-----------|--------------|
| **Customer profile** | Name, email, phone (masked) |
| **Enquiries list** | Date, destination, status |
| **Booking list** | Reference, dates, value |
| **Communications** | Their messages only (not yours) |
| **Consent records** | What they consented to |
| **Payment history** | Amounts, dates (not bank details) |

### Exclude (Legal Holds))+

| Data Type | Why Exclude |
|-----------|--------------|
| **Vendor communications** | Internal, not their data |
| **Agent notes** | Internal, not their data |
| **Tax records** (7 yrs) | Legal hold (Sector 57) |
| **Other customers' data** | PII of others |
| **Bank account details** | Your secret, not theirs |

**My insight:**   
Tax records = **legal hold** (7 years).   
Vendor comms = **internal**, not customer data.

---

## 4. Masking PII in Exports)+

### What to Mask (Safety))+

```python+
def mask_pii_in_export(data: dict) -> dict:
    """Mask PII before export."""
    
    # Mask phone+
    phone = data['customer']['phone_primary']
    if phone:
        # Keep country code + last 2 digits+
        data['customer']['phone_primary'] = f"{phone[:3]}******{phone[-2:]}"
    
    # Mask email (optional, GDPR says show first char)+
    email = data['customer']['email']
    if email:
        local, domain = email.split('@')
        masked_local = local[0] + '*' * (len(local) - 1)
        data['customer']['email'] = f"{masked_local}@{domain}"
    
    return data
```

**My insight:**   
Mask phone = **keep format** (they see it's their number).   
Mask email = **show first char** (GDPR recommendation).

---

## 5. Delivery Method (How to Send)+

### Options (Lean, Solo Dev))+

| Method | Cost | Why Use |
|--------|------|----------|
| **WhatsApp** | ₹0 | Customer sees it immediately |
| **Email attachment** | ₹0 | Formal, trackable |
| **S3 signed URL** | ₹0.50/export | Secure, expires |

**My recommendation:**   
**WhatsApp + Email** (customer choice).   
S3 signed URL = **expires in 7 days** (security).

---

### Sending Export (WhatsApp + Email))+

```python+
# After generating export+
async def send_export_to_customer(customer_id: str, format: str):
    customer = db.get_customer(customer_id)
    
    # 1. Generate+
    if format == "json":
        export_url = generate_json_export(customer_id)
    elif format == "pdf":
        export_url = generate_pdf_export(customer_id)
    
    # 2. Send via WhatsApp+
    whatsapp_msg = f"📎 Your data export is ready!\nDownload: {export_url}\nExpires: 7 days"
    await send_whatsapp(customer.phone_primary, whatsapp_msg)
    
    # 3. Send via Email (backup)+
    send_email(
        to=customer.email,
        subject="Your Data Export (GDPR/DPDP Act)",
        body=f"Dear {customer.first_name},\n\nYour data export is attached...\n\nDownload: {export_url}",
        attachment=export_url
    )
    
    # 4. Log (audit trail)+
    db.create_export_log({
        "customer_id": customer_id,
        "format": format,
        "sent_at": datetime.now(),
        "download_url": export_url,
        "expires_at": datetime.now() + timedelta(days=7)
    })
```

**My insight:**   
Send BOTH WhatsApp + Email = **redundancy**.   
Log in `export_log` = audit trail (legal proof). 

---

## 6. Current State vs Export Model)+

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| JSON export | None | `export_data` endpoint (GDPR) |
| PDF export | None | `reportlab` PDF (human-readable) |
| Excel export | None | `openpyxl` (for accountant) |
| PII masking | None | Mask phone/email in exports |
| Delivery | None | WhatsApp + Email (redundancy) |
| Audit log | None | `export_log` table |

---

## 7. Decisions Needed (Solo Dev Reality))+

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| JSON export? | Now / Later | **NOW** — GDPR mandate |
| PDF export? | Now / Later | **NOW** — customer-friendly |
| Excel for CA? | Now / Later | **NOW** — accountant needs it |
| Mask phone? | Full / Masked | **MASKED** — show format only |
| S3 for storage? | Yes / No | **YES** — secure, expires |
| Delivery method? | WhatsApp / Email / Both | **BOTH** — redundancy |

---

## 8. Next Discussion: Session Management+

Now that we know **HOW to export data**, we need to discuss: **What happens when JWT expires?**

Key questions for next discussion:
1. **JWT expiry** — 1 hour? 24 hours?
2. **Refresh tokens** — auto-renew or force re-login?
3. **WhatsApp session** — does it expire? (no, persistent)
4. **Multiple devices** — can customer login from 2 phones?
5. **Solo dev reality** — what's the MINIMUM session mgmt needed?

---

**Next file:** `Docs/discussions/session_management_2026-04-29.md`
