# Rediseño del dashboard (puerto 80) — landing + 3 páginas nuevas

> **⚠️ Plan histórico — parcialmente implementado**
> Este documento describe el diseño original con Jinja2 templates.
> El frontend real se implementó como React SPA (Vite + TypeScript + Tailwind v4).
> Ver [`AGENTS.md`](AGENTS.md) para la arquitectura actual.

> Ver también [`AGENTS.md`](AGENTS.md) — especialmente la sección sobre qué recursos existen solo en la VM de producción y no en este sandbox.

## Contexto

Hoy `GET /` en `dashboard/main.py` sirve directamente `dashboard/static/index.html`, que es la UI de los dos scrapers (API v2 y Agentic/Playwright). El usuario quiere que la home deje de ser esa UI y pase a ser un **hub de navegación** hacia páginas secundarias:

1. **Scrapers** (la herramienta actual, sin cambios funcionales).
2. **Resumen** — vista condensada por categorías de los tweets/likes/bookmarks ya analizados en `dashboard/outputs/manual/organized/`, en vez de listar tuits sueltos.
3. **Notes** — navegador del vault de Obsidian (`~/vault/` en la VM de producción, no existe en el sandbox) con preview renderizado de Markdown (no texto plano), incluyendo wikilinks `[[...]]`.
4. **Chat** — una página para hablar con Claude que mantenga el mismo contexto/memoria que la sesión interactiva original (mismo `MEMORY.md` de Claude Code, mismo acceso al vault).

Ya se confirmó explorando el código existente (`main.py`, `runner.py`, `static/*`, `requirements.txt`, `nginx.conf`) que **no hace falta tocar nginx ni `runner.py`** — el job runner ya es genérico (`tool` es un string libre, sin validación de valores). El usuario también eligió explícitamente que el chat tenga **paridad total de herramientas** (mismo nivel que una sesión interactiva normal de Claude Code) en vez de modo solo-lectura — se acepta ese riesgo porque el dashboard ya está restringido a la VPN WireGuard (`allow 10.0.0.0/24; deny all;` en nginx).

## Arquitectura

```
GET /          → landing.html (4 tarjetas de navegación)
GET /scrapers  → static/index.html (sin cambios funcionales, solo 1 link de vuelta agregado)
GET /resumen   → resumen.html + resumen.js  (lee outputs/manual/organized/)
GET /notes     → notes.html + notes.js      (lee ~/vault/*.md en producción)
GET /chat      → chat.html + chat.js        (spawna `claude -p ...` vía runner.py en producción)
```

Se introduce **Jinja2** (`dashboard/templates/`) solo para compartir una barra de navegación entre `landing.html`, `resumen.html`, `notes.html` y `chat.html`. Todo el contenido dinámico se carga client-side con `fetch()`/SSE — Jinja no recibe datos de negocio, solo el nombre de página activa para resaltar el link en la nav.

`static/index.html`, `static/app.js` y todas las rutas `/api/credentials*`, `/auth/*`, `/api/jobs*`, `/api/run/*`, `/api/files*` quedan **intactas**.

## Cambios por archivo

### `dashboard/requirements.txt`
Agregar una línea: `jinja2>=3.1.0` (hoy no está instalado, `Jinja2Templates` falla al importar sin él).

