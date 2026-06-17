import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchMisEquipos } from "@/features/comision/services/equipoService";
import type { AsignacionItem } from "@/features/comision/types/comision";
import type { ComisionContexto } from "@/features/coordinacion/types/coordinacion";

type CoordinacionContextValue = {
  equipos: AsignacionItem[];
  isLoading: boolean;
  selected: AsignacionItem | null;
  setSelectedId: (id: string) => void;
  contexto: ComisionContexto | null;
};

const CoordinacionContext = createContext<CoordinacionContextValue | null>(null);

function toContexto(item: AsignacionItem): ComisionContexto | null {
  if (!item.materia_id || !item.cohorte_id || !item.carrera_id) {
    return null;
  }
  return {
    asignacion_id: item.id,
    materia_id: item.materia_id,
    cohorte_id: item.cohorte_id,
    carrera_id: item.carrera_id,
  };
}

export function CoordinacionProvider({ children }: { children: ReactNode }) {
  const { data, isLoading } = useQuery({
    queryKey: ["mis-equipos-coord"],
    queryFn: () => fetchMisEquipos(true),
  });

  const equipos = useMemo(
    () =>
      (data?.items ?? []).filter((e) => e.materia_id && e.cohorte_id && e.carrera_id),
    [data],
  );

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(() => {
    if (equipos.length === 0) {
      return null;
    }
    return equipos.find((e) => e.id === selectedId) ?? equipos[0];
  }, [equipos, selectedId]);

  const value = useMemo<CoordinacionContextValue>(
    () => ({
      equipos,
      isLoading,
      selected,
      setSelectedId,
      contexto: selected ? toContexto(selected) : null,
    }),
    [equipos, isLoading, selected],
  );

  return (
    <CoordinacionContext.Provider value={value}>{children}</CoordinacionContext.Provider>
  );
}

export function useCoordinacionContext(): CoordinacionContextValue {
  const ctx = useContext(CoordinacionContext);
  if (!ctx) {
    throw new Error("useCoordinacionContext requiere CoordinacionProvider");
  }
  return ctx;
}
