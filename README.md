# Travel Agency Agent

B2B Revenue and Operations Copilot for Boutique Travel Agencies.

## Environment

- **Package manager**: `uv`
- **Python**: 3.13
- **Virtual env**: `.venv/`

```bash
# Install dependencies
uv sync

# Run a notebook
uv run jupyter notebook

# Run a script
uv run python main.py

# Add a dependency
uv add <package>

# Run tests
uv run pytest
```

**Never use system Python. Always use `uv run` or `.venv/bin/python`.**

## Project Structure

```
├── src/                    # Core implementation
├── notebooks/              # Prototype notebooks
│   ├── 01_intake_and_normalization.ipynb
│   └── 02_gap_and_decision.ipynb
├── specs/                  # JSON schemas and specs
├── Docs/                   # Product and technical docs
├── data/                   # Test fixtures and raw data
├── prompts/                # Prompt templates
├── memory/                 # Project memory and decisions
└── pyproject.toml          # Project dependencies
```

## Architecture

Two-Loop System:

- **Online Loop**: Source → Normalize → Validate → Infer → Decide → Execute → Log
- **Offline Loop**: Eval Harness → Mutation → Score → Persist (if improved)

## Notebook Status

| Notebook                              | Status                                         | Grade |
| ------------------------------------- | ---------------------------------------------- | ----- |
| 01 - Intake & Normalization           | Implemented                                    | —     |
| 02 - Gap & Decision                   | Implemented + 81 tests (68 unit + 13 scenario) | A-    |
| 03 - Session Strategy & Prompt Bundle | Next                                           | —     |
