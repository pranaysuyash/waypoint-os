import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import OpsPanel from '../OpsPanel';

const mockStore = {
  result_validation: null as unknown,
};

vi.mock('@/stores/workbench', () => ({
  useWorkbenchStore: () => mockStore,
}));

const mockApi = {
  getBookingData: vi.fn(),
  updateBookingData: vi.fn(),
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
    mockStore.result_validation = null;
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

  it('shows empty state when no readiness data', () => {
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-panel-empty')).toBeInTheDocument();
  });

  it('shows collection link section at proposal stage', async () => {
    mockStore.result_validation = { readiness: READINESS };
    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-documents-canonical-path-hint')).toBeInTheDocument();
  });

  it('shows collection link section at booking stage', async () => {
    mockStore.result_validation = { readiness: READINESS };
    render(<OpsPanel trip={tripAtStage('booking')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-collection-link')).toBeInTheDocument();
    });
  });

  it('hides collection link at discovery stage', async () => {
    mockStore.result_validation = { readiness: READINESS };
    render(<OpsPanel trip={tripAtStage('discovery')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-booking-data')).toBeInTheDocument();
    });
    expect(screen.queryByTestId('ops-collection-link')).not.toBeInTheDocument();
  });

  it('shows active link hint when GET returns has_active_token', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getCollectionLink.mockResolvedValue({
      has_active_token: true,
      token_id: 'tok_1',
      expires_at: '2026-05-11T00:00:00Z',
      status: 'active',
      has_pending_submission: false,
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-link-active-hint')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
  });

  it('generates collection link and shows URL', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.generateCollectionLink.mockResolvedValue({
      token_id: 'tok_1',
      collection_url: 'https://example.com/booking-collection/d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b/abc123',
      expires_at: '2026-05-11T00:00:00Z',
      trip_id: 'trip_1',
      status: 'active',
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const btn = await screen.findByTestId('ops-generate-link-btn');
    await user.click(btn);

    await waitFor(() => {
      expect(screen.getByTestId('ops-link-info')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-link-url')).toHaveValue('https://example.com/booking-collection/d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b/abc123');
    expect(screen.getByTestId('ops-copy-link-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-revoke-link-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-regenerate-link-btn')).toBeInTheDocument();
  });

  it('revokes collection link', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.generateCollectionLink.mockResolvedValue({
      token_id: 'tok_1',
      collection_url: 'https://example.com/booking-collection/d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b/abc123',
      expires_at: '2026-05-11T00:00:00Z',
      trip_id: 'trip_1',
      status: 'active',
    });
    mockApi.revokeCollectionLink.mockResolvedValue({ ok: true });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    // Generate first to get URL visible
    await user.click(await screen.findByTestId('ops-generate-link-btn'));
    await screen.findByTestId('ops-revoke-link-btn');

    await user.click(screen.getByTestId('ops-revoke-link-btn'));

    await waitFor(() => {
      expect(mockApi.revokeCollectionLink).toHaveBeenCalledWith('trip_1');
    });
    expect(screen.queryByTestId('ops-link-info')).not.toBeInTheDocument();
    expect(screen.getByTestId('ops-generate-link-btn')).toBeInTheDocument();
  });

  it('shows pending review section when customer data exists', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
        payer: { name: 'Jane Doe' },
      },
      booking_data_source: null,
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-pending-review')).toBeInTheDocument();
    });
    expect(screen.getByTestId('ops-accept-btn')).toBeInTheDocument();
    expect(screen.getByTestId('ops-reject-btn')).toBeInTheDocument();
    expect(screen.getByText('Submitted by customer')).toBeInTheDocument();
  });

  it('accepts pending booking data', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
      },
      booking_data_source: null,
    });
    mockApi.acceptPendingBookingData.mockResolvedValue({ ok: true });
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
      },
      updated_at: '2026-05-04T00:00:00Z',
      stage: 'proposal',
      readiness: {},
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const acceptBtn = await screen.findByTestId('ops-accept-btn');
    await user.click(acceptBtn);

    await waitFor(() => {
      expect(mockApi.acceptPendingBookingData).toHaveBeenCalledWith('trip_1');
    });
    await waitFor(() => {
      expect(screen.queryByTestId('ops-pending-review')).not.toBeInTheDocument();
    });
  });

  it('rejects pending booking data', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
      },
      booking_data_source: null,
    });
    mockApi.rejectPendingBookingData.mockResolvedValue({ ok: true });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    const rejectBtn = await screen.findByTestId('ops-reject-btn');
    await user.click(rejectBtn);

    await waitFor(() => {
      expect(mockApi.rejectPendingBookingData).toHaveBeenCalledWith('trip_1');
    });
    await waitFor(() => {
      expect(screen.queryByTestId('ops-pending-review')).not.toBeInTheDocument();
    });
  });

  it('shows source badge when booking data was entered by agent', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: null,
      booking_data_source: 'agent',
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-source-badge')).toBeInTheDocument();
    });
    expect(screen.getByText('Agent')).toBeInTheDocument();
  });

  it('shows source badge when booking data was accepted from customer', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getPendingBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      pending_booking_data: null,
      booking_data_source: 'customer_accepted',
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await waitFor(() => {
      expect(screen.getByTestId('ops-source-badge')).toBeInTheDocument();
    });
    expect(screen.getByText('Customer (verified)')).toBeInTheDocument();
  });

  it('shows payment tracking without exposing a payment collection workflow', async () => {
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
        payer: { name: 'Jane Doe' },
        payment_tracking: {
          agreed_amount: 120000,
          currency: 'INR',
          amount_paid: 50000,
          balance_due: 70000,
          payment_status: 'partially_paid',
          refund_status: 'not_applicable',
          tracking_only: true,
        },
      },
      updated_at: '2026-05-12T00:00:00Z',
      stage: 'proposal',
      readiness: {},
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    expect(await screen.findByTestId('ops-payment-tracking')).toBeInTheDocument();
    expect(screen.getByText('Status-only tracking')).toBeInTheDocument();
    expect(screen.getByText('INR 70,000')).toBeInTheDocument();
    expect(screen.queryByText(/wallet/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pay now/i)).not.toBeInTheDocument();
  });

  it('saves payment tracking through the booking data endpoint', async () => {
    const user = userEvent.setup();
    mockStore.result_validation = { readiness: READINESS };
    mockApi.getBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: {
        travelers: [
          { traveler_id: 'adult_1', full_name: 'Jane Doe', date_of_birth: '1990-01-01' },
        ],
        payer: { name: 'Jane Doe' },
      },
      updated_at: '2026-05-12T00:00:00Z',
      stage: 'proposal',
      readiness: {},
    });
    mockApi.updateBookingData.mockResolvedValue({
      trip_id: 'trip_1',
      booking_data: null,
      updated_at: '2026-05-12T00:01:00Z',
      stage: 'proposal',
      readiness: {},
    });

    render(<OpsPanel trip={tripAtStage('proposal')} />);

    await user.click(await screen.findByTestId('ops-edit-btn'));
    await user.clear(screen.getByTestId('ops-payment-agreed-amount'));
    await user.type(screen.getByTestId('ops-payment-agreed-amount'), '120000');
    await user.clear(screen.getByTestId('ops-payment-amount-paid'));
    await user.type(screen.getByTestId('ops-payment-amount-paid'), '50000');
    await user.selectOptions(screen.getByTestId('ops-payment-status'), 'partially_paid');
    await user.click(screen.getByTestId('ops-save-btn'));

    await waitFor(() => {
      expect(mockApi.updateBookingData).toHaveBeenCalled();
    });
    const [, payload] = mockApi.updateBookingData.mock.calls[0];
    expect(payload.payment_tracking).toMatchObject({
      agreed_amount: 120000,
      amount_paid: 50000,
      payment_status: 'partially_paid',
      tracking_only: true,
    });
    expect(payload.payment_tracking).not.toHaveProperty('wallet_id');
    expect(payload.payment_tracking).not.toHaveProperty('gateway_charge_id');
  });

  it('shows visa/passport concern when signal is present', () => {
    mockStore.result_validation = {
      readiness: {
        ...READINESS,
        signals: { visa_concerns_present: true },
      },
    };
    render(<OpsPanel trip={null} />);
    expect(screen.getByTestId('ops-signal-visa-concern')).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Phase 4C: Extraction apply flow tests
// ---------------------------------------------------------------------------

describe('OpsPanel extraction apply flow', () => {
  const DOC_ID = 'doc_abc123';

  /** Setup a trip with booking data, an accepted document, and an extraction. */
  function setupExtractionScene() {
    mockStore.result_validation = { readiness: READINESS };
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