### `dashboard/main.py`
- Import nuevo: `from fastapi.templating import Jinja2Templates`.
- Constantes nuevas junto a las existentes: `TEMPLATES_DIR = BASE_DIR / "templates"`, `MANUAL_DIR = OUTPUTS_DIR / "manual" / "organized"`, `VAULT_DIR = Path("/home/ubuntu/vault")` (no existe en el sandbox, solo en producción — el código debe manejar `FileNotFoundError`/directorio ausente con gracia, ej. devolviendo árbol vacío, para no romper en el sandbox).
- `ROOT_DIR` (ya existe, `= BASE_DIR.parent`) se reutiliza tal cual para el `cwd` del chat — en producción es el directorio cuya carpeta de memoria de Claude Code contiene el `MEMORY.md` de la sesión original.
- Después del mount de `/static`: `templates = Jinja2Templates(directory=TEMPLATES_DIR)`.
- Reemplazar el handler `@app.get("/")` para que renderice `templates.TemplateResponse(request, "landing.html", {"active": "home"})` en vez de devolver `index.html`.
- Agregar `@app.get("/scrapers")` que hace exactamente lo que hacía el `/` viejo: `return FileResponse(BASE_DIR / "static" / "index.html")`.
- Agregar 3 bloques de rutas nuevas (al final del archivo, después de `/api/files/{tool}/{filename}`): Resumen, Notes, Chat (detalle abajo).
- Pequeño helper para slugificar categorías (mismo criterio que `dashboard/outputs/manual/analyze.py`):
  ```python
  def _cat_slug(cat: str) -> str:
      return re.sub(r"[^a-zA-Z0-9]+", "_", cat).strip("_").lower()
  ```
  (agregar `import re` arriba).

### `dashboard/templates/base.html` (nuevo)
Layout compartido: `<head>` con `static/style.css`, una `<nav class="nav-bar">` con links a Inicio + las 4 secciones, marcando `.active` según la variable `active`, y `{% block content %}{% endblock %}` + `{% block scripts %}{% endblock %}`.

### `dashboard/templates/landing.html` (nuevo)
Extiende `base.html`. Grid de 4 tarjetas (reusa `.card`/`.grid-2` de `style.css`) con título + descripción corta + link a cada sección: Scrapers, Resumen, Notes, Chat.

### `dashboard/static/index.html` (1 línea agregada, sin tocar nada más)
Agregar un link `<a href="/">← Inicio</a>` cerca del header existente, para poder volver a la landing sin usar el botón "atrás" del navegador. Es el único cambio en este archivo.

### Página Resumen

**Backend (`main.py`):**
- `GET /api/resumen` → lee `MANUAL_DIR / "resumen.json"` y devuelve su contenido tal cual: por dataset (`tweets`/`likes`/`bookmarks`) trae `count`, `date_range`, `categories`, `top_accounts`, `media_breakdown`, `engagement`, `top_by_engagement`.
- `GET /api/resumen/{dataset}/{category}` → valida `dataset in {"tweets","likes","bookmarks"}`, slugifica `category` con `_cat_slug`, lee `MANUAL_DIR / dataset / f"{slug}.json"` (ya viene ordenado por fecha desc), devuelve los primeros N (ej. 20) registros para una vista expandible — nunca el feed completo.

**Frontend:** `templates/resumen.html` + `static/resumen.js`.
- 3 tabs (reusa el patrón `.tabs/.tab-btn/.tab-panel` ya existente en `style.css`/`app.js`): Tweets / Likes / Bookmarks.
- Por tab: encabezado con stats globales (rango de fechas, totales, % retweets/quotes/replies, breakdown de media, engagement total) usando `.grid-3` de tarjetas pequeñas.
- Debajo, una tarjeta por categoría (`.card`, grid) con: nombre, cantidad, % del total, top 3 cuentas de esa categoría. Un botón "Ver ejemplos" hace `fetch` a `/api/resumen/{dataset}/{cat}` y expande (`<details>`) una lista compacta (texto recortado + likes/RTs/views) — así se cumple "condensado y ordenado, ya no como tuits sueltos": por defecto solo se ven números agregados, el detalle es opt-in.
- Los datos reales (`dashboard/outputs/manual/organized/`) **sí están incluidos en este repo**, así que esta página es totalmente verificable en el sandbox.

### Página Notes (vault de Obsidian)

