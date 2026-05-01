import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import HomePage from '@/app/page';
import ItineraryCheckerPage from '@/app/(traveler)/itinerary-checker/page';

vi.mock('@/hooks/useSpineRun', () => {
  const execute = vi.fn().mockResolvedValue({
    run_id: 'run_test',
    state: 'completed',
    trip_id: null,
    stage: 'discovery',
    operating_mode: 'normal_intake',
    agency_id: null,
    created_at: null,
    started_at: null,
    completed_at: null,
    total_ms: null,
    steps_completed: [],
    events: [],
    validation: null,
    packet: null,
    decision_state: 'PROCEED_TRAVELER_SAFE',
    follow_up_questions: [],
    hard_blockers: [],
    soft_blockers: [],
  });

  return {
    useSpineRun: () => ({
      execute,
      isLoading: false,
    }),
  };
});

describe('public marketing pages', () => {
  it('renders the B2B landing page copy and CTA surfaces', () => {
    const { container } = render(<HomePage />);

    expect(screen.getAllByText('Waypoint OS').length).toBeGreaterThan(0);
    expect(
      screen.getByRole('heading', {
        name: /Waypoint OS/i,
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('heading', {
        name: /The operating system for boutique travel agencies/i,
        level: 2,
      }),
    ).toBeInTheDocument();
    expect(
      screen
        .getAllByRole('link', { name: /Book a demo/i })
        .every((link) => link.getAttribute('href') === '/signup'),
    ).toBe(true);
    expect(
      screen.getByRole('link', { name: /Explore the product/i }),
    ).toHaveAttribute('href', '#product');
    expect(screen.getByRole('img', { name: /Waypoint OS/i })).toBeInTheDocument();
  });

  it('homepage wedge section has an actionable itinerary checker CTA', () => {
    render(<HomePage />);

    const checkerLink = screen.getByRole('link', { name: /Try the free itinerary checker/i });
    expect(checkerLink).toHaveAttribute('href', '/itinerary-checker');

    expect(
      screen.getByRole('heading', { name: /Bring your plan\. Get it scored/i }),
    ).toBeInTheDocument();
  });

  it('homepage productMoments name concrete capabilities', () => {
    render(<HomePage />);

    expect(screen.getByRole('heading', { name: /Intake normalization/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Risk question generation/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Owner review escalation/i })).toBeInTheDocument();
  });

  it('renders the itinerary checker landing page with tool-first upload framing', () => {
    render(<ItineraryCheckerPage />);

    // Hero heading
    expect(
      screen.getByRole('heading', { name: /Bring your plan\. Get it checked/i }),
    ).toBeInTheDocument();

    // Mode tabs present
    expect(screen.getByRole('button', { name: /Upload file/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Paste itinerary/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Screenshot/i })).toBeInTheDocument();

    // Real upload button (not a link to a separate notebook section)
    expect(screen.getByRole('button', { name: /Score my itinerary/i })).toBeInTheDocument();
  });

  it('itinerary checker upload zone is a real interactive tool, not a sample preview', () => {
    const { container } = render(<ItineraryCheckerPage />);

    // No submit-action forms (upload is handled via drag-drop / button, not a form action)
    const formsWithAction = Array.from(container.querySelectorAll('form')).filter(
      (f) => f.getAttribute('action') !== null || f.querySelector('input[type="submit"]') !== null,
    );
    expect(formsWithAction).toHaveLength(0);

    // Should NOT say "sample preview" — the new design IS the real tool
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

    // Switch to paste mode
    fireEvent.click(screen.getByRole('button', { name: /Paste itinerary/i }));

    const textarea = screen.getByPlaceholderText(/Paste your day-by-day plan here/i);
    expect(textarea).toBeInTheDocument();

    const analyzeBtn = screen.getByRole('button', { name: /Score My Itinerary/i });
    expect(analyzeBtn).toBeDisabled();

    fireEvent.change(textarea, {
      target: {
        value: 'Paris to Rome in May, hotel near Termini, airport transfer on arrival, Vatican day.',
      },
    });

    expect(analyzeBtn).not.toBeDisabled();
  });

  it('accepts a text upload and runs the scoring flow', async () => {
    const { container } = render(<ItineraryCheckerPage />);

    const fileInput = container.querySelector('input[type="file"]');
    expect(fileInput).toBeTruthy();

    const file = new File(['Hong Kong in August for 2 elders and 1 child.'], 'trip.txt', {
      type: 'text/plain',
    });

    fireEvent.change(fileInput as HTMLInputElement, {
      target: { files: [file] },
    });

    expect(await screen.findByText(/Live review/i)).toBeInTheDocument();
    expect(screen.getByText(/PROCEED_TRAVELER_SAFE/i)).toBeInTheDocument();
  });
});
