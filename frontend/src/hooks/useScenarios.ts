import { useQuery } from "@tanstack/react-query";
import { getScenarios, getScenario, type ScenarioListItem, type ScenarioDetail } from "@/lib/api-client";

export function useScenarios() {
  const query = useQuery({
    queryKey: ["scenarios", "list"],
    queryFn: () => getScenarios(),
    staleTime: 30_000,
  });

  return { data: query.data ?? [], isLoading: query.isLoading, error: query.error as Error | null, refetch: query.refetch };
}

export function useScenario(id: string | null) {
  const query = useQuery({
    queryKey: ["scenarios", id],
    queryFn: () => getScenario(id!),
    enabled: !!id,
    staleTime: 30_000,
  });

  return { data: query.data ?? null, isLoading: query.isLoading, error: query.error as Error | null };
}
