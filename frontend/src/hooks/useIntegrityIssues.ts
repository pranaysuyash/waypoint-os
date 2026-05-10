import { useQuery } from '@tanstack/react-query';
import { getIntegrityIssues } from '@/lib/api-client';
import type { IntegrityIssue } from '@/types/spine';

const QK = {
  integrityIssues: () => ['integrity', 'issues'] as const,
};

const DEFAULT_STALE_TIME = 30_000;

export function useIntegrityIssues() {
  const query = useQuery({
    queryKey: QK.integrityIssues(),
    queryFn: () => getIntegrityIssues(),
    staleTime: DEFAULT_STALE_TIME,
  });
  const hasError = Boolean(query.error);

  return {
    data: (hasError ? [] : (query.data?.items ?? [])) as IntegrityIssue[],
    total: hasError ? 0 : (query.data?.total ?? 0),
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
}
