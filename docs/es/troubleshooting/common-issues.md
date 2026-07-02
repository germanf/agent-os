# Guía de Solución de Problemas

## El Backend No Inicia

| Síntoma | Causa Posible | Solución |
|---------|---------------|----------|
| `Address already in use` | Puerto 8765 ocupado | `lsof -ti:8765 \| xargs kill -9` |
| `ModuleNotFoundError` | Dependencias faltantes | `pip install -r requirements.txt` |
| `DASH_USER not set` | Auth no configurada | Configurar vars de entorno `DASH_USER` y `DASH_PASS` |
| `sqlite3.OperationalError` | BD corrupta | Restaurar desde backup: `bash dashboard/restore.sh` |

## El Build del Frontend Falla

| Síntoma | Causa Posible | Solución |
|---------|---------------|----------|
| `tsc errors` | Error de tipo TypeScript | Revisar y corregir errores de tipo |
| `Module not found` | Dependencias faltantes | `pnpm install` |
| `Build hangs` | Limitación de memoria | Aumentar memoria de Node: `NODE_OPTIONS=--max-old-space-size=4096 pnpm run build` |

## El Chat No Funciona

| Síntoma | Causa Posible | Solución |
|---------|---------------|----------|
| Claude no responde | Claude CLI no instalado | Instalar Claude Code |
| `claude: command not found` | CLI no está en PATH | Asegurar que Claude esté instalado y en PATH |
| Chat retorna vacío | Ningún backend seleccionado | Verificar variable `CHAT_BACKEND` |
| Stream SSE se traba | Buffering habilitado | Asegurar `proxy_buffering off` en nginx |

## Las Notas No Cargan

| Síntoma | Causa Posible | Solución |
|---------|---------------|----------|
| Árbol vacío | Vault no configurado | Configurar variable de entorno `VAULT_DIR` |
| Error de path traversal | Ruta inválida | Solo caracteres alfanuméricos, guiones, guiones bajos, slashes, puntos |
| Archivo no encontrado | La ruta no existe | Verificar la ruta exacta en el vault |

## Problemas del Orquestador

| Síntoma | Causa Posible | Solución |
|---------|---------------|----------|
| Tareas quedan en cola | No hay agentes disponibles | Verificar salud del agent pool: `GET /api/orchestrator/agents` |
| Tarea falla | Agente no responde | Verificar que el proceso del agente esté corriendo |
| DAG deadlock | Dependencia circular | Revisar el task graph por ciclos |
| Eventos SSE no se reciben | Cliente desconectado | Reconectar al stream |

## Problemas de Base de Datos

| Síntoma | Causa Posible | Solución |
|---------|---------------|----------|
| `database is locked` | Escrituras concurrentes | El modo WAL de SQLite debería prevenirlo; verificar transacciones largas |
| `no such table` | BD no inicializada | Acceder a cualquier endpoint para trigger auto-init |
| Espacio en disco | Archivo de BD creciendo | Los backups se mantienen 7 días; podar manualmente si es necesario |

## Rate Limiting

Si recibís `429 Too Many Requests`, esperá 60 segundos y reintentá. Los límites son:

- `/api/health`: 60/minuto
- La mayoría de endpoints: 30/minuto
- Mutaciones (POST/PATCH/DELETE): 10/minuto

## Obtener Ayuda

1. Revisá esta guía de solución de problemas
2. Consultá el [Runbook de Operaciones](../../operations/runbook.md)
3. Abrí un issue en GitHub con:
   - Mensaje de error completo y stack trace
   - Pasos para reproducir
   - Detalles del entorno (SO, versión de Python, versión de Node)
