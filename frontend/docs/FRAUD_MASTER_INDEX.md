# Travel Fraud Detection & Prevention — Master Index

> Exploration of fraud detection signals, payment fraud prevention, identity verification, and incident response.

| # | Document | Focus |
|---|----------|-------|
| 01 | [Detection Signals & Risk Scoring](FRAUD_01_DETECTION.md) | Fraud taxonomy, risk scoring model, anomaly detection, behavioral baselines |
| 02 | [Payment Fraud Prevention](FRAUD_02_PAYMENT.md) | Pre/during/post payment checks, chargeback management, PCI-DSS compliance |
| 03 | [Identity Verification](FRAUD_03_IDENTITY.md) | KYC automation, document fraud detection, customer authentication |
| 04 | [Investigation & Response](FRAUD_04_RESPONSE.md) | Investigation workflow, incident response, recovery, continuous monitoring |

---

## Key Themes

- **Prevent over recover** — Every ₹1 spent on prevention saves ₹10 in recovery. Focus on blocking fraud before it happens, not chasing losses after.
- **Risk-based, not rule-based** — Different customers, bookings, and payment methods carry different risk levels. Apply friction proportional to risk, not uniformly.
- **Evidence is everything** — In chargeback disputes and fraud investigations, evidence wins. Collect everything: communication logs, verification records, service delivery proof.
- **Internal fraud is the biggest risk** — External fraud is visible and blockable. Internal fraud (agent collusion, phantom suppliers) is harder to detect and causes larger losses.
- **Customer experience first** — 99%+ of bookings are legitimate. Fraud prevention must be invisible to genuine customers and only surface for suspicious activity.

## Integration Points

- **Booking Engine** — Risk scoring at booking creation, enhanced verification triggers
- **Payment Processing** — 3DS enforcement, card validation, chargeback handling
- **Customer Identity** — KYC verification, document checks, authentication
- **Supplier Invoice** — Supplier verification, phantom invoice detection
- **Agent Training** — Fraud awareness training, internal fraud prevention
- **Analytics & BI** — Fraud monitoring dashboard, chargeback analytics
- **Legal & Compliance** — FIR filing, CERT-In reporting, audit trail
