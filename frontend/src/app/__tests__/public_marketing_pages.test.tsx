import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HomePage from '@/app/page';
import ItineraryCheckerPage from '@/app/(traveler)/itinerary-checker/page';
import {
  DESTINATION_CATALOG_REGISTRY,
  resolveDynamicInquiryFixture,
} from '@/components/marketing/departure-board/board-fixtures';
import {
  computeHomographyMatrix3d,
  type QuadCorners,
} from '@/components/marketing/departure-board/SplitFlapBoard';
import { api } from '@/lib/api-client';

// FND-0386: the departure-board landing now ships behind
// NEXT_PUBLIC_LANDING_VARIANT (default = committed V5). These tests exercise
// the board explicitly, so opt in regardless of ambient env.
process.env.NEXT_PUBLIC_LANDING_VARIANT = 'departure-board';

// Mock gsap — animations are irrelevant in JSDOM and cause timeouts
vi.mock('gsap', () => ({
  default: {
    context: (fn: () => void) => { fn(); return { revert: () => {} }; },
    to: () => {},
    fromTo: () => {},
    registerPlugin: () => {},
    set: () => {},
    timeline: () => ({ to: () => {}, fromTo: () => {}, kill: () => {} }),
    utils: { toArray: () => [] },
  },
}));

vi.mock('gsap/ScrollTrigger', () => ({
  ScrollTrigger: { getAll: () => [] },
}));

vi.mock('@/lib/api-client', () => {
  const api = {
    post: vi.fn().mockResolvedValue({
      run_id: 'run_test',
      state: 'completed',
      trip_id: 'trip_public_test',
      stage: 'discovery',
      operating_mode: 'normal_intake',
      agency_id: 'waypoint-hq',
      created_at: '2026-05-01T00:00:00.000Z',
      started_at: '2026-05-01T00:00:00.000Z',
      completed_at: '2026-05-01T00:00:02.000Z',
      total_ms: 2000,
      steps_completed: ['intake'],
      events: [],
      validation: {
        overall_score: 81,
        public_checker_live_checks: {
          destination: 'Hong Kong',
          climate: {
            precipitation_mm_avg: 120,
            wind_kmh_avg: 14,
          },
          current_conditions: {
            current: {
              temperature_c: 31.2,
              apparent_temperature_c: 36.4,
              wind_kmh: 18,
            },
          },
          signals: ['seasonal humidity', 'current heat'],
          hard_blockers: [],
          soft_blockers: ['Current weather is warm and humid.'],
          source: 'open-meteo',
        },
      },
      decision_state: 'PROCEED_TRAVELER_SAFE',
      follow_up_questions: [],
      hard_blockers: [],
      soft_blockers: [],
      packet: {
        public_checker_live_checks: {
          destination: 'Hong Kong',
          climate: {
            precipitation_mm_avg: 120,
            wind_kmh_avg: 14,
          },
          current_conditions: {
            current: {
              temperature_c: 31.2,
              apparent_temperature_c: 36.4,
              wind_kmh: 18,
            },
          },
          signals: ['seasonal humidity', 'current heat'],
          hard_blockers: [],
          soft_blockers: ['Current weather is warm and humid.'],
          source: 'open-meteo',
        },
      },
    }),
  };

  return { api };
});

