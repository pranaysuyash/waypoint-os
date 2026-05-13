"use client";

/**
 * AuthProvider - Root-level authentication lifecycle manager.
 *
 * Responsibilities:
 * 1. Call auth.hydrate() on mount to restore session from httpOnly cookie
 * 2. Block rendering until auth state is resolved
 * 3. Redirect unauthenticated users away from protected pages
 *
 * Usage: Wrap the app in layout.tsx inside the Shell.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AUTH_UNAUTHORIZED_EVENT, ApiException, api } from "@/lib/api-client";
import { formatAuthRedirectLabel } from "@/lib/auth-redirect";
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
  const { push } = useRouter();
  const needsLogin = !isLoading && !isAuthenticated && !isPublic(pathname);

  type LoginFormState = { email: string; password: string; showPassword: boolean; submitting: boolean; error: string };
  const [loginForm, setLoginForm] = useState<LoginFormState>({ email: "", password: "", showPassword: false, submitting: false, error: "" });
  const { email, password, showPassword, submitting, error } = loginForm;
  const patchLoginForm = (p: Partial<LoginFormState>) => setLoginForm((s) => ({ ...s, ...p }));

  const modalRef = useRef<HTMLDivElement | null>(null);

  const redirectTarget = useMemo(() => {
    if (typeof window === "undefined") return pathname;
    return `${pathname}${window.location.search}`;
  }, [pathname]);
  const redirectLabel = useMemo(() => formatAuthRedirectLabel(redirectTarget), [redirectTarget]);

  // Hydrate once on mount
  useEffect(() => {
    hydrate();
  }, [hydrate]);

  // Keep auth state synchronized when any protected API request returns 401.
  useEffect(() => {
    function handleUnauthorized() {
      hydrate();
    }

    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized);
  }, [hydrate]);

  useEffect(() => {
    if (!needsLogin) return;

    const modalEl = modalRef.current;
    if (!modalEl) return;

    const selectors = [
      "button:not([disabled])",
      "a[href]",
      "input:not([disabled])",
      "select:not([disabled])",
      "textarea:not([disabled])",
      "[tabindex]:not([tabindex='-1'])",
    ].join(",");
    const focusables = Array.from(modalEl.querySelectorAll<HTMLElement>(selectors));
    focusables[0]?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (!modalEl) return;

      if (event.key === "Escape") {
        event.preventDefault();
        push(`/login?redirect=${encodeURIComponent(redirectTarget)}`);
        return;
      }
      if (event.key !== "Tab") return;

      const items = Array.from(modalEl.querySelectorAll<HTMLElement>(selectors));
      if (items.length === 0) return;

      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey) {
        if (!active || active === first || !modalEl.contains(active)) {
          event.preventDefault();
          last.focus();
        }
      } else if (!active || active === last || !modalEl.contains(active)) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [needsLogin, redirectTarget, push]);

  // Still hydrating - block everything
  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-foreground">Checking your session…</p>
        </div>
      </div>
    );
  }

  if (needsLogin) {
    async function handleLogin(e: React.FormEvent) {
      e.preventDefault();
      patchLoginForm({ submitting: true, error: "" });
      try {
        await api.post("/api/auth/login", { email, password });
        await hydrate();
      } catch (err) {
        if (err instanceof ApiException) {
          patchLoginForm({ error: err.message || "Invalid email or password" });
        } else {
          patchLoginForm({ error: "Network error. Please try again." });
        }
      } finally {
        patchLoginForm({ submitting: false });
      }
    }

    return (
      <div className="relative min-h-screen">
        <div aria-hidden className="pointer-events-none opacity-40">{children}</div>
        <div className="fixed inset-0 z-[80] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            ref={modalRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="auth-modal-title"
            className="w-full max-w-[430px] rounded-2xl border border-[#2a3440] bg-[#0d1117] shadow-2xl p-6"
          >
            <h2 id="auth-modal-title" className="text-xl font-semibold text-[#e6edf3]">Sign in required</h2>
            <p className="mt-1.5 text-sm text-[#8b949e]">
              Continue to <span className="text-[#c9d1d9] font-medium">{redirectLabel}</span>
            </p>

            <form className="mt-5 space-y-3.5" onSubmit={handleLogin}>
              {error && (
                <div className="rounded-md border border-red-500/30 bg-red-500/10 text-red-300 text-sm px-3 py-2">
                  {error}
                </div>
              )}
              <div>
                <label className="block text-xs uppercase tracking-[0.08em] text-[#8b949e] mb-1.5" htmlFor="modal-email">
                  Email
                </label>
                <input
                  id="modal-email"
                  type="email"
                  value={email}
                  onChange={(e) => patchLoginForm({ email: e.target.value })}
                  autoComplete="email"
                  required
                  className="w-full rounded-lg bg-[#080a0c] border border-[#1f2630] text-[#e6edf3] px-3 py-2 text-sm outline-none focus:border-[#58a6ff] focus:ring-2 focus:ring-[#58a6ff]/20"
                  placeholder="you@agency.com"
                />
              </div>
              <div>
                <label className="block text-xs uppercase tracking-[0.08em] text-[#8b949e] mb-1.5" htmlFor="modal-password">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="modal-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => patchLoginForm({ password: e.target.value })}
                    autoComplete="current-password"
                    required
                    className="w-full rounded-lg bg-[#080a0c] border border-[#1f2630] text-[#e6edf3] px-3 py-2 pr-16 text-sm outline-none focus:border-[#58a6ff] focus:ring-2 focus:ring-[#58a6ff]/20"
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => patchLoginForm({ showPassword: !showPassword })}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-semibold text-[#58a6ff] hover:text-[#79b8ff]"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-lg bg-gradient-to-r from-[#2563eb] to-[#1d4ed8] text-white text-sm font-semibold py-2.5 disabled:opacity-60"
              >
                {submitting ? "Signing in…" : "Sign in"}
              </button>
            </form>

            <div className="mt-3.5 text-center text-xs text-[#8b949e]">
              <Link href="/reset-password" className="text-[#58a6ff] hover:underline">Reset password</Link>
              <span className="mx-2">·</span>
              <Link href="/forgot-password" className="text-[#58a6ff] hover:underline">Forgot password?</Link>
            </div>
            <div className="mt-2 text-center text-xs">
              <Link
                href={`/login?redirect=${encodeURIComponent(redirectTarget)}`}
                className="text-[#8b949e] hover:text-[#c9d1d9] hover:underline"
              >
                Open full sign-in page
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
