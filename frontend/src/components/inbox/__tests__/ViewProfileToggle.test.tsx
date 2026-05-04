import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ViewProfileToggle } from '../ViewProfileToggle';
import * as inboxHelpers from '@/lib/inbox-helpers';

vi.mock('@/lib/inbox-helpers', async () => {
  const actual = await vi.importActual<typeof import('@/lib/inbox-helpers')>('@/lib/inbox-helpers');
  return {
    ...actual,
    saveViewProfile: vi.fn(),
  };
});

describe('ViewProfileToggle', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all 4 profile buttons', () => {
    render(<ViewProfileToggle current="operations" onChange={mockOnChange} />);
    expect(screen.getByText('Operations')).toBeInTheDocument();
    expect(screen.getByText('Team Lead')).toBeInTheDocument();
    expect(screen.getByText('Finance')).toBeInTheDocument();
    expect(screen.getByText('Fulfillment')).toBeInTheDocument();
  });

  it('highlights the active profile', () => {
    const { rerender } = render(<ViewProfileToggle current="operations" onChange={mockOnChange} />);
    const opsButton = screen.getByText('Operations').closest('button');
    expect(opsButton).toHaveAttribute('aria-checked', 'true');

    rerender(<ViewProfileToggle current="teamLead" onChange={mockOnChange} />);
    expect(screen.getByText('Team Lead').closest('button')).toHaveAttribute('aria-checked', 'true');
    expect(opsButton).toHaveAttribute('aria-checked', 'false');
  });

  it('calls onChange and saveViewProfile when a profile is clicked', () => {
    render(<ViewProfileToggle current="operations" onChange={mockOnChange} />);
    fireEvent.click(screen.getByText('Team Lead'));
    expect(inboxHelpers.saveViewProfile).toHaveBeenCalledWith('teamLead');
    expect(mockOnChange).toHaveBeenCalledWith('teamLead');
  });

  it('uses radio group role for accessibility', () => {
    render(<ViewProfileToggle current="operations" onChange={mockOnChange} />);
    expect(screen.getByRole('radiogroup')).toBeInTheDocument();
    expect(screen.getAllByRole('radio')).toHaveLength(4);
  });
});
