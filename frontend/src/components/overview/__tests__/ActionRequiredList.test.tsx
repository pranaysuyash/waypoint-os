import { describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import { ActionRequiredList } from '../ActionRequiredList';
import type { ActionRequiredItem } from '@/app/(agency)/overview/buildActionRequiredItems';

describe('ActionRequiredList', () => {
  it('does not emit duplicate key warnings when example IDs are absent', () => {
    const sharedExampleItem: ActionRequiredItem = {
      id: 'quote-',
      priority: 'normal',
      source: 'quote',
      label: 'Quote',
      title: 'Fallback quotes',
      subtitle: 'Missing quote IDs',
      meta: 'Needs review',
      reason: 'Needs action',
      href: '/trips/1',
      ctaLabel: 'Open quote',
      examples: [
        {
          id: '',
          title: 'Example one',
          detail: 'No stable IDs available yet',
          href: '/trips/1',
        },
      ],
    };

    const items: ActionRequiredItem[] = [
      sharedExampleItem,
      {
        ...sharedExampleItem,
        id: 'quote-',
        title: 'Another fallback group',
        examples: [
          {
            id: '',
            title: 'Example one',
            detail: 'No stable IDs available yet',
            href: '/trips/2',
          },
          {
            id: '',
            title: 'Example two',
            detail: 'Also duplicated title',
            href: '/trips/2',
          },
        ],
      },
    ];

    const warnSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<ActionRequiredList items={items} />);

    const duplicateWarning = warnSpy.mock.calls.some((call) => String(call[0]).includes('Encountered two children with the same key'));
    expect(duplicateWarning).toBe(false);

    warnSpy.mockRestore();
  });

  it('shows a count badge for grouped non-lead action items', () => {
    const items: ActionRequiredItem[] = [
      {
        id: 'group-quote:review:normal',
        priority: 'normal',
        source: 'quote',
        label: 'Quote',
        variant: 'group',
        title: 'Quotes to review',
        subtitle: '2 quote items need attention',
        meta: 'Submitted today',
        reason: 'Review quote',
        href: '/reviews',
        ctaLabel: 'Review quote',
        itemCount: 2,
        examples: [
          { id: 'example-1', title: 'Today', detail: 'Quote A', href: '/reviews' },
          { id: 'example-2', title: 'Today', detail: 'Quote B', href: '/reviews' },
        ],
        hidePriorityBadge: true,
      },
    ];

    const { getByText, queryByText } = render(<ActionRequiredList items={items} />);

    expect(getByText('2 matching quotes')).toBeInTheDocument();
    // Label 'Quote' is suppressed because '2 matching quotes' already communicates the entity
    expect(queryByText('Quote')).not.toBeInTheDocument();
  });

  it('sanitizes machine enum leaks and eliminates PENDING stutter', () => {
    const items: ActionRequiredItem[] = [
      {
        id: 'group-trip:pending:high',
        priority: 'high',
        source: 'trip',
        label: 'Trip',
        variant: 'group',
        title: 'Trips needing review',
        subtitle: '5 trip items need attention',
        meta: 'Red status',
        reason: 'Decision state STOP_NEEDS_REVIEW requires owner review',
        href: '/trips',
        ctaLabel: 'Open trip',
        pendingActions: ['PENDING', 'Resolve red status', 'Confirm travel window'],
        nextAction: 'Open highest-risk trip first.',
        examples: [
          {
            id: 'trip-1',
            title: 'Paris leisure trip',
            detail: '1 pax · Travel Dates to confirm · Red status · Ref TRIP-01',
            href: '/trips/1',
          },
        ],
      },
    ];

    const { getByText, queryByText } = render(<ActionRequiredList items={items} />);

    // Machine code leak is humanized
    expect(getByText(/Policy threshold hold · Owner review required/i)).toBeInTheDocument();
    expect(queryByText(/STOP_NEEDS_REVIEW/)).not.toBeInTheDocument();

    // PENDING is stripped from pending action chips
    expect(getByText('Resolve red status')).toBeInTheDocument();
    expect(getByText('Confirm travel window')).toBeInTheDocument();
    expect(queryByText('Pending: PENDING')).not.toBeInTheDocument();

    // Queue samples are rendered with interactive links and tags
    expect(getByText('Paris leisure trip')).toBeInTheDocument();
    expect(getByText('#1')).toBeInTheDocument();
    expect(getByText('Ref TRIP-01')).toBeInTheDocument();
  });
});
