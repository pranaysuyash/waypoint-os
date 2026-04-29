import { describe, expect, it } from "vitest";
import { loadScenarioById, loadScenarioList } from "../scenario-loader";

describe("scenario-loader docs catalog", () => {
  it("includes doc-backed scenarios in the catalog", () => {
    const scenarios = loadScenarioList();
    const docScenario = scenarios.find((item) => item.source === "doc");

    expect(docScenario).toBeTruthy();
    expect(docScenario?.id).toMatch(/^doc-/);
    expect(docScenario?.title).toBeTruthy();
  });

  it("can load a doc-backed scenario detail", () => {
    const scenarios = loadScenarioList();
    const docScenario = scenarios.find((item) => item.source === "doc");

    expect(docScenario).toBeTruthy();

    const detail = loadScenarioById(docScenario!.id);
    expect(detail).not.toBeNull();
    expect(detail?.input.raw_note).toBeTruthy();
    expect(detail?.input.owner_note).toContain("Loaded from doc scenario template");
  });

  it("infers emergency booking config for the emotional sentiment pivot scenario", () => {
    const detail = loadScenarioById("doc-additional-scenarios-316-emotional-ai-sentiment-pivot");

    expect(detail).not.toBeNull();
    expect(detail?.input.stage).toBe("booking");
    expect(detail?.input.mode).toBe("emergency");
  });
});
