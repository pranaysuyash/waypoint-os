# Random Document Audit v2 Status Update

**Date:** 2026-05-05
**Related audit:** `Docs/random_document_audit_v2_2026-05-03.md`

## Summary

This note captures the current codebase state relative to the `random_document_audit_v2` findings.

## Resolved findings

- **ISSUE-001** — `trip_priorities` / `date_flexibility` extraction
  - Verified implemented in `src/intake/extractors.py`.
  - `ExtractionPipeline` produces facts for both fields.
  - `spine_api/models/trips.py` already includes first-class `trip_priorities` and `date_flexibility` columns.
  - `spine_api/server.py` already syncs `trip_priorities` and `date_flexibility` during trip PATCH.

- **ISSUE-002** — `agentNotes` privacy guard gap
  - Verified already covered in `src/security/privacy_guard.py`.
  - `_FREEFORM_FIELD_NAMES` includes both `agent_notes` and `agentNotes`.

## Verification

Attempted to run:

```bash
python3 -m pytest tests/test_extraction_fixes.py tests/test_privacy_guard.py tests/test_call_capture_phase2.py -q
```

Result:

- Test collection failed due to missing runtime dependencies in the current environment:
  - `ModuleNotFoundError: No module named 'opentelemetry'`
  - `ModuleNotFoundError: No module named 'sqlalchemy'`

## Conclusion

The two primary audit issues from `random_document_audit_v2` are already resolved in the current codebase.
The remaining gap is documentation staleness rather than live code failure.
