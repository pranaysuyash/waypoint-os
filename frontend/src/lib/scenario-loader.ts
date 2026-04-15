import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const SCENARIOS_DIR = join(
  process.cwd(),
  "..",
  "data",
  "fixtures",
  "scenarios"
);

export interface ScenarioInputs {
  raw_note: string | null;
  owner_note: string | null;
  structured_json: Record<string, unknown> | null;
  itinerary_text: string | null;
  stage: string;
  mode: string;
}

export interface ScenarioExpected {
  allowed_decision_states: string[];
  required_packet_fields: string[];
  forbidden_traveler_terms: string[];
  leakage_expected: boolean;
  assertions: Array<{
    type: string;
    message: string;
    field?: string;
    value?: string;
  }>;
}

export interface ScenarioFixture {
  scenario_id: string;
  title: string;
  description: string;
  inputs: ScenarioInputs;
  expected: ScenarioExpected;
}

export interface ScenarioListItem {
  id: string;
  title: string;
}

export interface ScenarioDetail {
  id: string;
  input: ScenarioInputs;
  expected: ScenarioExpected;
}

function fileNameToId(fileName: string): string {
  return fileName
    .replace(/^SC-\d+_/, "")
    .replace(/\.json$/, "")
    .toLowerCase()
    .replace(/_/g, "-");
}

export function loadScenarioList(): ScenarioListItem[] {
  const files = readdirSync(SCENARIOS_DIR).filter((f) => f.endsWith(".json"));

  return files.map((file) => {
    const content = readFileSync(join(SCENARIOS_DIR, file), "utf-8");
    const scenario: ScenarioFixture = JSON.parse(content);
    return {
      id: fileNameToId(file),
      title: scenario.title,
    };
  });
}

export function loadScenarioById(id: string): ScenarioDetail | null {
  const files = readdirSync(SCENARIOS_DIR).filter((f) => f.endsWith(".json"));

  for (const file of files) {
    if (fileNameToId(file) === id) {
      const content = readFileSync(join(SCENARIOS_DIR, file), "utf-8");
      const scenario: ScenarioFixture = JSON.parse(content);
      return {
        id,
        input: scenario.inputs,
        expected: scenario.expected,
      };
    }
  }

  return null;
}