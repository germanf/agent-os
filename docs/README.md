# Documentación del Proyecto

> **Estado:** Estructura completa. Algunos archivos son stubs (marcados ⚠️) pendientes de contenido real.
> Ver [`AGENTS.md`](../AGENTS.md) para instrucciones del agente y arquitectura resumida.

**Ubicación canónica:** `/home/ubuntu/Claude/docs/`

## Filosofía de Organización

Este directorio contiene toda la documentación técnica del proyecto, organizada por **propósito** y **audiencia**, no por herramientas o tecnologías.

**¿Por qué aquí y no en `.github/`?**

- ✅ `.github/` es para **configuración de GitHub** (Actions, templates, codeowners)
- ✅ `docs/` es para **documentación técnica** (guías, arquitectura, referencias)
- ✅ Escalabilidad: cuando crezca, tenemos estructura clara
- ✅ Convención estándar: GitHub reconoce automáticamente `docs/` para GitHub Pages

---

## Estructura

```
docs/
├── README.md (este archivo)
├── setup/                         ← Guías de instalación/configuración
│   ├── HEADROOM.md               (Token optimization)
│   ├── PONYTAIL.md               (Code quality)
│   └── HERMES_OBSIDIAN.md        (Second brain architecture)
│
├── infrastructure/               ← Cambios & configuración CI/CD
│   ├── DEPLOY_YML_CHANGES.md     (Test gates para deploy.yml)
│   ├── HTTP_AUTH_CI_CD.md        (HTTP Auth injection)
│   └── WORKTREE_CLEANUP.md       (Worktree automation)
│
├── guides/                        ← Procedimientos y walkthroughs
│   ├── DEPLOY_CHECKLIST.md       (Pasos para desplegar)
│   ├── INCIDENT_RESPONSE.md      (Qué hacer si algo falla)
│   └── TROUBLESHOOTING.md        (Debugging común)
│
├── reference/                     ← Referencia técnica
│   ├── ARCHITECTURE.md           (Diseño del sistema)
│   ├── API.md                    (Endpoints y contratos)
│   └── DATABASE_SCHEMA.md        (Modelos de datos)
│
└── archive/                       ← Documentación histórica
    └── MIGRATION_NOTES.md        (Cambios pasados, decisiones)
```

---

## Justificación por Carpeta

### `/setup/`
**Propósito:** Guías paso-a-paso para instalar y configurar herramientas

**Contenido:**
- `HEADROOM.md` — Instalación, configuración, integración, monitoring
- `PONYTAIL.md` — Instalación, rules, CI/CD integration
- `HERMES_OBSIDIAN.md` — Arquitectura del segundo cerebro

**Justificación:**
- ✅ Agrupa todo lo relacionado a "cómo instalar X"
- ✅ Fácil de encontrar cuando alguien dice "necesito setup Headroom"
- ✅ Separado de cambios de config (que van a infrastructure/)

---

### `/infrastructure/`
**Propósito:** Cambios a la configuración de CI/CD y deployment

**Contenido:**
- `DEPLOY_YML_CHANGES.md` — Código exacto para modificar deploy.yml
- `HTTP_AUTH_CI_CD.md` — Cómo inyectar credenciales en CI/CD
- `WORKTREE_CLEANUP.md` — Automatizar limpieza de worktrees

**Justificación:**
- ✅ Diferente de "setup" (estos son cambios a archivos existentes)
- ✅ Criticidad: bloqueadores de deploy van aquí
- ✅ Fácil de encontrar cuando se debate "¿cómo hacemos deploy seguro?"

---

### `/guides/`
**Propósito:** Procedimientos operacionales (cómo hacer cosas recurrentes)

**Contenido:**
- `DEPLOY_CHECKLIST.md` — Pasos ordenados antes de desplegar
- `INCIDENT_RESPONSE.md` — Qué hacer si HTTPS falla, worktree explota, etc
- `TROUBLESHOOTING.md` — Errores comunes y soluciones

