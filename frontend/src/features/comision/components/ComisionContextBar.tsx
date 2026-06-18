import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import { workspaceLabel } from "@/features/comision/utils/comisionWorkspaces";

export function ComisionContextBar() {
  const { workspaces, isLoading, selected, setWorkspaceKey } = useComisionContext();

  if (isLoading) {
    return <p className="text-sm text-text-secondary">Cargando asignaciones…</p>;
  }

  if (workspaces.length === 0) {
    return (
      <p className="rounded-md border border-status-warning/30 bg-status-warning-soft px-4 py-3 text-sm text-status-warning">
        No tenés asignaciones vigentes. Pedí al administrador que cree tu usuario con materia y
        comisión.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2 rounded-md border border-border bg-surface-card p-4 sm:flex-row sm:items-end sm:justify-between">
      <label className="flex min-w-0 flex-1 flex-col gap-1 text-sm">
        <span className="font-medium text-text-primary">Comisión activa</span>
        <select
          className="max-w-xl rounded-md border border-border bg-surface px-3 py-2 text-sm"
          value={selected?.key ?? ""}
          onChange={(e) => setWorkspaceKey(e.target.value)}
        >
          {workspaces.map((w) => (
            <option key={w.key} value={w.key}>
              {workspaceLabel(w)}
            </option>
          ))}
        </select>
      </label>
      {selected?.comision && (
        <p className="text-xs text-text-secondary">
          Padrón filtrado a comisión <strong className="text-text-primary">{selected.comision}</strong>
        </p>
      )}
    </div>
  );
}
