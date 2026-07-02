# Configuración de Entorno

## Variables de Entorno

| Variable | Valor por Defecto | Requerida | Descripción |
|----------|-------------------|-----------|-------------|
| `DASH_USER` | — | Sí | Usuario de HTTP Basic Auth |
| `DASH_PASS` | — | Sí | Contraseña de HTTP Basic Auth |
| `CHAT_BACKEND` | `claude` | No | Backend preferido: `claude`, `opencode`, `codex`, `kimi` |
| `HEADROOM_PORT` | `8787` | No | Puerto del proxy Headroom |
| `HEADROOM_HOST` | `127.0.0.1` | No | Host del proxy Headroom |
| `HEADROOM_LEARN_INTERVAL_HOURS` | `168` | No | Intervalo del bucle de aprendizaje (horas, 7 días) |
| `HEADROOM_STATELESS` | `true` | No | Modo stateless de Headroom |
| `OPCODE_SERVER_PORT` | `8899` | No | Puerto del servidor OpenCode |
| `OPCODE_SERVER_HOST` | `127.0.0.1` | No | Host del servidor OpenCode |
| `HERMES_CURATOR_INTERVAL_HOURS` | `24` | No | Intervalo del bucle de revisión del curator |
| `PLATFORM_CRON_TICK_INTERVAL` | `30` | No | Intervalo del tick de cron en segundos |
| `LOG_JSON` | — | No | Habilitar serialización JSON de logs (cualquier valor) |
| `VAULT_DIR` | `/home/ubuntu/vault` | No | Ruta al directorio del vault de Obsidian |

## Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `dashboard/.credentials.json` | Alternativa a las variables `DASH_USER`/`DASH_PASS` |
| `dashboard/.env` | Definiciones de variables de entorno (gitignored) |
| `dashboard/nginx.conf` | Configuración de nginx para producción |
| `dashboard/agentic-software-boutique.service` | Archivo de unidad systemd |

## Gestión de Secretos

- Todos los archivos de credenciales (`.credentials.json`, `.env`) están en gitignore con `chmod 0600`
- Los secretos de API se muestran como `••••••••` en las respuestas GET
- Los endpoints POST preservan valores existentes cuando se envían valores enmascarados
- Nunca hardcodees credenciales en archivos fuente

## Configurar Autenticación

### Opción 1: Variables de Entorno
```bash
export DASH_USER=admin
export DASH_PASS=contraseñasegura
uvicorn dashboard.main:app --port 8765 --reload
```

### Opción 2: Archivo de Credenciales
Crear `dashboard/.credentials.json`:
```json
{
  "username": "admin",
  "password": "contraseñasegura"
}
```
Configurar permisos: `chmod 600 dashboard/.credentials.json`

## Prácticas Recomendadas

- Usá variables de entorno para producción (inyectadas via `.env` o unidad systemd)
- Rotá las credenciales regularmente
- Usá contraseñas fuertes (32+ caracteres recomendado para instancias expuestas a internet)
- Nunca commitees archivos de credenciales al control de versiones
- Para despliegues VPN-only, la subred VPN proporciona una capa de seguridad adicional
