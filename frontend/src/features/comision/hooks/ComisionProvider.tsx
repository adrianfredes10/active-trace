import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchMisEquipos } from "@/features/comision/services/equipoService";
import type { AsignacionItem, ComisionContexto } from "@/features/comision/types/comision";

type ComisionContextValue = {
  equipos: AsignacionItem[];
  isLoading: boolean;
  selected: AsignacionItem | null;
  setSelectedId: (id: string) => void;
  contexto: ComisionContexto | null;
};

const ComisionContext = createContext<ComisionContextValue | null>(null);

function toContexto(item: AsignacionItem): ComisionContexto | null {
  if (!item.materia_id || !item.cohorte_id) {
    return null;
  }
  return {
    asignacion_id: item.id,
    materia_id: item.materia_id,
    cohorte_id: item.cohorte_id,
  };
}

export function ComisionProvider({ children }: { children: ReactNode }) {
  const { data, isLoading } = useQuery({
    queryKey: ["mis-equipos"],
    queryFn: () => fetchMisEquipos(true),
  });

  const equipos = useMemo(
    () => (data?.items ?? []).filter((e) => e.materia_id && e.cohorte_id),
    [data],
  );

  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selected = useMemo(() => {
    if (equipos.length === 0) {
      return null;
    }
    const found = equipos.find((e) => e.id === selectedId);
    return found ?? equipos[0];
  }, [equipos, selectedId]);

  const value = useMemo<ComisionContextValue>(
    () => ({
      equipos,
      isLoading,
      selected,
      setSelectedId: setSelectedId,
      contexto: selected ? toContexto(selected) : null,
    }),
    [equipos, isLoading, selected],
  );

  return <ComisionContext.Provider value={value}>{children}</ComisionContext.Provider>;
}

export function useComisionContext(): ComisionContextValue {
  const ctx = useContext(ComisionContext);
  if (!ctx) {
    throw new Error("useComisionContext debe usarse dentro de ComisionProvider");
  }
  return ctx;
}
