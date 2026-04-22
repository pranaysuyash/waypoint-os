import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    total: 7,
    unassigned: 1,
    critical: 1,
    atRisk: 2,
  });
}
