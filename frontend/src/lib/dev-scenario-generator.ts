import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "fs";
import { join } from "path";
import { inferScenarioConfigFromText } from "./scenario-loader";

const REPO_ROOT = join(process.cwd(), "..");
const FIXTURES_DIR = join(REPO_ROOT, "data", "fixtures", "scenarios");
const DOCS_SCENARIO_DIR = join(REPO_ROOT, "Docs", "personas_scenarios");

export type DevScenarioSourceMode = "docs" | "fixtures" | "llm";

export interface DevScenarioInput {
  raw_note: string;
  owner_note: string | null;
  structured_json: Record<string, unknown> | null;
  itinerary_text: string | null;
  stage: string;
  operating_mode: string;
  strict_leakage: false;
  scenario_id: string;
}

export interface DevScenarioPayload {
  source: "docs_template" | "fixture_template" | "llm_generated";
  title: string;
  input: DevScenarioInput;
  prompt: string;
  persisted_fixture: {
    scenario_id: string;
    file_name: string;
    file_path: string;
  };
}

function randomPick<T>(items: T[]): T {
  return items[Math.floor(Math.random() * items.length)];
}

function toFixtureSchema(payload: Omit<DevScenarioPayload, "persisted_fixture">) {
  return {
    scenario_id: payload.input.scenario_id,
    title: payload.title,
    description: `Generated for dev reuse (${payload.source})`,
    inputs: {
      raw_note: payload.input.raw_note,
      owner_note: payload.input.owner_note,
      structured_json: payload.input.structured_json,
      itinerary_text: payload.input.itinerary_text,
      stage: payload.input.stage,
      operating_mode: payload.input.operating_mode,
      strict_leakage: payload.input.strict_leakage,
      scenario_id: payload.input.scenario_id,
    },
    expected: {
      allowed_terminal_states: ["completed", "blocked", "failed"],
      notes: [`Dev-generated from ${payload.source}`, `Prompt: ${payload.prompt}`],
    },
  };
}

function persistScenario(payload: Omit<DevScenarioPayload, "persisted_fixture">): DevScenarioPayload {
  mkdirSync(FIXTURES_DIR, { recursive: true });
  const now = new Date();
  const stamp =
    `${now.getUTCFullYear()}` +
    `${String(now.getUTCMonth() + 1).padStart(2, "0")}` +
    `${String(now.getUTCDate()).padStart(2, "0")}` +
    `${String(now.getUTCHours()).padStart(2, "0")}` +
    `${String(now.getUTCMinutes()).padStart(2, "0")}` +
    `${String(now.getUTCSeconds()).padStart(2, "0")}`;
  const scenarioId = payload.input.scenario_id || `DEV-GEN-${stamp}`;
  const fileName = `SC-9${stamp.slice(-2)}_${scenarioId.replace(/[^A-Za-z0-9]+/g, "_")}.json`;
  const filePath = join(FIXTURES_DIR, fileName);
  writeFileSync(filePath, JSON.stringify(toFixtureSchema(payload), null, 2));

  return {
    ...payload,
    persisted_fixture: {
      scenario_id: scenarioId,
      file_name: fileName,
      file_path: filePath,
    },
  };
}

function fixtureTemplates(prompt: string): Omit<DevScenarioPayload, "persisted_fixture">[] {
  const files = readdirSync(FIXTURES_DIR).filter((f) => f.endsWith(".json"));
  const out: Omit<DevScenarioPayload, "persisted_fixture">[] = [];

  for (const file of files) {
    try {
      const raw = readFileSync(join(FIXTURES_DIR, file), "utf-8");
      const parsed = JSON.parse(raw);
      const inputs = parsed?.inputs;
      if (!inputs || !inputs.raw_note) continue;
      out.push({
        source: "fixture_template",
        title: parsed?.title ?? file,
        prompt,
        input: {
          raw_note: String(inputs.raw_note),
          owner_note: inputs.owner_note ?? null,
          structured_json: inputs.structured_json ?? null,
          itinerary_text: inputs.itinerary_text ?? null,
          stage: "discovery",
          operating_mode: "normal_intake",
          strict_leakage: false,
          scenario_id: `DEV-FIX-${Date.now()}`,
        },
      });
    } catch {
      continue;
    }
  }

  return out;
}

