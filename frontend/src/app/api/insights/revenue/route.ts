import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const range = searchParams.get("range") || "30d";

  try {
    return NextResponse.json({
      period: range,
      totalPipelineValue: 52000,
      bookedRevenue: 18000,
      projectedRevenue: 35000,
      nearCloseRevenue: 11700,
      avgTripValue: 4857,
      revenueByMonth: [
        { month: "2026-01", inquiries: 8, booked: 2, revenue: 12000 },
        { month: "2026-02", inquiries: 12, booked: 4, revenue: 22000 },
        { month: "2026-03", inquiries: 15, booked: 5, revenue: 28000 },
        { month: "2026-04", inquiries: 7, booked: 2, revenue: 18000 },
      ],
    });
  } catch (error) {
    console.error("Error fetching revenue metrics:", error);
    return NextResponse.json(
      { error: "Failed to fetch revenue metrics" },
      { status: 500 }
    );
  }
}
