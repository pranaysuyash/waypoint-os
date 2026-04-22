import { NextResponse } from "next/server";

const MOCK_TRIPS = [
  { state: "green" },
  { state: "blue" },
  { state: "amber" },
  { state: "red" },
  { state: "green" },
  { state: "amber" },
  { state: "blue" },
];

export async function GET() {
  try {
    const active = MOCK_TRIPS.length;
    const pendingReview = MOCK_TRIPS.filter((t) => t.state === "amber").length;
    const readyToBook = MOCK_TRIPS.filter((t) => t.state === "green").length;
    const needsAttention = MOCK_TRIPS.filter((t) => t.state === "red").length;

    return NextResponse.json({
      active,
      pendingReview,
      readyToBook,
      needsAttention,
    });
  } catch (error) {
    console.error("Error fetching stats:", error);
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
