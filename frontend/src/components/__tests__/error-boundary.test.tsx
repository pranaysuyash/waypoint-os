import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  ErrorBoundary,
  DefaultErrorFallback,
  InlineError,
  useErrorHandler,
  withErrorBoundary,
} from '../error-boundary';

function ExplodingChild() {
  throw new Error('boom');
  return null;
}

function ThrowWithHook() {
  const raise = useErrorHandler();
  raise(new Error('hook boom'));
  return null;
}

describe('error-boundary public helpers', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders the default fallback and lets callers reset the boundary state', () => {
    render(<DefaultErrorFallback error={new Error('failure detail')} resetError={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to overview' })).toHaveAttribute('href', '/overview');
  });

  it('catches child render failures and invokes the onError hook', () => {
    const onError = vi.fn();
    render(
      <ErrorBoundary onError={onError}>
        <ExplodingChild />
      </ErrorBoundary>
    );

    expect(screen.getByRole('heading', { name: 'Something went wrong' })).toBeInTheDocument();
    expect(onError).toHaveBeenCalledWith(expect.any(Error), expect.any(Object));
  });

  it('wraps components with a reusable error boundary HOC', () => {
    const Wrapped = withErrorBoundary(ExplodingChild, ({ error }) => <div role="alert">{error?.message}</div>);

    render(<Wrapped />);

    expect(screen.getByRole('alert')).toHaveTextContent('boom');
  });

  it('turns imperative errors into boundary-visible render errors', () => {
    render(
      <ErrorBoundary fallback={({ error }) => <div role="alert">{error?.message}</div>}>
        <ThrowWithHook />
      </ErrorBoundary>
    );

    expect(screen.getByRole('alert')).toHaveTextContent('hook boom');
  });

  it('renders inline component-level errors with retry and dismiss controls', () => {
    render(<InlineError title="Could not save" message="Retry later" onRetry={vi.fn()} onDismiss={vi.fn()} />);

    expect(screen.getByRole('alert')).toHaveTextContent('Could not save');
    expect(screen.getByRole('button', { name: 'Dismiss error' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument();
  });
});
