import { useEffect, useState } from "react";

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

const FALLBACK_VERSION_LABEL = "v0.1 · decision engine";
const FALLBACK_DETAILS_LABEL = "runtime · unknown";

function shortSha(sha: string | null): string {
  if (!sha) return "";
  return sha.slice(0, 7);
}

export function useRuntimeVersion(): RuntimeVersionState {
  const [state, setState] = useState<RuntimeVersionState>({
    versionLabel: FALLBACK_VERSION_LABEL,
    detailsLabel: FALLBACK_DETAILS_LABEL,
  });

  useEffect(() => {
    let isMounted = true;

    const run = async () => {
      try {
        const response = await fetch("/api/version", {
          cache: "no-store",
          credentials: "include",
        });
        if (!response.ok) return;

        const payload = (await response.json()) as RuntimeVersionResponse;
        const sha = shortSha(payload.gitSha);
        const details = sha
          ? `runtime · ${payload.environment} · ${sha}`
          : `runtime · ${payload.environment}`;

        if (isMounted) {
          setState({
            versionLabel: `v${payload.version} · decision engine`,
            detailsLabel: details,
          });
        }
      } catch {
        // Keep fallback labels for resilience in local/offline/dev-error states.
      }
    };

    void run();

    return () => {
      isMounted = false;
    };
  }, []);

  return state;
}
