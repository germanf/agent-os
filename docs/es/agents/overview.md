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
├── SecurityCapability — run_static_analysis(), run_dependency_audit(), create_finding_issue()
├── UIUXCapability — review_design(), audit_accessibility(), create_design_issue()
└── OrchestratorCapability — decompose(), delegate(), status()
```

### Jerarquía de Agentes

```
CTO ── lanza agentes, verifica workflows, aprueba PRs, único que hace PR a main
 ├── Tech Lead ── Code Review (gate obligatorio), triage Security/UI-UX, delega a Dev
 ├── Full Stack Developer ── implementación
 ├── QA/Tester ── validación, QA loop
 ├── Security Specialist ── pentesting, SAST/DAST → crea Issue
 └── UI/UX Specialist ── review de diseño/UX, accesibilidad → crea Issue
      ↑
 Advisory ── revisión profunda de arquitectura a pedido del CTO (loop exhausto, diseño complejo)
```

### Agentes Implementados

| Agente | Capacidad | Archivo | Descripción |
|--------|-----------|---------|-------------|
| `OpencodeAgent` | DeveloperCapability | `agents/opencode_agent.py` | Se conecta al servidor OpenCode, implementa features, corrige bugs, refactoriza código |
| `HermesAgent` | OrchestratorCapability | `agents/hermes_agent.py` | Descompone objetivos en tareas kanban, delega en agentes disponibles, rastrea progreso |
| `TechLeadAgent` | ReviewerCapability | `agents/reviewer.py` | Code review automatizado, validación de PR, verificación de estándares |
| `SecuritySpecialistAgent` | SecurityCapability | `agents/security_agent.py` | Análisis estático, auditoría de dependencias, creación de issues de vulnerabilidad |
| `UIUXSpecialistAgent` | UIUXCapability | `agents/uiux_agent.py` | Review de diseño, auditoría de accesibilidad, verificación de consistencia UI |

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

## Protocolo de Handoff

Los agentes se comunican mediante mensajes de handoff estructurados definidos en `specs/protocol.md`:

- `HandoffRequest`: desde → hacia, razón, severidad, context_snapshot, attempt_count
- `HandoffResponse`: accepted, rejected, redirected
- Niveles de escalación: info → warning → blocker → critical

Secuencias de handoff estándar:
- **Loop QA exhausto**: QA → Tech Lead → CTO + Advisory → plan → Tech Lead → Dev → re-QA
- **Hallazgo de seguridad**: Security Specialist → Issue → Tech Lead → Dev → Review → Merge → Verificar
- **Hallazgo de UI/UX**: UI/UX Specialist → Issue → Tech Lead → Dev → Review → Merge → Verificar

## Orquestación

El orquestador (`dashboard/orchestrator/`) gestiona la ejecución multi-agente:

1. **Task Graph**: Un DAG de subtareas con dependencias
2. **Agent Pool**: Agentes registrados con estado de salud
3. **Executor**: Orden topológico → ejecución paralela/secuencial → reintento en fallo → propagación de contexto
4. **Aggregator**: Compila resultados con atribución de agente

### Flujo

```
Objetivo → TaskGraph (DAG) → Orden Topológico → Asignación de Agentes →
Ejecución Paralela → SSE Streaming → Agregación de Resultados → Reporte
```

### Propagación de Contexto

Cuando una subtarea se completa, su resultado está automáticamente disponible para las subtareas dependientes mediante variables de entorno (`SUBTASK_{id}_RESULT`). Esto permite pipelines donde la salida de un agente alimenta al siguiente.

## Acceso a Herramientas MCP

Los agentes pueden descubrir y llamar herramientas via el sistema MCP:

- **4 servidores MCP** registrados al inicio
- Herramientas para memoria, notas, kanban y operaciones de workflow
- Las herramientas MCP están expuestas a los agentes para capacidades de autoservicio
