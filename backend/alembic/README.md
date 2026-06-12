# Migraciones Alembic

Convención del proyecto: **una migración por cambio de schema**.

- Cada change que altere la estructura de la base aporta su propia migración,
  encadenada sobre la anterior (`down_revision` apunta a la previa).
- Las migraciones son reversibles: `downgrade` deshace exactamente lo que hizo
  `upgrade` (incluye drop de tipos enum creados).
- El historial forma una cadena lineal sin huérfanas.

## Comandos

```bash
alembic upgrade head      # aplica todas las migraciones pendientes
alembic downgrade -1      # revierte la última
alembic current           # revisión aplicada actualmente
alembic revision -m "..." # nueva migración (autogenerate: --autogenerate)
```

`env.py` resuelve la URL desde `Settings` (`DATABASE_URL`) e importa
`app.models` para que el autogenerate detecte el metadata completo.

## Historial

| Revisión | Descripción |
|----------|-------------|
| `001`    | Crea la tabla raíz `tenants` (C-02). |
