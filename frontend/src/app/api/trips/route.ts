import { NextRequest, NextResponse } from "next/server";

// Mock trip data (in production, this would come from a database)
const MOCK_TRIPS = [
  {
    id: "TRP-2026-SGP-0315",
    destination: "Singapore",
    type: "Family",
    state: "green" as const,
    age: "2h ago",
    createdAt: "2026-04-16T08:00:00Z",
    updatedAt: "2026-04-16T10:00:00Z",
    party: 4,
    dateWindow: "Aug 1–10",
    action: "Ready to proceed",
    overdue: false,
  },
  {
    id: "TRP-2026-DXB-0418",
    destination: "Dubai",
    type: "Corporate",
    state: "blue" as const,
    age: "5h ago",
    createdAt: "2026-04-16T05:00:00Z",
    updatedAt: "2026-04-16T07:00:00Z",
    party: 8,
    dateWindow: "Jul 3–7",
    action: "Clarification requested from client",
    overdue: false,
  },
  {
    id: "TRP-2026-AND-0420",
    destination: "Andaman",
    type: "Honeymoon",
    state: "amber" as const,
    age: "1d ago",
    createdAt: "2026-04-15T12:00:00Z",
    updatedAt: "2026-04-15T14:00:00Z",
    party: 2,
    dateWindow: "May 15–22",
    action: "Draft itinerary branch pending",
    overdue: false,
  },
  {
    id: "TRP-2026-MSC-0422",
    destination: "Moscow",
    type: "Solo",
    state: "red" as const,
    age: "2d ago",
    createdAt: "2026-04-14T10:00:00Z",
    updatedAt: "2026-04-14T12:00:00Z",
    party: 1,
    dateWindow: "Jun 10–20",
    action: "Requires owner review",
    overdue: true,
  },
  {
    id: "TRP-2026-BKK-0401",
    destination: "Bangkok",
    type: "Group",
    state: "green" as const,
    age: "3d ago",
    createdAt: "2026-04-13T08:00:00Z",
    updatedAt: "2026-04-13T10:00:00Z",
    party: 12,
    dateWindow: "Sep 5–12",
    action: "Booking confirmation pending",
    overdue: false,
  },
  {
    id: "TRP-2026-PAR-0430",
    destination: "Paris",
    type: "Anniversary",
    state: "amber" as const,
    age: "4d ago",
    createdAt: "2026-04-12T08:00:00Z",
    updatedAt: "2026-04-12T10:00:00Z",
    party: 2,
    dateWindow: "Oct 14–21",
    action: "Visa docs incomplete",
    overdue: false,
  },
  {
    id: "TRP-2026-NYC-0512",
    destination: "New York",
    type: "Family",
    state: "blue" as const,
    age: "6h ago",
    createdAt: "2026-04-16T06:00:00Z",
    updatedAt: "2026-04-16T08:00:00Z",
    party: 5,
    dateWindow: "Dec 20–28",
    action: "Budget clarification needed",
    overdue: false,
  },
];

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const state = searchParams.get("state");
    const limit = parseInt(searchParams.get("limit") || "10");
    const offset = parseInt(searchParams.get("offset") || "0");

    // Filter by state if provided
    let filtered = MOCK_TRIPS;
    if (state) {
      filtered = filtered.filter((trip) => trip.state === state);
    }

    // Apply pagination
    const paginated = filtered.slice(offset, offset + limit);

    return NextResponse.json({
      items: paginated,
      total: filtered.length,
    });
  } catch (error) {
    console.error("Error fetching trips:", error);
    return NextResponse.json(
      { error: "Failed to fetch trips" },
      { status: 500 }
    );
  }
}
