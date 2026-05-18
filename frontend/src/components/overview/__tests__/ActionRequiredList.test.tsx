import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActionRequiredList } from '../ActionRequiredList';

describe('ActionRequiredList', () => {
  it('renders empty state exact copy', () => {
    render(<ActionRequiredList items={[]} />);
    expect(screen.getByText('No urgent action detected from available data.')).toBeInTheDocument();
  });

  it('shows loading state and does not show empty state copy', () => {
    render(<ActionRequiredList items={[]} isLoading />);
    expect(screen.getByText('Checking for action required…')).toBeInTheDocument();
    expect(screen.queryByText('No urgent action detected from available data.')).not.toBeInTheDocument();
  });

  it('shows unavailable state on error and does not show empty state copy', () => {
    render(<ActionRequiredList items={[]} error={new Error('network')} />);
    expect(screen.getByText('Action required is unavailable right now.')).toBeInTheDocument();
    expect(screen.queryByText('No urgent action detected from available data.')).not.toBeInTheDocument();
  });

  it('renders quote review item', () => {
    render(
      <ActionRequiredList
        items={[
          {
            id: 'quote-review',
            priority: 'urgent',
            source: 'quote',
            title: 'Quote needs review',
            subtitle: 'Italy Honeymoon',
            meta: 'Submitted 15 May 2026',
            reason: '2 quotes are waiting for approval before sending.',
            href: '/reviews',
            ctaLabel: 'Review quote',
          },
        ]}
      />
    );

    expect(screen.getByText('Quote needs review')).toBeInTheDocument();
    expect(screen.getByText('Submitted 15 May 2026')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /review quote/i })).toHaveAttribute('href', '/reviews');
  });

  it('renders lead and trip items in compact queue rows', () => {
    render(
      <ActionRequiredList
        items={[
          {
            id: 'lead',
            priority: 'high',
            source: 'lead',
            title: 'New enquiry waiting',
            subtitle: 'Neha Kapoor · Dubai family trip',
            meta: 'Received 17 May 2026',
            reason: 'Needs qualification or assignment.',
            href: '/inbox',
            ctaLabel: 'Open enquiry',
          },
          {
            id: 'trip-1',
            priority: 'high',
            source: 'trip',
            title: 'Trip needs review',
            subtitle: 'Maldives Honeymoon',
            meta: 'Travel Jun 2026',
            reason: 'This trip is marked for attention in planning.',
            href: '/trips/trip-1',
            ctaLabel: 'Open trip',
          },
        ]}
      />
    );

    expect(screen.getByText('New enquiry waiting')).toBeInTheDocument();
    expect(screen.getByText('Trip needs review')).toBeInTheDocument();
    expect(screen.getByText('Received 17 May 2026')).toBeInTheDocument();
    expect(screen.queryByText('Agency health check')).not.toBeInTheDocument();
  });
});
