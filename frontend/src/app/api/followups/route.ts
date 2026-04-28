import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.toString();
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/followups/dashboard${query ? `?${query}` : ""}`;

    const response = await fetch(spineApiUrl, bffFetchOptions(request, "GET"));

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return bffJson(data);
  } catch (error) {
    console.error("Error fetching followups dashboard from spine_api:", error);
    return bffJson({ error: "Failed to fetch followups" }, 500);
  }
}
