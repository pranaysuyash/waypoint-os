import { useQuery } from '@tanstack/react-query';
import {
  getIntegrations,
  type Integration,
  type IntegrationListResponse,
} from '@/lib/api-client';

const INTEGRATIONS_QUERY_KEY = ['agency', 'integrations'] as const;
const INTEGRATIONS_STALE_TIME_MS = 60_000;

export type { Integration, IntegrationListResponse };

export function useIntegrations() {
  const query = useQuery({
    queryKey: INTEGRATIONS_QUERY_KEY,
    queryFn: getIntegrations,
    staleTime: INTEGRATIONS_STALE_TIME_MS,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    refetch: async () => {
      await query.refetch();
    },
  };
}
