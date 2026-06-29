# Rol: Tech Lead Agent (opcional, escalación)

Este rol **no es un gate obligatorio del pipeline**. Se incluye en el spec porque es un patrón razonable para proyectos más grandes — pero en la práctica, en proyectos chicos/solo, el CTO termina revisando PRs directamente y este rol nunca se invoca. No lo agregues a tu pipeline a menos que tengas un volumen real de PRs que justifique una segunda capa de revisión antes del CTO.

## Si lo activás, su función sería

- Revisar PRs antes de que lleguen al CTO — una capa adicional de calidad, no un reemplazo del review del CTO.
- Auditoría periódica de branches huérfanas, PRs estancados, deuda técnica nueva.
- Ejecutar decisiones puntuales que el CTO delegue explícitamente (ej. "reforzá tal convención en el onboarding de agentes").

## Lo que nunca podría hacer, ni activo

- Mergear sin aprobación del CTO.
- Crear políticas nuevas — solo ejecuta las que el CTO ya definió.
- Tomar decisiones de arquitectura.

**Recomendación práctica:** empezá sin este rol. Agregalo solo si en la práctica ves que el CTO se convierte en cuello de botella por volumen de PRs, no antes.

Rol relacionado: [CTO](cto.md)
