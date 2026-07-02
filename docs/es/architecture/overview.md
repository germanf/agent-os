# Visión General de Arquitectura

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│  nginx (puerto 80 → 443 redirect, 443 → proxy_pass :8765)│
│  VPN-only (allow 10.0.0.0/24), client_max_body_size 55M  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  uvicorn (puerto 8765) — FastAPI app                    │
│  dashboard/main.py                                      │
│                                                         │
│  Middleware stack:                                       │
│    AuthMiddleware (HTTP Basic Auth)                      │
│    HSTSHeaderMiddleware                                  │
│    TracingMiddleware (OpenTelemetry)                     │
│    RateLimiting (slowapi, por endpoint)                  │
│                                                         │
│  Módulos de ruta:                                        │
│    agents, jobs, kanban, backends, notes,                │
│    projects, chats, diagnostics, alerts,                 │
│    orchestration, mcp, approvals, hermes_webhook,        │
│    cron, workflows, token_accounting                     │
│                                                         │
│  SPA catch-all: @app.get("/{full_path:path}")            │
└──┬───────────────┬──────────────┬───────────────────────┘
   │               │              │
   ▼               ▼              ▼
runner.py     chat_store.py   static files
(SSE jobs)    (SQLite DB)     (frontend/dist/)
```

## Responsabilidades de Módulos

### Backend del Dashboard (`dashboard/`)

| Módulo | Responsabilidad |
|--------|----------------|
| `main.py` | Punto de entrada FastAPI, middleware, rutas, hooks de inicio, fallback SPA |
| `runner.py` | Ejecutor de subprocesos asíncrono genérico con streaming SSE de logs |
| `chat_store.py` | Persistencia SQLite para proyectos, chats, mensajes |
| `health.py` | Registro de health checks basado en componentes |
| `alerts.py` | Sistema de gestión de alertas en memoria |
| `rate_limit.py` | Singleton de rate limiter slowapi |
| `tracing.py` | Middleware de trazado OpenTelemetry |
| `log.py` | Configuración de logging con Loguru y serialización JSON opcional |
| `memory.py` | Almacenes de memoria clave-valor para proyectos y organización (SQLite) |
| `token_accounting.py` | Seguimiento de uso de tokens |
| `backup.py` | Backup automático de SQLite con rotación |
| `workflow.py` | Motor de ejecución de flujos de trabajo multi-paso |

### Backends de Chat (`dashboard/backends/`)

| Backend | Estado | Descripción |
|---------|--------|-------------|
| `ClaudeBackend` | ✅ Completo | Claude Code (subproceso `claude -p`) |
| `OpencodeBackend` | ✅ Completo | API HTTP OpenCode + fallback a subproceso |
| `CodexBackend` | ⚠️ Stub | Backend GPT Codex (no implementado) |
| `KimiBackend` | ⚠️ Stub | Backend Kimi Code (no implementado) |

### Orquestación (`dashboard/orchestrator/`)

| Módulo | Responsabilidad |
|--------|----------------|
| `task_graph.py` | Modelo de datos DAG TaskGraph |
| `agent_pool.py` | Registro de agentes con health checks |
| `executor.py` | Ejecutor DAG asíncrono con streaming SSE, reintentos, timeout |
| `aggregator.py` | Compilación de resultados de múltiples subtareas |

### Sistema MCP (`dashboard/mcp/`)

| Servidor | Herramientas | Recursos |
|----------|-------------|----------|
| **memory** | `store/get/list/search` memorias de proyecto/org | `memory://org/summary` |
| **notes** | `search_notes`, `read_note` | `notes://tree`, `notes://content/{path}` |
| **kanban** | `list/create/complete/show` tareas | — |
| **workflows** | `list/get/status` flujos de trabajo | — |

### Sistema de Agentes (`dashboard/agents/`)

| Agente | Capacidad | Descripción |
|--------|-----------|-------------|
| `HermesAgent` | OrchestratorCapability | Descompone objetivos en tareas kanban, delega |
| `OpencodeAgent` | DeveloperCapability | Correcciones de bugs, features, refactoring via OpenCode |

## Diagrama de Capas

```
┌──────────────────────────────┐
│         Presentación         │
│   React SPA (Tailwind v4)    │
├──────────────────────────────┤
│        Capa de API           │
│   FastAPI + uvicorn + SSE    │
├──────────────────────────────┤
│     Capa de Orquestación     │
│   Task Graph → Agent Pool    │
├──────────────────────────────┤
│   Capa de Backends de Chat   │
│   Claude / OpenCode / etc.   │
├──────────────────────────────┤
│      Capa de Persistencia    │
│   SQLite (WAL mode)          │
└──────────────────────────────┘
```

## Flujo de Ejecución

1. El usuario envía un mensaje de chat desde la UI React
2. FastAPI enruta la solicitud al backend de chat correspondiente
3. El backend ejecuta un subproceso (ej. `claude -p`) o llama a una API HTTP
4. La salida se transmite de vuelta via SSE (Server-Sent Events)
5. Los mensajes se persisten en SQLite mediante `chat_store.py`
6. Para orquestación: las tareas se descomponen en un DAG y se ejecutan via `executor.py`

## Decisiones Arquitectónicas

Ver [Architecture Decision Records (ADRs)](../../adr/) para el detalle de decisiones específicas.

- **ADR-001**: Servidores MCP en-proceso (sin protocolo wire)
- **ADR-002**: SQLite sobre PostgreSQL (usuario único, simplicidad de despliegue)
- **ADR-003**: SSE sobre WebSocket (simplicidad, compatibilidad HTTP)
- **ADR-004**: Protocolo agnóstico de agente (backends conectables)
