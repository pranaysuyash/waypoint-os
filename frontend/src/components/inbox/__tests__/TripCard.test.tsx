import { beforeEach, describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TripCard } from '../TripCard';
import type { InboxTrip } from '@/types/governance';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Mock localStorage for micro-labels
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

  it('renders destination and customer name', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Bali')).toBeInTheDocument();
    expect(screen.getByText('Sharma Family')).toBeInTheDocument();
  });

  it('renders stage badge', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Intake')).toBeInTheDocument();
  });

  it('renders contextual SLA badge', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    // 6 days in intake (24h SLA) = 600%
    expect(screen.getByText(/6d · 600% of SLA/)).toBeInTheDocument();
  });

  it('renders flags', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('high value')).toBeInTheDocument();
    expect(screen.getByText('needs clarification')).toBeInTheDocument();
  });

  it('renders operations metrics by default', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Pax')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('Budget')).toBeInTheDocument();
    expect(screen.getByText('$15.0k')).toBeInTheDocument();
    expect(screen.getByText('Dates')).toBeInTheDocument();
    expect(screen.getByText('June 2026')).toBeInTheDocument();
    expect(screen.getByText('Days')).toBeInTheDocument();
    expect(screen.getByText('6d')).toBeInTheDocument();
  });

  it('renders teamLead metrics when specified', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
        viewProfile="teamLead"
      />
    );

    expect(screen.getByText('Agent')).toBeInTheDocument();
    // Alex Agent appears in metrics row AND assignment badge in status footer
    expect(screen.getAllByText('Alex Agent')).toHaveLength(2);
    expect(screen.getByText('SLA')).toBeInTheDocument();
    expect(screen.getByText('at risk')).toBeInTheDocument();
    expect(screen.getByText('Score')).toBeInTheDocument();
    expect(screen.getByText('75')).toBeInTheDocument();
  });

  it('renders finance metrics when specified', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
        viewProfile="finance"
      />
    );

    expect(screen.getByText('Budget')).toBeInTheDocument();
    expect(screen.getByText('Stage')).toBeInTheDocument();
    expect(screen.getByText('Priority')).toBeInTheDocument();
  });

  it('renders fulfillment metrics when specified', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
        viewProfile="fulfillment"
      />
    );

    expect(screen.getByText('Dates')).toBeInTheDocument();
    expect(screen.getByText('Agent')).toBeInTheDocument();
    expect(screen.getByText('Stage')).toBeInTheDocument();
    expect(screen.getByText('Pax')).toBeInTheDocument();
  });

  it('shows unassigned when no agent', () => {
    const unassignedTrip = { ...mockTrip, assignedToName: undefined, assignedTo: undefined };
    render(
      <TripCard
        trip={unassignedTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('Unassigned')).toBeInTheDocument();
  });

  it('renders trip ID in footer', () => {
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText('TRIP-123')).toBeInTheDocument();
  });

  it('calls onSelect when checkbox clicked', () => {
    const onSelect = vi.fn();
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={onSelect}
      />
    );

    const checkbox = screen.getByRole('checkbox');
    checkbox.click();

    expect(onSelect).toHaveBeenCalledWith('TRIP-123', true);
  });

  it('shows micro-labels for new users', () => {
    // Visit count is 0 by default
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    // Should show "high attention" micro-label for high priority
    expect(screen.getByText(/high attention/)).toBeInTheDocument();
    // Should show "just arrived" micro-label for intake stage
    expect(screen.getByText(/just arrived/)).toBeInTheDocument();
    // Should show "approaching limit" micro-label for at_risk SLA
    expect(screen.getByText(/approaching limit/)).toBeInTheDocument();
  });

  it('hides micro-labels for experienced users', () => {
    // Set visit count above threshold
    localStorageMock.setItem('inbox_visit_count', '5');

    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    // Should NOT show micro-labels
    expect(screen.queryByText(/high attention/)).not.toBeInTheDocument();
    expect(screen.queryByText(/just arrived/)).not.toBeInTheDocument();
  });

  it('renders priority accent bar as top border with correct color', () => {
    const { container } = render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card).toBeInTheDocument();
    expect(card.style.borderTop).toContain('2px solid');
  });

  it('changes accent bar opacity when selected', () => {
    const { container } = render(
      <TripCard
        trip={mockTrip}
        isSelected={true}
        onSelect={vi.fn()}
      />
    );

    const card = container.firstChild as HTMLElement;
    expect(card.style.opacity).toBe('1');
  });

  it('renders breached SLA with red styling', () => {
    const breachedTrip = { ...mockTrip, slaStatus: 'breached' as const };
    render(
      <TripCard
        trip={breachedTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    // Should show contextual SLA
    expect(screen.getByText(/6d · 600% of SLA/)).toBeInTheDocument();
  });

  it('renders on-track SLA with green styling', () => {
    const onTrackTrip = { ...mockTrip, slaStatus: 'on_track' as const, daysInCurrentStage: 1 };
    render(
      <TripCard
        trip={onTrackTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByText(/1d · 100% of SLA/)).toBeInTheDocument();
  });

  it('shows Assign button for unassigned trip when onAssign provided', () => {
    const onAssign = vi.fn();
    const unassignedTrip = { ...mockTrip, assignedToName: undefined, assignedTo: undefined };
    render(
      <TripCard
        trip={unassignedTrip}
        isSelected={false}
        onSelect={vi.fn()}
        onAssign={onAssign}
      />
    );

    const assignButton = screen.getByText('Assign');
    expect(assignButton).toBeInTheDocument();
    fireEvent.click(assignButton);
    expect(onAssign).toHaveBeenCalledWith('TRIP-123');
  });

  it('does not show Assign button for assigned trip', () => {
    const onAssign = vi.fn();
    render(
      <TripCard
        trip={mockTrip}
        isSelected={false}
        onSelect={vi.fn()}
        onAssign={onAssign}
      />
    );

    expect(screen.queryByText('Assign')).not.toBeInTheDocument();
  });

  it('does not show Assign button when onAssign not provided', () => {
    const unassignedTrip = { ...mockTrip, assignedToName: undefined, assignedTo: undefined };
    render(
      <TripCard
        trip={unassignedTrip}
        isSelected={false}
        onSelect={vi.fn()}
      />
    );

    expect(screen.queryByText('Assign')).not.toBeInTheDocument();
  });
});
