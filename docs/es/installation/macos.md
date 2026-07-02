# Instalación en macOS

## Prerrequisitos

```bash
brew install python@3.11 node pnpm
```

## Clonar y Configurar

```bash
git clone <url-del-repo>
cd agent-os

# Entorno virtual Python
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r dashboard/requirements.txt

# Dependencias del frontend
cd dashboard/frontend
pnpm install
cd ../..
```

## Servidor de Desarrollo

```bash
# Terminal 1: backend
uvicorn dashboard.main:app --port 8765 --reload

# Terminal 2: frontend
cd dashboard/frontend && pnpm run dev
```

Ver [Inicio Rápido](../getting-started/quickstart.md) para instrucciones de primera ejecución.
