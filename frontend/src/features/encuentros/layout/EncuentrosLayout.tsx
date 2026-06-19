import { SubNavLayout, type SubNavTab } from "@/shared/components/SubNavLayout";

const TABS: SubNavTab[] = [
  { to: "/encuentros", label: "Instancias", end: true, permission: "encuentros:gestionar" },
  { to: "/encuentros/crear", label: "Crear", permission: "encuentros:gestionar" },
  { to: "/encuentros/guardias", label: "Guardias", permission: "guardias:registrar" },
];

export function EncuentrosLayout() {
  return (
    <SubNavLayout
      tabs={TABS}
      ariaLabel="Secciones de encuentros"
      deniedMessage="No tenés permisos para gestionar encuentros o guardias."
    />
  );
}
