import { NextRequest } from "next/server";
import {
  bffFetchOptions,
  bffJson,
  isAuthStatus,
  mergeCookieHeader,
  refreshAuthCookies,
} from "@/lib/bff-auth";

export async function GET(request: NextRequest) {
  try {
    const spineApiUrl = `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/auth/me`;
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
