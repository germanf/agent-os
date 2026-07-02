# Architectural Decisions

## 2026-06: SPA replaces Jinja2 templates

**Decisión:** El frontend se implementó como React SPA (Vite + TypeScript + Tailwind v4) en vez de Jinja2 templates como se había planeado originalmente en PLAN.md.

**Razón:** Mejor experiencia de desarrollo (HMR, TypeScript), separación clara de concerns, y el stack React/Vite es más mantenible para una UI con estado complejo como el chat.

**Impacto:** `dashboard/templates/` nunca se creó. El SPA catch-all vive en `main.py:936`.

## 2026-06: Chat via subprocess (no WebSocket persistente)

**Decisión:** Cada mensaje de chat spawna un proceso `claude -p` separado. La continuidad se maneja via `--session-id`/`--resume`.

**Razón:** El CLI `claude` no expone una API WebSocket. El modelo subprocess + SSE streaming permite reutilizar `runner.py` sin modificaciones.

**Impacto:** Cada mensaje es un proceso nuevo. Job retention de 1 hora / 200 jobs evita leak de memoria.

## 2026-06: HTTP Basic Auth (no OAuth2 proxy)

**Decisión:** Se implementó HTTP Basic Auth vía middleware de FastAPI en vez de usar nginx auth o un identity provider externo.

**Razón:** Simplicidad. El dashboard ya está restringido a la VPN WireGuard. `secrets.compare_digest()` para comparación timing-safe.

## 2026-06: Self-signed TLS (no Let's Encrypt)

**Decisión:** Certificado autofirmado de 10 años generado por `start.sh`.

**Razón:** El dashboard solo es accesible via VPN (IP privada 10.0.0.0/24). Let's Encrypt no funciona con RFC1918 IPs. HSTS header presente para futura integración con CA pública.

## 2026-06: Runner genérico (tool como string libre)

**Decisión:** `runner.create_job(tool, command, cwd)` no valida el string `tool`. Es libre.

**Razón:** Permitir agregar nuevos tools (chat, api, scraper, etc.) sin modificar `runner.py`.
