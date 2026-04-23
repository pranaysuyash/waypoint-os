import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterPill } from '../FilterPill';
import { InboxFilterBar, type FilterKey, type RoleKey } from '../InboxFilterBar';

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
    expect(button).toHaveClass('bg-[#161b22]');
    expect(button).toHaveClass('border-[#58a6ff]');
  });

  it('shows inactive styling when not isActive', () => {
    const { container } = render(<FilterPill label="All" />);
    const button = container.querySelector('button');
    expect(button).toHaveClass('text-[#8b949e]');
  });

  it('renders icon when provided', () => {
    render(<FilterPill label="All" icon={<span data-testid="icon">★</span>} />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('renders role variant correctly', () => {
    const { container } = render(<FilterPill label="Ops" variant="role" isActive />);
    const button = container.querySelector('button');
    expect(button).toHaveClass('bg-[#58a6ff]');
    expect(button).toHaveClass('text-[#0d1117]');
  });
});

describe('InboxFilterBar', () => {
  const defaultProps = {
    activeFilter: 'all' as FilterKey,
    onFilterChange: vi.fn(),
    activeRole: 'ops' as RoleKey,
    onRoleChange: vi.fn(),
    filters: [
      { key: 'all' as FilterKey, label: 'All', count: 10 },
      { key: 'at_risk' as FilterKey, label: 'At Risk', count: 3 },
    ],
    presets: [
      { key: 'my_urgent', label: 'My Urgent', count: 2 },
    ],
  };

  it('renders role switcher', () => {
    render(<InboxFilterBar {...defaultProps} />);
    expect(screen.getByText('Ops')).toBeInTheDocument();
    expect(screen.getByText('Lead')).toBeInTheDocument();
  });

  it('renders filters', () => {
    render(<InboxFilterBar {...defaultProps} />);
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('At Risk')).toBeInTheDocument();
  });

  it('renders presets', () => {
    render(<InboxFilterBar {...defaultProps} />);
    expect(screen.getByText('My Urgent')).toBeInTheDocument();
  });

  it('calls onRoleChange when role clicked', () => {
    const onRoleChange = vi.fn();
    render(<InboxFilterBar {...defaultProps} onRoleChange={onRoleChange} />);
    fireEvent.click(screen.getByText('Lead'));
    expect(onRoleChange).toHaveBeenCalledWith('mgr');
  });

  it('calls onFilterChange when filter clicked', () => {
    const onFilterChange = vi.fn();
    render(<InboxFilterBar {...defaultProps} onFilterChange={onFilterChange} />);
    fireEvent.click(screen.getByText('At Risk'));
    expect(onFilterChange).toHaveBeenCalledWith('at_risk');
  });

  it('shows active role styling', () => {
    render(<InboxFilterBar {...defaultProps} activeRole="ops" />);
    const opsButton = screen.getByText('Ops').closest('button');
    expect(opsButton).toHaveClass('bg-[#58a6ff]');
  });

  it('shows active filter styling', () => {
    render(<InboxFilterBar {...defaultProps} activeFilter="at_risk" />);
    const atRiskButton = screen.getByText('At Risk').closest('button');
    expect(atRiskButton).toHaveClass('bg-[#161b22]');
  });

  it('renders filter counts', () => {
    render(<InboxFilterBar {...defaultProps} />);
    expect(screen.getByText('10')).toBeInTheDocument(); // All count
    expect(screen.getByText('3')).toBeInTheDocument(); // At Risk count
    expect(screen.getByText('2')).toBeInTheDocument(); // My Urgent count
  });

  it('does not render presets section when empty', () => {
    render(<InboxFilterBar {...defaultProps} presets={[]} />);
    expect(screen.queryByText('My Urgent')).not.toBeInTheDocument();
  });
});
