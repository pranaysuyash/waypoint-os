import * as React from "react";
import { cn } from "@/lib/utils";
import { iconButtonProps } from "@/lib/accessibility";

export interface IconWrapperProps {
  children: React.ReactNode;
  label?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  color?: string;
}

const sizeMap = {
  sm: "size-3",
  md: "size-4",
  lg: "size-5",
};

/**
 * Icon wrapper that ensures icons are properly hidden from screen readers
 * and optionally provides a label for decorative icons that need context.
 */
export function IconWrapper({ children, label, className, size = "md", color }: IconWrapperProps) {
  return (
    <span
      className={cn("inline-flex shrink-0", sizeMap[size], className)}
      style={{ color }}
      aria-hidden={label ? undefined : "true"}
      {...(label && { "aria-label": label, role: "img" })}
    >
      {children}
    </span>
  );
}

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  label: string;
  variant?: "ghost" | "subtle" | "solid";
  size?: "sm" | "md" | "lg";
  color?: "blue" | "green" | "amber" | "red" | "neutral";
}

const variantStyles = {
  ghost: "hover:bg-elevated active:bg-highlight",
  subtle: "bg-surface border border-border-default hover:border-border-hover",
  solid: "border-transparent",
};

const colorStyles = {
  blue: "text-accent-blue hover:bg-[rgba(var(--accent-blue-rgb)/0.1)]",
  green: "text-accent-green hover:bg-[rgba(var(--accent-green-rgb)/0.1)]",
  amber: "text-accent-amber hover:bg-[rgba(var(--accent-amber-rgb)/0.1)]",
  red: "text-accent-red hover:bg-[rgba(var(--accent-red-rgb)/0.1)]",
  neutral: "text-text-muted hover:text-text-primary",
};

const sizeStyles = {
  sm: "p-1.5 rounded-md",
  md: "p-space-2 rounded-lg",
  lg: "p-2.5 rounded-lg",
};

/**
 * Accessible icon button with proper ARIA attributes
 */
export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon,
      label,
      variant = "ghost",
      size = "md",
      color = "neutral",
      className,
      type = "button",
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          "inline-flex items-center justify-center transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-accent-blue focus:ring-offset-2 focus:ring-offset-canvas",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          variantStyles[variant],
          colorStyles[color],
          sizeStyles[size],
          className
        )}
        aria-label={label}
        {...props}
      >
        <span className={sizeMap[size]} aria-hidden="true">
          {icon}
        </span>
      </button>
    );
  }
);
IconButton.displayName = "IconButton";

export interface IconLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  icon: React.ReactNode;
  label: string;
  size?: "sm" | "md" | "lg";
  color?: "blue" | "green" | "amber" | "red" | "neutral";
}

/**
 * Accessible icon link with proper ARIA attributes
 */
export const IconLink = React.forwardRef<HTMLAnchorElement, IconLinkProps>(
  (
    {
      icon,
      label,
      size = "md",
      color = "neutral",
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <a
        ref={ref}
        className={cn(
          "inline-flex items-center gap-1.5 transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-accent-blue focus:ring-offset-2 focus:ring-offset-canvas rounded-md",
          colorStyles[color],
          className
        )}
        aria-label={label}
        {...props}
      >
        <span className={sizeMap[size]} aria-hidden="true">
          {icon}
        </span>
        {children && <span>{children}</span>}
      </a>
    );
  }
);
IconLink.displayName = "IconLink";
