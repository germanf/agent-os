# Testing

## Testing del Backend

Los scripts de test están en `dashboard/tests/` y `tests/`:

```bash
# Verificación sintáctica
python3 -m py_compile dashboard/main.py

# Lint
ruff check dashboard/

# Ejecutar tests
python3 -m pytest dashboard/tests/
python3 -m pytest tests/
```

Los tests del backend cubren:
- **Inicio**: Importación de la app FastAPI y secuencia de inicio
- **Autenticación**: Cumplimiento de HTTP Basic Auth
- **HTTPS**: Cumplimiento de redirección
- **Entorno**: Permisos y configuración
- **Regresión**: Casos de test específicos de issues

## Testing del Frontend

Los tests usan **Vitest** + **@testing-library/react**:

```bash
cd dashboard/frontend

# Ejecutar tests
pnpm run test

# Con cobertura
pnpm run test:coverage
```

Los archivos de test están junto a los archivos fuente:
- `src/lib/__tests__/sanitize.test.ts` — Sanitización XSS
- `src/lib/useToolJob.test.ts` — Hook de ciclo de vida de jobs
- `src/pages/Chat.test.tsx` — Renderizado de la página de chat

### Configuración de Tests

- **Framework**: vitest
- **DOM**: jsdom
- **Matchers**: @testing-library/jest-dom
- **Config**: `vitest.config.ts` (TypeScript, globals, CSS mock)

### Escribir Tests

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MiComponente from './MiComponente';

describe('MiComponente', () => {
  it('se renderiza correctamente', () => {
    render(<MiComponente />);
    expect(screen.getByText('Hola')).toBeDefined();
  });
});
```

## Buenas Prácticas

- Escribí tests para lógica no trivial (branches, loops, parsers, paths de seguridad)
- Las líneas individuales generalmente no necesitan tests (YAGNI aplica también a tests)
- Usá nombres de test descriptivos que expliquen el comportamiento esperado
- Hacé que los tests sean deterministas — evitá llamadas de red en tests unitarios
