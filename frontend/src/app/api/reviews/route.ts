import { NextRequest, NextResponse } from "next/server";

const MOCK_REVIEWS = [
  {
    id: "REV-001",
    tripId: "TRP-2026-MSC-0422",
    tripReference: "TRP-2026-MSC-0422",
    destination: "Moscow",
    tripType: "Solo",
    partySize: 1,
    dateWindow: "Jun 10-20",
    value: 3200,
    currency: "USD",
    agentId: "agent-001",
    agentName: "Sarah Chen",
    submittedAt: "2026-04-14T12:00:00Z",
    status: "pending",
    reason: "Unusual solo destination, requires owner review per policy",
    agentNotes: "Client is experienced traveler, has visited Russia before. Visa processing started.",
    riskFlags: ["unusual_destination", "visa_required"],
  },
  {
    id: "REV-002",
    tripId: "TRP-2026-PAR-0430",
    tripReference: "TRP-2026-PAR-0430",
    destination: "Paris",
    tripType: "Anniversary",
    partySize: 2,
    dateWindow: "Oct 14-21",
    value: 8500,
    currency: "USD",
    agentId: "agent-002",
    agentName: "Mike Johnson",
    submittedAt: "2026-04-12T10:00:00Z",
    status: "pending",
    reason: "High-value anniversary trip exceeds auto-approval threshold",
    agentNotes: "Client requested luxury accommodations and private tours. Repeat customer.",
    riskFlags: ["high_value"],
  },
  {
    id: "REV-003",
    tripId: "TRP-2026-BKK-0401",
    tripReference: "TRP-2026-BKK-0401",
    destination: "Bangkok",
    tripType: "Group",
    partySize: 12,
    dateWindow: "Sep 5-12",
    value: 12000,
    currency: "USD",
    agentId: "agent-003",
    agentName: "Alex Kim",
    submittedAt: "2026-04-13T10:00:00Z",
    status: "escalated",
    reason: "Large group with complex itinerary and tight booking deadline",
    riskFlags: ["high_value", "complex_itinerary", "tight_deadline"],
  },
];

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const status = searchParams.get("status");

    let filtered = MOCK_REVIEWS;
    if (status) {
      filtered = filtered.filter((r) => r.status === status);
    }

    return NextResponse.json({
      items: filtered,
      total: filtered.length,
    });
  } catch (error) {
    console.error("Error fetching reviews:", error);
    return NextResponse.json(
      { error: "Failed to fetch reviews" },
      { status: 500 }
    );
  }
}
