import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterPill } from '../FilterPill';
import { InboxFilterBar, type FilterKey } from '../InboxFilterBar';

describe('FilterPill', () => {
  it('renders label', () => {
    render(<FilterPill label="All" />);
    expect(screen.getByText('All')).toBeInTheDocument();
  });

  it('shows count when provided', () => {
    render(<FilterPill label="All" count={5} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const onClick = vi.fn();
    render(<FilterPill label="All" onClick={onClick} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('shows active styling when isActive', () => {
    const { container } = render(<FilterPill label="All" isActive />);
    const button = container.querySelector('button');
    expect(button).toHaveClass('bg-elevated');
  });

  it('shows inactive styling when not isActive', () => {
    const { container } = render(<FilterPill label="All" />);
    const button = container.querySelector('button');
    expect(button).toHaveClass('text-text-muted');
  });

  it('renders icon when provided', () => {
    render(<FilterPill label="All" icon={<span data-testid="icon">★</span>} />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('renders role variant correctly', () => {
    const { container } = render(<FilterPill label="Operations" variant="role" isActive />);
    const button = container.querySelector('button');
    expect(button).toHaveClass('bg-accent-blue');
    expect(button).toHaveClass('text-text-on-accent');
  });
});

describe('InboxFilterBar', () => {
  const defaultProps = {
    activeFilter: 'all' as FilterKey,
    onFilterChange: vi.fn(),
    filters: [
      { key: 'all' as FilterKey, label: 'All leads', count: 10, tone: 'neutral' as const },
      { key: 'incomplete' as FilterKey, label: 'Needs details', count: 3, tone: 'attention' as const },
      { key: 'unassigned' as FilterKey, label: 'Unassigned', count: 2, tone: 'ownership' as const },
      { key: 'at_risk' as FilterKey, label: 'At Risk', count: 0, tone: 'risk' as const, muted: true },
    ],
  };

  it('renders filters', () => {
    render(<InboxFilterBar {...defaultProps} />);
    expect(screen.getByText('All leads')).toBeInTheDocument();
    expect(screen.getByText('Needs details')).toBeInTheDocument();
    expect(screen.getByText('Unassigned')).toBeInTheDocument();
    expect(screen.getByText('At Risk')).toBeInTheDocument();
  });

  it('calls onFilterChange when filter clicked', () => {
    const onFilterChange = vi.fn();
    render(<InboxFilterBar {...defaultProps} onFilterChange={onFilterChange} />);
    fireEvent.click(screen.getByText('Needs details'));
    expect(onFilterChange).toHaveBeenCalledWith('incomplete');
  });

  it('shows active filter styling', () => {
    render(<InboxFilterBar {...defaultProps} activeFilter="all" />);
    const allButton = screen.getByText('All leads').closest('button');
    expect(allButton).toHaveClass('bg-elevated');
  });

  it('renders filter counts', () => {
    render(<InboxFilterBar {...defaultProps} />);
    expect(screen.getByText('10')).toBeInTheDocument(); // All count
    expect(screen.getByText('3')).toBeInTheDocument(); // Needs details count
    expect(screen.getByText('2')).toBeInTheDocument(); // Unassigned count
    expect(screen.getByText('0')).toBeInTheDocument(); // At Risk count
  });

  it('mutes the at-risk chip when there is no risk', () => {
    render(<InboxFilterBar {...defaultProps} />);
    const atRiskButton = screen.getByText('At Risk').closest('button');
    expect(atRiskButton).toHaveClass('text-text-muted');
  });
});
