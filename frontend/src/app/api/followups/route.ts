import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.toString();
    const spineApiUrl = spineUrl(`/followups/dashboard${query ? `?${query}` : ""}`);

    const response = await fetch(spineApiUrl, { ...bffFetchOptions(request, "GET"), cache: "no-store" });

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
