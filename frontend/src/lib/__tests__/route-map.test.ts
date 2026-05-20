import { describe, expect, it } from "vitest";
import { resolveBackendPath, resolveBackendRoute } from "../route-map";

describe("resolveBackendPath", () => {
  it("maps the spine run BFF endpoint to the backend run endpoint", () => {
    expect(resolveBackendPath(["spine", "run"])).toBe("run");
  });

  it("keeps long-running spine execution policy in the route registry", () => {
    expect(resolveBackendRoute(["spine", "run"])).toEqual({
      backendPath: "run",
      timeoutMs: 60_000,
    });
  });

  it("keeps frontend-local routes out of the backend registry", () => {
    expect(resolveBackendPath(["version"])).toBeNull();
    expect(resolveBackendPath(["scenarios"])).toBeNull();
    expect(resolveBackendPath(["scenarios", "clean-family-booking"])).toBeNull();
  });

  it("keeps explicit Next API routes out of the catch-all registry", () => {
    expect(resolveBackendPath(["pipeline"])).toBeNull();
    expect(resolveBackendPath(["insights", "agent-trips"])).toBeNull();
    expect(resolveBackendPath(["inbox"])).toBeNull();
    expect(resolveBackendPath(["runs"])).toBeNull();
    expect(resolveBackendPath(["trips", "trip-123"])).toBeNull();
  });

  it("denies stale BFF aliases that are not backed by runtime backend routes", () => {
    expect(resolveBackendPath(["items"])).toBeNull();
    expect(resolveBackendPath(["overrides"])).toBeNull();
    expect(resolveBackendPath(["team", "members", "member-1", "workload"])).toBeNull();
  });

  it("keeps canonical override and team workload routes available", () => {
    expect(resolveBackendPath(["trips", "trip_123", "overrides"])).toBe(
      "trips/trip_123/overrides"
    );
    expect(resolveBackendPath(["overrides", "override-1"])).toBe("overrides/override-1");
    expect(resolveBackendPath(["team", "workload"])).toBe("api/team/workload");
    expect(resolveBackendPath(["team", "members", "member-1"])).toBe(
      "api/team/members/member-1"
    );
  });

  it("denies unknown routes by returning null", () => {
    expect(resolveBackendPath(["unmapped", "resource"])).toBeNull();
  });

  it("resolves trip timeline paths with non-UUID trip IDs", () => {
    expect(resolveBackendPath(["trips", "trip_1cad495b9586", "timeline"])).toBe(
      "api/trips/trip_1cad495b9586/timeline"
    );
  });

  it("maps product-agent runtime and trip event surfaces through the canonical proxy", () => {
    expect(resolveBackendPath(["agents", "runtime"])).toBe("agents/runtime");
    expect(resolveBackendRoute(["agents", "runtime", "run-once"])).toEqual({
      backendPath: "agents/runtime/run-once",
      timeoutMs: 60_000,
    });
    expect(resolveBackendPath(["agents", "runtime", "events"])).toBe("agents/runtime/events");
    expect(resolveBackendPath(["trips", "trip_123", "agent-events"])).toBe("trips/trip_123/agent-events");
    expect(resolveBackendPath(["trips", "trip_123", "reassess"])).toBe("trips/trip_123/reassess");
  });

  it("resolves run step paths with placeholder substitution", () => {
    expect(
      resolveBackendPath([
        "runs",
        "0c5d4e8d-0407-4211-803d-27095e9a896d",
        "steps",
        "decision",
      ])
    ).toBe("runs/0c5d4e8d-0407-4211-803d-27095e9a896d/steps/decision");
  });

  it("resolves run status and run events polling paths", () => {
    expect(resolveBackendPath(["runs", "run_123"])).toBe("runs/run_123");
    expect(resolveBackendPath(["runs", "run_123", "events"])).toBe("runs/run_123/events");
  });

  it("maps typed integrity reads through the system proxy", () => {
    expect(resolveBackendPath(["system", "integrity", "issues"])).toBe(
      "api/system/integrity/issues"
    );
  });

  it("maps booking-data read/write paths through the proxy", () => {
    expect(resolveBackendPath(["trips", "abc123", "booking-data"])).toBe(
      "trips/abc123/booking-data"
    );
    expect(resolveBackendPath(["trips", "abc123", "booking-data", "payment"])).toBe(
      "trips/abc123/booking-data/payment"
    );
  });

  it("maps the payments read-model queue endpoint through the proxy", () => {
    expect(resolveBackendPath(["payments"])).toBe("payments");
  });

  it("maps integration status paths through the proxy", () => {
    expect(resolveBackendPath(["integrations"])).toBe("api/integrations");
    expect(resolveBackendPath(["integrations", "whatsapp"])).toBe(
      "api/integrations/whatsapp"
    );
    expect(resolveBackendPath(["integrations", "gmail"])).toBe(
      "api/integrations/gmail"
    );
  });

  it("maps booking-task ops panel paths through the proxy", () => {
    expect(resolveBackendPath(["booking-tasks", "trip_abc"])).toBe(
      "api/booking-tasks/trip_abc"
    );
    expect(resolveBackendPath(["booking-tasks", "trip_abc", "generate"])).toBe(
      "api/booking-tasks/trip_abc/generate"
    );
    expect(resolveBackendPath(["booking-tasks", "trip_abc", "task_1"])).toBe(
      "api/booking-tasks/trip_abc/task_1"
    );
    expect(resolveBackendPath(["booking-tasks", "trip_abc", "task_1", "complete"])).toBe(
      "api/booking-tasks/trip_abc/task_1/complete"
    );
    expect(resolveBackendPath(["booking-tasks", "trip_abc", "task_1", "cancel"])).toBe(
      "api/booking-tasks/trip_abc/task_1/cancel"
    );
  });

  it("maps confirmation and execution-timeline ops panel paths through the proxy", () => {
    expect(resolveBackendPath(["trips", "trip_abc", "confirmations"])).toBe(
      "api/trips/trip_abc/confirmations"
    );
    expect(resolveBackendPath(["trips", "trip_abc", "confirmations", "conf_1"])).toBe(
      "api/trips/trip_abc/confirmations/conf_1"
    );
    expect(resolveBackendPath(["trips", "trip_abc", "confirmations", "conf_1", "record"])).toBe(
      "api/trips/trip_abc/confirmations/conf_1/record"
    );
    expect(resolveBackendPath(["trips", "trip_abc", "confirmations", "conf_1", "verify"])).toBe(
      "api/trips/trip_abc/confirmations/conf_1/verify"
    );
    expect(resolveBackendPath(["trips", "trip_abc", "confirmations", "conf_1", "void"])).toBe(
      "api/trips/trip_abc/confirmations/conf_1/void"
    );
    expect(resolveBackendPath(["trips", "trip_abc", "execution-timeline"])).toBe(
      "api/trips/trip_abc/execution-timeline"
    );
  });
});
