export async function register() {
  // Instrumentation is temporarily disabled while we upgrade the
  // OpenTelemetry SDK. The previous implementation used WebTracerProvider
  // APIs that are no longer available in the installed version.
  // TODO: re-enable telemetry once instrumentation.ts is updated.
}
