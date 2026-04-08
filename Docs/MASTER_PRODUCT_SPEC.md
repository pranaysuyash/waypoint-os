# Comprehensive Agency OS Product Specification

## 1. Product Vision & Thesis
The system is a **B2B Revenue and Operations Copilot for Boutique Travel Agencies**. 
It is not a generic AI trip planner; it is an operational workflow optimizer.

### Core Value Props:
- **Workflow Compression**: Reduces the time from lead to first high-quality quote.
- **Operational Intelligence**: Captures the "hidden" logic of a planner (e.g., "Hotel X is great for Indians because of breakfast").
- **Risk Mitigation**: Detects "wasted spend" (e.g., paying for Universal Studios for a group where 3/5 people cannot use it).
- **Sourcing Hierarchy**: Optimizes for: $\text{Internal Packages} \rightarrow \text{Preferred Partners} \rightarrow \text{Network/Consortium} \rightarrow \text{Open Market}$.

---

## 2. The Voice Intake Orchestration Spec

### A. The Two-Screen Model
1. **Agency Screen**:
    - **Input**: Lead notes from 1st call, referral source, rough budget, family composition.
    - **Output**: A unique session link for the traveler.
2. **Traveler Screen**:
    - **Experience**: Joins a voice session; sees a **Live Trip Brief** updating in real-time on the right panel.

### B. Backend Orchestration (The Loop)
The system uses a dynamic question router, not a static script.
1. **State Extraction**: User answer $\rightarrow$ Structured field update.
2. **Classification**: Assigns "brackets" (e.g., `family_with_toddler`, `shopping_first`, `comfort_first`).
3. **Gap Detection**: Identifies missing critical fields.
4. **Next-Question Policy**:
    - $\text{Priority 1}$: Blocking unknowns (Destination, Budget).
    - $\text{Priority 2}$: Contradiction resolution.
    - $\text{Priority 3}$: Route-changing fields.
    - $\text{Priority 4}$: Low-value refinements.

### C. The "Audit Mode" (High Value Wedge)
- **Input**: PDF, URL, or pasted text of an existing itinerary/package.
- **Process**:
    - Extract hotels, activities, and costs.
    - Compare against actual group composition (elderly, kids).
    - **Output**: Fit Score, Waste Flags, Missing Cost Buckets, and a "Smarter Alternative."

---

## 3. Technical Routing & Optimization Architecture

### A. The Production Path (Online Loop)
1. **Context Normalization**: Raw context $\rightarrow$ `Normalized Context Packet`.
2. **Intake Router**: Cheap model $\rightarrow$ `Fixed Taxonomy` (e.g., `billing`, `sales`).
3. **Prompt Composer**: Registry-based assembly (`Base` + `Domain` + `Policy` + `Few-Shot`).
4. **Specialist Execution**: Specialist agent generates response.
5. **Verifier Layer**: Checks for hallucinations, policy violations, and missed required fields.

### B. The Self-Improvement Path (Offline Loop / Autoresearch)
Inspired by Karpathy's autoresearch, the system evolves without risking live stability.
- **Eval Harness**: A gold-labeled dataset of 200-500 cases.
- **Mutation Loop**: 
    - Mutate a single dimension (e.g., a few-shot example or a router prompt).
    - Run against the Eval Harness.
    - Measure `Composite Score` (Routing Accuracy + Tool F1 + Quality).
    - Persist only if the score improves.

---

## 4. Data Model & Entity Schema

### Traveler Profile
- `members`: List of types (adult, toddler, elderly) and constraints.
- `brackets`: Classification tags.
- `preferences`: Food, shopping, pace, hotel style.

### Supplier Inventory
- `partner_profile`: Destination, star category, commission band, toddler-friendliness, reliability notes.
- `internal_packages`: Pre-built, high-conversion bundles.

### Budget Model
- `total_budget`: Total amount.
- `splits`: Allocated buckets for Flights, Stay, Food, Activities, Shopping, Buffer.

---

## 5. Implementation Roadmap (MVP)
1. **Phase 1**: Deterministic skeleton (Router $\rightarrow$ Registry $\rightarrow$ Generalist Agent $\rightarrow$ Verifier).
2. **Phase 2**: Eval Harness & 200+ labeled cases.
3. **Phase 3**: Offline Autoresearch loop for Router and Prompt Packs.
4. **Phase 4**: Specialized agent split based on error clusters.
