import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TripCard } from '../TripCard';
import type { InboxTrip } from '@/types/governance';

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

const mockTrip: InboxTrip = {
  id: 'TRIP-123',
  reference: 'REF-123',
  destination: 'Bali',
  tripType: 'Leisure',
  partySize: 4,
  dateWindow: 'June 2026',
  value: 15000,
  priority: 'high',
  priorityScore: 75,
  stage: 'intake',
  stageNumber: 1,
  assignedTo: 'agent-1',
  assignedToName: 'Alex Agent',
  submittedAt: '2026-04-23',
  lastUpdated: '2026-04-23',
  daysInCurrentStage: 6,
  slaStatus: 'at_risk',
  customerName: 'Sharma Family',
  flags: ['high_value', 'needs_clarification'],
};

describe('TripCard', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  it('renders the lead summary', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Bali leisure trip')).toBeInTheDocument();
    expect(screen.getByText('Sharma Family · 4 pax · Jun 2026')).toBeInTheDocument();
  });

  it('shows the primary work-order signals', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Needs details')).toBeInTheDocument();
    expect(screen.getByText('Assigned to Alex Agent')).toBeInTheDocument();
    expect(screen.getByText('SLA due soon')).toBeInTheDocument();
    expect(screen.getByText('Budget $15.0k')).toBeInTheDocument();
    expect(screen.getByText('Next: review customer details before planning.')).toBeInTheDocument();
  });

  it('keeps the same hierarchy across view profiles', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} viewProfile='teamLead' />);

    expect(screen.getByText('Needs details')).toBeInTheDocument();
    expect(screen.getByText('Assigned to Alex Agent')).toBeInTheDocument();
    expect(screen.getByText('SLA due soon')).toBeInTheDocument();
  });

  it('collapses duplicate missing-info tags into one visible pill', () => {
    render(
      <TripCard
        trip={{
          ...mockTrip,
          assignedTo: undefined,
          assignedToName: undefined,
          flags: ['incomplete', 'needs_clarification', 'details_unclear', 'unassigned'],
        }}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Needs details')).toBeInTheDocument();
    expect(screen.getByText('Unassigned')).toBeInTheDocument();
    expect(screen.queryByText('details unclear')).not.toBeInTheDocument();
    expect(screen.queryByText('needs clarification')).not.toBeInTheDocument();
  });

  it('shows a friendly reference instead of the raw internal id', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Inquiry Ref: REF-123')).toBeInTheDocument();
    expect(screen.queryByText('TRIP-123')).not.toBeInTheDocument();
  });

  it('shows budget missing instead of fake zero budget precision', () => {
    render(<TripCard trip={{ ...mockTrip, value: 0, flags: ['incomplete', 'needs_clarification', 'unassigned'] }} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Budget missing')).toBeInTheDocument();
    expect(screen.getByText('Next: confirm budget and trip details.')).toBeInTheDocument();
  });

  it('renders an explicit Review Lead action for inspection', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByRole('link', { name: /review lead/i })).toHaveAttribute(
      'href',
      '/trips/TRIP-123/intake'
    );
  });

  it('calls onSelect when the checkbox is clicked', () => {
    const onSelect = vi.fn();
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('checkbox'));
    expect(onSelect).toHaveBeenCalledWith('TRIP-123', true);
  });
});
