import { NextRequest, NextResponse } from 'next/server';
import { forwardAuthHeaders } from "@/lib/proxy-utils";

/**
 * Unified State API — Pure proxy to backend aggregator.
 *
 * The backend (DashboardAggregator) is the sole source of truth.
 * No local aggregation or fallback logic exists in the frontend.
 */
export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/system/unified-state`, {
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Spine API unified-state returned ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Unified State Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch unified state from backend' },
      { status: 502 }
    );
  }
}
