import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

export interface AnalyticsPipelineStage {
  label: string;
  status: "complete" | "current" | "pending";
  timestamp?: string;
}

export interface AnalyticsSummary {
  total: number;
  byStatus: Record<string, number>;
  byType: Record<string, number>;
  recent: Array<{
    id: string;
    title: string;
    status: string;
    date: string;
  }>;
}

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/dashboard/stats`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`Spine API dashboard stats returned ${response.status}`);
    }

    const raw = await response.json();

    const pipeline: AnalyticsPipelineStage[] = Array.isArray(raw.pipeline)
      ? raw.pipeline.map((stage: unknown) => {
          const s = stage as Record<string, unknown>;
          return {
            label: typeof s.label === "string" ? s.label : "Stage",
            status: ["complete", "current", "pending"].includes(s.status as string)
              ? (s.status as "complete" | "current" | "pending")
              : "pending",
            timestamp: typeof s.timestamp === "string" ? s.timestamp : undefined,
          };
        })
      : [];

    const summary: AnalyticsSummary = {
      total: typeof raw.total === "number" ? raw.total : 0,
      byStatus:
        typeof raw.byStatus === "object" && raw.byStatus !== null
          ? (raw.byStatus as Record<string, number>)
          : {},
      byType:
        typeof raw.byType === "object" && raw.byType !== null
          ? (raw.byType as Record<string, number>)
          : {},
      recent: Array.isArray(raw.recent)
        ? raw.recent.map((item: unknown) => {
            const r = item as Record<string, unknown>;
            return {
              id: typeof r.id === "string" ? r.id : "",
              title: typeof r.title === "string" ? r.title : "Untitled",
              status: typeof r.status === "string" ? r.status : "unknown",
              date: typeof r.date === "string" ? r.date : new Date().toISOString(),
            };
          })
        : [],
    };

    return NextResponse.json({ pipeline, summary });
  } catch (error) {
    console.error("Error fetching stats from spine_api:", error);
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
