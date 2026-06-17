import { useCoordinacionContext } from "@/features/coordinacion/hooks/CoordinacionProvider";
import { asignacionLabel } from "@/features/comision/utils/asignacionLabel";

export function CoordinacionContextBar() {
  const { equipos, isLoading, selected, setSelectedId } = useCoordinacionContext();

  if (isLoading) {
    return <p className="text-sm text-slate-600">Cargando contexto…</p>;
  }

  if (equipos.length === 0) {
    return (
      <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        Sin asignaciones con materia, carrera y cohorte.
      </p>
    );
  }

  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-slate-700">Contexto académico</span>
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
