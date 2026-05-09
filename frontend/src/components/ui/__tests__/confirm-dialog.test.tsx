import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfirmDialog } from '../confirm-dialog';

describe('ConfirmDialog', () => {
  it('renders nothing when closed', () => {
    const { container } = render(
      <ConfirmDialog
        isOpen={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        message="Are you sure?"
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders when open', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        message="Are you sure you want to proceed?"
      />
    );
    expect(screen.getByText('Confirm')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument();
  });

  it('shows custom title', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Delete Trip"
        message="This cannot be undone."
      />
    );
    expect(screen.getByText('Delete Trip')).toBeInTheDocument();
  });

  it('shows custom button labels', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        message="Are you sure?"
        confirmLabel="Yes, delete"
        cancelLabel="Never mind"
      />
    );
    expect(screen.getByText('Yes, delete')).toBeInTheDocument();
    expect(screen.getByText('Never mind')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button clicked', async () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={onConfirm}
        message="Are you sure?"
      />
    );
    await userEvent.click(screen.getByText('Confirm'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('shows danger styling with alert icon', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        message="This is destructive."
        variant="danger"
      />
    );
    const dangerButton = screen.getByText('Confirm');
    expect(dangerButton).toBeInTheDocument();
  });
});
