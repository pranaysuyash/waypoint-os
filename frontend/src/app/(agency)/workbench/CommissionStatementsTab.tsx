'use client';

import { useState } from 'react';
import { FileSpreadsheet, Link2, Upload } from 'lucide-react';
import {
  ingestCommissionStatement,
  linkCommissionStatementRow,
  type CommissionIngestBatch,
  type CommissionIngestRow,
} from '@/lib/api-client';

/**
 * Commission statement ingest (R2-B / Travefy bar, 2026-11-03).
 *
 * Paste a supplier statement (CSV export, email body, or screenshot OCR
 * text); the backend parses candidate rows, matches them to agency trips
 * (booking-ref exact → amount-tolerance + fuzzy supplier), and returns
 * manual-link candidates. Candidates are preview-grade working state —
 * money truth moves only when a payout is recorded through the durable
 * payout store (the batch is labeled `durable: false` by the backend and
 * this surface says so).
 */

const STATUS_STYLES: Record<CommissionIngestRow['match_status'], string> = {
  matched: 'bg-[#3fb950]/10 text-[#3fb950]',
  manual_candidate: 'bg-[#d29922]/10 text-[#d29922]',
  unmatched: 'bg-[#484f58]/20 text-[#8b949e]',
};

const STATUS_LABELS: Record<CommissionIngestRow['match_status'], string> = {
  matched: 'Matched',
  manual_candidate: 'Needs manual link',
  unmatched: 'Unrecognized',
};

