'use client';

import React, { useState } from 'react';
import { DollarSign, CreditCard, Calendar } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: this panel is a local arithmetic and workflow preview.
 * It never calls a settlement/VCC issuance endpoint, creates card-like
 * identifiers, or represents payment, authorization, or supplier effects.
 */

type FinSubTab = 'fx_buffer' | 'vcc' | 'schedules';

export default function FinancialSettlementPanel() {
  const [activeTab, setActiveTab] = useState<FinSubTab>('fx_buffer');
  const [vccAmount, setVccAmount] = useState('4500');
  const [vccPreviewAmount, setVccPreviewAmount] = useState<number | null>(null);
  const [vccPreviewError, setVccPreviewError] = useState<string | null>(null);

  const handlePreviewVCC = () => {
    const amount = Number.parseFloat(vccAmount);
    if (!Number.isFinite(amount) || amount <= 0) {
      setVccPreviewAmount(null);
      setVccPreviewError('Enter a positive amount to calculate a local payment-instrument preview.');
      return;
    }

    setVccPreviewError(null);
    setVccPreviewAmount(amount);
  };

  return (
    <div className="space-y-6">
      <div
        data-testid="financial-settlement-preview-notice"
        role="note"
        className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-5 text-amber-100"
      >
        <strong>Local financial preview:</strong> calculations and timing examples below use sample inputs. No FX quote is live, no money is captured, no card is created, and no supplier or payment provider is contacted.
      </div>
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          type="button"
          aria-pressed={activeTab === 'fx_buffer'}
          onClick={() => setActiveTab('fx_buffer')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'fx_buffer' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <DollarSign className="h-3.5 w-3.5" />
          FX Cushion Calculation (Preview)
        </button>
        <button
          type="button"
          aria-pressed={activeTab === 'vcc'}
          onClick={() => setActiveTab('vcc')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'vcc' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <CreditCard className="h-3.5 w-3.5" />
          VCC Design Preview
        </button>
        <button
          type="button"
          aria-pressed={activeTab === 'schedules'}
          onClick={() => setActiveTab('schedules')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'schedules' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <Calendar className="h-3.5 w-3.5" />
          Payment Timing Preview
        </button>
      </div>

      {activeTab === 'fx_buffer' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-emerald-500" />
              Illustrative FX Cushion Calculation (2.0% Buffer + Gateway Assumption)
            </h4>
            <div className="flex items-center gap-2 shrink-0">
              <SimulatedBadge label="Sample data" />
              <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 px-2 py-0.5 rounded">ARITHMETIC PREVIEW · NOT A QUOTE</span>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground text-[10px] block">SAMPLE BASE COST</span>
              <span className="font-mono font-bold text-foreground text-sm">$1,000.00 USD</span>
              <span className="text-[10px] text-muted-foreground block mt-1">Reference assumption: €0.9200</span>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground text-[10px] block">BUFFERED CALCULATION (2%)</span>
              <span className="font-mono font-bold text-emerald-500 text-sm">€938.40 EUR</span>
              <span className="text-[10px] text-emerald-600 block mt-1">+€18.40 illustrative cushion</span>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground text-[10px] block">ILLUSTRATIVE GATEWAY FEE</span>
              <span className="font-mono font-bold text-amber-500 text-sm">€27.51 EUR</span>
              <span className="text-[10px] text-muted-foreground block mt-1">Assumption: 2.9% + €0.30</span>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground text-[10px] block">NET CALCULATED VALUE</span>
              <span className="font-mono font-bold text-foreground text-sm">€910.89 EUR</span>
              <span className="text-[10px] text-blue-500 block mt-1">No payment captured</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'vcc' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-primary" />
              VCC Design Preview (No Card Created)
            </h4>
            <SimulatedBadge label="Simulated" />
          </div>
          <p className="text-xs text-muted-foreground">
            This screen only previews an amount and currency locally. It does not call an issuance endpoint, authorize funds, create card credentials, or contact a supplier/payment provider.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              aria-label="Sample VCC amount in EUR"
              value={vccAmount}
              onChange={(e) => setVccAmount(e.target.value)}
              className="p-2 text-xs font-mono rounded border border-border bg-background text-foreground w-40"
              placeholder="Amount (EUR)"
            />
            <button
              type="button"
              onClick={handlePreviewVCC}
              className="px-3 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
            >
              Preview Amount (No Card)
            </button>
          </div>

          {vccPreviewError && (
            <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
              {vccPreviewError}
            </p>
          )}

          {vccPreviewAmount !== null && (
            <div data-testid="vcc-preview-result" className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 space-y-2">
              <div className="flex items-center justify-between text-xs gap-2">
                <span className="font-semibold text-amber-200">Local amount preview</span>
                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 font-mono text-[10px] font-bold border border-amber-500/30">NO CARD CREATED</span>
              </div>
              <p className="font-mono text-lg tracking-widest text-foreground font-bold">{vccPreviewAmount.toFixed(2)} EUR</p>
              <div className="text-xs text-muted-foreground pt-1">
                Payment authorization: <strong className="text-foreground">not attempted</strong> · Provider reference: <strong className="text-foreground">none</strong>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'schedules' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Calendar className="h-4 w-4 text-blue-500" />
              Illustrative Payment Timing (20% Deposit / 80% Balance)
            </h4>
            <SimulatedBadge label="Sample data" />
          </div>
          <p className="text-xs leading-5 text-muted-foreground">
            Example timing only. No invoice, payment schedule, authorization, or charge is created by this preview.
          </p>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
              <div className="flex items-center justify-between font-semibold">
                <span>1. Initial Booking Deposit (20%)</span>
                <span className="font-mono text-emerald-600">$1,000.00 USD</span>
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">Example timing; no deposit scheduled</p>
            </div>
            <div className="p-3 rounded-lg border border-blue-500/20 bg-blue-500/5">
              <div className="flex items-center justify-between font-semibold">
                <span>2. Final Balance Payment (80%)</span>
                <span className="font-mono text-blue-600">$4,000.00 USD</span>
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">Example timing; no balance scheduled</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
