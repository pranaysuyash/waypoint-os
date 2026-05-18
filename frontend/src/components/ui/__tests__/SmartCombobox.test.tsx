import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SmartCombobox } from '../SmartCombobox';

const options = [
  { value: 'Beach', label: 'Beach' },
  { value: 'Mountain', label: 'Mountain' },
  { value: 'City break', label: 'City Break' },
];

describe('SmartCombobox', () => {
  it('renders as an APG-style combobox with listbox metadata', () => {
    render(<SmartCombobox value='' onChange={vi.fn()} options={options} label='Trip Type' />);

    const input = screen.getByRole('combobox', { name: 'Trip Type' });
    expect(input).toHaveAttribute('aria-expanded', 'false');
    expect(input).toHaveAttribute('aria-haspopup', 'listbox');
    expect(input).toHaveAttribute('aria-autocomplete', 'list');
    expect(input).toHaveAttribute('aria-controls');
  });

  it('opens listbox with arrow key and keeps DOM focus in the input', () => {
    render(<SmartCombobox value='' onChange={vi.fn()} options={options} />);

    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.keyDown(input, { key: 'ArrowDown' });

    expect(input).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(input).toHaveFocus();
  });

  it('highlights options with arrow keys and selects with Enter', () => {
    const onChange = vi.fn();
    render(<SmartCombobox value='' onChange={onChange} options={options} />);

    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.keyDown(input, { key: 'ArrowDown' }); // open
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onChange).toHaveBeenCalled();
  });

  it('announces custom add entry for unmatched value and selects it', () => {
    const onChange = vi.fn();
    render(<SmartCombobox value='' onChange={onChange} options={options} />);

    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Desert' } });

    fireEvent.keyDown(input, { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith('Desert');
  });

  it('closes listbox with Escape', () => {
    render(<SmartCombobox value='' onChange={vi.fn()} options={options} />);

    const input = screen.getByRole('combobox');
    fireEvent.focus(input);
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    expect(screen.getByRole('listbox')).toBeInTheDocument();

    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('closes listbox with Tab and allows focus to move to next control', async () => {
    const user = userEvent.setup();
    render(
      <>
        <SmartCombobox value='' onChange={vi.fn()} options={options} />
        <button type='button'>Next control</button>
      </>
    );

    const input = screen.getByRole('combobox');
    await user.click(input);
    expect(input).toHaveFocus();
    await user.keyboard('{ArrowDown}');
    expect(screen.getByRole('listbox')).toBeInTheDocument();

    await user.tab();

    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Next control' })).toHaveFocus();
  });
});
