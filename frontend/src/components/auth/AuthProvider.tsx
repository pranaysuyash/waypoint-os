"use client";

/**
 * AuthProvider — Root-level authentication lifecycle manager.
 *
 * Responsibilities:
 * 1. Call auth.hydrate() on mount to restore session from httpOnly cookie
 * 2. Block rendering until auth state is resolved
 * 3. Redirect unauthenticated users away from protected pages
 *
 * Usage: Wrap the app in layout.tsx inside the Shell.
 */

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

const PUBLIC_PATHS = ["/login", "/signup", "/logout", "/"];
function isPublic(path: string) {
  return PUBLIC_PATHS.some((p) => path === p || path.startsWith(p + "/"));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const hydrate = useAuthStore((s) => s.hydrate);
  const isLoading = useAuthStore((s) => s.isLoading);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const pathname = usePathname();
  const router = useRouter();
  const needsRedirect = !isLoading && !isAuthenticated && !isPublic(pathname);

  // Hydrate once on mount
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Redirect unauthenticated users away from protected pages.
  useEffect(() => {
    if (!needsRedirect) return;
    const search = typeof window === "undefined" ? "" : window.location.search;
    const redirectTarget = `${pathname}${search}`;
    router.replace(`/login?redirect=${encodeURIComponent(redirectTarget)}`);
  }, [needsRedirect, pathname, router]);

  // Still hydrating — block everything
  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-foreground">Checking your session...</p>
        </div>
      </div>
    );
  }

  if (needsRedirect) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
