import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

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

// Map spine-api status to inbox stage
const stageMap: Record<string, string> = {
  new: 'intake',
  assigned: 'options',
  in_progress: 'details',
  completed: 'booking',
  cancelled: 'completed'
};

// Helper function to extract customer name from trip data
function extractCustomerName(trip: any): string {
  // Try to get from raw input or notes
  if (trip.rawInput?.fixture_id) {
    return `Customer ${trip.rawInput.fixture_id}`;
  }
  
  // Fallback to extracting from ID or using placeholder
  return `Client ${trip.id.slice(-6)}`;
}

// Helper function to extract flags based on trip data
function extractFlags(trip: any): string[] {
  const flags: string[] = [];
  
  // Add flags based on validation errors
  if (!trip.validation?.is_valid) {
    flags.push("validation_failed");
  }
  
  // Add flags based on confidence score
  const confidence = trip.decision?.confidence_score || 0;
  if (confidence < 0.3) flags.push("low_confidence");
  if (confidence > 0.8) flags.push("high_confidence");
  
  // Add flags based on analytics
  if (trip.analytics?.requires_review) {
    flags.push("requires_review");
  }
  
  // Add flags based on margin
  const margin = trip.analytics?.margin_pct || 0;
  if (margin < 10) flags.push("low_margin");
  if (margin > 30) flags.push("high_margin");
  
  // Add flags based on decision state
  if (trip.decision?.decision_state === "ASK_FOLLOWUP") {
    flags.push("needs_clarification");
  }
  
  // Add flags based on hard blockers
  if (trip.decision?.hard_blockers?.length && trip.decision.hard_blockers.length > 0) {
    flags.push("missing_information");
  }
  
  // Add flags based on budget
  const budgetStr = trip.budget || '$0';
  const budgetValue = parseFloat(budgetStr.replace(/[^\d.-]/g, '') || '0');
  if (budgetValue > 100000) flags.push("high_value");
  if (budgetValue < 1000) flags.push("low_value");
  
  return flags;
}

// Helper function to get stage number for inbox display
function getStageNumber(stage: string): number {
  const stageMap: Record<string, number> = {
    intake: 1,
    options: 2,
    details: 3,
    review: 4,
    booking: 5,
    completed: 6
  };
  return stageMap[stage] || 0;
}

