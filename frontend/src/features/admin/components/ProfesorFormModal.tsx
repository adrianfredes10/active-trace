import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { useState } from "react";

import {
  crearProfesorCompleto,
  fetchCohortes,
} from "@/features/admin/services/profesorAdminService";
import {
  fetchCarreras,
  fetchMaterias,
} from "@/features/admin/services/estructuraAdminService";
import { Button } from "@/shared/components/ui/Button";
import { Dialog } from "@/shared/components/ui/Dialog";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

type ProfesorFormModalProps = {
  open: boolean;
  onClose: () => void;
};

function formatApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg ?? String(d)).join(", ");
  }
  return "No se pudo completar la operación.";
}

export function ProfesorFormModal({ open, onClose }: ProfesorFormModalProps) {
  const queryClient = useQueryClient();
  const [carreraId, setCarreraId] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const carreras = useQuery({ queryKey: ["admin-carreras"], queryFn: fetchCarreras, enabled: open });
  const materias = useQuery({ queryKey: ["admin-materias"], queryFn: fetchMaterias, enabled: open });
  const cohortes = useQuery({
    queryKey: ["admin-cohortes", carreraId],
    queryFn: () => fetchCohortes(carreraId || undefined),
    enabled: open && Boolean(carreraId),
  });

  const crearMutation = useMutation({
    mutationFn: crearProfesorCompleto,
    onSuccess: (result) => {
      showToast(
        `Profesor creado — comisión ${result.comision}`,
        "success",
      );
      void queryClient.invalidateQueries({ queryKey: ["admin-usuarios"] });
      onClose();
    },
    onError: (error) => {
      setSubmitError(formatApiError(error));
    },
  });

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Nuevo profesor"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            disabled={crearMutation.isPending}
            onClick={() => {
              const form = document.getElementById("profesor-form") as HTMLFormElement | null;
              form?.requestSubmit();
            }}
          >
            {crearMutation.isPending ? "Creando…" : "Crear profesor"}
          </Button>
        </>
      }
    >
      <p className="mb-4 text-xs text-text-secondary">
        Crea la cuenta, asigna rol PROFESOR y vincula materia + cohorte + comisión en un solo paso.
      </p>
      <form
        id="profesor-form"
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const email = (form.elements.namedItem("prof-email") as HTMLInputElement).value.trim();
          const password = (form.elements.namedItem("prof-password") as HTMLInputElement).value;
          const nombre = (form.elements.namedItem("prof-nombre") as HTMLInputElement).value.trim();
          const apellidos = (form.elements.namedItem("prof-apellidos") as HTMLInputElement).value.trim();
          const materiaId = (form.elements.namedItem("prof-materia") as HTMLSelectElement).value;
          const cohorteId = (form.elements.namedItem("prof-cohorte") as HTMLSelectElement).value;
          const comision = (form.elements.namedItem("prof-comision") as HTMLInputElement).value.trim();

          if (!email || password.length < 8 || !materiaId || !carreraId || !cohorteId || !comision) {
            setSubmitError("Completá email, contraseña (8+), carrera, cohorte, materia y comisión.");
            return;
          }

          setSubmitError(null);
          crearMutation.mutate({
            email,
            password,
            nombre: nombre || undefined,
            apellidos: apellidos || undefined,
            materia_id: materiaId,
            carrera_id: carreraId,
            cohorte_id: cohorteId,
            comision,
          });
        }}
      >
        <Input label="Email institucional" id="prof-email" name="prof-email" type="email" placeholder="profesor@instituto.edu" />
        <Input label="Contraseña inicial" id="prof-password" name="prof-password" type="password" placeholder="Mínimo 8 caracteres" />
        <div className="grid grid-cols-2 gap-3">
          <Input label="Nombre" id="prof-nombre" name="prof-nombre" placeholder="María" />
          <Input label="Apellidos" id="prof-apellidos" name="prof-apellidos" placeholder="García" />
        </div>

        <label className="block text-xs font-medium text-text-secondary" htmlFor="prof-carrera">
          Carrera
        </label>
        <select
          id="prof-carrera"
          className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
          value={carreraId}
          onChange={(e) => setCarreraId(e.target.value)}
        >
          <option value="">Seleccionar…</option>
          {(carreras.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.codigo} — {c.nombre}
            </option>
          ))}
        </select>

        <label className="block text-xs font-medium text-text-secondary" htmlFor="prof-cohorte">
          Cohorte
        </label>
        <select
          id="prof-cohorte"
          name="prof-cohorte"
          className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
          disabled={!carreraId}
        >
          <option value="">Seleccionar…</option>
          {(cohortes.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>

        <label className="block text-xs font-medium text-text-secondary" htmlFor="prof-materia">
          Materia
        </label>
        <select
          id="prof-materia"
          name="prof-materia"
          className="w-full rounded-md border border-border bg-surface-card px-3 py-2 text-sm"
        >
          <option value="">Seleccionar…</option>
          {(materias.data ?? []).map((m) => (
            <option key={m.id} value={m.id}>
              {m.codigo} — {m.nombre}
            </option>
          ))}
        </select>

        <Input
          label="Comisión"
          id="prof-comision"
          name="prof-comision"
          placeholder="A"
        />
        <p className="text-[11px] text-text-secondary">Debe coincidir con el padrón importado.</p>

        {submitError && <p className="text-xs text-status-danger">{submitError}</p>}
      </form>
    </Dialog>
  );
}
