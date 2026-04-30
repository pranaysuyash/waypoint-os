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

    expect(screen.getByText('Bali')).toBeInTheDocument();
    expect(screen.getByText('Sharma Family')).toBeInTheDocument();
    expect(screen.getByText('At Risk')).toBeInTheDocument();
  });

  it('renders operational metrics for the default view', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Pax')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Dates')).toBeInTheDocument();
    expect(screen.getByText('June 2026')).toBeInTheDocument();
    expect(screen.getByText('Budget')).toBeInTheDocument();
    expect(screen.getByText('$15.0k')).toBeInTheDocument();
  });

  it('renders team lead metrics when specified', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} viewProfile='teamLead' />);

    expect(screen.getByText('Owner')).toBeInTheDocument();
    expect(screen.getByText('Alex Agent')).toBeInTheDocument();
    expect(screen.getByText('SLA')).toBeInTheDocument();
    expect(screen.getByText('At risk')).toBeInTheDocument();
    expect(screen.getByText('Priority')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('renders finance metrics when specified', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} viewProfile='finance' />);

    expect(screen.getAllByText('Budget').length).toBeGreaterThan(0);
    expect(screen.getByText('Priority')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('renders fulfillment metrics when specified', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} viewProfile='fulfillment' />);

    expect(screen.getByText('Dates')).toBeInTheDocument();
    expect(screen.getByText('Owner')).toBeInTheDocument();
    expect(screen.getByText('Pax')).toBeInTheDocument();
  });

  it('renders flags', () => {
    render(
      <TripCard
        trip={{ ...mockTrip, flags: ['incomplete', 'needs_clarification', 'details_unclear', 'unassigned'] }}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('incomplete')).toBeInTheDocument();
    expect(screen.getByText('needs clarification')).toBeInTheDocument();
    expect(screen.getByText('details unclear')).toBeInTheDocument();
    expect(screen.getByText('unassigned')).toBeInTheDocument();
  });

  it('shows a friendly reference instead of the raw internal id', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);

    expect(screen.getByText('Ref: REF-123')).toBeInTheDocument();
    expect(screen.queryByText('TRIP-123')).not.toBeInTheDocument();
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
