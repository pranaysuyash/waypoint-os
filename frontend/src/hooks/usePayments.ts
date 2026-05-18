import { useQuery } from "@tanstack/react-query";
import {
  getPaymentsQueue,
  type PaymentQueueParams,
  type PaymentQueueResponse,
} from "@/lib/api-client";

const QK = {
  queue: (params: PaymentQueueParams) => ["payments", "queue", params] as const,
};

const DEFAULT_STALE_TIME = 30_000;

export function usePaymentsQueue(params: PaymentQueueParams) {
  const query = useQuery<PaymentQueueResponse>({
    queryKey: QK.queue(params),
    queryFn: () => getPaymentsQueue(params),
    staleTime: DEFAULT_STALE_TIME,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error as Error | null,
    refetch: query.refetch,
  };
}

