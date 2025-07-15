import logging
import os


def configure_logging() -> None:
    """Configure application logging.

    Reads the desired log level from the ``LOG_LEVEL`` environment variable
    when invoked so environment changes take effect without restarting.
    """

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

