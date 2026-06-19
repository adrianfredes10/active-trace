import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import {
  fetchCarreras,
  fetchCohortes,
  fetchMaterias,
} from "@/features/admin/services/estructuraAdminService";
import { fetchAsignaciones } from "@/features/coordinacion/services/equiposCoordService";
import {
  crearGuardia,
  exportarGuardiasCsv,
  fetchGuardias,
} from "@/features/encuentros/services/guardiaService";
import { DIAS_SEMANA } from "@/features/encuentros/types/encuentros";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

export function GuardiasPage() {
  const queryClient = useQueryClient();
  const [materiaId, setMateriaId] = useState("");
  const [carreraId, setCarreraId] = useState("");
  const [cohorteId, setCohorteId] = useState("");
  const [asignacionId, setAsignacionId] = useState("");
  const [dia, setDia] = useState<string>(DIAS_SEMANA[0]);
  const [horario, setHorario] = useState("18:00 - 20:00");
  const [comentarios, setComentarios] = useState("");
  const [error, setError] = useState<string | null>(null);

  const materias = useQuery({ queryKey: ["admin-materias"], queryFn: fetchMaterias });
  const carreras = useQuery({ queryKey: ["admin-carreras"], queryFn: fetchCarreras });
  const cohortes = useQuery({ queryKey: ["admin-cohortes"], queryFn: fetchCohortes });
  const asignaciones = useQuery({
    queryKey: ["asignaciones", materiaId],
    queryFn: () => fetchAsignaciones(materiaId),
    enabled: Boolean(materiaId),
  });
  const guardias = useQuery({
    queryKey: ["guardias", materiaId, cohorteId],
    queryFn: () => fetchGuardias({ materia_id: materiaId || undefined, cohorte_id: cohorteId || undefined }),
    retry: 1,
  });

  const crear = useMutation({
    mutationFn: () => {
      if (!materiaId || !carreraId || !cohorteId || !asignacionId) {
        throw new Error("Completá materia, carrera, cohorte y asignación.");
      }
      return crearGuardia({
        materia_id: materiaId,
        carrera_id: carreraId,
        cohorte_id: cohorteId,
        asignacion_id: asignacionId,
        dia,
        horario,
        comentarios: comentarios || undefined,
      });
    },
    onSuccess: () => {
      setError(null);
      setComentarios("");
      showToast("Guardia registrada.");
      void queryClient.invalidateQueries({ queryKey: ["guardias"] });
    },
    onError: (err) => setError(formatError(err)),
  });

  const exportar = async () => {
    const blob = await exportarGuardiasCsv({
      materia_id: materiaId || undefined,
      cohorte_id: cohorteId || undefined,
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "guardias.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader title="Guardias" subtitle="Registro de guardias docentes." />
        <Button type="button" variant="secondary" size="sm" onClick={() => void exportar()}>
          Exportar CSV
        </Button>
      </div>

      <form
        className="grid max-w-3xl gap-4 rounded-lg border border-border bg-surface-card p-4 lg:grid-cols-2"
        onSubmit={(e) => {
          e.preventDefault();
          crear.mutate();
        }}
      >
        <SelectField
          label="Materia"
          value={materiaId}
          onChange={(v) => {
            setMateriaId(v);
            setAsignacionId("");
          }}
          options={(materias.data ?? []).map((m) => ({ value: m.id, label: `${m.codigo} — ${m.nombre}` }))}
        />
        <SelectField
          label="Asignación"
          value={asignacionId}
          onChange={setAsignacionId}
          disabled={!materiaId}
          options={(asignaciones.data ?? []).map((a) => ({
            value: a.id,
            label: `${a.rol} · ${a.id.slice(0, 8)}`,
          }))}
        />
        <SelectField
          label="Carrera"
          value={carreraId}
          onChange={setCarreraId}
          options={(carreras.data ?? []).map((c) => ({ value: c.id, label: c.codigo }))}
        />
        <SelectField
          label="Cohorte"
          value={cohorteId}
          onChange={setCohorteId}
          options={(cohortes.data ?? []).map((c) => ({ value: c.id, label: c.nombre }))}
        />
        <div>
          <label className="mb-1 block text-xs font-medium text-text-secondary">Día</label>
          <select
            value={dia}
            onChange={(e) => setDia(e.target.value)}
            className="w-full rounded-md border border-border px-3 py-2 text-sm focus-ring"
          >
            {DIAS_SEMANA.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        <Input label="Horario" value={horario} onChange={(e) => setHorario(e.target.value)} />
        <div className="lg:col-span-2">
          <Input label="Comentarios" value={comentarios} onChange={(e) => setComentarios(e.target.value)} />
        </div>
        {error && (
          <p className="text-sm text-status-danger lg:col-span-2" role="alert">
            {error}
          </p>
        )}
        <div className="lg:col-span-2">
          <Button type="submit" disabled={crear.isPending}>
            {crear.isPending ? "Guardando…" : "Registrar guardia"}
          </Button>
        </div>
      </form>

      <GuardiasTable loading={guardias.isLoading} error={guardias.isError} items={guardias.data ?? []} />
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  disabled?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-text-secondary">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-md border border-border px-3 py-2 text-sm focus-ring disabled:opacity-50"
      >
        <option value="">Seleccionar…</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function GuardiasTable({
  loading,
  error,
  items,
}: {
  loading: boolean;
  error: boolean;
  items: { id: string; dia: string; horario: string; estado: string; comentarios: string | null }[];
}) {
  if (loading) return <p className="text-sm text-text-secondary">Cargando guardias…</p>;
  if (error) return <p className="text-sm text-status-danger">No se pudo cargar el listado.</p>;

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-surface-card">
      <table className="min-w-full text-sm">
        <thead className="border-b border-border bg-surface text-left text-xs uppercase text-text-secondary">
          <tr>
            <th className="px-4 py-2">Día</th>
            <th className="px-4 py-2">Horario</th>
            <th className="px-4 py-2">Estado</th>
            <th className="px-4 py-2">Comentarios</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {items.map((g) => (
            <tr key={g.id}>
              <td className="px-4 py-2">{g.dia}</td>
              <td className="px-4 py-2">{g.horario}</td>
              <td className="px-4 py-2">{g.estado}</td>
              <td className="px-4 py-2 text-text-secondary">{g.comentarios ?? "—"}</td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={4} className="px-4 py-6 text-center text-text-secondary">
                Sin guardias registradas.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function formatError(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "No se pudo registrar la guardia.";
}
