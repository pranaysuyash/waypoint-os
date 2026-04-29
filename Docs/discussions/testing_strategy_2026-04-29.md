# Testing Strategy — First Principles Analysis

**Date:** 2026-04-29  
**Context:** Travel Agency Agent — solo dev, NO QA team, YOU test everything  
**Approach:** Independent analysis — what actually needs testing vs nice-to-have  

---

## 1. The Core Truth: You're the Only Tester**

### Your Reality (Solo Dev)

| What You CAN'T Do | What You MUST Do |
|-------------------|-------------------|
| ❌ Hire QA team | ✅ Automate tests (write once, run forever) |
| ❌ Manual test everytime | ✅ Regression suite (catch breaks fast) |
| ❌ Cross-browser testing | ✅ Test on YOUR devices only |
| ❌ Load testing (1000 users) | ✅ Test 10 enquiries manually, assume scale |

**My insight:**  
As solo dev, **every bug costs you 3x** (find it, fix it, verify it).  
Automated tests = insurance policy (cheap compared to your time).

---

## 2. My Testing Pyramid (Lean, Practical)**

### Level 1: Unit Tests (70% of tests)**

**What to Test (Critical Business Logic Only):**

```python
# tests/test_payment_logic.py
def test_emi_overdue_detection():
    """EMI overdue → alert triggered."""
    emi = EMI_Tracking(
        total_emi_amount=150000,
        emi_tenure_months=6,
        next_due_date="2026-04-20",  # 9 days ago
        installments_paid=3  # Should be 4
    )
    assert emi.overdue_count == 1
    assert emi.status == "OVERDUE"

def test_visa_blocked_detection():
    """Passport X from country Y → blocked country Z."""
    visa = VisaRequirement(
        country="XYZ",
        passport_issued_by="India",
        visa_status="BLOCKED",
        blocked_reason="Indian passport holders not permitted"
    )
    assert visa.eligible == False
    assert visa.severity == "CRITICAL"

def test_commission_calculation():
    """Agency keeps 10%, vendor gets 90%."""
    payout = VendorPayout(
        gross_amount=100000,
        commission_rate_applied=10.0
    )
    assert payout.agency_commission == 10000
    assert payout.vendor_payout_amount == 90000
```

**My insight:**  
Test **money logic** (EMI, commission, payout) — bugs here = legal/financial risk.  
Test **compliance logic** (visa blocked, passport expiry) — bugs here = stranded customers.

---

### Level 2: Integration Tests (20% of tests)**

**What to Test (API + DB):**

```python
# tests/test_enquiry_api.py
def test_create_enquiry_triggers_ai():
    """POST /api/enquiries → AI runs, status = TRIAGED."""
    response = client.post("/api/enquiries", json={
        "raw_text": "Bali honeymoon June 15-20, family of 4, budget 1.2L"
    })
    assert response.status_code == 201
    enquiry_id = response.json()['enquiry_id']
    
    # Wait for AI (async)
    import time
    time.sleep(5)
    
    enquiry = db.get_enquiry(enquiry_id)
    assert enquiry['status'] == "TRIAGED"
    assert enquiry['ai_analysis'] is not None

def test_booking_creation_from_enquiry():
    """POST /api/bookings (from confirmed enquiry)."""
    # 1. Create enquiry
    enquiry = db.create_enquiry(...)
    
    # 2. Confirm it
    db.update_enquiry(enquiry.id, {'status': 'CONFIRMED'})
    
    # 3. Create booking
    response = client.post("/api/bookings", json={
        "enquiry_id": enquiry.id,
        "customer_id": enquiry.customer_id
    })
    assert response.status_code == 201
    assert response.json()['booking_id'] is not None
```

**My insight:**  
Integration tests = **API + DB** (not just API mock).  
Test the **full flow** (enquiry → AI → booking) — that's what users care about.

---

### Level 3: E2E Tests (10% of tests)**

**What to Test (Critical Paths Only):**

```typescript
// tests/e2e/critical-flow.spec.ts
// Playwright (but maybe SKIP for solo dev — heavy)

test('Agent can create enquiry and send draft', async ({ page }) => {
  // 1. Login
  await page.goto('/login')
  await page.fill('[name="email"]', 'you@agency.com')
  await page.fill('[name="password"]', '...')
  await page.click('button[type="submit"]')
  
  // 2. New enquiry
  await page.click('a:has-text("New Enquiry")')
  await page.fill('[name="raw_text"]', 'Bali honeymoon...')
  await page.click('button:has-text("Submit")')
  
  // 3. Wait for AI
  await page.waitForSelector('text=Triaged')
  
  // 4. Send draft
  await page.click('button:has-text("Send Draft")')
  await page.waitForSelector('text=Sent')
})
```

**My insight:**  
E2E = **heavy, flaky, slow**. For solo dev, maybe SKIP and do **manual test checklist** instead.  
Checklist: "Can I create enquiry? Can I send WhatsApp? Can I mark payment?"

---

## 3. What NOT to Test (Save Time)**

| DON'T Test | Why (Solo Dev) |
|------------|-------------------|
| **UI animations** | Visual polish, not business logic |
| **API response times** | You have 1 user (yourself) |
| **Cross-browser** | You use Chrome/Safari only |
| **Accessibility (A11y)** | Internal tool, not public |
| **Load testing** | 1000 enquiries? You wish :) |
| **Third-party APIs** | Stripe mock is enough |

**My insight:**  
Every test you DON'T write = **30 minutes saved**.  
Focus on **money, compliance, data integrity** (the expensive bugs).

---

## 4. Test Data Strategy (Synthetic Only)**

