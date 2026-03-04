import logging
import logging.config
import sys
from contextvars import ContextVar
from typing import Optional

# Context variables for correlation
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
task_id_ctx: ContextVar[Optional[str]] = ContextVar("task_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        # Add context variables to the record
        record.request_id = request_id_ctx.get() or "-"
        record.task_id = task_id_ctx.get() or "-"
        record.user_id = user_id_ctx.get() or "-"
        return super().format(record)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "()": StructuredFormatter,
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | [REQ:%(request_id)s] [TASK:%(task_id)s] [USER:%(user_id)s] | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger("app")
    logger.info("Logging initialized with structured formatting")
    return logger