**Justificación:**
- ✅ Para personas que necesitan "actuar ahora"
- ✅ Procedimientos paso-a-paso, no guías de instalación
- ✅ Living documentation (se actualiza con experience)

---

### `/reference/`
**Propósito:** Referencia técnica sobre el sistema (léxico, APIs, diseño)

**Contenido:**
- `ARCHITECTURE.md` — Cómo funciona todo together
- `API.md` — Endpoints, parámetros, responses
- `DATABASE_SCHEMA.md` — Tablas, relaciones, constraints

**Justificación:**
- ✅ Para personas que necesitan entender el sistema (devs nuevos)
- ✅ Respuesta a "¿qué endpoints existen?" o "¿cómo está diseñado?"
- ✅ No acción = referencia pura

---

### `/archive/`
**Propósito:** Histórico de decisiones y cambios pasados

**Contenido:**
- `MIGRATION_NOTES.md` — "Por qué movimos de X a Y"
- Viejas guías (cuando cambian)
- Decisiones arquitectónicas ya resueltas

**Justificación:**
- ✅ Preservar contexto histórico (ej: "¿por qué usamos Vitest y no Jest?")
- ✅ No clutters la documentación actual
- ✅ Útil para auditorías y entendimiento

---

## Cómo Navegar

### "Necesito instalar Headroom"
→ `docs/setup/HEADROOM.md`

### "¿Cómo hago deploy?"
→ `docs/guides/DEPLOY_CHECKLIST.md`

### "¿Qué endpoints existen?"
→ `docs/reference/API.md`

### "¿Por qué design así?"
→ `docs/reference/ARCHITECTURE.md`

### "HTTPS no funciona"
→ `docs/guides/TROUBLESHOOTING.md`

### "¿Cómo cambio deploy.yml?"
→ `docs/infrastructure/DEPLOY_YML_CHANGES.md`

### "¿Por qué migramos de X?"
→ `docs/archive/MIGRATION_NOTES.md`

---

## GitHub Integration

GitHub reconoce automáticamente este directorio:

1. **GitHub Pages:** Si habilitamos, `docs/` se publica como sitio público
2. **GitHub Code Search:** Buscable desde GitHub UI
3. **Visibility:** Aparece en el "About" del repo como documentación
4. **Wiki Alternative:** Mejor que GitHub Wiki (versionado en git)

---

## Convenciones

### Nómina de archivos
- UPPERCASE.md para conceptos (ARCHITECTURE.md)
- Capitalized.md para procedimientos (DEPLOY_CHECKLIST.md)
- Docs críticos en setup/ e infrastructure/

### Formato
```markdown
# Título (h1)

## Propósito
Qué es y por qué existe

## Contenido
Secciones principales

## How-to
Pasos accionables

## References
Enlaces a otros docs
```

### Linking
Usar rutas relativas:
```markdown
Ver [Setup Headroom](../setup/HEADROOM.md)
Ver [Deploy Checklist](../guides/DEPLOY_CHECKLIST.md)
```

---

## Mantenimiento

**Actualizar cuando:**
- [ ] Se cambia un proceso (ej: nuevo workflow)
- [ ] Se resuelve un problema (agregar a troubleshooting)
- [ ] Se toma decisión arquitectónica importante

**No actualizar:**
- Cambios menores de código (va en commits)
- Descubrimientos personales (va en memory/ del usuario)
- Estado temporal (va en PRs/issues)

---

## Próximas Adiciones

- [ ] `reference/DATABASE_SCHEMA.md`
- [ ] `guides/TROUBLESHOOTING.md`
- [ ] `guides/INCIDENT_RESPONSE.md`
- [ ] `archive/MIGRATION_NOTES.md`

---

**Creado:** 2026-06-25  
**Filosofía:** Structure by purpose, not by tool  
**Mantenedor:** CTO
