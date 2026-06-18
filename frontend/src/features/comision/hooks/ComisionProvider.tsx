import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";

import { fetchMisEquipos } from "@/features/comision/services/equipoService";
import type { ComisionContexto } from "@/features/comision/types/comision";
import {
  buildComisionWorkspaces,
  type ComisionWorkspace,
} from "@/features/comision/utils/comisionWorkspaces";

type ComisionContextValue = {
  workspaces: ComisionWorkspace[];
  isLoading: boolean;
  selected: ComisionWorkspace | null;
  setWorkspaceKey: (key: string) => void;
  contexto: ComisionContexto | null;
};

const ComisionContext = createContext<ComisionContextValue | null>(null);

function toContexto(workspace: ComisionWorkspace): ComisionContexto | null {
  const item = workspace.asignacion;
  if (!item.materia_id || !item.cohorte_id) {
    return null;
  }
  return {
    asignacion_id: item.id,
    materia_id: item.materia_id,
    cohorte_id: item.cohorte_id,
    comision: workspace.comision,
  };
}

export function ComisionProvider({ children }: { children: ReactNode }) {
  const { data, isLoading } = useQuery({
    queryKey: ["mis-equipos"],
    queryFn: () => fetchMisEquipos(true),
  });

  const workspaces = useMemo(() => {
    const equipos = (data?.items ?? []).filter((e) => e.materia_id && e.cohorte_id);
    return buildComisionWorkspaces(equipos);
  }, [data]);

  const [workspaceKey, setWorkspaceKey] = useState<string | null>(null);

  const selected = useMemo(() => {
    if (workspaces.length === 0) return null;
    return workspaces.find((w) => w.key === workspaceKey) ?? workspaces[0];
  }, [workspaces, workspaceKey]);

  const value = useMemo<ComisionContextValue>(
    () => ({
      workspaces,
      isLoading,
      selected,
      setWorkspaceKey,
      contexto: selected ? toContexto(selected) : null,
    }),
    [workspaces, isLoading, selected],
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
