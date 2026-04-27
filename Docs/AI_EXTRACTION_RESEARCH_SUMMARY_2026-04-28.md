# AI Extraction Research Summary

Date: 2026-04-28

## Purpose

Capture the recent exploration of travel document extraction approaches for the project, including:
- deterministic regex extraction
- NLP-based extraction
- LLM-based extraction
- OCR / NER / PII research areas
- hybrid extraction pipeline recommendations

This document is meant to preserve the current state of thinking and the decisions made during the research session.

## What was documented

- The `Docs/research/RESEARCH_OPPORTUNITY_MASTER_LIST_2026-04-25.md` master research list was updated with new AI research items covering:
  - document extraction research (OCR + NER)
  - travel-specific NER taxonomy
  - OCR source quality research
  - PII classification and redaction research
  - PII consent and retention policy research
  - secure document ingestion research

- A practical comparison of extraction approaches was also captured for this session:
  - regex
  - NLP
  - LLM

## Key findings

### 1. Regex extraction

- Best for strong, repeatable travel fields and deterministic signals.
- Useful for booking references, ticket numbers, formatted dates, times, prices, email/phone patterns.
- Advantages: fast, auditable, cheap, deterministic.
- Risks: brittle on messy, unstructured, OCR-noisy, multilingual, or handwritten input.

### 2. NLP extraction

- Best for semi-structured itinerary text, emails, chat logs, and variable travel documents.
- Useful for entity recognition and document segmentation when the format is not fixed.
- Enables travel-specific extraction of destinations, hotels, flights, transfers, visas, activities, and costs.
- Requires training/tuning for travel domain and multi-lingual support.

### 3. LLM extraction

- Best for free-form, ambiguous, or highly variable travel text.
- Good for schema-driven extraction, contradiction detection, and follow-up question generation.
- Valuable as a verification layer or fallback when regex/NLP coverage is weak.
- Needs careful prompt engineering, schema validation, and cost control.

## Recommended pipeline pattern

1. ingest raw text / OCR output
2. text cleanup and normalization
3. regex extraction for deterministic fields
4. NLP extraction for travel NER and document segmentation
5. LLM extraction for ambiguity resolution, schema-driven extraction, and quality reasoning
6. output validation and conflict detection

## Existing documents and repo context

- The team already has a relevant architecture document in `Docs/PHASE_B_MERGE_CONTRACT_2026-04-15.md` describing the hybrid extraction approach: regex first, then semantic extraction (NER/LLM).
- The project also has a public GTM wedge at `/itinerary-checker` and a broader research master list that now includes the AI/PII extraction items.

## Next recommended steps

- Validate whether the backend has a real extraction API to wire up `/itinerary-checker` beyond UI simulation.
- Map the current extraction pipeline in `src/intake/` and `src/analytics/` to this hybrid pattern.
- Create a small proof-of-concept extraction path using regex first, with a semantic candidate layer for missing or ambiguous fields.
- Add tests for regex baseline coverage plus semantic candidate validation.

## Notes

This summary documents the work done without requiring a follow-up request. It should be referenced when the team continues the AI extraction research or begins implementation of the hybrid intake pipeline.
