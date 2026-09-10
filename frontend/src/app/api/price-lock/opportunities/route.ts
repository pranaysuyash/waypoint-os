import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

/**
 * BFF proxy for price-lock opportunities (I-2 freshness card): forwards the
 * authenticated agency request to the spine backend's price-lock sentinel
 * (72h window audits + rate drops).
 */
export async function GET(request: NextRequest) {
  try {
    const spineApiUrl = spineUrl("/api/v1/price-lock/opportunities");
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
    console.error("Error fetching price-lock opportunities from spine_api:", error);
    return bffJson({ error: "Failed to fetch price-lock opportunities" }, 500);
  }
}
