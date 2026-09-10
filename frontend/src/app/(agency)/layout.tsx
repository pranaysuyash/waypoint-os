import type { Metadata } from "next";
import { cookies } from "next/headers";
import { spineUrl } from "@/lib/proxy-core";
import { AuthProvider } from '@/components/auth/AuthProvider';
import { Providers } from '@/components/providers';
import { Shell } from '@/components/layouts/Shell';
import { ToastContainer } from '@/components/ui/toast';
import type { AuthSession } from "@/types/auth-session";

export const metadata: Metadata = {
  title: "Waypoint OS — Agency Workspace",
  description:
    "Manage trips, inbox, reviews, and team performance from your agency workspace.",
};

export default async function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("access_token")?.value;
  const refreshToken = cookieStore.get("refresh_token")?.value;
  let initialSession: AuthSession | null = null;

  if (accessToken) {
    const cookieParts = [`access_token=${accessToken}`];
    if (refreshToken) {
      cookieParts.push(`refresh_token=${refreshToken}`);
    }

    try {
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

      if (response.ok) {
        const data = await response.json();
        if (data?.ok && data.user && data.agency && data.membership) {
          initialSession = {
            user: data.user,
            agency: data.agency,
            membership: data.membership,
          };
        }
      }
    } catch {
      initialSession = null;
    }
  }

  if (!initialSession && process.env.NODE_ENV !== "production") {
    initialSession = {
      user: { id: "usr_dev_1", email: "agent@waypoint.com", name: "Agent Dev" },
      agency: { id: "agency_dev_1", name: "Waypoint Global Expeditions", slug: "waypoint-global" },
      membership: { role: "agency_admin", isPrimary: true },
    };
  }

  return (
    <Providers>
      <AuthProvider initialSession={initialSession}>
        <Shell>{children}</Shell>
        <ToastContainer />
      </AuthProvider>
    </Providers>
  );
}
