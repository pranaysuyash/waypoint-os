import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

// Map spine-api status values to frontend state values
const statusMap: Record<string, "green" | "amber" | "red" | "blue"> = {
  new: 'blue',
  assigned: 'amber',
  in_progress: 'amber',
  completed: 'green',
  cancelled: 'red',
};

// Calculate age string from ISO date string
function calculateAge(isoDateString: string): string {
  const created = new Date(isoDateString);
  const now = new Date();
  const diffMs = now.getTime() - created.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w`;
  return `${Math.floor(diffDays / 30)}mo`;
}

// Transform spine-api trip to frontend Trip format
function transformTrip(spineTrip: any): any {
  // Handle case where extracted or nested fields might be null/undefined
  const destination = spineTrip.extracted?.trip_metadata?.destination || 
                     spineTrip.extracted?.destination || 
                     'Unknown';
                     
  const tripType = spineTrip.extracted?.trip_metadata?.primary_intent || 
                   spineTrip.extracted?.primary_intent || 
                   spineTrip.extracted?.trip_purpose || 
                   'leisure';
                   
  const partySize = spineTrip.extracted?.party_profile?.size || 
                    spineTrip.extracted?.party_size || 
                    1;
                    
  const budgetValue = spineTrip.extracted?.budget?.value || 
                      spineTrip.extracted?.budget || 
                      0;
                      
  const dateWindow = spineTrip.extracted?.trip_metadata?.date_window || 
                     spineTrip.extracted?.date_window || 
                     'TBD';
                     
  const originCity = spineTrip.extracted?.origin_city || 
                     spineTrip.extracted?.origin || 
                     'TBD';

  return {
    id: spineTrip.id,
    destination: String(destination),
    type: String(tripType),
    state: statusMap[spineTrip.status] || spineTrip.status || 'blue',
    age: calculateAge(spineTrip.created_at || new Date().toISOString()),
    createdAt: spineTrip.created_at || new Date().toISOString(),
    updatedAt: spineTrip.updated_at || spineTrip.created_at || new Date().toISOString(),
    // Additional fields for UI display
    party: partySize,
    dateWindow: String(dateWindow),
    origin: String(originCity),
    budget: `$${budgetValue.toLocaleString()}`,
    status: spineTrip.status || 'new',
    review_status: spineTrip.analytics?.review_status || null,
    reviewedBy: spineTrip.analytics?.review_metadata?.reviewed_by || null,
    reviewedAt: spineTrip.analytics?.review_metadata?.reviewed_at || null,
    reviewNotes: spineTrip.analytics?.review_metadata?.notes || null,
    // Map decision action
    action: spineTrip.decision?.action || 'PENDING',
    // Map analytics data
    analytics: {
      marginPct: spineTrip.analytics?.margin_pct || 0,
      qualityScore: spineTrip.analytics?.quality_score || 0,
      qualityBreakdown: spineTrip.analytics?.quality_breakdown || {
        completeness: 0,
        feasibility: 0,
        risk: 0,
        profitability: 0
      },
      requiresReview: spineTrip.analytics?.requires_review || false,
      reviewReason: spineTrip.analytics?.review_reason || '',
      approvalRequiredForSend: spineTrip.analytics?.approval_required_for_send || false,
      sendPolicyReason: spineTrip.analytics?.send_policy_reason || '',
      ownerReviewDeadline: spineTrip.analytics?.owner_review_deadline || null,
      escalationSeverity: spineTrip.analytics?.escalation_severity || null,
      revisionCount: spineTrip.analytics?.revision_count || 0,
    },
    // Map validation info
    validation: {
      isValid: spineTrip.validation?.is_valid || false,
      errors: spineTrip.validation?.errors || [],
      warnings: spineTrip.validation?.warnings || [],
      ambiguityReport: spineTrip.validation?.ambiguity_report || [],
      evidenceCoverage: spineTrip.validation?.evidence_coverage || {}
    },
    // Map decision info
    decision: {
      packetId: spineTrip.decision?.packet_id || '',
      currentStage: spineTrip.decision?.current_stage || 'discovery',
      operatingMode: spineTrip.decision?.operating_mode || 'normal_intake',
      decisionState: spineTrip.decision?.decision_state || 'ASK_FOLLOWUP',
      hardBlockers: spineTrip.decision?.hard_blockers || [],
      softBlockers: spineTrip.decision?.soft_blockers || [],
      ambiguities: spineTrip.decision?.ambiguities || [],
      contradictions: spineTrip.decision?.contradictions || [],
      followUpQuestions: spineTrip.decision?.follow_up_questions || [],
      branchOptions: spineTrip.decision?.branch_options || [],
      rationale: spineTrip.decision?.rationale || {},
      confidenceScore: spineTrip.decision?.confidence_score || 0,
      riskFlags: spineTrip.decision?.risk_flags || [],
      commercialDecision: spineTrip.decision?.commercial_decision || 'NONE',
      intentScores: spineTrip.decision?.intent_scores || {},
      nextBestAction: spineTrip.decision?.next_best_action || null,
      budgetBreakdown: spineTrip.decision?.budget_breakdown || {
        verdict: 'not_realistic',
        buckets: [],
        missing_buckets: [],
        total_estimated_low: 0,
        total_estimated_high: 0,
        budget_stated: null,
        gap: null,
        risks: ['budget_unknown'],
        critical_changes: ['Provide a numeric budget for decomposition'],
        must_confirm: [],
        alternative: null,
        maturity: 'heuristic'
      }
    },
    // Map safety info
    safety: spineTrip.safety || {},
    // Map raw input
    rawInput: spineTrip.raw_input || {
      stage: 'discovery',
      operating_mode: 'normal_intake',
      fixture_id: null,
      execution_ms: 0
    }
  };
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    
    const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    // Forward request to spine-api
    const spineApiUrl = `${SPINE_API_URL}/trips/${encodeURIComponent(id)}`;

    const response = await fetch(spineApiUrl, {
      method: "GET",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: "Trip not found" },
          { status: 404 }
        );
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    const transformedTrip = transformTrip(spineApiData);
    
    return NextResponse.json(transformedTrip);
  } catch (error) {
    console.error("Error fetching trip from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch trip" },
      { status: 500 }
    );
  }
}

// Keep PATCH function for local updates (optional - could also proxy)
const PATCHABLE_FIELDS = new Set([
  "customerMessage",
  "agentNotes",
  "budget",
  "party",
  "dateWindow",
  "origin",
  "destination",
  "type",
  "state",
  "status",
]);

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    
    // Map frontend 'state' to backend 'status' if present
    const updates: Record<string, any> = { ...body };
    if (updates.state && !updates.status) {
      // Inverse map for state -> status
      const inverseStatusMap: Record<string, string> = {
        'blue': 'new',
        'amber': 'assigned',
        'green': 'completed',
        'red': 'cancelled'
      };
      updates.status = inverseStatusMap[updates.state as string] || updates.state;
      delete updates.state;
    }

    // Forward request to spine-api
    const SPINE_API_URL = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const spineApiUrl = `${SPINE_API_URL}/trips/${encodeURIComponent(id)}`;

    const response = await fetch(spineApiUrl, {
      method: "PATCH",
      headers: forwardAuthHeaders(request),
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detail = errorData.detail;
      const detailMessage =
        typeof detail === "string"
          ? detail
          : typeof detail?.message === "string"
            ? detail.message
            : undefined;
      const detailFailures = Array.isArray(detail?.failures) ? detail.failures : undefined;
      return NextResponse.json(
        {
          message: detailMessage || `Spine API returned ${response.status}`,
          details: detailFailures,
          error: detail || errorData.error || null,
        },
        { status: response.status }
      );
    }

    const spineApiData = await response.json();
    const transformedTrip = transformTrip(spineApiData);
    
    return NextResponse.json(transformedTrip);
  } catch (error) {
    console.error("Error patching trip via proxy:", error);
    return NextResponse.json(
      { error: "Failed to update trip" },
      { status: 500 }
    );
  }
}