describe('public marketing pages', () => {
  it('renders the B2B landing page copy, interactive departure board, and CTA surfaces', () => {
    render(<HomePage />);

    expect(screen.getAllByText(/WAYPOINT/i).length).toBeGreaterThan(0);
    expect(
      screen.getByRole('heading', {
        name: /Every inquiry\.\s*Under control\./i,
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', {
        name: /Turn raw trip notes into quote-ready briefs/i,
        level: 2,
      }),
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByRole('link', { name: /Create workspace/i })
        .every((link) => link.getAttribute('href') === '/signup'),
    ).toBe(true);
    expect(
      screen.getByRole('img', { name: /Waypoint Brushed Steel Departure Board Monument/i }),
    ).toBeInTheDocument();
    expect(screen.getByTestId('see-it-work-cta')).toBeInTheDocument();
    expect(screen.getByTestId('inquiry-switcher-dock')).toBeInTheDocument();
  });

  it('supports interactive departure board modes and destination switching', () => {
    render(<HomePage />);

    // Switch inquiry from Italy -> Japan -> Morocco
    fireEvent.click(screen.getByTestId('inquiry-pill-japan'));
    expect(screen.getByRole('img', { name: /JPN luggage tag/i })).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('inquiry-pill-morocco'));
    expect(screen.getByRole('img', { name: /MAR luggage tag/i })).toBeInTheDocument();

    // Trigger Frame 2 Voice Ingest state
    fireEvent.click(screen.getByTestId('mode-toggle-voice-ingest'));
    expect(
      screen.getByRole('heading', { name: /From inquiry\s*to itinerary\./i, level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByTestId('incoming-request-voice-card')).toBeInTheDocument();
    expect(screen.getByTestId('voice-workflow-status-card')).toHaveTextContent(/Dates Need Clarity/i);

    // Switch destination directly inside the Voice Card (Morocco -> Japan) and verify quote flips
    fireEvent.click(screen.getByTestId('voice-switch-japan'));
    expect(screen.getByTestId('incoming-request-voice-card')).toHaveTextContent(/Two of us want to do Japan for 14 days/i);

    // Trigger Frame 3 Provenance & Brief X-Ray state
    fireEvent.click(screen.getByTestId('mode-toggle-provenance'));
    expect(
      screen.getByRole('heading', { name: /See how it\s*organizes\s*the request\./i, level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByTestId('provenance-svg-wires')).toBeInTheDocument();
    expect(screen.getByTestId('structured-brief-drawer')).toBeInTheDocument();

    // Switch destination directly inside the Brief Drawer (Japan -> Morocco) and verify brief cards flip
    fireEvent.click(screen.getByTestId('brief-switch-morocco'));
    expect(screen.getByTestId('brief-card-destination')).toHaveTextContent(/Morocco/i);

    // Clicking the Dates row card inside the brief drawer confirms the dates on the board & brief
    expect(screen.getByTestId('brief-card-dates')).toHaveTextContent(/Needs confirmation/i);
    fireEvent.click(screen.getByTestId('brief-card-dates'));
    expect(screen.getByTestId('brief-card-dates')).toHaveTextContent(/Confirmed/i);

    // Trigger Live Dynamic Catalog & Free-Text Inquiry Drawer (completes §6.1 dynamic capability)
    fireEvent.click(screen.getByTestId('mode-toggle-custom-inquiry'));
    expect(screen.getByTestId('dynamic-inquiry-popover')).toBeInTheDocument();
    fireEvent.change(screen.getByTestId('dynamic-inquiry-input'), {
      target: { value: '5 travelers to Greece for 12 days in June' },
    });
    fireEvent.click(screen.getByTestId('dynamic-inquiry-submit'));
    expect(screen.getByRole('button', { name: /DESTINATION: Greece/i })).toBeInTheDocument();
  });

  it('solves exact 8-DOF 2D projective homography mapping canonical row corners to perspective quad corners within < 1e-6 px (Tier 2, S3)', () => {
    const w = 477;
    const h = 82;
    const quad: QuadCorners = {
      tl: [881, 272],
      tr: [1358, 244],
      br: [1358, 333],
      bl: [881, 351],
    };

    const matrixStr = computeHomographyMatrix3d(w, h, quad);
    expect(matrixStr.startsWith('matrix3d(')).toBe(true);
    const nums = matrixStr
      .replace(/^matrix3d\(|\)$/g, '')
      .split(',')
      .map((s) => Number.parseFloat(s.trim()));
    expect(nums).toHaveLength(16);

    // Project (u, v, 0, 1) through the column-major 4x4 CSS matrix3d:
    const projectPoint = (u: number, v: number): [number, number] => {
      const xPrime = nums[0] * u + nums[4] * v + nums[12];
      const yPrime = nums[1] * u + nums[5] * v + nums[13];
      const wPrime = nums[3] * u + nums[7] * v + nums[15];
      return [xPrime / wPrime, yPrime / wPrime];
    };

    const pTL = projectPoint(0, 0);
    const pTR = projectPoint(w, 0);
    const pBR = projectPoint(w, h);
    const pBL = projectPoint(0, h);

    expect(Math.hypot(pTL[0] - quad.tl[0], pTL[1] - quad.tl[1])).toBeLessThan(1e-6);
    expect(Math.hypot(pTR[0] - quad.tr[0], pTR[1] - quad.tr[1])).toBeLessThan(1e-6);
    expect(Math.hypot(pBR[0] - quad.br[0], pBR[1] - quad.br[1])).toBeLessThan(1e-6);
    expect(Math.hypot(pBL[0] - quad.bl[0], pBL[1] - quad.bl[1])).toBeLessThan(1e-6);

    // S3 Mutation Sensitivity Proof: a 1-DOF skewY(-2.85deg) approximation preserves vertical height (82px) on both ends,
    // whereas the true perspective cavity expands from 79px on the left to 89px on the right (10px foreshortening delta)
    // and leaves a > 2.7px corner registration error at BR:
    const leftEdgeHeight = quad.bl[1] - quad.tl[1];
    const rightEdgeHeight = quad.br[1] - quad.tr[1];
    expect(rightEdgeHeight - leftEdgeHeight).toBe(10);
    const skewRad = (-2.85 * Math.PI) / 180;
    const skewBR_Y = quad.tl[1] + h + w * Math.tan(skewRad);
    expect(Math.abs(skewBR_Y - quad.br[1])).toBeGreaterThan(2.5);
  });

  it('dynamically resolves catalog destinations and free-text inquiries into split-flap fixtures', () => {
    expect(DESTINATION_CATALOG_REGISTRY.length).toBeGreaterThanOrEqual(12);

    // Every catalog destination resolves with its own IATA code, default party size, duration, and voice quote
    const swissPreset = resolveDynamicInquiryFixture('Switzerland');
    expect(swissPreset.pillTitle).toBe('Switzerland');
    expect(swissPreset.tagCode).toBe('CHE');
    expect(swissPreset.rows[1].cells.map((c) => c.topText).join('')).toBe('4 TRAVELERS ');
    expect(swissPreset.rows[2].cells.map((c) => c.topText).join('')).toBe('9  DAYS ');
    expect(swissPreset.voiceNote.quote).toMatch(/panoramic rail and Zermatt chalets/i);

    const greeceFixture = resolveDynamicInquiryFixture(
      'Family of 5 looking at 12 days in Greece next June, islands + private yacht, dates flexible',
    );
    expect(greeceFixture.pillTitle).toBe('Greece');
    expect(greeceFixture.tagCode).toBe('GRC');
    expect(greeceFixture.rows[0].cells.map((c) => c.topText).join('')).toBe('GREECE  ');
    expect(greeceFixture.rows[1].cells.map((c) => c.topText).join('')).toBe('5 TRAVELERS ');
    expect(greeceFixture.rows[2].cells.map((c) => c.topText).join('')).toBe('12 DAYS ');
    expect(greeceFixture.rows[4].cells.map((c) => c.topText).join('')).toBe('ISLAND + YACHT ');
    expect(greeceFixture.briefSummary[3].status).toBe('needs_confirmation');

    const customFixture = resolveDynamicInquiryFixture(
      'Planning a honeymoon to Patagonia for 2 weeks in November',
    );
    expect(customFixture.pillTitle).toBe('Patagonia');
    expect(customFixture.rows[0].cells).toHaveLength(8);
    expect(customFixture.rows[1].cells.map((c) => c.topText).join('')).toBe('2 TRAVELERS ');
    expect(customFixture.rows[2].cells.map((c) => c.topText).join('')).toBe('14 DAYS ');

    // First-principles natural-language parser test for lowercase "2 travelers for dubai around june next year"
    const dubaiFixture = resolveDynamicInquiryFixture(
      '2 travelers for dubai around june next year',
    );
    expect(dubaiFixture.pillTitle).toBe('Dubai');
    expect(dubaiFixture.tagCode).toBe('DXB');
    expect(dubaiFixture.hangingTagImage).toBe('/landing/departure-board/tag-blank-gold.png');
    expect(dubaiFixture.rows[0].cells.map((c) => c.topText).join('')).toBe('DUBAI   ');
    expect(dubaiFixture.rows[0].photoFlap?.src).toBe('/landing/departure-board/catalog/photo-dubai-1.png');
    expect(dubaiFixture.rows[1].cells.map((c) => c.topText).join('')).toBe('2 TRAVELERS ');
    expect(dubaiFixture.rows[1].fact.basis).toBe('explicit');
    expect(dubaiFixture.rows[2].cells.map((c) => c.topText).join('')).toBe('7  DAYS ');
    expect(dubaiFixture.rows[2].fact.basis).toBe('inferred');
    expect(dubaiFixture.rows[2].photoFlap?.src).toBe('/landing/departure-board/catalog/photo-dubai-2.png');
    expect(dubaiFixture.rows[3].confirmedValueLabel).toBe('Jun 10 – Jun 16 (Confirmed)');
    expect(dubaiFixture.rows[4].cells.map((c) => c.topText).join('')).toBe('LUXURY + DESERT');
    expect(dubaiFixture.voiceNote.quote).toMatch(/Looking at Dubai for 2 travelers for about 7 days in June next year/i);
    expect(dubaiFixture.briefSummary[0].thumbUrl).toBe('/landing/departure-board/catalog/photo-dubai-1.png');
    expect(dubaiFixture.briefSummary[4].thumbUrl).toBe('/landing/departure-board/catalog/photo-dubai-2.png');

    // Verify all 15 catalog destinations have distinct supporting photography and synchronized randomized numbers
    expect(DESTINATION_CATALOG_REGISTRY.length).toBe(15);
    const seenPhoto1 = new Set<string>();
    for (const entry of DESTINATION_CATALOG_REGISTRY) {
      expect(entry.destinationPhotoUrl).toBeTruthy();
      expect(entry.durationPhotoUrl).toBeTruthy();
      seenPhoto1.add(entry.destinationPhotoUrl);

      const varied = resolveDynamicInquiryFixture(entry.displayName, {
        randomizeNumbers: true,
        variationSeed: 1,
      });
      const expectedTravelers = varied.briefSummary[1].value;
      const expectedDuration = varied.briefSummary[2].value;
      expect(varied.rows[1].fact.value).toBe(expectedTravelers);
      expect(varied.rows[2].fact.value).toBe(expectedDuration);
      expect(varied.voiceNote.quote).toContain(entry.displayName);
      expect(varied.voiceNote.quote).toContain(expectedDuration);
    }
    expect(seenPhoto1.size).toBe(15);
  });

  it('compiles a live custom inquiry ("2 travelers for dubai around june next year") on the homepage hero', () => {
    render(<HomePage />);

    const input = screen.getByTestId('hero-custom-inquiry-input');
    const submit = screen.getByTestId('hero-custom-inquiry-submit');

    fireEvent.change(input, {
      target: { value: '2 travelers for dubai around june next year' },
    });
    fireEvent.click(submit);

    expect(screen.getByTestId('board-hanging-iata-tag')).toHaveAttribute('data-iata-code', 'DXB');
    expect(screen.getByTestId('hero-live-sync-badge')).toHaveTextContent('DXB · 2 travelers · 7 days');

    // Verify Fold 2, Fold 3, and Fold 4 interactive controls synchronize with the active case
    const fold2Input = screen.getByTestId('fold2-custom-inquiry-input');
    const fold2Submit = screen.getByTestId('fold2-custom-inquiry-submit');
    fireEvent.change(fold2Input, {
      target: { value: '4 travelers to Switzerland for 9 days in July' },
    });
    fireEvent.click(fold2Submit);
    expect(screen.getByTestId('board-hanging-iata-tag')).toHaveAttribute('data-iata-code', 'CHE');

    // Fold 3 provenance trace slot and epistemic latch toggle
    fireEvent.click(screen.getByTestId('fold3-trace-slot-destination'));
    fireEvent.click(screen.getByTestId('fold3-latch-toggle'));
    expect(screen.getByTestId('fold3-latch-toggle')).toHaveTextContent(/Reset Hold/i);

    // Fold 3 destination flight deck pass card flips the entire page
    fireEvent.click(screen.getByTestId('fold3-gallery-card-dubai'));
    expect(screen.getByTestId('board-hanging-iata-tag')).toHaveAttribute('data-iata-code', 'DXB');
  });

  it('homepage makes the agency workflow benefits explicit', () => {
    render(<HomePage />);

    expect(
      screen.getByRole('heading', { name: /It helps teams answer faster, quote cleaner, and keep owners out of every tiny decision/i }),
    ).toBeInTheDocument();
  });

  it('homepage hero frames the product as an agency brief and quoting surface', () => {
    render(<HomePage />);

    expect(
      screen.getByText(/Waypoint helps boutique travel agencies turn the notes they already have, whether from calls, emails, WhatsApp messages, or copied itineraries/i),
    ).toBeInTheDocument();
  });

  it('homepage names concrete workflow improvements', () => {
    render(<HomePage />);

    expect(screen.getByText(/Extract dates, party size, budget, pace, and trip type from messy messages/i)).toBeInTheDocument();
    expect(screen.getByText(/Surface the missing facts that change itinerary quality before anyone quotes/i)).toBeInTheDocument();
    expect(screen.getByText(/Protect owner time by showing what needs a human decision and what does not/i)).toBeInTheDocument();
  });

  it('renders the itinerary checker landing page with tool-first upload framing', () => {
    render(<ItineraryCheckerPage />);

    // Hero heading
    expect(
      screen.getByRole('heading', { name: /Check your itinerary before you book/i }),
    ).toBeInTheDocument();

    // Mode tabs present — labels follow the unslop rewrite of PageClient
    // (17684bee): 'Upload PDF / file', 'Paste plan / ChatGPT', 'Screenshot'.
    expect(screen.getByRole('button', { name: /Upload PDF \/ file/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Paste plan \/ ChatGPT/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Screenshot/i })).toBeInTheDocument();

    // Upload drop zone — 57113daf rebuilt it as a labeled `region` (it wraps
    // interactive children: source picker, consent toggle, choose-file button),
    // so `button` semantics on the container would be nested-interactive and
    // wrong. The region keeps its aria-label as the accessible name; actual
    // upload activation lives in the real button inside it. The card opens on
    // the paste tab (17684bee default), so the file tab must be selected for
    // the region to mount.
    fireEvent.click(screen.getByRole('button', { name: /Upload PDF \/ file/i }));
    expect(screen.getByRole('region', { name: /Upload itinerary/i })).toBeInTheDocument();
  });

  it('itinerary checker upload zone is a real interactive tool, not a sample preview', () => {
    const { container } = render(<ItineraryCheckerPage />);

    // No submit-action forms (upload is handled via drag-drop / button, not a form action)
    const formsWithAction = Array.from(container.querySelectorAll('form')).filter(
      (f) => f.getAttribute('action') !== null || f.querySelector('input[type="submit"]') !== null,
    );
    expect(formsWithAction).toHaveLength(0);

    // Should NOT say "sample preview" - the new design IS the real tool
    expect(screen.queryByText('Sample preview')).not.toBeInTheDocument();

    // Trust chips confirming it is free and privacy-safe
    expect(screen.getByText(/Free to use/i)).toBeInTheDocument();
    expect(screen.getByText(/No sign-up required/i)).toBeInTheDocument();
    expect(screen.getByText(/Consent-based storage/i)).toBeInTheDocument();
  });

  it('itinerary checker surfaces data-handling privacy assurance in trust chips', () => {
    render(<ItineraryCheckerPage />);

    // Trust chips visible beneath the upload zone
    expect(screen.getByText(/Consent-based storage/i)).toBeInTheDocument();
    expect(screen.getByText(/No sign-up required/i)).toBeInTheDocument();
    expect(screen.getByText(/Free to use/i)).toBeInTheDocument();
  });

  it('enables the paste analyze button once enough text is provided', () => {
    render(<ItineraryCheckerPage />);

    // Switch to paste mode (tab label from the 17684bee unslop rewrite)
    fireEvent.click(screen.getByRole('button', { name: /Paste plan \/ ChatGPT/i }));

    const textarea = screen.getByRole('textbox', { name: 'Your itinerary' });
    expect(textarea).toBeInTheDocument();

    const analyzeBtn = screen.getByRole('button', { name: /^Check my itinerary$/i });
    expect(analyzeBtn).toBeDisabled();

    fireEvent.change(textarea, {
      target: {
        value: 'Paris to Rome in May, hotel near Termini, airport transfer on arrival, Vatican day.',
      },
    });

    expect(analyzeBtn).not.toBeDisabled();
  });

  it('accepts a text upload and reports the destination evidence returned for it', async () => {
    render(<ItineraryCheckerPage />);

    // The card opens on the paste tab; switch to the file tab to mount the
    // drop zone and its file input (17684bee default-tab redesign).
    fireEvent.click(screen.getByRole('button', { name: /Upload PDF \/ file/i }));
    const fileInput = screen.getByLabelText('Upload itinerary file');

    const note = 'Hong Kong in August for 2 elders and 1 child.';
    const file = new File([note], 'trip.txt', {
      type: 'text/plain',
    });

    // jsdom's File omits Blob.text(), which browsers provide for text uploads.
    Object.defineProperty(file, 'text', { value: () => Promise.resolve(note) });
    await userEvent.upload(fileInput, file);

    expect(await screen.findByRole('heading', { name: 'Your itinerary check' })).toBeInTheDocument();
    expect(screen.getByText('Destination evidence')).toBeInTheDocument();
    expect(screen.getByText(/Current weather is warm and humid/i)).toBeInTheDocument();
    expect(screen.queryByText(/No issues were flagged/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Critical')).not.toBeInTheDocument();
    expect(screen.getByText(/Current weather: 31.2°C now/i)).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/api/public-checker/run', expect.objectContaining({
      itinerary_text: note,
      retention_consent: false,
    }), { retry: 0 });
  });

  it('shows the evidence status of each attempted public place lookup', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      run_id: 'run_place', state: 'completed', trip_id: 'trip_place', decision_state: 'PROCEED_TRAVELER_SAFE',
      packet: {
        facts: { destination_candidates: { value: ['Goa'] } },
        public_checker_entity_checks: [
          { name: 'Hotel A', status: 'unverified', reason: 'source_unavailable', message: 'Lookup could not run.' },
          { name: 'Hotel B', status: 'unverified', reason: 'lodging_match_uncertain', message: 'Record is not listed as lodging.' },
          { name: 'Hotel C', status: 'not_found', message: 'The lookup returned no matches.' },
        ],
      },
    });
    render(<ItineraryCheckerPage />);
    fireEvent.change(screen.getByRole('textbox', { name: 'Your itinerary' }), {
      target: { value: 'We are planning a Goa trip and comparing three hotels.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^Check my itinerary$/i }));
    expect(await screen.findByText('Source unavailable')).toBeVisible();
    expect(screen.getByText('Lodging match uncertain')).toBeVisible();
    expect(screen.getByText('No public record')).toBeVisible();
    expect(screen.queryByText(/No issues were flagged/i)).not.toBeInTheDocument();
  });

  it('keeps the submitted text available when the run has no usable packet', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ run_id: 'run_empty', state: 'blocked', packet: {} });
    render(<ItineraryCheckerPage />);
    const note = 'Singapore and Marina Bay this October for five travelers.';
    const input = screen.getByRole('textbox', { name: 'Your itinerary' });
    fireEvent.change(input, { target: { value: note } });
    fireEvent.click(screen.getByRole('button', { name: /^Check my itinerary$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Itinerary check unavailable');
    expect(input).toHaveValue(note);
    expect(screen.getByRole('button', { name: /^Check my itinerary$/i })).toBeEnabled();
    expect(screen.queryByText('Itinerary report')).not.toBeInTheDocument();
  });

  it('leads with actionable findings and asks for the return date once', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      run_id: 'run_goa', state: 'completed', trip_id: 'trip_goa', decision_state: 'ASK_FOLLOWUP',
      packet: {
        public_checker_return_date_pending: true,
        itinerary_feasibility_findings: [
          { flag: 'overnight_hotel_arrival', message: 'Confirm the room will be held.', details: { authority: 'advisory', title: 'Confirm late hotel arrival' } },
          { flag: 'goa_day_pacing', message: 'Check the transfer from Collem.', details: { authority: 'advisory', title: 'Check whether all three stops fit' } },
        ],
      },
    });
    render(<ItineraryCheckerPage />);
    fireEvent.click(screen.getByRole('button', { name: /Paste plan \/ ChatGPT/i }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Your itinerary' }), {
      target: { value: 'Our Goa flight arrives after midnight and the return date is open.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^Check my itinerary$/i }));
    expect(await screen.findByRole('heading', { name: '2 itinerary details to confirm' })).toBeVisible();
    const returnDate = screen.getByText('Add your return date when you know it.');
    const pacing = screen.getByRole('heading', { name: 'Check whether all three stops fit' });
    expect(pacing.compareDocumentPosition(returnDate) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const summary = screen.getByText('Share findings summary', { selector: 'summary' }).parentElement!;
    expect(summary).toHaveTextContent('Confirm late hotel arrival');
    expect(summary).toHaveTextContent('Confirm the room will be held.');
    expect(summary).toHaveTextContent('Check the transfer from Collem.');
    expect(summary).toHaveTextContent('Ask the hotel reservations team');
    expect(summary).toHaveTextContent('Ask your travel agent or local tour operator');
    expect(summary).not.toHaveTextContent('Our Goa flight arrives after midnight');

  });

  it('shows traveler-safe wording for thin extraction results', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      run_id: 'run_thin',
      state: 'blocked',
      trip_id: 'trip_thin',
      stage: 'discovery',
      operating_mode: 'normal_intake',
      agency_id: 'waypoint-hq',
      created_at: '2026-05-01T00:00:00.000Z',
      started_at: '2026-05-01T00:00:00.000Z',
      completed_at: '2026-05-01T00:00:02.000Z',
      total_ms: 2000,
      steps_completed: ['intake'],
      events: [],
      validation: {
        overall_score: 42,
      },
      decision_state: 'STOP_NEEDS_REVIEW',
      follow_up_questions: [],
      hard_blockers: ['extraction_quality'],
      soft_blockers: [],
      packet: { facts: {}, unknowns: [] },
    });

    render(<ItineraryCheckerPage />);

    fireEvent.click(screen.getByRole('button', { name: /Paste plan \/ ChatGPT/i }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Your itinerary' }), {
      target: {
        value: 'Fly to Singapore for 5 days with family in October. Need help checking the trip.',
      },
    });
    fireEvent.click(screen.getByRole('button', { name: /^Check my itinerary$/i }));

    expect(await screen.findByRole('heading', { name: 'Your check needs more details' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Correct or add trip details' })).toBeInTheDocument();
    expect(screen.getByText(/^We could not confidently read the key trip details from this plan yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/^extraction_quality$/i)).not.toBeInTheDocument();
  });

  it.each([
    ['nothing_booked', false],
    ['We have nothing booked yet.', true],
  ])('shows packet-derived understanding and respects booking evidence (%s)', async (excerpt, visible) => {
    vi.mocked(api.post).mockResolvedValueOnce({
      run_id: 'run_packet',
      state: 'blocked',
      trip_id: 'trip_packet',
      stage: 'discovery',
      operating_mode: 'normal_intake',
      agency_id: 'waypoint-hq',
      created_at: '2026-05-01T00:00:00.000Z',
      started_at: '2026-05-01T00:00:00.000Z',
      completed_at: '2026-05-01T00:00:02.000Z',
      total_ms: 2000,
      steps_completed: ['packet', 'validation'],
      events: [],
      validation: {
        overall_score: 42,
        errors: [
          {
            message: "Required field 'date_window' not present",
          },
        ],
        ambiguity_report: [
          {
            field: 'destination_candidates',
            raw_value: 'Singapore or Marina Bay',
          },
        ],
      },
      decision_state: 'STOP_NEEDS_REVIEW',
      follow_up_questions: [],
      hard_blockers: ['extraction_quality'],
      soft_blockers: [],
      packet: {
        facts: {
          destination_candidates: { value: ['Singapore', 'Marina Bay'] },
          party_size: { value: 5 },
          party_composition: { value: { adults: 2, elderly: 2, children: 1 } },
          trip_purpose: { value: 'family leisure' },
          traveler_plan: {
            value: 'nothing_booked', confidence: 0.85, authority_level: 'explicit_user', extraction_mode: 'direct_extract',
            evidence_refs: [{ evidence_type: 'text_span', excerpt, field_path: null }],
          },
          soft_preferences: { value: ['minimal long walks', 'one free afternoon for rest'] },
        },
        unknowns: [
          { field_name: 'date_window' },
          { field_name: 'origin_city' },
        ],
      },
    });

    render(<ItineraryCheckerPage />);

    fireEvent.click(screen.getByRole('button', { name: /Paste plan \/ ChatGPT/i }));
    fireEvent.change(screen.getByRole('textbox', { name: 'Your itinerary' }), {
      target: {
        value: 'Singapore family trip with grandparents and a toddler. Comfortable pace please.',
      },
    });
    fireEvent.click(screen.getByRole('button', { name: /^Check my itinerary$/i }));

    expect(await screen.findByText(/Trip Summary \(Extracted\)/i, {}, { timeout: 10_000 })).toBeInTheDocument();
    const readFacts = within(screen.getByLabelText('What we read from your itinerary'));
    expect(readFacts.getByText('Singapore, Marina Bay')).toBeInTheDocument();
    expect(screen.queryAllByText('Nothing booked yet')).toHaveLength(visible ? 1 : 0);
    expect(readFacts.getByText('5')).toBeInTheDocument();
    expect(screen.getByText(/family leisure/i)).toBeInTheDocument();
    expect(screen.getByText(/minimal long walks, one free afternoon for rest/i)).toBeInTheDocument();
    expect(screen.getByText(/What to clarify next/i)).toBeInTheDocument();
    expect(screen.getByText(/• Add travel dates\./i)).toBeInTheDocument();
    expect(screen.getByText(/Add departure city\./i)).toBeInTheDocument();
    expect(screen.getByText(/Clarify destination \(Singapore or Marina Bay\)\./i)).toBeInTheDocument();
  });
});
