import { NextRequest, NextResponse } from "next/server";

const AGENTS = [
  { id: "agent-001", name: "Sarah Chen" },
  { id: "agent-002", name: "Mike Johnson" },
  { id: "agent-003", name: "Alex Kim" },
];

const INBOX_TRIPS = [
  {
    id: "TRP-2026-MSC-0422",
    reference: "TRP-2026-MSC-0422",
    destination: "Moscow",
    tripType: "Solo",
    partySize: 1,
    dateWindow: "Jun 10-20",
    value: 3200,
    priority: "critical" as const,
    priorityScore: 92,
    stage: "review",
    stageNumber: 4,
    assignedTo: undefined,
    assignedToName: undefined,
    submittedAt: "2026-04-14T10:00:00Z",
    lastUpdated: "2026-04-20T12:00:00Z",
    daysInCurrentStage: 3,
    slaStatus: "breached" as const,
    customerName: "Dmitri V.",
    flags: ["unusual_destination", "visa_required", "overdue"],
  },
  {
    id: "TRP-2026-NYC-0512",
    reference: "TRP-2026-NYC-0512",
    destination: "New York",
    tripType: "Family",
    partySize: 4,
    dateWindow: "Jul 20-28",
    value: 8200,
    priority: "high" as const,
    priorityScore: 78,
    stage: "options",
    stageNumber: 3,
    assignedTo: "agent-003",
    assignedToName: "Alex Kim",
    submittedAt: "2026-04-15T08:00:00Z",
    lastUpdated: "2026-04-19T14:00:00Z",
    daysInCurrentStage: 4,
    slaStatus: "at_risk" as const,
    customerName: "The Patels",
    flags: ["high_value", "tight_deadline"],
  },
  {
    id: "TRP-2026-PAR-0430",
    reference: "TRP-2026-PAR-0430",
    destination: "Paris",
    tripType: "Anniversary",
    partySize: 2,
    dateWindow: "Oct 14-21",
    value: 8500,
    priority: "high" as const,
    priorityScore: 75,
    stage: "details",
    stageNumber: 2,
    assignedTo: "agent-002",
    assignedToName: "Mike Johnson",
    submittedAt: "2026-04-12T10:00:00Z",
    lastUpdated: "2026-04-18T09:00:00Z",
    daysInCurrentStage: 5,
    slaStatus: "at_risk" as const,
    customerName: "James & Lily S.",
    flags: ["high_value", "visa_docs_incomplete"],
  },
  {
    id: "TRP-2026-AND-0420",
    reference: "TRP-2026-AND-0420",
    destination: "Andaman",
    tripType: "Honeymoon",
    partySize: 2,
    dateWindow: "May 15-22",
    value: 4200,
    priority: "medium" as const,
    priorityScore: 55,
    stage: "options",
    stageNumber: 3,
    assignedTo: "agent-003",
    assignedToName: "Alex Kim",
    submittedAt: "2026-04-15T12:00:00Z",
    lastUpdated: "2026-04-18T16:00:00Z",
    daysInCurrentStage: 1,
    slaStatus: "on_track" as const,
    customerName: "Arjun & Priya M.",
    flags: ["tight_deadline"],
  },
  {
    id: "TRP-2026-DXB-0418",
    reference: "TRP-2026-DXB-0418",
    destination: "Dubai",
    tripType: "Corporate",
    partySize: 8,
    dateWindow: "Jul 3-7",
    value: 12000,
    priority: "medium" as const,
    priorityScore: 50,
    stage: "intake",
    stageNumber: 1,
    assignedTo: "agent-002",
    assignedToName: "Mike Johnson",
    submittedAt: "2026-04-16T05:00:00Z",
    lastUpdated: "2026-04-16T07:00:00Z",
    daysInCurrentStage: 1,
    slaStatus: "on_track" as const,
    customerName: "Acme Corp",
    flags: ["high_value", "corporate"],
  },
  {
    id: "TRP-2026-SGP-0315",
    reference: "TRP-2026-SGP-0315",
    destination: "Singapore",
    tripType: "Family",
    partySize: 4,
    dateWindow: "Aug 1-10",
    value: 5600,
    priority: "low" as const,
    priorityScore: 25,
    stage: "booking",
    stageNumber: 5,
    assignedTo: "agent-001",
    assignedToName: "Sarah Chen",
    submittedAt: "2026-04-16T08:00:00Z",
    lastUpdated: "2026-04-16T10:00:00Z",
    daysInCurrentStage: 0,
    slaStatus: "on_track" as const,
    customerName: "The Wongs",
    flags: [],
  },
  {
    id: "TRP-2026-BKK-0401",
    reference: "TRP-2026-BKK-0401",
    destination: "Bangkok",
    tripType: "Group",
    partySize: 12,
    dateWindow: "Sep 5-12",
    value: 12000,
    priority: "low" as const,
    priorityScore: 20,
    stage: "booking",
    stageNumber: 5,
    assignedTo: "agent-001",
    assignedToName: "Sarah Chen",
    submittedAt: "2026-04-13T08:00:00Z",
    lastUpdated: "2026-04-18T10:00:00Z",
    daysInCurrentStage: 3,
    slaStatus: "on_track" as const,
    customerName: "Thai Food Lovers Club",
    flags: ["complex_itinerary"],
  },
];

export async function GET(request: NextRequest) {
  try {
    const sp = request.nextUrl.searchParams;

    const page = parseInt(sp.get("page") || "1", 10);
    const limit = parseInt(sp.get("limit") || "20", 10);

    let filtered = [...INBOX_TRIPS];

    const priority = sp.get("priority");
    if (priority) {
      const priorities = priority.split(",");
      filtered = filtered.filter((t) => priorities.includes(t.priority));
    }

    const stage = sp.get("stage");
    if (stage) {
      const stages = stage.split(",");
      filtered = filtered.filter((t) => stages.includes(t.stage));
    }

    const assignedTo = sp.get("assignedTo");
    if (assignedTo) {
      const ids = assignedTo.split(",");
      filtered = filtered.filter(
        (t) => t.assignedTo && ids.includes(t.assignedTo)
      );
    }

    const slaStatus = sp.get("slaStatus");
    if (slaStatus) {
      const statuses = slaStatus.split(",");
      filtered = filtered.filter((t) => statuses.includes(t.slaStatus));
    }

    const minValue = sp.get("minValue");
    if (minValue) filtered = filtered.filter((t) => t.value >= parseInt(minValue, 10));

    const maxValue = sp.get("maxValue");
    if (maxValue) filtered = filtered.filter((t) => t.value <= parseInt(maxValue, 10));

    const total = filtered.length;
    const start = (page - 1) * limit;
    const items = filtered.slice(start, start + limit);
    const hasMore = start + limit < total;

    return NextResponse.json({ items, total, hasMore });
  } catch (error) {
    console.error("Error fetching inbox:", error);
    return NextResponse.json(
      { error: "Failed to fetch inbox" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tripIds, action, params } = body;

    if (!tripIds || !Array.isArray(tripIds) || !action) {
      return NextResponse.json(
        { error: "tripIds (string[]) and action are required" },
        { status: 400 }
      );
    }

    return NextResponse.json({
      success: true,
      processed: tripIds.length,
      failed: 0,
    });
  } catch (error) {
    console.error("Error processing bulk action:", error);
    return NextResponse.json(
      { error: "Failed to process bulk action" },
      { status: 500 }
    );
  }
}
