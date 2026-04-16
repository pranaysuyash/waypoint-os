import * as React from "react";
import { cn } from "@/lib/utils";
import { COLORS } from "@/lib/tokens";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "bordered" | "ghost";
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl",
          {
            "bg-[#0f1115]": variant === "default" || variant === "bordered",
            "bg-[#161b22] shadow-lg": variant === "elevated",
            "bg-transparent": variant === "ghost",
            "border border-[#1c2128]": variant === "default" || variant === "elevated" || variant === "bordered",
          },
          className
        )}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    />
  )
);
CardHeader.displayName = "CardHeader";

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: "h1" | "h2" | "h3" | "h4";
}

const CardTitle = React.forwardRef<HTMLParagraphElement, CardTitleProps>(
  ({ className, level = "h3", children, ...props }, ref) => {
    const Tag = level;
    const sizeClasses = {
      h1: "text-[15px] font-semibold",
      h2: "text-[14px] font-semibold",
      h3: "text-[13px] font-semibold",
      h4: "text-[12px] font-semibold",
    };

    return (
      <Tag
        ref={ref}
        className={cn(sizeClasses[level], "leading-none tracking-tight", className)}
        {...props}
      >
        {children}
      </Tag>
    );
  }
);
CardTitle.displayName = "CardTitle";

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-xs text-[#6e7681]", className)}
      {...props}
    />
  )
);
CardDescription.displayName = "CardDescription";

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center p-6 pt-0", className)}
      {...props}
    />
  )
);
CardFooter.displayName = "CardFooter";

export interface CardAccentProps {
  color?: keyof typeof COLORS;
  position?: "left" | "top" | "right" | "bottom";
}

export function CardAccent({ color = "accentBlue", position = "left" }: CardAccentProps) {
  const colorValue = COLORS[color as keyof typeof COLORS] || COLORS.accentBlue;

  const positionStyles: Record<typeof position, string> = {
    left: "left-0 top-4 bottom-4 w-0.5 rounded-r",
    top: "top-0 left-4 right-4 h-0.5 rounded-b",
    right: "right-0 top-4 bottom-4 w-0.5 rounded-l",
    bottom: "bottom-0 left-4 right-4 h-0.5 rounded-t",
  };

  return (
    <div
      className={`absolute ${positionStyles[position]} transition-colors`}
      style={{ backgroundColor: colorValue }}
      aria-hidden="true"
    />
  );
}

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
