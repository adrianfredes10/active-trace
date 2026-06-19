export type BarChartItem = {
  label: string;
  value: number;
  colorClass?: string;
};

type SimpleBarChartProps = {
  items: BarChartItem[];
  emptyLabel?: string;
};

export function SimpleBarChart({ items, emptyLabel = "Sin datos." }: SimpleBarChartProps) {
  if (items.length === 0) {
    return <p className="text-sm text-text-secondary">{emptyLabel}</p>;
  }

  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <div className="space-y-3" role="img" aria-label="Gráfico de barras">
      {items.map((item) => {
        const widthPct = Math.round((item.value / max) * 100);
        return (
          <div key={item.label}>
            <div className="mb-1 flex items-center justify-between gap-2 text-xs">
              <span className="truncate text-text-secondary">{item.label}</span>
              <span className="shrink-0 font-medium tabular-nums text-text-primary">{item.value}</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-surface">
              <div
                className={`h-full rounded-full transition-all ${item.colorClass ?? "bg-accent-gold"}`}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
