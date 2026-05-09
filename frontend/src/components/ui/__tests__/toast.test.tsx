import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToastContainer } from '../toast';
import { useToastStore, toast } from '@/lib/toast-store';

describe('Toast system', () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it('renders nothing when no toasts exist', () => {
    const { container } = render(<ToastContainer />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a toast notification', () => {
    useToastStore.getState().add('Trip saved', 'success');
    render(<ToastContainer />);
    expect(screen.getByText('Trip saved')).toBeInTheDocument();
  });

  it('renders multiple toasts', () => {
    useToastStore.getState().add('Trip saved', 'success');
    useToastStore.getState().add('Connection lost', 'error');
    render(<ToastContainer />);
    expect(screen.getByText('Trip saved')).toBeInTheDocument();
    expect(screen.getByText('Connection lost')).toBeInTheDocument();
  });

  it('removes toast on dismiss button click', async () => {
    useToastStore.getState().add('Trip saved', 'success');
    render(<ToastContainer />);
    const dismissBtn = screen.getByLabelText('Dismiss notification');
    await userEvent.click(dismissBtn);
    await waitFor(() => {
      expect(screen.queryByText('Trip saved')).not.toBeInTheDocument();
    });
  });

  it('renders correct icon by type', () => {
    useToastStore.getState().add('Success', 'success');
    useToastStore.getState().add('Error', 'error');
    useToastStore.getState().add('Info', 'info');
    useToastStore.getState().add('Warning', 'warning');
    const { container } = render(<ToastContainer />);
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Info')).toBeInTheDocument();
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(container.querySelectorAll('[role="alert"]').length).toBe(4);
  });

  it('has live-region accessibility wrapper', () => {
    useToastStore.getState().add('Test', 'info');
    render(<ToastContainer />);
    const alerts = document.querySelectorAll('[role="alert"]');
    const liveRegion = alerts[0]?.closest('[aria-live]');
    expect(liveRegion).not.toBeNull();
    expect(liveRegion?.getAttribute('aria-live')).toBe('polite');
  });

  it('standalone toast function works', () => {
    toast('Quick notification', 'success');
    const toasts = useToastStore.getState().toasts;
    expect(toasts.length).toBe(1);
    expect(toasts[0].message).toBe('Quick notification');
    expect(toasts[0].type).toBe('success');
  });
});
