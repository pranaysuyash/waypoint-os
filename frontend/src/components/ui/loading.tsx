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
  sm: "w-3 h-3",
  md: "w-5 h-5",
  lg: "w-8 h-8",
};

const colorMap = {
  blue: "border-[#58a6ff] border-t-transparent",
  green: "border-[#3fb950] border-t-transparent",
  amber: "border-[#d29922] border-t-transparent",
  red: "border-[#f85149] border-t-transparent",
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
      <span className="sr-only">Loading...</span>
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
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  (
    {
      className,
      variant = "rectangular",
      width,
      height,
      animation = "pulse",
      ...props
    },
    ref
  ) => {
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
          "bg-[#161b22]",
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
);
Skeleton.displayName = "Skeleton";

// ============================================================================
// SKELETON VARIANTS
// ============================================================================

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
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
    sm: "w-8 h-8",
    md: "w-10 h-10",
    lg: "w-12 h-12",
  };
  return <Skeleton variant="circular" className={sizeMap[size]} />;
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-xl border border-[#1c2128] bg-[#0f1115] p-4 space-y-3", className)}>
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
        "fixed inset-0 z-50 flex items-center justify-center bg-[#080a0c]/80",
        blur && "backdrop-blur-sm"
      )}
      role="status"
      aria-label="Loading content"
      aria-busy="true"
    >
      <div className="flex flex-col items-center gap-3">
        <Spinner size="lg" />
        {message && (
          <p className="text-[13px] text-[#8b949e]">{message}</p>
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

export function InlineLoading({ message = "Loading...", size = "sm" }: InlineLoadingProps) {
  return (
    <div className="flex items-center gap-2 text-[#8b949e]">
      <Spinner size={size} />
      <span className="text-[12px]">{message}</span>
    </div>
  );
}

export { Skeleton };
