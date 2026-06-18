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
});
