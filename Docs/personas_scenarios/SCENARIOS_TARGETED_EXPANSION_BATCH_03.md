# Targeted Scenario Expansion - Batch 03 (Sustainability & Finance)

This batch targets "Zero Coverage" buckets in Sustainability metrics and complex Financial/Treasury operations.

---

## 1. Sustainable & Regenerative Travel

### [SUST-001] Carbon Budget Violation (P3)
- **Persona**: P3 (Junior Agent)
- **Scenario**: A corporate traveler (S1) wants to book a last-minute flight from Mumbai to Delhi. The only available flight is an older, less efficient aircraft with high emissions.
- **Input (System Alert)**: "Warning: Carbon per KM for flight AI-101 exceeds Corporate CSR limit by 15%."
- **N01 Fact**: { "flight": "AI-101", "emission_over_limit": 0.15, "client_policy": "CSR-2026" }
- **N02 Decision**: Proceed with caution. Flag the violation to the Junior Agent. Propose an alternative "Train" option (Tejas Express) which is 90% lower carbon, or suggest an immediate "Carbon Offset" purchase of $5 to neutralize the excess.
- **Failure Mode**: Stage Blindness. System ignores the carbon limit and books the flight, causing a CSR audit failure later.

### [SUST-002] "Greenwashing" Supplier Vetting (P2)
- **Persona**: P2 (Agency Owner)
- **Scenario**: A new hotel in Bali claims to be "Eco-Friendly" but a recent traveler review in the `AuditStore` mentions they use single-use plastic bottles in all rooms.
- **Input (AuditStore Event)**: "Traveler Feedback for Hotel_X: 'They claim eco-friendly but gave us 4 plastic bottles a day.'"
- **N01 Fact**: { "supplier": "Hotel_X", "claim": "eco", "evidence": "plastic_use", "contradiction": "high" }
- **N02 Decision**: Stop. Flag the supplier in the master database. Notify the Junior Agents (P3) to stop recommending Hotel_X for "Sustainability-focused" leads until they provide proof of policy change.
- **Failure Mode**: Contradiction Blind. System continues to tag the hotel as "Green" based on the hotel's own marketing data.

---

## 2. Financial Operations & Treasury

### [FIN-001] Forex Margin Erosion Catch (P2)
- **Persona**: P2 (Agency Owner)
- **Scenario**: The agency quoted a $10,000 Luxury trip to a traveler 3 days ago. The traveler just paid in INR. In those 3 days, the USD has strengthened by 2% against INR.
- **Input (Payment Received)**: "Payment of ₹8,35,000 received for Trip_101."
- **N01 Fact**: { "quoted_usd": 10000, "inr_received": 835000, "current_usd_rate": 85.2, "margin_impact": -17000 }
- **N02 Decision**: Stop. The margin has eroded by ₹17,000. Alert the Owner. Propose using a "Multi-Currency Wallet" balance to pay the supplier at the old rate if available, or apply a "Forex Surcharge" if the contract allows.
- **Failure Mode**: False Positive. System assumes the INR amount is "Full Payment" and proceeds to pay the supplier at a loss.

### [FIN-002] LRS Limit Breach Detection (S1)
- **Persona**: S1 (Individual Traveler - High Value)
- **Scenario**: A traveler is booking a "Family World Tour" costing $60,000.
- **Input (Quote Request)**: "Book the $60k tour for my family of 4."
- **N01 Fact**: { "traveler": "VIP_X", "amount": 60000, "statutory_limit": 250000 }
- **N02 Decision**: Proceed. Request PAN card copies for all 4 travelers. Calculate the 20% TCS (₹10,00,000+) that must be collected upfront. Verify if the traveler has already used their LRS limit with other agencies this year.
- **Failure Mode**: Stage Blindness. System fails to mention the 20% TCS requirement until the final payment page, causing the traveler to drop out in frustration.
