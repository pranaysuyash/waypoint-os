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
        {process.env.NODE_ENV === "development" && (
          <details className="mb-4">
            <summary className="cursor-pointer text-xs text-[#484f58] hover:text-[#8b949e] mb-2">
              Error details
            </summary>
            <div className="p-3 rounded-md bg-[#161b22] border border-[#30363d]">
              <pre className="text-xs text-[#f85149] overflow-auto max-h-40">
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
