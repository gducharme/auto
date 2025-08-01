import logging
import os
import sys

from .config import load_env


def configure_logging() -> None:
    """Configure application logging.

    Reads the desired log level from the ``LOG_LEVEL`` environment variable
    when invoked so environment changes take effect without restarting.
    """

    load_env()
    level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
        force=True,
    )
