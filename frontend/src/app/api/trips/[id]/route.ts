import { NextRequest, NextResponse } from "next/server";

// Mock trip data (in production, this would come from a database)
const MOCK_TRIPS: Record<string, {
  id: string;
  destination: string;
  type: string;
  state: "green" | "amber" | "red" | "blue";
  age: string;
  createdAt: string;
  updatedAt: string;
}> = {
  "TRP-2026-SGP-0315": {
    id: "TRP-2026-SGP-0315",
    destination: "Singapore",
    type: "Family",
    state: "green",
    age: "2h ago",
    createdAt: "2026-04-16T08:00:00Z",
    updatedAt: "2026-04-16T10:00:00Z",
  },
  "TRP-2026-DXB-0418": {
    id: "TRP-2026-DXB-0418",
    destination: "Dubai",
    type: "Corporate",
    state: "blue",
    age: "5h ago",
    createdAt: "2026-04-16T05:00:00Z",
    updatedAt: "2026-04-16T07:00:00Z",
  },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const trip = MOCK_TRIPS[id];

    if (!trip) {
      return NextResponse.json(
        { error: "Trip not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(trip);
  } catch (error) {
    console.error("Error fetching trip:", error);
    return NextResponse.json(
      { error: "Failed to fetch trip" },
      { status: 500 }
    );
  }
}
