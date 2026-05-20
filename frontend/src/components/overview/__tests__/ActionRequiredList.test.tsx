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

  it('renders quote review item as a compact record-first row', () => {
    render(
      <ActionRequiredList
        items={[
          {
            id: 'quote-review',
            priority: 'urgent',
            source: 'quote',
            label: 'Quote',
            title: 'Italy honeymoon quote',
            subtitle: '2 pax · Travel June 2026 · Owner Agent',
            meta: 'Submitted 15 May · 4d waiting',
            reason: 'High-risk quote review',
            reference: 'Ref TRIP-1',
            href: '/reviews',
            ctaLabel: 'Review quote',
            criticalityLabel: 'High-risk feedback · 4d waiting',
            pendingActions: ['Review quote', 'Confirm approval'],
            nextAction: 'Review risk, approve or return.',
          },
        ]}
      />
    );

    expect(screen.getByText('Quote')).toBeInTheDocument();
    expect(screen.getByText('Italy honeymoon quote')).toBeInTheDocument();
    expect(screen.getByText('Submitted 15 May · 4d waiting')).toBeInTheDocument();
    expect(screen.getByText('High-risk quote review · High-risk feedback · 4d waiting · Ref TRIP-1')).toBeInTheDocument();
    expect(screen.getByText('Pending:')).toBeInTheDocument();
    expect(screen.getByText(/Review quote · Confirm approval/)).toBeInTheDocument();
    expect(screen.getByText('Next:')).toBeInTheDocument();
    expect(screen.getByText(/Review risk, approve or return\./)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /review quote/i })).toHaveAttribute('href', '/reviews');
  });

  it('renders lead and trip items without generic enquiry titles', () => {
    render(
      <ActionRequiredList
        items={[
          {
            id: 'lead',
            priority: 'urgent',
            source: 'lead',
            label: 'Enquiry',
            title: 'Dubai family enquiry',
            subtitle: 'Neha Kapoor · 5 pax · Travel June 2026',
            meta: 'Received 17 May · 2d waiting',
            reason: 'Qualification overdue',
            href: '/inbox',
            ctaLabel: 'Open enquiry',
          },
          {
            id: 'trip-1',
            priority: 'high',
            source: 'trip',
            label: 'Trip',
            title: 'Maldives honeymoon trip',
            subtitle: 'Travel Jun 2026 · Red status',
            meta: 'Red status',
            reason: 'Needs planning attention',
            href: '/trips/trip-1',
            ctaLabel: 'Open trip',
          },
        ]}
      />
    );

    expect(screen.getByText('Dubai family enquiry')).toBeInTheDocument();
    expect(screen.getByText('Maldives honeymoon trip')).toBeInTheDocument();
    expect(screen.getByText('Received 17 May · 2d waiting')).toBeInTheDocument();
    expect(screen.queryByText('New enquiry waiting')).not.toBeInTheDocument();
    expect(screen.queryByText('Agency health check')).not.toBeInTheDocument();
  });

  it('renders repeated enquiry work as a grouped compact card with examples', () => {
    render(
      <ActionRequiredList
        items={[
          {
            id: 'group-lead-overdue',
            variant: 'group',
            priority: 'urgent',
            source: 'lead',
            label: 'Enquiry',
            title: 'Overdue enquiries',
            subtitle: '2,425 enquiries in queue · 1,184 unassigned · oldest 25d waiting',
            meta: '25d waiting',
            reason: 'Qualification overdue',
            href: '/inbox',
            ctaLabel: 'Open oldest enquiry',
            secondaryHref: '/inbox',
            secondaryCtaLabel: 'Open all enquiries',
            hidePriorityBadge: true,
            itemCount: 2425,
            criticalityLabel: 'Breached SLA · 2,425 breached · unassigned oldest 25d waiting',
            pendingActions: ['Qualify', 'Assign 1,184 unowned (25d waiting)', 'Identify 1,184 customers', 'Complete 932 basics'],
            nextAction: 'Open oldest, clear basics, continue by age.',
            examples: [
              {
                id: 'lead-1',
                title: '25d waiting',
                detail: 'Unnamed customer · 1 pax · Travel TBD · Ref SC-901',
                href: '/inbox',
              },
              {
                id: 'lead-2',
                title: '14d waiting',
                detail: 'Unnamed customer · 5 pax · Travel Feb 9-14, 2026 · Ref SC-902',
                href: '/inbox',
              },
            ],
          },
        ]}
      />
    );

    expect(screen.getByText('Overdue enquiries')).toBeInTheDocument();
    expect(screen.getByText('2,425 enquiries in queue · 1,184 unassigned · oldest 25d waiting')).toBeInTheDocument();
    expect(screen.getByText('Qualification overdue · Breached SLA · 2,425 breached · unassigned oldest 25d waiting')).toBeInTheDocument();
    expect(screen.getByText('Pending:')).toBeInTheDocument();
    expect(screen.getByText(/Qualify · Assign 1,184 unowned \(25d waiting\) · Identify 1,184 customers · Complete 932 basics/)).toBeInTheDocument();
    expect(screen.getByText('Next:')).toBeInTheDocument();
    expect(screen.getByText(/Open oldest, clear basics, continue by age\./)).toBeInTheDocument();
    expect(screen.getAllByText('25d waiting')).toHaveLength(2);
    expect(screen.getByText('14d waiting')).toBeInTheDocument();
    expect(screen.queryByText('11d waiting')).not.toBeInTheDocument();
    expect(screen.queryByText(/Leisure enquiry/)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open oldest enquiry/i })).toHaveAttribute('href', '/inbox');
    expect(screen.getByRole('link', { name: /open all enquiries/i })).toHaveAttribute('href', '/inbox');
    expect(screen.queryByText('Urgent')).not.toBeInTheDocument();
  });
});
