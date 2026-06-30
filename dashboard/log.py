import sys
from pathlib import Path

from loguru import logger as _base_logger

LOG_DIR = Path(__file__).parent / "data" / "logs"


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _base_logger.remove()
    _base_logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
            " | <level>{level: <8}</level>"
            " | <cyan>{name}</cyan>:<cyan>{line: >4}</cyan>"
            " | <level>{message}</level>"
        ),
        level="DEBUG",
    )
    _base_logger.add(
        LOG_DIR / "dashboard_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{line} | {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
    )


logger = _base_logger
