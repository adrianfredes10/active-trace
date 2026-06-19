import { Button } from "@/shared/components/ui/Button";

type PageHeaderAction = {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary";
};

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  actions?: PageHeaderAction[];
};

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-text-secondary">{subtitle}</p>}
      </div>
      {actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <Button
              key={action.label}
              type="button"
              variant={action.variant === "secondary" ? "secondary" : "primary"}
              size="sm"
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
