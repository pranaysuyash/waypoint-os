'use client';

import { useState, useEffect, useCallback } from 'react';
import { Clock, RotateCcw, AlertTriangle, CheckCircle, XCircle, FileText } from 'lucide-react';
import {
  type ExtractionResponse,
  type AttemptSummary,
  listExtractionAttempts,
  retryExtraction,
} from '@/lib/api-client';

interface ExtractionHistoryPanelProps {
  tripId: string;
  documentId: string;
  extraction: ExtractionResponse | null;
  onRetryComplete: (extraction: ExtractionResponse) => void;
}

function formatLatency(ms: number | null): string {
  if (ms === null) return '--';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatCost(usd: number | null): string {
  if (usd === null) return '--';
  if (usd < 0.001) return `$${usd.toFixed(6)}`;
  if (usd < 1) return `$${usd.toFixed(4)}`;
  return `$${usd.toFixed(2)}`;
}

function fallbackLabel(rank: number | null): string {
  if (rank === null || rank === 0) return 'Primary';
  return `Fallback ${rank}`;
}

function groupAttemptsByRun(attempts: AttemptSummary[]): Map<number, AttemptSummary[]> {
  const groups = new Map<number, AttemptSummary[]>();
  for (const a of attempts) {
    const existing = groups.get(a.run_number) ?? [];
    existing.push(a);
    groups.set(a.run_number, existing);
  }
  for (const [, arr] of groups) {
    arr.sort((a, b) => a.attempt_number - b.attempt_number);
  }
  return groups;
}

export function ExtractionHistoryPanel({
  tripId,
  documentId,
  extraction,
  onRetryComplete,
}: ExtractionHistoryPanelProps) {
  const [attempts, setAttempts] = useState<AttemptSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAttempts = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listExtractionAttempts(tripId, documentId);
      setAttempts(data);
    } catch {
      // Silently fail — attempt history is supplementary
    } finally {
      setLoading(false);
    }
  }, [tripId, documentId]);

  useEffect(() => {
    fetchAttempts();
  }, [fetchAttempts]);

  const handleRetry = async () => {
    setRetrying(true);
    setError(null);
    try {
      const updated = await retryExtraction(tripId, documentId);
      onRetryComplete(updated);
      await fetchAttempts();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Retry failed');
    } finally {
      setRetrying(false);
    }
  };

  const canRetry = extraction?.status === 'failed' && !retrying;
  const grouped = groupAttemptsByRun(attempts);
  const sortedRuns = [...grouped.entries()].sort((a, b) => b[0] - a[0]);
  const currentAttemptId = extraction?.current_attempt_id;

  return (
    <div className="bg-elevated border border-border-default rounded-xl p-4 mt-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-text-muted" />
          <h3 className="text-ui-sm font-semibold text-text-primary">Extraction History</h3>
          {attempts.length > 0 && (
            <span className="text-ui-xs bg-[#58a6ff] text-[#0d1117] px-2 py-0.5 rounded-full">
              {attempts.length} attempt{attempts.length !== 1 ? 's' : ''}
            </span>
          )}
          {extraction?.run_count != null && extraction.run_count > 0 && (
            <span className="text-ui-xs text-text-muted">
              {extraction.run_count} run{extraction.run_count !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {canRetry && (
          <button
            data-testid={`ops-extraction-retry-btn-${documentId}`}
            onClick={handleRetry}
            disabled={retrying}
            className="flex items-center gap-1 text-ui-xs text-accent-blue hover:text-[#79b8ff] disabled:opacity-50"
          >
            <RotateCcw className="w-3 h-3" />
            {retrying ? 'Retrying...' : 'Retry'}
          </button>
        )}
      </div>

      {/* Metadata summary row */}
      {extraction && (
        <div className="flex items-center gap-3 text-ui-xs text-text-muted mb-3">
          {extraction.provider_name && (
            <span>{extraction.provider_name}</span>
          )}
          {extraction.model_name && (
            <span>/ {extraction.model_name}</span>
          )}
          {extraction.latency_ms != null && (
            <span>· {formatLatency(extraction.latency_ms)}</span>
          )}
          {extraction.page_count != null && extraction.page_count > 0 && (
            <span className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {extraction.page_count} page{extraction.page_count !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      )}

      {loading && attempts.length === 0 && (
        <p className="text-ui-sm text-text-muted">Loading attempt history...</p>
      )}

      {!loading && attempts.length === 0 && (
        <p className="text-ui-sm text-text-muted">No attempt history available.</p>
      )}

      {/* Attempt groups by run */}
      {sortedRuns.length > 0 && (
        <div className="space-y-3 max-h-80 overflow-y-auto">
          {sortedRuns.map(([runNumber, runAttempts]) => (
            <div key={runNumber}>
              <div className="text-ui-xs text-text-muted uppercase tracking-wide mb-1">
                Run {runNumber}{runNumber === (extraction?.run_count ?? 0) ? ' (latest)' : ''}
              </div>
              <div className="space-y-1">
                {runAttempts.map((attempt) => {
                  const isCurrent = attempt.attempt_id === currentAttemptId;
                  const isFailed = attempt.status === 'failed';

                  return (
                    <div
                      key={attempt.attempt_id}
                      data-testid={`ops-attempt-${attempt.attempt_id}`}
                      className={`flex items-center gap-2 p-2 rounded text-xs ${
                        isCurrent
                          ? 'bg-emerald-900/20 border border-emerald-800/30'
                          : 'bg-surface border border-[#21262d]'
                      }`}
                    >
                      {/* Status indicator */}
                      {isFailed ? (
                        <XCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                      ) : (
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      )}

                      {/* Current marker */}
                      {isCurrent && (
                        <span data-testid={`ops-attempt-current-${attempt.attempt_id}`} className="text-emerald-300 font-medium text-[10px] uppercase tracking-wide">
                          Current
                        </span>
                      )}

                      {/* Attempt number and fallback rank */}
                      <span className="text-text-muted">
                        Attempt {attempt.attempt_number}
                      </span>
                      <span className="text-text-muted">
                        ({fallbackLabel(attempt.fallback_rank)})
                      </span>

                      {/* Provider/model */}
                      <span className="text-text-primary">
                        {attempt.provider_name}{attempt.model_name ? ` / ${attempt.model_name}` : ''}
                      </span>

                      {/* Latency */}
                      {attempt.latency_ms != null && (
                        <span className="text-text-muted">
                          {formatLatency(attempt.latency_ms)}
                        </span>
                      )}

                      {/* Error code — only error_code, never error_summary */}
                      {isFailed && attempt.error_code && (
                        <span className="flex items-center gap-1 text-yellow-400">
                          <AlertTriangle className="w-3 h-3" />
                          {attempt.error_code}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {error && (
        <div data-testid={`ops-extraction-retry-error-${documentId}`} className="text-xs text-red-400 mt-2">
          {error}
        </div>
      )}
    </div>
  );
}
