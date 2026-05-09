"use client";

import * as React from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================================
// ERROR BOUNDARY
// ============================================================================

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorFallbackProps {
  error: Error | null;
  resetError: () => void;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo);

    // Update state with error info
    this.setState({
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return (
        <FallbackComponent
          error={this.state.error}
          resetError={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

// ============================================================================
// DEFAULT ERROR FALLBACK
// ============================================================================

export function DefaultErrorFallback({
  error,
  resetError,
}: ErrorFallbackProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-canvas)] p-4">
      <div className="max-w-md w-full rounded-xl border border-[var(--border-default)] bg-[var(--bg-surface)] p-6">
        {/* Icon */}
        <div className="flex justify-center mb-4">
          <div className="size-12 rounded-full bg-[var(--accent-red)]/10 flex items-center justify-center">
            <AlertTriangle className="size-6 text-[var(--accent-red)]" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-center text-[15px] font-semibold text-[var(--text-primary)] mb-2">
          Something went wrong
        </h1>

        {/* Message */}
        <p className="text-center text-[12px] text-[var(--text-secondary)] mb-4">
          An unexpected error occurred. This has been logged and our team will look into it.
        </p>

        {/* Error Details (Development Only) */}
        {process.env.NODE_ENV === "development" && error && (
          <details className="mb-4">
            <summary className="cursor-pointer text-[var(--ui-text-xs)] text-[var(--text-placeholder)] hover:text-[var(--text-secondary)] mb-2">
              Error details
            </summary>
            <div className="p-3 rounded-md bg-[var(--bg-surface-hover)] border border-[var(--border-default)]">
              <pre className="text-[var(--ui-text-xs)] text-[var(--accent-red)] overflow-auto max-h-40">
                {error.message}
                {error.stack}
              </pre>
            </div>
          </details>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-2">
          <button
            onClick={resetError}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[var(--accent-blue)] text-[var(--text-on-accent)] rounded-lg font-medium hover:bg-[var(--accent-blue-hover)] transition-colors text-[13px]"
          >
            <RefreshCw className="size-4" />
            Try again
          </button>
          <Link
            href="/overview"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[var(--bg-surface-hover)] text-[var(--text-primary)] border border-[var(--border-default)] rounded-lg font-medium hover:bg-[var(--bg-count-badge)] transition-colors text-[13px]"
          >
            <Home className="size-4" />
            Back to overview
          </Link>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// INLINE ERROR (for component-level errors)
// ============================================================================

export interface InlineErrorProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export function InlineError({
  title = "Error",
  message,
  onRetry,
  onDismiss,
  className,
}: InlineErrorProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-[var(--accent-red)]/20 bg-[var(--accent-red)]/5 p-4",
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="size-4 text-[var(--accent-red)] shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-[12px] font-medium text-[var(--text-primary)]">{title}</p>
          <p className="text-[var(--ui-text-xs)] text-[var(--text-secondary)] mt-0.5">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-[var(--text-placeholder)] hover:text-[var(--text-secondary)] transition-colors"
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 flex items-center gap-1.5 text-[var(--ui-text-xs)] text-[var(--accent-blue)] hover:text-[var(--accent-blue-hover)] transition-colors"
        >
          <RefreshCw className="size-3" />
          Try again
        </button>
      )}
    </div>
  );
}

// ============================================================================
// HOOK: USE ERROR BOUNDARY (for functional components)
// ============================================================================

export function useErrorHandler() {
  return React.useCallback((error: Error) => {
    throw error;
  }, []);
}

// ============================================================================
// HOC: WITH ERROR BOUNDARY
// ============================================================================

export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorFallback?: React.ComponentType<ErrorFallbackProps>,
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
) {
  return function WithErrorBoundaryWrapper(props: P) {
    return (
      <ErrorBoundary fallback={errorFallback} onError={onError}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}
