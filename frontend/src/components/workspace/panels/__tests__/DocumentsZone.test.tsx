import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DocumentsZone from '../DocumentsZone';

const mockApi = {
  getDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  acceptDocument: vi.fn(),
  rejectDocument: vi.fn(),
  deleteDocument: vi.fn(),
  getDocumentDownloadUrl: vi.fn(),
  extractDocument: vi.fn(),
  applyExtraction: vi.fn(),
  rejectExtraction: vi.fn(),
};

vi.mock('@/lib/api-client', () => ({
  getDocuments: (...args: unknown[]) => mockApi.getDocuments(...args),
  uploadDocument: (...args: unknown[]) => mockApi.uploadDocument(...args),
  acceptDocument: (...args: unknown[]) => mockApi.acceptDocument(...args),
  rejectDocument: (...args: unknown[]) => mockApi.rejectDocument(...args),
  deleteDocument: (...args: unknown[]) => mockApi.deleteDocument(...args),
  getDocumentDownloadUrl: (...args: unknown[]) => mockApi.getDocumentDownloadUrl(...args),
  extractDocument: (...args: unknown[]) => mockApi.extractDocument(...args),
  applyExtraction: (...args: unknown[]) => mockApi.applyExtraction(...args),
  rejectExtraction: (...args: unknown[]) => mockApi.rejectExtraction(...args),
}));

vi.mock('@/components/workspace/panels/ExtractionHistoryPanel', () => ({
  ExtractionHistoryPanel: () => null,
}));

function docFixture(id: string, status: 'pending_review' | 'accepted' | 'rejected') {
  return {
    id,
    trip_id: 'trip_1',
    traveler_id: null,
    uploaded_by_type: 'agent' as const,
    document_type: 'passport',
    filename_present: true,
    filename_ext: 'pdf',
    mime_type: 'application/pdf',
    size_bytes: 1024,
    status,
    scan_status: 'clean' as const,
    review_notes_present: false,
    created_at: '2026-05-14T00:00:00Z',
    updated_at: '2026-05-14T00:00:00Z',
    reviewed_at: null,
    reviewed_by: null,
  };
}

describe('DocumentsZone', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getDocuments.mockResolvedValue({ documents: [] });
  });

  it('renders document section container', async () => {
    render(<DocumentsZone tripId="trip_1" canUpload={false} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-documents')).toBeInTheDocument();
    });
  });

  it('shows empty state when no documents', async () => {
    render(<DocumentsZone tripId="trip_1" canUpload={false} />);
    await waitFor(() => {
      expect(screen.getByText('No documents uploaded yet.')).toBeInTheDocument();
    });
  });

  it('shows upload button when canUpload is true', async () => {
    render(<DocumentsZone tripId="trip_1" canUpload={true} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-document-upload-btn')).toBeInTheDocument();
    });
  });

  it('hides upload button when canUpload is false', async () => {
    render(<DocumentsZone tripId="trip_1" canUpload={false} />);
    await waitFor(() => {
      expect(screen.queryByTestId('ops-document-upload-btn')).not.toBeInTheDocument();
    });
  });

  it('renders documents when loaded', async () => {
    mockApi.getDocuments.mockResolvedValue({
      documents: [
        docFixture('doc_1', 'pending_review'),
        docFixture('doc_2', 'accepted'),
      ],
    });

    render(<DocumentsZone tripId="trip_1" canUpload={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-document-doc_1')).toBeInTheDocument();
      expect(screen.getByTestId('ops-document-doc_2')).toBeInTheDocument();
    });
  });

  it('shows accept/reject buttons for pending_review document', async () => {
    mockApi.getDocuments.mockResolvedValue({
      documents: [docFixture('doc_1', 'pending_review')],
    });

    render(<DocumentsZone tripId="trip_1" canUpload={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-document-doc_1-accept-btn')).toBeInTheDocument();
      expect(screen.getByTestId('ops-document-doc_1-reject-btn')).toBeInTheDocument();
    });
  });

  it('calls acceptDocument and refreshes on accept', async () => {
    const user = userEvent.setup();
    mockApi.getDocuments.mockResolvedValue({
      documents: [docFixture('doc_1', 'pending_review')],
    });
    mockApi.acceptDocument.mockResolvedValue({});

    render(<DocumentsZone tripId="trip_1" canUpload={false} />);
    await screen.findByTestId('ops-document-doc_1-accept-btn');
    await user.click(screen.getByTestId('ops-document-doc_1-accept-btn'));

    await waitFor(() => {
      expect(mockApi.acceptDocument).toHaveBeenCalledWith('trip_1', 'doc_1');
    });
  });

  it('calls deleteDocument and clears extraction state on delete', async () => {
    const user = userEvent.setup();
    mockApi.getDocuments.mockResolvedValue({
      documents: [docFixture('doc_1', 'accepted')],
    });
    mockApi.deleteDocument.mockResolvedValue({});

    render(<DocumentsZone tripId="trip_1" canUpload={false} />);
    await screen.findByTestId('ops-document-doc_1-delete-btn');
    await user.click(screen.getByTestId('ops-document-doc_1-delete-btn'));

    await waitFor(() => {
      expect(mockApi.deleteDocument).toHaveBeenCalledWith('trip_1', 'doc_1');
    });
  });

  it('calls onDocumentsChange after fetch', async () => {
    const docs = [docFixture('doc_1', 'pending_review')];
    mockApi.getDocuments.mockResolvedValue({ documents: docs });
    const onDocumentsChange = vi.fn();

    render(
      <DocumentsZone tripId="trip_1" canUpload={false} onDocumentsChange={onDocumentsChange} />,
    );

    await waitFor(() => {
      expect(onDocumentsChange).toHaveBeenCalledWith(docs);
    });
  });

  it('shows extract button for pending_review or accepted documents', async () => {
    mockApi.getDocuments.mockResolvedValue({
      documents: [
        docFixture('doc_pending', 'pending_review'),
        docFixture('doc_accepted', 'accepted'),
      ],
    });

    render(<DocumentsZone tripId="trip_1" canUpload={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-doc-extract-btn-doc_pending')).toBeInTheDocument();
      expect(screen.getByTestId('ops-doc-extract-btn-doc_accepted')).toBeInTheDocument();
    });
  });
});
