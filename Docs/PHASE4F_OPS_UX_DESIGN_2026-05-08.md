# Phase 4F: Extraction Ops UX + Quality Harness

## Context

Phase 4E (closed 2026-05-08) delivered multi-model fallback, PDF extraction, append-only attempts, and retry. The backend now supports real extraction with full history. Phase 4F makes this operational for agents and measurable without weakening privacy boundaries.

**No auto-apply. No customer-facing extraction UI. No raw OCR text storage. No PII in attempts list.**

---

## Scope

1. **OpsPanel attempt history UI** — Show all extraction attempts per document with provider/model/status/latency/cost.
2. **Retry failed extraction button** — One-click retry from the ops panel.
3. **Provider/model/fallback rank display** — Show which model was used and where it sat in the chain.
4. **Error code display** — Show `error_code` only, never raw `error_summary` if it risks leakage.
5. **Current successful attempt highlight** — Clearly mark which attempt produced the current fields.
6. **PII boundary** — Decrypted fields stay in the main extraction review area only. Attempt history has no PII.
7. **Extraction quality harness** — Synthetic document testing against expected fields.
8. **Provider smoke test** — Behind explicit env flag, not in production.
9. **Extraction quality report** — CLI command that outputs per-provider accuracy metrics.

---

## Part 1: Frontend API Types Update

**File:** `frontend/src/lib/api-client.ts`

Add types for Phase 4E response fields and new endpoints:

```typescript
// Updated ExtractionResponse with Phase 4E fields
export interface ExtractionResponse {
  id: string;
  document_id: string;
  status: 'pending_review' | 'applied' | 'rejected' | 'failed' | 'running';
  extracted_by: string;
  overall_confidence: number | null;
  field_count: number;
  fields: ExtractionFieldView[];
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  provider_name: string | null;
  model_name: string | null;
  latency_ms: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  cost_estimate_usd: number | null;
  error_code: string | null;
  error_summary: string | null;
  confidence_method: string | null;
  // Phase 4E
  attempt_count: number;
  run_count: number;
  current_attempt_id: string | null;
  page_count: number | null;
}

// New: attempt summary (no PII)
export interface AttemptSummary {
  attempt_id: string;
  run_number: number;
  attempt_number: number;
  fallback_rank: number | null;
  provider_name: string;
  model_name: string | null;
  latency_ms: number | null;
  status: 'success' | 'failed';
  error_code: string | null;
  created_at: string | null;
}
```

New API functions:

```typescript
export async function listExtractionAttempts(tripId: string, documentId: string): Promise<AttemptSummary[]>
export async function retryExtraction(tripId: string, documentId: string): Promise<ExtractionResponse>
```

---

## Part 2: ExtractionHistoryPanel Component

**New file:** `frontend/src/components/workspace/panels/ExtractionHistoryPanel.tsx`

### Design

A panel that shows attempt history for a document's extraction. Used within OpsPanel when a document is selected and has an extraction.

```
┌─────────────────────────────────────────────────┐
│ ⚙ Extraction History                    [Retry] │
│ 3 attempts · 2 runs · gpt-5.4-nano · 142ms     │
├─────────────────────────────────────────────────┤
│ Run 2 (latest)                                  │
│ ├─ Attempt 2 ★ SUCCESS ── gpt-5.4-nano          │
│ │  latency: 142ms · cost: $0.00008              │
│ │                                                │
│ └─ Attempt 1   FAILED    gemini-2.5-flash        │
│    error: api_timeout · latency: 30021ms         │
│                                                  │
│ Run 1                                           │
│ └─ Attempt 1   FAILED    gemini-2.5-flash        │
│    error: api_timeout · latency: 30012ms         │
└─────────────────────────────────────────────────┘
```

### Component structure

```typescript
interface ExtractionHistoryPanelProps {
  tripId: string;
  documentId: string;
  extraction: ExtractionResponse | null;
  onRetryComplete: (extraction: ExtractionResponse) => void;
}
```

### Behavior

- Fetches attempts on mount via `listExtractionAttempts()`.
- Groups attempts by `run_number` in reverse chronological order.
- Highlights the current successful attempt (`attempt_id === extraction.current_attempt_id`).
- Shows retry button only when `extraction.status === "failed"`.
- Retry button calls `retryExtraction()`, then refreshes both attempts and parent extraction.
- Error display: shows `error_code` only. Never shows `error_summary` in the panel.
- Provider metadata row: `provider_name / model_name · latency_ms · cost_estimate_usd`.
- PDF badge: if `extraction.page_count`, show `📄 {page_count} pages`.
- No PII: no decrypted fields, no encrypted blob, no raw provider response.

### Styling

- Follow existing panel pattern from `ChangeHistoryPanel.tsx`.
- Status badge colors: success = green, failed = red, running = amber.
- Current attempt = highlighted background with star marker.
- Fallback rank indicator: `Primary`, `Fallback 1`, `Fallback 2`.

---

## Part 3: OpsPanel Integration

**File:** `frontend/src/app/(agency)/workbench/OpsPanel.tsx`

Add the extraction history panel below the existing extraction review section:

```typescript
{extraction && (
  <ExtractionHistoryPanel
    tripId={tripId}
    documentId={selectedDocId}
    extraction={extraction}
    onRetryComplete={(updated) => {
      setExtractions(prev => ({ ...prev, [selectedDocId]: updated }));
    }}
  />
)}
```

