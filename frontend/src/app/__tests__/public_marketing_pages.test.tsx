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
