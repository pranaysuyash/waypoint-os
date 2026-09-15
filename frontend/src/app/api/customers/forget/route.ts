import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";
import { spineUrl } from "@/lib/proxy-core";

/**
 * BFF proxy for the E-D slot 2 purge affordance: forwards a GDPR erase for
 * the traveler's on-file memory entity (durable tombstones + legacy-registry
 * propagation, agency-scoped on the backend). The on-file display surfaces
 * nothing for the entity afterwards.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const customerId = typeof body?.customerId === "string" ? body.customerId : "";
    if (!customerId) {
      return bffJson({ error: "customerId is required" }, 400);
    }

    const spineApiUrl = spineUrl("/api/v1/customers/memory/forget");
    const base = bffFetchOptions(request, "POST");
    const response = await fetch(spineApiUrl, {
      ...base,
      headers: {
        ...base.headers,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ customer_id: customerId }),
      cache: "no-store",
    });

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }
      throw new Error(`Spine API returned ${response.status}`);
    }

    const data = await response.json();
    return bffJson(data);
  } catch (error) {
    console.error("Error proxying memory forget:", error);
    return bffJson({ error: "Failed to forget on-file memory" }, 500);
  }
}
