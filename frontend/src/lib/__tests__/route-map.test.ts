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

  it("resolves trip timeline and stage transition paths with non-UUID trip IDs", () => {
    expect(resolveBackendPath(["trips", "trip_1cad495b9586", "timeline"])).toBe(
      "api/trips/trip_1cad495b9586/timeline"
    );
    expect(resolveBackendPath(["trips", "trip_1cad495b9586", "stage"])).toBe(
      "api/v1/trips/trip_1cad495b9586/stage"
    );
    expect(resolveBackendPath(["v1", "trips", "trip_1cad495b9586", "stage"])).toBe(
      "api/v1/trips/trip_1cad495b9586/stage"
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

  it("maps workbench v1 panel fetches through the canonical BFF proxy (D-10)", () => {
    // FinancialSettlementPanel (VCC) — the original D-10 hardcoded-URL revert.
    expect(resolveBackendPath(["v1", "settlement", "vcc", "issue"])).toBe(
      "api/v1/settlement/vcc/issue"
    );
    // GDSSandboxPanel
    expect(resolveBackendPath(["v1", "gds-sandbox", "search"])).toBe(
      "api/v1/gds-sandbox/search"
    );
    expect(resolveBackendPath(["v1", "gds-sandbox", "book"])).toBe(
      "api/v1/gds-sandbox/book"
    );
    // IVRBypassPanel
    expect(resolveBackendPath(["v1", "ivr-bypass", "calls", "dispatch"])).toBe(
      "api/v1/ivr-bypass/calls/dispatch"
    );
    expect(resolveBackendPath(["v1", "ivr-bypass", "calls", "bridge"])).toBe(
      "api/v1/ivr-bypass/calls/bridge"
    );
    // IROPSAutoHealerPanel / DocumentMRZPanel / PersonaCouncilPanel
    expect(resolveBackendPath(["v1", "irops-healer", "heal"])).toBe(
      "api/v1/irops-healer/heal"
    );
    expect(resolveBackendPath(["v1", "documents", "mrz", "parse-td3"])).toBe(
      "api/v1/documents/mrz/parse-td3"
    );
    expect(resolveBackendPath(["v1", "passenger-rights", "evaluate"])).toBe(
      "api/v1/passenger-rights/evaluate"
    );
    expect(resolveBackendPath(["v1", "financial-ops", "convert-currency"])).toBe(
      "api/v1/financial-ops/convert-currency"
    );
    expect(resolveBackendPath(["v1", "counterfactual", "replan-disruption"])).toBe(
      "api/v1/counterfactual/replan-disruption"
    );
    expect(resolveBackendPath(["v1", "counterfactual", "group-consensus"])).toBe(
      "api/v1/counterfactual/group-consensus"
    );
    expect(resolveBackendPath(["v1", "boundaries", "tokens", "issue"])).toBe(
      "api/v1/boundaries/tokens/issue"
    );
    // DutyOfCareRadar / Charter / Compiler / Logistics / Epistemic
    expect(resolveBackendPath(["v1", "duty-of-care-radar", "cockpit", "summary"])).toBe(
      "api/v1/duty-of-care-radar/cockpit/summary"
    );
    expect(resolveBackendPath(["v1", "charter-aviation", "quotes", "calculate"])).toBe(
      "api/v1/charter-aviation/quotes/calculate"
    );
    expect(resolveBackendPath(["v1", "proposal-compiler", "compile"])).toBe(
      "api/v1/proposal-compiler/compile"
    );
    expect(resolveBackendPath(["v1", "logistics", "connection-risk"])).toBe(
      "api/v1/logistics/connection-risk"
    );
    expect(resolveBackendPath(["v1", "logistics", "route-geometry", "evaluate"])).toBe(
      "api/v1/logistics/route-geometry/evaluate"
    );
    expect(resolveBackendPath(["v1", "logistics", "route-geometry", "open-jaw"])).toBe(
      "api/v1/logistics/route-geometry/open-jaw"
    );
    expect(resolveBackendPath(["v1", "epistemic", "constraints", "extract-implicit"])).toBe(
      "api/v1/epistemic/constraints/extract-implicit"
    );
    // Stress benchmark is long-running and keeps its extended timeout policy.
    expect(resolveBackendRoute(["v1", "benchmarking", "stress-test"])).toEqual({
      backendPath: "api/v1/benchmarking/stress-test",
      timeoutMs: 60_000,
    });
  });

  it("maps the canonical agency-scoped yield contract and denies invented paths", () => {
    expect(resolveBackendPath(["v1", "yield", "arbitrage", "trip_123"])).toBe(
      "api/v1/yield/arbitrage/trip_123"
    );
    expect(resolveBackendPath(["v1", "yield", "swap-supplier"])).toBe(
      "api/v1/yield/swap-supplier"
    );
    expect(resolveBackendPath(["v1", "yield-arbitrage", "rates", "compare"])).toBeNull();
    expect(resolveBackendPath(["v1", "yield-arbitrage", "reticket", "execute"])).toBeNull();
  });

  it("routes traveler public surfaces through the allowlist (F-43)", () => {
    // /p/[token] proposal share page
    expect(resolveBackendPath(["public", "proposals", "tok_abc"])).toBe(
      "api/public/proposals/tok_abc"
    );
    expect(resolveBackendPath(["public", "proposals", "tok_abc", "calculate"])).toBe(
      "api/public/proposals/tok_abc/calculate"
    );
    expect(resolveBackendPath(["public", "proposals", "tok_abc", "accept"])).toBe(
      "api/public/proposals/tok_abc/accept"
    );
    // Traveler companion journey graph (signed share token rides the query string)
    expect(resolveBackendPath(["public", "journey-graph", "trip_123"])).toBe(
      "api/public/journey-graph/trip_123"
    );
    // Group member decision page
    expect(resolveBackendPath(["v1", "group", "token", "tok_1"])).toBe(
      "api/v1/group/token/tok_1"
    );
    expect(resolveBackendPath(["v1", "group", "token", "tok_1", "pay-share"])).toBe(
      "api/v1/group/token/tok_1/pay-share"
    );
    // 2026-09-06 route-inventory gate: no backend endpoint exists for
    // logistics/assess-route — it stays denied until the backend ships it.
    expect(resolveBackendPath(["v1", "logistics", "assess-route"])).toBeNull();
  });

  it("keeps wildcard v1/public reachability denied now that next.config rewrites are gone (F-43)", () => {
    expect(resolveBackendPath(["public", "unknown-resource"])).toBeNull();
    expect(resolveBackendPath(["public", "proposals"])).toBeNull();
    expect(resolveBackendPath(["v1", "not-a-real-router"])).toBeNull();
    expect(resolveBackendPath(["v1", "fulfillment", "proposals", "fulfill"])).toBeNull();
  });
});
