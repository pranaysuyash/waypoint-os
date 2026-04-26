# Corp Spec: Agentic 'IP-Protection' Watchdog (CORP-REAL-021)

**Status**: Research/Draft
**Area**: Agency Intellectual Property & Asset Protection

---

## 1. The Problem: "The Itinerary-DNA Theft"
A travel agency's most valuable asset is often its unique, expertly-curated itineraries (e.g., "The Secret Samurai Trails of Kyushu"). In a multi-tenant ecosystem, there is a risk of "Content-Leakage" or "Scraping" by competitor agencies. If a proprietary itinerary is replicated without authorization, the originating agency loses its "Competitive-Edge" and "Asset-Value."

## 2. The Solution: 'Intellectual-Property-Protection-Protocol' (IPPP)

The IPPP acts as the "Digital-Curator-Guard."

### Protection Actions:

1.  **Itinerary-DNA Fingerprinting**:
    *   **Action**: Generating a unique "Logical-Fingerprint" for every proprietary itinerary. This captures the specific sequencing, vendor selection, and "Hidden-Gem" markers that make the product unique.
2.  **Ecosystem-Replication-Monitor**:
    *   **Action**: Monitoring the broader SaaS ecosystem for itineraries that have a "High-Similarity-Score" (e.g., >85%) to a protected fingerprint.
3.  **Dynamic-Watermarking**:
    *   **Action**: Injecting "Traceable-Artifacts" into the itinerary presentation (e.g., unique routing variations or specific descriptions) that, if replicated, provide "Forensic-Proof" of copying.
4.  **Automated-IP-Enforcement**:
    *   **Action**: If a violation is detected, the agent autonomously issues a "Digital-Cease-and-Desist" to the offending tenant and notifies the ecosystem administrators.

## 3. Data Schema: `IP_Protection_Audit`

```json
{
  "audit_id": "IPPP-55221",
  "itinerary_id": "SAMURAI-KYUSHU-001",
  "owner_agency_id": "AGENCY_ALPHA",
  "similarity_event_detected": {
    "detected_tenant_id": "AGENCY_OMEGA",
    "similarity_score": 0.92,
    "matching_markers": ["SECRET_VALLEY_HIKE", "TEA_HOUSE_EXCLUSIVE"]
  },
  "status": "ENFORCEMENT_PENDING"
}
```

## 4. Key Logic Rules

- **Rule 1: The 'Fair-Use' Buffer**: The agent MUST distinguish between "Industry-Standard-Sequencing" (e.g., Tokyo -> Kyoto) and "Proprietary-Product-Innovation" (e.g., a specific private temple opening). Only unique innovations are protected.
- **Rule 2: Authorization-Registry**: Owners MUST be able to authorize "White-Label-Sharing" of their itineraries with specific partners (e.g., via the Inter-Agency-Handoff-Protocol).
- **Rule 3: Non-Destructive-Alerting**: Before taking enforcement action, the agent MUST verify that the matching itinerary wasn't created independently using publicly available information.

## 5. Success Metrics (IP Protection)

- **Uniqueness-Preservation-Rate**: % of protected itineraries that remain exclusive to the owner or authorized partners.
- **Theft-Detection-Latency**: Time between an unauthorized replication and the IP watchdog detection.
- **Commercial-Value-Protected**: Estimated USD value of exclusive products maintained through agentic enforcement.
