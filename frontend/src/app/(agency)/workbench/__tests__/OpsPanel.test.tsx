import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OpsPanel from '../OpsPanel';

// OpsPanel no longer reads from the Workbench store — readiness comes from trip.validation only.
// No useWorkbenchStore mock needed here.

const mockApi = {
  getBookingData: vi.fn(),
  updateBookingData: vi.fn(),
  updatePaymentTracking: vi.fn(),
  getCollectionLink: vi.fn(),
  generateCollectionLink: vi.fn(),
  revokeCollectionLink: vi.fn(),
  getPendingBookingData: vi.fn(),
  acceptPendingBookingData: vi.fn(),
  rejectPendingBookingData: vi.fn(),
  getDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  acceptDocument: vi.fn(),
  rejectDocument: vi.fn(),
  deleteDocument: vi.fn(),
  getDocumentDownloadUrl: vi.fn(),
  extractDocument: vi.fn(),
  getExtraction: vi.fn(),
  applyExtraction: vi.fn(),
  rejectExtraction: vi.fn(),
};

vi.mock('@/lib/api-client', () => ({
  getBookingData: (...args: unknown[]) => mockApi.getBookingData(...args),
  updateBookingData: (...args: unknown[]) => mockApi.updateBookingData(...args),
  updatePaymentTracking: (...args: unknown[]) => mockApi.updatePaymentTracking(...args),
  getCollectionLink: (...args: unknown[]) => mockApi.getCollectionLink(...args),
  generateCollectionLink: (...args: unknown[]) => mockApi.generateCollectionLink(...args),
  revokeCollectionLink: (...args: unknown[]) => mockApi.revokeCollectionLink(...args),
  getPendingBookingData: (...args: unknown[]) => mockApi.getPendingBookingData(...args),
  acceptPendingBookingData: (...args: unknown[]) => mockApi.acceptPendingBookingData(...args),
  rejectPendingBookingData: (...args: unknown[]) => mockApi.rejectPendingBookingData(...args),
  getDocuments: (...args: unknown[]) => mockApi.getDocuments(...args),
  uploadDocument: (...args: unknown[]) => mockApi.uploadDocument(...args),
  acceptDocument: (...args: unknown[]) => mockApi.acceptDocument(...args),
  rejectDocument: (...args: unknown[]) => mockApi.rejectDocument(...args),
  deleteDocument: (...args: unknown[]) => mockApi.deleteDocument(...args),
  getDocumentDownloadUrl: (...args: unknown[]) => mockApi.getDocumentDownloadUrl(...args),
  extractDocument: (...args: unknown[]) => mockApi.extractDocument(...args),
  getExtraction: (...args: unknown[]) => mockApi.getExtraction(...args),
  applyExtraction: (...args: unknown[]) => mockApi.applyExtraction(...args),
  rejectExtraction: (...args: unknown[]) => mockApi.rejectExtraction(...args),
}));

const READINESS = {
  highest_ready_tier: 'proposal_ready',
  suggested_next_stage: 'booking',
  should_auto_advance_stage: false,
  missing_for_next: [],
  tiers: {
    intake_minimum: {
      tier: 'intake_minimum',
      ready: true,
      met: ['destination_candidates', 'date_window'],
      unmet: [],
    },
  },
};

function tripAtStage(stage: string) {
  return { id: 'trip_1', stage, validation: { readiness: READINESS } } as never;
}

