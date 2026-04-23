# Additional Scenario 319: The Post-Trip GDPR Cleanse

**Scenario**: A VVIP traveler requests a "Full Data Purge" after a sensitive business trip to a high-risk jurisdiction. The system must orchestrate the deletion across multiple fragmented supplier systems.

---

## Situation

- Traveler (S1) is a high-profile CEO. 
- The trip involved stay in 3 hotels and 2 regional airlines in a country with high surveillance.
- The CEO invokes the "Right to be Forgotten" (GDPR) and wants absolute confirmation that their PNR, passport copies, and preferences are purged.

## What the system should do

- Identify every digital "Touchpoint" where the traveler's PII was sent (GDS, Hotel PMS, Airline DCS).
- Trigger "Automated Deletion Requests" to all suppliers via API or standardized legal email.
- Anonymize the traveler's record in the Agency's internal database (keeping only the financial aggregate for tax reasons).
- Issue a "Certificate of Purge" to the traveler, documenting the successful deletion at each node.

## Why this matters

GDPR compliance is easy for local data, but "Travel Data" is globally fragmented.
Providing a "Purge Orchestrator" is a premium service that guarantees privacy in a world of persistent digital shadows.

## Success criteria

- All PII (Name, Passport, DOB) is removed from the system.
- Success/Failure responses from suppliers are tracked.
- The traveler receives a formal, high-trust confirmation report.
