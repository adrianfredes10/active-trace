import type { ReactNode } from "react";

type StatusVariant = "success" | "warning" | "danger" | "info" | "neutral";

const VARIANT_CLASSES: Record<StatusVariant, string> = {
  success: "bg-status-success-soft text-status-success",
  warning: "bg-status-warning-soft text-status-warning",
  danger: "bg-status-danger-soft text-status-danger",
  info: "bg-status-info-soft text-status-info",
  neutral: "bg-surface text-text-secondary",
};

type StatusBadgeProps = {
  variant: StatusVariant;
  children: ReactNode;
  className?: string;
};

export function StatusBadge({ variant, children, className = "" }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
