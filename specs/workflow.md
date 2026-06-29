# Workflow: el pipeline de desarrollo

Issue → Plan → Dev (rama + PR) → CTO review → **aprobación del usuario** → CTO merge → QA → cierre.

Este es el único pipeline — no debería haber una segunda versión circulando en paralelo. Si lo modificás, actualizá este archivo en el mismo cambio; un pipeline "real" que vive solo en la memoria de los agentes y no en un doc versionado termina divergiendo de lo que en verdad se hace.

## 0. Issue + Plan (antes de escribir código)

- Cada bug/feature tiene un issue. Etiquetas de categoría obligatorias y permanentes (nunca se borran): `bug`, `feature`, `security`, `documentation` — podés agregar más, pero estas cuatro no deberían faltar nunca en ningún issue.
- El CTO comenta en el issue un plan breve antes de delegar: root cause (si es bug), archivos a tocar, constraints técnicos. Esto no es burocracia — es lo que evita que el implementador rediseñe sobre la marcha y se desvíe del alcance.
- Convención de nombres de rama: `fix/nombre-corto` para bugs, `feature/nombre-corto` para features.

## 1. Dev (Full Stack Developer Agent)

- Rama desde la rama principal, siguiendo el plan del paso 0.
- Implementa, valida localmente (build/tests, o el entorno de sandbox si el proyecto tiene uno — ver [sandbox.md](sandbox.md)).
- Pushea la rama y **abre el PR** — el implementador escribe la descripción porque tiene el contexto completo del diff. El PR no cierra el issue todavía (`Refs #N`, no `Closes #N`) — el cierre lo hace QA después de validar, no el merge.

## 2. CTO (Code Review)

- Revisa correctness, seguridad, estilo.
- Si hay comentarios, el Dev los resuelve y el CTO revisa de nuevo — un PR con comentarios sin resolver no se mergea, sin excepciones de "mergeamos y arreglamos después".
- Si está OK, pasa al paso 2.5 — **el CTO no mergea todavía**, aunque ya lo haya aprobado técnicamente.

## 2.5. Aprobación del usuario — el gate que no se salta

Este es el paso con más consecuencia de todo el pipeline, y es deliberadamente manual.

**Por qué existe pese a que el CTO ya tiene autoridad técnica total:** la autoridad del CTO cubre decisiones técnicas — arquitectura, cómo se implementa algo. No reemplaza al usuario como gate de qué llega a producción. Son ejes distintos: uno es "¿está bien construido?", el otro es "¿quiero que esto exista en el mundo, ahora, así?" — y el segundo es una decisión que el usuario nunca delegó, ni siquiera cuando delega todo lo técnico.

El costo de pedir esta aprobación es bajo (un mensaje, una respuesta). El costo de mergear sin ella, si el usuario no lo quería, no es reversible de la misma forma — el código ya corrió, ya se desplegó, ya tuvo efecto. Esa asimetría es la razón de fondo del gate, no burocracia por la burocracia.

**Cómo se salta, si alguna vez corresponde:** solo con instrucción explícita y específica del usuario — "mergeá esto sin preguntarme" en ese momento puntual, o una autorización duradera tipo "mergeá lo que vos apruebes, no me consultes cada vez" dicha de forma clara. Una frase ambigua de alcance general ("encargate de todo", "manejate vos") **no** cuenta como esa autorización — si hay ambigüedad real sobre si el usuario quiso decir esto, se pregunta, no se asume.

## 3. CTO Merge

Una vez aprobado por el usuario: el CTO mergea, y si el proyecto usa labels de estado, marca el issue como listo para QA (ej. `ready-to-test`).

## 4. QA/Tester

Ejecuta el test plan del issue contra el código ya mergeado, con evidencia real (ver [qa-tester.md](roles/qa-tester.md)). Si pasa, cierra el issue. Si falla, lo reabre con el detalle del fallo — el ciclo vuelve al paso 1, no se cierra un issue que no pasó su propio test plan.

## Excepciones

Todo el pipeline (incluido el paso 2.5) aplica siempre, salvo instrucción explícita del usuario en sentido contrario para ese caso puntual ("pusheá directo a la rama principal", "no hagas PR", "saltá el plan"). Sin esa instrucción, el flujo completo es la regla, no la excepción.

Roles involucrados: [CTO](roles/cto.md) · [Full Stack Developer](roles/fullstack-developer.md) · [QA/Tester](roles/qa-tester.md) · [UX/UI Designer](roles/ux-ui-designer.md) (consultivo, no bloqueante) · [Tech Lead](roles/tech-lead.md) (opcional, no wireado por default)
