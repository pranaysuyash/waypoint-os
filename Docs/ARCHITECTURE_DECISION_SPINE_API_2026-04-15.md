# Architecture Decision: Spine API Service (2026-04-15)

> **Note (2026-05-04):** This ADR documents the initial migration. The response contract has evolved significantly since then. `spine_api/contract.py` is the canonical source of truth for all current models. The ADR's 4-field response signature (`ok`, `safety`, `assertions`, `meta`) is historical — the actual `SpineRunResponse` now has 15+ fields including `packet`, `validation`, `decision`, `strategy`, `traveler_bundle`, `internal_bundle`, `fees`, `autonomy_outcome`, and `frontier_result`.

**Date**: 2026-04-15
**Decision**: Replace `spine-wrapper.py` (subprocess wrapper) with `spine_api` (FastAPI HTTP service)
**Status**: Implemented and committed
**Commit**: `42f561a50674aed1537e5953f360407c849ef4c5`

---

## What Changed

### Before (Deleted)
- **File**: `frontend/src/lib/spine-wrapper.py`
- **Pattern**: Next.js BFF spawns Python subprocess per request
- **Communication**: JSON via stdin/stdout
- **Process**: Spawn → Import modules → Run → Serialize → Exit (per request)

### After (Current)
- **File**: `spine_api/server.py`
- **Pattern**: Next.js BFF → HTTP POST to persistent FastAPI service
- **Communication**: HTTP with Pydantic models
- **Process**: Persistent Python process, modules pre-loaded, HTTP endpoint

**Frontend client**: `frontend/src/lib/spine-client.ts` (TypeScript fetch client — **removed 2026-05-04**, superseded by `hooks/useSpineRun`)

---

## Why This Change Was Made

### Performance
| Aspect | Subprocess | FastAPI HTTP |
|--------|-----------|--------------|
| Per-request overhead | 100-500ms (Python startup + module import) | ~0ms (process already running) |
| Module loading | Every request | Once at startup |
| Connection cost | New process per call | Connection reuse |

### Reliability
- **Subprocess stdin/stdout**: Fragile, encoding issues, buffer limits, hard to debug
- **HTTP with Pydantic**: Structured error handling, proper status codes, type validation at boundary

### Production Readiness
- FastAPI supports multiple uvicorn workers (configurable via `SPINE_API_WORKERS`)
- Standard HTTP service pattern — easier to deploy, monitor, scale
- Environment-based configuration (`SPINE_API_HOST`, `PORT`, `CORS`)

### Response Contract
- **Before**: Ad-hoc serialization in wrapper
- **After**: Canonical `SpineRunResponse` with:
  - `ok: bool` — success indicator
  - `safety: { strict_leakage, leakage_passed, leakage_errors }` — structured leakage reporting
  - `assertions: [...]` — scenario validation results
  - `meta: { stage, operating_mode, fixture_id, execution_ms }` — telemetry

---

## Architecture Diagram

### Before (Subprocess)
```
Next.js BFF
    ↓ (spawns)
Python process
    ├── Import modules (100-500ms)
    ├── run_spine_once()
    └── Exit
    ↓ (stdout)
JSON result
```

### After (HTTP Service)
```
Next.js BFF → HTTP POST /run → FastAPI (spine_api)
                                      ├── Modules pre-loaded
                                      ├── Pydantic validation
                                      ├── run_spine_once()
                                      └── Structured response
```

---

## Usage Comparison

### Before (spine-wrapper.py)
```typescript
// Frontend called Python subprocess
const result = await spawn('python', ['frontend/src/lib/spine-wrapper.py'], {
  input: JSON.stringify({ raw_note: "...", stage: "discovery" })
});
```

### After (spine_api + spine-client.ts)
```typescript
import { runSpine } from '@/lib/spine-client';

const result = await runSpine({
  raw_note: "...",
  stage: "discovery",
  operating_mode: "normal_intake",
  strict_leakage: true
});
// HTTP POST to localhost:8000/run
```

---

## Configuration

### Development
```bash
# Start the spine_api service
uv run python spine_api/server.py
# Or with reload
SPINE_API_RELOAD=1 uv run python spine_api/server.py

# Frontend automatically connects to localhost:8000
```

### Environment Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `SPINE_API_HOST` | 127.0.0.1 | Bind address |
| `SPINE_API_PORT` | 8000 | Port |
| `SPINE_API_WORKERS` | 1 | Uvicorn workers |
| `SPINE_API_CORS` | - | Allowed origins (comma-separated) |
| `SPINE_API_RELOAD` | 1 (dev) | Auto-reload on changes |
| `SPINE_API_URL` | http://127.0.0.1:8000 | Frontend client override |
| `TRAVELER_SAFE_STRICT` | 0 | Global strict leakage mode |

---

## Migration Notes

### For Frontend Developers
- Replace direct subprocess calls with `runSpine()` from `@/lib/spine-client`
- Ensure `spine_api` service is running (`uv run python spine_api/server.py`)
- Response shape changed: now includes `safety` and `assertions` fields
- Errors are now HTTP errors with structured detail, not exit codes

### For Backend/Deployment
- spine_api is a standalone FastAPI service
- Requires Python environment with `src/intake` modules on path
- Can be containerized separately from Next.js
- Consider `SPINE_API_WORKERS` > 1 for production load

---

## Files Affected

| File | Change | Purpose |
|------|--------|---------|
| `frontend/src/lib/spine-wrapper.py` | **DELETED** | Old subprocess wrapper |
| `spine_api/server.py` | **CREATED** | FastAPI HTTP service |
| `frontend/src/lib/spine-client.ts` | **CREATED** | TypeScript HTTP client |
| `frontend/src/types/spine.ts` | **CREATED** | TypeScript type definitions |

---

## Relationship to Phase A/Phase B

This change aligns with the **frozen spine** principle:

- **Phase A (UI/Workbench)**: Stable API contract for frontend to build against
- The HTTP service provides a **stable, versioned contract** (`SpineRunResponse`)
- Frontend can build independently while backend implementation evolves
- **Phase B (Hybrid Extraction)**: Will plug into the same `spine_api` endpoint
- NER/LLM results will flow through the same HTTP interface
- Frontend sees same contract, different backend implementation

---

## Decision Rationale

**Trade-offs considered:**

| Alternative | Why Not Chosen |
|-------------|---------------|
| Keep subprocess wrapper | Performance unacceptable for production; process spawn per request adds 100-500ms latency |
| gRPC instead of HTTP | Additional complexity; HTTP is sufficient for current needs; can migrate later if needed |
| Direct Python→Python import | Breaks language boundary; Next.js BFF is TypeScript |
| Serverless (AWS Lambda, etc.) | Cold start latency; local development complexity; overkill for current scale |

**Chosen**: FastAPI HTTP service as the pragmatic balance of performance, simplicity, and standard patterns.

---

## References

- `spine_api/server.py` — FastAPI implementation
- `frontend/src/lib/spine-client.ts` — TypeScript client
- `frontend/src/types/spine.ts` — Type definitions
- Commit `42f561a` — Implementation (note: bundled with unrelated docs commit)
- `Docs/FROZEN_SPINE_STATUS.md` — Post-freeze rules (Phase A/B)

---

## Open Questions

1. **Production deployment**: Should spine_api be containerized separately or co-located with Next.js?
2. **Scaling**: At what load does `SPINE_API_WORKERS` need to increase? Need metrics.
3. **Health checks**: Should `/health` endpoint be added for k8s/docker-compose?
4. **Graceful shutdown**: Current implementation — sufficient for production?