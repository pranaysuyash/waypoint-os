import * as React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "bordered" | "ghost";
  ref?: React.Ref<HTMLDivElement>;
}

function Card({ className, variant = "default", ref, ...props }: CardProps) {
  return (
    <div
      ref={ref}
      className={cn(
        "rounded-xl",
        {
          "bg-surface": variant === "default" || variant === "bordered",
          "bg-elevated shadow-lg": variant === "elevated",
          "bg-transparent": variant === "ghost",
          "border border-default": variant === "default" || variant === "elevated" || variant === "bordered",
        },
        className
      )}
      {...props}
    />
  );
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  ref?: React.Ref<HTMLDivElement>;
}

function CardHeader({ className, ref, ...props }: CardHeaderProps) {
  return (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 p-space-6", className)}
      {...props}
    />
  );
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: "h1" | "h2" | "h3" | "h4";
  ref?: React.Ref<HTMLHeadingElement>;
}

function CardTitle({ className, level = "h3", children, ref, ...props }: CardTitleProps) {
  const Tag = level;
  const sizeClasses = {
     h1: "text-[var(--ui-text-lg)] font-semibold",
     h2: "text-[var(--ui-text-base)] font-semibold",
     h3: "text-[var(--ui-text-sm)] font-semibold",
     h4: "text-[var(--ui-text-sm)] font-medium",
  };

  return (
    <Tag
      ref={ref}
      className={cn(sizeClasses[level], "leading-tight tracking-tight", className)}
      {...props}
    >
      {children}
    </Tag>
  );
}

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  ref?: React.Ref<HTMLParagraphElement>;
}

function CardDescription({ className, ref, ...props }: CardDescriptionProps) {
  return (
    <p
      ref={ref}
       className={cn("text-[var(--ui-text-sm)] text-text-muted", className)}
      {...props}
    />
  );
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  ref?: React.Ref<HTMLDivElement>;
}

function CardContent({ className, ref, ...props }: CardContentProps) {
  return <div ref={ref} className={cn("p-space-6 pt-0", className)} {...props} />;
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  ref?: React.Ref<HTMLDivElement>;
}

function CardFooter({ className, ref, ...props }: CardFooterProps) {
  return (
    <div
      ref={ref}
      className={cn("flex items-center p-space-6 pt-0", className)}
      {...props}
    />
  );
}

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
