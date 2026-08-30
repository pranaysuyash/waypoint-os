# OpenTelemetry Trace-Correlation & Observability Gap — R-16

**Status:** Exploration / gap assessment (Observed facts → Proposed improvements)
**Date:** 2026-08-29
**Owner:** Observability
**Associated finding:** R-16 (OTel spans are real but there is no trace-to-log correlation reader, no dashboards, and no CI assertion that event flow works)

## Problem

Waypoint OS has real OpenTelemetry instrumentation, but it is **not wired into a usable observability loop**. The spans exist; the ability to answer "what happened, for whom, when, in which run, with which provider, and did a fallback occur" does not — without pulling a collector, querying an external store, and correlating manually.

## Observed ground truth

- **Real spans** are opened in the intake pipeline: `src/intake/orchestration.py` uses `_otel_tracer = trace.get_tracer("orchestration.pipeline")` and opens `extraction`, `validation`, `nb01_gate`, `decision`, `suitability`, `safety`, `readiness` spans with attributes (`envelope_count`, `trip_id`, `verdict`). `spine_api/server.py:155` opens `spine_api.pipeline` spans.
- **Exporter is gated**: `server.py:93-98` builds the `TracerProvider` + `BatchSpanProcessor(OTLPSpanExporter(...))` only when an OTLP endpoint is set (`otel_endpoint`). With no endpoint (dev/default), the whole OTel block is skipped — no spans are actually exported.
- **Sensitive data filter** is real: `spine_api/core/logging_filter.py` installs a `SensitiveDataFilter` that scrubs emails/phones/tokens.
- **Frontend** depends on `@opentelemetry/*` (`@opentelemetry/api`, `exporter-trace-otlp-http`, `instrumentation-document-load`, `resources`, `semantic-conventions`, `instrumentation`) but browser tracing is not obviously correlated to backend spans.
- **No trace-log correlation**: spans set `trip_id`/`verdict` attributes, and the structured `logs/` output exists, but there is no trace_id→log linkage, no span-correlation reader, and no OTEL-collector query path in CI or operator docs.
- **No CI assertion** that events flow. The test conftest explicitly sets `OTEL_EXPORTER_OTLP_ENDPOINT=""` to disable OTel in tests (the `BatchSpanProcessor` background thread outlives the TestClient loop).

## Gaps

1. **No trace_id in logs** — a production defect requires manually finding the span by `trip_id` rather than following the trace ID from a log line.
2. **No dashboard / query path** — OTLP export requires an external collector + backend (e.g. Grafana Tempo / Jaeger); none is documented or configured in the repo.
3. **No CI assertion** — nothing verifies that OpenTelemetry is wired to an endpoint, that spans are emitted, or that the exporter is reachable.
4. **Frontend↔backend correlation** — the browser and server span contexts are not linked via a shared correlation header (e.g. `traceparent`), so a user's page view cannot be joined to the backend run it triggered.

## Proposed improvements (doctrine-aligned)

- **Add `trace_id`/`span_id` to the structured log record** so the `SensitiveDataFilter`-scrubbed logs carry `otel.trace_id` and `otel.span_id`. This enables trace→log correlation without an external system.
- **Emit a `traceparent` header** from the frontend BFF and consume it server-side so browser and backend spans join the same trace.
- **Add a CI "OTel smoke test"**: assert that when `OTEL_EXPORTER_OTLP_ENDPOINT` is set, a span is emitted and the exporter is reachable (a Tier-3 integration check), rather than only asserting the instrumentation exists.
- **Document the collector setup** (Tempo/Jaeger + Grafana) as a runbook, and add a dashboard note for the key span attributes (`trip_id`, `verdict`, `envelope_count`, `stage`).

## Non-goals / stopping rules

- Do not require a collector for every dev run — the exporter should stay optional (gated), but the `trace_id` in logs should always be available.
- Do not add a second tracing system; extend the existing OpenTelemetry path.
- OTel must remain disabled in tests (current behavior is correct) — the gap is production correlation, not test span emission.

## Acceptance criteria

- `spine_api` structured log records include `otel.trace_id`/`otel.span_id` when a span context is active.
- The frontend sends `traceparent` on API calls; the backend joins the browser trace.
- A documented runbook covers collector setup + a dashboard for key spans.
- CI smoke test asserts the exporter path emits (when a test collector is available).

## Evidence tier

- Observed (Tier 1 static): span calls, exporter gating, log filter, frontend deps — all verified by reading the cited files.
- Proposed (Tier 0 design): the correlation improvements are proposals pending implementation.
