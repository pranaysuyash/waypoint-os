import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Fetch both summary and pipeline data for better stats
    const [summaryResponse, pipelineResponse] = await Promise.all([
      fetch("http://localhost:8000/analytics/summary", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }),
      fetch("http://localhost:8000/analytics/pipeline", {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }),
    ]);

    if (!summaryResponse.ok) {
      throw new Error(`Spine API summary returned ${summaryResponse.status}`);
    }
    
    if (!pipelineResponse.ok) {
      throw new Error(`Spine API pipeline returned ${pipelineResponse.status}`);
    }

    const spineApiSummary = await summaryResponse.json();
    const spineApiPipeline = await pipelineResponse.json();
    
    // Transform spine-api stats to frontend TripStats format
    const totalInquiries = spineApiSummary.totalInquiries || 0;
    const convertedToBooked = spineApiSummary.convertedToBooked || 0;
    
    // Calculate pending review from pipeline data
    // Sum of all trips in pipeline stages minus those already booked
    const totalInPipeline = spineApiPipeline.reduce(
      (sum, stage) => sum + (stage.tripCount || 0), 
      0
    );
    
    // Pending review: trips in pipeline that haven't been converted yet
    const pendingReview = Math.max(0, totalInPipeline - convertedToBooked);
    
    // Ready to book: estimate based on exit rates from later stages
    // Let's look at strategy and output stages as closest to booking
    const strategyStage = spineApiPipeline.find(stage => stage.stageId === "strategy");
    const outputStage = spineApiPipeline.find(stage => stage.stageId === "output");
    
    const strategyCount = strategyStage?.tripCount || 0;
    const outputCount = outputStage?.tripCount || 0;
    
    // Estimate ready to book as a portion of strategy+output trips
    const readyToBook = Math.floor((strategyCount + outputCount) * 0.4);
    
    // Needs attention: trips that have stalled or have issues
    // We'll estimate based on low exit rates or high avg time in stage
    const safetyStage = spineApiPipeline.find(stage => stage.stageId === "safety");
    const discoveryStage = spineApiPipeline.find(stage => stage.stageId === "discovery");
    
    let needsAttention = 0;
    if (safetyStage && safetyStage.exitRate < 50) {
      needsAttention += Math.floor(safetyStage.tripCount * 0.3);
    }
    if (discoveryStage && discoveryStage.avgTimeInStage > 10) {
      needsAttention += Math.floor(discoveryStage.tripCount * 0.2);
    }
    
    // Ensure we don't exceed pending review
    needsAttention = Math.min(needsAttention, pendingReview);
    
    const frontendStats = {
      active: convertedToBooked,
      pendingReview: pendingReview,
      readyToBook: readyToBook,
      needsAttention: needsAttention
    };
    
    return NextResponse.json(frontendStats);
  } catch (error) {
    console.error("Error fetching stats from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}