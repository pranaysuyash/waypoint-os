'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  Search,
  Plus,
  ShieldCheck,
  Sparkles,
  FileText,
  Trash2,
  Database,
  AlertTriangle,
  CheckCircle2,
  X,
} from 'lucide-react';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { SimulatedBadge } from '@/components/ui/SimulatedBadge';

type DocumentSourceType =
  | 'agency_policy'
  | 'supplier_contract'
  | 'government_advisory'
  | 'trip_document'
  | 'tribal_knowledge'
  | 'override_log'
  | 'itinerary_template'
  | 'specialty_knowledge';

interface RAGDocumentItem {
  document_id: string;
  title: string;
  source_type: DocumentSourceType | string;
  license_class?: string;
  embedding_model?: string | null;
  chunk_count: number;
}

interface RAGStatusResponse {
  provider?: string;
  embedding_model?: string;
  lexical_backend?: string;
  indexed_chunks?: number;
  semantic_available?: boolean;
  corpus_provenance?: string;
}

interface RAGCitation {
  chunk: {
    id: string;
    text: string;
    metadata: {
      document_id: string;
      title: string;
      source_type: string;
    };
  };
  score: number;
  match_type?: string;
}

interface RAGQueryResponse {
  answer: string;
  citations: RAGCitation[];
  groundedness_score?: number;
  ungrounded_claims?: string[];
}

interface StarterTemplate {
  document_id: string;
  title: string;
  source_type: DocumentSourceType;
  tags: string[];
  text: string;
}

const SOURCE_TYPE_LABELS: Record<DocumentSourceType, string> = {
  agency_policy: 'Agency Policy',
  supplier_contract: 'Supplier Contract',
  government_advisory: 'Government Advisory',
  trip_document: 'Trip Document',
  tribal_knowledge: 'Tribal Knowledge',
  override_log: 'Override Log',
  itinerary_template: 'Itinerary Template',
  specialty_knowledge: 'Specialty Knowledge',
};

const CURATED_CATEGORIES: Array<{
  id: string;
  label: string;
  sourceTypes: DocumentSourceType[];
}> = [
  {
    id: 'cat:playbooks',
    label: 'Playbooks & Cheatsheets',
    sourceTypes: ['specialty_knowledge', 'itinerary_template', 'tribal_knowledge'],
  },
  {
    id: 'cat:regulatory',
    label: 'Visa & Regulatory',
    sourceTypes: ['government_advisory', 'trip_document'],
  },
  {
    id: 'cat:memory',
    label: 'Customer Memory',
    sourceTypes: ['override_log'],
  },
  {
    id: 'cat:rules',
    label: 'Agency Rules',
    sourceTypes: ['agency_policy', 'supplier_contract'],
  },
];

const STARTER_TEMPLATES: StarterTemplate[] = [
  {
    document_id: 'starter_sa_safari_malaria_free',
    title: 'South Africa Luxury Safari & Malaria-Free Reserves Guide',
    source_type: 'specialty_knowledge',
    tags: ['Safari', 'Luxury', 'Family', 'Malaria-Free'],
    text: 'Operational playbook for high-net-worth families seeking 5-star safari experiences with zero malaria risk (Madikwe & Eastern Cape). Recommended reserves: Madikwe Game Reserve, Shamwari, and Kwandwe. Fly into Johannesburg OR Tambo (JNB) and connect via private charter or FedAir into Madikwe airstrip. Standard minimum stay: 3 nights per lodge.',
  },
  {
    document_id: 'starter_schengen_visa_checklist',
    title: 'Schengen Visa Processing & Appointment Strategy for Indian Passports',
    source_type: 'agency_policy',
    tags: ['Visa', 'Schengen', 'Compliance', 'Indian Passport'],
    text: 'Mandatory Schengen checklist: passport valid at least 3 months beyond return date, confirmed round-trip flight reservation, day-by-day hotel confirmation, minimum EUR 30,000 travel medical insurance covering repatriation, 6 months stamped bank statements, and VFS appointment lead time of 45 to 60 days in peak season.',
  },
  {
    document_id: 'starter_quote_approval_margin_policy',
    title: 'Agency Margin Guardrail & Senior Operator Approval Policy',
    source_type: 'agency_policy',
    tags: ['Margin', 'Finance', 'Approval', 'Guardrail'],
    text: 'Quotes exceeding $25,000 USD total value or carrying a net agency margin below 12% require explicit senior operator sign-off before issuing client payment links. Non-refundable supplier deposits must be disclosed in writing prior to booking confirmation.',
  },
];

