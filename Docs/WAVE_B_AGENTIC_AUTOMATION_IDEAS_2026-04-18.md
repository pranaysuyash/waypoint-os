# Wave B — Agentic Automation & Flow Expansion Ideas
**Date**: 2026-04-18
**Context**: Building upon the deterministic foundation of the Spine API and the lifecycle management introduced in Wave A. This document outlines concrete strategies to inject true "agentic" capabilities into the Waypoint OS platform.

---

## The Core Philosophy
The current architecture prioritizes safety and determinism (the "Spine"). It parses, identifies gaps, and scores confidence perfectly. However, when it hits an ambiguity or a gap, it simply flags it and stops (the `blocked` state). 

The goal of **Wave B** is to transition from *passive gap identification* to *active gap resolution* and *proactive operator assistance*, without compromising the safety boundaries established in Wave A.

---

## 1. Proactive Information Retrieval (The "Scout" Agent)
Currently, if a destination requires a visa, or if a specific activity is requested, the system relies on static logic or human intervention.

*   **The Idea:** Introduce a specialized retrieval agent that runs parallel to or immediately after the `NB02 (Decision)` stage.
*   **How it works:** 
    *   If `NB02` flags `Missing Information: Visa Requirements for Destination X (Passport Y)`, the Scout Agent is dispatched.
    *   It uses external APIs (e.g., Sherpa, or targeted web search) to fetch the real-time requirements, processing times, and costs.
    *   **Outcome:** Instead of telling the operator "Find out visa info," the system populates the `StrategyBundle` with "Visa required: E-Visa, $50, takes 3 days. [Link to portal]."

## 2. Autonomous Clarification Drafting (The "Communicator")
When an inquiry is fundamentally contradictory (e.g., "We want a luxury 5-star experience for $500 total in Paris"), the pipeline currently blocks.

*   **The Idea:** Leverage an LLM agent specifically tuned for empathetic, conversion-optimized B2B communication.
*   **How it works:**
    *   When the run hits a `blocked` state due to `Contradiction` or `Critical Ambiguity`, the Communicator agent analyzes the `DecisionState`.
    *   It drafts 1-3 options for a WhatsApp or Email message that the operator can send to the client with one click.
    *   *Example Draft:* "Hi [Name], we'd love to put this Paris trip together! To get you the true 5-star experience you're looking for, we'd typically need to look at a budget closer to $X. Alternatively, for $500, we can curate a fantastic boutique 3-star experience in a great neighborhood. Which direction feels better to you?"
    *   **Outcome:** Reduces operator cognitive load from "How do I say no nicely?" to "Click to send."

## 3. The Self-Healing Evaluation Loop (The "QA" Agent)
Wave A introduces a deterministic step ledger and event audit trail (`run_failed`, `run_blocked`). This is a goldmine for continuous improvement.

*   **The Idea:** Automate the "Offline Loop" entirely.
*   **How it works:**
    *   A background agent (running nightly or triggered on specific errors) sweeps the audit trail for runs that failed or were blocked due to parsing errors or unhandled edge cases.
    *   The QA Agent sanitizes the PII from the raw inquiry.
    *   It formulates a new JSON test fixture representing this edge case and commits it to `data/fixtures/`.
    *   It can optionally draft a PR to adjust the `extractors.py` regex or LLM prompts to handle this new fixture.
    *   **Outcome:** The system's test coverage and robustness grow autonomously based on real-world agency traffic.

## 4. Multi-Agent Decision Debate (The "Committee")
For simple point-to-point trips, a single processing pass is sufficient. For complex, high-value, multi-destination inquiries, the "first answer" is rarely the best.

*   **The Idea:** Implement a scoped LangGraph (or similar) multi-agent workflow specifically for the `NB03 (Strategy)` phase of complex trips.
*   **How it works:**
    *   Instantiate two opposing specialist agents: 
        1.  **The Budget Optimizer:** Mandated to find the most cost-effective routing and vendor combinations.
        2.  **The Experience Maximizer:** Mandated to optimize for comfort, minimal layovers, and premium vendor selection.
    *   A third **"Trip Architect"** agent reviews both proposals, synthesizes the trade-offs, and presents a blended `StrategyBundle` to the operator.
    *   **Outcome:** Higher quality itineraries for complex trips, giving the operator immediate access to "High/Medium/Low" tier options without manual sourcing.

## 5. Conversational State Interventions (The "Operator Copilot")
The UI currently allows the operator to review the `Packet`. If it's wrong, manual editing is required.

*   **The Idea:** Embed a conversational agent directly into the Next.js Workbench UI that can mutate the backend state safely.
*   **How it works:**
    *   The operator views a completed run. The system inferred "Family Trip", but the operator knows it's a "Honeymoon" from a previous phone call.
    *   Instead of navigating forms, the operator types into a command bar: *"Actually, this is a honeymoon. They want adults-only resorts."*
    *   The Copilot Agent understands the context, patches the `CanonicalPacket` (changing `trip_type` to `Honeymoon` and adding `adults_only` to preferences), and safely re-triggers the pipeline from `NB02`.
    *   **Outcome:** Drastically speeds up corrections and edge-case handling using natural language against a structured state machine.

---

## Implementation Phasing Recommendation

1.  **Phase 1 (Immediate leverage):** Autonomous Clarification Drafting (Communicator). *Why?* It plugs directly into Wave A's `blocked` state and provides immediate time-savings for the operator.
2.  **Phase 2 (UX enhancement):** Conversational State Interventions (Copilot). *Why?* Requires Wave 2 Frontend completion, but makes the tool feel truly "magical" and fluid.
3.  **Phase 3 (Data moats):** The Self-Healing Evaluation Loop (QA). *Why?* Requires a critical mass of real runs to be valuable, but creates an insurmountable data advantage over time.
4.  **Phase 4 (Deep Intelligence):** Proactive Retrieval & Multi-Agent Debate. *Why?* High complexity, requires robust external integrations (APIs, scraping) and careful prompt tuning to avoid hallucination.
