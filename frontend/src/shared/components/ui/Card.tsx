import { cn } from "@/shared/lib/utils";

type CardProps = {
  children: React.ReactNode;
  className?: string;
};

export function Card({ children, className }: CardProps) {
  return (
    <div className={cn("rounded-lg border border-border bg-surface-card shadow-sm", className)}>
      {children}
    </div>
  );
}
