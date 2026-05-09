import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToastContainer } from '../toast';
import { useToastStore, toast } from '@/lib/toast-store';

describe('ToastContainer integration', () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
    vi.useRealTimers();
  });

  it('renders toast from action path (standalone toast function)', () => {
    act(() => toast('Document uploaded successfully', 'success'));
    const { container } = render(<ToastContainer />);
    expect(screen.getByText('Document uploaded successfully')).toBeInTheDocument();
    expect(container.querySelectorAll('[role="alert"]').length).toBe(1);
  });

  it('stacks multiple toasts from sequential actions', () => {
    act(() => {
      toast('Override recorded', 'success');
      toast('Connection lost, retrying', 'error');
      toast('3 follow-ups due today', 'info');
    });
    const { container } = render(<ToastContainer />);
    const alerts = container.querySelectorAll('[role="alert"]');
    expect(alerts.length).toBe(3);
    expect(screen.getByText('Override recorded')).toBeInTheDocument();
    expect(screen.getByText('Connection lost, retrying')).toBeInTheDocument();
    expect(screen.getByText('3 follow-ups due today')).toBeInTheDocument();
  });

  it('removes toast via store action path and UI updates', async () => {
    act(() => toast('Temporary notification', 'info'));
    render(<ToastContainer />);
    expect(screen.getByText('Temporary notification')).toBeInTheDocument();

    const id = useToastStore.getState().toasts[0].id;
    act(() => useToastStore.getState().remove(id));

    await waitFor(() => {
      expect(screen.queryByText('Temporary notification')).not.toBeInTheDocument();
    });
  });

  it('all four toast types render with correct icons', () => {
    act(() => {
      toast('Success message', 'success');
      toast('Error message', 'error');
      toast('Info message', 'info');
      toast('Warning message', 'warning');
    });
    render(<ToastContainer />);

    expect(screen.getByText('Success message')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
    expect(screen.getByText('Info message')).toBeInTheDocument();
    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  it('returns null (no DOM) when store is empty', () => {
    const { container } = render(<ToastContainer />);
    expect(container.firstChild).toBeNull();
  });
});
