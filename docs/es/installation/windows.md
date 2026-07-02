# Instalación en Windows

## Prerrequisitos

1. Instalar **Python 3.11+** desde [python.org](https://python.org)
2. Instalar **Node.js 20+** desde [nodejs.org](https://nodejs.org)
3. Instalar **pnpm**: `npm install -g pnpm`
4. Instalar **Git** desde [git-scm.com](https://git-scm.com)

## Clonar y Configurar

```powershell
git clone <url-del-repo>
cd agent-os

# Entorno virtual Python
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r dashboard\requirements.txt

# Dependencias del frontend
cd dashboard\frontend
pnpm install
cd ..\..
```

## Servidor de Desarrollo

```powershell
# Terminal 1: backend
uvicorn dashboard.main:app --port 8765 --reload

# Terminal 2: frontend
cd dashboard\frontend
pnpm run dev
```

## Solución de Problemas

- Si `uvicorn` no se encuentra, asegurate de que el directorio Scripts de Python esté en PATH
- En Windows, usá `python` en lugar de `python3`
- Para problemas con rutas de archivo, usá barras normales o barras invertidas escapadas

Ver [Inicio Rápido](../getting-started/quickstart.md) para instrucciones de primera ejecución.
