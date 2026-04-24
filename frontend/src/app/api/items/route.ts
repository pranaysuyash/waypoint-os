import { NextRequest, NextResponse } from "next/server";
import { forwardAuthHeaders } from "@/lib/proxy-utils";

export async function GET(request: NextRequest) {
  try {
    const spineApiUrl = process.env.SPINE_API_URL || "http://127.0.0.1:8000";
    const response = await fetch(`${spineApiUrl}/items`);

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ items: [], total: 0 });
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Spine API returned ${response.status}`);
    }

    const data = await response.json();
    const nextResponse = NextResponse.json(data);
    nextResponse.headers.set("Cache-Control", "public, max-age=60, s-maxage=60");
    return nextResponse;
  } catch (error) {
    console.error("Error fetching items from spine-api:", error);
    return NextResponse.json(
      { error: "Failed to fetch items" },
      { status: 500 }
    );
  }
}
