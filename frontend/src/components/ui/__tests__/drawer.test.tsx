import { describe, it, expect, vi } from 'vitest';
import { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Drawer } from '../drawer';

function DrawerHarness() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div>
      <button onClick={() => setIsOpen(true)}>Open drawer</button>
      <Drawer
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title='Travel options'
        description='Choose filters'
      >
        <button type='button'>Apply</button>
      </Drawer>
    </div>
  );
}

describe('Drawer', () => {
  it('opens and renders dialog content when mounted', () => {
    render(<DrawerHarness />);

    fireEvent.click(screen.getByRole('button', { name: 'Open drawer' }));

    expect(screen.getByRole('dialog', { name: 'Travel options' })).toBeInTheDocument();
    expect(screen.getByText('Apply')).toBeInTheDocument();
  });

  it('closes on overlay mouse down interaction', async () => {
    const onClose = vi.fn();
    render(
      <Drawer isOpen={true} onClose={onClose} title='Travel options' description='Choose filters'>
        <button type='button'>Apply</button>
      </Drawer>
    );

    const overlays = Array.from(document.querySelectorAll('[class*=\"bg-black\"]'));
    const overlay = overlays.find((node) => {
      return !!node.closest('[data-ui-layer=\"drawer\"]');
    }) as HTMLElement | undefined;

    expect(overlay).toBeTruthy();
    fireEvent.mouseDown(overlay!);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on Escape and restores focus to the opener', async () => {
    const user = userEvent.setup();
    render(<DrawerHarness />);

    const opener = screen.getByRole('button', { name: 'Open drawer' });
    opener.focus();
    await user.click(opener);
    expect(screen.getByRole('dialog', { name: 'Travel options' })).toBeInTheDocument();

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog', { name: 'Travel options' })).not.toBeInTheDocument();
    expect(opener).toHaveFocus();
  });
});
