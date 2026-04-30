# Customer Credit & Wallet — Master Index

> Research on customer credit balances, store wallet, refund-as-credit programs, promotional credits, gift card balances, credit expiry management, and credit analytics for the Waypoint OS platform.

---

## Series Overview

This series covers the customer credit and wallet system — the stored-value layer that retains revenue from cancellations, incentivizes rebooking, and drives repeat purchases. From refund-as-credit with bonus incentives (cancel a Goa trip, get ₹8,800 credit instead of ₹8,000 refund) to promotional welcome credits, loyalty point conversions, and gift card balances, the wallet is the agency's customer retention and revenue-recovery engine.

**Target Audience:** Product managers, finance managers, agents

**Key Insight:** 85% of cancelled-trip revenue is recovered when customers choose refund-as-credit with a 10% bonus. A customer with ₹5,000+ in wallet credit has a 40% higher rebooking rate than one without. The credit wallet isn't just a payment feature — it's a retention strategy that converts cancellation disappointment into future booking commitment.

---

## Documents

| # | Document | Focus |
|---|----------|-------|
| 1 | [CUSTOMER_CREDIT_01_WALLET.md](CUSTOMER_CREDIT_01_WALLET.md) | Credit sources (refund-as-credit, promo, loyalty, gift card, voucher), credit rules engine, combination and partial usage, expiry management with notifications, credit analytics, fraud prevention |

---

## Key Themes

### 1. Refund-as-Credit Recovers Revenue
When a customer cancels, offering credit + 10% bonus instead of cash refund recovers 85% of revenue. The customer feels compensated (bonus), the agency retains the booking value, and the credit drives a future booking.

### 2. Expiring Credits Drive Urgency
A credit expiring in 30 days creates the same urgency as a flash sale. Expiry notifications ("Your ₹500 credit expires next week!") convert dormant customers into active bookers at zero acquisition cost.

### 3. Credit Balance = Re-engagement Signal
Customers with credit in their wallet are pre-qualified for re-engagement. The credit is a reason to reach out ("You have ₹8,800 credit — want to use it for a Singapore trip?") that feels helpful, not spammy.

### 4. Track Liability Carefully
Every credit issued is a liability on the balance sheet. The finance team needs real-time visibility into total outstanding credits, expiry schedules, and utilization rates to manage cash flow.

---

## Cross-References

| Related Series | Connection |
|---------------|------------|
| Refund & Cancellation (REFUND_CANCELLATION_*) | Refund-as-credit option during cancellation |
| Loyalty (LOYALTY_*) | Loyalty points to credit conversion |
| Voucher & Coupons (VOUCHER_*) | Voucher credit to wallet |
| Payment Processing (PAYMENT_PROCESSING_*) | Credit as payment method at checkout |
| Finance (FINANCE_*) | Credit liability accounting |
| Referral & Viral (REFERRAL_VIRAL_*) | Referral reward credits |
| Email Marketing (EMAIL_MKTG_*) | Credit expiry notification campaigns |
| Customer Onboarding (CUSTOMER_ONBOARD_*) | Welcome credit issuance |
| Complaint Management (COMPLAINT_RES_*) | Apology credit compensation |
| Deals & Promotions (DEALS_PROMO_*) | Promotional credit issuance |
| Trip Budget (TRIP_BUDGET_*) | Credit application to trip budget |

---

**Created:** 2026-04-30
