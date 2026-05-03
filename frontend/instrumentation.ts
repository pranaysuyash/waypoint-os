import { trace, TracerProvider } from "@opentelemetry/api";
import {
  BasicTracerProvider,
  SimpleSpanProcessor,
} from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";
import { registerInstrumentations } from "@opentelemetry/instrumentation";

const OTEL_ENDPOINT =
  process.env.OTEL_EXPORTER_OTLP_ENDPOINT || "http://localhost:4318/v1/traces";

export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;

  const provider: TracerProvider = new BasicTracerProvider({
    resource: resourceFromAttributes({
      [ATTR_SERVICE_NAME]: "travel_agency_frontend",
    }),
    spanProcessors: [
      new SimpleSpanProcessor(
        new OTLPTraceExporter({ url: OTEL_ENDPOINT }),
      ),
    ],
  });

  trace.setGlobalTracerProvider(provider);

  registerInstrumentations({
    tracerProvider: provider,
  });

  console.log("OpenTelemetry tracing enabled (OTLP HTTP → %s)", OTEL_ENDPOINT);
}
