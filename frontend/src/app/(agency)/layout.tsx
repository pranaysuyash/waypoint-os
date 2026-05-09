import type { Metadata } from "next";
import { AuthProvider } from '@/components/auth/AuthProvider';
import { Providers } from '@/components/providers';
import { Shell } from '@/components/layouts/Shell';
import { ToastContainer } from '@/components/ui/toast';

export const metadata: Metadata = {
  title: "Waypoint OS — Agency Workspace",
  description:
    "Manage trips, inbox, reviews, and team performance from your agency workspace.",
};

export default function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Providers>
      <AuthProvider>
        <Shell>{children}</Shell>
        <ToastContainer />
      </AuthProvider>
    </Providers>
  );
}
