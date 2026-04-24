# SYSTEM_AUTONOMIC_IMMUNE_RESPONSE: Rule Engine Spec

## 1. The "Self-Healing" Concept
The Autonomic Immune Response (AIR) is a background monitor that identifies "Systemic Sepsis" (Corruption, Inconsistency, or Ethical Failure) and takes corrective action automatically.

## 2. Detection Vectors (Antigens)
What the system "Looks" for:
- **Data Drift**: Inconsistency between `Itinerary` and `SupplierConfirmation`.
- **Financial Leakage**: Unreconciled payments > $500.
- **Ethical Breach**: Booking a supplier with a recent "Critical Human Rights" flag.
- **Agent Hallucination**: AI generating a promise (e.g., "Free Breakfast") that isn't in the net cost contract.

## 3. Response Protocols (Antibodies)

| Severity | Protocol | Action |
|----------|----------|--------|
| **L1 (Subtle)** | `Soothe` | Log warning + Add "Clarification Task" to Agent's Inbox. |
| **L2 (Operational)**| `Isolate` | Block "Send Proposal" until the data drift is resolved. |
| **L3 (Critical)** | `Rollback` | Revert to the last "Clean State" and notify the Agency Owner (P1). |
| **L4 (Sepsis)** | `Shutdown` | Temporarily disable the specialist agent and trigger a "Deep Integrity Audit". |

## 4. Example Rules (Pseudocode)

### Rule: Hallucination Sentinel
```python
IF message.contains("Included") AND NetCost.excludes(service):
   TRIGGER L2_ISOLATE
   REASON: "Agent promised service not found in supplier contract."
```

### Rule: Financial Discrepancy Watchdog
```python
IF (Total_Traveler_Paid - Total_Supplier_Cost) < Agency_Margin_Floor:
   TRIGGER L3_ROLLBACK
   REASON: "Negative margin detected on trip #123. Audit required."
```

### Rule: Ethical Drift
```python
IF Supplier.rating < 2.0 OR Supplier.news_contains("scandal"):
   TRIGGER L1_SOOTHE
   REASON: "Supplier quality dip detected. Suggest alternative."
```

## 5. The "Immunological Memory"
When a response is triggered, the system records the "Outcome":
- Did the Agent fix the issue?
- Was it a false positive?
- Did the correction save margin/reputation?

This "Memory" is fed back into the **Systemic Feedback Loop** to refine the rules.