**Backend (`main.py`):**
- `GET /api/notes/tree` → recorre `VAULT_DIR.rglob("*.md")`, devuelve un árbol anidado `{name, path (relativo a VAULT_DIR), type: "dir"|"file", children: [...]}`. Si `VAULT_DIR` no existe (caso sandbox), devolver `[]` en vez de fallar.
- `GET /api/notes/content?path=...` → validación estricta antes de leer:
  ```python
  rel = Path(path)
  if rel.is_absolute() or ".." in rel.parts or rel.suffix != ".md":
      raise HTTPException(400, "Ruta inválida")
  full = (VAULT_DIR / rel).resolve()
  if not full.is_relative_to(VAULT_DIR.resolve()) or not full.exists():
      raise HTTPException(404, "Nota no encontrada")
  return {"path": path, "content": full.read_text()}
  ```
  Esto bloquea `..`, paths absolutos, y cualquier sufijo que no sea `.md`.

**Frontend:** `templates/notes.html` + `static/notes.js` + `static/vendor/marked.min.js` (vendorizar una sola vez desde `cdn.jsdelivr.net`, para no depender de la CDN en runtime).
- Layout de 2 columnas: sidebar con el árbol (`.file-list/.file-item`, reusando clases existentes) + panel principal.
- Al hacer click en una nota: `fetch` del contenido crudo, preprocesar wikilinks con regex `/\[\[([^\]|]+)(\|([^\]]+))?\]\]/g` → reemplazar por `<a class="wikilink" data-target="...">texto</a>`, luego pasar el resultado por `marked.parse()` para obtener HTML real (headers, listas, tablas, etc. — no markdown plano).
- Click en un `.wikilink` resuelve el target contra el árbol ya cargado: primero por path exacto, si no existe por nombre de archivo (basename) — porque el vault real mezcla wikilinks con y sin carpeta.
- **No verificable end-to-end en el sandbox** (no hay vault): verificar acá solo que el endpoint maneja con gracia la ausencia de `VAULT_DIR` y que el path-traversal se bloquea correctamente con un directorio de prueba ficticio si hace falta.

### Página Chat

**Backend (`main.py`)** — reutiliza `runner.py` **sin modificarlo** (ya es genérico: `create_job(tool, command, cwd)`):
```python
class ChatRequest(BaseModel):
    session_id: str
    message: str
    first: bool = False

@app.post("/api/chat/send")
async def chat_send(req: ChatRequest, bg: BackgroundTasks):
    cmd = [
        "claude", "-p", req.message,
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--permission-mode", "bypassPermissions",
        "--add-dir", str(VAULT_DIR),
    ]
    cmd += ["--session-id", req.session_id] if req.first else ["--resume", req.session_id]
    job = create_job("chat", cmd, cwd=str(ROOT_DIR))
    bg.add_task(run_job, job)
    return {"job_id": job.id}
```
- `cwd=str(ROOT_DIR)` es, en producción, exactamente el directorio cuya carpeta de proyecto de Claude Code contiene el `MEMORY.md` de la sesión original — así el chat lee la misma memoria.
- `--add-dir /home/ubuntu/vault` replica el acceso adicional que tiene la sesión original, para que el chat pueda leer/escribir notas del vault igual que ella.
- `--permission-mode bypassPermissions` implementa la paridad total de herramientas que el usuario eligió explícitamente (sin esto, cada uso de Bash/Edit/Write quedaría bloqueado esperando una confirmación interactiva que no existe en modo `-p`).
- Cada mensaje es un proceso `claude -p` nuevo; la continuidad de la conversación la da `--session-id` (primer mensaje) / `--resume` (siguientes), no un proceso persistente.
- **No verificable end-to-end en el sandbox** (no hay CLI `claude` autenticado ahí): verificar acá solo que el endpoint construye el comando correctamente (test unitario sobre la función que arma `cmd`, sin ejecutar `claude` de verdad).

