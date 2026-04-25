# Black Spec: Mesh-Handoff & Offline Agency (BLACK-001)

**Status**: Research/Draft
**Area**: Post-Connectivity Logistics & Systemic Survival

---

## 1. The Problem: "The Digital Darkness"
In a scenario where the global fiber backbone or satellite constellation is disabled (e.g., Massive Solar Storm, Targeted Infrastructure Sabotage), the central "Spine" becomes unreachable. Agents lose contact with their "Cloud-Home" and "Financial Clearing Houses." Without a protocol, travel stops entirely.

## 2. The Solution: 'Mesh-Handoff-Protocol' (MHP)

The MHP enables agents to form "Regional Intelligence Clusters" that coordinate logistics locally using short-range mesh nets (Bluetooth, LoRa, Radio) and "Physical-Verification-Tokens."

### Survival Actions:

1.  **Gossip-Protocol-Logistics**:
    *   **Action**: Agents sharing "Resource-Availability" (e.g., "Hub A has fuel," "Train B is moving") across a multi-hop mesh network.
2.  **Physical-Evidence-Minting**:
    *   **Action**: The agent generates a "QR-Handoff-Packet" (offline-signed) that can be scanned by another agent's device to verify a traveler's "Identity, Wallet-Balance, and Priority."
3.  **Local-Consensus-Engine**:
    *   **Action**: Local agents "Vote" on the best use of a scarce resource (e.g., one available bus) based on the "Moral-Utility-Weighting" (ETHIC-001) stored in their local ROM.

## 3. Data Schema: `Mesh_Handoff_Packet`

```json
{
  "packet_id": "MESH-TX-7711",
  "source_agent_id": "AGENT_LOCAL_A",
  "traveler_state_blob": "ENCRYPTED_AES_GCM_BLOB",
  "verification_sig": "OFFLINE_ED25519_SIG",
  "local_timestamp": 1745612345,
  "priority_rank": "TIER_1_LIFE_SAFETY",
  "resource_need": "TRANSPORT_EAST_EXIT"
}
```

## 4. Key Logic Rules

- **Rule 1: Trust-by-Signature**: Since the "Cloud" is gone, agents must trust "Pre-Shared Keys" (PSKs) and "Decentralized Public Keys" to verify each other.
- **Rule 2: Entropy-Aware-Timing**: Agents use "Local Atomic Clocks" or "Radio-Beacons" to maintain a "Shared-Sense-of-Time" to prevent replay attacks on handoff tokens.
- **Rule 3: Graceful-Information-Decay**: Older "Gossip" data is progressively marked as "Low-Confidence" if it hasn't been refreshed within the mesh.

## 5. Success Metrics (Mesh-Survival)

- **Mesh-Latency**: Average time for a "Resource-Alert" to traverse a 10-mile urban mesh.
- **Verification-Success-Rate**: % of "Physical-Handoffs" that were successfully verified by a disconnected counter-party agent.
- **Continuity-Rate**: % of travelers who reached their "Safe-Zone" during a >24h internet blackout.
