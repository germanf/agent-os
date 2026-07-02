# Despliegue en Producción

## Stack

- **SO**: Ubuntu 20.04+ (VPN-only, subred WireGuard `10.0.0.0/24`)
- **Servidor Web**: nginx (reverse proxy, HTTP→HTTPS redirect, terminación SSL)
- **Servidor de App**: uvicorn (puerto 8765, gestionado por systemd)
- **Base de Datos**: SQLite (modo WAL)
- **Firewall**: iptables (persistido via netfilter-persistent)

## Despliegue en un Comando

```bash
bash dashboard/start.sh
```

Este script idempotente:

1. Build del frontend (`pnpm install --frozen-lockfile && pnpm run build`)
2. Crea un entorno virtual Python atómicamente (`.venv.new` → swap a `.venv`)
3. Instala dependencias Python desde `requirements.txt`
4. Genera un certificado TLS autofirmado (validez 10 años)
5. Instala la configuración de nginx
6. Instala el servicio systemd (`agentic-software-boutique.service`)
7. Inyecta `DASH_USER`/`DASH_PASS` desde `.env` en la unidad systemd
8. Ejecuta verificaciones previas (directorio de datos, prueba de inicio de app Python)
9. Reinicia uvicorn y verifica que esté escuchando

## Configuración Manual

### 1. Dependencias del Sistema

```bash
sudo apt update
sudo apt install nginx python3 python3-venv python3-pip netfilter-persistent iptables-persistent
```

### 2. Configuración de nginx

La configuración de producción está en `dashboard/nginx.conf`. Opciones clave:

```nginx
location / {
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Soporte SSE (buffering off)
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;

    # Uploads
    client_max_body_size 55M;
}
```

### 3. Servicio systemd

El archivo de servicio está en `dashboard/agentic-software-boutique.service`:

```ini
[Unit]
Description=Agentic Software Boutique
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agent-os/dashboard
ExecStart=/home/ubuntu/agent-os/dashboard/.venv/bin/uvicorn dashboard.main:app --host 127.0.0.1 --port 8765 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4. Certificado TLS

Generación de certificado autofirmado (lo hace `start.sh`):

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/agentic-boutique-selfsigned.key \
  -out /etc/nginx/ssl/agentic-boutique-selfsigned.crt \
  -subj "/CN=agentic-boutique"
```

Para producción, reemplazar con un certificado de una CA real.

### 5. Firewall

```bash
# Permitir HTTP/HTTPS desde VPN
sudo iptables -A INPUT -s 10.0.0.0/24 -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -s 10.0.0.0/24 -p tcp --dport 443 -j ACCEPT
# Permitir puerto de app solo desde localhost
sudo iptables -A INPUT -s 127.0.0.1 -p tcp --dport 8765 -j ACCEPT
# Guardar reglas
sudo netfilter-persistent save
```

## Variables de Entorno

Configurá estas en el entorno de systemd o en un archivo `.env` leído por `start.sh`:

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `DASH_USER` | Sí | Usuario de HTTP Basic Auth |
| `DASH_PASS` | Sí | Contraseña de HTTP Basic Auth |
| `LOG_JSON` | No | Habilitar logs JSON (cualquier valor) |
| `VAULT_DIR` | No | Ruta al vault de Obsidian |

## Monitoreo

### Health Checks

```bash
curl https://tu-dominio/api/health
# → {"status":"healthy","checks":{"db":"ok","frontend":"ok"},...}
```

### Diagnósticos

```bash
curl -u usuario:contraseña https://tu-dominio/api/diagnostics
# → Reporte completo de salud del despliegue
```

### Alertas

```bash
curl -u usuario:contraseña https://tu-dominio/api/alerts
# → Lista de alertas activas
```

## Backup y Restauración

Los backups automáticos se ejecutan cada 6 horas con retención de 7 días:

```bash
# Backup manual
python3 -c "from dashboard.backup import manual_backup; manual_backup()"

# Restaurar
bash dashboard/restore.sh
```

## Logging

Por defecto, los logs son legibles por humanos. Configurá `LOG_JSON=1` para serialización JSON:

```bash
LOG_JSON=1 uvicorn dashboard.main:app --port 8765
```

Formato JSON: `{"time":"...", "level":"INFO", "event":"...", "module":"...", "context":{...}}`

## Runbook de Operaciones

Ver `docs/operations/runbook.md` para:
- Procedimientos de reinicio
- Pasos de backup/restauración
- Modos de fallo comunes
- Rutas de escalamiento
