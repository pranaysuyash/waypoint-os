import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import HomePage from '@/app/page';
import ItineraryCheckerPage from '@/app/itinerary-checker/page';

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
      screen.getByRole('heading', { name: /Test your plan before you book/i }),
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
      screen.getByRole('heading', { name: /Find what your travel plan missed/i }),
    ).toBeInTheDocument();

    // Mode tabs present
    expect(screen.getByRole('button', { name: /Upload file/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Paste itinerary/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Screenshot/i })).toBeInTheDocument();

    // Real upload button (not a link to a separate notebook section)
    expect(screen.getByRole('button', { name: /Choose file to upload/i })).toBeInTheDocument();
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
    expect(screen.getByText(/Analyzed then deleted/i)).toBeInTheDocument();
  });

  it('itinerary checker surfaces data-handling privacy assurance in trust chips', () => {
    render(<ItineraryCheckerPage />);

    // Trust chips visible beneath the upload zone
    expect(screen.getByText(/Analyzed then deleted/i)).toBeInTheDocument();
    expect(screen.getByText(/No sign-up required/i)).toBeInTheDocument();
    expect(screen.getByText(/Free to use/i)).toBeInTheDocument();
  });

  it('enables the paste analyze button once enough text is provided', () => {
    render(<ItineraryCheckerPage />);

    // Switch to paste mode
    fireEvent.click(screen.getByRole('button', { name: /Paste itinerary/i }));

    const textarea = screen.getByPlaceholderText(/Paste your day-by-day plan here/i);
    expect(textarea).toBeInTheDocument();

    const analyzeBtn = screen.getByRole('button', { name: /Analyze My Itinerary/i });
    expect(analyzeBtn).toBeDisabled();

    fireEvent.change(textarea, {
      target: {
        value: 'Paris to Rome in May, hotel near Termini, airport transfer on arrival, Vatican day.',
      },
    });

    expect(analyzeBtn).not.toBeDisabled();
  });
});
