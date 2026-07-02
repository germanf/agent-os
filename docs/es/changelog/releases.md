# Historial de Versiones

## Estrategia de Lanzamientos

El proyecto usa **versionado lineal** basado en fases de desarrollo:

- **Fase 1**: Fundación (specs, sandbox)
- **Fase 2**: Interfaz de Chat + Notas
- **Fase 3**: Memoria, skills, aprendizaje
- **Fase 4**: Plataforma completa — memoria, observabilidad, auto-mejora
- **Fase 5**: Listo para producción — multi-agente, MCP, hardening, frontend & UX

Cada fase se entrega como un conjunto de issues de GitHub, cada uno cerrado por un pull request a la rama `dev`. La rama `main` representa código listo para producción.

## Fase 5 (Última)

| Issue | Descripción | PR |
|-------|-------------|-----|
| #71 | Orquestación Multi-Agente — Task Graph, Agent Pool, Executor, SSE | #78 |
| #72 | Ecosistema MCP — 4 servidores MCP, Registry, UI de Admin | #79 |
| #73 | Hardening de Producción — Alertas, Backup, Rate Limits, Runbook | #77 |
| #74 | Frontend & UX — Landing, Dashboard, Componentes UI, Breadcrumbs | #80 |
| #68 | Skills de Plataforma Auto-mejorables — 5 archivos SKILL.md, bucle curator | #69 |

## Fase 4

| Issue | Descripción |
|-------|-------------|
| #27 | Sistema de memoria (almacenes de proyecto/org) |
| #28 | Trazado OpenTelemetry |
| #29 | Token accounting |
| #30 | Integración Headroom |
| #31 | Adaptador kanban Hermes |
| #32 | Flujos de aprobación |
| #33 | Checkpoints y reanudación de jobs |
| #34 | Notificaciones y alertas |
| #35 | Gestión de jobs cron |

## Fase 3

| Issue | Descripción |
|-------|-------------|
| — | Compresión de contexto Headroom |
| — | Bucle de revisión del curator Hermes |
| — | Definiciones de skills de plataforma |
| — | Plugin Ponytail |

## Fase 2

| Issue | Descripción |
|-------|-------------|
| — | Interfaz de chat con Claude |
| — | Navegador de vault Obsidian |
| — | Subida de archivos para chat |
| — | Soporte multi-backend |

## Fase 1

| Issue | Descripción |
|-------|-------------|
| — | Scaffolding del proyecto |
| — | Backend FastAPI |
| — | Frontend React |
| — | Contenedores sandbox |
| — | Middleware de auth |
| — | Rate limiting |
| — | Scripts de despliegue |
