# ADR 16: Multi-Agent High-Concurrency Stress Suite & Load Benchmark Standard

**Date**: 2026-08-02  
**Status**: APPROVED  
**Deciders**: AI Workforce Team, Infrastructure Engineering  
**Governing Rule**: `motto_v4.md` (Rule 0.10: Observability & Load Verification)

---

## 1. Context & Business Need

In high-volume B2B travel agencies, multiple human planners and automated background workers simultaneously submit trip inquiries, generate proposal options, and stream pipeline status updates. We must guarantee that database persistence (`spine_api/persistence.py`), SSE event streams, and audit chain hash calculations remain 100% deadlock-free and tamper-evident under 50+ concurrent active agents.

## 2. Technical Decision & Benchmark Architecture

1. **Async Multi-Agent Workload Generator (`tools/benchmarks/stress_test_multi_agent_workforce.py`)**:
   - Uses `asyncio` and `httpx` to spawn 50+ concurrent worker tasks.
   - Each worker submits structured inquiry requests (`POST /api/v1/inbound/process`), reads SSE state updates (`/api/stream-events`), and checks quote signoff gates.

2. **Automated Pytest Concurrency Suite (`tests/test_multi_agent_concurrency_suite.py`)**:
   - Asserts zero SQLite/PostgreSQL lock contention errors under high concurrent write rates.
   - Verifies SHA-256 block hash integrity (`previous_hash`, `current_hash`) across 100+ rapidly appended audit log events.

## 3. SLA Performance Boundaries

- **Throughput Target**: $\ge 150$ inquiries processed per minute.
- **p95 Latency**: $\le 450\text{ms}$ per request under 50-agent concurrency.
- **Audit Hash Continuity**: 100% hash linkage match with 0 corrupted blocks.
