import { readFileSync } from "fs";
import { join } from "path";
import { NextResponse } from "next/server";

const scenarioAlphaPath = join(process.cwd(), "..", "data", "fixtures", "scenario_alpha.json");
let scenarioAlphaData: unknown;
let scenarioAlphaLoadError: unknown;

try {
  scenarioAlphaData = JSON.parse(readFileSync(scenarioAlphaPath, "utf-8"));
} catch (error) {
  scenarioAlphaLoadError = error;
}

export async function GET() {
  try {
    if (scenarioAlphaLoadError) {
      throw scenarioAlphaLoadError;
    }
    return NextResponse.json(scenarioAlphaData);
  } catch (error) {
    console.error("Failed to load scenario_alpha.json:", error);
    return NextResponse.json({ error: "Failed to load scenario" }, { status: 500 });
  }
}
