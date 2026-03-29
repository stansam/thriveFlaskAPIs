import sys
import logging
from app.core.config import BaseConfig


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def _configure_logging(config: BaseConfig) -> None:
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    if config.LOG_FORMAT == "json":
        try:
            from pythonjsonlogger.json import JsonFormatter  # type: ignore

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                JsonFormatter(
                    "%(asctime)s %(name)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%SZ",
                )
            )
        except ImportError:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
            )
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(name)-30s %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()
    root.addHandler(handler)

    for noisy in ("werkzeug", "sqlalchemy.engine", "urllib3", "boto3", "botocore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if config.DATABASE_ECHO else logging.WARNING
    )
