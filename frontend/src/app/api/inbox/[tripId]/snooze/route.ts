import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ tripId: string }> }
) {
  try {
    const { tripId } = await params;
    const body = await request.json();
    const { snoozeUntil } = body;

    if (!snoozeUntil) {
      return NextResponse.json(
        { error: "snoozeUntil is required" },
        { status: 400 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error snoozing trip:", error);
    return NextResponse.json(
      { error: "Failed to snooze trip" },
      { status: 500 }
    );
  }
}
