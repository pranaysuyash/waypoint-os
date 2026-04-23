import { NextRequest, NextResponse } from "next/server";

// Map spine-api status values to frontend state values
const statusMap: Record<string, "green" | "amber" | "red" | "blue"> = {
  new: 'blue',
  assigned: 'amber',
  in_progress: 'amber',
  completed: 'green',
  cancelled: 'red',
};

// Canonical definition of which frontend states count as "in workspace".
// Single source of truth — workspace page and any future consumer must use
// the ?view=workspace param rather than client-side filtering.
const WORKSPACE_STATES = new Set(["green", "amber", "red"] as const);

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

// Helper function to safely get nested values
function getNestedValue(obj: any, path: string, defaultValue: any = null): any {
  const parts = path.split('.');
  let current = obj;
  
  for (const part of parts) {
    if (current === null || current === undefined) {
      return defaultValue;
    }
    current = current[part];
  }
  
  return current === undefined ? defaultValue : current;
}

// Transform spine-api trip to frontend Trip format
function transformTrip(spineTrip: any): any {
  // Extract destination from facts if available, otherwise from extracted.trip_metadata
  const destination = getNestedValue(spineTrip, 'extracted.facts.destination_candidates.value.0') ||
                     getNestedValue(spineTrip, 'extracted.trip_metadata.destination') ||
                     getNestedValue(spineTrip, 'extracted.destination') ||
                     'Unknown';
                     
  // Extract trip type from facts if available, otherwise from extracted.trip_metadata
  const tripType = getNestedValue(spineTrip, 'extracted.facts.primary_intent.value.0') ||
                   getNestedValue(spineTrip, 'extracted.facts.trip_purpose.value.0') ||
                   getNestedValue(spineTrip, 'extracted.trip_metadata.primary_intent') ||
                   getNestedValue(spineTrip, 'extracted.trip_metadata.trip_purpose') ||
                   getNestedValue(spineTrip, 'extracted.primary_intent') ||
                   getNestedValue(spineTrip, 'extracted.trip_purpose') ||
                   'leisure';
                   
  // Extract party size from facts if available, otherwise from extracted.trip_metadata
  const partySize = getNestedValue(spineTrip, 'extracted.facts.party_profile.value') ||
                    getNestedValue(spineTrip, 'extracted.facts.party_size.value') ||
                    getNestedValue(spineTrip, 'extracted.trip_metadata.party_profile.size') ||
                    getNestedValue(spineTrip, 'extracted.trip_metadata.party_size') ||
                    getNestedValue(spineTrip, 'extracted.party_profile.size') ||
                    getNestedValue(spineTrip, 'extracted.party_size') ||
                    1;
                    
  // Extract budget value from facts if available, otherwise from extracted.trip_metadata
  const budgetValue = getNestedValue(spineTrip, 'extracted.facts.budget.value') ||
                      getNestedValue(spineTrip, 'extracted.trip_metadata.budget.value') ||
                      getNestedValue(spineTrip, 'extracted.budget.value') ||
                      getNestedValue(spineTrip, 'extracted.budget') ||
                      0;
                      
  // Extract date window from facts if available, otherwise from extracted.trip_metadata
  const dateWindow = getNestedValue(spineTrip, 'extracted.facts.date_window.value') ||
                     getNestedValue(spineTrip, 'extracted.trip_metadata.date_window.value') ||
                     getNestedValue(spineTrip, 'extracted.trip_metadata.date_window') ||
                     getNestedValue(spineTrip, 'extracted.date_window') ||
                     'TBD';
                     
  // Extract origin city from facts if available, otherwise from extracted.trip_metadata
  const originCity = getNestedValue(spineTrip, 'extracted.facts.origin_city.value') ||
                     getNestedValue(spineTrip, 'extracted.trip_metadata.origin_city.value') ||
                     getNestedValue(spineTrip, 'extracted.trip_metadata.origin_city') ||
                     getNestedValue(spineTrip, 'extracted.origin_city') ||
                     getNestedValue(spineTrip, 'extracted.origin') ||
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

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const view = searchParams.get("view");

    // Strip our custom param before forwarding to spine-api
    const forwardParams = new URLSearchParams(searchParams.toString());
    forwardParams.delete("view");
    const query = forwardParams.toString();
    const spineApiUrl = `http://localhost:8000/trips${query ? `?${query}` : ""}`;

    const response = await fetch(spineApiUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    
    let transformedItems: any[];

    if (spineApiData.items && Array.isArray(spineApiData.items)) {
      transformedItems = spineApiData.items.map(transformTrip);
    } else {
      transformedItems = Array.isArray(spineApiData)
        ? spineApiData.map(transformTrip)
        : [transformTrip(spineApiData)];
    }

    // Server-side view filter — canonical definitions live here
    if (view === "workspace") {
      transformedItems = transformedItems.filter(
        (trip: any) => WORKSPACE_STATES.has(trip.state)
      );
    }

    return NextResponse.json({
      items: transformedItems,
      total: transformedItems.length,
    });
  } catch (error) {
    console.error("Error fetching trips from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch trips" },
      { status: 500 }
    );
  }
}
