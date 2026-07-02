# Instalación con Docker

> El soporte Docker está limitado al entorno sandbox para aislamiento de agentes. La aplicación principal no está containerizada — ejecutarla con `uvicorn` directamente es el método estándar.

## Contenedores Sandbox

El directorio `sandbox/` proporciona aislamiento basado en Docker para ejecutar agentes en paralelo. Ver `sandbox/README.md` para detalles.

### Prerrequisitos

```bash
sudo apt install docker.io
sudo usermod -aG docker $USER
# Cerrar sesión y volver a iniciar
```

### Uso

```bash
# Iniciar un contenedor sandbox
bash sandbox/sandbox-up.sh <rol>

# Detener un sandbox
bash sandbox/sandbox-down.sh <rol>

# Verificar estado
bash scripts/check-sandboxes.sh
```

## Despliegue en Producción

Para producción, ver la [Guía de Despliegue](../deployment/production.md) — usa systemd + nginx, no Docker.
