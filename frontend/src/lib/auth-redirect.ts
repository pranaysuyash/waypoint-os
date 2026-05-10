const DEFAULT_PROTECTED_REDIRECT = "/overview";

/**
 * Resolve a post-auth redirect target from untrusted query params.
 * Accept only internal absolute paths and block auth-page loops.
 */
export function resolveSafeRedirect(
  candidate: string | null | undefined,
  fallback: string = DEFAULT_PROTECTED_REDIRECT,
): string {
  if (!candidate) return fallback;
  if (!candidate.startsWith("/")) return fallback;
  if (candidate.startsWith("//")) return fallback;

  try {
    const parsed = new URL(candidate, "http://localhost");
    if (parsed.pathname === "/login" || parsed.pathname === "/signup") {
      return fallback;
    }
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}

export const DEFAULT_AUTH_REDIRECT = DEFAULT_PROTECTED_REDIRECT;
