import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { UsuarioAdminItem } from "@/features/admin/types/admin";
import { Button } from "@/shared/components/ui/Button";
import { Dialog } from "@/shared/components/ui/Dialog";
import { Input } from "@/shared/components/ui/Input";
import { showToast } from "@/shared/components/ui/Toast";

const createSchema = z.object({
  nombre: z.string().min(1, "El nombre es requerido"),
  apellidos: z.string().min(1, "Los apellidos son requeridos"),
  email: z.string().email("Email inválido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
  banco: z.string().optional(),
  regional: z.string().optional(),
  legajo: z.string().optional(),
  facturador: z.boolean().optional(),
});

const editSchema = z.object({
  nombre: z.string().min(1, "El nombre es requerido"),
  apellidos: z.string().min(1, "Los apellidos son requeridos"),
  banco: z.string().optional(),
  regional: z.string().optional(),
  legajo: z.string().optional(),
  facturador: z.boolean().optional(),
});

type CreateForm = z.infer<typeof createSchema>;
type EditForm = z.infer<typeof editSchema>;

type UsuarioFormModalProps = {
  open: boolean;
  onClose: () => void;
  usuario?: UsuarioAdminItem | null;
  onCreate: (payload: CreateForm) => Promise<void>;
  onUpdate: (id: string, payload: EditForm) => Promise<void>;
};

export function UsuarioFormModal({
  open,
  onClose,
  usuario,
  onCreate,
  onUpdate,
}: UsuarioFormModalProps) {
  const isEdit = Boolean(usuario);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm | EditForm>({
    resolver: zodResolver(isEdit ? editSchema : createSchema),
    defaultValues: {
      nombre: "",
      apellidos: "",
      email: "",
      password: "",
      facturador: false,
    },
  });

  useEffect(() => {
    if (!open) return;
    if (usuario) {
      reset({
        nombre: usuario.nombre ?? "",
        apellidos: usuario.apellidos ?? "",
        banco: usuario.banco ?? "",
        regional: usuario.regional ?? "",
        legajo: usuario.legajo ?? "",
        facturador: usuario.facturador,
      });
    } else {
      reset({
        nombre: "",
        apellidos: "",
        email: "",
        password: "",
        banco: "",
        regional: "",
        legajo: "",
        facturador: false,
      });
    }
  }, [open, usuario, reset]);

  const onSubmit = handleSubmit(async (data) => {
    try {
      if (isEdit && usuario) {
        await onUpdate(usuario.id, data as EditForm);
        showToast("Usuario actualizado", "success");
      } else {
        await onCreate(data as CreateForm);
        showToast("Usuario creado", "success");
      }
      onClose();
    } catch {
      showToast("No se pudo guardar el usuario", "error");
    }
  });

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={isEdit ? "Editar usuario" : "Nuevo usuario"}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit(onSubmit)} disabled={isSubmitting}>
            {isSubmitting ? "Guardando…" : isEdit ? "Actualizar" : "Crear"}
          </Button>
        </>
      }
    >
      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <div className="grid grid-cols-2 gap-4">
          <Input label="Nombre" {...register("nombre")} error={errors.nombre?.message} />
          <Input label="Apellidos" {...register("apellidos")} error={errors.apellidos?.message} />
        </div>
        {!isEdit && (
          <>
            <Input
              label="Email"
              type="email"
              {...register("email")}
              error={"email" in errors ? errors.email?.message : undefined}
            />
            <Input
              label="Contraseña"
              type="password"
              autoComplete="new-password"
              {...register("password")}
              error={"password" in errors ? errors.password?.message : undefined}
            />
          </>
        )}
        <div className="grid grid-cols-2 gap-4">
          <Input label="Banco" {...register("banco")} />
          <Input label="Legajo" {...register("legajo")} />
        </div>
        <Input label="Regional" {...register("regional")} />
        <label className="flex items-center gap-2 text-sm text-text-primary">
          <input type="checkbox" className="size-4 rounded border-border" {...register("facturador")} />
          Facturador
        </label>
      </form>
    </Dialog>
  );
}
