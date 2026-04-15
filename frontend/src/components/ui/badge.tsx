"use client";

import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium font-mono lowercase border transition-colors",
  {
    variants: {
      variant: {
        default: "bg-bg-elevated text-text-secondary border-border-default",
        explicit_user: "badge-explicit-user",
        explicit_owner: "badge-explicit-owner",
        derived: "badge-derived",
        hypothesis: "badge-hypothesis",
        manual: "badge-manual",
      },
      size: {
        default: "px-2 py-0.5 text-[10px]",
        sm: "px-1.5 py-0.5 text-[9px]",
        lg: "px-2.5 py-1 text-[11px]",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
