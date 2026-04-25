# DePIN Spec: Offline-First Resilience (DEPIN-001)

**Status**: Research/Draft
**Area**: Decentralized Infrastructure & Edge Intelligence

---

## 1. The Problem: "The Digital Dead-Zone"
A disruption often happens in places with poor connectivity (e.g., a diverted plane on a remote tarmac, a basement terminal during a storm). If the agent requires a "Cloud Connection" to think, the traveler is left alone in the most critical moment.

## 2. The Solution: 'Edge-Agency' (EA)

The EA protocol enables the mobile agent to function as a "Sovereign Node" without cloud access.

### Resilience Layers:

1.  **Distilled Local Reasoning**:
    *   **Action**: A small, high-quantized LLM (e.g., 2B parameters) runs directly on the smartphone for basic "Re-booking Logic" and "Policy-Adherence" checks.
2.  **Mesh-Network Communication**:
    *   **Action**: Using Bluetooth/Ultra-Wideband (UWB) to "Hop" data between traveler devices at the gate to share "Evidence Snapshots" or "Barter Intel."
3.  **Decentralized State Mirroring**:
    *   **Action**: Cryptographic proofs of "Itinerary State" and "Evidence" are stored on a local DePIN layer (e.g., IPFS/Helium) to ensure they aren't lost if the app is deleted or the phone is damaged.

## 3. Data Schema: `Edge_Sync_Packet`

```json
{
  "node_id": "EA-MOB-9901",
  "sync_priority": "CRITICAL",
  "local_inference_verdict": "BOOK_SHUTTLE_T5_TO_T2",
  "evidence_hash": "sha256:7f8e9a... (Evidence of PNR failure)",
  "mesh_peers_detected": ["EA-MOB-7788", "EA-MOB-1122"],
  "cloud_last_seen": "2026-05-10T14:15:00Z",
  "resilience_mode": "SOVEREIGN_OFFLINE"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Final-State-Anchor'**: Before a plane takes off, the agent MUST "Anchor" the latest itinerary state to the device's local encrypted storage.
- **Rule 2: Mesh-Trust-Anchor**: Agents only share "Barter Intel" or "Evidence" with peers who present a valid "Agency-Signature" (preventing adversarial data injection).
- **Rule 3: Post-Dead-Zone Re-sync**: The moment a "Cloud-Connection" is restored, the Edge node must perform a "Three-Way-Handshake" with the `Spine` and `Evidence Vault` to reconcile all offline decisions.

## 5. Success Metrics (Offline-Agency)

- **Offline-Decision-Rate**: % of disruption events where the agent provided a "Successful Recovery Path" while completely offline.
- **Mesh-Discovery-Time**: Average time to find a peer node in a disconnected terminal (Target: < 10 seconds).
- **Data Integrity**: Zero discrepancies between "Offline-Inference" and "Final-Cloud-Audit" after re-sync.
