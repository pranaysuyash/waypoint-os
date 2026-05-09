import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  description?: string;
  inputSize?: "sm" | "md" | "lg";
  resize?: "none" | "both" | "horizontal" | "vertical" | "block";
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      label,
      error,
      description,
      inputSize = "md",
      resize = "vertical",
      id,
      ...props
    },
    ref
  ) => {
    const fallbackId = React.useId();
    const textareaId = id || fallbackId;
    const errorId = error ? `${textareaId}-error` : undefined;
    const descriptionId = description ? `${textareaId}-description` : undefined;

    const sizeStyles = {
      sm: "px-2.5 py-2 text-[12px] min-h-[64px]",
      md: "px-space-3 py-space-2 text-[13px] min-h-[80px]",
      lg: "px-3.5 py-2.5 text-[14px] min-h-[96px]",
    };

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={textareaId}
            className="text-[12px] font-medium text-text-muted"
          >
            {label}
          </label>
        )}

        <textarea
          id={textareaId}
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
            },
            sizeStyles[inputSize],
            className
          )}
          style={{ resize }}
          {...props}
        />

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
Textarea.displayName = "Textarea";

export { Textarea };
