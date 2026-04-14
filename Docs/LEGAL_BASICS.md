# Legal Basics (Minimal)

**Date**: 2026-04-14
**Purpose: Bare minimum legal stuff to not get sued

---

## The Solo Builder Legal Reality

> "I am not a lawyer. This is not legal advice. Talk to a lawyer."

That said, here are basics to get you started. You can improve later.

---

## Part 1: Business Entity

### Do You Need to Register?

**Short answer**: Yes, eventually.

| Stage | Recommendation |
|-------|----------------|
| **Idea/validation** | Not needed yet |
| **First revenue** | Consider registering |
| **₹20K+ MRR** | Definitely register |

### Options (India)

| Entity | When to use | Pros | Cons |
|--------|-------------|------|------|
| **Sole Proprietorship** | Just starting | Simple, no registration | Personal liability |
| **Partnership** | Multiple founders | Simple | Joint liability |
| **Pvt Ltd (Company)** | Raising money, hiring | Limited liability | Compliance burden |
| **LLP** | Middle ground | Limited liability, simpler | Less common |

**Recommendation**: Start as sole proprietorship, convert to Pvt Ltd when raising money or hiring.

---

## Part 2: Terms of Service (What You Need)

### Minimal TOS Sections

```markdown
# Terms of Service

## 1. Acceptance
By using Agency OS, you agree to these terms.

## 2. Service Description
Agency OS provides AI-powered trip planning assistance for travel agencies.

## 3. Your Responsibilities
- You are responsible for all content you input
- You must verify all suggestions before presenting to travelers
- Final booking and travel decisions are yours

## 4. AI-Generated Content
- Suggestions are AI-generated and may not be accurate
- You must independently verify all information
- We are not liable for booking decisions based on our suggestions

## 5. Data and Privacy
- You own your data
- We use data to improve the service
- We may pause service for maintenance

## 6. Payment and Billing
- Fees are charged monthly/annually
- You can cancel anytime
- No refunds for partial months

## 7. Limitation of Liability
- Our liability is limited to fees paid
- We are not liable for lost bookings or damages

## 8. Termination
- We can terminate accounts that violate terms
- You can cancel anytime

## 9. Governing Law
- These terms are governed by laws of India

## 10. Contact
- Questions: legal@yourdomain.com
```

---

## Part 3: Privacy Policy

### What to Include

```markdown
# Privacy Policy

## 1. Information We Collect
- Agency account information
- Trip planning data (destinations, dates, budgets)
- Messages and conversations

## 2. How We Use Information
- Provide the service
- Improve our AI models
- Communicate with you

## 3. Data Storage
- Stored securely in India
- Encrypted at rest and in transit
- Retained while you're a customer

## 4. Data Sharing
- We do not sell your data
- We may share with service providers (hosting, AI APIs)
- We may share if required by law

## 5. Your Rights
- Access your data
- Correct your data
- Delete your data
- Export your data

## 6. Security
- Industry-standard encryption
- Regular security reviews
- Access controls

## 7. Children's Privacy
- Our service is not for children under 13

## 8. Changes
- We may update this policy
- Significant changes will be notified

## 9. Contact
- Questions: privacy@yourdomain.com
```

---

## Part 4: Key Disclaimers

### AI-Specific Disclaimers (Critical)

**Put in UI**:
- "AI-generated suggestions. Verify before booking."
- "Not guaranteed accurate. Use professional judgment."

**Put in contracts**:
- "Agency is solely responsible for all travel bookings and advice given to travelers."
- "Service provides suggestions only, not professional travel advice."

**Why**: If something goes wrong, you need to show you warned them.

---

## Part 5: Data Protection

### India: DPDP Act 2023 Compliance

**Key points**:
- Get consent before collecting data
- Allow data access/deletion requests
- Don't collect more than needed
- Secure storage
- Clear privacy policy

### GDPR (If EU Customers)

**Additional requirements**:
- Explicit consent checkboxes
- Data processing agreement
- EU data storage options
- Right to be forgotten (with exceptions)

**For MVP**: Focus on India DPDP. Add GDPR compliance when you have EU customers.

---

## Part 6: Payment Terms

### What to Include

```markdown
# Payment Terms

## Fees
- Solo: ₹999/month (billed monthly)
- Small: ₹3,999/month (billed monthly)
- Medium: ₹9,999/month (billed monthly)

## Billing Cycle
- Charges on same day each month
- Annual plans available with discount

## Refunds
- No refunds for partial months
- Refunds for service failures (prorated)

## Cancellation
- Cancel anytime, effective next billing cycle
- No cancellation fees

## Payment Methods
- Credit/debit card (Razorpay/Stripe)
- UPI (via Razorpay)
- Bank transfer (annual only)
```

---

## Part 7: Intellectual Property

### What You Own

- Code you write
- Designs, branding
- Documentation
- Training data you create

### What Users Own

- Their trip data
- Their customer information
- Any customizations they request

### Clear Statement

```markdown
# Intellectual Property

## Our IP
- Agency OS platform, code, design, and branding are our property
- You may not copy, modify, or redistribute

## Your IP
- You retain ownership of all data you input
- You may export your data anytime

## User Content
- You grant us license to use your data to improve the service
- We do not claim ownership of your data
```

---

## Part 8: When to Actually Talk to a Lawyer

| Situation | Get a lawyer |
|-----------|--------------|
| First revenue (₹10K+) | Maybe, for basic contract review |
| Raising investment | Yes, absolutely |
| Hiring employees | Yes, employment agreements |
| Handling EU data | Yes, GDPR is complex |
| Someone threatens legal action | Immediately |
| >₹1L MRR | Yes, for proper contracts |

**Cost**: ₹5,000-20,000 for initial consultation. Worth it to avoid bigger problems.

---

## Part 9: Affordable Legal Help

| Option | For what | Approx cost |
|--------|----------|-------------|
| **Vakilsearch** | Basic registration, templates | ₹2,000-5,000 |
| **LegalZoom** | Templates, basic advice | ₹3,000-10,000 |
| **Law firm (small)** | Custom contracts | ₹10,000-30,000 |
| **Law firm (big)** | Complex matters, funding | ₹50,000+ |

**For MVP**: Templates + one review session = sufficient.

---

## Part 10: Legal Checklist (Before Launch)

- [ ] Business entity registered (or plan to)
- [ ] Terms of Service drafted and displayed
- [ ] Privacy Policy drafted and displayed
- [ ] AI disclaimers in UI
- [ ] Payment terms defined
- [ ] Data deletion process documented
- [ ] Contact email for legal/privacy questions
- [ ] Consulted with lawyer (even briefly)

---

## Summary

**This is not legal advice.** Talk to a lawyer.

**Bare minimum**:
1. Terms of Service (especially AI disclaimers)
2. Privacy Policy
3. Data deletion option
4. Clear liability limitations

**Principles**:
- Agencies are responsible for final decisions
- AI suggestions must be verified
- Agencies own their data
- You're not liable for booking outcomes

**When to scale legal effort**: Revenue > ₹20K/month or hiring employees.

**For now**: Basic docs + one lawyer review = good enough for MVP.

---

## Templates

You can find free templates at:
- [Termly](https://termly.io/) (TOS, privacy policy)
- [Privacy Policy Online](https://www.privacypolicyonline.in/) (India-specific)
- [Vakilsearch](https://www.vakilsearch.com/) (legal templates)

**Customize for your specific use case.** Templates are starting points, not final.
