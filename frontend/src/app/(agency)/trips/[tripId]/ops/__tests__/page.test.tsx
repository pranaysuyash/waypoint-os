import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TripContextProvider } from '@/contexts/TripContext';
import type { Trip } from '@/lib/api-client';
import OpsPageClient from '../PageClient';

// OpsPanel is a large component — stub it to test the page shell in isolation
vi.mock('@/app/(agency)/workbench/OpsPanel', () => ({
  default: ({ trip }: { trip: Trip | null }) => (
    <div data-testid="ops-panel-stub">
      {trip ? `OpsPanel for ${trip.id}` : 'No trip'}
    </div>
  ),
}));

const TRIP: Trip = {
  id: 'TRIP-OPS-1',
  destination: 'Maldives',
  type: 'Honeymoon',
  state: 'green',
  age: '1h',
  createdAt: '2026-05-14T10:00:00Z',
  updatedAt: '2026-05-14T10:00:00Z',
  stage: 'proposal',
} as Trip;

function renderWithContext(trip: Trip | null = TRIP, tripId = 'TRIP-OPS-1') {
  return render(
    <TripContextProvider value={{ tripId, trip, isLoading: false, error: null, refetchTrip: vi.fn(), replaceTrip: vi.fn() }}>
      <OpsPageClient />
    </TripContextProvider>,
  );
}

const BANNER_KEY = 'waypoint:ops-migration-banner-dismissed:v1';

// Mock next/link and getTripRoute for the stage-gate path
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe('Trip Workspace Ops page', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders stage-gate fallback for non-proposal/booking trip', () => {
    render(
      <TripContextProvider value={{
        tripId: 'TRIP-OPS-1',
        trip: { ...TRIP, stage: 'intake' } as Trip,
        isLoading: false, error: null, refetchTrip: vi.fn(), replaceTrip: vi.fn(),
      }}>
        <OpsPageClient />
      </TripContextProvider>,
    );
    expect(screen.getByTestId('ops-stage-gate')).toBeInTheDocument();
    expect(screen.queryByTestId('ops-panel-stub')).not.toBeInTheDocument();
  });

  it('renders stage-gate fallback for discovery-stage trip with link back to intake', () => {
    render(
      <TripContextProvider value={{
        tripId: 'TRIP-OPS-1',
        trip: { ...TRIP, stage: 'discovery' } as Trip,
        isLoading: false, error: null, refetchTrip: vi.fn(), replaceTrip: vi.fn(),
      }}>
        <OpsPageClient />
      </TripContextProvider>,
    );
    expect(screen.getByTestId('ops-stage-gate')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /return to intake/i }))
      .toHaveAttribute('href', '/trips/TRIP-OPS-1/intake');
  });

  it('renders OpsPanel for the current trip', () => {
    renderWithContext();
    expect(screen.getByTestId('ops-panel-stub')).toBeInTheDocument();
    expect(screen.getByText('OpsPanel for TRIP-OPS-1')).toBeInTheDocument();
  });

  it('renders nothing when trip is null', () => {
    const { container } = renderWithContext(null);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing when tripId is null', () => {
    const { container } = render(
      <TripContextProvider value={{ tripId: null, trip: null, isLoading: false, error: null, refetchTrip: vi.fn(), replaceTrip: vi.fn() }}>
        <OpsPageClient />
      </TripContextProvider>,
    );
    expect(container).toBeEmptyDOMElement();
  });

  describe('migration banner', () => {
    it('shows migration banner on first visit', () => {
      renderWithContext();
      expect(screen.getByText(/Booking operations have moved here from Workbench/i)).toBeInTheDocument();
    });

    it('hides migration banner when already dismissed', () => {
      localStorage.setItem(BANNER_KEY, '1');
      renderWithContext();
      expect(screen.queryByText(/Booking operations have moved here from Workbench/i)).not.toBeInTheDocument();
    });

    it('dismisses banner and persists dismissal', () => {
      renderWithContext();
      expect(screen.getByText(/Booking operations have moved here from Workbench/i)).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /dismiss/i }));

      expect(screen.queryByText(/Booking operations have moved here from Workbench/i)).not.toBeInTheDocument();
      expect(localStorage.getItem(BANNER_KEY)).toBe('1');
    });
  });
});
