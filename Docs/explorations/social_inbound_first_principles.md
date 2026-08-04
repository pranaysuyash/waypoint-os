# Exploration & First-Principles Design: Social Inbound

## 1. Overview
The Social Inbound intake system parses raw text from social media DMs, messaging apps, and fast-pass links into structured travel inquiry packets.

## 2. Reality Tier Classification
- **Reality Tier**: `DATA_DEPENDENT`
- **Capabilities**:
  - `can_write_success_events`: True
  - `can_appear_as_paid`: False
  - `can_make_safety_claims`: False
  - `can_make_financial_claims`: False
  - `can_mutate_booking_state`: False

## 3. Extraction & Processing Pipeline
1. **Sanitization**: Raw DM text is processed through `sanitize_input` to redact PII before storage/LLM egress.
2. **Extraction**: Raw text is routed through `ExtractionPipeline` (`src/intake/extractors.py`), extracting destination, dates, budget, party size, and preferences.
3. **Suitability Scoring**: Evaluated against decision rules (`DecisionEngine`), returning real computed scores.
4. **Teaser Proposal**: Creates a masked Stage 1 teaser link.
5. **Unmasking**: Unmasks itinerary details upon deposit payment, using real trip strategy details if present rather than hardcoded fake hotel/flight data.
