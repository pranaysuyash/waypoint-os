# Additional Scenario 39: Multi-Currency Pricing Confusion

**Scenario**: A customer is confused by pricing shown in multiple currencies, and the system must clarify totals, exchange rates, and local payment options.

---

## Situation

A quote includes components priced in USD, EUR, and local currency, and the customer is unsure what they will actually pay.
They expect the agency to present a single, clear total and explain any exchange-rate assumptions.

## What the system should do

- Normalize the quote into the customer’s preferred currency
- Show the exchange rate assumptions and any fees
- Explain which components are payable locally vs in advance
- Avoid surprising the customer with hidden currency costs

## Why this matters

Multi-currency quotes are a common source of distrust.
Clear pricing prevents friction and reduces cancellation risk.

## Success criteria

- The customer sees one understandable total
- Exchange-rate handling is transparent
- The system flags local-currency components clearly
