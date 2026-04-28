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
    expect(container.querySelector('img[src="/brand/waypoint-logo-compass.svg"]')).toBeInTheDocument();
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

  it('renders the itinerary checker landing page with upload-first framing', () => {
    render(<ItineraryCheckerPage />);

    expect(
      screen.getByRole('heading', { name: /Find what your travel plan missed/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Upload\. Analyze\. Travel confident\./i).length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Things worth discussing before you finalize\./i).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByRole('link', { name: /Start free analysis/i })[0],
    ).toHaveAttribute('href', '/itinerary-checker#upload');
    expect(screen.getByRole('link', { name: /Try notebook mode/i })).toHaveAttribute(
      'href',
      '#notebook',
    );
  });

  it('itinerary checker hero upload card is labeled as a sample preview, not a real upload form', () => {
    const { container } = render(<ItineraryCheckerPage />);

    // The hero upload zone must not be a real <form> — no submit or action
    const forms = container.querySelectorAll('form');
    const heroUploadForms = Array.from(forms).filter(
      (f) => f.getAttribute('action') !== null || f.querySelector('input[type="submit"]') !== null,
    );
    expect(heroUploadForms).toHaveLength(0);

    // The card kicker must explicitly label it as a sample preview
    expect(screen.getByText('Sample preview')).toBeInTheDocument();

    // The primary CTA in the hero upload card directs users to the notebook, not a live upload
    expect(screen.getByRole('link', { name: /Try it in notebook mode/i })).toHaveAttribute(
      'href',
      '#notebook',
    );
  });

  it('itinerary checker has a data-handling privacy statement', () => {
    const { container } = render(<ItineraryCheckerPage />);

    const privacyEl = container.querySelector('[data-testid="privacy-statement"]');
    expect(privacyEl).toBeInTheDocument();
    expect(privacyEl?.textContent).toMatch(/not stored/i);
    expect(privacyEl?.textContent).toMatch(/not.*shared/i);
    expect(privacyEl?.textContent).toMatch(/session/i);

    // The privacy ProofChip must also surface this claim visibly
    expect(screen.getByText(/Not stored · Not shared · Session only/i)).toBeInTheDocument();
  });

  it('enables the notebook checker once trip context is provided', () => {
    render(<ItineraryCheckerPage />);

    const button = screen.getByRole('button', { name: /Start notebook check/i });
    expect(button).toBeDisabled();

    fireEvent.change(
      screen.getByPlaceholderText(/Paste a rough itinerary/i),
      {
        target: {
          value:
            'Paris to Rome in May, hotel near Termini, airport transfer on arrival, Vatican day, Amalfi day trip.',
        },
      },
    );

    expect(button).not.toBeDisabled();
  });
});
