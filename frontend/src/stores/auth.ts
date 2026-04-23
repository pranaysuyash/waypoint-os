/**
 * Auth Store — Zustand store for authentication state.
 *
 * Manages:
 * - User session (user, agency, role)
 * - Authentication status (synced with cookies, not localStorage)
 * - Login/logout actions
 *
 * NOTE: Token storage is now cookie-based (httpOnly) for security.
 * Zustand store holds in-memory state only; persistence is via cookies.
 * On page load, /api/auth/me is called to rehydrate state from the cookie.
 */

import { create } from "zustand";

// ============================================================================
// TYPES
// ============================================================================

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
  token: string | null; // In-memory only, synced from cookie via /me endpoint
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (token: string, user: AuthUser, agency: AuthAgency, membership: AuthMembership) => void;
  logout: () => void;
  hydrate: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

// ============================================================================
// STORE
// ============================================================================

export const useAuthStore = create<AuthState>((set, get) => ({
  // Initial state — not reading from localStorage anymore (cookies are httpOnly)
  user: null,
  agency: null,
  membership: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: (token, user, agency, membership) => {
    set({
      token,
      user,
      agency,
      membership,
      isAuthenticated: true,
      error: null,
    });
  },

  logout: async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors — cookies will be cleared by the route
    }
    set({
      token: null,
      user: null,
      agency: null,
      membership: null,
      isAuthenticated: false,
      error: null,
    });
  },

  hydrate: async () => {
    // Rehydrate auth state from the httpOnly cookie via /api/auth/me
    // This is called on app startup to check if user has a valid session
    try {
      set({ isLoading: true, error: null });
      const response = await fetch('/api/auth/me');
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
    } catch (err) {
      set({ isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),

  setLoading: (loading) => set({ isLoading: loading }),
}));