export default function CommissionStatementsTab() {
  const [format, setFormat] = useState<'csv' | 'email' | 'image_ocr'>('csv');
  const [content, setContent] = useState('');
  const [batch, setBatch] = useState<CommissionIngestBatch | null>(null);
  const [linkTripIds, setLinkTripIds] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [linkFeedback, setLinkFeedback] = useState<string | null>(null);

  const handleIngest = async () => {
    setError(null);
    setLinkFeedback(null);
    if (!content.trim()) {
      setError('Paste the statement content first.');
      return;
    }
    setIsSubmitting(true);
    try {
      const res = await ingestCommissionStatement(format, content);
      setBatch(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Statement ingest failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLink = async (rowIndex: number) => {
    if (!batch) return;
    const tripId = (linkTripIds[rowIndex] ?? '').trim();
    if (!tripId) {
      setLinkFeedback('Enter the trip ID to link this row to.');
      return;
    }
    setError(null);
    try {
      const updated = await linkCommissionStatementRow(batch.batch_id, rowIndex, tripId);
      setBatch(updated);
      setLinkFeedback(`Row ${rowIndex} linked to ${tripId}.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Manual link failed.');
    }
  };

  return (
    <div className="space-y-4" data-testid="commission-statements-tab">
      <div
        role="note"
        className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-5 text-amber-100"
      >
        <strong>Preview-grade candidates:</strong> statement rows here are working matches for
        review — money truth only moves when a payout is recorded through the durable payout
        store. Image statements must be pasted as OCR text (no in-process OCR).
      </div>

      <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="size-4 text-[#58a6ff]" />
          <span className="text-ui-sm font-semibold text-[#e6edf3]">Ingest a statement</span>
        </div>
        <div className="flex gap-2">
          {(['csv', 'email', 'image_ocr'] as const).map((f) => (
            <button
              key={f}
              type="button"
              aria-pressed={format === f}
              onClick={() => setFormat(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                format === f ? 'bg-[#58a6ff] text-white' : 'bg-[#21262d] text-[#8b949e] hover:bg-[#2a3038]'
              }`}
            >
              {f === 'csv' ? 'CSV' : f === 'email' ? 'Email body' : 'Screenshot OCR text'}
            </button>
          ))}
        </div>
        <textarea
          aria-label="Statement content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={
            format === 'csv'
              ? 'supplier,booking_ref,amount,currency,date\nBali Villas Direct,BVD-88231,2400.00,USD,2026-10-12'
              : 'Paste the email body or the screenshot OCR text — one statement line per row.'
          }
          rows={6}
          className="w-full px-3 py-2 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff] resize-none font-mono"
        />
        <button
          type="button"
          onClick={handleIngest}
          disabled={isSubmitting}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#58a6ff] text-white text-ui-sm font-semibold disabled:opacity-50"
          data-testid="commission-ingest-submit"
        >
          <Upload className="size-3.5" />
          {isSubmitting ? 'Parsing…' : 'Parse & match statement'}
        </button>
        {error && (
          <p role="alert" className="text-ui-xs text-[#f85149]">
            {error}
          </p>
        )}
        {linkFeedback && (
          <p className="text-ui-xs text-[#3fb950]" data-testid="commission-link-feedback">
            {linkFeedback}
          </p>
        )}
      </div>

      {batch && (
        <div className="rounded-xl border border-[#30363d] bg-[#0f1115] overflow-hidden" data-testid="commission-ingest-batch">
          <div className="px-4 py-3 border-b border-[#30363d] bg-[#161b22] flex items-center justify-between flex-wrap gap-2">
            <span className="text-ui-sm font-semibold text-[#e6edf3]">
              {batch.row_count} statement row{batch.row_count === 1 ? '' : 's'}
            </span>
            <span className="text-ui-xs text-[#8b949e]">
              {batch.matched_count} matched · {batch.manual_candidate_count} manual ·{' '}
              {batch.unmatched_count} unrecognized · batch {batch.batch_id}
            </span>
          </div>
          {batch.rows.length === 0 ? (
            <p className="p-4 text-ui-sm text-[#8b949e]">
              No statement rows were recognized in that content. Check the format and try again.
            </p>
          ) : (
            <ul className="divide-y divide-[#21262d]">
              {batch.rows.map((row) => (
                <li key={row.row_index} className="px-4 py-3 flex flex-wrap items-start gap-3" data-testid="commission-statement-row">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${STATUS_STYLES[row.match_status]}`}
                  >
                    {STATUS_LABELS[row.match_status]}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-ui-sm text-[#e6edf3]">
                      {row.supplier_name || <span className="text-[#484f58] italic">unknown supplier</span>}
                      {row.booking_ref && <span className="text-[#8b949e]"> · {row.booking_ref}</span>}
                    </p>
                    <p className="text-ui-xs text-[#484f58] mt-0.5">
                      {row.amount != null ? `${row.currency || ''} ${row.amount.toLocaleString()}` : 'no amount'}
                      {row.date ? ` · ${row.date}` : ''}
                      {row.match_method === 'manual_link' && ' · manually linked'}
                      {row.match_method === 'amount_fuzzy_supplier' && row.match_confidence != null && (
                        <> · fuzzy {Math.round(row.match_confidence * 100)}%</>
                      )}
                    </p>
                  </div>
                  {row.match_status === 'manual_candidate' && (
                    <div className="flex items-center gap-2">
                      <input
                        aria-label={`Trip ID for row ${row.row_index}`}
                        value={linkTripIds[row.row_index] ?? ''}
                        onChange={(e) =>
                          setLinkTripIds((prev) => ({ ...prev, [row.row_index]: e.target.value }))
                        }
                        placeholder="trip_id"
                        className="w-40 px-2 py-1 bg-[#0f1115] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3] placeholder:text-[#484f58]"
                      />
                      <button
                        type="button"
                        onClick={() => handleLink(row.row_index)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[#30363d] bg-[#161b22] text-[11px] font-medium text-[#58a6ff] hover:bg-[#1c2431]"
                      >
                        <Link2 className="size-3" />
                        Link trip
                      </button>
                    </div>
                  )}
                  {row.match_status === 'matched' && row.match_trip_id && (
                    <a
                      href={`/trips/${row.match_trip_id}`}
                      className="text-ui-xs text-[#58a6ff] hover:underline"
                    >
                      open trip
                    </a>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
