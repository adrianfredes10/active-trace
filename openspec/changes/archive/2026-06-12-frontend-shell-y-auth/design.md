# Design — frontend-shell-y-auth (C-21)

## Contexto

SPA feature-based según `docs/ARQUITECTURA.md`. Consume endpoints de C-03/C-04. El backend expone permisos vía `GET /api/rbac/permisos-efectivos`; el menú NO hardcodea capacidades.

## Decisiones

### D1 — Tokens: access en memoria, refresh en sessionStorage
Access token vive en el AuthContext (memoria). Refresh token en `sessionStorage` para sobrevivir reload sin persistir indefinidamente como localStorage.

### D2 — Refresh transparente en interceptor Axios
Ante 401 en requests autenticados (excepto `/auth/login`, `/auth/refresh`), una cola serializada llama `POST /api/auth/refresh` solo con refresh token, actualiza tokens y reintenta la request original.

### D3 — Permisos desde API, no del JWT
El guard de UI usa el set cacheado de TanStack Query (`permisos-efectivos`), invalidado al login/logout.

### D4 — Rutas públicas vs protegidas
Públicas: `/login`, `/2fa`, `/forgot-password`, `/reset-password`. Protegidas: `/` con `AppLayout`. Redirect a `/login` si no hay sesión.

### D5 — Proxy Vite en dev
`vite.config.ts` proxy `/api` → `http://localhost:8000` para evitar CORS en dev (CORS sigue configurado para otros entornos).

## Estructura

```
frontend/src/
├── features/auth/{components,hooks,services,types,pages}
├── shared/{components,services,pages}
└── App.tsx + router
```

## Riesgos

- Impersonación UI diferida a C-24 (admin).
- Enroll 2FA desde perfil → C-20.
