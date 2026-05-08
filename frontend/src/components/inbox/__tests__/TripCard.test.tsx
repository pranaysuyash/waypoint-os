import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TripCard } from '../TripCard';
import type { InboxTrip, TripPriority } from '@/types/governance';

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
  urgency: 60,
  importance: 50,
  urgencyBreakdown: { sla_breach: 60, departure_proximity: 50 },
  importanceBreakdown: { revenue: 35, client_tier: 70 },
};

describe('TripCard v2 - priority indicator', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  it('renders PriorityIndicator with urgency dot and priority text', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    const indicator = screen.getByRole('status');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveAttribute('aria-label', expect.stringContaining('Urgency'));
  });

  it('shows critical label for critical priority', () => {
    const criticalTrip = { ...mockTrip, priority: 'critical' as TripPriority, urgency: 90, importance: 80 };
    render(<TripCard trip={criticalTrip} isSelected={false} onSelect={vi.fn()} />);
    const indicator = screen.getByRole('status');
    expect(indicator).toHaveTextContent('CRIT');
  });

  it('shows medium label for medium priority', () => {
    const mediumTrip = { ...mockTrip, priority: 'medium' as TripPriority, urgency: 30, importance: 25 };
    render(<TripCard trip={mediumTrip} isSelected={false} onSelect={vi.fn()} />);
    const indicator = screen.getByRole('status');
    expect(indicator).toHaveTextContent('MEDI');
  });
});

describe('TripCard v2 - primary context (row 1)', () => {
  it('renders destination and trip type as title', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByTestId('trip-card-destination')).toHaveTextContent('Bali leisure');
  });

  it('renders customer name below title', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByTestId('trip-card-customer')).toHaveTextContent('Sharma Family');
  });

  it('renders stage badge', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByTestId('trip-card-stage')).toHaveTextContent('intake');
  });
});

describe('TripCard v2 - metrics row (role-dependent)', () => {
  it('operations view shows party · date · value · days', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} viewProfile="operations" />);
    const metrics = screen.getByTestId('trip-card-metrics');
    expect(metrics).toHaveTextContent('4 pax');
    expect(metrics).toHaveTextContent('June 2026');
    expect(metrics).toHaveTextContent('$15.0k');
    expect(metrics).toHaveTextContent('6d');
  });

  it('teamLead view shows assignee · SLA · days · priority', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} viewProfile="teamLead" />);
    const metrics = screen.getByTestId('trip-card-metrics');
    expect(metrics).toHaveTextContent('Alex Agent');
    expect(metrics).toHaveTextContent('at risk');
    expect(metrics).toHaveTextContent('6d');
    expect(metrics).toHaveTextContent('High');
  });
});

describe('TripCard v2 - status row (row 3)', () => {
  it('renders contextual SLA badge with days and percentage', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    const sla = screen.getByTestId('trip-card-sla');
    expect(sla).toHaveTextContent('6d');
    expect(sla).toHaveTextContent('600%');
  });

  it('renders assigned agent badge when assigned', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByTestId('trip-card-assigned')).toHaveTextContent('Alex Agent');
  });

  it('renders unassigned badge when unassigned', () => {
    const unassigned = { ...mockTrip, assignedTo: undefined, assignedToName: undefined };
    render(<TripCard trip={unassigned} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByTestId('trip-card-unassigned')).toHaveTextContent('Unassigned');
  });
});

describe('TripCard v2 - flags', () => {
  it('renders flag badges when flags present', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    const flags = screen.getByTestId('trip-card-flags');
    expect(flags).toBeInTheDocument();
    expect(flags.children.length).toBe(2);
  });

  it('hides flags section when no flags', () => {
    const noFlags = { ...mockTrip, flags: [] };
    render(<TripCard trip={noFlags} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.queryByTestId('trip-card-flags')).not.toBeInTheDocument();
  });
});

describe('TripCard v2 - footer', () => {
  it('shows trip ID in footer', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByTestId('trip-card-id')).toHaveTextContent('TRIP-123');
  });

  it('shows "View" link in footer', () => {
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={vi.fn()} />);
    expect(screen.getByRole('link', { name: /view/i })).toHaveAttribute(
      'href',
      '/trips/TRIP-123/intake'
    );
  });

  it('calls onSelect when checkbox clicked', () => {
    const onSelect = vi.fn();
    render(<TripCard trip={mockTrip} isSelected={false} onSelect={onSelect} />);
    fireEvent.click(screen.getByRole('checkbox'));
    expect(onSelect).toHaveBeenCalledWith('TRIP-123', true);
  });
});