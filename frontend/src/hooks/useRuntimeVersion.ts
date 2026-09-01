import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

interface RuntimeVersionResponse {
  app: string;
  version: string;
  environment: string;
  gitSha: string | null;
  generatedAt: string;
}

interface RuntimeVersionState {
  versionLabel: string;
  detailsLabel: string;
}

const FALLBACK_VERSION_LABEL = "Operations live";
const FALLBACK_DETAILS_LABEL = "";

function shortSha(sha: string | null): string {
  if (!sha) return "";
  return sha.slice(0, 7);
}

/**
 * Ops metadata (environment name + git SHA) is engineering chrome, not
 * end-user information (DEMO-07). It is hidden by default and only rendered
 * when NEXT_PUBLIC_SHOW_RUNTIME_META is set to a truthy value ('1' or 'true')
 * in the local/dev environment. The "Operations live" indicator in the Shell
 * status footer stays visible for everyone. Read inline (not module-level)
 * so test env stubbing takes effect per call.
 */
function shouldShowRuntimeMeta(): boolean {
  const flag = process.env.NEXT_PUBLIC_SHOW_RUNTIME_META;
  return flag === "1" || flag === "true";
}

export function useRuntimeVersion(): RuntimeVersionState {
  const query = useQuery({
    queryKey: ["runtime-version"],
    queryFn: async (): Promise<RuntimeVersionResponse | null> => {
      try {
        const response = await fetch("/api/version", {
          cache: "no-store",
          credentials: "include",
        });
        if (!response.ok) return null;
        return (await response.json()) as RuntimeVersionResponse;
      } catch {
        return null;
      }
    },
    staleTime: 60_000,
    gcTime: 5 * 60_000,
    retry: false,
    refetchOnWindowFocus: false,
  });

  return useMemo(() => {
    const payload = query.data;
    if (!payload) {
      return {
        versionLabel: FALLBACK_VERSION_LABEL,
        detailsLabel: FALLBACK_DETAILS_LABEL,
      };
    }

    const sha = shortSha(payload.gitSha);
    return {
      versionLabel: payload.version
        ? `v${payload.version}`
        : FALLBACK_VERSION_LABEL,
      detailsLabel: shouldShowRuntimeMeta()
        ? sha
          ? `runtime · ${payload.environment} · ${sha}`
          : `runtime · ${payload.environment}`
        : FALLBACK_DETAILS_LABEL,
    };
  }, [query.data]);
}
