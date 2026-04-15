import { NextResponse } from "next/server";

// Mock pipeline data (in production, this would be calculated from actual trip data)
const MOCK_PIPELINE = [
  { label: "Lead", count: 4 },
  { label: "Qualified", count: 3 },
  { label: "Planning", count: 6 },
  { label: "Quoted", count: 5 },
  { label: "Booked", count: 8 },
  { label: "Traveling", count: 2 },
  { label: "Complete", count: 12 },
];

export async function GET() {
  try {
    return NextResponse.json(MOCK_PIPELINE);
  } catch (error) {
    console.error("Error fetching pipeline:", error);
    return NextResponse.json(
      { error: "Failed to fetch pipeline" },
      { status: 500 }
    );
  }
}
