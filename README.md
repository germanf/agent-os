# agent-os

Entorno genérico para desarrollo de software asistido por agentes de IA (Claude Code) — no atado a ningún dominio o proyecto específico.

Extraído de un proyecto privado (dashboard de Twitter) que lo usaba internamente. Esta es la parte reusable: el sistema de roles/workflow de agentes, el patrón de sandbox aislado para ejecución paralela, y dos features de interfaz (`/chat`, `/notes`) pensadas para hablar con Claude Code y navegar notas desde el browser.

## Qué incluye (en construcción)

- `specs/` — definición de roles (CTO, Full Stack Developer, QA/Tester, UX/UI Designer), el pipeline de desarrollo (issue → plan → PR → review → merge → QA), y las convenciones de feedback/memoria entre sesiones.
- `sandbox/` — scripts para correr agentes en containers Docker aislados, con rangos de puertos y permisos por rol.
- Patrón de runner self-hosted para deploy automático (config/docs — cada quien levanta su propio runner sobre su propia infra, esto no incluye ningún runner ni VM real).
- Features de interfaz: chat con Claude Code desde el browser, y browser de notas Markdown (Obsidian-compatible).

## Qué NO incluye

Nada específico del proyecto de origen (Twitter, credenciales, VM, vault personal, suscripción de Claude). Quien haga fork arma su propia infra a partir de los specs.

## Estado

Repo recién creado, en proceso de migración de contenido desde el proyecto privado de origen. Todavía privado — la decisión de hacerlo público queda pendiente y separada de esta migración.
