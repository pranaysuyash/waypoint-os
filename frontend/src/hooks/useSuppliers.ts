'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  createSupplierSoftHold,
  listSupplierContracts,
  listSupplierHolds,
  uploadSupplierContract,
  type SupplierContractRecord,
  type SupplierContractUploadPayload,
  type SupplierContractUploadResponse,
  type SupplierHoldRecord,
  type SupplierSoftHoldPayload,
  type SupplierSoftHoldResponse,
} from '@/lib/api-client';

export interface UseSupplierLedgerResult {
  contracts: SupplierContractRecord[];
  holds: SupplierHoldRecord[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  uploadContract: (payload: SupplierContractUploadPayload) => Promise<SupplierContractUploadResponse>;
  createSoftHold: (payload: SupplierSoftHoldPayload) => Promise<SupplierSoftHoldResponse>;
}

/**
 * Operator-recorded supplier contracts and 48h soft-holds hook.
 * Calls canonical `/api/v1/supplier/*` endpoints scoped to the active agency.
 */
export function useSupplierLedger(): UseSupplierLedgerResult {
  const [contracts, setContracts] = useState<SupplierContractRecord[]>([]);
  const [holds, setHolds] = useState<SupplierHoldRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [contractsRes, holdsRes] = await Promise.all([
        listSupplierContracts(),
        listSupplierHolds(),
      ]);
      setContracts(contractsRes?.items ?? []);
      setHolds(holdsRes?.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load supplier ledger.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadInitial() {
      try {
        const [contractsRes, holdsRes] = await Promise.all([
          listSupplierContracts(),
          listSupplierHolds(),
        ]);
        if (cancelled) return;
        setContracts(contractsRes?.items ?? []);
        setHolds(holdsRes?.items ?? []);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Unable to load supplier ledger.');
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }
    void loadInitial();
    return () => {
      cancelled = true;
    };
  }, []);

  const uploadContract = useCallback(
    async (payload: SupplierContractUploadPayload) => {
      const result = await uploadSupplierContract(payload);
      await refresh();
      return result;
    },
    [refresh]
  );

  const createSoftHold = useCallback(
    async (payload: SupplierSoftHoldPayload) => {
      const result = await createSupplierSoftHold(payload);
      await refresh();
      return result;
    },
    [refresh]
  );

  return {
    contracts,
    holds,
    isLoading,
    error,
    refresh,
    uploadContract,
    createSoftHold,
  };
}
