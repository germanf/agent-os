# Contribuir

## Flujo de Trabajo de Desarrollo

```
Issue → Plan → Dev → CTO Review → Human Approval → CTO Merge → QA → Close
```

Ver `specs/workflow.md` para detalles completos.

## Estrategia de Branching

- `main` — código listo para producción
- `dev` — rama de integración para trabajo de features
- `feature/<nombre>` — ramas de feature, fusionadas a `dev` via PR
- No se permiten commits directos a `main` o `dev`

## Proceso de Pull Request

1. Creá una rama feature desde `dev`
2. Implementá tus cambios
3. Ejecutá lint y typecheck:
   ```bash
   ruff check dashboard/
   python3 -m py_compile dashboard/main.py
   cd dashboard/frontend && pnpm run build
   ```
4. Creá un PR a `dev`
5. El CTO revisa y aprueba
6. Humano aprueba (cuando sea requerido)
7. El CTO fusiona
8. QA valida
9. El issue se cierra

## Convenciones de Commits

Usá mensajes de commit claros y descriptivos:

```
<área> — <descripción breve>

Ejemplos:
agents — agregar stub de backend codex
docs — traducir página de arquitectura a español
fix — resolver path traversal en endpoint de notas
```

## Estándares de Código

### Python
- Type hints requeridos en todas las firmas de funciones
- Seguir reglas de linting de ruff (configurado en `pyproject.toml`)
- Una clase por archivo para tipos significativos
- Usar ABCs para interfaces

### TypeScript / React
- Modo estricto de TypeScript
- Componentes funcionales con hooks (sin class components)
- Tailwind v4 para estilos (CSS-first, sin `tailwind.config.ts`)
- Nombres de componentes descriptivos

### Documentación
- Cada nueva funcionalidad debe incluir documentación
- Toda la documentación debe existir tanto en **inglés** como en **español**
- Los archivos de documentación deben mantener estructura idéntica entre idiomas
- Usar solo Markdown (sin HTML, sin GitHub Wiki)

## Reporte de Issues

- Usá issues de GitHub para reportes de bugs, solicitudes de features y tareas
- Cada issue recibe exactamente una etiqueta: `bug`, `feature`, `security`, o `documentation`
- Incluí pasos para reproducir en bugs
- Incluí criterios de aceptación para features

## Archivos Temporales

Usá siempre `tmp/` (raíz del proyecto) para archivos temporales — nunca `/tmp/`, `/dev/shm/`, o directorios temporales del sistema. El directorio `tmp/` está en gitignore, tiene alcance del proyecto, y se limpia con `git clean`.

## Licencia

Al contribuir, aceptás que tus contribuciones se licenciarán bajo la licencia del proyecto.
