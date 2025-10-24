from __future__ import annotations
import logging
import logging.config
from typing import Literal

from app.core.config import settings

# Simple, production-friendly console logging that plays nice with Uvicorn.
# No extra deps, but consistent formatting across app/uvicorn/access loggers.

def setup_logging(level: Literal["CRITICAL","ERROR","WARNING","INFO","DEBUG","NOTSET"]) -> None:
    lvl = (level or settings.LOG_LEVEL).upper()
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "access": {
                "format": '%(asctime)s %(levelname)s [%(name)s] %(message)s',
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "default": {"class": "logging.StreamHandler", "formatter": "standard"},
            "access": {"class": "logging.StreamHandler", "formatter": "access"},
        },
        "loggers": {
            "": {"handlers": ["default"], "level": lvl},
            "uvicorn": {"handlers": ["default"], "level": lvl, "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": lvl, "propagate": False},
            "uvicorn.access": {"handlers": ["access"], "level": lvl, "propagate": False},
            # sqlalchemy can be noisy; tune as needed
            "sqlalchemy.engine": {"handlers": ["default"], "level": "WARNING", "propagate": False},
        },
    }
    
    logging.config.dictConfig(config)
    logging.getLogger(__name__).info("Logging configured (level=%s)", lvl)
