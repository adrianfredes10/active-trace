import { useQuery } from "@tanstack/react-query";

import { fetchLote } from "@/features/comision/services/comunicacionService";

type ComunicacionTrackingProps = {
  loteId: string;
};

const ESTADO_COLOR: Record<string, string> = {
  Pendiente: "bg-amber-100 text-amber-800",
  Enviando: "bg-blue-100 text-blue-800",
  Enviado: "bg-green-100 text-green-800",
  Error: "bg-red-100 text-red-800",
  Cancelado: "bg-slate-100 text-slate-600",
};

export function ComunicacionTracking({ loteId }: ComunicacionTrackingProps) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["comunicacion-lote", loteId],
    queryFn: () => fetchLote(loteId),
    refetchInterval: 3000,
  });

  if (isLoading) {
    return <p className="text-sm text-slate-600">Cargando estado del lote…</p>;
  }

  if (isError || !data) {
    return <p className="text-sm text-red-600">No se pudo cargar el tracking del lote.</p>;
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-slate-800">
        Tracking lote ({data.total} mensajes)
      </h3>
      <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white text-sm">
        {data.items.map((item) => (
          <li key={item.id} className="flex items-center justify-between px-4 py-2">
            <span className="truncate text-slate-700">{item.asunto}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                ESTADO_COLOR[item.estado] ?? "bg-slate-100 text-slate-600"
              }`}
            >
              {item.estado}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
