import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    // Forward request to spine-api analytics reviews endpoint
    const response = await fetch("http://localhost:8000/analytics/reviews", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    
    // Transform spine-api reviews to frontend review format
    // spine-api returns: { items: [...], total: N }
    // frontend expects: { items: [...] }
    
    const reviews = spineApiData.items || [];
    
    // Transform each review to match frontend expectations
    const frontendReviews = reviews.map(review => transformReviewToFrontendFormat(review));
    
    // Apply filtering based on status query parameter
    const searchParams = request.nextUrl.searchParams;
    const statusFilter = searchParams.get("status");
    
    let filteredReviews = frontendReviews;
    if (statusFilter) {
      filteredReviews = frontendReviews.filter(review => 
        review.status === statusFilter
      );
    }
    
    return NextResponse.json({
      items: filteredReviews,
      total: filteredReviews.length
    });
  } catch (error) {
    console.error("Error fetching reviews from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch reviews" },
      { status: 500 }
    );
  }
}

// Transform spine-api review to frontend review format
function transformReviewToFrontendFormat(review: any): any {
  // Map spine-api status to frontend status
  const statusMap: Record<string, string> = {
    pending: 'pending',
    approved: 'approved',
    rejected: 'rejected',
    escalated: 'escalated',
    revision_needed: 'revision_needed'
  };
  
  return {
    id: review.id || review.tripId || `review-${Math.random().toString(36).substr(2, 9)}`,
    tripId: review.tripId || '',
    tripReference: review.tripReference || review.id || '',
    destination: review.destination || 'Unknown',
    tripType: review.tripType || 'leisure',
    partySize: review.partySize || 1,
    dateWindow: review.dateWindow || 'TBD',
    value: review.value || 0,
    currency: review.currency || 'USD',
    agentId: review.agentId || 'unassigned',
    agentName: review.agentName || 'Unassigned',
    submittedAt: review.submittedAt || new Date().toISOString(),
    status: statusMap[review.status] || review.status || 'pending',
    reason: review.reason || 'Under review',
    agentNotes: review.agentNotes || '',
    riskFlags: review.riskFlags || []
  };
}