import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import KnowledgePanel from '../KnowledgePanel';
import type { RagGroundedAnswer, RagStatus } from '@/types/spine';

// Panel contract: live data only — real status chips, grounded answers with
// citations, must-confirm flags. No simulated content (determinism-audit bar).

const status: RagStatus = {
  embedding_provider: 'openai',
  embedding_model: 'text-embedding-3-small',
  embedding_dimension: 1536,
  is_semantic: true,
  fts_lexical_leg: true,
  store_path: '/tmp/rag.db',
  agency_chunk_count: 3,
  corpus_embedding_models: [
    { embedding_model: 'text-embedding-3-small', embedding_dimension: 1536, chunk_count: 3 },
  ],
};

const grounded: RagGroundedAnswer = {
  query: 'visa free duration japan',
  answer: 'Based on retrieved documents:\n\nUS passport holders enter Japan visa free for 90 days.',
  groundedness_score: 0.91,
  is_grounded: true,
  claim_support_status: 'source_excerpt',
  grounding_method: 'lexical_overlap_numeric_guard_v1',
  lexical_overlap_score: 0.91,
  citations: [
    {
      chunk: {
        id: 'c1',
        parent_id: null,
        content: 'US passport holders enter Japan visa free for 90 days with a valid passport.',
        embedding: null,
        metadata: {
          document_id: 'adv1',
          agency_id: 'a',
          source_type: 'government_advisory',
          title: 'Japan Visa Advisory',
          tags: [],
          entity_references: [],
          embedding_model: 'text-embedding-3-small',
          embedding_dimension: 1536,
          source_text: 'US passport holders enter Japan visa free for 90 days with a valid passport.',
          license_class: 'agency_owned',
          created_at: '2026-10-22T00:00:00Z',
        },
        token_count: 14,
      },
      score: 0.02,
      dense_score: 0.6,
      sparse_score: 0.4,
      retrieval_method: 'hybrid',
    },
  ],
  must_confirm: [],
  execution_telemetry_id: 'rag_eval_test',
};

function mockFetch(queryResponse?: RagGroundedAnswer) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/rag/status')) {
      return new Response(JSON.stringify(status), { status: 200 });
    }
    if (url.includes('/rag/documents')) {
      return new Response(JSON.stringify({ items: [] }), { status: 200 });
    }
    if (url.includes('/rag/query')) {
      return new Response(JSON.stringify(queryResponse ?? grounded), { status: 200 });
    }
    return new Response('not found', { status: 404 });
  });
}

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch());
});

describe('KnowledgePanel', () => {
  it('renders the truthful status chips (semantic + FTS5) from the live service', async () => {
    render(<KnowledgePanel />);
    await waitFor(() => expect(screen.getByText('SEMANTIC')).toBeInTheDocument());
    expect(screen.getByText('FTS5')).toBeInTheDocument();
    expect(screen.getByText('text-embedding-3-small')).toBeInTheDocument();
  });

  it('renders a grounded answer with citation provenance and license', async () => {
    render(<KnowledgePanel />);
    await userEvent.type(
      screen.getByPlaceholderText('Ask the agency knowledge base…'),
      'visa free duration japan',
    );
    await userEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('SOURCE EXCERPT')).toBeInTheDocument());
    expect(screen.getByText(/Japan Visa Advisory/)).toBeInTheDocument();
    expect(screen.getByText(/license: agency_owned/)).toBeInTheDocument();
  });

  it('surfaces the low-grounding warning and must-confirm flags when ungrounded', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch({ ...grounded, is_grounded: false, groundedness_score: 0.4, must_confirm: ['Low grounding confidence (0.40 < 0.75). Operator must verify document details before client proposal.'] }),
    );
    render(<KnowledgePanel />);
    await userEvent.type(
      screen.getByPlaceholderText('Ask the agency knowledge base…'),
      'something obscure',
    );
    await userEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('CLAIMS NEED REVIEW')).toBeInTheDocument());
    expect(screen.getByText(/Operator must verify/)).toBeInTheDocument();
  });

  it('keeps high-overlap generated claims visibly unverified', async () => {
    vi.stubGlobal('fetch', mockFetch({
      ...grounded,
      claim_support_status: 'not_verified',
      is_grounded: true,
      groundedness_score: 1,
      must_confirm: ['Claim support has not been verified.'],
    }));
    render(<KnowledgePanel />);
    await userEvent.type(screen.getByPlaceholderText('Ask the agency knowledge base…'), 'visa rules');
    await userEvent.click(screen.getByRole('button', { name: /search/i }));
    await waitFor(() => expect(screen.getByText('CLAIMS NEED REVIEW')).toBeInTheDocument());
    expect(screen.queryByText('SOURCE EXCERPT')).not.toBeInTheDocument();
    expect(screen.getByText('Claim support has not been verified.')).toBeInTheDocument();
  });
});
