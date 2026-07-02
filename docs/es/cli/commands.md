# Referencia de CLI

## CLIs Externos

La plataforma interactúa con varios CLIs externos. No están incluidos — deben instalarse por separado.

### Hermes

La CLI de la plataforma Hermes gestiona tableros kanban, jobs cron, skills y revisiones del curator.

```bash
# Kanban
hermes kanban list
hermes kanban create --queue "Fase 5" --title "Tarea"
hermes kanban complete <id>

# Cron
hermes cron list
hermes cron create --schedule "0 9 * * *" --command "..."

# Curator
hermes curator run

# Skills
hermes skills list
hermes skills install <ruta>
```

### Claude Code

```bash
claude -p "implementar feature X"                         # Una sola ejecución
claude -p "continue" --resume <sesión>                     # Reanudar conversación
claude -p "explica este código" --output-format stream-json # Para uso programático
```

### Headroom

Proxy de compresión de contexto y optimización de tokens:

```bash
headroom                                       # Iniciar proxy
headroom remember "contexto importante"        # Almacenar en memoria
headroom recall                                # Recuperar contexto
headroom learn                                 # Aprender de patrones
headroom status                                # Estado del proxy
```

### OpenCode

```bash
opencode serve --port 8899                     # Iniciar servidor
opencode run "implementar feature"             # Tarea única
```

## Comandos Internos

### Backend

```bash
uvicorn dashboard.main:app --port 8765 --reload                    # Servidor de desarrollo
python3 -m py_compile dashboard/main.py                             # Verificación sintáctica
ruff check dashboard/                                                # Lint
```

### Frontend

```bash
pnpm run dev         # Servidor de desarrollo (puerto 5173, proxy al backend)
pnpm run build       # Build de producción
pnpm run test        # Ejecutar tests
pnpm run lint        # ESLint
```

### Despliegue

```bash
bash dashboard/start.sh   # Despliegue completo de producción (idempotente)
bash dashboard/restore.sh # Restaurar BD desde backup
bash dashboard/diagnose.sh # Diagnóstico de VM (español)
```
