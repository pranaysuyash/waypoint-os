import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json([]);
}

export async function POST(request: Request) {
  try {
    const { alertId } = await request.json();
    return NextResponse.json({ success: true, dismissed: alertId });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