function slugifyId(title: string): string {
  const base = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 64);
  return base || `doc_${Date.now()}`;
}

export default function KnowledgePage() {
  const [status, setStatus] = useState<RAGStatusResponse | null>(null);
  const [documents, setDocuments] = useState<RAGDocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const [queryResult, setQueryResult] = useState<RAGQueryResponse | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newSourceType, setNewSourceType] = useState<DocumentSourceType>('agency_policy');
  const [newTags, setNewTags] = useState('');
  const [newContent, setNewContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadKnowledgeBase = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const [statusRes, docsRes] = await Promise.all([
        fetch('/api/v1/rag/status', { cache: 'no-store' }),
        fetch('/api/v1/rag/documents', { cache: 'no-store' }),
      ]);
      if (!statusRes.ok) {
        throw new Error(`RAG status failed (HTTP ${statusRes.status})`);
      }
      if (!docsRes.ok) {
        throw new Error(`Document listing failed (HTTP ${docsRes.status})`);
      }
      const statusJson = (await statusRes.json()) as RAGStatusResponse;
      const docsJson = (await docsRes.json()) as { items?: RAGDocumentItem[] };
      const items = Array.isArray(docsJson.items) ? docsJson.items : [];
      setStatus(statusJson);
      setDocuments(items);
      setSelectedDocId((prev) =>
        prev && items.some((d) => d.document_id === prev) ? prev : items[0]?.document_id ?? null,
      );
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Unable to load Knowledge Base');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [statusRes, docsRes] = await Promise.all([
          fetch('/api/v1/rag/status', { cache: 'no-store' }),
          fetch('/api/v1/rag/documents', { cache: 'no-store' }),
        ]);
        if (!active) return;
        if (!statusRes.ok) throw new Error(`RAG status failed (HTTP ${statusRes.status})`);
        if (!docsRes.ok) throw new Error(`Document listing failed (HTTP ${docsRes.status})`);
        const statusJson = (await statusRes.json()) as RAGStatusResponse;
        const docsJson = (await docsRes.json()) as { items?: RAGDocumentItem[] };
        if (!active) return;
        const items = Array.isArray(docsJson.items) ? docsJson.items : [];
        setStatus(statusJson);
        setDocuments(items);
        setSelectedDocId((prev) =>
          prev && items.some((d) => d.document_id === prev) ? prev : items[0]?.document_id ?? null,
        );
      } catch (err) {
        if (active) {
          setLoadError(err instanceof Error ? err.message : 'Unable to load Knowledge Base');
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const filteredDocuments = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const curated = CURATED_CATEGORIES.find((cat) => cat.id === activeFilter);
    return documents.filter((doc) => {
      const matchesFilter =
        activeFilter === 'all' ||
        (curated
          ? curated.sourceTypes.includes(doc.source_type as DocumentSourceType)
          : doc.source_type === activeFilter);
      const matchesQuery =
        !q ||
        doc.title.toLowerCase().includes(q) ||
        doc.document_id.toLowerCase().includes(q) ||
        doc.source_type.toLowerCase().includes(q);
      return matchesFilter && matchesQuery;
    });
  }, [documents, activeFilter, searchQuery]);

  const selectedDoc = useMemo(
    () => documents.find((d) => d.document_id === selectedDocId) ?? filteredDocuments[0] ?? null,
    [documents, filteredDocuments, selectedDocId],
  );

  const handleAskRag = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const q = searchQuery.trim();
    if (!q) return;
    setQueryLoading(true);
    setQueryError(null);
    try {
      const res = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, top_k: 5, include_graph: true }),
      });
      if (!res.ok) {
        const detail = await res.text().catch(() => '');
        throw new Error(`Query failed (${res.status}): ${detail || res.statusText}`);
      }
      const data = (await res.json()) as RAGQueryResponse;
      setQueryResult(data);
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : 'Knowledge query failed');
    } finally {
      setQueryLoading(false);
    }
  };

  const indexPlaybook = async (payload: {
    document_id: string;
    title: string;
    source_type: DocumentSourceType;
    text: string;
    tags: string[];
  }) => {
    const res = await fetch('/api/v1/rag/documents/index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        license_class: 'agency_owned',
      }),
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => '');
      throw new Error(`Indexing failed (${res.status}): ${detail || res.statusText}`);
    }
    const result = (await res.json()) as { chunks_created?: number; document_id?: string };
    setActionMessage(
      `Indexed "${payload.title}" (${result.chunks_created ?? 1} chunk${result.chunks_created === 1 ? '' : 's'}).`,
    );
    await loadKnowledgeBase();
    setSelectedDocId(payload.document_id);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) {
      setSubmitError('Title and playbook content are required.');
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const tags = newTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean)
        .slice(0, 20);
      await indexPlaybook({
        document_id: slugifyId(newTitle.trim()),
        title: newTitle.trim(),
        source_type: newSourceType,
        text: newContent.trim(),
        tags,
      });
      setNewTitle('');
      setNewTags('');
      setNewContent('');
      setShowCreateModal(false);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Unable to index playbook');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteDocument = async (documentId: string, title: string) => {
    setActionMessage(null);
    setLoadError(null);
    try {
      const res = await fetch(`/api/v1/rag/documents/${encodeURIComponent(documentId)}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        throw new Error(`Delete failed (HTTP ${res.status})`);
      }
      setActionMessage(`Removed "${title}" from the agency knowledge base.`);
      await loadKnowledgeBase();
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Unable to delete document');
    }
  };

  const indexedIds = useMemo(() => new Set(documents.map((d) => d.document_id)), [documents]);

  return (
    <div className='p-6 max-w-6xl mx-auto space-y-6'>
      {/* Header */}
      <header className='flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#1c2128] pb-4'>
        <div>
          <BackToOverviewLink />
          <h1 className='text-ui-2xl font-semibold text-[#e6edf3] flex items-center gap-2.5 mt-2'>
            <BookOpen className='size-6 text-[#58a6ff]' />
            Knowledge Base &amp; Agency Memory
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Agency-scoped RAG documents, SOPs, visa policies, and grounded retrieval citations.
          </p>
        </div>

        <button
          type='button'
          onClick={() => {
            setSubmitError(null);
            setShowCreateModal(true);
          }}
          className='flex items-center gap-2 px-4 py-2 bg-[#238636] text-white rounded-lg text-ui-sm font-medium hover:bg-[#2ea043] transition-colors shrink-0'
        >
          <Plus className='size-4' /> Create New Playbook
        </button>
      </header>

      {/* Live RAG Engine Status Bar */}
      <section
        aria-label='RAG engine status'
        className='rounded-xl border border-[#30363d] bg-[#0d1117] px-4 py-3 flex flex-wrap items-center justify-between gap-3 text-ui-xs'
      >
        <div className='flex flex-wrap items-center gap-3 text-[#c9d1d9]'>
          <span className='inline-flex items-center gap-1.5 font-medium text-[#e6edf3]'>
            <Database className='size-3.5 text-[#58a6ff]' />
            RAG Store:
          </span>
          <span>
            {documents.length} document{documents.length === 1 ? '' : 's'} ·{' '}
            {status?.indexed_chunks ?? 0} indexed chunks
          </span>
          {status?.lexical_backend ? (
            <span className='text-[#8b949e]'>Lexical: {status.lexical_backend}</span>
          ) : null}
          {status?.embedding_model ? (
            <span className='text-[#8b949e]'>Embeddings: {status.embedding_model}</span>
          ) : null}
        </div>
        <span className='text-[#8b949e]'>
          {status ? (status.semantic_available ? 'Hybrid semantic + lexical active' : 'Lexical retrieval active') : 'Connecting…'}
        </span>
      </section>

      {actionMessage ? (
        <div className='rounded-lg border border-[#3fb950]/40 bg-[#3fb950]/10 px-4 py-2.5 text-ui-xs text-[#3fb950] flex items-center justify-between'>
          <span className='flex items-center gap-2'>
            <CheckCircle2 className='size-4' />
            {actionMessage}
          </span>
          <button type='button' onClick={() => setActionMessage(null)} aria-label='Dismiss notice'>
            <X className='size-3.5' />
          </button>
        </div>
      ) : null}

      {loadError ? (
        <div className='rounded-xl border border-[#f85149]/40 bg-[#f85149]/10 p-4 flex items-center justify-between'>
          <span className='text-ui-sm text-[#f85149] flex items-center gap-2'>
            <AlertTriangle className='size-4' />
            {loadError}
          </span>
          <button
            type='button'
            onClick={() => void loadKnowledgeBase()}
            className='px-3 py-1.5 rounded-lg border border-[#30363d] bg-[#161b22] text-ui-xs text-[#e6edf3]'
          >
            Retry
          </button>
        </div>
      ) : null}

      {/* Search & Grounded Query Bar */}
      <div className='space-y-3'>
        <form onSubmit={(e) => void handleAskRag(e)} className='flex gap-2'>
          <div className='relative flex-1'>
            <label htmlFor='knowledge-search-input' className='sr-only'>
              Search agency knowledge or ask a grounded question
            </label>
            <Search className='absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-[#8b949e]' />
            <input
              id='knowledge-search-input'
              name='knowledgeSearch'
              type='text'
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder='Search playbooks or ask a grounded question (e.g. "Schengen visa", "margin approval")...'
              aria-label='Search agency knowledge'
              className='w-full pl-10 pr-4 py-2.5 bg-[#0f1115] border border-[#30363d] rounded-xl text-ui-sm text-[#e6edf3] placeholder:text-[#8b949e] focus:outline-none focus:border-[#58a6ff]'
            />
          </div>
          <button
            type='submit'
            disabled={queryLoading || !searchQuery.trim()}
            className='px-4 py-2.5 rounded-xl bg-[#1f6feb] text-white text-ui-sm font-medium hover:bg-[#388bfd] disabled:opacity-50 shrink-0 flex items-center gap-1.5'
          >
            <Sparkles className='size-4' />
            {queryLoading ? 'Querying…' : 'Query RAG'}
          </button>
        </form>

        <div className='space-y-2'>
          <div className='flex items-center gap-2 flex-wrap'>
            <button
              type='button'
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1.5 rounded-lg text-ui-xs font-medium transition-colors ${
                activeFilter === 'all'
                  ? 'bg-[#1f6feb] text-white'
                  : 'bg-[#161b22] text-[#8b949e] hover:text-[#e6edf3]'
              }`}
            >
              All Intelligence ({documents.length})
            </button>
            {CURATED_CATEGORIES.map((category) => (
              <button
                key={category.id}
                type='button'
                onClick={() => setActiveFilter(category.id)}
                className={`px-3 py-1.5 rounded-lg text-ui-xs font-medium transition-colors ${
                  activeFilter === category.id
                    ? 'bg-[#1f6feb] text-white'
                    : 'bg-[#161b22] text-[#8b949e] hover:text-[#e6edf3]'
                }`}
              >
                {category.label}
              </button>
            ))}
          </div>
          <div className='flex items-center gap-1.5 flex-wrap'>
            <span className='text-[11px] text-[#8b949e] mr-1'>Source type:</span>
            {(Object.entries(SOURCE_TYPE_LABELS) as Array<[DocumentSourceType, string]>).map(([key, label]) => (
              <button
                key={key}
                type='button'
                onClick={() => setActiveFilter(key)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  activeFilter === key
                    ? 'bg-[#58a6ff]/20 text-[#79c0ff] border border-[#58a6ff]/40'
                    : 'bg-[#0d1117] text-[#8b949e] border border-[#21262d] hover:text-[#e6edf3]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Grounded RAG Query Answer */}
      {queryError ? (
        <div className='rounded-xl border border-[#f85149]/30 bg-[#f85149]/5 p-4 text-ui-xs text-[#f85149]'>
          {queryError}
        </div>
      ) : null}

      {queryResult ? (
        <section
          aria-label='Grounded RAG answer'
          className='rounded-xl border border-[#58a6ff]/40 bg-[#0d1117] p-5 space-y-3'
        >
          <div className='flex items-center justify-between'>
            <h2 className='text-ui-sm font-semibold text-[#e6edf3] flex items-center gap-2'>
              <Sparkles className='size-4 text-[#58a6ff]' />
              Grounded Retrieval Answer
            </h2>
            <button
              type='button'
              onClick={() => setQueryResult(null)}
              className='text-ui-xs text-[#8b949e] hover:text-[#e6edf3]'
            >
              Clear
            </button>
          </div>
          <p className='text-ui-sm text-[#e6edf3] whitespace-pre-line'>{queryResult.answer}</p>
          {queryResult.citations.length > 0 ? (
            <div className='space-y-2 pt-2 border-t border-[#21262d]'>
              <p className='text-ui-xs text-[#8b949e] uppercase tracking-wider'>
                Citations ({queryResult.citations.length})
              </p>
              {queryResult.citations.map((cit) => (
                <div
                  key={cit.chunk.id}
                  className='rounded-lg border border-[#21262d] bg-[#161b22] p-3 text-ui-xs space-y-1'
                >
                  <div className='flex items-center justify-between text-[#c9d1d9] font-medium'>
                    <span>{cit.chunk.metadata.title}</span>
                    <span className='text-[#8b949e]'>score {cit.score.toFixed(2)}</span>
                  </div>
                  <p className='text-[#8b949e] line-clamp-3'>{cit.chunk.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className='text-ui-xs text-[#8b949e]'>No matching citations found in indexed agency documents.</p>
          )}
        </section>
      ) : null}

      {/* Main Content Split */}
      <div className='grid grid-cols-1 lg:grid-cols-12 gap-6'>
        {/* Left List */}
        <div className='lg:col-span-7 space-y-3'>
          <h2 className='text-ui-xs font-semibold uppercase tracking-wider text-[#8b949e] px-1'>
            Indexed Agency Documents ({filteredDocuments.length})
          </h2>

          {isLoading ? (
            <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-6 text-ui-sm text-[#8b949e]'>
              Loading indexed agency documents…
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-8 text-center space-y-3'>
              <FileText className='size-8 text-[#8b949e] mx-auto' />
              <p className='text-ui-sm text-[#e6edf3] font-medium'>No indexed documents match this view</p>
              <p className='text-ui-xs text-[#8b949e]'>
                Create a playbook above or index one of the starter templates below to enable grounded search.
              </p>
            </div>
          ) : (
            filteredDocuments.map((doc) => {
              const isSelected = selectedDoc?.document_id === doc.document_id;
              return (
                <div
                  key={doc.document_id}
                  onClick={() => setSelectedDocId(doc.document_id)}
                  className={`rounded-xl border p-4 cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#161b22] border-[#58a6ff]'
                      : 'bg-[#0f1115] border-[#1c2128] hover:border-[#30363d]'
                  }`}
                >
                  <div className='flex items-start justify-between gap-2 mb-1.5'>
                    <div className='flex items-center gap-2 flex-wrap'>
                      <span className='px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-[#58a6ff]/15 text-[#58a6ff]'>
                        {SOURCE_TYPE_LABELS[doc.source_type as DocumentSourceType] ?? doc.source_type}
                      </span>
                      <span className='text-ui-xs text-[#8b949e]'>
                        {doc.chunk_count} chunk{doc.chunk_count === 1 ? '' : 's'}
                      </span>
                    </div>
                    <button
                      type='button'
                      onClick={(e) => {
                        e.stopPropagation();
                        void handleDeleteDocument(doc.document_id, doc.title);
                      }}
                      aria-label={`Delete ${doc.title}`}
                      className='text-[#8b949e] hover:text-[#f85149] p-1 rounded'
                    >
                      <Trash2 className='size-3.5' />
                    </button>
                  </div>
                  <h3 className='text-ui-base font-semibold text-[#e6edf3]'>{doc.title || doc.document_id}</h3>
                  <p className='text-ui-xs text-[#8b949e] mt-1 font-mono'>
                    id: {doc.document_id} · license: {doc.license_class ?? 'agency_owned'}
                  </p>
                </div>
              );
            })
          )}
        </div>

        {/* Right Preview & Starter Templates */}
        <div className='lg:col-span-5 space-y-4'>
          {selectedDoc ? (
            <div className='rounded-xl border border-[#1c2128] bg-[#0f1115] p-5 space-y-3'>
              <div className='flex items-center justify-between text-ui-xs text-[#8b949e]'>
                <span className='flex items-center gap-1.5 text-[#58a6ff]'>
                  <ShieldCheck className='size-4' />
                  Agency-scoped corpus record
                </span>
                <span>{selectedDoc.chunk_count} chunks</span>
              </div>
              <h2 className='text-ui-lg font-semibold text-[#e6edf3]'>{selectedDoc.title}</h2>
              <div className='text-ui-xs text-[#8b949e] space-y-1'>
                <div>Document ID: <span className='font-mono text-[#c9d1d9]'>{selectedDoc.document_id}</span></div>
                <div>Source type: <span className='text-[#c9d1d9]'>{selectedDoc.source_type}</span></div>
                <div>License: <span className='text-[#c9d1d9]'>{selectedDoc.license_class ?? 'agency_owned'}</span></div>
                <div>Embedding model: <span className='text-[#c9d1d9]'>{selectedDoc.embedding_model || 'lexical-only'}</span></div>
              </div>
              <button
                type='button'
                onClick={() => {
                  setSearchQuery(selectedDoc.title);
                  void handleAskRag();
                }}
                className='w-full mt-2 px-3 py-2 rounded-lg border border-[#30363d] bg-[#161b22] text-ui-xs text-[#e6edf3] hover:border-[#58a6ff]'
              >
                Query chunks for this document
              </button>
            </div>
          ) : null}

          {/* Reference Starter Templates (honestly marked until indexed) */}
          <div className='rounded-xl border border-[#30363d] bg-[#0d1117] p-5 space-y-3'>
            <div className='flex items-center justify-between gap-2'>
              <h3 className='text-ui-sm font-semibold text-[#e6edf3]'>Reference Starter Playbooks</h3>
              <SimulatedBadge label='Starter Templates' />
            </div>
            <p className='text-ui-xs text-[#8b949e]'>
              Curated operational templates. Click Index to add a template to your agency RAG store.
            </p>
            <div className='space-y-2.5'>
              {STARTER_TEMPLATES.map((tpl) => {
                const alreadyIndexed = indexedIds.has(tpl.document_id);
                return (
                  <div key={tpl.document_id} className='rounded-lg border border-[#21262d] bg-[#161b22] p-3 space-y-2'>
                    <div className='flex items-start justify-between gap-2'>
                      <div>
                        <p className='text-ui-xs font-medium text-[#e6edf3]'>{tpl.title}</p>
                        <p className='text-[11px] text-[#8b949e] mt-0.5 line-clamp-2'>{tpl.text}</p>
                      </div>
                      <button
                        type='button'
                        disabled={alreadyIndexed}
                        onClick={() => void indexPlaybook(tpl)}
                        className='px-2.5 py-1 rounded text-[11px] border border-[#30363d] bg-[#0d1117] text-[#e6edf3] hover:border-[#58a6ff] disabled:opacity-50 shrink-0'
                      >
                        {alreadyIndexed ? 'Indexed' : 'Index'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Create Playbook Modal */}
      {showCreateModal ? (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4'>
          <form
            onSubmit={(e) => void handleCreateSubmit(e)}
            className='bg-[#161b22] border border-[#30363d] rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl'
          >
            <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
              <h3 className='text-ui-lg font-semibold text-[#e6edf3]'>Index New Agency Playbook</h3>
              <button
                type='button'
                onClick={() => setShowCreateModal(false)}
                className='text-[#8b949e] hover:text-[#e6edf3]'
              >
                Cancel
              </button>
            </div>
            {submitError ? <p className='text-ui-xs text-[#f85149]'>{submitError}</p> : null}
            <div className='space-y-3'>
              <div>
                <label htmlFor='kb-new-title' className='block text-ui-xs font-medium text-[#8b949e] mb-1'>
                  Title
                </label>
                <input
                  id='kb-new-title'
                  name='title'
                  type='text'
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder='e.g. Maldives Water Villa Transfer Guidelines'
                  className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3]'
                />
              </div>
              <div>
                <label htmlFor='kb-new-source-type' className='block text-ui-xs font-medium text-[#8b949e] mb-1'>
                  Source Type
                </label>
                <select
                  id='kb-new-source-type'
                  name='sourceType'
                  value={newSourceType}
                  onChange={(e) => setNewSourceType(e.target.value as DocumentSourceType)}
                  className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3]'
                >
                  {(Object.entries(SOURCE_TYPE_LABELS) as Array<[DocumentSourceType, string]>).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor='kb-new-tags' className='block text-ui-xs font-medium text-[#8b949e] mb-1'>
                  Tags (comma-separated)
                </label>
                <input
                  id='kb-new-tags'
                  name='tags'
                  type='text'
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                  placeholder='e.g. Maldives, Seaplane, Luxury'
                  className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3]'
                />
              </div>
              <div>
                <label htmlFor='kb-new-content' className='block text-ui-xs font-medium text-[#8b949e] mb-1'>
                  Content / Operational Rules
                </label>
                <textarea
                  id='kb-new-content'
                  name='content'
                  rows={5}
                  required
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder='Enter detailed agency policy, visa checklist, or supplier instructions...'
                  className='w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3]'
                />
              </div>
            </div>
            <div className='flex justify-end gap-2 pt-2'>
              <button
                type='button'
                onClick={() => setShowCreateModal(false)}
                className='px-4 py-2 text-ui-sm text-[#8b949e] hover:text-[#e6edf3]'
              >
                Cancel
              </button>
              <button
                type='submit'
                disabled={isSubmitting}
                className='px-4 py-2 bg-[#238636] text-white rounded-lg text-ui-sm font-medium hover:bg-[#2ea043] disabled:opacity-50'
              >
                {isSubmitting ? 'Indexing…' : 'Save & Index into Agency Brain'}
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
