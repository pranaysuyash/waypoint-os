import { NextRequest, NextResponse } from 'next/server';
import { bffHeaders, bffJson, isAuthStatus } from "@/lib/bff-auth";

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
    return bffJson({ error: 'agentId is required' }, 400);
  }

  try {
    const response = await fetch(
      `${SPINE_API_URL}/analytics/agent/${encodeURIComponent(agentId)}/drill-down?metric=${metric}`,
      {
        method: "GET",
        headers: bffHeaders(request),
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return bffJson({ agentId, metric, trips: [], count: 0 });
      }
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Analytics service responded with ${response.status}`);
    }

    const data = await response.json();
    return bffJson({
      agentId,
      metric,
      trips: data.trips || [],
      count: (data.trips || []).length,
    } as DrillDownResponse);
  } catch (error) {
    console.error('Error proxying to analytics service:', error);
    return bffJson({
      agentId,
      metric,
      trips: [],
      count: 0,
    } as DrillDownResponse);
  }
}
