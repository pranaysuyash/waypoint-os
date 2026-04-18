import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Tabs, getTabPanelId, getTabButtonId } from '../tabs';

describe('Tabs Component', () => {
  const mockTabs = [
    { id: 'intake', label: 'New Inquiry' },
    { id: 'packet', label: 'Trip Details' },
    { id: 'decision', label: 'Ready to Quote?' },
  ];

  it('renders all tabs', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    expect(screen.getByRole('tab', { name: 'New Inquiry' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Trip Details' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Ready to Quote?' })).toBeInTheDocument();
  });

  it('has proper ARIA roles', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    expect(screen.getByRole('tablist')).toBeInTheDocument();
    const tabs = screen.getAllByRole('tab');
    expect(tabs).toHaveLength(3);
  });

  it('marks active tab with aria-selected', () => {
    render(<Tabs tabs={mockTabs} activeTab='packet' onTabChange={vi.fn()} />);

    const activeTab = screen.getByRole('tab', { name: 'Trip Details' });
    expect(activeTab).toHaveAttribute('aria-selected', 'true');

    const inactiveTabs = screen.getAllByRole('tab').filter(
      (tab) => tab !== activeTab
    );
    inactiveTabs.forEach((tab) => {
      expect(tab).toHaveAttribute('aria-selected', 'false');
    });
  });

  it('calls onTabChange when tab is clicked', () => {
    const handleChange = vi.fn();
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={handleChange} />);

    fireEvent.click(screen.getByRole('tab', { name: 'Trip Details' }));
    expect(handleChange).toHaveBeenCalledWith('packet');
  });

  it('sets correct tabIndex on active tab', () => {
    render(<Tabs tabs={mockTabs} activeTab='decision' onTabChange={vi.fn()} />);

    const activeTab = screen.getByRole('tab', { name: 'Ready to Quote?' });
    expect(activeTab).toHaveAttribute('tabIndex', '0');

    const inactiveTab = screen.getByRole('tab', { name: 'New Inquiry' });
    expect(inactiveTab).toHaveAttribute('tabIndex', '-1');
  });

  it('has aria-controls pointing to tabpanel', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    const intakeTab = screen.getByRole('tab', { name: 'New Inquiry' });
    expect(intakeTab).toHaveAttribute('aria-controls', getTabPanelId('intake'));
  });

  it('uses custom ariaLabel when provided', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} ariaLabel='Trip workspace sections' />);

    const tablist = screen.getByRole('tablist');
    expect(tablist).toHaveAttribute('aria-label', 'Trip workspace sections');
  });

  it('defaults ariaLabel to "Tab navigation"', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    const tablist = screen.getByRole('tablist');
    expect(tablist).toHaveAttribute('aria-label', 'Tab navigation');
  });

  it('has a live region for screen reader announcements', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    const liveRegion = document.querySelector('[role="status"][aria-live="polite"]');
    expect(liveRegion).toBeInTheDocument();
  });

  it('announces tab changes via live region', () => {
    const handleChange = vi.fn();
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={handleChange} />);

    const liveRegion = document.querySelector('[role="status"][aria-live="polite"]');
    expect(liveRegion?.textContent).toBe('New Inquiry tab selected');
  });

  it('renders tab with id from getTabButtonId', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    const intakeTab = screen.getByRole('tab', { name: 'New Inquiry' });
    expect(intakeTab).toHaveAttribute('id', getTabButtonId('intake'));
  });

  it('displays tab count when provided', () => {
    const tabsWithCount = [
      { id: 'inbox', label: 'Inbox', count: 5 },
      { id: 'sent', label: 'Sent', count: 0 },
    ];

    render(<Tabs tabs={tabsWithCount} activeTab='inbox' onTabChange={vi.fn()} />);

    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.queryByText('0')).not.toBeInTheDocument();
  });

  it('applies active styles to selected tab', () => {
    render(<Tabs tabs={mockTabs} activeTab='intake' onTabChange={vi.fn()} />);

    const activeTab = screen.getByRole('tab', { name: 'New Inquiry' });
    expect(activeTab).toHaveClass('text-[#e6edf3]');
  });
});
