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
  supplier_options: SupplierOption[];
  optimal_supplier: string;
  potential_margin_gain: number;
}

interface YieldArbitragePanelProps {
  tripId?: string;
}

export function YieldArbitragePanel({ tripId = 'trip_demo123' }: YieldArbitragePanelProps) {
  const [data, setData] = useState<YieldArbitrageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [swapping, setSwapping] = useState<string | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);

  useEffect(() => {
    async function loadOpportunities() {
      try {
        const res = await api.get<YieldArbitrageData>(`/api/v1/yield/arbitrage/${tripId}`);
        setData(res);
        if (res.optimal_supplier) {
          setSelectedSupplier(res.optimal_supplier);
        }
      } catch (err) {
        console.warn('Failed to load yield arbitrage data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadOpportunities();
  }, [tripId]);

  const handleSwap = async (supplierName: string) => {
    setSwapping(supplierName);
    try {
      await api.post('/api/v1/yield/swap-supplier', {
        trip_id: tripId,
        supplier_name: supplierName,
      });
      setSelectedSupplier(supplierName);
    } catch (err) {
      alert(`Supplier swap failed: ${(err as Error).message}`);
    } finally {
      setSwapping(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-xl text-center text-xs text-slate-400">
        Scanning supplier GDS &amp; bedbank rates for yield arbitrage...
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

      <div className="space-y-2.5">
        {data.supplier_options.map((opt, idx) => {
          const isSelected = selectedSupplier === opt.supplier_name;
          const isOptimal = data.optimal_supplier === opt.supplier_name;

          return (
            <div
              key={idx}
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
