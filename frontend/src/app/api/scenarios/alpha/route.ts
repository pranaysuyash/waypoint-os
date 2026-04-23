import { readFileSync } from "fs";
import { join } from "path";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const filePath = join(process.cwd(), "..", "data", "fixtures", "scenario_alpha.json");
    const content = readFileSync(filePath, "utf-8");
    const data = JSON.parse(content);
    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to load scenario_alpha.json:", error);
    return NextResponse.json({ error: "Failed to load scenario" }, { status: 500 });
  }
}
