import * as React from "react";
import { cn } from "@/lib/utils";

// ============================================================================
// SPINNER
// ============================================================================

export interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  color?: "blue" | "green" | "amber" | "red" | "white";
  className?: string;
}

const sizeMap = {
  sm: "size-3",
  md: "size-5",
  lg: "size-8",
};

const colorMap = {
  blue: "border-accent-blue border-t-transparent",
  green: "border-accent-green border-t-transparent",
  amber: "border-accent-amber border-t-transparent",
  red: "border-accent-red border-t-transparent",
  white: "border-white border-t-transparent",
};

export function Spinner({ size = "md", color = "blue", className }: SpinnerProps) {
  return (
    <div
      className={cn(
        "rounded-full border-2 animate-spin",
        sizeMap[size],
        colorMap[color],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading…</span>
    </div>
  );
}

// ============================================================================
// SKELETON
// ============================================================================

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  animation?: "pulse" | "wave" | "none";
  ref?: React.Ref<HTMLDivElement>;
}

function Skeleton({
  className,
  variant = "rectangular",
  width,
  height,
  animation = "pulse",
  ref,
  ...props
}: SkeletonProps) {
    const variantStyles = {
      text: "rounded max-w-full",
      circular: "rounded-full",
      rectangular: "rounded-md",
    };

    const animationStyles = {
      pulse: "animate-pulse",
      wave: "",
      none: "",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "bg-elevated",
          variantStyles[variant],
          animationStyles[animation],
          className
        )}
        style={{ width, height }}
        aria-hidden="true"
        {...props}
      />
    );
}

// ============================================================================
// SKELETON VARIANTS
// ============================================================================

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-space-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          height={14}
          className={cn(i === lines - 1 ? "w-3/4" : "w-full")}
        />
      ))}
    </div>
  );
}

export function SkeletonAvatar({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeMap = {
    sm: "size-8",
    md: "size-10",
    lg: "size-12",
  };
  return <Skeleton variant="circular" className={sizeMap[size]} />;
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border border-highlight bg-surface p-space-4 space-y-space-3", className)}>
      <Skeleton variant="rectangular" height={20} width="60%" />
      <Skeleton variant="text" />
      <Skeleton variant="text" />
      <Skeleton variant="rectangular" height={32} width="40%" className="mt-4" />
    </div>
  );
}

// ============================================================================
// LOADING OVERLAY
// ============================================================================

export interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  blur?: boolean;
}

export function LoadingOverlay({ isLoading, message, blur = true }: LoadingOverlayProps) {
  if (!isLoading) return null;

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center bg-[rgba(var(--bg-canvas-rgb)/0.8)]",
        blur && "backdrop-blur-sm"
      )}
      role="status"
      aria-label="Loading content"
      aria-busy="true"
    >
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        {message && (
          <p className="text-[13px] text-text-muted">{message}</p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// INLINE LOADING
// ============================================================================

export interface InlineLoadingProps {
  message?: string;
  size?: "sm" | "md" | "lg";
}

export function InlineLoading({ message = "Loading…", size = "sm" }: InlineLoadingProps) {
  return (
    <div className="flex items-center gap-2 text-text-muted">
      <Spinner size={size} />
      <span className="text-[12px]">{message}</span>
    </div>
  );
}

export { Skeleton };
