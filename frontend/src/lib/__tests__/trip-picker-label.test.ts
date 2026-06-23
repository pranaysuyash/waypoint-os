import { describe, expect, it } from "vitest";
import type { Trip } from "@/lib/api-client";
import { formatTripPickerLabel } from "../trip-picker-label";

describe("formatTripPickerLabel", () => {
  it("keeps the row readable and unique for incomplete trips", () => {
    expect(
      formatTripPickerLabel({
        id: "trip_bc27d5cadcae",
        destination: "",
        type: "",
        age: "Today",
      } as Trip),
    ).toBe("Trip details incomplete · Updated today · BC27");
  });

  it("uses the planning title, recency, and inquiry reference for complete trips", () => {
    expect(
      formatTripPickerLabel({
        id: "trip_10d3343e2ab3",
        destination: "Cape Town",
        type: "business",
        origin: "Mumbai",
        budget: "$5,000",
        dateWindow: "October 2026",
        tripPurpose: "business",
        party: 18,
        validation: {
          is_valid: true,
          errors: [],
          warnings: [],
        } as Trip["validation"],
        decision: {
          decision_state: "ASK_FOLLOWUP",
          hard_blockers: [],
          soft_blockers: [],
          contradictions: [],
          risk_flags: [],
          follow_up_questions: [],
          branch_options: [],
          rationale: {} as Trip["decision"]["rationale"],
          confidence: {} as Trip["decision"]["confidence"],
          commercial_decision: "NONE",
          budget_breakdown: null,
        } as Trip["decision"],
        age: "Yesterday",
      } as Trip),
    ).toBe("Cape Town business trip · Updated yesterday · 10D3");
  });
});
