"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to error reporting service
    console.error("Application error:", error);
  }, [error]);

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
        {process.env.NODE_ENV === "development" && (
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
            onClick={reset}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[var(--accent-blue)] text-[var(--text-on-accent)] rounded-lg font-medium hover:bg-[var(--accent-blue-hover)] transition-colors text-[13px]"
          >
            <RefreshCw className="size-4" />
            Try again
          </button>
          <a
            href="/overview"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[var(--bg-surface-hover)] text-[var(--text-primary)] border border-[var(--border-default)] rounded-lg font-medium hover:bg-[var(--bg-count-badge)] transition-colors text-[13px]"
          >
            <Home className="size-4" />
            Back to overview
          </a>
        </div>
      </div>
    </div>
  );
}
