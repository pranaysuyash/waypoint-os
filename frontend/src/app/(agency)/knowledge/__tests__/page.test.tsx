// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import KnowledgePage from '../PageClient';

vi.mock('@/components/navigation/BackToOverviewLink', () => ({
  BackToOverviewLink: () => <div data-testid='back-link' />,
}));

describe('KnowledgePage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads real RAG status, indexed agency documents, and starter templates', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo) => {
        const url = String(input);
        if (url.includes('/api/v1/rag/status')) {
          return {
            ok: true,
            json: async () => ({
              provider: 'local_hash',
              embedding_model: 'hash-v1',
              lexical_backend: 'sqlite_fts5',
              indexed_chunks: 4,
              semantic_available: false,
            }),
          } as Response;
        }
        if (url.includes('/api/v1/rag/documents')) {
          return {
            ok: true,
            json: async () => ({
              items: [
                {
                  document_id: 'doc_visa_1',
                  title: 'Schengen Visa Checklist',
                  source_type: 'agency_policy',
                  license_class: 'agency_owned',
                  chunk_count: 4,
                },
              ],
            }),
          } as Response;
        }
        return { ok: false, status: 404, json: async () => ({}) } as Response;
      }),
    );

    render(<KnowledgePage />);

    expect(screen.getByText(/Knowledge Base & Agency Memory/i)).toBeInTheDocument();
    expect(screen.getByText(/Create New Playbook/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText(/Schengen Visa Checklist/i).length).toBeGreaterThan(0);
    });
    expect(screen.getByText(/1 document · 4 indexed chunks/i)).toBeInTheDocument();
    expect(screen.getByText(/Reference Starter Playbooks/i)).toBeInTheDocument();
    expect(screen.getByText(/Starter Templates/i)).toBeInTheDocument();
  });
});
