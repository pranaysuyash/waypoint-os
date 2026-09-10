import { cookies } from "next/headers";
import { spineUrl } from "@/lib/proxy-core";
import type { AuthSession } from "@/types/auth-session";

export async function loadServerAuthSession(): Promise<AuthSession | null> {
  try {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("access_token")?.value;
    if (!accessToken) return null;

    const refreshToken = cookieStore.get("refresh_token")?.value;
    const cookieParts = [`access_token=${accessToken}`];
    if (refreshToken) {
      cookieParts.push(`refresh_token=${refreshToken}`);
    }

    // spineUrl() applies the validated backend base from proxy-core.ts.
    const meUrl = spineUrl("/api/auth/me");
    const response = await fetch(meUrl, {
      method: "GET",
      headers: {
        Accept: "application/json",
        Cookie: cookieParts.join("; "),
      },
      cache: "no-store",
    });

    if (!response.ok) return null;

    const data = (await response.json()) as {
      ok?: boolean;
      user?: AuthSession["user"];
      agency?: AuthSession["agency"];
      membership?: AuthSession["membership"];
    };

    if (!data.ok || !data.user || !data.agency || !data.membership) {
      return null;
    }

    return {
      user: data.user,
      agency: data.agency,
      membership: data.membership,
    };
  } catch {
    return null;
  }
}
