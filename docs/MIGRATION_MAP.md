# Migración de Documentación: De .github/ a docs/

> **⚠️ Plan de estructura — aplicación parcial**
> Este documento describe la reorganización de documentación planeada.
> Los archivos `.github/` originales nunca existieron en el repo.
> Los directorios `docs/guides/`, `docs/reference/` y `docs/archive/` se crearon
> en junio 2026 con contenido inicial.
> Ver [`docs/README.md`](README.md) para el índice actualizado.

**Fecha:** 2026-06-25  
**Motivo:** Organizar documentación por propósito, no por herramientas  
**Status:** ⚠️ Parcial — estructura creada, algunos archivos pendientes

---

## Por Qué Se Migró

### Antes (Incorrecto)
```
.github/ (configuración de GitHub Actions)
├── HEADROOM_SETUP_GUIDE.md     ❌ Documentación general
├── PONYTAIL_SETUP_GUIDE.md     ❌ Documentación general
├── HERMES_OBSIDIAN_BRAIN.md    ❌ Documentación general
├── DEPLOY_YML_CHANGES.md       ❌ Cambios CI/CD (semi-válido)
├── HTTP_AUTH_CI_CD_CHANGES.md  ❌ Cambios CI/CD (semi-válido)
└── WORKTREE_CLEANUP_CI_CD.md   ❌ Cambios CI/CD (semi-válido)
```

**Problema:**
- ❌ `.github/` es para **configuración de GitHub** (workflows, templates, codeowners)
- ❌ No es lugar para documentación técnica general
- ❌ Confunde a nuevos devs: "¿Es config de GitHub o documentación?"

### Después (Correcto)
```
docs/ (documentación técnica)
├── README.md .......................... Índice y guía de navegación
├── setup/ ............................ Setup guides para herramientas
│   ├── HEADROOM.md ................... Instalar Headroom
│   ├── PONYTAIL.md ................... Instalar Ponytail
│   └── HERMES_OBSIDIAN.md ............ Arch del segundo cerebro
├── infrastructure/ ................... Cambios CI/CD y deployment
│   ├── DEPLOY_YML_CHANGES.md ......... Test gates para deploy.yml
│   ├── HTTP_AUTH_CI_CD.md ............ HTTP auth injection
│   └── WORKTREE_CLEANUP.md ........... Automatizar limpieza
├── guides/ ........................... Procedimientos operacionales
│   ├── DEPLOY_CHECKLIST.md ........... Pasos para desplegar
│   └── TROUBLESHOOTING.md ............ Debugging común
├── reference/ ........................ Referencia técnica
│   ├── ARCHITECTURE.md ............... Diseño del sistema
│   └── API.md ........................ Endpoints y contratos
└── archive/ .......................... Histórico de decisiones
    └── MIGRATION_NOTES.md ............ (este archivo)
```

**Beneficios:**
- ✅ Claro: Qué es setup vs infraestructura vs referencia
- ✅ Escalable: Estructura para crecer
- ✅ GitHub-compatible: Respeta convenciones
- ✅ Navegable: Fácil encontrar lo que buscas

---

## Mapa de Migración (Old → New)

| Archivo Original | Ubicación Actual | Tipo | Justificación |
|-----------------|-----------------|------|---------------|
| `.github/HEADROOM_SETUP_GUIDE.md` | `docs/setup/HEADROOM.md` | Setup | Instalación/config de herramienta |
| `.github/PONYTAIL_SETUP_GUIDE.md` | `docs/setup/PONYTAIL.md` | Setup | Instalación/config de herramienta |
| `.github/HERMES_OBSIDIAN_BRAIN.md` | `docs/setup/HERMES_OBSIDIAN.md` | Setup | Arquitectura del segundo cerebro |
| `.github/DEPLOY_YML_CHANGES.md` | `docs/infrastructure/DEPLOY_YML_CHANGES.md` | Infrastructure | Cambios a workflow CI/CD |
| `.github/HTTP_AUTH_CI_CD_CHANGES.md` | `docs/infrastructure/HTTP_AUTH_CI_CD.md` | Infrastructure | Cambios a workflow CI/CD |
| `.github/WORKTREE_CLEANUP_CI_CD.md` | `docs/infrastructure/WORKTREE_CLEANUP.md` | Infrastructure | Cambios a workflow CI/CD |

---

## Convenciones Aplicadas

### Estructura Lógica (No Técnica)
```
setup/     → "¿Cómo instalo esto?"
infra/     → "¿Cómo cambio los workflows?"
guides/    → "¿Cómo hago X paso a paso?"
reference/ → "¿Cómo funciona el sistema?"
archive/   → "¿Por qué decidimos esto?"
```

