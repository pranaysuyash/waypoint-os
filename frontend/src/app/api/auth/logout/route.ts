import { NextRequest } from "next/server";
import { proxyRequest } from "@/lib/proxy-core";

export async function POST(request: NextRequest) {
  const response = await proxyRequest(request, {
    backendPath: "api/auth/logout",
  });

  const isProd = process.env.NODE_ENV === "production";

  // Clear both auth cookies on the frontend domain
  response.cookies.set("access_token", "", {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  response.cookies.set("refresh_token", "", {
    httpOnly: true,
    secure: isProd,
    sameSite: "lax",
    path: "/api/auth",
    maxAge: 0,
  });

  return response;
}
