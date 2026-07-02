import json
from pathlib import Path

from loguru import logger

CONFIG_PATH = Path(__file__).parent.parent / "opencode.json"
PONYTAIL_PLUGIN = "@dietrichgebert/ponytail"


def get_status() -> dict:
    config_found = CONFIG_PATH.exists()
    ponytail_configured = False
    plugins: list[str] = []

    if config_found:
        try:
            data = json.loads(CONFIG_PATH.read_text())
            raw = data.get("plugin", [])
            plugins = raw if isinstance(raw, list) else []
            ponytail_configured = PONYTAIL_PLUGIN in plugins
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read opencode.json: {}", exc)

    return {
        "configured": ponytail_configured,
        "plugin": PONYTAIL_PLUGIN,
        "plugins_count": len(plugins),
        "config_path": str(CONFIG_PATH),
    }


def get_metrics() -> dict:
    return {
        "tokens_before": None,
        "tokens_after": None,
        "loc_before": None,
        "loc_after": None,
        "note": "Metrics collection not yet implemented — requires Ponytail analytics endpoint",
    }
