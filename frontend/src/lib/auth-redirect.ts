const DEFAULT_PROTECTED_REDIRECT = "/overview";
const ROUTE_LABELS: Record<string, string> = {
  "/audit": "Audit",
  "/inbox": "Lead Inbox",
  "/insights": "Insights",
  "/overview": "Overview",
  "/reviews": "Quote Review",
  "/settings": "Settings",
  "/trips": "Trips in Planning",
  "/workbench": "New Inquiry",
};

const WORKBENCH_TAB_LABELS: Record<string, string> = {
  intake: "New Inquiry",
  safety: "Risk Review",
};

function titleCaseSegment(segment: string): string {
  return segment
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function appendContext(base: string, context: string | null): string {
  if (!context || context === base) return base;
  return `${base} - ${context}`;
}

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

/**
 * Convert a safe redirect target into language an operator can understand.
 * Keep this paired with resolveSafeRedirect so auth surfaces never expose raw
 * query strings such as "workbench?draft=new&tab=safety" as product copy.
 */
export function formatAuthRedirectLabel(
  target: string | null | undefined,
  fallback: string = DEFAULT_PROTECTED_REDIRECT,
): string {
  const safeTarget = resolveSafeRedirect(target, fallback);

  try {
    const parsed = new URL(safeTarget, "http://localhost");
    const [firstSegment] = parsed.pathname.split("/").filter(Boolean);
    const basePath = firstSegment ? `/${firstSegment}` : DEFAULT_PROTECTED_REDIRECT;
    const baseLabel = ROUTE_LABELS[parsed.pathname] ?? ROUTE_LABELS[basePath] ?? titleCaseSegment(firstSegment ?? "overview");

    if (parsed.pathname === "/workbench") {
      const tabLabel = WORKBENCH_TAB_LABELS[parsed.searchParams.get("tab") ?? ""];
      if (parsed.searchParams.get("draft") === "new") {
        return appendContext("New Inquiry", tabLabel);
      }
      return appendContext(baseLabel, tabLabel ?? null);
    }

    if (parsed.pathname === "/settings") {
      const tab = parsed.searchParams.get("tab");
      return appendContext(baseLabel, tab ? titleCaseSegment(tab) : null);
    }

    return baseLabel;
  } catch {
    return ROUTE_LABELS[fallback] ?? "Overview";
  }
}

export const DEFAULT_AUTH_REDIRECT = DEFAULT_PROTECTED_REDIRECT;
