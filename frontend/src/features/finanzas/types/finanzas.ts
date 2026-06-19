export type LiquidacionSegmento = "general" | "nexo" | "factura";

export type FacturaItem = {
  id: string;
  usuario_id: string;
  periodo: string;
  detalle: string;
  referencia_archivo: string | null;
  tamano_kb: string | null;
  estado: string;
  cargada_at: string;
  abonada_at: string | null;
};

export type LiquidacionItem = {
  id: string;
  periodo: string;
  segmento: LiquidacionSegmento;
  usuario_id: string;
  total: string;
  estado: "Abierta" | "Cerrada";
  es_nexo: boolean;
  excluido_por_factura: boolean;
};

export type LiquidacionKpis = {
  total_general: string;
  total_nexo: string;
  total_factura: string;
  cantidad_abiertas: number;
};

export type SalarioBaseItem = {
  id: string;
  rol: string;
  monto: string;
  vig_desde: string;
  vig_hasta: string | null;
};
