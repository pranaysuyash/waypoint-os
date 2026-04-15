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
    const textareaId = id || React.useId();
    const errorId = error ? `${textareaId}-error` : undefined;
    const descriptionId = description ? `${textareaId}-description` : undefined;

    const sizeStyles = {
      sm: "px-2.5 py-2 text-[12px] min-h-[64px]",
      md: "px-3 py-2 text-[13px] min-h-[80px]",
      lg: "px-3.5 py-2.5 text-[14px] min-h-[96px]",
    };

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={textareaId}
            className="text-[12px] font-medium text-[#8b949e]"
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
            "flex w-full rounded-md border bg-[#0f1115] text-[#e6edf3] transition-colors",
            "placeholder:text-[#484f58]",
            "focus:outline-none focus:ring-2 focus:ring-[#58a6ff] focus:ring-offset-2 focus:ring-offset-[#080a0c]",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "read-only:cursor-default read-only:bg-[#161b22]",
            {
              "border-[#30363d] hover:border-[#8b949e]": !error,
              "border-[#f85149] focus:ring-[#f85149]": error,
            },
            sizeStyles[inputSize],
            className
          )}
          style={{ resize }}
          {...props}
        />

        {description && !error && (
          <p id={descriptionId} className="text-[11px] text-[#484f58]">
            {description}
          </p>
        )}

        {error && (
          <p id={errorId} className="text-[11px] text-[#f85149]" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };
