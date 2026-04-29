import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  label?: string;
  error?: string;
  description?: string;
  inputSize?: "sm" | "md" | "lg";
  options: SelectOption[];
  placeholder?: string;
  emptyText?: string;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      label,
      error,
      description,
      inputSize = "md",
      options,
      placeholder = "Select an option...",
      emptyText = "No options available",
      id,
      ...props
    },
    ref
  ) => {
    const selectId = id || React.useId();
    const errorId = error ? `${selectId}-error` : undefined;
    const descriptionId = description ? `${selectId}-description` : undefined;

    const sizeStyles = {
      sm: "h-8 px-2.5 text-[12px]",
      md: "h-9 px-space-3 text-[13px]",
      lg: "h-10 px-3.5 text-[14px]",
    };

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={selectId}
            className="text-[12px] font-medium text-text-muted"
          >
            {label}
          </label>
        )}

        <div className="relative">
          <select
            id={selectId}
            ref={ref}
            aria-invalid={error ? "true" : undefined}
            aria-describedby={cn(
              descriptionId,
              error && errorId
            )}
            className={cn(
              "flex w-full appearance-none rounded-md border bg-surface text-text-primary transition-colors",
              "focus:outline-none focus:ring-2 focus:ring-accent-blue focus:ring-offset-2 focus:ring-offset-canvas",
              "disabled:cursor-not-allowed disabled:opacity-50",
              {
                "border-border-default hover:border-border-hover": !error,
                "border-accent-red focus:ring-accent-red": error,
              },
              sizeStyles[inputSize],
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.length === 0 ? (
              <option disabled>{emptyText}</option>
            ) : (
              options.map((option) => (
                <option
                  key={option.value}
                  value={option.value}
                  disabled={option.disabled}
                >
                  {option.label}
                </option>
              ))
            )}
          </select>

          {/* Custom arrow indicator */}
          <div
            className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted"
            aria-hidden="true"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M3 4.5L6 7.5L9 4.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
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
Select.displayName = "Select";

export { Select };
