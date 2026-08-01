#!/usr/bin/env bash
# =============================================================================
# scripts/setup_nlp_models.sh — One-shot installer for SpaCy NLP Layer 2
# =============================================================================
# Installs spacy>=3.7 into the project venv and downloads en_core_web_sm (12MB).
#
# Usage:
#   bash scripts/setup_nlp_models.sh
#
# Requirements:
#   - uv must be on PATH (https://docs.astral.sh/uv/)
#   - Python >= 3.10 (project requires 3.13)
#
# After running:
#   - Set NLP_PII_GUARD_ENABLED=1 (default) in .env or environment
#   - DATA_PRIVACY_MODE=dogfood will now use SpaCy NER as Layer 2 PII check
#
# To verify installation:
#   uv run python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('OK:', nlp.meta)"
#
# In CI without the model (e.g. GitHub Actions free tier):
#   Set NLP_PII_GUARD_ENABLED=0 to disable SpaCy layer gracefully.
# =============================================================================

set -euo pipefail

echo "=== Setting up SpaCy NLP models for privacy_guard Layer 2 ==="
echo ""

# 1. Install spacy into the project venv via uv
echo "[1/3] Installing spacy>=3.7.0 into project venv..."
uv add --group privacy spacy
echo "      Done."
echo ""

# 2. Download en_core_web_sm (12MB, English small model with NER)
echo "[2/3] Downloading en_core_web_sm model..."
uv run python -m spacy download en_core_web_sm
echo "      Done."
echo ""

# 3. Verify installation
echo "[3/3] Verifying installation..."
MODEL_META=$(uv run python -c "
import spacy
nlp = spacy.load('en_core_web_sm')
print(f'Model: {nlp.meta[\"name\"]} v{nlp.meta[\"version\"]}')
print(f'Pipeline: {nlp.pipe_names}')
test_doc = nlp('My name is Priya Sharma and I want to travel to Maldives.')
persons = [ent.text for ent in test_doc.ents if ent.label_ == 'PERSON']
print(f'PERSON detection test: {persons}')
" 2>&1)
echo "      $MODEL_META"
echo ""

echo "=== SpaCy NLP Layer 2 setup complete! ==="
echo ""
echo "To enable: NLP_PII_GUARD_ENABLED=1 (default — already enabled)"
echo "To disable in tests: NLP_PII_GUARD_ENABLED=0"
echo ""
echo "Run tests:"
echo "  NLP_PII_GUARD_ENABLED=0 uv run pytest tests/test_privacy_guard_nlp.py -v  (no model needed)"
echo "  NLP_PII_GUARD_ENABLED=1 DATA_PRIVACY_MODE=dogfood uv run pytest tests/test_privacy_guard_nlp.py -v  (requires model)"
