import { describe, expect, it } from "vitest";
import { DECISION_STATE_LABELS } from "../label-maps";

describe("label-maps", () => {
  it("uses operator-facing wording for ask-follow-up decisions", () => {
    expect(DECISION_STATE_LABELS.ASK_FOLLOWUP).toBe("Waiting on Customer");
  });
});
