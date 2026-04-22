import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tripIds, assignTo, reason, notifyAssignee } = body;

    if (!tripIds || !Array.isArray(tripIds) || !assignTo) {
      return NextResponse.json(
        { error: "tripIds (string[]) and assignTo are required" },
        { status: 400 }
      );
    }

    return NextResponse.json({
      success: true,
      assigned: tripIds.length,
    });
  } catch (error) {
    console.error("Error assigning trips:", error);
    return NextResponse.json(
      { error: "Failed to assign trips" },
      { status: 500 }
    );
  }
}
