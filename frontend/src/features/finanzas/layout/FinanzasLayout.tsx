import { SubNavLayout, type SubNavTab } from "@/shared/components/SubNavLayout";

const TABS: SubNavTab[] = [
  { to: "/finanzas", label: "Liquidaciones", end: true, permission: "liquidaciones:grilla" },
  { to: "/finanzas/grilla", label: "Grilla salarial", permission: "liquidaciones:grilla" },
  { to: "/finanzas/facturas", label: "Facturas", permission: "facturas:gestionar" },
];

export function FinanzasLayout() {
  return (
    <SubNavLayout
      tabs={TABS}
      ariaLabel="Secciones de finanzas"
      deniedMessage="No tenés permisos de finanzas."
    />
  );
}