describe('OpsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: null,
      updated_at: null,
      stage: 'proposal',
      readiness: {},
    });
    mockApi.getCollectionLink.mockRejectedValue(new Error('not found'));
    mockApi.getPendingBookingData.mockRejectedValue(new Error('not found'));
    mockApi.getDocuments.mockResolvedValue({ documents: [] });
  });

  it('shows readiness notice (not a hard gate) when trip has no readiness data', () => {
    render(<OpsPanel trip={{ id: 'trip_1', stage: 'proposal' } as never} />);
    expect(screen.getByTestId('ops-readiness-empty')).toBeInTheDocument();
    // The full panel still renders — readiness is a section, not a global gate
    expect(screen.getByTestId('ops-panel')).toBeInTheDocument();
  });

  it('renders booking data section when readiness is missing', async () => {
    render(<OpsPanel trip={{ id: 'trip_1', stage: 'proposal' } as never} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-booking-data')).toBeInTheDocument();
    });
  });

  it('renders document section when readiness is missing', async () => {
    render(<OpsPanel trip={{ id: 'trip_1', stage: 'proposal' } as never} />);
    await waitFor(() => {
      expect(screen.getByTestId('ops-documents')).toBeInTheDocument();
    });
  });

  it('shows visa/passport concern when signal is present in trip.validation', () => {
    const tripWithVisa = {
      id: 'trip_1',
      stage: 'proposal',
      validation: {
        readiness: {
          ...READINESS,
          signals: { visa_concerns_present: true },
        },
      },
    } as never;
    render(<OpsPanel trip={tripWithVisa} />);
    expect(screen.getByTestId('ops-signal-visa-concern')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Phase 4C: Extraction apply flow tests
// These tests exercise DocumentsZone behavior through OpsPanel's composite render.
// The module-level vi.mock intercepts all api-client imports including DocumentsZone's.
// ---------------------------------------------------------------------------

describe('OpsPanel extraction apply flow', () => {
  const DOC_ID = 'doc_abc123';

  /** Setup a trip with booking data, an accepted document, and an extraction. */
  function setupExtractionScene() {

    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [
          { traveler_id: 't1', full_name: 'Manual Entry' },
          { traveler_id: 't2', full_name: 'Second Person' },
        ],
      },
      updated_at: '2026-05-04T00:00:00Z',
      stage: 'proposal',
      readiness: {},
    });
    mockApi.getDocuments.mockResolvedValue({
      documents: [
        {
          id: DOC_ID,
          document_type: 'passport',
          status: 'accepted',
          uploaded_by: 'agent',
          created_at: '2026-05-06T00:00:00Z',
        },
      ],
    });
    mockApi.getCollectionLink.mockRejectedValue(new Error('not found'));
    mockApi.getPendingBookingData.mockRejectedValue(new Error('not found'));
  }

  const EXTRACTION_RESPONSE = {
    id: 'ext_1',
    document_id: DOC_ID,
    status: 'pending_review',
    extracted_by: 'noop_extractor',
    overall_confidence: 0.85,
    field_count: 3,
    fields: [
      { field_name: 'full_name', value: 'EXTRACTED_NAME', confidence: 0.9, present: true },
      { field_name: 'passport_number', value: 'AB1234567', confidence: 0.8, present: true },
      { field_name: 'date_of_birth', value: '1990-01-01', confidence: 0.85, present: true },
    ],
    created_at: '2026-05-06T00:00:00Z',
    updated_at: '2026-05-06T00:00:00Z',
    reviewed_at: null,
    reviewed_by: null,
  };

  it('apply button disabled when no traveler selected', async () => {
    setupExtractionScene();
    mockApi.extractDocument.mockResolvedValue(EXTRACTION_RESPONSE);

    const user = userEvent.setup();
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const extractBtn = await screen.findByTestId(`ops-doc-extract-btn-${DOC_ID}`);
    await user.click(extractBtn);

    const applyBtn = await screen.findByTestId(`ops-extraction-apply-btn-${DOC_ID}`);
    expect(applyBtn).toBeDisabled();
  });

  it('apply button disabled when no fields selected', async () => {
    setupExtractionScene();
    mockApi.extractDocument.mockResolvedValue(EXTRACTION_RESPONSE);

    const user = userEvent.setup();
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const extractBtn = await screen.findByTestId(`ops-doc-extract-btn-${DOC_ID}`);
    await user.click(extractBtn);

    // Select traveler but no fields
    const travelerSelect = await screen.findByTestId(`ops-extraction-traveler-select-${DOC_ID}`);
    await user.selectOptions(travelerSelect, 't1');

    const applyBtn = await screen.findByTestId(`ops-extraction-apply-btn-${DOC_ID}`);
    expect(applyBtn).toBeDisabled();
  });

  it('apply sends selected traveler_id and selected fields', async () => {
    setupExtractionScene();
    mockApi.extractDocument.mockResolvedValue(EXTRACTION_RESPONSE);
    mockApi.applyExtraction.mockResolvedValue({
      applied: true,
      conflicts: [],
      extraction: { ...EXTRACTION_RESPONSE, status: 'applied' },
    });

    const user = userEvent.setup();
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const extractBtn = await screen.findByTestId(`ops-doc-extract-btn-${DOC_ID}`);
    await user.click(extractBtn);

    // Select traveler
    const travelerSelect = await screen.findByTestId(`ops-extraction-traveler-select-${DOC_ID}`);
    await user.selectOptions(travelerSelect, 't2');

    // Select one field
    const fieldCb = await screen.findByTestId(`ops-extraction-field-cb-${DOC_ID}-passport_number`);
    await user.click(fieldCb);

    // Click apply
    const applyBtn = await screen.findByTestId(`ops-extraction-apply-btn-${DOC_ID}`);
    await user.click(applyBtn);

    await waitFor(() => {
      expect(mockApi.applyExtraction).toHaveBeenCalledWith('trip_1', DOC_ID, {
        traveler_id: 't2',
        fields_to_apply: ['passport_number'],
        allow_overwrite: false,
      });
    });
  });

  it('first apply sends allow_overwrite=false', async () => {
    setupExtractionScene();
    mockApi.extractDocument.mockResolvedValue(EXTRACTION_RESPONSE);
    mockApi.applyExtraction.mockResolvedValue({
      applied: true,
      conflicts: [],
      extraction: { ...EXTRACTION_RESPONSE, status: 'applied' },
    });

    const user = userEvent.setup();
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await user.click(await screen.findByTestId(`ops-doc-extract-btn-${DOC_ID}`));
    await user.selectOptions(
      await screen.findByTestId(`ops-extraction-traveler-select-${DOC_ID}`),
      't1',
    );
    await user.click(
      await screen.findByTestId(`ops-extraction-field-cb-${DOC_ID}-passport_number`),
    );
    await user.click(await screen.findByTestId(`ops-extraction-apply-btn-${DOC_ID}`));

    await waitFor(() => {
      expect(mockApi.applyExtraction).toHaveBeenCalledWith('trip_1', DOC_ID,
        expect.objectContaining({ allow_overwrite: false }),
      );
    });
  });

  it('shows conflict display when apply returns conflicts', async () => {
    setupExtractionScene();
    mockApi.extractDocument.mockResolvedValue(EXTRACTION_RESPONSE);
    mockApi.applyExtraction.mockResolvedValue({
      applied: false,
      conflicts: [
        {
          field_name: 'full_name',
          existing_value: 'Ma***y',
          extracted_value: 'EX***ME',
        },
      ],
      extraction: null,
    });

    const user = userEvent.setup();
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await user.click(await screen.findByTestId(`ops-doc-extract-btn-${DOC_ID}`));
    await user.selectOptions(
      await screen.findByTestId(`ops-extraction-traveler-select-${DOC_ID}`),
      't1',
    );
    await user.click(
      await screen.findByTestId(`ops-extraction-field-cb-${DOC_ID}-full_name`),
    );
    await user.click(await screen.findByTestId(`ops-extraction-apply-btn-${DOC_ID}`));

    expect(await screen.findByTestId(`ops-extraction-conflicts-${DOC_ID}`)).toBeInTheDocument();
    expect(screen.getByText(/conflicts detected/i)).toBeInTheDocument();
    expect(screen.getByTestId(`ops-extraction-overwrite-btn-${DOC_ID}`)).toBeInTheDocument();
  });

  it('overwrite confirmation sends allow_overwrite=true', async () => {
    setupExtractionScene();
    mockApi.extractDocument.mockResolvedValue(EXTRACTION_RESPONSE);
    let callCount = 0;
    mockApi.applyExtraction.mockImplementation(() => {
      callCount++;
      if (callCount === 1) {
        return Promise.resolve({
          applied: false,
          conflicts: [
            { field_name: 'full_name', existing_value: 'Ma***y', extracted_value: 'EX***ME' },
          ],
          extraction: null,
        });
      }
      return Promise.resolve({
        applied: true,
        conflicts: [],
        extraction: { ...EXTRACTION_RESPONSE, status: 'applied' },
      });
    });

    const user = userEvent.setup();
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await user.click(await screen.findByTestId(`ops-doc-extract-btn-${DOC_ID}`));
    await user.selectOptions(
      await screen.findByTestId(`ops-extraction-traveler-select-${DOC_ID}`),
      't1',
    );
    await user.click(
      await screen.findByTestId(`ops-extraction-field-cb-${DOC_ID}-full_name`),
    );
    await user.click(await screen.findByTestId(`ops-extraction-apply-btn-${DOC_ID}`));

    // Wait for conflict display, then click overwrite
    const overwriteBtn = await screen.findByTestId(`ops-extraction-overwrite-btn-${DOC_ID}`);
    await user.click(overwriteBtn);

    await waitFor(() => {
      expect(mockApi.applyExtraction).toHaveBeenLastCalledWith('trip_1', DOC_ID,
        expect.objectContaining({ allow_overwrite: true }),
      );
    });
  });
});
