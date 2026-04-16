import * as React from "react";
import { cn } from "@/lib/utils";
import { COLORS } from "@/lib/tokens";

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
    const inputId = id || React.useId();
    const errorId = error ? `${inputId}-error` : undefined;
    const descriptionId = description ? `${inputId}-description` : undefined;

    const sizeStyles = {
      sm: "h-8 px-2.5 text-[12px]",
      md: "h-9 px-3 text-[13px]",
      lg: "h-10 px-3.5 text-[14px]",
    };

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-[12px] font-medium text-[#8b949e]"
          >
            {label}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#6e7681] pointer-events-none">
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
              "flex w-full rounded-md border bg-[#0f1115] text-[#e6edf3] transition-colors",
              "placeholder:text-[#484f58]",
              "focus:outline-none focus:ring-2 focus:ring-[#58a6ff] focus:ring-offset-2 focus:ring-offset-[#080a0c]",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "read-only:cursor-default read-only:bg-[#161b22]",
              {
                "border-[#30363d] hover:border-[#8b949e]": !error,
                "border-[#f85149] focus:ring-[#f85149]": error,
                "pl-9": leftIcon,
                "pr-9": rightIcon,
              },
              sizeStyles[inputSize],
              className
            )}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6e7681] pointer-events-none">
              {rightIcon}
            </div>
          )}
        </div>

        {description && !error && (
          <p id={descriptionId} className="text-xs text-[#484f58]">
            {description}
          </p>
        )}

        {error && (
          <p id={errorId} className="text-xs text-[#f85149]" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";

export { Input };
