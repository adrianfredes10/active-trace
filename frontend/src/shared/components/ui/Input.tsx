import { cn } from "@/shared/lib/utils";

type InputProps = {
  label: string;
  error?: string;
} & React.ComponentPropsWithoutRef<"input">;

export function Input({ label, error, id, className, ...props }: InputProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-text-secondary" htmlFor={inputId}>
        {label}
      </label>
      <input
        id={inputId}
        className={cn(
          "w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm text-text-primary focus-ring",
          error && "border-status-danger",
          className,
        )}
        {...props}
      />
      {error && (
        <p className="mt-1 text-xs text-status-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
