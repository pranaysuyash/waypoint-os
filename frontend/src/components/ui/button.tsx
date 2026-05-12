"use client";

import React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
   "inline-flex items-center justify-center gap-space-2 whitespace-nowrap rounded-lg text-[var(--ui-text-sm)] font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-blue focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-accent-blue text-text-on-accent hover:bg-accent-blue-hover",
        secondary: "bg-elevated text-text-primary border border-border-default hover:bg-highlight hover:border-border-hover",
        ghost: "text-text-secondary hover:text-text-primary hover:bg-elevated",
        destructive: "bg-accent-red text-white hover:bg-accent-red/80",
        outline: "border border-border-default bg-transparent hover:bg-elevated hover:border-border-hover",
      },
      size: {
        default: "h-8 px-space-4 py-space-2",
         sm: "h-7 px-space-3 text-[var(--ui-text-xs)]",
         lg: "h-10 px-space-6 text-[var(--ui-text-base)]",
        icon: "size-8",
         xl: "h-11 px-space-8 text-[var(--ui-text-base)]",
        touch: "h-11 px-space-4 text-[var(--ui-text-sm)]",
        "icon-lg": "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  ref?: React.Ref<HTMLButtonElement>;
  disabledReason?: string;
}

function Button({ className, variant, size, asChild = false, ref, disabledReason, disabled, children, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : "button";
  const tooltipId = React.useId();

  const button = (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      disabled={disabled}
      aria-describedby={disabled && disabledReason ? tooltipId : undefined}
      {...props}
    >
      {children}
    </Comp>
  );

  if (!disabled || !disabledReason) {
    return button;
  }

  return (
    <span className="relative inline-flex group">
      {button}
      <span
        id={tooltipId}
        role="tooltip"
        className="invisible group-hover:visible group-focus-within:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-max max-w-[240px] rounded-md bg-[#1c2128] px-2.5 py-1.5 text-xs leading-tight text-[#e6edf3] shadow-lg pointer-events-none"
      >
        {disabledReason}
      </span>
    </span>
  );
}

export { Button, buttonVariants };
