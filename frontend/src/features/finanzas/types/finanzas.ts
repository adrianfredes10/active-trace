export type LiquidacionSegmento = "general" | "nexo" | "factura";

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
