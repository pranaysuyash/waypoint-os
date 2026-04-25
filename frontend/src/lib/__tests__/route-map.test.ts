import { describe, expect, it } from "vitest";
import { resolveBackendPath } from "../route-map";

describe("resolveBackendPath", () => {
  it("maps the spine run BFF endpoint to the backend run endpoint", () => {
    expect(resolveBackendPath(["spine", "run"])).toBe("run");
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
});
