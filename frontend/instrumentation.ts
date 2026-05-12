import { trace, TracerProvider } from "@opentelemetry/api";
import {
  BasicTracerProvider,
  BatchSpanProcessor,
} from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";
import { registerInstrumentations } from "@opentelemetry/instrumentation";

function parsePositiveInt(raw: string | undefined, fallback: number): number {
  if (!raw) return fallback;
  const n = Number.parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : fallback;
}

// Frontend uses OTLP HTTP exporter URL.
const OTEL_ENDPOINT =
  process.env.OTEL_EXPORTER_OTLP_HTTP_TRACES_ENDPOINT ||
  process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
const BSP_MAX_QUEUE_SIZE = parsePositiveInt(process.env.FRONTEND_OTEL_BSP_MAX_QUEUE_SIZE, 512);
const BSP_MAX_EXPORT_BATCH_SIZE = parsePositiveInt(process.env.FRONTEND_OTEL_BSP_MAX_EXPORT_BATCH_SIZE, 128);
const BSP_SCHEDULE_DELAY_MS = parsePositiveInt(process.env.FRONTEND_OTEL_BSP_SCHEDULE_DELAY_MS, 1500);
const BSP_EXPORT_TIMEOUT_MS = parsePositiveInt(process.env.FRONTEND_OTEL_BSP_EXPORT_TIMEOUT_MS, 3000);

export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  if (!OTEL_ENDPOINT) return;

  const provider: TracerProvider = new BasicTracerProvider({
    resource: resourceFromAttributes({
      [ATTR_SERVICE_NAME]: "travel_agency_frontend",
    }),
    spanProcessors: [
      new BatchSpanProcessor(
        new OTLPTraceExporter({
          url: OTEL_ENDPOINT,
          timeoutMillis: BSP_EXPORT_TIMEOUT_MS,
        }),
        {
          maxQueueSize: BSP_MAX_QUEUE_SIZE,
          maxExportBatchSize: BSP_MAX_EXPORT_BATCH_SIZE,
          scheduledDelayMillis: BSP_SCHEDULE_DELAY_MS,
          exportTimeoutMillis: BSP_EXPORT_TIMEOUT_MS,
        },
      ),
    ],
  });

  trace.setGlobalTracerProvider(provider);

  registerInstrumentations({
    tracerProvider: provider,
  });

  console.log("OpenTelemetry tracing enabled (OTLP HTTP → %s)", OTEL_ENDPOINT);
}
