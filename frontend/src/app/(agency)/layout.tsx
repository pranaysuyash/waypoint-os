import type { Metadata } from "next";
import { cookies } from "next/headers";
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
      const response = await fetch(`${process.env.SPINE_API_URL || "http://127.0.0.1:8000"}/api/auth/me`, {
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

  return (
    <Providers>
      <AuthProvider initialSession={initialSession}>
        <Shell>{children}</Shell>
        <ToastContainer />
      </AuthProvider>
    </Providers>
  );
}
