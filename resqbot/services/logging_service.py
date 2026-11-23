"""Application logging configuration."""
import logging
from pathlib import Path

def configure_logging():
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        filename="logs/resqbot.log",
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        encoding="utf-8",
    )
    return logging.getLogger("resqbot")
