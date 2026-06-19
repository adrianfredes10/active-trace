import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { fetchUsuariosAdmin } from "@/features/admin/services/usuarioAdminService";
import {
  abonarFactura,
  crearFactura,
  fetchFacturas,
} from "@/features/finanzas/services/facturaService";
import type { FacturaItem } from "@/features/finanzas/types/finanzas";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

const DEFAULT_PERIODO = "2026-06";

export function FacturasPanel() {
  const queryClient = useQueryClient();
  const [periodo, setPeriodo] = useState(DEFAULT_PERIODO);
  const [modalOpen, setModalOpen] = useState(false);
  const [usuarioId, setUsuarioId] = useState("");
  const [detalle, setDetalle] = useState("");

  const facturas = useQuery({
    queryKey: ["facturas", periodo],
    queryFn: () => fetchFacturas(periodo),
    retry: 1,
  });
  const usuarios = useQuery({
    queryKey: ["admin-usuarios"],
    queryFn: fetchUsuariosAdmin,
  });

  const crear = useMutation({
    mutationFn: () => {
      if (!usuarioId || !detalle.trim()) throw new Error("Completá usuario y detalle.");
      return crearFactura({ usuario_id: usuarioId, periodo, detalle: detalle.trim() });
    },
    onSuccess: () => {
      showToast("Factura registrada.");
      setModalOpen(false);
      setDetalle("");
      void queryClient.invalidateQueries({ queryKey: ["facturas", periodo] });
    },
  });

  const abonar = useMutation({
    mutationFn: (id: string) => abonarFactura(id),
    onSuccess: () => {
      showToast("Factura marcada como abonada.");
      void queryClient.invalidateQueries({ queryKey: ["facturas", periodo] });
    },
  });

  const facturadores = (usuarios.data ?? []).filter((u) => u.facturador);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeader title="Facturas" subtitle="Carga y seguimiento de facturas de honorarios." />
        <div className="flex flex-wrap items-end gap-2">
          <Input
            label="Período"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            placeholder="2026-06"
            className="w-32"
          />
          <Button type="button" onClick={() => setModalOpen(true)}>
            Nueva factura
          </Button>
        </div>
      </div>

      {facturas.isLoading && <p className="text-sm text-text-secondary">Cargando…</p>}
      {facturas.isError && (
        <p className="text-sm text-status-danger">No se pudieron cargar las facturas.</p>
      )}

      {!facturas.isLoading && !facturas.isError && (
        <FacturasTable
          items={facturas.data ?? []}
          onAbonar={(id) => abonar.mutate(id)}
          abonando={abonar.isPending}
        />
      )}

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/50 p-4">
          <form
            className="w-full max-w-md space-y-4 rounded-lg border border-border bg-surface-card p-6 shadow-lg"
            onSubmit={(e) => {
              e.preventDefault();
              crear.mutate();
            }}
          >
            <h3 className="text-lg font-semibold text-text-primary">Nueva factura</h3>
            <div>
              <label className="mb-1 block text-xs font-medium text-text-secondary">Profesor</label>
              <select
                value={usuarioId}
                onChange={(e) => setUsuarioId(e.target.value)}
                className="w-full rounded-md border border-border px-3 py-2 text-sm focus-ring"
              >
                <option value="">Seleccionar…</option>
                {facturadores.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.legajo ?? u.id.slice(0, 8)}
                  </option>
                ))}
              </select>
            </div>
            <Input label="Detalle" value={detalle} onChange={(e) => setDetalle(e.target.value)} />
            <div className="flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={crear.isPending}>
                {crear.isPending ? "Guardando…" : "Registrar"}
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function FacturasTable({
  items,
  onAbonar,
  abonando,
}: {
  items: FacturaItem[];
  onAbonar: (id: string) => void;
  abonando: boolean;
}) {
  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
      <table className="min-w-full text-sm">
        <thead className="border-b border-border bg-surface text-left text-xs uppercase text-text-secondary">
          <tr>
            <th className="px-4 py-2">Usuario</th>
            <th className="px-4 py-2">Detalle</th>
            <th className="px-4 py-2">Estado</th>
            <th className="px-4 py-2">Cargada</th>
            <th className="px-4 py-2" />
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((f) => (
            <tr key={f.id}>
              <td className="px-4 py-2 font-mono text-xs">{f.usuario_id.slice(0, 8)}…</td>
              <td className="px-4 py-2">{f.detalle}</td>
              <td className="px-4 py-2">{f.estado}</td>
              <td className="px-4 py-2 text-text-secondary">
                {new Date(f.cargada_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-2 text-right">
                {f.estado !== "abonada" && (
                  <Button
                    type="button"
                    size="sm"
                    variant="secondary"
                    disabled={abonando}
                    onClick={() => onAbonar(f.id)}
                  >
                    Abonar
                  </Button>
                )}
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-text-secondary">
                Sin facturas en este período.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
