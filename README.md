# activia-trace

Plataforma multi-tenant de gestión académica y trazabilidad sobre Moodle.

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL |
| Frontend | React 18, TypeScript, Vite, TanStack Query, Tailwind |
| Infra | Docker Compose (API, worker, Postgres, frontend dev) |

## Arranque local

```bash
# 1. Variables de entorno del backend
cp backend/.env.example backend/.env

# 2. Levantar servicios
docker compose up -d --build

# 3. Migraciones y datos demo
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_dev.py
```

| Servicio | URL |
|----------|-----|
| API | http://localhost:8000 |
| Frontend | http://localhost:5173 |
| Health | http://localhost:8000/health |

**Login demo:** tenant `demo` · email `admin@demo.local` · password `Admin1234!`

## Documentación del proyecto

- [CHANGES.md](CHANGES.md) — roadmap de implementación (changes C-01…C-24)
- [knowledge-base/](knowledge-base/) — dominio y reglas de negocio
- [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) — arquitectura técnica
- [AGENTS.md](AGENTS.md) — instrucciones para agentes de desarrollo

## Estado actual (changes completados)

- C-01 foundation-setup
- C-02 core-models-y-tenancy
- C-03 auth-jwt-2fa
- C-04 rbac-permisos-finos
- C-05 audit-log
- C-06 estructura-academica *(implementado, pendiente archivar)*
- C-21 frontend-shell-y-auth

## Tests

```bash
# Backend (requiere Postgres de test en localhost:5432/activia_test)
cd backend
pip install ".[test]"
pytest
```