---

## Part 4: Extraction Quality Harness

**New file:** `src/extraction/quality_harness.py`

A test harness that evaluates extraction quality against synthetic documents with known ground truth.

```python
@dataclass
class QualityTestCase:
    """A synthetic document with known expected fields."""
    name: str
    document_type: str  # passport, visa, insurance
    mime_type: str
    file_data: bytes
    expected_fields: dict[str, str]  # ground truth
    tolerance: dict[str, float] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Result of running quality harness."""
    test_cases: list[TestCaseResult]
    overall_field_accuracy: float
    overall_confidence_avg: float
    provider_results: dict[str, ProviderResult]


def run_quality_harness(
    test_cases: list[QualityTestCase],
    model_chain: str | None = None,
) -> QualityReport:
    """Run extraction against synthetic documents and measure accuracy."""
    ...
```

### Design principles

- **No production data.** Only synthetic test documents.
- **Behind env flag.** `EXTRACTION_QUALITY_HARNESS=1` must be set. Disabled by default.
- **No PII in output.** Report shows field-level match rates, not field values.
- **Per-provider breakdown.** Shows accuracy by provider/model.
- **CI-optional.** Can run in CI but doesn't block merges. Run manually for provider evaluation.

### Synthetic test documents

Create minimal synthetic documents (images, PDFs) with known content:
- Synthetic passport JPEG with known name/number
- Synthetic visa PDF with known visa type/number
- Synthetic insurance card with known provider/policy

These are generated by the harness, not stored. Each has a `QualityTestCase` with expected fields.

---

## Part 5: Provider Smoke Test

**New file:** `src/extraction/smoke_test.py`

A lightweight smoke test that verifies each configured provider can extract from a trivial document.

```python
def run_smoke_test(provider: str | None = None) -> dict:
    """Run extraction smoke test against configured providers.

    Returns per-provider result: {provider, model, status, latency_ms, fields_found}
    Must have EXTRACTION_SMOKE_TEST=1 set to run.
    """
    ...
```

### Design

- **Not in production.** Only runs when `EXTRACTION_SMOKE_TEST=1` is set and `APP_ENV != production`.
- **Minimal document.** Uses a tiny synthetic image (1x1 white pixel with text overlay).
- **Verifies:** API key works, structured output parses, fields are returned.
- **Output:** `{provider, model, status, latency_ms, fields_found, error_code}`.
- **CLI command:** `python -m src.extraction.smoke_test`.

---

## Part 6: Extraction Quality Report CLI

**New file:** `tools/extraction_quality_report.py`

CLI tool that outputs a quality report for the configured extraction chain.

```bash
# Run quality harness and print report
python tools/extraction_quality_report.py --model-chain "gemini-2.5-flash,gpt-5.4-nano"

# Run smoke test only
python tools/extraction_quality_report.py --smoke-test

# JSON output for CI
python tools/extraction_quality_report.py --json --output report.json
```

Output format:

```
Extraction Quality Report
=========================
Chain: gemini-2.5-flash → gpt-5.4-nano
Date: 2026-05-08

Provider Results:
  gemini-2.5-flash:  5/5 tests passed · avg latency 340ms · avg cost $0.00012
  gpt-5.4-nano:      4/5 tests passed · avg latency 210ms · avg cost $0.00005

Field Accuracy:
  full_name:             100% (5/5)
  passport_number:        80% (4/5)
  passport_expiry:        60% (3/5) ← needs review
  nationality:           100% (5/5)

Overall: 90% field accuracy · 0.88 avg confidence
```

---

## Files Changed

| File | Action | Notes |
|:-----|:-------|:------|
| `frontend/src/lib/api-client.ts` | Update | Add Phase 4E types, retry/attempts API |
| `frontend/src/components/workspace/panels/ExtractionHistoryPanel.tsx` | New | Attempt history UI |
| `frontend/src/app/(agency)/workbench/OpsPanel.tsx` | Update | Integrate history panel |
| `src/extraction/quality_harness.py` | New | Synthetic document quality testing |
| `src/extraction/smoke_test.py` | New | Provider connectivity smoke test |
| `tools/extraction_quality_report.py` | New | CLI quality report generator |
| `tests/test_quality_harness.py` | New | Quality harness tests |

---

## Out of Scope

- Auto-apply extraction fields
- Customer-facing extraction UI
- Raw OCR text storage
- Real document quality testing (only synthetic)
- Provider credential rotation
- Extraction scheduling or batch processing
- Multi-document extraction correlation

---

## Privacy Boundaries

| Surface | PII? | Notes |
|:--------|:-----|:------|
| Attempt history panel | No | Only attempt metadata, no fields |
| Extraction review area | Yes | Decrypted fields shown, same as Phase 4D |
| Quality harness output | No | Only match rates, no field values |
| Smoke test output | No | Only provider/model/status |
| Quality report CLI | No | Aggregated metrics only |

---

## Implementation Order

1. Frontend API types update (api-client.ts)
2. ExtractionHistoryPanel component
3. OpsPanel integration
4. Quality harness
5. Provider smoke test
6. Quality report CLI
7. Tests

---

## Dependencies

- Phase 4E must be closed (it is — 2026-05-08)
- `google-genai` SDK installed for Gemini smoke test
- `pypdf` installed for PDF test documents
- Frontend test infrastructure (Vitest) for panel tests
