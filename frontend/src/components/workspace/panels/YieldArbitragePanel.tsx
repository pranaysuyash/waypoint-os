'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, ArrowUpRight, DollarSign, Award, CheckCircle } from 'lucide-react';
import { api } from '@/lib/api-client';

interface SupplierOption {
  supplier_name: string;
  supplier_type: string;
  base_cost: number;
  commission_pct: number;
  net_margin: number;
  bonus_override_eligible: boolean;
  suitability_score: number;
}

interface YieldArbitrageData {
  ok: boolean;
  trip_id: string;
  data_sufficient: boolean;
  supplier_options: SupplierOption[];
  optimal_supplier: string;
  potential_margin_gain: number;
}

interface YieldArbitragePanelProps {
  tripId?: string;
}

export function YieldArbitragePanel({ tripId }: YieldArbitragePanelProps) {
  const [data, setData] = useState<YieldArbitrageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [swapping, setSwapping] = useState<string | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tripId) return;

    async function loadOpportunities() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<YieldArbitrageData>(`/api/v1/yield/arbitrage/${tripId}`);
        setData(res);
        if (res.optimal_supplier) {
          setSelectedSupplier(res.optimal_supplier);
        }
      } catch (err) {
        console.warn('Failed to load yield arbitrage data:', err);
        setData(null);
        setError(err instanceof Error ? err.message : 'Supplier yield data is unavailable.');
      } finally {
        setLoading(false);
      }
    }
    loadOpportunities();
  }, [tripId]);

  const handleSwap = async (supplierName: string) => {
    if (!tripId) return;
    setSwapping(supplierName);
    setError(null);
    try {
      await api.post('/api/v1/yield/swap-supplier', {
        trip_id: tripId,
        supplier_name: supplierName,
      });
      setSelectedSupplier(supplierName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Supplier swap failed.');
    } finally {
      setSwapping(null);
    }
  };

  if (!tripId) {
    return (
      <div
        className="p-6 bg-slate-900/60 border border-amber-500/30 rounded-xl text-center text-xs text-amber-200"
        role="status"
      >
        Select a trip before reviewing supplier yield.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl text-center text-xs text-slate-400">
        Loading agency supplier contracts for yield review...
      </div>
    );
  }

  if (error && !data) {
    return (
      <div
        className="p-6 bg-slate-900/60 border border-amber-500/30 rounded-xl text-center text-xs text-amber-200"
        role="status"
      >
        {error}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100">Yield &amp; Commission Arbitrage</h3>
            <p className="text-[11px] text-slate-400">Compare wholesale rate contracts &amp; net margins</p>
          </div>
        </div>

        {data.potential_margin_gain > 0 && (
          <div className="text-right">
            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1 justify-end">
              <ArrowUpRight className="w-3.5 h-3.5" />
              +${data.potential_margin_gain} Margin Gain
            </span>
            <span className="text-[10px] text-slate-500 block">vs lowest margin supplier</span>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-200" role="alert">
          {error}
        </div>
      )}

      {!data.data_sufficient && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-200" role="status">
          No supplier contracts are uploaded for this agency. Upload a contract before comparing margins.
        </div>
      )}

      <div className="space-y-2.5">
        {data.supplier_options.map((opt) => {
          const isSelected = selectedSupplier === opt.supplier_name;
          const isOptimal = data.optimal_supplier === opt.supplier_name;

          return (
            <div
              key={opt.supplier_name}
              className={`p-3.5 rounded-lg border transition-all ${
                isSelected
                  ? 'bg-slate-800/80 border-emerald-500/40 shadow-sm'
                  : 'bg-slate-950/40 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-100">{opt.supplier_name}</span>
                  {isOptimal && (
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
                      Highest Margin
                    </span>
                  )}
                </div>

                <span className="text-xs font-bold text-slate-200">${opt.base_cost.toLocaleString()}</span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center gap-3">
                  <span>Commission: <strong className="text-slate-200">{opt.commission_pct}%</strong></span>
                  <span>Net Profit: <strong className="text-emerald-400">${opt.net_margin}</strong></span>
                  <span>Suitability: <strong className="text-indigo-400">{opt.suitability_score}%</strong></span>
                </div>

                {isSelected ? (
                  <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                    <CheckCircle className="w-3.5 h-3.5" /> Selected
                  </span>
                ) : (
                  <button
                    onClick={() => handleSwap(opt.supplier_name)}
                    disabled={swapping === opt.supplier_name}
                    className="px-2.5 py-1 rounded bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-[10px] font-semibold transition-colors cursor-pointer disabled:opacity-50"
                  >
                    {swapping === opt.supplier_name ? 'Swapping...' : 'Swap Supplier'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
