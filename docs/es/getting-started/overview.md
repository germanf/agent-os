# Visión General del Proyecto

## ¿Qué es Agentic Software Boutique?

Agentic Software Boutique (agent-os) es una **plataforma genérica y agnóstica para el desarrollo de software asistido por IA**. Proporciona un panel web, orquestación multi-agente, un ecosistema MCP (Model Context Protocol) de herramientas, y un sistema de backends conectables para interactuar con diversos agentes de IA de codificación.

La plataforma está diseñada para conectarse a cualquier proyecto — tú traes tu propio código, credenciales e infraestructura.

## Visión

Permitir que agentes de IA colaboren en tareas de desarrollo de software con supervisión humana, usando una plataforma modular y liviana que no estorba. El mejor código es el código que nunca se escribe.

## Filosofía

- **Agnóstico de agente**: funciona con Claude, Codex, Kimi, OpenCode — cualquier backend que implemente el protocolo `ChatBackend`
- **Protocolo primero**: MCP como interfaz estándar para exponer herramientas
- **Degradación gradual**: cada funcionalidad funciona sin servidores MCP, multi-agente, o cualquier componente opcional
- **Observabilidad por defecto**: logs estructurados, métricas, health checks en todos los componentes
- **Despliegue incremental**: cada sub-fase se despliega independientemente a producción

## Conceptos de Alto Nivel

| Concepto | Descripción |
|----------|-------------|
| Dashboard | FastAPI + React SPA para monitoreo e interacción |
| Chat Backend | Backend de subproceso conectable para conversación con IA |
| Agent Pool | Registro de agentes de IA disponibles para delegar tareas |
| Task Graph | DAG de tareas multi-paso con dependencias |
| MCP Server | Servidor de herramientas/recursos en-proceso para consumo de agentes IA |
| Kanban | Seguimiento de flujo de trabajo mediante integración con Hermes |
| Headroom | Proxy de compresión de contexto y optimización de tokens |
| Sandbox | Contenedores Docker para ejecución aislada de agentes |

## Principios de Diseño

- Sin despliegues big-bang — cada cambio es desplegable independientemente
- Todas las dependencias externas son opcionales — el sistema degrada gradualmente
- Los secretos nunca se hardcodean, loguean o commitean
- Evaluación lazy — el modo ponytail prioriza soluciones mínimas funcionales
