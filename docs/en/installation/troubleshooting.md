# Installation Troubleshooting

## Backend Issues

### `pip install` fails
Ensure you have Python 3.11+ and the latest pip:
```bash
python3 -m pip install --upgrade pip
```

### `uvicorn: command not found`
Activate the virtual environment first:
```bash
source .venv/bin/activate
```

### Port 8765 already in use
```bash
lsof -ti:8765 | xargs kill -9
```

## Frontend Issues

### `pnpm: command not found`
Install pnpm globally:
```bash
npm install -g pnpm
```

### `pnpm install` fails
Ensure Node.js 20+:
```bash
node --version
```

### Build errors
Clear caches and retry:
```bash
rm -rf node_modules .pnpm-store
pnpm install
pnpm run build
```

## Still Stuck?

- Check the [Troubleshooting Guide](../troubleshooting/common-issues.md)
- Open a GitHub issue with your error logs
