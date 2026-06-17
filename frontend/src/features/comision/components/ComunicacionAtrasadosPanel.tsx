import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useComisionContext } from "@/features/comision/hooks/ComisionProvider";
import { fetchAtrasados } from "@/features/comision/services/analisisService";
import {
  enviarComunicacion,
  previewComunicacion,
} from "@/features/comision/services/comunicacionService";
import { ComunicacionTracking } from "@/features/comision/components/ComunicacionTracking";

export function ComunicacionAtrasadosPanel() {
  const { contexto } = useComisionContext();
  const [asunto, setAsunto] = useState("Recordatorio de entregas pendientes");
  const [cuerpo, setCuerpo] = useState(
    "Hola {{nombre}}, tenés actividades pendientes en la materia.",
  );
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);
  const [loteId, setLoteId] = useState<string | null>(null);

  const atrasados = useQuery({
    queryKey: ["atrasados-com", contexto],
    queryFn: () => fetchAtrasados(contexto!),
    enabled: Boolean(contexto),
  });

  const previewMutation = useMutation({
    mutationFn: async () => {
      const muestra = atrasados.data?.items[0];
      if (!muestra) {
        throw new Error("Sin destinatarios");
      }
      return previewComunicacion(asunto, cuerpo, muestra);
    },
    onSuccess: (data) => setPreviewHtml(`${data.asunto}\n\n${data.cuerpo}`),
  });

  const enviarMutation = useMutation({
    mutationFn: async () => {
      const dest = atrasados.data?.items ?? [];
      if (dest.length === 0) {
        throw new Error("Sin destinatarios");
      }
      return enviarComunicacion(contexto!, asunto, cuerpo, dest, true);
    },
    onSuccess: (data) => setLoteId(data.lote_id),
  });

  if (!contexto) {
    return null;
  }

  const total = atrasados.data?.items.length ?? 0;

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        Enviar comunicación a {total} alumno(s) atrasado(s).
      </p>
      <div className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="com-asunto">
            Asunto
          </label>
          <input
            id="com-asunto"
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={asunto}
            onChange={(e) => setAsunto(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="com-cuerpo">
            Cuerpo
          </label>
          <textarea
            id="com-cuerpo"
            rows={4}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={cuerpo}
            onChange={(e) => setCuerpo(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={total === 0 || previewMutation.isPending}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50 disabled:opacity-50"
            onClick={() => previewMutation.mutate()}
          >
            Preview
          </button>
          <button
            type="button"
            disabled={total === 0 || enviarMutation.isPending}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50"
            onClick={() => enviarMutation.mutate()}
          >
            {enviarMutation.isPending ? "Enviando…" : "Enviar a atrasados"}
          </button>
        </div>
        {previewHtml && (
          <pre className="whitespace-pre-wrap rounded bg-slate-50 p-3 text-xs text-slate-700">
            {previewHtml}
          </pre>
        )}
      </div>
      {loteId && <ComunicacionTracking loteId={loteId} />}
    </div>
  );
}
