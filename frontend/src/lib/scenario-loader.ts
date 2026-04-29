import { readFileSync, readdirSync } from "fs";
import { join } from "path";

const SCENARIOS_DIR = join(
  process.cwd(),
  "..",
  "data",
  "fixtures",
  "scenarios"
);
const DOCS_SCENARIOS_DIR = join(process.cwd(), "..", "Docs", "personas_scenarios");

const SCENARIO_DOC_PREFIXES = [
  "P",
  "S",
  "ADDITIONAL_SCENARIOS_",
  "AREA_DEEP_DIVE_",
  "SCENARIOS_",
  "OE_",
];

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
  source?: "fixture" | "doc";
  description?: string;
}

export interface ScenarioConfig {
  stage: string;
  mode: string;
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

function docFileToId(fileName: string): string {
  return `doc-${fileName
    .replace(/\.md$/, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")}`;
}

function isScenarioDocFile(fileName: string): boolean {
  return SCENARIO_DOC_PREFIXES.some((prefix) => fileName.startsWith(prefix));
}

function extractDocTitle(content: string, fallback: string): string {
  return content.match(/^#\s+(.+)$/m)?.[1]?.trim() || fallback;
}

function extractDocScenarioDescription(content: string): string {
  const explicitScenario = content.match(/^\*\*Scenario\*\*:\s*(.+)$/m)?.[1]?.trim();
  if (explicitScenario) return explicitScenario;

  const situationMatch = content.match(/## Situation\s+([\s\S]*?)(?:\n## |\n---|\s*$)/i);
  if (situationMatch?.[1]) {
    const lines = situationMatch[1]
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .filter((line) => !line.startsWith("###"));
    if (lines.length > 0) {
      return lines.slice(0, 3).join(" ");
    }
  }

  return "";
}

function inferScenarioMode(content: string): string {
  const text = content.toLowerCase();

  if (
    text.includes("emergency") ||
    text.includes("crisis") ||
    text.includes("fix this now") ||
    text.includes("nowhere to go") ||
    text.includes("stranded") ||
    text.includes("overbooking") ||
    text.includes("lost passport") ||
    text.includes("lost documents")
  ) {
    return "emergency";
  }

  if (
    text.includes("review") ||
    text.includes("audit") ||
    text.includes("coach") ||
    text.includes("correction") ||
    text.includes("margin") ||
    text.includes("approval")
  ) {
    return "audit";
  }

  if (
    text.includes("follow-up") ||
    text.includes("follow up") ||
    text.includes("callback") ||
    text.includes("existing thread") ||
    text.includes("escalation") ||
    text.includes("pivot") ||
    text.includes("reply")
  ) {
    return "follow_up";
  }

  if (text.includes("cancellation") || text.includes("refund")) {
    return "cancellation";
  }

  if (text.includes("post-trip") || text.includes("post trip") || text.includes("feedback")) {
    return "post_trip";
  }

  return "normal_intake";
}

function inferScenarioStage(content: string): string {
  const text = content.toLowerCase();

  if (
    text.includes("booking") ||
    text.includes("check-in") ||
    text.includes("hotel") ||
    text.includes("arrival") ||
    text.includes("arrives") ||
    text.includes("overbooking")
  ) {
    return "booking";
  }

  if (
    text.includes("proposal") ||
    text.includes("quote") ||
    text.includes("review") ||
    text.includes("alternatives") ||
    text.includes("budget") ||
    text.includes("estimate")
  ) {
    return "proposal";
  }

  if (text.includes("shortlist") || text.includes("compare") || text.includes("option")) {
    return "shortlist";
  }

  return "discovery";
}

export function inferScenarioConfigFromText(content: string): ScenarioConfig {
  return {
    stage: inferScenarioStage(content),
    mode: inferScenarioMode(content),
  };
}

function loadDocScenarioList(): ScenarioListItem[] {
  const files = readdirSync(DOCS_SCENARIOS_DIR).filter(
    (f) => f.endsWith(".md") && isScenarioDocFile(f)
  );

  return files.map((file) => {
    const content = readFileSync(join(DOCS_SCENARIOS_DIR, file), "utf-8");
    return {
      id: docFileToId(file),
      title: extractDocTitle(content, file),
      source: "doc",
      description: extractDocScenarioDescription(content),
    };
  });
}

export function loadScenarioList(): ScenarioListItem[] {
  const fixtureFiles = readdirSync(SCENARIOS_DIR).filter((f) => f.endsWith(".json"));
  const fixtures = fixtureFiles.map((file) => {
    const content = readFileSync(join(SCENARIOS_DIR, file), "utf-8");
    const scenario: ScenarioFixture = JSON.parse(content);
    return {
      id: fileNameToId(file),
      title: scenario.title,
      source: "fixture" as const,
      description: scenario.description,
    };
  });

  return [...loadDocScenarioList(), ...fixtures].sort((a, b) => {
    if (a.source !== b.source) {
      return a.source === "doc" ? -1 : 1;
    }
    return a.title.localeCompare(b.title);
  });
}

export function loadScenarioById(id: string): ScenarioDetail | null {
  const fixtureFiles = readdirSync(SCENARIOS_DIR).filter((f) => f.endsWith(".json"));

  for (const file of fixtureFiles) {
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

  const docFiles = readdirSync(DOCS_SCENARIOS_DIR).filter(
    (f) => f.endsWith(".md") && isScenarioDocFile(f)
  );

  for (const file of docFiles) {
    if (docFileToId(file) === id) {
      const content = readFileSync(join(DOCS_SCENARIOS_DIR, file), "utf-8");
      const title = extractDocTitle(content, file);
      const description = extractDocScenarioDescription(content);
      return {
        id,
        input: {
          raw_note: [
            title,
            description,
            "Use this doc-backed scenario as a reusable dev intake template.",
          ]
            .filter(Boolean)
            .join(" "),
          owner_note: `Loaded from doc scenario template: ${file}`,
          structured_json: null,
          itinerary_text: null,
          ...inferScenarioConfigFromText(`${title} ${description}`),
        },
        expected: {
          allowed_decision_states: [],
          required_packet_fields: [],
          forbidden_traveler_terms: [],
          leakage_expected: false,
          assertions: [],
        },
      };
    }
  }

  return null;
}
