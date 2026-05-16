'use client';

import { useState } from 'react';
import type { PaymentTracking, PaymentStatus, RefundStatus } from '@/lib/api-client';
import { updatePaymentTracking } from '@/lib/api-client';

function formatLabel(value: string): string {
  return value.replaceAll('_', ' ');
}

function formatMoney(amount?: number | null, currency = 'INR'): string {
  if (amount == null || Number.isNaN(amount)) return '-';
  return `${currency} ${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
}

function daysUntil(dateStr: string): number {
  const due = new Date(dateStr + 'T00:00:00');
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / 86400000);
}

interface DueBadgeProps {
  finalPaymentDue: string;
}

function DueBadge({ finalPaymentDue }: DueBadgeProps) {
  const days = daysUntil(finalPaymentDue);
  if (days < 0) {
    return (
      <span
        data-testid="ops-payment-due-badge"
        className="rounded bg-red-950/50 px-2 py-0.5 text-red-400 text-xs"
      >
        Overdue by {Math.abs(days)} day{Math.abs(days) !== 1 ? 's' : ''}
      </span>
    );
  }
  if (days <= 3) {
    return (
      <span
        data-testid="ops-payment-due-badge"
        className="rounded bg-red-950/50 px-2 py-0.5 text-red-400 text-xs"
      >
        Due in {days} day{days !== 1 ? 's' : ''}
      </span>
    );
  }
  if (days <= 7) {
    return (
      <span
        data-testid="ops-payment-due-badge"
        className="rounded bg-amber-950/50 px-2 py-0.5 text-amber-400 text-xs"
      >
        Due in {days} day{days !== 1 ? 's' : ''}
      </span>
    );
  }
  if (days <= 14) {
    return (
      <span
        data-testid="ops-payment-due-badge"
        className="rounded bg-[#21262d] px-2 py-0.5 text-[#8b949e] text-xs"
      >
        Due in {days} day{days !== 1 ? 's' : ''}
      </span>
    );
  }
  return (
    <span data-testid="ops-payment-due-badge" className="text-[#8b949e] text-xs">
      Due {finalPaymentDue}
    </span>
  );
}

const PAYMENT_STATUS_OPTIONS: PaymentStatus[] = [
  'unknown', 'not_started', 'deposit_paid', 'partially_paid', 'paid', 'overdue', 'waived', 'refunded',
];

const REFUND_STATUS_OPTIONS: RefundStatus[] = [
  'not_applicable', 'not_requested', 'pending_review', 'approved', 'processing', 'paid', 'rejected', 'cancelled',
];

interface PaymentTrackingDraft {
  agreed_amount: string;
  amount_paid: string;
  currency: string;
  payment_status: PaymentStatus;
  payment_method: string;
  payment_reference: string;
  payment_proof_url: string;
  refund_status: RefundStatus;
  refund_amount_agreed: string;
  refund_method: string;
  refund_reference: string;
  refund_paid_by_agency: boolean;
  notes: string;
  final_payment_due: string;
}

function trackingToDraft(pt: PaymentTracking): PaymentTrackingDraft {
  return {
    agreed_amount: pt.agreed_amount != null ? String(pt.agreed_amount) : '',
    amount_paid: pt.amount_paid != null ? String(pt.amount_paid) : '',
    currency: pt.currency || 'INR',
    payment_status: pt.payment_status || 'unknown',
    payment_method: pt.payment_method || '',
    payment_reference: pt.payment_reference || '',
    payment_proof_url: pt.payment_proof_url || '',
    refund_status: pt.refund_status || 'not_applicable',
    refund_amount_agreed: pt.refund_amount_agreed != null ? String(pt.refund_amount_agreed) : '',
    refund_method: pt.refund_method || '',
    refund_reference: pt.refund_reference || '',
    refund_paid_by_agency: pt.refund_paid_by_agency ?? false,
    notes: pt.notes || '',
    final_payment_due: pt.final_payment_due || '',
  };
}

function draftToTracking(draft: PaymentTrackingDraft): PaymentTracking {
  return {
    agreed_amount: draft.agreed_amount ? parseFloat(draft.agreed_amount) : null,
    amount_paid: draft.amount_paid ? parseFloat(draft.amount_paid) : null,
    currency: draft.currency || 'INR',
    payment_status: draft.payment_status,
    payment_method: draft.payment_method || null,
    payment_reference: draft.payment_reference || null,
    payment_proof_url: draft.payment_proof_url || null,
    refund_status: draft.refund_status,
    refund_amount_agreed: draft.refund_amount_agreed ? parseFloat(draft.refund_amount_agreed) : null,
    refund_method: draft.refund_method || null,
    refund_reference: draft.refund_reference || null,
    refund_paid_by_agency: draft.refund_paid_by_agency,
    notes: draft.notes || null,
    final_payment_due: draft.final_payment_due || null,
  };
}

interface PaymentTrackingCardProps {
  paymentTracking: PaymentTracking;
  tripId: string;
  updatedAt: string | null;
  onPaymentSaved?: (tracking: PaymentTracking, newUpdatedAt: string | null) => void;
}

export default function PaymentTrackingCard({
  paymentTracking,
  tripId,
  updatedAt,
  onPaymentSaved,
}: PaymentTrackingCardProps) {
  const currency = paymentTracking.currency || 'INR';
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<PaymentTrackingDraft>(() => trackingToDraft(paymentTracking));
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleEdit() {
    setDraft(trackingToDraft(paymentTracking));
    setConflict(false);
    setError(null);
    setEditing(true);
  }

  function handleCancel() {
    setEditing(false);
    setConflict(false);
    setError(null);
  }

  async function handleSave() {
    setSaving(true);
    setConflict(false);
    setError(null);
    try {
      const resp = await updatePaymentTracking(tripId, draftToTracking(draft), updatedAt ?? undefined);
      setEditing(false);
      onPaymentSaved?.(
        resp.booking_data?.payment_tracking ?? paymentTracking,
        resp.updated_at,
      );
    } catch (err: unknown) {
      const status = (err as { status?: number })?.status;
      if (status === 409) {
        setConflict(true);
      } else {
        setError('Failed to save payment tracking. Please try again.');
      }
    } finally {
      setSaving(false);
    }
  }

  function field(label: string, id: string, children: React.ReactNode) {
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={id} className="text-xs text-[#8b949e]">{label}</label>
        {children}
      </div>
    );
  }

  const inputCls = 'rounded border border-[#30363d] bg-[#0d1117] px-2 py-1 text-xs text-[#e6edf3] focus:border-[#58a6ff] focus:outline-none';
  const selectCls = inputCls;

  if (editing) {
    return (
      <div
        data-testid="ops-payment-tracking"
        className="mt-3 border border-[#30363d] rounded p-3 text-xs"
      >
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="font-medium text-[#e6edf3]">Edit payment tracking</span>
          <span className="rounded bg-blue-950/40 px-2 py-0.5 text-blue-300">Status-only tracking</span>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {field('Agreed amount', 'pt-agreed', (
            <input id="pt-agreed" type="number" min="0" className={inputCls}
              value={draft.agreed_amount}
              onChange={e => setDraft(d => ({ ...d, agreed_amount: e.target.value }))} />
          ))}
          {field('Amount paid', 'pt-paid', (
            <input id="pt-paid" type="number" min="0" className={inputCls}
              value={draft.amount_paid}
              onChange={e => setDraft(d => ({ ...d, amount_paid: e.target.value }))} />
          ))}
          {field('Currency', 'pt-currency', (
            <input id="pt-currency" type="text" maxLength={3} className={inputCls}
              value={draft.currency}
              onChange={e => setDraft(d => ({ ...d, currency: e.target.value.toUpperCase() }))} />
          ))}
          {field('Payment status', 'pt-status', (
            <select id="pt-status" className={selectCls}
              value={draft.payment_status}
              onChange={e => setDraft(d => ({ ...d, payment_status: e.target.value as PaymentStatus }))}>
              {PAYMENT_STATUS_OPTIONS.map(s => <option key={s} value={s}>{formatLabel(s)}</option>)}
            </select>
          ))}
          {field('Payment method', 'pt-method', (
            <input id="pt-method" type="text" className={inputCls}
              value={draft.payment_method}
              onChange={e => setDraft(d => ({ ...d, payment_method: e.target.value }))} />
          ))}
          {field('Payment reference', 'pt-ref', (
            <input id="pt-ref" type="text" className={inputCls}
              value={draft.payment_reference}
              onChange={e => setDraft(d => ({ ...d, payment_reference: e.target.value }))} />
          ))}
          {field('Proof URL', 'pt-proof', (
            <input id="pt-proof" type="text" className={inputCls}
              value={draft.payment_proof_url}
              onChange={e => setDraft(d => ({ ...d, payment_proof_url: e.target.value }))} />
          ))}
          {field('Final payment due', 'pt-due', (
            <input id="pt-due" type="date" className={inputCls}
              data-testid="ops-payment-due-input"
              value={draft.final_payment_due}
              onChange={e => setDraft(d => ({ ...d, final_payment_due: e.target.value }))} />
          ))}
          {field('Refund status', 'pt-refund-status', (
            <select id="pt-refund-status" className={selectCls}
              value={draft.refund_status}
              onChange={e => setDraft(d => ({ ...d, refund_status: e.target.value as RefundStatus }))}>
              {REFUND_STATUS_OPTIONS.map(s => <option key={s} value={s}>{formatLabel(s)}</option>)}
            </select>
          ))}
          {field('Refund amount', 'pt-refund-amount', (
            <input id="pt-refund-amount" type="number" min="0" className={inputCls}
              value={draft.refund_amount_agreed}
              onChange={e => setDraft(d => ({ ...d, refund_amount_agreed: e.target.value }))} />
          ))}
          {field('Refund method', 'pt-refund-method', (
            <input id="pt-refund-method" type="text" className={inputCls}
              value={draft.refund_method}
              onChange={e => setDraft(d => ({ ...d, refund_method: e.target.value }))} />
          ))}
          {field('Refund reference', 'pt-refund-ref', (
            <input id="pt-refund-ref" type="text" className={inputCls}
              value={draft.refund_reference}
              onChange={e => setDraft(d => ({ ...d, refund_reference: e.target.value }))} />
          ))}
        </div>

        <div className="mt-3">
          {field('Notes', 'pt-notes', (
            <textarea id="pt-notes" rows={2} className={inputCls + ' w-full resize-none'}
              value={draft.notes}
              onChange={e => setDraft(d => ({ ...d, notes: e.target.value }))} />
          ))}
        </div>

        <div className="mt-2 flex items-center gap-2">
          <input id="pt-refund-paid" type="checkbox"
            checked={draft.refund_paid_by_agency}
            onChange={e => setDraft(d => ({ ...d, refund_paid_by_agency: e.target.checked }))} />
          <label htmlFor="pt-refund-paid" className="text-xs text-[#8b949e]">Refund paid by agency</label>
        </div>

        {conflict && (
          <div data-testid="ops-payment-conflict" className="mt-3 rounded bg-red-950/30 px-3 py-2 text-xs text-red-400">
            Payment data was updated by another session.{' '}
            <button
              data-testid="ops-payment-conflict-reload"
              className="underline"
              onClick={handleCancel}
            >
              Reload
            </button>
          </div>
        )}
        {error && (
          <div className="mt-3 rounded bg-red-950/30 px-3 py-2 text-xs text-red-400">{error}</div>
        )}

        <div className="mt-3 flex gap-2">
          <button
            data-testid="ops-payment-save-btn"
            onClick={handleSave}
            disabled={saving}
            className="rounded bg-[#238636] px-3 py-1 text-xs text-white hover:bg-[#2ea043] disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save Payment'}
          </button>
          <button
            data-testid="ops-payment-cancel-btn"
            onClick={handleCancel}
            disabled={saving}
            className="rounded border border-[#30363d] px-3 py-1 text-xs text-[#8b949e] hover:text-[#e6edf3] disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="ops-payment-tracking"
      className="mt-3 border border-[#30363d] rounded p-3 text-xs"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-[#e6edf3]">Payment & refund tracking</span>
        <div className="flex items-center gap-2">
          <span className="rounded bg-blue-950/40 px-2 py-0.5 text-blue-300">Status-only tracking</span>
          <button
            data-testid="ops-payment-edit-btn"
            onClick={handleEdit}
            className="rounded border border-[#30363d] px-2 py-0.5 text-[#8b949e] hover:text-[#e6edf3]"
          >
            Edit Payment
          </button>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-[#8b949e] sm:grid-cols-4">
        <div>
          <div>Agreed</div>
          <div className="text-[#e6edf3]">
            {formatMoney(paymentTracking.agreed_amount, currency)}
          </div>
        </div>
        <div>
          <div>Paid</div>
          <div className="text-[#e6edf3]">
            {formatMoney(paymentTracking.amount_paid, currency)}
          </div>
        </div>
        <div>
          <div>Balance due</div>
          <div className="text-[#e6edf3]">
            {formatMoney(paymentTracking.balance_due, currency)}
          </div>
        </div>
        <div>
          <div>Status</div>
          <div className="text-[#e6edf3]">{formatLabel(paymentTracking.payment_status || 'unknown')}</div>
        </div>
      </div>
      <div className="mt-2 text-[#8b949e]">
        Refund: <span className="text-[#e6edf3]">{formatLabel(paymentTracking.refund_status || 'not_applicable')}</span>
      </div>
      {paymentTracking.final_payment_due && (
        <div className="mt-2 flex items-center gap-2 text-[#8b949e]">
          <span>Final payment due:</span>
          <DueBadge finalPaymentDue={paymentTracking.final_payment_due} />
        </div>
      )}
    </div>
  );
}
