import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  description?: string;
  inputSize?: "sm" | "md" | "lg";
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = "text",
      label,
      error,
      description,
      inputSize = "md",
      leftIcon,
      rightIcon,
      id,
      ...props
    },
    ref
  ) => {
    const fallbackId = React.useId();
    const inputId = id || fallbackId;
    const errorId = error ? `${inputId}-error` : undefined;
    const descriptionId = description ? `${inputId}-description` : undefined;

    const sizeStyles = {
      sm: "h-8 px-2.5 text-[12px]",
      md: "h-9 px-space-3 text-[13px]",
      lg: "h-10 px-3.5 text-[14px]",
    };

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-[12px] font-medium text-text-muted"
          >
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
              {leftIcon}
            </div>
          )}

          <input
            id={inputId}
            type={type}
            ref={ref}
            aria-invalid={error ? "true" : undefined}
            aria-describedby={cn(
              descriptionId,
              error && errorId
            )}
            className={cn(
              "flex w-full rounded-md border bg-surface text-text-primary transition-colors",
              "placeholder:text-text-placeholder",
              "focus:outline-none focus:ring-2 focus:ring-accent-blue focus:ring-offset-2 focus:ring-offset-canvas",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "read-only:cursor-default read-only:bg-elevated",
              {
                "border-border-default hover:border-border-hover": !error,
                "border-accent-red focus:ring-accent-red": error,
                "pl-9": leftIcon,
                "pr-9": rightIcon,
              },
              sizeStyles[inputSize],
              className
            )}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
              {rightIcon}
            </div>
          )}
        </div>

        {description && !error && (
          <p id={descriptionId} className="text-[var(--ui-text-xs)] text-text-placeholder">
            {description}
          </p>
        )}

        {error && (
          <p id={errorId} className="text-[var(--ui-text-xs)] text-accent-red" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
