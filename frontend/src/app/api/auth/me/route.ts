import { NextRequest } from "next/server";
import { bffFetchOptions, bffJson, isAuthStatus } from "@/lib/bff-auth";

export async function GET(request: NextRequest) {
  try {
    const response = await fetch(
      `${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/auth/me`,
      { ...bffFetchOptions(request, "GET"), cache: "no-store" }
    );

    if (!response.ok) {
      if (isAuthStatus(response.status)) {
        return bffJson({ error: "Not authenticated" }, response.status);
      }

      const errorData = await response.json().catch(() => ({ detail: "Failed to load auth state" }));
      return bffJson(
        { error: errorData.detail || "Failed to load auth state" },
        response.status,
      );
    }

    return bffJson(await response.json());
  } catch (error) {
    console.error("Error proxying auth me:", error);
    return bffJson({ error: "Backend unavailable" }, 502);
  }
}
