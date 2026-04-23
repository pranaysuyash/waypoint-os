/**
 * Auth Store — Zustand store for authentication state.
 *
 * Manages:
 * - User session (user, agency, role)
 * - JWT token (persisted in localStorage)
 * - Authentication status
 * - Login/logout actions
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
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (token: string, user: AuthUser, agency: AuthAgency, membership: AuthMembership) => void;
  logout: () => void;
  setToken: (token: string) => void;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

// ============================================================================
// STORAGE HELPERS
// ============================================================================

const TOKEN_KEY = "access_token";

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function setStoredToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// ============================================================================
// STORE
// ============================================================================

export const useAuthStore = create<AuthState>((set) => ({
  // Initial state — check localStorage for existing token
  user: null,
  agency: null,
  membership: null,
  token: getStoredToken(),
  isAuthenticated: !!getStoredToken(),
  isLoading: false,
  error: null,

  login: (token, user, agency, membership) => {
    setStoredToken(token);
    set({
      token,
      user,
      agency,
      membership,
      isAuthenticated: true,
      error: null,
    });
  },

  logout: () => {
    setStoredToken(null);
    set({
      token: null,
      user: null,
      agency: null,
      membership: null,
      isAuthenticated: false,
      error: null,
    });
  },

  setToken: (token) => {
    setStoredToken(token);
    set({ token, isAuthenticated: !!token });
  },

  clearError: () => set({ error: null }),

  setLoading: (loading) => set({ isLoading: loading }),
}));
