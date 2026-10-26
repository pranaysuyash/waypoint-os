'use client';

/**
 * KnowledgePanel — operator surface for the agency RAG repository.
 * Live data only: status/document inventory from the mounted spine router,
 * grounded answers with citations and must-confirm flags. No simulated
 * content anywhere on this panel (determinism-audit standard: anything that
 * looks like a probability or a source must be one).
 *
 * Contract: frontend/src/types/spine.ts (verified against the router).
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { BookOpen, Search, AlertTriangle, FileText, Loader2 } from 'lucide-react';
import type {
  RagDocument,
  RagGroundedAnswer,
  RagStatus,
} from '@/types/spine';

export default function KnowledgePanel() {
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [documents, setDocuments] = useState<RagDocument[] | null>(null);
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<RagGroundedAnswer | null>(null);
  const [querying, setQuerying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/rag/status');
      if (!res.ok) throw new Error(`status ${res.status}`);
      const body = (await res.json()) as RagStatus;
      if (mountedRef.current) setStatus(body);
    } catch {
      if (mountedRef.current) setError('Knowledge service status unavailable.');
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/rag/documents');
      if (!res.ok) throw new Error(`documents ${res.status}`);
      const body = (await res.json()) as { items?: RagDocument[] };
      if (mountedRef.current) setDocuments(Array.isArray(body?.items) ? body.items : []);
    } catch {
      if (mountedRef.current) setDocuments([]);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadStatus();
    void loadDocuments();
  }, [loadStatus, loadDocuments]);

  const runQuery = async () => {
    const trimmed = query.trim();
    if (!trimmed || querying) return;
    setQuerying(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: trimmed, top_k: 5 }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(body?.detail ?? `query failed (${res.status})`);
      }
      const body = (await res.json()) as RagGroundedAnswer;
      if (mountedRef.current) setAnswer(body);
    } catch (exc) {
      if (mountedRef.current) setError(exc instanceof Error ? exc.message : 'Query failed.');
    } finally {
      if (mountedRef.current) setQuerying(false);
    }
  };

  return (
    <div className='space-y-6'>
      {/* Service posture — the honest status strip */}
      <div className='p-4 rounded-xl border border-border bg-card space-y-3'>
        <div className='flex items-center justify-between'>
          <h3 className='text-sm font-semibold text-foreground flex items-center gap-2'>
            <BookOpen className='h-4 w-4 text-primary' />
            Agency Knowledge Base
          </h3>
          {status && (
            <div className='flex items-center gap-2 text-[10px] font-mono'>
              <span
                className={`px-2 py-0.5 rounded ${
                  status.is_semantic
                    ? 'bg-emerald-500/10 text-emerald-500'
                    : 'bg-muted text-muted-foreground'
                }`}
                title={status.is_semantic ? 'Semantic embedding lane active' : 'Deterministic hash lane (no semantic provider configured)'}
              >
                {status.is_semantic ? 'SEMANTIC' : 'HASH LANE'}
              </span>
              <span className='text-muted-foreground'>{status.embedding_model}</span>
              <span
                className={`px-2 py-0.5 rounded ${
                  status.fts_lexical_leg
                    ? 'bg-sky-500/10 text-sky-500'
                    : 'bg-amber-500/10 text-amber-500'
                }`}
                title={status.fts_lexical_leg ? 'FTS5 lexical index' : 'Substring fallback (FTS5 unavailable)'}
              >
                {status.fts_lexical_leg ? 'FTS5' : 'LEX:FALLBACK'}
              </span>
            </div>
          )}
        </div>

        {/* Provider-switch honesty: corpus holding another model's vectors */}
        {(status?.corpus_embedding_models?.length ?? 0) > 1 && (
          <div className='flex items-center gap-2 p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5 text-xs text-amber-500'>
            <AlertTriangle className='h-3.5 w-3.5 shrink-0' />
            Corpus holds vectors from multiple embedding models — dense search only
            compares against the live model. Re-index older documents to unify.
          </div>
        )}

        {/* Documents inventory */}
        <div className='space-y-1.5'>
          {documents === null ? (
            <p className='text-xs text-muted-foreground'>Loading documents…</p>
          ) : documents.length === 0 ? (
            <p className='text-xs text-muted-foreground'>
              No documents indexed yet. Specialty knowledge seeds automatically on first use.
            </p>
          ) : (
            <div className='grid gap-1.5'>
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className='flex items-center justify-between p-2.5 rounded-lg border border-border bg-muted/20 text-xs'
                >
                  <div className='flex items-center gap-2 min-w-0'>
                    <FileText className='h-3.5 w-3.5 text-muted-foreground shrink-0' />
                    <span className='font-medium text-foreground truncate'>{doc.title}</span>
                    <span className='text-[10px] text-muted-foreground shrink-0'>
                      {doc.chunk_count} chunks
                    </span>
                  </div>
                  <span
                    className={`shrink-0 text-[10px] font-mono px-1.5 py-0.5 rounded ${
                      doc.license_class === 'agency_owned'
                        ? 'bg-muted text-muted-foreground'
                        : doc.license_class === 'redistribution_safe'
                          ? 'bg-emerald-500/10 text-emerald-500'
                          : 'bg-amber-500/10 text-amber-500'
                    }`}
                    title={`License: ${doc.license_class}`}
                  >
                    {doc.license_class}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Grounded query */}
      <div className='p-4 rounded-xl border border-border bg-card space-y-3'>
        <h3 className='text-sm font-semibold text-foreground flex items-center gap-2'>
          <Search className='h-4 w-4 text-primary' />
          Grounded Query
        </h3>
        <div className='flex gap-2'>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void runQuery();
            }}
            placeholder='Ask the agency knowledge base…'
            maxLength={4000}
            className='flex-1 px-3 py-2 rounded-lg border border-border bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary'
          />
          <button
            onClick={() => void runQuery()}
            disabled={querying || !query.trim()}
            className='px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50 flex items-center gap-1.5'
          >
            {querying ? <Loader2 className='h-4 w-4 animate-spin' /> : <Search className='h-4 w-4' />}
            {querying ? 'Searching' : 'Search'}
          </button>
        </div>

        {error && (
          <p className='text-xs text-[#f85149]'>{error}</p>
        )}

        {answer && (
          <div className='space-y-3 pt-1'>
            <div className='flex items-center gap-2 text-xs'>
              {answer.claim_support_status === 'source_excerpt' && answer.is_grounded ? (
                <span className='flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-foreground font-semibold'>
                  <BookOpen className='h-3.5 w-3.5' />
                  SOURCE EXCERPT
                </span>
              ) : (
                <span className='flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 font-semibold'>
                  <AlertTriangle className='h-3.5 w-3.5' />
                  CLAIMS NEED REVIEW
                </span>
              )}
              <span className='text-muted-foreground'>
                {answer.citations.length} citation{answer.citations.length === 1 ? '' : 's'}
              </span>
            </div>

            <p className='text-xs text-muted-foreground'>
              Citations show the source material. Verify its date and applicability before advising a traveler.
            </p>

            {answer.must_confirm.length > 0 && (
              <div className='p-2.5 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-1'>
                {answer.must_confirm.map((m, i) => (
                  <p key={i} className='text-xs text-amber-500'>
                    ⚠ {m}
                  </p>
                ))}
              </div>
            )}

            <div className='p-3 rounded-lg border border-border bg-muted/10 text-sm text-foreground whitespace-pre-wrap'>
              {answer.answer}
            </div>

            {answer.citations.length > 0 && (
              <div className='space-y-1.5'>
                <p className='text-[10px] font-semibold tracking-wide text-muted-foreground'>
                  SOURCES &amp; PROVENANCE
                </p>
                {answer.citations.map((c, i) => (
                  <div key={c.chunk.id} className='p-2.5 rounded-lg border border-border bg-muted/20 text-xs space-y-1'>
                    <div className='flex items-center justify-between gap-2'>
                      <span className='font-medium text-foreground truncate'>
                        [{i + 1}] {c.chunk.metadata.title}
                      </span>
                      <span className='text-[10px] font-mono text-muted-foreground shrink-0'>
                        {c.retrieval_method}
                      </span>
                    </div>
                    <p className='text-muted-foreground line-clamp-2'>
                      {(c.chunk.metadata.source_text ?? c.chunk.content).slice(0, 200)}
                    </p>
                    <p className='text-[10px] text-muted-foreground'>
                      Doc: {c.chunk.metadata.document_id} · license: {c.chunk.metadata.license_class}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
