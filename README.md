# Waypoint OS

**B2B Revenue and Operations Copilot for Boutique Travel Agencies.**

Waypoint OS is an AI-powered operations platform that helps boutique travel agencies manage inbound inquiries, make intelligent booking decisions, generate strategy prompts, and maintain revenue pipeline health — all through a structured two-loop system.

## What It Does

- **Intake & Normalization**: Parse vague, contradictory, or under-specified travel inquiries from agency inboxes and normalize them into structured trip packets
- **Gap Analysis & Decision**: Identify missing information, infer traveler preferences, classify trips (domestic/international), and score decision confidence
- **Session Strategy & Prompt Bundle**: Build traveler-safe output bundles and internal operator packets with strategy context
- **Workbench UI**: Next.js frontend for operators to review, validate, and execute the full pipeline

## Architecture

### Two-Loop System

| Loop             | Purpose                                                        |
| ---------------- | -------------------------------------------------------------- |
| **Online Loop**  | Source → Normalize → Validate → Infer → Decide → Execute → Log |
| **Offline Loop** | Eval Harness → Mutation → Score → Persist (if improved)        |

### Pipeline Stages

```
Inquiry → NB01 Intake → NB02 Gap & Decision → NB03 Strategy & Prompt → Output
```

| Stage               | Responsibility                               | Key Outputs                           |
| ------------------- | -------------------------------------------- | ------------------------------------- |
| **NB01 — Intake**   | Parse, normalize, classify                   | SanitizedPacket, geography extraction |
| **NB02 — Decision** | Gap detection, confidence scoring, inference | DecisionState, gap_report, confidence |
| **NB03 — Strategy** | Traveler-safe bundle + internal prompt       | StrategyBundle, follow-up questions   |

### Safety Model

- **Traveler-safe output**: Structurally excludes raw packet data, internal confidence scores, and decision_state
- **Internal bundle**: Full access to raw packet, confidence, and strategy context
- **Leakage detection**: Production code path enforces separation (validated by 38+ tests)

## Project Structure

```
├── src/intake/              # Core pipeline implementation
│   ├── geography.py         # GeoNames + world cities destination filtering
│   ├── extractors.py        # Trip detail extraction from natural language
│   ├── decision.py          # Gap detection, confidence scoring, inference
│   ├── strategy.py          # Traveler-safe + internal bundle builders
│   ├── safety.py            # SanitizedPacketView and leakage detection
│   ├── validation.py        # Input validation rules
│   └── orchestration.py     # Pipeline coordination
├── frontend/                # Next.js operator workbench
│   ├── src/app/             # Routes (inbox, workbench, owner views)
│   ├── src/components/      # UI components + design system
│   └── src/lib/             # API clients, stores, types
├── notebooks/               # Prototype & evaluation notebooks
├── tests/                   # Unit, integration, and E2E tests
├── data/fixtures/           # Scenario fixtures and test data
├── specs/                   # JSON schemas and contracts
├── prompts/                 # LLM prompt templates
├── Docs/                    # Product specs, decision logs, strategy docs
└── memory/                  # Project memory and institutional knowledge
```

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Install dependencies
uv sync

# Run the backend
uv run python main.py

# Run tests
uv run pytest

# Run the frontend
cd frontend && npm install && npm run dev
```

### Key Commands

| Command                      | Purpose                   |
| ---------------------------- | ------------------------- |
| `uv sync`                    | Install dependencies      |
| `uv run python main.py`      | Run backend server        |
| `uv run pytest`              | Run test suite            |
| `uv run jupyter notebook`    | Open notebooks            |
| `cd frontend && npm run dev` | Start frontend dev server |

## Test Coverage

| Area                                      | Tests                            | Status     |
| ----------------------------------------- | -------------------------------- | ---------- |
| Geography extraction                      | 10 tests                         | ✅ Passing |
| Geography regression (concern separation) | 22 tests                         | ✅ Passing |
| NB03 v0.2 strategy                        | 38 tests                         | ✅ Passing |
| NB02 comprehensive                        | 81 tests (68 unit + 13 scenario) | ✅ Passing |
| E2E freeze pack                           | Tests                            | ✅ Passing |
| Follow-up mode                            | Tests                            | ✅ Passing |
| Lifecycle retention                       | Tests                            | ✅ Passing |

## Tech Stack

- **Backend**: Python 3.13, uv (package manager)
- **Frontend**: Next.js (App Router), TypeScript, Zustand (state)
- **AI/ML**: LLM-based extraction and decision inference
- **Testing**: pytest, scenario-based testing
- **Geography**: GeoNames dataset + world-cities.json (~590k cities)

> **License note:** GeoNames is CC-BY 4.0 and requires attribution. `world-cities.json` is supplemental and ODbL-1.0, so we keep it documented as licensed data rather than a proprietary dataset.

## Development Philosophy

- **Preservation-first**: Never delete historical documentation or code
- **Verification discipline**: Verify code works before moving to next task
- **Reusable tools**: Build tools, not throwaway scripts
- **Evidence-based**: Decisions backed by tests, specs, and real-world scenarios

## License

Private — all rights reserved.
