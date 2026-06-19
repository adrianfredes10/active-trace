import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ConfirmDialog } from "@/features/admin/components/shared/ConfirmDialog";
import { DataTable } from "@/features/admin/components/shared/DataTable";
import { PageHeader } from "@/features/admin/components/shared/PageHeader";
import { ProfesorFormModal } from "@/features/admin/components/ProfesorFormModal";
import { UsuarioFormModal } from "@/features/admin/components/UsuarioFormModal";
import {
  actualizarUsuarioAdmin,
  desactivarUsuarioAdmin,
  fetchUsuariosAdmin,
} from "@/features/admin/services/usuarioAdminService";
import type { UsuarioAdminItem } from "@/features/admin/types/admin";
import { StatusBadge } from "@/shared/components/StatusBadge";
import { Button } from "@/shared/components/ui/Button";
import { showToast } from "@/shared/components/ui/Toast";

export function UsuariosPanel() {
  const queryClient = useQueryClient();
  const [profesorModalOpen, setProfesorModalOpen] = useState(false);
  const [selectedUsuario, setSelectedUsuario] = useState<UsuarioAdminItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<UsuarioAdminItem | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-usuarios"],
    queryFn: fetchUsuariosAdmin,
    retry: 1,
  });

  const actualizarMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { nombre: string; apellidos: string } }) =>
      actualizarUsuarioAdmin(id, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["admin-usuarios"] }),
  });

  const eliminarMutation = useMutation({
    mutationFn: desactivarUsuarioAdmin,
    onSuccess: () => {
      showToast("Usuario desactivado", "success");
      void queryClient.invalidateQueries({ queryKey: ["admin-usuarios"] });
      setDeleteTarget(null);
    },
    onError: () => showToast("No se pudo desactivar el usuario", "error"),
  });

  const columns = [
    {
      key: "nombre",
      header: "Nombre",
      render: (u: UsuarioAdminItem) =>
        `${u.apellidos ?? "—"}, ${u.nombre ?? "—"}${u.legajo ? ` (${u.legajo})` : ""}`,
    },
    {
      key: "estado",
      header: "Estado",
      render: (u: UsuarioAdminItem) => (
        <StatusBadge variant={u.estado === "activo" ? "success" : "neutral"}>
          {u.estado}
        </StatusBadge>
      ),
    },
    {
      key: "acciones",
      header: "Acciones",
      render: (u: UsuarioAdminItem) => (
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setSelectedUsuario(u)}
          >
            Editar
          </Button>
          <Button variant="danger" size="sm" onClick={() => setDeleteTarget(u)}>
            Desactivar
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Usuarios"
        subtitle="Creá docentes con rol PROFESOR y asignación a materia y comisión."
        actions={[
          {
            label: "Nuevo profesor",
            onClick: () => setProfesorModalOpen(true),
          },
        ]}
      />

      {isError && (
        <p className="text-sm text-status-danger" role="alert">
          No se pudo cargar usuarios.
        </p>
      )}

      <DataTable
        columns={columns}
        data={data ?? []}
        isLoading={isLoading}
        keyExtractor={(u) => u.id}
        emptyMessage="Sin usuarios activos."
      />

      {selectedUsuario && (
        <UsuarioFormModal
          open
          usuario={selectedUsuario}
          onClose={() => setSelectedUsuario(null)}
          onUpdate={async (id, payload) => {
            await actualizarMutation.mutateAsync({ id, payload });
          }}
        />
      )}

      <ProfesorFormModal open={profesorModalOpen} onClose={() => setProfesorModalOpen(false)} />

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Desactivar usuario"
        message={`¿Desactivar a ${deleteTarget?.nombre} ${deleteTarget?.apellidos}?`}
        confirmLabel="Desactivar"
        isPending={eliminarMutation.isPending}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={() => {
          if (deleteTarget) eliminarMutation.mutate(deleteTarget.id);
        }}
      />
    </div>
  );
}
