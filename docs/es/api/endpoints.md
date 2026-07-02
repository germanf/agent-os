# Referencia de API

**URL Base:** `http://127.0.0.1:8765` (desarrollo) / `https://tu-dominio` (producción)

**Autenticación:** HTTP Basic Auth via `DASH_USER`/`DASH_PASS`.
**Excepción:** `/api/health` es público.

**Rate Limiting:** Cada endpoint tiene un límite slowapi (típicamente 30/min).
**Formato de Respuesta:** JSON salvo que se indique lo contrario. Los endpoints SSE retornan `text/event-stream`.

## Endpoints Públicos

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/health` | 60/min | Health check |

## Jobs

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/jobs` | 30/min | Listar todos los jobs |
| GET | `/api/jobs/{id}` | 30/min | Obtener detalle de job |
| GET | `/api/jobs/{id}/stream` | 30/min | Stream SSE de logs |
| GET | `/api/jobs/{id}/events` | 30/min | Stream SSE de eventos parseados |
| GET | `/api/jobs/{id}/logs` | 30/min | Logs pasados del job |
| POST | `/api/jobs/{id}/cancel` | 30/min | Cancelar job en ejecución |
| POST | `/api/jobs/{id}/checkpoint` | 30/min | Guardar checkpoint |
| GET | `/api/jobs/checkpoints` | 30/min | Listar checkpoints |
| GET | `/api/jobs/orphans` | 30/min | Checkpoints huérfanos |
| POST | `/api/jobs/checkpoints/{id}/resume` | 30/min | Reanudar desde checkpoint |

## Sistema de Chat

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/projects` | 30/min | Listar proyectos |
| POST | `/api/projects` | 10/min | Crear proyecto |
| PATCH | `/api/projects/{id}` | 10/min | Actualizar proyecto |
| DELETE | `/api/projects/{id}` | 10/min | Eliminar proyecto |
| POST | `/api/projects/{id}/folders` | 10/min | Agregar carpeta a proyecto |
| DELETE | `/api/projects/folders/{id}` | 10/min | Eliminar carpeta |
| GET | `/api/chats` | 30/min | Listar chats |
| POST | `/api/chats` | 10/min | Crear chat |
| GET | `/api/chats/{id}` | 30/min | Obtener chat |
| PATCH | `/api/chats/{id}` | 10/min | Actualizar chat |
| DELETE | `/api/chats/{id}` | 10/min | Eliminar chat |
| GET | `/api/chats/{id}/messages` | 30/min | Obtener mensajes |
| POST | `/api/chat/send` | 10/min | Enviar mensaje (retorna SSE) |
| POST | `/api/files/upload` | 10/min | Subir archivo para chat |

## Notas (Vault Obsidian)

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/notes/tree` | 30/min | Árbol de archivos del vault |
| GET | `/api/notes/content?path=` | 30/min | Leer contenido de nota |

## Orquestador

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| POST | `/api/orchestrator/tasks` | 10/min | Crear task graph |
| GET | `/api/orchestrator/tasks` | 30/min | Listar graphs |
| GET | `/api/orchestrator/tasks/{id}` | 30/min | Obtener detalle del graph |
| DELETE | `/api/orchestrator/tasks/{id}` | 10/min | Cancelar graph |
| GET | `/api/orchestrator/tasks/{id}/stream` | 30/min | SSE eventos de tareas |
| GET | `/api/orchestrator/agents` | 30/min | Listar agentes disponibles |

## MCP

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/mcp/servers` | 30/min | Listar servidores MCP |
| GET | `/api/mcp/tools` | 30/min | Todas las herramientas |
| GET | `/api/mcp/servers/{name}/tools` | 30/min | Herramientas de un servidor |
| GET | `/api/mcp/servers/{name}/resources` | 30/min | Recursos de un servidor |
| POST | `/api/mcp/servers/{name}/call` | 10/min | Invocar una herramienta |

## Kanban

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/kanban/tasks` | 30/min | Listar tareas kanban |
| POST | `/api/kanban/tasks` | 10/min | Crear tarea |
| GET | `/api/kanban/tasks/{id}` | 30/min | Obtener detalle de tarea |
| POST | `/api/kanban/tasks/{id}/complete` | 10/min | Completar tarea |
| POST | `/api/kanban/tasks/{id}/block` | 10/min | Bloquear tarea |
| POST | `/api/kanban/tasks/{id}/unblock` | 10/min | Desbloquear tarea |
| POST | `/api/kanban/feedback/poll` | 30/min | Poll de feedback |

## Aprobaciones

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/approvals/pending` | 30/min | Aprobaciones pendientes |
| POST | `/api/approvals/{id}/approve` | 10/min | Aprobar |
| POST | `/api/approvals/{id}/deny` | 10/min | Rechazar |
| POST | `/api/approvals/{id}/complete-task` | 10/min | Completar post-aprobación |

## Diagnósticos

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/diagnostics` | 10/min | Diagnóstico completo de despliegue |
| GET | `/api/ponytail/metrics` | 30/min | Métricas Ponytail |

## Alertas

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/alerts` | 30/min | Listar alertas |
| POST | `/api/alerts/{id}/acknowledge` | 10/min | Reconocer alerta |
| POST | `/api/alerts/acknowledge-all` | 10/min | Reconocer todas |

## Token Accounting

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/tokens` | 30/min | Entradas de log de tokens |
| POST | `/api/tokens` | 10/min | Registrar uso de tokens |
| GET | `/api/tokens/summary` | 30/min | Resumen de uso de tokens |

## Workflows

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/workflows` | 30/min | Listar definiciones |
| POST | `/api/workflows/load` | 10/min | Cargar workflow desde archivo |
| GET | `/api/workflows/{name}` | 30/min | Obtener detalle |
| POST | `/api/workflows/{name}/execute` | 10/min | Ejecutar workflow |
| GET | `/api/workflows/{name}/status` | 30/min | Estado del workflow |

## Cron

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/cron/jobs` | 30/min | Listar jobs cron |
| POST | `/api/cron/jobs` | 10/min | Crear job cron |
| POST | `/api/cron/jobs/{name}/pause` | 10/min | Pausar job |
| POST | `/api/cron/jobs/{name}/resume` | 10/min | Reanudar job |
| POST | `/api/cron/jobs/{name}/run-now` | 10/min | Ejecutar ahora |
| DELETE | `/api/cron/jobs/{name}` | 10/min | Eliminar job |
| POST | `/api/cron/tick` | 30/min | Trigger tick de cron |
| GET | `/api/cron/status` | 30/min | Estado del sistema cron |

## Otros

| Método | Ruta | Límite | Descripción |
|--------|------|--------|-------------|
| GET | `/api/backends` | 30/min | Listar backends de chat disponibles |
| GET | `/api/agents` | 30/min | Listar agentes registrados |
| POST | `/api/hermes/webhook` | 30/min | Webhook de kanban Hermes |

## Manejo de Errores

Todos los endpoints retornan errores en el formato:

```json
{
  "detail": "Descripción del error"
}
```

Códigos de estado HTTP comunes:
- `200` — Éxito
- `401` — No autorizado (auth faltante/inválida)
- `404` — No encontrado
- `429` — Rate limit excedido
- `500` — Error interno del servidor