**Frontend:** `templates/chat.html` + `static/chat.js`.
- Al cargar la página: `session_id = crypto.randomUUID()`, `first = true`.
- Al enviar: `POST /api/chat/send` → recibe `job_id` → abre `EventSource("/api/jobs/{job_id}/stream")` (endpoint ya existente, sin cambios) → parsea cada línea como JSON `stream-json` (eventos `system`/`assistant`/`user`/`result`) y renderiza:
  - texto del asistente → burbuja `.chat-bubble.assistant` (se va completando con los deltas).
  - bloques `tool_use` → `<details class="tool-call">` colapsable mostrando la herramienta y el input.
  - bloques `tool_result` → contenido dentro del mismo `<details>`, truncado si es muy largo.
  - evento `result` final → marca el turno como completo, vuelve a habilitar el input, pone `first = false`.
- Mensajes del usuario → burbuja `.chat-bubble.user`, agregada al instante (no espera al server).

### `dashboard/static/style.css` (solo agregar clases nuevas al final, nada existente se modifica)
`.nav-bar`, `.nav-link`, `.nav-link.active`, `.landing-grid` (alias de `.grid-2`), `.wikilink`, `.note-layout` (sidebar + panel), `.chat-layout`, `.chat-bubble`, `.chat-bubble.user`, `.chat-bubble.assistant`, `.tool-call`, `.chat-input-bar`. Reusar variables existentes (`--bg`, `--surface`, `--accent`, `--border`, `--radius`, etc.) para mantener el mismo tema oscuro.

## Verificación

### En el sandbox cloud (disponible ahora)
1. `python3 -m py_compile dashboard/main.py` y demás archivos `.py` tocados — sin errores de sintaxis.
2. Instanciar la app (`from main import app`) y confirmar que las rutas nuevas quedan registradas en `app.routes` (`/`, `/scrapers`, `/resumen`, `/notes`, `/chat`, `/api/resumen`, `/api/resumen/{dataset}/{category}`, `/api/notes/tree`, `/api/notes/content`, `/api/chat/send`).
3. Tests unitarios o llamadas directas (con `TestClient` de FastAPI) a `/api/resumen` y `/api/resumen/{dataset}/{category}` contra los datos reales en `dashboard/outputs/manual/organized/` (sí están en el repo) — confirmar que devuelven JSON con la forma esperada y que nunca devuelven el feed completo sin paginar.
4. `/api/notes/tree` y `/api/notes/content` con un directorio de prueba temporal (no el vault real, que no existe acá) — confirmar manejo de directorio ausente y que el path-traversal (`../../etc/passwd`, paths absolutos, sufijo distinto de `.md`) se bloquea con 400/404.
5. Para `/api/chat/send`: testear solamente la construcción del comando (lista de argumentos) sin ejecutar `claude` realmente.

### Solo en la VM de producción (después del merge — requiere recursos que no existen en el sandbox)
6. `./start.sh` reinicia uvicorn/nginx sin errores; `systemctl status nginx` y `ss -tlnp sport = :8765` siguen OK.
7. `curl http://127.0.0.1:8765/` devuelve la landing con 4 links; `curl .../scrapers` devuelve el HTML del scraper (con el link nuevo) y la UI de scrapers sigue funcionando end-to-end (lanzar un job real).
8. Abrir `/resumen` en el browser, confirmar que se ven tarjetas por categoría con números (no una lista larga de tuits), y que "Ver ejemplos" expande correctamente.
9. Abrir `/notes`, abrir una nota real con wikilinks, confirmar que se renderiza como HTML real y que la navegación por wikilink funciona.
10. Abrir `/chat`, enviar un primer mensaje y confirmar streaming; enviar un segundo mensaje que dependa del primero para confirmar que `--resume` mantiene contexto; preguntar algo que requiera leer el vault o la memoria para confirmar paridad de contexto; pedir una acción que dispare una tool real para confirmar que `bypassPermissions` no cuelga y que el bloque de tool-call se renderiza colapsable.
