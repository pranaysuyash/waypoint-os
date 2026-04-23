# Additional Scenario 79: Slow Customer Response Risk

**Scenario**: A customer delay in responding risks losing a time-sensitive booking, and the system must prompt the customer and protect the holding status.

---

## Situation

The agency is waiting on a customer decision for a quote or hold that expires soon.
They need to nudge the customer without causing pressure and preserve the booking if possible.

## What the system should do

- Track pending customer decisions and expiration deadlines
- Send clear reminders with the consequences of waiting too long
- Offer a shorter decision window if needed
- Keep the tone helpful and time-oriented, not desperate

## Why this matters

Slow responses are a common lost-opportunity source.
A proactive system can recover business before deadlines expire.

## Success criteria

- The system alerts both agent and customer before expiration
- It preserves the booking or offers the next best option
- The customer feels informed, not pushed
