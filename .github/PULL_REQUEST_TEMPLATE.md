## Description

<!-- Brief description of the change. What does this do and why? -->

Related to #<!-- issue number -->

## Pre-merge Checklist

### Validation
- [ ] `ruff check dashboard/` passes
- [ ] `python3 -m py_compile dashboard/main.py` passes
- [ ] `pnpm run build` passes
- [ ] `pnpm run test` passes
- [ ] `bash scripts/validate-workflow.sh` passes (checks all of the above)

### Conventions
- [ ] Branch follows naming: `feature/<name>` or `fix/<name>`
- [ ] PR targets `dev` (not `main`)
- [ ] Issue referenced as `Related to #N` (not `Closes #N`)
- [ ] One issue, one branch, one PR

### Review Gates
- [ ] Tech Lead Code Review completed
- [ ] CTO Review completed
- [ ] Human approval obtained (when required)

### Documentation
- [ ] New features include bilingual docs (EN + ES) with identical structure
- [ ] Updated relevant spec files in `specs/` if behavior or roles changed
