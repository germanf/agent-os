# Inicio Rápido

## Prerrequisitos

- Python 3.11+
- Node.js 20+
- pnpm
- Git

## Instalación

```bash
git clone <url-del-repo>
cd agent-os

# Backend
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
pnpm install
```

## Primer Ejecución

```bash
# Iniciar el servidor backend (desde dashboard/)
uvicorn dashboard.main:app --port 8765 --reload

# En otra terminal, iniciar el frontend (desde dashboard/frontend/)
pnpm run dev
```

Abrí `http://localhost:5173` en tu navegador. El servidor de desarrollo Vite proxyfica las peticiones `/api` y `/auth` al backend FastAPI en el puerto 8765.

## Flujo de Trabajo Básico

1. **Configurar autenticación** — definí las variables de entorno `DASH_USER` y `DASH_PASS`, o creá un archivo `dashboard/.credentials.json`
2. **Explorar el dashboard** — navegá a `/` para la landing page, `/dashboard` para el estado del sistema
3. **Iniciar un chat** — andá a `/chat` para abrir una conversación con un backend de IA
4. **Crear un task graph** — andá a `/orchestrator` para definir flujos multi-agente
5. **Navegar notas** — si hay un vault de Obsidian configurado, visitá `/notes`

## ¿Qué Sigue?

- [Guía de Instalación](../installation/linux.md)
- [Referencia de Configuración](../configuration/environment.md)
- [Visión General de Arquitectura](../architecture/overview.md)
