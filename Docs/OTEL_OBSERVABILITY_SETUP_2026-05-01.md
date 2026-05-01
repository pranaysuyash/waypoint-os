# Local OpenTelemetry + Jaeger Tracing Setup

## Architecture

```
Browser ──HTTP──> Next.js (frontend, port 3000)
                     │ @opentelemetry/instrumentation
                     ▼
                 OTLP Exporter ──HTTP :4318──┐
                                              │
FastAPI (spine_api, port 8000)               │
  │ opentelemetry-instrumentation-fastapi     │
  └─ OTLP Exporter ──gRPC :4317 ─────────────┤
                                              ▼
                                     Jaeger (Docker)
                                     UI: http://localhost:16686
                                     gRPC: :4317
                                     HTTP :4318
```

Every HTTP request sent to the backend generates a **trace** in Jaeger. Within each trace, **spans** represent individual operations — the endpoint handler, database queries, and (with our custom instrumentation) each pipeline stage.

---

## Components Set Up

### Infrastructure (Docker)

| Component | Location | Status |
|-----------|----------|--------|
| Jaeger all-in-one | `docker/docker-compose.otel.yml` | Running |
| Jaeger UI | http://localhost:16686 | Available |
| OTLP gRPC endpoint | localhost:4317 | Receiving traces |

### Backend (spine_api / FastAPI)

| File | What was added |
|------|----------------|
| `spine_api/server.py` | OTel SDK init with `TracerProvider` + `BatchSpanProcessor` sending to `localhost:4317` |
| `spine_api/server.py` | `FastAPIInstrumentor.instrument_app(app)` — auto-instruments all endpoints |
| `spine_api/server.py` | `_otel_tracer` wraps the `run_spine_once()` call as `"spine_pipeline"` span with run_id, stage, trip_id attributes |
| `src/intake/orchestration.py` | `_otel_tracer` wraps each individual pipeline stage (see below) |
| `pyproject.toml` | 17 new OTel dependencies added via `uv add` |

### Custom Pipeline Stage Spans (orchestration.py)

Each pipeline stage in `run_spine_once()` is now wrapped with its own span. This means Jaeger shows a breakdown like:

```
spine_pipeline (total request)
├── extraction         time spent extracting data from raw input
├── validation         time validating the packet
├── nb01_gate          NB01 quality gate evaluation
├── decision           gap analysis and decision engine
├── suitability        activity suitability scoring
├── nb02_gate          NB02 autonomy gate
├── frontier           ghost concierge + sentiment analysis
├── strategy           session strategy construction
├── output_bundles     internal + traveler-safe prompt bundles
├── safety             sanitization + leakage detection
└── fee_calculation    trip fee computation
```

Each span carries attributes (e.g., extraction sets `envelope_count`, decision sets `decision_state`, nb01 sets `verdict`) for filtering in Jaeger.

### Frontend (Next.js)

| File | What was added |
|------|----------------|
| `frontend/instrumentation.ts` | OTel WebTracerProvider with OTLP HTTP exporter to `localhost:4318/v1/traces` |
| `frontend/package.json` | 4 OTel npm packages added |

Note: Frontend tracing requires the frontend dev server to be running and the Jaeger HTTP OTLP port (4318) to be accessible from the browser.

---

## How to Start / Stop

### Start the full stack

```bash
# Terminal 1: Jaeger
docker compose -f docker/docker-compose.otel.yml up -d

# Terminal 2: Backend (served from the project root)
cd /path/to/project
uv run uvicorn spine_api.server:app --port 8000

# Terminal 3: Frontend
cd frontend
npm run dev
```

### Verify traces are flowing

Open Jaeger UI:

```bash
open http://localhost:16686
```

Then send a request to the backend:

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"raw_note":"customer wants a trip to paris"}'
```

In Jaeger:
1. Select `spine_api` from the Service dropdown
2. Click **Find Traces**
3. Click the most recent trace
4. You'll see the flamegraph with all pipeline stages

### Stop

```bash
docker compose -f docker/docker-compose.otel.yml down
```

---

## How to Read the Jaeger Flamegraph

Each trace in Jaeger is a timeline of the full request. Spans are stacked:

```
OVERVIEW
─────────────────────────────────────────────────────────
[spine_pipeline             ████████████████████████████]
  [extraction               ████                       ]
  [validation               ██                         ]
  [nb01_gate                █                          ]
  [decision                 ████████████████           ]
  [suitability              ██                         ]
  [nb02_gate                █                          ]
  [frontier                 ██████████                 ]
  [strategy                 ███                        ]
  [output_bundles           ██                         ]
  [safety                   █                          ]
  [fee_calculation          █                          ]
