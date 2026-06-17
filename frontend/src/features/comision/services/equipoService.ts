import { api } from "@/shared/services/api";
import type { EquipoListResponse } from "@/features/comision/types/comision";

export async function fetchMisEquipos(soloVigentes = true): Promise<EquipoListResponse> {
  const { data } = await api.get<EquipoListResponse>("/api/equipos/mis-equipos", {
    params: { solo_vigentes: soloVigentes },
  });
  return data;
}
