import logging
import os

from .config import load_env


def configure_logging() -> None:
    """Configure application logging.

    Reads the desired log level from the ``LOG_LEVEL`` environment variable
    when invoked so environment changes take effect without restarting.
    """

    load_env()
    level = os.getenv("LOG_LEVEL", "INFO")
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