```

### What each visual element means

| Element | Meaning |
|---------|---------|
| **Width of a bar** | Time spent in that span — wider = slower |
| **Nested bars** | Child spans within a parent (e.g., pipeline stages inside the HTTP request) |
| **Red bars** | Errors — click to see the error message |
| **Gaps between bars** | Untracked work — time not covered by any child span |
| **Tags / Attributes** | Click a span to see its attributes (e.g., `decision_state`, `verdict`, `envelope_count`) |

### Diagnosing common patterns

| Pattern | What it means | Action |
|---------|---------------|--------|
| One stage dominates width | That stage is the bottleneck | Profile that stage specifically |
| Large gaps between stages | Overhead not tracked (callbacks, serialization) | Add more spans |
| Red spans | Errors occurring | Click the span to see error details |
| Frontend-to-backend trace | Full request trace across both services | Requires frontend OTel active |
| Short total but slow user experience | Network latency or client-side processing | Check frontend spans |

### Example: Finding a bottleneck

1. Open Jaeger UI → Service: `spine_api` → Find Traces
2. Sort by Duration (descending)
3. Click the longest trace
4. Look at the flamegraph — the widest bar is your bottleneck
5. Click that span to see its attributes and tags
6. Compare against the SLAs:

| Metric | Good | Needs attention |
|--------|------|-----------------|
| Total pipeline | < 5s | > 10s |
| Decision (LLM) | < 3s | > 8s |
| Extraction | < 1s | > 3s |
| Safety | < 500ms | > 2s |

---

## How to Add This to a New Project

A reusable skill is available at `~/Projects/skills/observability/local-otel-tracing/SKILL.md`.

### For a FastAPI backend

```bash
# Install deps
uv add opentelemetry-distro opentelemetry-exporter-otlp-proto-grpc opentelemetry-instrumentation-fastapi

# Add to your server.py:
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317"))
)
trace.set_tracer_provider(provider)

app = FastAPI(...)
FastAPIInstrumentor.instrument_app(app)
```

### For a Next.js frontend

```bash
# Install deps
npm install @opentelemetry/api @opentelemetry/sdk-trace-web @opentelemetry/exporter-trace-otlp-http

# Create instrumentation.ts in project root:
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { OTLPTraceExporter } = await import("@opentelemetry/exporter-trace-otlp-http");
    const { BatchSpanProcessor } = await import("@opentelemetry/sdk-trace-base");
    const { WebTracerProvider } = await import("@opentelemetry/sdk-trace-web");

    const provider = new WebTracerProvider();
    provider.addSpanProcessor(
      new BatchSpanProcessor(new OTLPTraceExporter({ url: "http://localhost:4318/v1/traces" }))
    );
    provider.register();
  }
}
```

### For custom pipeline stages (any Python code)

```python
from opentelemetry import trace
tracer = trace.get_tracer("my_app")

def process():
    with tracer.start_as_current_span("stage_name") as span:
        span.set_attribute("key", "value")
        # ... do work ...
```

### Docker compose (copy-paste)

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "16686:16686"
      - "4317:4317"
      - "4318:4318"
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

Save as `docker/docker-compose.otel.yml` and run:

```bash
docker compose -f docker/docker-compose.otel.yml up -d
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC endpoint for backend traces |
| `NEXT_PUBLIC_OTEL_ENDPOINT` | `http://localhost:4318/v1/traces` | OTLP HTTP endpoint for frontend traces |
| `OTEL_SERVICE_NAME` | auto-detected | Service name shown in Jaeger |
| `SPINE_TELEMETRY_DIR` | `~/.gstack/telemetry` | Local JSONL telemetry (from pipeline-timing) |

---

## Related Skills

| Skill | Location | Purpose |
|-------|----------|---------|
| `local-otel-tracing` | `~/Projects/skills/observability/` | This setup, reusable for any FastAPI/Next.js project |
| `pipeline-timing` | `~/.hermes/skills/observability/` | Lightweight JSONL-based stage timing (no Docker needed) |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| No traces in Jaeger | OTel can't connect | Check `docker ps` — Jaeger must be running |
| Server won't start after adding OTel | OTLP endpoint unreachable | The init has a `try/except` — check server logs for warning |
| Frontend traces missing | CORS or endpoint issue | Ensure `localhost:4318` is accessible from the browser |
| Jaeger UI shows service but no traces | No requests sent yet | Send a request to the backend |
| Span attributes missing (`decision.decision_source`) | Attribute doesn't exist on the model | Check the actual dataclass fields — use `hard_blocker_count` instead |
