import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import {
  Spinner,
  Skeleton,
  LoadingOverlay,
  InlineLoading,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
} from '../loading';

describe('Spinner Component', () => {
  it('renders with default props', () => {
    const { container } = render(<Spinner />);
    const spinner = within(container).getByRole('status');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
  });

  it('applies size classes correctly', () => {
    const { container: smContainer } = render(<Spinner size='sm' />);
    expect(smContainer.firstChild).toHaveClass('w-3');

    const { container: lgContainer } = render(<Spinner size='lg' />);
    expect(lgContainer.firstChild).toHaveClass('w-8');
  });

  it('applies color classes correctly', () => {
    const { container: greenContainer } = render(<Spinner color='green' />);
    expect(greenContainer.firstChild).toHaveClass('border-accent-green');

    const { container: redContainer } = render(<Spinner color='red' />);
    expect(redContainer.firstChild).toHaveClass('border-accent-red');
  });

  it('has sr-only text for screen readers', () => {
    const { container } = render(<Spinner />);
    expect(within(container).getByText('Loading...')).toHaveClass('sr-only');
  });
});

describe('Skeleton Component', () => {
  it('renders with default rectangular variant', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass('rounded-md');
  });

  it('applies variant styles correctly', () => {
    const { container: circularContainer } = render(<Skeleton variant='circular' />);
    expect(circularContainer.firstChild).toHaveClass('rounded-full');

    const { container: textContainer } = render(<Skeleton variant='text' />);
    expect(textContainer.firstChild).toHaveClass('rounded');
  });

  it('applies custom width and height', () => {
    const { container } = render(<Skeleton width='100px' height='50px' />);
    const skeleton = container.firstChild as HTMLElement;
    expect(skeleton.style.width).toBe('100px');
    expect(skeleton.style.height).toBe('50px');
  });

  it('has aria-hidden attribute', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveAttribute('aria-hidden', 'true');
  });
});

describe('SkeletonText Component', () => {
  it('renders specified number of lines', () => {
    const { container } = render(<SkeletonText lines={3} />);
    expect(container.querySelectorAll('div.bg-elevated')).toHaveLength(3);
  });

  it('last line is shorter than others', () => {
    const { container } = render(<SkeletonText lines={3} />);
    const skeletons = container.querySelectorAll('[class*="bg-elevated"]');
    const lastSkeleton = skeletons[skeletons.length - 1] as HTMLElement;
    expect(lastSkeleton).toHaveClass('w-3/4');
  });
});

describe('SkeletonAvatar Component', () => {
  it('renders circular avatar', () => {
    const { container } = render(<SkeletonAvatar />);
    expect(container.firstChild).toHaveClass('rounded-full');
  });

  it('applies size classes correctly', () => {
    const { container: smContainer } = render(<SkeletonAvatar size='sm' />);
    expect(smContainer.firstChild).toHaveClass('w-8');

    const { container: lgContainer } = render(<SkeletonAvatar size='lg' />);
    expect(lgContainer.firstChild).toHaveClass('w-12');
  });
});

describe('SkeletonCard Component', () => {
  it('renders card structure', () => {
    const { container } = render(<SkeletonCard />);
    expect(container.firstChild).toHaveClass('rounded-xl', 'border');
  });
});

describe('LoadingOverlay Component', () => {
  it('does not render when not loading', () => {
    const { container } = render(<LoadingOverlay isLoading={false} />);
    expect(container.firstChild).toBe(null);
  });

  it('renders when loading', () => {
    const { container } = render(<LoadingOverlay isLoading={true} />);
    expect(container.firstChild).toBeInTheDocument();
    // The outer div has aria-label="Loading content"
    expect(container.firstChild).toHaveAttribute('aria-label', 'Loading content');
  });

  it('displays custom message', () => {
    const { container } = render(<LoadingOverlay isLoading={true} message='Please wait...' />);
    expect(within(container).getByText('Please wait...')).toBeInTheDocument();
  });

  it('has aria-busy attribute when loading', () => {
    const { container } = render(<LoadingOverlay isLoading={true} />);
    expect(container.firstChild).toHaveAttribute('aria-busy', 'true');
  });
});

describe('InlineLoading Component', () => {
  it('renders with default message', () => {
    const { container } = render(<InlineLoading />);
    // Find the visible message (not the sr-only one in spinner)
    const visibleMessage = container.querySelector('.text-\\[12px\\]');
    expect(visibleMessage).toBeInTheDocument();
    expect(visibleMessage?.textContent).toBe('Loading...');
  });

  it('renders custom message', () => {
    const { container } = render(<InlineLoading message='Processing...' />);
    const visibleMessage = container.querySelector('.text-\\[12px\\]');
    expect(visibleMessage?.textContent).toBe('Processing...');
  });

  it('contains a Spinner', () => {
    const { container } = render(<InlineLoading size='lg' />);
    expect(within(container).getByRole('status')).toBeInTheDocument();
  });
});
