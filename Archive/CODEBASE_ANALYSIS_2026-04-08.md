# Travel Agency Agent - Comprehensive Codebase Analysis

**Generated**: 2026-04-08  
**Project**: travel-agency-agent  
**Status**: Early Stage (Design Complete, Implementation Minimal)

---

## Executive Summary

This is a **B2B Revenue and Operations Copilot for Boutique Travel Agencies** - an ambitious AI-powered operating system designed to help small travel agencies automate their workflow from lead intake to trip execution.

### The Core Thesis

Not a consumer trip planner, but an **Agency Copilot** that compresses the workflow:

```
Lead Intake → Constraint Solving → Option Research → Trade-off Ranking → Packaging → Change Handling → Execution
```

---

## Current State Assessment

### ✅ What's Done (Well Done)

| Area                       | Status   | Quality                                                   |
| -------------------------- | -------- | --------------------------------------------------------- |
| Product Vision & Strategy  | Complete | Excellent - Clear positioning, monetization, value props  |
| Architecture Documentation | Complete | Excellent - Two-loop system, state management, provenance |
| Data Models & Schemas      | Complete | Excellent - JSON schemas with full provenance tracking    |
| Agent Taxonomy             | Complete | Excellent - 20+ agents mapped with clear responsibilities |
| Decision Policies          | Complete | Good - State machine logic defined                        |
| Question Bank              | Complete | Good - Priority-ordered question taxonomy                 |

### ⚠️ What's Partially Done

| Area            | Status                            | Notes                                                |
| --------------- | --------------------------------- | ---------------------------------------------------- |
| Notebooks       | 2 files, NB02 has 7 passing tests | NB01: prototype code, NB02: complete with tests (A-) |
| Data Fixtures   | Empty dirs                        | Directory structure for test data exists, no data    |
| Prompt Registry | Empty dirs                        | Registry structure planned, not populated            |
| Source Code     | Empty                             | All src/ subdirectories are empty                    |

### ❌ What's Missing

| Area                | Priority |
| ------------------- | -------- |
| Core Implementation | Critical |
| Tests               | Critical |
| LLM Integration     | Critical |
| Database Layer      | High     |
| API/Interface       | High     |
| Voice Integration   | High     |
| PDF/URL Ingestion   | High     |
| Deployment Config   | High     |
| CI/CD               | Medium   |

---

## Project Structure

```
travel_agency_agent/
├── src/                    # EMPTY - All subdirectories empty
├── Docs/                   # EXCELLENT - 15 comprehensive docs
├── specs/                  # EXCELLENT - JSON schemas & specs
├── prompts/                # EMPTY
├── notebooks/              # SKELETON - 2 prototype notebooks
├── data/                   # EMPTY DIRS
├── pyproject.toml          # Minimal dependencies
├── main.py                 # Placeholder only (6 lines)
└── README.md               # EMPTY
```

---

## Technical Architecture (Documented)

### The Two-Loop System

**Online Loop (Production)**: Source → Normalize → Validate → Infer → Decide → Execute → Log

**Offline Loop (Autoresearch)**: Eval Harness → Mutation → Score → Persist (if improved)

### Core Data Model: The Canonical Packet

Sophisticated state management with provenance tracking. Every field has 7 authority levels from manual_override to unknown.

---

## Key Features (Planned)

1. **Voice Intake Orchestration** - Two-screen model with dynamic question routing
2. **"Wasted Spend" Detection** - Analyzes utility per person (the moat)
3. **Audit Mode** - Upload itineraries, get fit scores and recommendations
4. **Sourcing Hierarchy** - Mirrors real agency: Internal → Preferred → Network → Open Market

---

## Key Questions

### Strategic

1. Has customer development been done with actual travel agencies?
2. Is voice required for v1, or can text work initially?
3. How does this differ from existing tools?

### Technical

4. Which LLM providers? (OpenAI, Anthropic, local?)
5. What's the data security strategy?
6. Which CRM/OTA integrations are needed?

### Business

7. Pricing model? (Per-trip, per-planner, freemium?)
8. Go-to-market strategy?

---

## Recommendations

### Immediate (This Week)

1. Populate the README
2. Create a working skeleton - one happy path
3. Add LLM and web framework dependencies

### Short-Term (2-4 Weeks)

4. Start with text, not voice
5. Implement ONE agent well (Client Intake)
6. Create test fixtures
7. Build the prompt registry
8. Add basic CI/CD

### Medium-Term (1-3 Months)

9. Build the Eval Harness
10. Ship Audit Mode first (perfect wedge feature)
11. Add database layer
12. Build API layer

---

## Conclusion

**Well-conceived, now executing.**

## Environment & Tooling

- **Package manager**: `uv` — all commands: `uv run python ...`, `uv run pytest`, `uv run jupyter notebook`
- **Python**: 3.13, venv at `.venv/`
- **Rule**: Never use system Python. Always use `uv run` or `.venv/bin/python`.

## Notebook Progress

| Notebook                    | Status        | Tests       |
| --------------------------- | ------------- | ----------- |
| 01 - Intake & Normalization | Prototype     | —           |
| 02 - Gap & Decision         | Complete (A-) | 7/7 passing |
| 03 - Session Strategy       | Next          | —           |

The documentation is exceptional. The architecture is thoughtful with proper attention to provenance and state management.

However, there is virtually no working code:

- 15+ documentation files
- 9 specification files
- 0 production implementations
- 0 tests
- 0 API endpoints

### Bottom Line

Great vision, excellent planning, now needs ruthless execution focus on a much narrower MVP. Consider shipping "Audit Mode" first - it demonstrates value with 1/10th the complexity.

---

_Generated by Claude Code CLI for travel-agency-agent project review._
