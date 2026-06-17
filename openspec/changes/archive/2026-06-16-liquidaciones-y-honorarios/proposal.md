# Proposal — C-18 `liquidaciones-y-honorarios`

Backend de honorarios docentes: grilla salarial (base + plus), cálculo mensual, cierre inmutable, facturas.

## Decisiones de dominio

- **PA-23 cerrado** vía RN-33/34: Plus se acumula N× por comisión en la misma clave.
- **PA-22 operativo**: `materias.plus_grupo` configurable por tenant (mapeo materia → clave Plus).

## Entregables

- Migración 017: `salarios_base`, `salarios_plus`, `liquidaciones`, `facturas`, `plus_grupo` en materias
- `/api/liquidaciones/*`, `/api/facturas/*` con RBAC FINANZAS
- Audit `LIQUIDACION_CERRAR`
- Tests: base vigente, plus acumulado, cierre, facturador excluido, segmentación, facturas
