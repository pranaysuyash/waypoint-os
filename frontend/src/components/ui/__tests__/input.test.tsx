import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../input';

describe('Input Component', () => {
  it('renders input correctly', () => {
    render(<Input />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label='Username' />);
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
  });

  it('calls onChange when value changes', () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test' } });

    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('displays error message when error prop is provided', () => {
    render(<Input error='This field is required' />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('sets aria-invalid when error is present', () => {
    render(<Input error='Error message' />);
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true');
  });

  it('renders description text', () => {
    render(<Input description='Enter your email address' />);
    expect(screen.getByText('Enter your email address')).toBeInTheDocument();
  });

  it('does not show description when error is present', () => {
    render(
      <Input description='Description' error='Error message' />
    );
    expect(screen.queryByText('Description')).not.toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('applies size styles correctly', () => {
    const { container: smContainer } = render(<Input inputSize='sm' />);
    const smInput = smContainer.querySelector('input');
    expect(smInput).toHaveClass('h-8');

    const { container: lgContainer } = render(<Input inputSize='lg' />);
    const lgInput = lgContainer.querySelector('input');
    expect(lgInput).toHaveClass('h-10');
  });

  it('renders with left icon', () => {
    render(<Input leftIcon={<span data-testid='left-icon'>@</span>} />);
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
  });

  it('renders with right icon', () => {
    render(<Input rightIcon={<span data-testid='right-icon'>*</span>} />);
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<Input disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<Input className='custom-class' />);
    expect(screen.getByRole('textbox')).toHaveClass('custom-class');
  });

  it('generates unique id when not provided', () => {
    render(<Input label='Input 1' />);
    render(<Input label='Input 2' />);

    const inputs = screen.getAllByRole('textbox');
    expect(inputs[0]).toHaveAttribute('id');
    expect(inputs[1]).toHaveAttribute('id');
    expect(inputs[0].id).not.toBe(inputs[1].id);
  });

  it('uses provided id', () => {
    render(<Input id='custom-id' />);
    expect(screen.getByRole('textbox')).toHaveAttribute('id', 'custom-id');
  });
});
