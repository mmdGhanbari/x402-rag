import logging

import colorlog

from x402_rag.core import Settings


def setup_logging(settings: Settings):
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s[%(levelname)s]%(reset)s  %(asctime)s - %(name)s - %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        handlers=[handler],
    )

    app_log_level = getattr(logging, settings.app_log_level.upper())
    logging.getLogger("x402_rag").setLevel(app_log_level)
