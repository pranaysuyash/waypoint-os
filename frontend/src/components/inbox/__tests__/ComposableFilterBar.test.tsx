import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ComposableFilterBar } from '../ComposableFilterBar';
import type { InboxFilters } from '@/types/governance';

describe('ComposableFilterBar - interaction patterns', () => {
  const initialFilters: InboxFilters = {};
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens and applies a quick preset via keyboard', () => {
    const onFiltersChange = vi.fn();
    render(
      <ComposableFilterBar
        filters={initialFilters}
        onFiltersChange={onFiltersChange}
        total={42}
      />,
    );

    const presetTrigger = screen.getByRole('button', { name: /quick presets/i });
    fireEvent.keyDown(presetTrigger, { key: 'ArrowDown', code: 'ArrowDown' });

    const menu = screen.getByRole('menu');
    expect(menu).toBeInTheDocument();

    const presetItems = screen.getAllByRole('menuitem');
    expect(presetItems[0]).toHaveTextContent('My Urgent');

    fireEvent.keyDown(menu, { key: 'Home', code: 'Home' });
    fireEvent.keyDown(menu, { key: 'Enter', code: 'Enter' });

    expect(onFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({
        priority: ['critical', 'high'],
        slaStatus: ['breached', 'at_risk'],
      }),
    );
  });

  it('supports listbox keyboard navigation and Enter selection', () => {
    const onFiltersChange = vi.fn();
    render(
      <ComposableFilterBar
        filters={initialFilters}
        onFiltersChange={onFiltersChange}
      />,
    );

    const priorityTrigger = screen.getByText('Priority').closest('button');
    if (!priorityTrigger) {
      throw new Error('Priority trigger not found');
    }

    fireEvent.keyDown(priorityTrigger, { key: 'ArrowDown', code: 'ArrowDown' });

    const listbox = screen.getByRole('listbox');
    expect(listbox).toHaveAttribute('aria-activedescendant');

    fireEvent.keyDown(listbox, { key: 'ArrowDown', code: 'ArrowDown' });
    fireEvent.keyDown(listbox, { key: 'Enter', code: 'Enter' });

    expect(onFiltersChange).toHaveBeenCalledWith(
      expect.objectContaining({
        priority: ['high'],
      }),
    );
  });

  it('handles Tab from listbox by closing and moving focus forward', () => {
    const onFiltersChange = vi.fn();
    render(
      <ComposableFilterBar
        filters={{}}
        onFiltersChange={onFiltersChange}
      />,
    );

    const slaTrigger = screen.getByText('SLA Status').closest('button');
    if (!slaTrigger) {
      throw new Error('SLA trigger not found');
    }

    fireEvent.click(slaTrigger);
    const listbox = screen.getByRole('listbox');

    fireEvent.keyDown(listbox, { key: 'Tab', code: 'Tab' });

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('handles Tab from quick presets menu by closing', () => {
    const onFiltersChange = vi.fn();
    render(
      <ComposableFilterBar
        filters={{}}
        onFiltersChange={onFiltersChange}
      />,
    );

    const presetTrigger = screen.getByRole('button', { name: /quick presets/i });
    fireEvent.keyDown(presetTrigger, { key: 'ArrowDown', code: 'ArrowDown' });

    const menu = screen.getByRole('menu');
    fireEvent.keyDown(menu, { key: 'Tab', code: 'Tab' });

    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });
});
