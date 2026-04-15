"use client";

import * as React from "react";
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
    <div className="min-h-screen flex items-center justify-center bg-[#080a0c] p-4">
      <div className="max-w-md w-full rounded-xl border border-[#1c2128] bg-[#0f1115] p-6">
        {/* Icon */}
        <div className="flex justify-center mb-4">
          <div className="h-12 w-12 rounded-full bg-[#f85149]/10 flex items-center justify-center">
            <AlertTriangle className="h-6 w-6 text-[#f85149]" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-center text-[15px] font-semibold text-[#e6edf3] mb-2">
          Something went wrong
        </h1>

        {/* Message */}
        <p className="text-center text-[12px] text-[#6e7681] mb-4">
          An unexpected error occurred. This has been logged and our team will look into it.
        </p>

        {/* Error Details (Development Only) */}
        {process.env.NODE_ENV === "development" && error && (
          <details className="mb-4">
            <summary className="cursor-pointer text-[11px] text-[#484f58] hover:text-[#8b949e] mb-2">
              Error details
            </summary>
            <div className="p-3 rounded-md bg-[#161b22] border border-[#30363d]">
              <pre className="text-[10px] text-[#f85149] overflow-auto max-h-40">
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
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#58a6ff] text-[#0d1117] rounded-lg font-medium hover:bg-[#6eb5ff] transition-colors text-[13px]"
          >
            <RefreshCw className="w-4 h-4" />
            Try again
          </button>
          <a
            href="/"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[#161b22] text-[#e6edf3] border border-[#30363d] rounded-lg font-medium hover:bg-[#21262d] transition-colors text-[13px]"
          >
            <Home className="w-4 h-4" />
            Go home
          </a>
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
        "rounded-lg border border-[#f85149]/20 bg-[#f85149]/5 p-4",
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-4 h-4 text-[#f85149] shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-[12px] font-medium text-[#e6edf3]">{title}</p>
          <p className="text-[11px] text-[#6e7681] mt-0.5">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-[#484f58] hover:text-[#8b949e] transition-colors"
            aria-label="Dismiss error"
          >
            ×
          </button>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 flex items-center gap-1.5 text-[11px] text-[#58a6ff] hover:text-[#79b8ff] transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
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
