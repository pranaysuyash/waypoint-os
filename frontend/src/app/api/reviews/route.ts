import { NextRequest, NextResponse } from "next/server";
import type { TripReview, ReviewStatus } from "@/types/governance";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

// ============================================================================
// SPINE API RAW TYPES
// Types returned by the spine_api /analytics/reviews endpoint.
// These are transformed into canonical TripReview types for the frontend.
// ============================================================================

interface SpineReview {
  id?: string;
  tripId?: string;
  tripReference?: string;
  destination?: string;
  tripType?: string;
  partySize?: number;
  dateWindow?: string;
  value?: number;
  currency?: string;
  agentId?: string;
  agentName?: string;
  submittedAt?: string;
  status?: string;
  reason?: string;
  agentNotes?: string;
  riskFlags?: string[];
}

interface SpineReviewsResponse {
  items: SpineReview[];
  total: number;
}

const STATUS_MAP: Record<string, ReviewStatus> = {
  pending: "pending",
  approved: "approved",
  rejected: "rejected",
  escalated: "escalated",
  revision_needed: "revision_needed",
};

function mapStatus(raw: string): ReviewStatus {
  return STATUS_MAP[raw] ?? "pending";
}

function transformReviewToFrontendFormat(review: SpineReview): TripReview {
  return {
    id: review.id ?? review.tripId ?? `review-${Math.random().toString(36).slice(2, 11)}`,
    tripId: review.tripId ?? "",
    tripReference: review.tripReference ?? review.id ?? "",
    destination: review.destination ?? "Unknown",
    tripType: review.tripType ?? "leisure",
    partySize: review.partySize ?? 1,
    dateWindow: review.dateWindow ?? "TBD",
    value: review.value ?? 0,
    currency: review.currency ?? "USD",
    agentId: review.agentId ?? "unassigned",
    agentName: review.agentName ?? "Unassigned",
    submittedAt: review.submittedAt ?? new Date().toISOString(),
    status: mapStatus(review.status ?? ""),
    reason: review.reason ?? "Under review",
    agentNotes: review.agentNotes,
    riskFlags: (review.riskFlags ?? []) as TripReview["riskFlags"],
  };
}

export async function GET(request: NextRequest) {
  try {
    const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${SPINE_API_URL}/analytics/reviews`, {
      method: "GET",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = (await response.json()) as SpineReviewsResponse;

    const reviews = spineApiData.items ?? [];
    const frontendReviews = reviews.map(transformReviewToFrontendFormat);

    const searchParams = request.nextUrl.searchParams;
    const statusFilter = searchParams.get("status");

    let filteredReviews = frontendReviews;
    if (statusFilter) {
      filteredReviews = frontendReviews.filter(
        (review) => review.status === statusFilter
      );
    }

    return NextResponse.json({
      items: filteredReviews,
      total: filteredReviews.length,
    });
  } catch (error) {
    console.error("Error fetching reviews from spine_api:", error);
    return NextResponse.json(
      { error: "Failed to fetch reviews" },
      { status: 500 }
    );
  }
}
