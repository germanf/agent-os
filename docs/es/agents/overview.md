# Sistema de Agentes

## Visión General

El sistema de agentes proporciona dos capas: **capacidades de agente** (lo que los agentes pueden hacer) y **backends de chat** (cómo se invocan los agentes). Esta separación permite emparejar cualquier capacidad con cualquier backend.

## Capacidades de Agente

Definidas en `dashboard/agents/protocol.py`:

```
AgentCapability (ABC)
├── DeveloperCapability — fix_bug(), implement_feature(), refactor()
├── ReviewerCapability — review_pr(), check_standards()
├── QACapability — write_tests(), run_validation()
└── OrchestratorCapability — decompose(), delegate(), status()
```

### Agentes Implementados

| Agente | Capacidad | Archivo | Descripción |
|--------|-----------|---------|-------------|
| `OpencodeAgent` | DeveloperCapability | `agents/opencode_agent.py` | Se conecta al servidor OpenCode, implementa features, corrige bugs, refactoriza código |
| `HermesAgent` | OrchestratorCapability | `agents/hermes_agent.py` | Descompone objetivos en tareas kanban, delega en agentes disponibles, rastrea progreso |

### Ciclo de Vida

1. **Registro**: Los agentes se registran al inicio via `dashboard/agents/__init__.py`
2. **Descubrimiento**: El agent pool (`dashboard/orchestrator/agent_pool.py`) perfila todos los agentes registrados
3. **Health checks**: El pool verifica disponibilidad cada 60 segundos
4. **Delegación**: El orquestador asigna subtareas a agentes disponibles según capacidad

## Backends de Chat

Definidos en `dashboard/backends/`:

| Backend | Estado | Mecanismo |
|---------|--------|-----------|
| `ClaudeBackend` | ✅ Completo | Subproceso: `claude -p` con `--output-format stream-json` |
| `OpencodeBackend` | ✅ Completo | API HTTP (servidor OpenCode) + fallback a subproceso |
| `CodexBackend` | ⚠️ Stub | No implementado |
| `KimiBackend` | ⚠️ Stub | No implementado |

## Orquestación

El orquestador (`dashboard/orchestrator/`) gestiona la ejecución multi-agente:

1. **Task Graph**: Un DAG de subtareas con dependencias
2. **Agent Pool**: Agentes registrados con estado de salud
3. **Executor**: Orden topológico → ejecución paralela/secuencial → reintento en fallo
4. **Aggregator**: Compila resultados con atribución de agente

### Flujo

```
Objetivo → TaskGraph (DAG) → Orden Topológico → Asignación de Agentes →
Ejecución Paralela → SSE Streaming → Agregación de Resultados → Reporte
```

## Acceso a Herramientas MCP

Los agentes pueden descubrir y llamar herramientas via el sistema MCP:

- **4 servidores MCP** registrados al inicio
- Herramientas para memoria, notas, kanban y operaciones de workflow
- Las herramientas MCP están expuestas a los agentes para capacidades de autoservicio
