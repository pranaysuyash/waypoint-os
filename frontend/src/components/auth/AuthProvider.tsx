"use client";

/**
 * AuthProvider — Root-level authentication lifecycle manager.
 *
 * Responsibilities:
 * 1. Call auth.hydrate() on mount to restore session from httpOnly cookie
 * 2. Expose loading state so UI can wait before rendering protected content
 * 3. Handle auth errors gracefully
 *
 * Usage: Wrap the app in layout.tsx inside the Shell.
 */

import { useEffect } from "react";
import { useAuthStore } from "@/stores/auth";

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const hydrate = useAuthStore((state) => state.hydrate);
  const isLoading = useAuthStore((state) => state.isLoading);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Optional: show a minimal loading state while hydrating
  // This prevents flash of unauthenticated content on refresh
  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
