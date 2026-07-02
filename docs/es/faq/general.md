# Preguntas Frecuentes

## Generales

### ¿Qué es Agentic Software Boutique?
Una plataforma abierta para desarrollo de software asistido por IA. Proporciona un panel web, orquestación multi-agente, servidores de herramientas MCP y backends de chat conectables para interactuar con diversos agentes de IA de codificación.

### ¿Qué backends de IA están soportados?
Claude Code (completo), OpenCode (completo), Codex (stub), Kimi (stub). El protocolo `ChatBackend` facilita agregar nuevos backends.

### ¿Necesito una suscripción?
Necesitás una suscripción de Claude Code para usar el backend Claude. El dashboard y las funcionalidades de orquestación funcionan sin ninguna suscripción.

### ¿Qué es la filosofía "ponytail"?
Un enfoque de desarrollo lazy pero eficiente: usar lo que ya existe, preferir stdlib sobre dependencias, escribir el código mínimo que funciona, y marcar simplificaciones deliberadas con comentarios `ponytail:`.

## Técnicas

### ¿Qué base de datos usa?
SQLite con modo WAL, almacenado en `dashboard/data/chat.db`. No requiere servidor de base de datos externo.

### ¿Puedo usar PostgreSQL?
No actualmente. El proyecto está diseñado para despliegue de usuario único/equipo pequeño donde la simplicidad de SQLite es superior. La capa de persistencia está aislada en `chat_store.py` para reemplazo futuro.

### ¿Cómo restablezco la base de datos?
Eliminá `dashboard/data/chat.db` y reiniciá el servidor. Se recreará automáticamente.

### ¿Hay una API REST?
Sí. Todas las funcionalidades están expuestas via endpoints HTTP bajo `/api/`. Ver la [Referencia de API](../api/endpoints.md) para detalles.

### ¿Puedo ejecutar esto en Docker?
La aplicación principal no está containerizada — se ejecuta directamente con uvicorn. Docker se usa solo para el aislamiento del sandbox de agentes (ver `sandbox/`).

## Desarrollo

### ¿Cómo agrego un nuevo backend de chat?
1. Creá un nuevo archivo en `dashboard/backends/`
2. Implementá la ABC `ChatBackend` de `dashboard/backends/protocol.py`
3. Registralo en `dashboard/backends/__init__.py`

### ¿Cómo agrego un nuevo servidor MCP?
1. Creá un nuevo archivo en `dashboard/mcp/servers/`
2. Extendé `MCPServer` de `dashboard/mcp/server.py`
3. Definí herramientas con `ToolDef` y recursos con `ResourceDef`
4. Registralo en `dashboard/main.py` durante el inicio

### ¿Cómo agrego una nueva capacidad de agente?
1. Agregá una nueva clase extendiendo `AgentCapability` en `dashboard/agents/protocol.py`
2. Creá la implementación en `dashboard/agents/`
3. Registrala en `dashboard/agents/__init__.py`

## Operaciones

### ¿Cómo reinicio el servicio?
```bash
sudo systemctl restart agentic-software-boutique
```

### ¿Cómo veo los logs?
```bash
sudo journalctl -u agentic-software-boutique -f
```

### ¿Cada cuánto se hacen los backups?
Cada 6 horas, con retención de 7 días.

### ¿Cómo resto desde un backup?
```bash
bash dashboard/restore.sh
```

### ¿Puedo acceder al dashboard desde fuera de la VPN?
Por defecto, nginx restringe el acceso a `10.0.0.0/24`. Para cambiarlo, editá `dashboard/nginx.conf` y actualizá las directivas `allow`.
