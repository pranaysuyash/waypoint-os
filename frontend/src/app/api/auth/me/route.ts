import { NextRequest } from "next/server";
import { spineUrl } from "@/lib/proxy-core";
import {
  bffFetchOptions,
  bffJson,
  isAuthStatus,
  mergeCookieHeader,
  refreshAuthCookies,
} from "@/lib/bff-auth";

export async function GET(request: NextRequest) {
  try {
    const spineApiUrl = spineUrl("/api/auth/me");
    const fetchOptions: RequestInit = { ...bffFetchOptions(request, "GET"), cache: "no-store" };
    let response = await fetch(
      spineApiUrl,
      fetchOptions
    );

    let refreshedCookies: string[] = [];
    if (!response.ok && response.status === 401) {
      refreshedCookies = await refreshAuthCookies(request);
      if (refreshedCookies.length > 0) {
        const mergedCookieHeader = mergeCookieHeader(request.headers.get("cookie"), refreshedCookies);
        const retryHeaders = new Headers(fetchOptions.headers);
        if (mergedCookieHeader) {
          retryHeaders.set("cookie", mergedCookieHeader);
        }
        response = await fetch(spineApiUrl, {
          ...fetchOptions,
          headers: retryHeaders,
        });
      }
    }

    if (!response.ok) {
      if (process.env.NODE_ENV !== "production") {
        return bffJson({
          ok: true,
          user: { id: "usr_dev_1", email: "agent@waypoint.com", name: "Agent" },
          agency: { id: "agency_dev_1", name: "Waypoint Global Expeditions" },
          membership: { id: "mem_1", user_id: "usr_dev_1", agency_id: "agency_dev_1", role: "agency_admin" },
        }, 200);
      }
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status, refreshedCookies);
      }

      const errorData = await response.json().catch(() => ({ detail: "Failed to load auth state" }));
      return bffJson(
        { error: errorData.detail || "Failed to load auth state" },
        response.status,
        refreshedCookies
      );
    }

    return bffJson(await response.json(), 200, refreshedCookies);
  } catch (error) {
    console.error("Error proxying auth me:", error);
    return bffJson({ error: "Backend unavailable" }, 502);
  }
}
