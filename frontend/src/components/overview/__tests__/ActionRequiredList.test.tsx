import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ActionRequiredList } from '../ActionRequiredList';

describe('ActionRequiredList', () => {
  it('renders empty state exact copy', () => {
    render(<ActionRequiredList items={[]} />);
    expect(screen.getByText('No urgent action detected from available data.')).toBeInTheDocument();
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
            reason: '2 quotes are waiting for approval before sending.',
            href: '/reviews',
            ctaLabel: 'Review quotes',
          },
        ]}
      />
    );

    expect(screen.getByText('Quote needs review')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /review quotes/i })).toHaveAttribute('href', '/reviews');
  });

  it('renders lead, trip, and system items', () => {
    render(
      <ActionRequiredList
        items={[
          {
            id: 'lead',
            priority: 'high',
            source: 'lead',
            title: 'New enquiries waiting',
            subtitle: 'Lead inbox',
            reason: '3 new enquiries need qualification or assignment.',
            href: '/inbox',
            ctaLabel: 'Open enquiries',
          },
          {
            id: 'trip-1',
            priority: 'high',
            source: 'trip',
            title: 'Trip needs review',
            subtitle: 'Maldives Honeymoon',
            reason: 'This trip is marked for attention in planning.',
            href: '/trips/trip-1',
            ctaLabel: 'Open trip',
          },
          {
            id: 'system',
            priority: 'low',
            source: 'system',
            title: 'Agency health check',
            subtitle: 'System check',
            reason: '2 items need review.',
            href: '/overview?panel=system-check',
            ctaLabel: 'Check status',
          },
        ]}
      />
    );

    expect(screen.getByText('New enquiries waiting')).toBeInTheDocument();
    expect(screen.getByText('Trip needs review')).toBeInTheDocument();
    expect(screen.getByText('Agency health check')).toBeInTheDocument();
  });
});
