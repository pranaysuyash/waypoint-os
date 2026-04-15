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
  sm: "w-3 h-3",
  md: "w-4 h-4",
  lg: "w-5 h-5",
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
  ghost: "hover:bg-[#161b22] active:bg-[#1c2128]",
  subtle: "bg-[#0f1115] border border-[#30363d] hover:border-[#8b949e]",
  solid: "border-transparent",
};

const colorStyles = {
  blue: "text-[#58a6ff] hover:bg-[#58a6ff]/10",
  green: "text-[#3fb950] hover:bg-[#3fb950]/10",
  amber: "text-[#d29922] hover:bg-[#d29922]/10",
  red: "text-[#f85149] hover:bg-[#f85149]/10",
  neutral: "text-[#8b949e] hover:text-[#e6edf3]",
};

const sizeStyles = {
  sm: "p-1.5 rounded-md",
  md: "p-2 rounded-lg",
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
          "focus:outline-none focus:ring-2 focus:ring-[#58a6ff] focus:ring-offset-2 focus:ring-offset-[#080a0c]",
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
          "focus:outline-none focus:ring-2 focus:ring-[#58a6ff] focus:ring-offset-2 focus:ring-offset-[#080a0c] rounded-md",
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
