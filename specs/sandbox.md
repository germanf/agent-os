# Convención: sandboxes aislados por agente

Cuando varios agentes de implementación corren en paralelo sobre el mismo repo, necesitan aislarse entre sí para no pisarse archivos, puertos, ni estado. Dos mecanismos complementarios, no mutuamente excluyentes:

## 1. Git worktree por agente

Cada agente trabaja en su propio `git worktree` (rama propia, directorio propio), no en el checkout principal. Esto evita que dos agentes corriendo a la vez se interfieran con `git checkout`/commits del otro.

**Riesgo conocido a verificar, no asumir:** algunos mecanismos de "worktree aislado" no garantizan de forma confiable que el agente nunca termine operando sobre el directorio principal compartido. Después de que un agente con aislamiento termina, conviene confirmar con `git worktree list` y `git status` en el directorio principal que efectivamente quedó intacto — no asumirlo por el solo hecho de haber pedido aislamiento.

**Orden de limpieza importa:** si además hay un container (sección 2) con bind-mount al worktree, hay que bajar el container *antes* de borrar el worktree — si el worktree desaparece primero, el container puede quedar con procesos colgados apuntando a un directorio que ya no existe.

## 2. Containers Docker por rol, con rangos de puerto fijos

Si el proyecto lo soporta, cada rol corre en su propio container con su propio rango de puertos — evita colisión cuando hay varios agentes activos al mismo tiempo. Ejemplo de convención (los números son ilustrativos, no hay nada especial en ellos — elegí los que tengan sentido para tu setup):

| Rol | Rango de puertos (ejemplo) | Acceso a datos |
|---|---|---|
| Full Stack Developer | 8800-8849 | Read-write código, credenciales mockeadas |
| QA/Tester | 8850-8899 | Read-only, snapshot de datos (no producción real) |
| UX/UI Designer | 8900-8949 | Read-write frontend, read-only backend |

**Credenciales:** siempre mockeadas dentro del sandbox — nunca credenciales ni datos reales de producción, ni siquiera de solo lectura. El aislamiento de red/puertos no sustituye al aislamiento de datos.

## Cuándo no hace falta esto

Si trabajás con un solo agente a la vez (sin paralelismo real), el worktree por sí solo alcanza para mantener el historial de git limpio — el container Docker es para cuando hay colisión real de puertos/procesos por correr varias cosas a la vez, no un requisito universal.

Rol relacionado: [Full Stack Developer](roles/fullstack-developer.md) · [QA/Tester](roles/qa-tester.md)
