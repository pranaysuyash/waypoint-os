import { NextRequest } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";

export async function GET(request: NextRequest) {
  return proxyRequest(request, { backendPath: "api/auth/me" });
}
