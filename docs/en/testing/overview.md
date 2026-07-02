# Testing

## Backend Testing

Test scripts are in `dashboard/tests/` and `tests/`:

```bash
# Syntax check
python3 -m py_compile dashboard/main.py

# Lint
ruff check dashboard/

# Run tests
python3 -m pytest dashboard/tests/
python3 -m pytest tests/
```

Backend tests cover:
- **Startup**: FastAPI app import and startup sequence
- **Authentication**: HTTP Basic Auth enforcement
- **HTTPS**: Redirect enforcement
- **Environment**: Permissions and configuration
- **Regression**: Issue-specific test cases

## Frontend Testing

Tests use **Vitest** + **@testing-library/react**:

```bash
cd dashboard/frontend

# Run tests
pnpm run test

# With coverage
pnpm run test:coverage
```

Test files are co-located with source files:
- `src/lib/__tests__/sanitize.test.ts` — XSS sanitization
- `src/lib/useToolJob.test.ts` — Job lifecycle hook
- `src/pages/Chat.test.tsx` — Chat page rendering

### Test Setup

- **Framework**: vitest
- **DOM**: jsdom
- **Matchers**: @testing-library/jest-dom
- **Config**: `vitest.config.ts` (TypeScript, globals, CSS mock)

### Writing Tests

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeDefined();
  });
});
```

## Best Practices

- Write tests for non-trivial logic (branches, loops, parsers, security paths)
- One-liners generally don't need tests (YAGNI applies to tests too)
- Use descriptive test names that explain the expected behavior
- Make tests deterministic — avoid network calls in unit tests
