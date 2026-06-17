import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import { asignacionLabel } from "@/features/comision/utils/asignacionLabel";

export function ComisionContextBar() {
  const { equipos, isLoading, selected, setSelectedId } = useComisionContext();

  if (isLoading) {
    return <p className="text-sm text-slate-600">Cargando asignaciones…</p>;
  }

  if (equipos.length === 0) {
    return (
      <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        No tenés asignaciones vigentes con materia y cohorte.
      </p>
    );
  }

  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-slate-700">Asignación activa</span>
      <select
        className="max-w-md rounded-lg border border-slate-300 bg-white px-3 py-2"
        value={selected?.id ?? ""}
        onChange={(e) => setSelectedId(e.target.value)}
      >
        {equipos.map((e) => (
          <option key={e.id} value={e.id}>
            {asignacionLabel(e)}
          </option>
        ))}
      </select>
    </label>
  );
}
