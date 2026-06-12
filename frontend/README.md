# activia-trace — Frontend

SPA React + TypeScript (Vite). Consume la API en `http://localhost:8000` vía proxy de desarrollo.

## Desarrollo

```bash
npm install
npm run dev
```

En Docker Compose el servicio `frontend` ya expone http://localhost:5173.

## Scripts

| Comando | Descripción |
|---------|-------------|
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | Build de producción |
| `npm run test` | Tests (Vitest) |

## Estructura

```
src/
  features/     # módulos por dominio (auth, auditoria, …)
  shared/         # layout, api client, utilidades
```

Ver [README.md](../README.md) en la raíz del repo para el arranque completo con Docker.
