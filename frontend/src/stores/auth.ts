/**
 * Auth Store — Zustand store for authentication state.
 *
 * Manages:
 * - User session (user, agency, role)
 * - Authentication status (synced with cookies, not localStorage)
 * - Login/logout actions
 *
 * NOTE: Token storage is cookie-based (httpOnly). Zustand holds in-memory state only.
 * On page load, /api/auth/me is called to rehydrate state from the cookie.
 */

import { create } from "zustand";

export interface AuthUser {
  id: string;
  email: string;
  name?: string;
}

export interface AuthAgency {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
}

export interface AuthMembership {
  role: string;
  isPrimary: boolean;
}

export interface AuthState {
  user: AuthUser | null;
  agency: AuthAgency | null;
  membership: AuthMembership | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  setAuth: (user: AuthUser, agency: AuthAgency, membership: AuthMembership) => void;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  agency: null,
  membership: null,
  isAuthenticated: false,
  isLoading: true,          // start TRUE so AuthProvider blocks children until verified
  error: null,

  setAuth: (user, agency, membership) =>
    set({ user, agency, membership, isAuthenticated: true, error: null }),

  logout: async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    } catch {
      // ignore
    }
    set({ user: null, agency: null, membership: null, isAuthenticated: false });
  },

  hydrate: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch("/api/auth/me", { credentials: "include" });
      if (!response.ok) {
        set({ isAuthenticated: false, isLoading: false });
        return;
      }
      const data = await response.json();
      if (data.ok && data.user) {
        set({
          user: data.user,
          agency: data.agency,
          membership: data.membership,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({ isAuthenticated: false, isLoading: false });
      }
    } catch {
      set({ isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));
