import { NextResponse } from "next/server";
import frontendPackage from "../../../../package.json";

export async function GET() {
  try {
    return NextResponse.json(
      {
        app: "waypoint-frontend",
        version: frontendPackage.version,
        environment: process.env.NODE_ENV,
        gitSha: process.env.NEXT_PUBLIC_GIT_SHA ?? null,
        generatedAt: new Date().toISOString(),
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      }
    );
  } catch (error) {
    console.error("Error fetching frontend version:", error);
    return NextResponse.json(
      { error: "Failed to fetch frontend version" },
      { status: 500 }
    );
  }
}