### Never Use Real Customer Data**

```python
# tests/factories.py
def create_fake_customer():
    return {
        "first_name": "Ravi",  # Fake
        "last_name": "Kumar",
        "email": f"test+{uuid4()}@example.com",  # Always test+*
        "phone_primary": "+91 98765 43210",  # Fake
        "passport_number": "A1234567",  # Fake
        "pan_number": "ABCDE1234F"  # Fake
    }

def create_fake_enquiry():
    return {
        "raw_text": "Bali honeymoon June 15-20, family of 4, budget ₹1.2L",
        "channel": "whatsapp",
        "acquisition_source": "inbound_organic"
    }
```

**My insight:**  
Use `test+*` prefix for emails — Gmail ignores everything after `+`.  
NEVER use real passports — even in tests, it's PII exposure.

---

### Test Database (Isolated)**

```python
# conftest.py
import pytest

@pytest.fixture
def db():
    """Create isolated test DB."""
    test_db_url = "postgresql://test:test@localhost/travel_agency_test"
    # 1. Create fresh DB
    # 2. Run migrations
    # 3. Yield DB connection
    yield db_connection
    # 4. Drop DB (clean slate)
```

**My insight:**  
Test DB = copy of prod schema, ZERO prod data.  
Run tests in parallel — `pytest -n auto` (if you have multiple CPUs).

---

## 5. AI Testing (The Hard Part)**

### How to Test LLM Outputs (Variance!)**

```python
# tests/test_ai_enquiry_parsing.py
def test_ai_extracts_destination():
    """AI should extract 'Bali' from text."""
    test_cases = [
        ("Bali honeymoon June 15-20, family of 4", "Bali"),
        ("Planning trip to Bali and Phuket", ["Bali", "Phuket"]),
        ("Bali, Indonesia", "Bali")
    ]
    
    for text, expected in test_cases:
        result = spine_client.run(text)
        destinations = result.facts['destination_candidates']['value']
        
        if isinstance(expected, list):
            assert all(d in destinations for d in expected)
        else:
            assert expected in destinations

def test_ai_detects_visa_blocked():
    """AI should flag blocked destination."""
    text = "North Korean tour, Indian passport"
    result = spine_client.run(text)
    
    assert result.derived_signals['visa_requirements']['blocked_destinations'] != []
    assert result.decision_state == "STOP_NEEDS_REVIEW"
```

**My insight:**  
AI tests = **fuzzy** (not exact match).  
Test **decision outcomes** (STOP_NEEDS_REVIEW) more than exact text.

---

## 6. Manual Test Checklist (Solo Dev Backup)**

### What to Test Manually (Monthly)**

```markdown
# Manual Test Checklist (run before major releases)

## Enquiry Flow
- [ ] Create enquiry via WhatsApp (scan QR)
- [ ] Create enquiry via email forward
- [ ] AI parses correctly (destination, dates, budget)
- [ ] Draft generated with correct tone (casual for leisure)
- [ ] Send draft via WhatsApp → customer receives

## Booking Flow
- [ ] Create booking from confirmed enquiry
- [ ] Add flight + hotel items
- [ ] Mark payment as "COMPLETED"
- [ ] Upload voucher PDF
- [ ] Customer receives confirmation WhatsApp

## Vendor Flow
- [ ] Search vendor by city "Bali"
- [ ] Filter by PREFERRED tier
- [ ] Send quote request via email
- [ ] Log vendor reply (quoted ₹50k)

## Critical
- [ ] EMI overdue alert fires (simulate overdue date)
- [ ] VIP message alerts on WhatsApp
- [ ] Can delete customer (GDPR right to delete)
```

**My insight:**  
Manual checklist = YOUR safety net.  
Run it **before deploying** (not after).

---

## 7. Current State vs Testing Model**

| Concept | Current State | My Lean Model |
|---------|---------------|-------------------|
| Unit tests | 618 backend (existing) | Add **money + compliance** tests |
| Integration tests | None | Add **API + DB** flow tests |
| E2E tests | None | **SKIP** (too heavy for solo dev) |
| Test data | None | **Factories** (fake passports, emails) |
| AI testing | None | **Fuzzy outcome** tests (not exact text) |
| Manual checklist | None | **Monthly** before major releases |

---

## 8. Decisions Needed (Solo Dev Reality)**

| Decision | Options | My Recommendation |
|-----------|---------|-------------------|
| E2E tests? | Playwright / Cypress / Skip | **SKIP** — too heavy, manual checklist instead |
| Test DB? | SQLite / PostgreSQL test | **PostgreSQL test** — same as prod |
| AI test depth? | Exact match / Fuzzy outcome | **Fuzzy outcome** (decision state) |
| Test coverage goal? | 80% / 60% / 40% | **40%** — cover money + compliance only |
| Manual checklist? | Yes / No | **YES** — run monthly before releases |
| CI/CD? | GitHub Actions / None | **GitHub Actions** — free, run tests on push |

---

## 9. Next Discussion: Mobile & PWA**

Now that we know **HOW to test**, we need to discuss: **Where do you work?**

Key questions for next discussion:
1. **WhatsApp is primary** — can you work WITHOUT the web app?
2. **PWA** — install on phone, works offline?
3. **Mobile-responsive** — is the web app usable on your phone?
4. **WhatsApp Business API** — send/receive via API (not manual)?
5. **Push notifications** — WhatsApp notifications vs SMS?
6. **Solo dev reality** — what's the MINIMUM mobile presence needed?

---

**Next file:** `Docs/discussions/mobile_and_pwa_2026-04-29.md`