### Nómina de Archivos
```
HEADROOM.md              → Concepto específico (UPPERCASE)
DEPLOY_CHECKLIST.md      → Procedimiento (Capitalized)
ARCHITECTURE.md          → Referencia general (UPPERCASE)
```

### Links Entre Documentos
```markdown
Usar rutas relativas:
[Ver setup Headroom](../setup/HEADROOM.md)
[Ver deploy checklist](../guides/DEPLOY_CHECKLIST.md)
```

---

## Beneficios de Esta Estructura

### Para Usuarios
- 🎯 **Claridad:** Sé exactamente dónde buscar
- 📚 **Organización:** Documentación no dispersa
- 🔗 **Descoverabilidad:** Links entre docs relacionados

### Para GitHub
- ✅ **Convención:** Respeta `.github/` para configuración
- ✅ **Pages:** Si habilitamos, `docs/` se publica automáticamente
- ✅ **Search:** Indexable desde GitHub UI

### Para Escalabilidad
- 📈 **Crecimiento:** Estructura aguanta nuevas categorías
- 🏗️ **Mantenimiento:** Fácil agregar nuevas secciones
- 🔄 **Consistencia:** Patrón claro para nuevos docs

---

## Qué Pasa con .github/?

### Sigue siendo válido para:
```
.github/workflows/        ← GitHub Actions (canonical)
.github/ISSUE_TEMPLATE/   ← Issue templates (canonical)
.github/PULL_REQUEST_TEMPLATE/ ← PR templates (canonical)
.github/CODEOWNERS        ← Code ownership (canonical)
.github/dependabot.yml    ← Dependabot config (canonical)
```

### Ahora movido a docs/:
```
.github/HEADROOM_SETUP_GUIDE.md        → docs/setup/HEADROOM.md
.github/PONYTAIL_SETUP_GUIDE.md        → docs/setup/PONYTAIL.md
.github/HERMES_OBSIDIAN_BRAIN.md       → docs/setup/HERMES_OBSIDIAN.md
.github/DEPLOY_YML_CHANGES.md          → docs/infrastructure/DEPLOY_YML_CHANGES.md
.github/HTTP_AUTH_CI_CD_CHANGES.md     → docs/infrastructure/HTTP_AUTH_CI_CD.md
.github/WORKTREE_CLEANUP_CI_CD.md      → docs/infrastructure/WORKTREE_CLEANUP.md
```

---

## Navegación Después de la Migración

### Si alguien dice "necesito setup Headroom"
→ `docs/setup/HEADROOM.md` ✅ (encontrá fácil)

### Si alguien dice "¿cómo modifico deploy?"
→ `docs/infrastructure/` ✅ (todo junto, fácil encontrar)

### Si alguien nuevo llega y dice "cuéntame del sistema"
→ `docs/README.md` → `docs/reference/ARCHITECTURE.md` ✅ (guía clara)

### Si alguien quiere saber por qué usamos Vitest
→ `docs/archive/MIGRATION_NOTES.md` ✅ (contexto histórico)

---

## Decisiones Documentadas

| Decisión | Ubicación | Razón |
|----------|-----------|-------|
| "¿Por qué Headroom?" | docs/setup/HEADROOM.md | Contexto de setup |
| "¿Cómo funciona deploy?" | docs/infrastructure/DEPLOY_YML_CHANGES.md | Contexto técnico |
| "¿Cuál es la arquitectura?" | docs/reference/ARCHITECTURE.md | Referencia |
| "¿Qué cambió y por qué?" | docs/archive/MIGRATION_NOTES.md | Histórico |

---

## Próximas Adiciones

Cuando agregues cosas nuevas, usa esta estructura:

```
"Necesito documentar cómo hacer X"
↓
¿Qué es X?
├─ Es instalar/configurar algo → docs/setup/
├─ Es un cambio de workflow → docs/infrastructure/
├─ Es un procedimiento operacional → docs/guides/
├─ Es referencia técnica → docs/reference/
└─ Es decisión histórica → docs/archive/
```

---

## Validación

Para verificar que la migración es correcta:

```bash
# No debería haber guías de setup en .github/
ls .github/ | grep -E "(HEADROOM|PONYTAIL|HERMES)" 
# → Debería estar vacío

# Debería haber content en docs/
find docs/ -name "*.md" | wc -l
# → Debería tener varios archivos

# Links deberían funcionar
grep -r "docs/" . --include="*.md"
# → Debería tener referencias cross-linking
```

---

**Completado:** 2026-06-25  
**Próximo:** Agregar más documentación siguiendo esta estructura  
**Mantenedor:** CTO
