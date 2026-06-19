import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { UsuarioAdminItem } from "@/features/admin/types/admin";
import { Button } from "@/shared/components/ui/Button";
import { Dialog } from "@/shared/components/ui/Dialog";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

const editSchema = z.object({
  nombre: z.string().min(1, "El nombre es requerido"),
  apellidos: z.string().min(1, "Los apellidos son requeridos"),
});

type EditForm = z.infer<typeof editSchema>;

type UsuarioFormModalProps = {
  open: boolean;
  onClose: () => void;
  usuario: UsuarioAdminItem;
  onUpdate: (id: string, payload: EditForm) => Promise<void>;
};

export function UsuarioFormModal({ open, onClose, usuario, onUpdate }: UsuarioFormModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EditForm>({
    resolver: zodResolver(editSchema),
    defaultValues: { nombre: "", apellidos: "" },
  });

  useEffect(() => {
    if (!open) return;
    reset({
      nombre: usuario.nombre ?? "",
      apellidos: usuario.apellidos ?? "",
    });
  }, [open, usuario, reset]);

  const onSubmit = handleSubmit(async (data) => {
    try {
      await onUpdate(usuario.id, data);
      showToast("Usuario actualizado", "success");
      onClose();
    } catch {
      showToast("No se pudo guardar el usuario", "error");
    }
  });

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="Editar usuario"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Guardando…" : "Actualizar"}
          </Button>
        </>
      }
    >
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Nombre" {...register("nombre")} error={errors.nombre?.message} />
          <Input label="Apellidos" {...register("apellidos")} error={errors.apellidos?.message} />
        </div>
      </form>
    </Dialog>
  );
}