function docsTemplates(prompt: string): Omit<DevScenarioPayload, "persisted_fixture">[] {
  const files = readdirSync(DOCS_SCENARIO_DIR).filter((f) => f.endsWith(".md"));
  const out: Omit<DevScenarioPayload, "persisted_fixture">[] = [];

  for (const file of files) {
    try {
      const text = readFileSync(join(DOCS_SCENARIO_DIR, file), "utf-8");
      const titleMatch = text.match(/^#\s+(.+)$/m);
      const quoteMatch = text.match(/(?:Customer|Message|Input)\s*[:\-]\s*"([^"]{40,})"/i);
      const bulletMatch = text.match(/^-\s+(?:Customer|Message|Input)\s*[:\-]\s*(.+)$/im);
      const candidate = quoteMatch?.[1] ?? bulletMatch?.[1];
      if (!candidate || candidate.trim().length < 60) continue;
      const config = inferScenarioConfigFromText(`${titleMatch?.[1] ?? file} ${text}`);

      out.push({
        source: "docs_template",
        title: titleMatch?.[1]?.trim() ?? file,
        prompt,
        input: {
          raw_note: candidate.trim(),
          owner_note: `Auto-generated from scenario doc template: ${file}`,
          structured_json: null,
          itinerary_text: null,
          stage: config.stage as "discovery" | "shortlist" | "proposal" | "booking",
          operating_mode: config.mode as "normal_intake" | "audit" | "emergency" | "follow_up" | "cancellation" | "post_trip",
          strict_leakage: false,
          scenario_id: `DEV-DOC-${Date.now()}`,
        },
      });
    } catch {
      continue;
    }
  }

  return out;
}

async function llmGenerate(prompt: string): Promise<Omit<DevScenarioPayload, "persisted_fixture">> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY not found. Put it in frontend/.env.local");
  }

  const req = {
    model: process.env.DEV_SCENARIO_LLM_MODEL || "gpt-4.1-mini",
    input: `Generate one realistic messy travel-agency customer call note for intake testing. Keep it 80-160 words. Theme: ${prompt}. Return strict JSON with keys raw_note and owner_note only.`,
    reasoning: { effort: "low" },
    text: {
      format: {
        type: "json_schema",
        name: "dev_scenario",
        strict: true,
        schema: {
          type: "object",
          additionalProperties: false,
          properties: {
            raw_note: { type: "string" },
            owner_note: { type: "string" },
          },
          required: ["raw_note", "owner_note"],
        },
      },
    },
    max_output_tokens: 1200,
  };

  const resp = await fetch("https://api.openai.com/v1/responses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(req),
  });

  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`LLM generation failed: HTTP ${resp.status} ${body}`);
  }

  const data = await resp.json();
  const outputText =
    (typeof data?.output_text === "string" && data.output_text.trim().length > 0
      ? data.output_text
      : undefined) ??
    (Array.isArray(data?.output)
      ? data.output
          .flatMap((item: { content?: Array<{ text?: string }> }) => item?.content?.map(c => c.text ?? "") ?? [])
          .join("")
          .trim()
      : "");
  if (!outputText) throw new Error("LLM returned empty output text");

  let parsed: { raw_note?: string; owner_note?: string };
  try {
    parsed = JSON.parse(outputText);
  } catch {
    throw new Error("LLM output was not valid JSON");
  }
  if (!parsed?.raw_note) throw new Error("LLM output missing raw_note");

  return {
    source: "llm_generated",
    title: `LLM dev scenario (${new Date().toISOString().slice(0, 10)})`,
    prompt,
    input: {
      raw_note: String(parsed.raw_note),
      owner_note: parsed.owner_note ? String(parsed.owner_note) : "Generated by LLM",
      structured_json: null,
      itinerary_text: null,
      stage: "discovery",
      operating_mode: "normal_intake",
      strict_leakage: false,
      scenario_id: `DEV-LLM-${Date.now()}`,
    },
  };
}

export async function generateDevScenario(prompt: string, mode: DevScenarioSourceMode): Promise<DevScenarioPayload> {
  if (mode === "docs") {
    const docs = docsTemplates(prompt);
    if (docs.length === 0) throw new Error("No docs templates found");
    return persistScenario(randomPick(docs));
  }

  if (mode === "fixtures") {
    const fixtures = fixtureTemplates(prompt);
    if (fixtures.length === 0) throw new Error("No fixture templates found");
    return persistScenario(randomPick(fixtures));
  }

  const generated = await llmGenerate(prompt);
  return persistScenario(generated);
}
