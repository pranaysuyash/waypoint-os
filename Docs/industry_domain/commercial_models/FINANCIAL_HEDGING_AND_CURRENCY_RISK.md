# Domain Knowledge: Financial Hedging & Currency Risk

**Category**: Commercial Models  
**Focus**: FX (Foreign Exchange) management, multi-currency bookings, and profit protection.

---

## 1. The "Currency Gap" Risk

Travel agencies often collect money in one currency (e.g., INR) but pay vendors in another (e.g., USD or EUR).

### The Scenario
1. Client pays 10,00,000 INR for a US trip (based on $1 = 80 INR).
2. Agency holds the money for 30 days.
3. By payment day, $1 = 85 INR.
4. **Loss**: The agency now needs 10,62,500 INR to pay the same $12,500 USD. The profit is wiped out.

---

## 2. Risk Mitigation SOPs

### The "Dynamic FX" Buffer
- **Logic**: Adding a 2-5% "Buffer" to the exchange rate used in quotes to the client.
- **SOP**: "Quotes are valid for 24 hours based on today's rate. If the rate fluctuates by >1%, the price will be adjusted."

### Forward Contracts (Hedging)
- **Logic**: Buying the required USD from the bank the *moment* the client pays, to lock in the rate.
- **SOP**: Use "Virtual Multi-currency Wallets" (e.g., Revolut Business, Wise) to hold the currency until the vendor payment is due.

---

## 3. The "GDS ROE" (Rate of Exchange)

### The IATA ROE
- **Logic**: IATA publishes a daily "Rate of Exchange" for all airline tickets.
- **SOP**: The agent must check if the "GDS ROE" is significantly different from the "Market ROE" and decide whether to ticket in local or original currency.

---

## 4. Multi-currency Credit Cards

### The "VCN" (Virtual Card Number)
- **Logic**: Generating a one-time use virtual card in the specific currency of the vendor (e.g., a card in EUR to pay a Paris hotel).
- **Benefit**: Zero FX fees and better reconciliation.

---

## 5. Proposed Scenarios
- **The "Flash Crash"**: A sudden 10% drop in the local currency occurs after the client paid but before the agency paid the DMC.
- **Double FX Fee**: An agent pays a USD vendor using an INR card, but the bank charges an "International Fee" plus a "Markup" on the rate.
- **Pricing Conflict**: A client sees a lower price on a US-based website (because the US site uses a different ROE). The agent must explain the "Currency Logic."
- **Refund Loss**: A client is refunded for a trip, but due to currency changes, they get back less than they paid (or the agency loses money on the refund).
