import { NextRequest, NextResponse } from "next/server";
import { DevScenarioSourceMode, generateDevScenario } from "@/lib/dev-scenario-generator";

export async function POST(request: NextRequest) {
  if (process.env.NODE_ENV !== "development" && process.env.DEV_SCENARIO_GENERATOR_ENABLED !== "1") {
    return NextResponse.json({ error: "Dev scenario generator is disabled" }, { status: 403 });
  }

  try {
    const body = (await request.json().catch(() => ({}))) as {
      prompt?: string;
      source_mode?: DevScenarioSourceMode;
    };
    const prompt = (body.prompt || "general travel intake stress test").trim();
    const sourceMode = body.source_mode || "docs";
    const generated = await generateDevScenario(prompt, sourceMode);
    return NextResponse.json(generated);
  } catch (error) {
    console.error("Failed to generate dev scenario:", error);
    const message = error instanceof Error ? error.message : "Failed to generate dev scenario";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
