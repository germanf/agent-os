# Glosario de Términos

| Término | Definición |
|---------|------------|
| **ADR** | Architecture Decision Record — documento que captura una decisión arquitectónica y su fundamento |
| **Agente** | Entidad impulsada por IA que puede realizar tareas de desarrollo de software (ej. corregir bugs, implementar features) |
| **Agent Pool** | Registro de agentes disponibles con monitoreo de salud |
| **Backend** | Implementación de `ChatBackend` que envuelve una CLI de IA (Claude, OpenCode, etc.) para interacción por chat |
| **Capacidad** | Interfaz que define lo que un agente puede hacer (desarrollar, revisar, QA, orquestar) |
| **ChatBackend** | Clase base abstracta para backends de conversación de IA conectables |
| **DAG** | Directed Acyclic Graph — usado para modelar dependencias de tareas en orquestación |
| **DOMPurify** | Biblioteca de sanitización XSS usada en el frontend |
| **FastAPI** | Framework web Python usado para la API del backend |
| **Headroom** | Proxy de compresión de contexto y optimización de tokens de IA |
| **Hermes** | CLI de la plataforma de agentes para kanban, cron, curator y gestión de skills |
| **HSTS** | HTTP Strict-Transport-Security — fuerza conexiones HTTPS |
| **Kanban** | Sistema de seguimiento de tareas usado para gestión de flujos de trabajo |
| **MCP** | Model Context Protocol — interfaz estándar para exponer herramientas y recursos a agentes de IA |
| **MCPServer** | Clase base abstracta para servidores de herramientas/recursos MCP en-proceso |
| **Middleware** | Componentes ASGI middleware para auth, HSTS, trazado y rate limiting |
| **Obsidian** | Aplicación de toma de notas en Markdown; la plataforma puede navegar vaults de Obsidian |
| **OpenCode** | CLI de agente de codificación; uno de los backends de chat soportados |
| **Orquestador** | Sistema que descompone objetivos en task graphs y delega en agentes |
| **Ponytail** | Filosofía de desarrollo lazy que prioriza soluciones mínimas funcionales |
| **Rate Limiting** | Limitación de solicitudes por endpoint mediante slowapi |
| **Sandbox** | Entorno aislado basado en Docker para ejecutar agentes |
| **SPA** | Single Page Application — el frontend React |
| **SQLite** | Motor de base de datos embebido usado para persistencia |
| **SSE** | Server-Sent Events — usado para streaming de logs de jobs y eventos de tareas |
| **SubTask** | Unidad de trabajo individual dentro de un task graph |
| **systemd** | Sistema de init de Linux usado para gestionar el proceso uvicorn |
| **Tailwind v4** | Framework CSS usado para estilos del frontend |
| **Task Graph** | DAG de subtareas con dependencias para ejecución multi-agente |
| **Token Accounting** | Seguimiento del uso de tokens LLM en toda la plataforma |
| **uvicorn** | Servidor ASGI usado para ejecutar la aplicación FastAPI |
| **Vault** | Directorio de vault de Obsidian que contiene notas Markdown |
| **Vitest** | Framework de tests unitarios para el frontend |
| **WAL mode** | Write-Ahead Logging — modo SQLite para mejor acceso concurrente |
| **Workflow** | Definición de proceso multi-paso que puede cargarse y ejecutarse |
