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

  it("denies unknown routes by returning null", () => {
    expect(resolveBackendPath(["unmapped", "resource"])).toBeNull();
  });

  it("resolves trip timeline paths with non-UUID trip IDs", () => {
    expect(resolveBackendPath(["trips", "trip_1cad495b9586", "timeline"])).toBe(
      "api/trips/trip_1cad495b9586/timeline"
    );
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
});
