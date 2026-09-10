import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { docsTemplates } from "@/lib/dev-scenario-generator";
import { extractDocScenarioDescription } from "@/lib/scenario-loader";

/**
 * Contract tests for the dev-scenario-generator docs mode (FND-0256 B3b-1).
 *
 * Docs-schema contract (canonical, shared with scenario-loader):
 *   Tier 1: `Customer:`/`Message:`/`Input:` line with a quoted message
 *           (>=40 chars) — crafted customer voice.
 *   Tier 2: `**Scenario**:` line, else first prose lines of `## Situation`
 *           — the ADDITIONAL_SCENARIOS stub shape.
 * Candidates must yield >=60 chars of raw_note text.
 *
 * These tests exercise the real corpus (no mocked directory), per the
 * repo's real-schema test rule: the ADDITIONAL_SCENARIOS series (302 docs,
 * Situation-prose format) was skipped 302/303 before B3b-1; the series
 * must now appear in docsTemplates output.
 */

const DOCS_DIR = join(process.cwd(), "..", "Docs", "personas_scenarios");
const REAL_STUB = "ADDITIONAL_SCENARIOS_100_GROUP_SEAT_ASSIGNMENT_COORDINATION.md";

function stubPath(name: string) {
  return join(DOCS_DIR, name);
}

describe("extractDocScenarioDescription (shared tier-2 parser)", () => {
  it("extracts Situation prose from a real stub doc", () => {
    const text = readFileSync(stubPath(REAL_STUB), "utf-8");
    const description = extractDocScenarioDescription(text);
    expect(description.length).toBeGreaterThan(0);
    expect(description).toContain("group"); // real content from Scenario 100
  });

  it("prefers the explicit **Scenario**: line when present", () => {
    const doc = `# Title\n\n**Scenario**: A traveler needs a last-minute complex multi-city itinerary change with visa constraints.\n\n## Situation\n\nDifferent prose here that should not be the candidate.\n`;
    expect(extractDocScenarioDescription(doc)).toContain("last-minute complex multi-city");
  });
});

describe("docsTemplates (docs mode ingestion)", () => {
  const templates = docsTemplates("contract test");

  it("ingests stub-format docs (the 302-doc series)", () => {
    // Before B3b-1, ADDITIONAL_SCENARIOS stubs were all skipped (302/303).
    // Now at least one real stub must appear in the template list.
    const stubs = templates.filter((t) => t.input.owner_note?.includes(REAL_STUB));
    expect(stubs.length).toBeGreaterThan(0);
    expect(stubs[0].input.raw_note.length).toBeGreaterThanOrEqual(60);
  });

  it("still ingests tier-1 quoted-message docs", () => {
    // Empirically 3 docs in the corpus carry the quoted-message shape; pin
    // the known one so tier 1 (crafted customer voice) stays ingestible.
    const tier1 = templates.filter((t) =>
      t.input.owner_note?.includes("OE_003_A_HANDOFF_FAILURE.md")
    );
    expect(tier1.length).toBeGreaterThan(0);
    // Tier-1 capture is the quoted-message content (quotes stripped by the
    // capture group); assert substance, not syntax.
    expect(tier1[0].input.raw_note.length).toBeGreaterThanOrEqual(60);
  });

  it("raw_note candidates meet the minimum length", () => {
    for (const t of templates) {
      expect(t.input.raw_note.trim().length).toBeGreaterThanOrEqual(60);
    }
  });

  it("every ingested doc records its source file in owner_note", () => {
    for (const t of templates) {
      expect(t.input.owner_note).toMatch(/Auto-generated from scenario doc template: .+\.md$/);
    }
  });
});
