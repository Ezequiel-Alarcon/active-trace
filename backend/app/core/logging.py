import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return _json_dumps(log_data)


def _json_dumps(data: dict) -> str:
    import json

    return json.dumps(data, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    # Suppress per-request access logs (noisy) but keep uvicorn.error at INFO
    # so that operational messages like "Application startup complete." are visible.
    # Setting uvicorn or uvicorn.error to WARNING silences startup/shutdown
    # confirmation messages and makes the app appear to hang on startup.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
