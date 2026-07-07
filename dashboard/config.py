import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
_vault = os.environ.get("VAULT_DIR")
VAULT_DIR = Path(_vault) if _vault else None

# ── Alerting ───────────────────────────────────────────────────────────────
ALERT_WEBHOOK_URL: str | None = os.environ.get("ALERT_WEBHOOK_URL")
ALERT_HEALTH_DEGRADED_INTERVAL: int = int(os.environ.get("ALERT_HEALTH_DEGRADED_INTERVAL", "300"))
