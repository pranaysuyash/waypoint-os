import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../button';

describe('Button Component', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const recordButtonActivation = vi.fn();
    render(<Button onClick={recordButtonActivation}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(recordButtonActivation).toHaveBeenCalledTimes(1);
  });

  it('applies default variant styles', () => {
    render(<Button>Default</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-accent-blue');
  });

  it('applies secondary variant styles', () => {
    render(<Button variant='secondary'>Secondary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-elevated');
    expect(button).toHaveClass('border');
  });

  it('applies ghost variant styles', () => {
    render(<Button variant='ghost'>Ghost</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('text-text-secondary');
  });

  it('applies destructive variant styles', () => {
    render(<Button variant='destructive'>Delete</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-accent-red');
  });

  it('applies outline variant styles', () => {
    render(<Button variant='outline'>Outline</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('border', 'bg-transparent');
  });

  it('applies size styles correctly', () => {
    const { container: smContainer } = render(<Button size='sm'>Small</Button>);
    const smBtn = smContainer.querySelector('button');
    expect(smBtn).toHaveClass('h-7');

    const { container: defaultContainer } = render(<Button>Default</Button>);
    const defaultBtn = defaultContainer.querySelector('button');
    expect(defaultBtn).toHaveClass('h-8');

    const { container: lgContainer } = render(<Button size='lg'>Large</Button>);
    const lgBtn = lgContainer.querySelector('button');
    expect(lgBtn).toHaveClass('h-10');
  });

  it('applies icon size styles', () => {
    render(<Button size='icon'>X</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('size-8');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('disabled:opacity-50');
  });

  it('does not call onClick when disabled', () => {
    const recordDisabledActivation = vi.fn();
    render(
      <Button onClick={recordDisabledActivation} disabled>
        Click me
      </Button>
    );

    fireEvent.click(screen.getByRole('button'));
    expect(recordDisabledActivation).not.toHaveBeenCalled();
  });

  it('applies custom className', () => {
    render(<Button className='custom-class'>Custom</Button>);
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  it('has proper accessibility attributes', () => {
    render(<Button aria-label='Close dialog'>&times;</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Close dialog');
  });

  it('has focus-visible ring styles', () => {
    render(<Button>Focus Test</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus-visible:ring-2');
  });

  it('has proper transition classes', () => {
    render(<Button>Transition</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('transition-all');
  });

  it('shows tooltip with disabledReason when disabled', () => {
    render(<Button disabled disabledReason="Complete the form first">Save changes</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    const tooltip = document.querySelector('[role="tooltip"]');
    expect(tooltip).toBeInTheDocument();
    expect(tooltip).toHaveTextContent('Complete the form first');
  });

  it('applies aria-describedby when disabledReason is set', () => {
    render(<Button disabled disabledReason="Missing required fields">Save</Button>);
    const button = screen.getByRole('button');
    const describedBy = button.getAttribute('aria-describedby');
    expect(describedBy).toBeTruthy();
    const tooltip = document.getElementById(describedBy!);
    expect(tooltip).toBeInTheDocument();
    expect(tooltip).toHaveTextContent('Missing required fields');
  });

  it('does not render tooltip when disabledReason is not set', () => {
    render(<Button disabled>Disabled</Button>);
    const tooltip = document.querySelector('[role="tooltip"]');
    expect(tooltip).not.toBeInTheDocument();
  });

  it('renders without wrapper when not disabled', () => {
    const { container } = render(<Button>Normal</Button>);
    expect(container.querySelector('span')).toBeNull();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
