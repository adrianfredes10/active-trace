# Proposal — C-20 `perfil-y-mensajeria-interna`

Perfil propio (F11.1) y bandeja de mensajes internos (F3.4, F11.2, FL-10).

## Entregables

- `GET/PATCH /api/perfil` — edición de campos propios; CUIL solo lectura
- `GET /api/inbox/hilos`, `GET /api/inbox/hilos/{id}`, `POST /api/inbox/mensajes`, `POST /api/inbox/hilos/{id}/responder`
- Migración 016: `hilos_mensaje`, `mensajes_internos`
- Logout reutiliza C-03 (`POST /api/auth/logout`)
