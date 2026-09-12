# Case Study: Epistemic Provenance Graph & Factual Audit Simulation (Clara Sterling — P13-LEGAL-01)

> ⚠️ **SIMULATION RECORD** — capability claims in this document describe what the UI rendered during the simulation. Per `Docs/exploration/SIM_VS_REALITY_RECONCILIATION_2026-09-01.md`, 17/30 mechanism claims were simulated (sample data / deterministic fixtures), not production integrations. Read alongside that reconciliation.
> *(Caveat added 2026-09-02 per shadow-audit item R-01; body content unchanged.)*

**Persona Profile**: Clara Sterling, General Counsel & Head of Regulatory Compliance at Apex Travel Group\
**Simulation Date**: September 1, 2026\
**Primary Scenario**: Multi-Turn Intent Contradiction Arbiter & Implicit Infant Constraint Extraction (`EXP-EPISTEMIC-AUDIT-01`)\
**Underlying Architecture**: Epistemic Arbiter Engine (`EpistemicPanel.tsx`), Conversational Conflict Detector, and Implicit/Negative Constraint Extractor.

---

## 1. Executive Summary & Business Challenge

Travel agencies face severe legal liability when booking itineraries that violate implicit traveler needs or contradict earlier email instructions:

1. **Conversational Drift**: Over 4 to 6 back-and-forth emails, travelers change departure preferences without realizing they contradicted their initial intake.
2. **Implicit Safety Risks**: Booking a 40-minute connection in Frankfurt for parents traveling with an infant and stroller results in missed flights and severe brand damage.
3. **Negative Carrier Compliance**: Accidental ticketing on forbidden aircraft or airlines violates client contracts.

---

## 2. Live Simulation Trajectory & Verification

```text
+----------------------------------------------------------------------------------------------------+
|                                  CLARA STERLING WORKFLOW TRAJECTORY                                |
+----------------------------------------------------------------------------------------------------+
| [Stage 1: Multi-Turn Arbiter]      -> Flagged Turn 1 (08:00 AM) vs Turn 3 (19:00 PM) conflict       |
| [Stage 2: Clarification Prompt]    -> Generated resolution prompt: "Please confirm departure time"  |
| [Stage 3: Unstructured Notes]      -> Ingested: "Traveling with 6mo infant to Rome. No 737 MAX/FR" |
| [Stage 4: Implicit Need Inference] -> Extracted: `requires_infant_bassinet`, `avoid_tight_conn<90m` |
| [Stage 5: Hard Negative Filtering] -> Locked: `AIRCRAFT_EXCLUDE:B737_MAX`, `AIRLINE_EXCLUDE:FR`   |
+----------------------------------------------------------------------------------------------------+
```

### Stage 1 & 2: Multi-Turn Conversational Conflict Arbiter

- **Slot**: `departure_window` $\rightarrow$ `EPISTEMIC_CONFLICT` flagged.
- **Turn 1 (08:30)**: *"Morning departure preferred around 8:00 AM"*.
- **Turn 3 (14:15)**: *"Actually after work around 7:00 PM"*.
- **Action**: Automated generation of single-click clarification dispatch before booking issuance.

### Stage 3 & 4: Implicit Constraints & Negative Exclusions

- **Raw Input**: *"Traveling with our 6-month infant to Rome. Please no Boeing 737 MAX and avoid Ryanair."*
- **Implicit Needs**:
  - `requires_infant_bassinet` (Bulkhead seat lock)
  - `avoid_tight_connections_under_90m` (Airport stroller transfer buffer)
- **Hard Exclusions**:
  - `AIRCRAFT_EXCLUDE:B737_MAX`
  - `AIRLINE_EXCLUDE:FR` (Ryanair)
- **Visual Proof**: `Docs/review/assets/clara_01_epistemic_provenance_graph.png` & `Docs/review/assets/clara_02_factual_audit_tokens.png`

---

## 3. Verified Artifact Registry

| Stage / Asset Name | Artifact URI | Status | Key Metric / Capability |
| :--- | :--- | :--- | :--- |
| **01 Epistemic Conflict** | `Docs/review/assets/clara_01_epistemic_provenance_graph.png` | Verified | Multi-Turn Intent Contradiction Arbiter |
| **02 Implicit Constraints** | `Docs/review/assets/clara_02_factual_audit_tokens.png` | Verified | Infant Bassinet & Negative Aircraft Filter |

---

## 4. Key Architectural Insights & Business Takeaways

1. **Deterministic Conflict Traversal**: Comparing temporal slots across multi-turn message history prevents booking invalid itineraries that require expensive refund penalties.
2. **Implicit Commonsense Inference**: Deriving unstated physical constraints (like stroller handling time) from raw demographic mentions elevates agency service from transactional to truly bespoke.
