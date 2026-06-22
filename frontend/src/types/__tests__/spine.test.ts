import { describe, expect, it } from "vitest";
import { validationLabelFor } from "../spine";

describe("validationLabelFor", () => {
  it("uses operator-facing alert wording for intake detail blockers", () => {
    expect(validationLabelFor("NB01", "alert_title")).toBe("Trip details need attention");
    expect(validationLabelFor("intake_completion", "alert_title")).toBe("Trip details need attention");
  });
});
