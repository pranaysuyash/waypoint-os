'use client';

import React, { useEffect, useState } from 'react';
import { TrendingUp, RefreshCw, CheckCircle2 } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';
import { api } from '@/lib/api-client';

/**
 * N-04 contract repair: this panel uses the canonical authenticated yield
 * routes. It does not fabricate a booking, supplier quote, or reticket result
 * when the API is unavailable or no agency contract is uploaded.
 */

interface SupplierOption {
  supplier_name: string;
  supplier_type: string;
  base_cost: number;
  commission_pct: number;
  net_margin: number;
  bonus_override_eligible: boolean;
  suitability_score: number;
}

interface YieldArbitrageResponse {
  ok: boolean;
  trip_id: string;
  data_sufficient: boolean;
  supplier_options: SupplierOption[];
  optimal_supplier: string;
  potential_margin_gain: number;
  generated_at: string;
  _meta?: { reality_tier?: string; missing_for_upgrade?: string[] };
}

interface SupplierSwapResponse {
  ok: boolean;
  trip_id: string;
  selected_supplier: string;
  message?: string;
}

interface YieldArbitragePanelProps {
  tripId?: string | null;
}

export default function YieldArbitragePanel({ tripId }: YieldArbitragePanelProps) {
  const [data, setData] = useState<YieldArbitrageResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [swapping, setSwapping] = useState<string | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadYield() {
      if (!tripId) {
        setData(null);
        setError(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      setSuccess(null);
      try {
        const response = await api.get<YieldArbitrageResponse>(
          `/api/v1/yield/arbitrage/${encodeURIComponent(tripId)}`,
        );
        if (cancelled) return;
        setData(response);
        setSelectedSupplier(
          response.optimal_supplier !== 'None (No Contracts Uploaded)'
            ? response.optimal_supplier
            : null,
        );
      } catch (err) {
        if (cancelled) return;
        setData(null);
        setError(err instanceof Error ? err.message : 'Yield data is unavailable.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadYield();
    return () => {
      cancelled = true;
    };
  }, [tripId]);

  const handleSwap = async (supplierName: string) => {
    if (!tripId) return;
    setSwapping(supplierName);
    setError(null);
    setSuccess(null);
    try {
      const response = await api.post<SupplierSwapResponse>('/api/v1/yield/swap-supplier', {
        trip_id: tripId,
        supplier_name: supplierName,
      });
      setSelectedSupplier(response.selected_supplier);
      setSuccess(response.message ?? `Supplier selection saved for ${tripId}.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Supplier selection failed.');
    } finally {
      setSwapping(null);
    }
  };

  if (!tripId) {
    return (
      <div className="p-4 rounded-xl border border-border bg-card text-xs text-muted-foreground" role="status">
        Select a trip to inspect agency-scoped yield data. No sample booking or supplier rate is shown without a trip context.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 rounded-xl border border-border bg-card text-xs text-muted-foreground" role="status">
        Loading yield data for <span className="font-mono">{tripId}</span>…
      </div>
    );
  }

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-emerald-500" aria-hidden="true" />
            Yield &amp; Commission Arbitrage
          </h4>
          <p className="text-[11px] text-muted-foreground mt-1">
            Agency-scoped supplier comparison for <span className="font-mono">{tripId}</span>
          </p>
        </div>
        <SimulatedBadge label="Data-dependent" />
      </div>

      {error && (
        <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 text-xs" role="alert">
          Yield data unavailable: {error}
        </div>
      )}

      {success && (
        <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold flex items-center gap-2" role="status">
          <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
          {success}
        </div>
      )}

      {!error && data && !data.data_sufficient && (
        <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs" role="status">
          No uploaded supplier contracts are available for this agency. Yield comparison is not claimable until live contract data exists.
        </div>
      )}

      {data && data.data_sufficient && (
        <>
          {data.potential_margin_gain > 0 && (
            <div className="text-xs font-semibold text-emerald-500">
              Potential margin difference: ${data.potential_margin_gain.toLocaleString()}
            </div>
          )}
          <div className="space-y-2.5">
            {data.supplier_options.map((option) => {
              const isSelected = selectedSupplier === option.supplier_name;
              const isOptimal = data.optimal_supplier === option.supplier_name;
              return (
                <div key={option.supplier_name} className="p-3.5 rounded-lg border border-border bg-background space-y-2 text-xs">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-bold text-foreground">{option.supplier_name}</span>
                    {isOptimal && <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-mono">Highest margin</span>}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-[11px]">
                    <span className="text-muted-foreground">Cost <strong className="text-foreground">${option.base_cost.toLocaleString()}</strong></span>
                    <span className="text-muted-foreground">Commission <strong className="text-foreground">{option.commission_pct}%</strong></span>
                    <span className="text-muted-foreground">Net margin <strong className="text-emerald-500">${option.net_margin.toLocaleString()}</strong></span>
                  </div>
                  {isSelected ? (
                    <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-500">
                      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> Selected
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => void handleSwap(option.supplier_name)}
                      disabled={swapping !== null}
                      className="w-full py-1.5 px-2 bg-primary text-primary-foreground rounded text-xs font-semibold hover:bg-primary/90 flex items-center justify-center gap-1 disabled:opacity-50"
                    >
                      <RefreshCw className="h-3 w-3" aria-hidden="true" />
                      {swapping === option.supplier_name ? 'Saving…' : 'Select supplier'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
