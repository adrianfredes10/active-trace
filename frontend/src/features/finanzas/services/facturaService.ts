import type { FacturaItem } from "@/features/finanzas/types/finanzas";
import { api } from "@/shared/services/api";

export async function fetchFacturas(periodo: string): Promise<FacturaItem[]> {
  const { data } = await api.get<{ items: FacturaItem[] }>("/api/facturas", {
    params: { periodo },
  });
  return data.items;
}

export async function crearFactura(payload: {
  usuario_id: string;
  periodo: string;
  detalle: string;
  referencia_archivo?: string;
  tamano_kb?: number;
}): Promise<FacturaItem> {
  const { data } = await api.post<FacturaItem>("/api/facturas", payload);
  return data;
}

export async function abonarFactura(facturaId: string): Promise<FacturaItem> {
  const { data } = await api.post<FacturaItem>(`/api/facturas/${facturaId}/abonar`);
  return data;
}
