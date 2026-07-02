# Deploy.yml Changes: Test Gates

> **⚠️ Plan no aplicado**
> Este documento describe cambios planeados para un workflow CI/CD (`.github/workflows/deploy.yml`)
> que nunca se implementó en el repo. El deploy actual es manual vía `dashboard/start.sh`
> en la VM de producción. Ver [`AGENTS.md`](../../AGENTS.md) para el flujo actual.

**Ubicación canónica:** `/home/ubuntu/Claude/docs/infrastructure/DEPLOY_YML_CHANGES.md`

**Propósito:** Documentación exacta de cambios a `.github/workflows/deploy.yml`

**Criticidad:** 🔴 CRÍTICA (unblocks deployment)

**Anteriormente en:** `.github/DEPLOY_YML_CHANGES.md` (movido para mejor organización)

---

## Cambios Requeridos

Aplicar los siguientes cambios a `.github/workflows/deploy.yml`:

### Ubicación: `jobs > deploy > steps`

Después del paso "Pull latest main", ANTES de "Rebuild and restart", agregar:

```yaml
- name: Frontend Validations
  run: |
    cd "${{ vars.DEPLOY_PATH }}/dashboard/frontend"
    pnpm install --frozen-lockfile
    pnpm run build
    echo "✓ Frontend build completed successfully"

- name: Backend Validations
  run: |
    cd "${{ vars.DEPLOY_PATH }}/dashboard"
    echo "Checking Python syntax..."
    python3 -m py_compile main.py runner.py chat_store.py
    python3 -m py_compile test_fastapi_minimal.py test_http_auth.py test_https_enforcement.py test_env_permissions.py
    echo "✓ All Python files have valid syntax"

    echo "Verifying imports..."
    python3 test_fastapi_minimal.py
    echo "✓ FastAPI app imports successfully"
```

### Concurrency Guard

En `jobs > deploy`, agregar:

```yaml
concurrency:
  group: deploy
```

---

## Justificación

| Change | Why | Impact |
|--------|-----|--------|
| **Frontend Validations** | Catch CSS/build errors early | ✅ Prevent broken UI |
| **Backend Validations** | Verify Python syntax + imports | ✅ Prevent crashes |
| **Concurrency Guard** | Prevent overlapping deploys | ✅ Avoid race conditions |

---

## Cómo Aplicar

### Opción A: GitHub UI (Recomendada)
1. GitHub → Código → `.github/workflows/deploy.yml`
2. Click ✏️ (Edit)
3. Copy código de arriba
4. Paste en la sección correcta
5. Commit

### Opción B: CLI con PAT Token
```bash
git checkout -b fix/deploy-test-gates
# Edit .github/workflows/deploy.yml
git add .github/workflows/deploy.yml
git commit -m "Fix: Add test gates to deploy pipeline"
git push -u origin fix/deploy-test-gates
# Create PR
```

---

## Verification

Después de aplicar:

```bash
# Validar sintaxis YAML
yamllint .github/workflows/deploy.yml

# Hacer un push de prueba a main
git push origin main
# Verificar que workflow ejecutó sin errores
```

---

*Nota: Ver también `HTTP_AUTH_CI_CD.md` y `WORKTREE_CLEANUP.md` para otros cambios necesarios a deploy.yml*
