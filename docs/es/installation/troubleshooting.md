# Solución de Problemas de Instalación

## Problemas del Backend

### `pip install` falla
Asegurate de tener Python 3.11+ y la última versión de pip:
```bash
python3 -m pip install --upgrade pip
```

### `uvicorn: command not found`
Activá el entorno virtual primero:
```bash
source .venv/bin/activate
```

### Puerto 8765 ya está en uso
```bash
lsof -ti:8765 | xargs kill -9
```

## Problemas del Frontend

### `pnpm: command not found`
Instalá pnpm globalmente:
```bash
npm install -g pnpm
```

### `pnpm install` falla
Asegurate de tener Node.js 20+:
```bash
node --version
```

### Errores de build
Limpia los cachés y reintentá:
```bash
rm -rf node_modules .pnpm-store
pnpm install
pnpm run build
```

## ¿Seguís Atascado?

- Consultá la [Guía de Solución de Problemas](../troubleshooting/common-issues.md)
- Abrí un issue en GitHub con tus logs de error
