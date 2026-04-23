import { NextResponse } from 'next/server';

/**
 * Unified State API — Pure proxy to backend aggregator.
 *
 * The backend (DashboardAggregator) is the sole source of truth.
 * No local aggregation or fallback logic exists in the frontend.
 */
export async function GET() {
  try {
    const response = await fetch('http://localhost:8000/api/system/unified-state', {
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      throw new Error(`Spine API unified-state returned ${response.status}`);
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