// Transform spine-api trip to frontend inbox trip format
function transformTripToInboxFormat(trip: any): any {
  // Extract destination from facts if available, otherwise from extracted.trip_metadata
  const destination = getNestedValue(trip, 'extracted.facts.destination_candidates.value.0') ||
                     getNestedValue(trip, 'extracted.trip_metadata.destination') ||
                     getNestedValue(trip, 'extracted.destination') ||
                     'Unknown';
                     
  // Extract trip type from facts if available, otherwise from extracted.trip_metadata
  const tripType = getNestedValue(trip, 'extracted.facts.primary_intent.value.0') ||
                   getNestedValue(trip, 'extracted.facts.trip_purpose.value.0') ||
                   getNestedValue(trip, 'extracted.trip_metadata.primary_intent') ||
                   getNestedValue(trip, 'extracted.trip_metadata.trip_purpose') ||
                   getNestedValue(trip, 'extracted.primary_intent') ||
                   getNestedValue(trip, 'extracted.trip_purpose') ||
                   'leisure';
                   
  // Extract party size from facts if available, otherwise from extracted.trip_metadata
  const partySize = getNestedValue(trip, 'extracted.facts.party_profile.value') ||
                    getNestedValue(trip, 'extracted.facts.party_size.value') ||
                    getNestedValue(trip, 'extracted.trip_metadata.party_profile.size') ||
                    getNestedValue(trip, 'extracted.trip_metadata.party_size') ||
                    getNestedValue(trip, 'extracted.party_profile.size') ||
                    getNestedValue(trip, 'extracted.party_size') ||
                    1;
                    
  // Extract budget value from facts if available, otherwise from extracted.trip_metadata
  const budgetValue = getNestedValue(trip, 'extracted.facts.budget.value') ||
                      getNestedValue(trip, 'extracted.trip_metadata.budget.value') ||
                      getNestedValue(trip, 'extracted.budget.value') ||
                      getNestedValue(trip, 'extracted.budget') ||
                      0;
                      
  // Extract date window from facts if available, otherwise from extracted.trip_metadata
  const dateWindow = getNestedValue(trip, 'extracted.facts.date_window.value') ||
                     getNestedValue(trip, 'extracted.trip_metadata.date_window.value') ||
                     getNestedValue(trip, 'extracted.trip_metadata.date_window') ||
                     getNestedValue(trip, 'extracted.date_window') ||
                     'TBD';
                     
  // Map spine-api status to inbox stage
  const spineStatus = trip.status || 'new';
  const stage = stageMap[spineStatus] || spineStatus || 'options';
  
  // Determine priority based on analytics/validation
  let priority: 'low' | 'medium' | 'high' | 'critical' = 'medium';
  let priorityScore = 50;
  
  if (trip.analytics?.requires_review || 
      !trip.validation?.is_valid || 
      (trip.decision?.confidence_score || 0) < 0.5) {
    priority = 'high';
    priorityScore = 75;
  }
  
  if ((trip.decision?.confidence_score || 0) < 0.3) {
    priority = 'critical';
    priorityScore = 90;
  }
  
   // Calculate days in current stage based on trip events
   let daysInCurrentStage = 0;
   
   try {
     // Get all timestamps from events and created_at
     const timestamps: string[] = [];
     
     // Add created_at if available
     if (trip.created_at) {
       timestamps.push(trip.created_at);
     }
     
     // Add all event timestamps
     if (Array.isArray(trip.extracted?.events)) {
       trip.extracted.events.forEach((event: any) => {
         if (event.timestamp) {
           timestamps.push(event.timestamp);
         }
       });
     }
     
     // Find the most recent timestamp
     if (timestamps.length > 0) {
       const dates = timestamps.map(ts => new Date(ts));
       const mostRecent = new Date(Math.max(...dates.map(d => d.getTime())));
       const now = new Date();
       const diffTime = now.getTime() - mostRecent.getTime();
       daysInCurrentStage = Math.floor(diffTime / (1000 * 60 * 60 * 24));
       // Ensure we don't have negative days (in case of clock issues)
       daysInCurrentStage = Math.max(0, daysInCurrentStage);
     }
   } catch (error) {
     // Fallback to a reasonable default if calculation fails
     console.warn('Failed to calculate daysInCurrentStage, using fallback:', error);
     daysInCurrentStage = 3; // Reasonable default for trips in progress
   }
  
  // Determine SLA status based on days in stage
  let slaStatus: "on_track" | "at_risk" | "breached" = "on_track";
  if (daysInCurrentStage > 7) slaStatus = "breached";
  else if (daysInCurrentStage > 4) slaStatus = "at_risk";
  
  // Extract customer name (placeholder - would come from raw input or notes)
  const customerName = extractCustomerName(trip);
  
  // Extract flags based on trip data
  const flags = extractFlags(trip);
  
  return {
    id: trip.id,
    reference: trip.id,
    destination: String(destination),
    tripType: String(tripType),
    partySize: partySize,
    dateWindow: String(dateWindow),
    value: budgetValue,
    priority,
    priorityScore,
    stage,
    stageNumber: getStageNumber(stage),
    assignedTo: trip.assignedTo || undefined,
    assignedToName: trip.assignedToName || undefined,
    submittedAt: trip.createdAt || new Date().toISOString(),
    lastUpdated: trip.updated_at || trip.createdAt || new Date().toISOString(),
    daysInCurrentStage,
    slaStatus,
    customerName,
    flags
  };
}

export async function GET(request: NextRequest) {
  try {
    // Forward request to spine-api with all query parameters
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.toString();
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/trips${query ? `?${query}` : ""}`;

    const response = await fetch(spineApiUrl, {
      method: "GET",
      headers: forwardAuthHeaders(request),
    });

    if (!response.ok) {
      throw new Error(`Spine API returned ${response.status}`);
    }

    const spineApiData = await response.json();
    
    // Transform spine-api trips to frontend inbox format
    // spine-api returns { items: [...], total: N }
    const trips = spineApiData.items || [];
    const total = spineApiData.total || trips.length;
    
    // Transform each trip to match the frontend inbox expectations
    const inboxTrips = trips.map((trip: any) => transformTripToInboxFormat(trip));
    
    // Apply pagination
    const page = parseInt(searchParams.get("page") || "1", 10);
    const limit = parseInt(searchParams.get("limit") || "20", 10);
    const start = (page - 1) * limit;
    const paginatedTrips = inboxTrips.slice(start, start + limit);
    const hasMore = start + limit < inboxTrips.length;
    
    return NextResponse.json({ 
      items: paginatedTrips, 
      total: inboxTrips.length, 
      hasMore 
    });
  } catch (error) {
    console.error("Error fetching inbox from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch inbox" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { tripIds, action, params } = body;

    if (!tripIds || !Array.isArray(tripIds) || !action) {
      return NextResponse.json(
        { error: "tripIds (string[]) and action are required" },
        { status: 400 }
      );
    }

    // For now, we'll simulate the bulk action since spine-api may not have bulk endpoints
    // In a full implementation, we'd make individual API calls or use a bulk endpoint
    return NextResponse.json({
      success: true,
      processed: tripIds.length,
      failed: 0,
    });
  } catch (error) {
    console.error("Error processing bulk action:", error);
    return NextResponse.json(
      { error: "Failed to process bulk action" },
      { status: 500 }
    );
  }
}