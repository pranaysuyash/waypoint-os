import { describe, it, expect, vi } from 'vitest';
import { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../modal';

function ModalHarness() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>Open modal</button>
      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title='Trip details'>
        <button type='button'>Save changes</button>
      </Modal>
    </div>
  );
}

describe('Modal', () => {
  it('opens and renders dialog content when mounted', () => {
    render(<ModalHarness />);

    fireEvent.click(screen.getByRole('button', { name: 'Open modal' }));

    expect(screen.getByRole('dialog', { name: 'Trip details' })).toBeInTheDocument();
    expect(screen.getByText('Save changes')).toBeInTheDocument();
  });

  it('closes on overlay mouse down interaction', async () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title='Trip details'>
        <button type='button'>Save changes</button>
      </Modal>
    );

    const overlays = Array.from(document.querySelectorAll('[class*=\"bg-black\"]'));
    const overlay = overlays.find((node) => {
      return !!node.closest('[data-ui-layer=\"modal\"]');
    }) as HTMLElement | undefined;

    expect(overlay).toBeTruthy();
    fireEvent.mouseDown(overlay!);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on Escape and restores focus to the opener', async () => {
    const user = userEvent.setup();
    render(<ModalHarness />);

    const opener = screen.getByRole('button', { name: 'Open modal' });
    opener.focus();
    await user.click(opener);
    expect(screen.getByRole('dialog', { name: 'Trip details' })).toBeInTheDocument();

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog', { name: 'Trip details' })).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });
});
