# Configuración de Desarrollo

## Estructura del Repositorio

```
agent-os/
├── AGENTS.md                  # Convenciones principales de desarrollo
├── README.md                  # Visión general del proyecto
├── dashboard/                 # Backend FastAPI + React SPA
│   ├── main.py                # Punto de entrada de la app
│   ├── chat_store.py          # Persistencia SQLite
│   ├── runner.py              # Ejecutor de subprocesos asíncrono
│   ├── config.py              # Constantes de rutas
│   ├── health.py              # Registro de health checks
│   ├── alerts.py              # Sistema de alertas
│   ├── rate_limit.py          # Rate limiter
│   ├── tracing.py             # OpenTelemetry
│   ├── log.py                 # Configuración de logging
│   ├── memory.py              # Almacenes de memoria clave-valor
│   ├── token_accounting.py    # Seguimiento de tokens
│   ├── backup.py              # Backup de BD
│   ├── approvals.py           # Flujo de aprobaciones
│   ├── checkpoints.py         # Checkpoints de jobs
│   ├── kanban.py              # Adaptador Kanban
│   ├── kanban_feedback.py     # Poller de feedback Kanban
│   ├── workflow.py            # Motor de flujos de trabajo
│   ├── hermes_adapter.py      # Adaptador CLI de Hermes
│   ├── headroom_sidecar.py    # Proxy Headroom
│   ├── headroom_learn.py      # Aprendizaje Headroom
│   ├── headroom_memory.py     # Memoria de sesión Headroom
│   ├── cron_loop.py           # Ticker de cron
│   ├── cron_adapter.py        # Adaptador cron de Hermes
│   ├── curator_loop.py        # Bucle de revisión del curator
│   ├── ponytail.py            # Estado del plugin Ponytail
│   ├── start.sh               # Despliegue en producción
│   ├── restore.sh             # Restauración de BD
│   ├── diagnose.sh            # Diagnósticos de VM
│   ├── nginx.conf             # Configuración de nginx para producción
│   ├── .env.example           # Plantilla de variables de entorno
│   ├── requirements.txt       # Dependencias Python
│   ├── backends/              # Implementaciones de backends de chat
│   │   ├── protocol.py        # ABC + eventos normalizados
│   │   ├── claude.py          # Backend Claude Code
│   │   ├── opencode.py        # Backend OpenCode
│   │   ├── codex.py           # Backend Codex (stub)
│   │   └── kimi.py            # Backend Kimi (stub)
│   ├── agents/                # Implementaciones de capacidades de agente
│   │   ├── protocol.py        # ABCs: Developer, Reviewer, QA, Orchestrator
│   │   ├── hermes_agent.py    # Orquestador Hermes
│   │   └── opencode_agent.py  # Desarrollador OpenCode
│   ├── orchestrator/          # Orquestación multi-agente
│   │   ├── task_graph.py      # Modelo de datos DAG
│   │   ├── agent_pool.py      # Registro de agentes
│   │   ├── executor.py        # Ejecutor DAG asíncrono
│   │   └── aggregator.py      # Compilación de resultados
│   ├── mcp/                   # Sistema de servidores MCP
│   │   ├── server.py          # ABC + registro
│   │   ├── client.py          # Helpers de descubrimiento
│   │   └── servers/           # Implementaciones de servidores MCP
│   ├── middleware/             # Middleware ASGI
│   │   ├── auth.py            # HTTP Basic Auth
│   │   └── hsts.py            # Headers HSTS
│   ├── routes/                # Manejadores de rutas API
│   ├── models/                # Schemas Pydantic
│   ├── skills/                # Definiciones de skills Hermes
│   └── data/                  # Bases de datos SQLite + uploads (gitignored)
├── frontend/                  # (en realidad dashboard/frontend/)
│   └── src/
│       ├── App.tsx            # Rutas
│       ├── main.tsx           # Punto de entrada
│       ├── index.css          # Configuración Tailwind v4
│       ├── pages/             # Componentes de página
│       ├── components/        # Componentes UI compartidos
│       └── lib/               # Utilidades, hooks, tests
├── sandbox/                   # Sandbox Docker para agentes
├── specs/                     # Definiciones de roles + flujo de trabajo
├── tests/                     # Scripts de test Python
├── docs/                      # Documentación
│   ├── en/                    # Documentación en inglés
│   ├── es/                    # Documentación en español
│   ├── adr/                   # Architecture Decision Records
│   └── assets/                # Imágenes y diagramas
├── scripts/                   # Scripts de utilidad
└── tmp/                       # Archivos temporales (gitignored)
```

## Estándares de Código

### Python
- **Estilo**: ruff (configurado en `pyproject.toml`)
- **Type hints**: requeridos en todas las firmas de funciones
- **Verificación sintáctica**: `python3 -m py_compile dashboard/main.py`
- **Lint**: `ruff check dashboard/`
- **Formato**: ruff formatter

### TypeScript / React
- **TypeScript**: modo estricto, `tsc -b` para type checking
- **Lint**: ESLint (configuración plana en `eslint.config.js`)
- **Build**: `pnpm run build` (ejecuta `tsc -b && vite build`)
- **Framework**: React 19 con componentes funcionales y hooks
- **Estilos**: Tailwind v4 CSS-first via `@theme` en `index.css`

### General
- No hay CI/CD en el repo — el despliegue es manual via `dashboard/start.sh`
- Cada issue recibe exactamente una etiqueta: `bug`, `feature`, `security`, o `documentation`
- Los archivos temporales van en `tmp/` (raíz del proyecto) — nunca en `/tmp/` o temp del sistema

## Flujo de Trabajo de Desarrollo

Ver `specs/workflow.md` para el pipeline completo:
```
Issue → Plan → Dev → CTO Review → Human Approval → CTO Merge → QA → Close
```

### Comandos Rápidos

```bash
# Backend
uvicorn dashboard.main:app --port 8765 --reload
ruff check dashboard/
python3 -m py_compile dashboard/main.py

# Frontend
cd dashboard/frontend
pnpm run dev         # Servidor de desarrollo (proxy a :8765)
pnpm run build       # TypeScript check + build producción
pnpm run test        # Vitest
pnpm run lint        # ESLint
```

## Depuración

- Para problemas de backend: revisá los logs de FastAPI en la terminal de uvicorn
- Para problemas de frontend: DevTools del navegador (pestañas Console, Network)
- Los streams SSE se pueden inspeccionar en `/api/jobs/{id}/stream` o `/api/orchestrator/tasks/{id}/stream`
- Inspección de base de datos: `sqlite3 dashboard/data/chat.db` (modo WAL)
