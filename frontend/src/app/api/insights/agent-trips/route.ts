import { NextRequest, NextResponse } from 'next/server';
import { forwardAuthHeaders } from "@/lib/proxy-core";

const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";

interface TripData {
  tripId: string;
  destinationName?: string;
  status: 'approved' | 'rejected' | 'pending';
  responseTime?: number;
  suitabilityScore?: number;
  decisionReason?: string;
  createdAt?: string;
}

interface DrillDownResponse {
  agentId: string;
  metric: string;
  trips: TripData[];
  count: number;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const agentId = searchParams.get('agentId');
  const metric = searchParams.get('metric') || 'conversion';

  if (!agentId) {
    return NextResponse.json(
      { error: 'agentId is required' },
      { status: 400 }
    );
  }

  try {
    const response = await fetch(
      `${SPINE_API_URL}/analytics/agent/${encodeURIComponent(agentId)}/drill-down?metric=${metric}`,
      {
        cache: 'no-store',
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { agentId, metric, trips: [], count: 0 },
          { status: 200 }
        );
      }
      throw new Error(`Analytics service responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json({
      agentId,
      metric,
      trips: data.trips || [],
      count: (data.trips || []).length,
    } as DrillDownResponse);
  } catch (error) {
    console.error('Error proxying to analytics service:', error);
    // Return empty trips list on error instead of 500
    return NextResponse.json(
      {
        agentId,
        metric,
        trips: [],
        count: 0,
      } as DrillDownResponse,
      { status: 200 }
    );
  }
}
