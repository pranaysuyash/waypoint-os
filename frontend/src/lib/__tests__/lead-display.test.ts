import { describe, expect, it } from "vitest";
import { formatBudgetDisplay, formatDateWindowDisplay } from "../lead-display";

describe("lead-display", () => {
  it("normalizes label-style budget strings into a readable amount", () => {
    expect(formatBudgetDisplay("Budget: USD 4,500")).toBe("$4,500");
    expect(formatBudgetDisplay("Budget INR 2.5L")).toBe("₹2.5L");
    expect(formatBudgetDisplay("Budget KSh480,000")).toBe("KSh480,000");
  });

  it("preserves range budgets in readable form", () => {
    expect(formatBudgetDisplay("Budget USD 7000-9000")).toBe("$7,000 - $9,000");
    expect(formatBudgetDisplay("Budget INR 2.5L-3L")).toBe("₹2.5L - ₹3L");
  });

  it("keeps budget missing for zero values", () => {
    expect(formatBudgetDisplay("$0")).toBe("Budget missing");
  });

  it("normalizes unknown date windows into a confirmable label", () => {
    expect(formatDateWindowDisplay("TBD")).toBe("Dates to confirm");
    expect(formatDateWindowDisplay("dates unknown")).toBe("Dates to confirm");
  });
});
