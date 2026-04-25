# Legal Spec: Autonomous Evidence Vault (LE-002)

**Status**: Research/Draft
**Area**: Forensic Logging & Evidence Preservation

---

## 1. The Problem: "The Volatile decision"
AI decisions happen in milliseconds. By the time a legal claim is filed (often months later), the specific prompts, model versions, and transient supplier API responses may be gone, leaving the agency with no way to defend its "Reasonableness."

## 2. The Solution: 'Defense-Snapshot-Protocol' (DSP)

The DSP creates an immutable, cryptographically hashed "Evidence Bundle" for every `Operational_Exception` or `High_Value_Action`.

### Snapshot Contents:

1.  **Model Metadata**: Model ID, Version, and specific System-Prompts used.
2.  **Inference Trace**: The raw input (User message), the AI "Thought Process" (Reasoning chain), and the final Output.
3.  **Supplier Telemetry**: The raw HTTP Request/Response logs from the external vendor (e.g., Sabre, Amadeus).
4.  **Environmental Context**: Global status (Strikes, weather) at the time of the decision.
5.  **State Differential**: The database state before and after the action.

## 3. Data Schema: `Evidence_Bundle`

```json
{
  "bundle_id": "EV-5544-XZ",
  "incident_id": "OE-1122",
  "timestamp": "2026-05-10T09:30:00Z",
  "hash_algorithm": "SHA-256",
  "merkle_root": "0x5f33e...",
  "storage_location": "WORM_BUCKET_PRIMARY",
  "retention_policy": "7_YEARS_LEGAL",
  "contents": [
    "prompt_log_v2.json",
    "vendor_api_trace_9922.pcap",
    "db_snapshot_pre_post.sql"
  ]
}
```

## 4. Key Logic Rules

- **Rule 1: WORM Storage**: All Evidence Bundles must be stored in "Write Once, Read Many" (WORM) storage to prevent tampering (even by internal admins).
- **Rule 2: PII Anonymization**: All evidence is stored with "Preserved-Privacy." PII is encrypted with a "Legal-Key" that requires multi-party authorization to decrypt for court use.
- **Rule 3: Auto-Discovery**: If the `Legal_Assessment` (LE-001) flags an incident as "High-Liability," the system auto-notifies the internal legal team with a link to the `Evidence_Bundle`.

## 5. Success Metrics (Forensics)

- **Audit Pass Rate**: % of snapshots that are verified as authentic and complete during internal/external audits.
- **Defense Success**: % of legal claims dismissed or settled favorably due to "High-Fidelity Evidence."
- **Data Integrity**: Zero instances of tampered or deleted decision logs.
