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
      detailsLabel: sha
        ? `runtime · ${payload.environment} · ${sha}`
        : `runtime · ${payload.environment}`,
    };
  }, [query.data]);
}
