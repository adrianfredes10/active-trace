import { SubNavLayout, type SubNavTab } from "@/shared/components/SubNavLayout";

const TABS: SubNavTab[] = [
  { to: "/coloquios", label: "Panel", end: true, permission: "evaluaciones:gestionar" },
  { to: "/coloquios/crear", label: "Nueva convocatoria", permission: "evaluaciones:gestionar" },
];

export function ColoquiosLayout() {
  return (
    <SubNavLayout
      tabs={TABS}
      ariaLabel="Secciones de coloquios"
      deniedMessage="No tenés permisos para gestionar evaluaciones."
    />
  );
}
