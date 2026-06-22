import { describe, expect, it } from "vitest";
import { formatBudgetDisplay, formatDateWindowDisplay } from "../lead-display";

describe("lead-display", () => {
  it("normalizes label-style budget strings into a readable amount", () => {
    expect(formatBudgetDisplay("Budget: USD 4,500")).toBe("$4,500");
    expect(formatBudgetDisplay("Budget INR 2.5L")).toBe("₹2.5L");
  });

  it("keeps budget missing for zero values", () => {
    expect(formatBudgetDisplay("$0")).toBe("Budget missing");
  });

  it("normalizes unknown date windows into a confirmable label", () => {
    expect(formatDateWindowDisplay("TBD")).toBe("Dates to confirm");
    expect(formatDateWindowDisplay("dates unknown")).toBe("Dates to confirm");
  });
});
