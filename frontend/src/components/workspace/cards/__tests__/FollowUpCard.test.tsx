import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, test, it, expect, beforeEach, vi } from 'vitest';
import { FollowUpCard } from '../FollowUpCard';

describe('FollowUpCard', () => {
  const defaultProps = {
    tripId: 'trip_001',
    travelerName: 'Ravi Singh',
    agentName: 'Pranay',
    dueDate: '2026-04-28T14:00:00Z',
    status: 'pending' as const,
    daysUntilDue: 1,
    onComplete: vi.fn(),
    onSnooze: vi.fn(),
    onReschedule: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ======== RENDERING TESTS ========

  test('renders card with trip information', () => {
    render(<FollowUpCard {...defaultProps} />);
    expect(screen.getByText('trip_001')).toBeInTheDocument();
    expect(screen.getByText('Ravi Singh')).toBeInTheDocument();
    expect(screen.getByText(/Pranay/)).toBeInTheDocument();
  });

  test('renders status badge for pending', () => {
    render(<FollowUpCard {...defaultProps} status="pending" />);
    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  test('renders status badge for completed', () => {
    render(<FollowUpCard {...defaultProps} status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  test('renders status badge for snoozed', () => {
    render(<FollowUpCard {...defaultProps} status="snoozed" />);
    expect(screen.getByText('Snoozed')).toBeInTheDocument();
  });

  test('displays due date in readable format', () => {
    render(<FollowUpCard {...defaultProps} />);
    // Should show formatted date (e.g., "Apr 28, 2026")
    expect(screen.getByText(/Apr/)).toBeInTheDocument();
  });

  // ======== URGENCY BADGE TESTS ========

  test('shows OVERDUE badge for negative days', () => {
    render(<FollowUpCard {...defaultProps} daysUntilDue={-2} />);
    expect(screen.getByText(/OVERDUE/)).toBeInTheDocument();
  });

  test('shows day counter for zero days', () => {
    render(<FollowUpCard {...defaultProps} daysUntilDue={0} />);
    // Component renders "0d" for due-today, styled with urgency color
    expect(screen.getByText(/0d/)).toBeInTheDocument();
  });

  test('shows day counter for 1-3 days out', () => {
    render(<FollowUpCard {...defaultProps} daysUntilDue={2} />);
    // Component renders "2d"
    expect(screen.getByText(/2d/)).toBeInTheDocument();
  });

  test('shows day counter for >3 days out', () => {
    render(<FollowUpCard {...defaultProps} daysUntilDue={5} />);
    // Component renders "5d"
    expect(screen.getByText(/5d/)).toBeInTheDocument();
  });

  // ======== ACTION BUTTON TESTS ========

  test('shows action buttons for pending status', () => {
    render(<FollowUpCard {...defaultProps} status="pending" />);
    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('Snooze')).toBeInTheDocument();
    expect(screen.getByText('Reschedule')).toBeInTheDocument();
  });

  test('hides action buttons for completed status', () => {
    render(<FollowUpCard {...defaultProps} status="completed" />);
    expect(screen.queryByText('Complete')).not.toBeInTheDocument();
    expect(screen.queryByText('Snooze')).not.toBeInTheDocument();
  });

  // ======== COMPLETE ACTION TESTS ========

  test('calls onComplete when complete button clicked', async () => {
    const onComplete = vi.fn();
    render(<FollowUpCard {...defaultProps} onComplete={onComplete} />);
    
    const completeButton = screen.getByText('Complete');
    fireEvent.click(completeButton);
    
    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledWith('trip_001');
    });
  });

  test('disables complete button while loading', async () => {
    const onComplete = vi.fn(
      () => new Promise(() => {}) // Never resolves
    );
    render(<FollowUpCard {...defaultProps} onComplete={onComplete} />);
    
    const completeButton = screen.getByText('Complete') as HTMLButtonElement;
    fireEvent.click(completeButton);
    
    await waitFor(() => {
      expect(completeButton.disabled).toBe(true);
    });
  });

  // ======== SNOOZE ACTION TESTS ========

  test('opens snooze modal when snooze button clicked', async () => {
    render(<FollowUpCard {...defaultProps} />);
    
    const snoozeButton = screen.getByText('Snooze');
    fireEvent.click(snoozeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Snooze Follow-up')).toBeInTheDocument();
    });
  });

  test('snooze modal shows 1, 3, 7 day options', async () => {
    render(<FollowUpCard {...defaultProps} />);
    
    const snoozeButton = screen.getByText('Snooze');
    fireEvent.click(snoozeButton);
    
    await waitFor(() => {
      expect(screen.getByText('1 day')).toBeInTheDocument();
      expect(screen.getByText('3 days')).toBeInTheDocument();
      expect(screen.getByText('7 days')).toBeInTheDocument();
    });
  });

  test('calls onSnooze with correct days when option selected', async () => {
    const onSnooze = vi.fn();
    render(<FollowUpCard {...defaultProps} onSnooze={onSnooze} />);
    
    const snoozeButton = screen.getByText('Snooze');
    fireEvent.click(snoozeButton);
    
    await waitFor(() => {
      const threeDay = screen.getByText('3 days');
      fireEvent.click(threeDay);
    });
    
    await waitFor(() => {
      expect(onSnooze).toHaveBeenCalledWith('trip_001', 3);
    });
  });

  test('closes snooze modal on cancel', async () => {
    render(<FollowUpCard {...defaultProps} />);
    
    const snoozeButton = screen.getByText('Snooze');
    fireEvent.click(snoozeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Snooze Follow-up')).toBeInTheDocument();
    });
    
    const cancelButton = screen.getAllByText('Cancel')[0];
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(screen.queryByText('Snooze Follow-up')).not.toBeInTheDocument();
    });
  });

  // ======== RESCHEDULE ACTION TESTS ========

  test('opens reschedule modal when reschedule button clicked', async () => {
    render(<FollowUpCard {...defaultProps} />);
    
    const rescheduleButton = screen.getByText('Reschedule');
    fireEvent.click(rescheduleButton);
    
    await waitFor(() => {
      expect(screen.getByText('Reschedule Follow-up')).toBeInTheDocument();
    });
  });

  test('calls onReschedule with new date', async () => {
    const onReschedule = vi.fn();
    render(<FollowUpCard {...defaultProps} onReschedule={onReschedule} />);

    const rescheduleButton = screen.getByText('Reschedule');
    fireEvent.click(rescheduleButton);

    await waitFor(() => {
      expect(screen.getByText('Reschedule Follow-up')).toBeInTheDocument();
    });

    // datetime-local input — query by type attribute directly
    const input = document.querySelector('input[type="datetime-local"]') as HTMLInputElement;
    expect(input).not.toBeNull();
    fireEvent.change(input, { target: { value: '2026-05-01T10:00' } });

    // Click the submit button inside the modal (second "Reschedule" button)
    const rescheduleButtons = screen.getAllByText('Reschedule');
    fireEvent.click(rescheduleButtons[rescheduleButtons.length - 1]);

    await waitFor(() => {
      expect(onReschedule).toHaveBeenCalledWith(
        'trip_001',
        expect.stringContaining('2026-05-01')
      );
    });
  });

  test('disables reschedule button without date selected', async () => {
    render(<FollowUpCard {...defaultProps} />);
    
    const rescheduleButton = screen.getByText('Reschedule');
    fireEvent.click(rescheduleButton);
    
    await waitFor(() => {
      const submitButton = screen.getAllByText('Reschedule')[1] as HTMLButtonElement;
      expect(submitButton.disabled).toBe(true);
    });
  });
});
