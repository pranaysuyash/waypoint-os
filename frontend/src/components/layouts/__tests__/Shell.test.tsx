import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SidebarTripContext } from '../Shell';
import type { Trip } from '@/lib/api-client';

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

vi.mock('next/navigation', () => ({
  usePathname: () => '/trips/trip_1/intake',
}));

function makeTrip(overrides: Partial<Trip> = {}): Trip {
  return {
    id: 'trip_1',
    destination: 'Bali',
    type: 'Family',
    state: 'blue',
    age: 'today',
    createdAt: '2026-05-12T00:00:00Z',
    updatedAt: '2026-05-12T00:00:00Z',
    party: 4,
    dateWindow: 'TBD',
    budget: '250000',
    status: 'assigned',
    rawInput: 'Sharma family wants a Bali trip',
    ...overrides,
  };
}

describe('SidebarTripContext', () => {
  it('does not render outside a loaded trip context', () => {
    const { container } = render(<SidebarTripContext trip={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('summarizes current trip status and next action with the canonical trip route', () => {
    render(<SidebarTripContext trip={makeTrip()} />);

    expect(screen.getByRole('region', { name: 'Current trip context' })).toBeInTheDocument();
    expect(screen.getByText('Current trip')).toBeInTheDocument();
    expect(screen.getByText('Need Customer Details')).toBeInTheDocument();
    expect(screen.getByText('Bali family trip')).toBeInTheDocument();
    expect(screen.getByText(/Next: confirm travel window before building options/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open missing details' })).toHaveAttribute(
      'href',
      '/trips/trip_1/intake',
    );
  });
});
