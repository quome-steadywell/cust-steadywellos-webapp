import logging
import os
import json
from flask import request, g, has_request_context

# Configure logging levels based on environment
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json").lower()


class RequestFormatter(logging.Formatter):
    """Custom formatter that includes request information when available."""

    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.method = request.method
            record.remote_addr = request.remote_addr
            record.user_id = getattr(g, "user_id", None)
        else:
            record.url = None
            record.method = None
            record.remote_addr = None
            record.user_id = None

        return super().format(record)


class JsonFormatter(RequestFormatter):
    """Formatter that outputs JSON strings after formatting the record."""

    def format(self, record):
        super().format(record)

        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available
        if record.url:
            log_data.update(
                {
                    "url": record.url,
                    "method": record.method,
                    "remote_addr": record.remote_addr,
                    "user_id": record.user_id,
                }
            )

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(app):
    """Configure application logging to stdout/stderr only."""
    # Create logger
    logger = logging.getLogger("palliative_care")
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Clear existing handlers
    logger.handlers = []

    # Create console handler for stdout/stderr
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    # Set formatter based on configuration
    if LOG_FORMAT == "json":
        formatter = JsonFormatter()
    else:
        formatter = RequestFormatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    # Set as app logger
    app.logger = logger

    # Log a message about the logging configuration
    logger.info("Application logging configured to use stdout/stderr only")

    return logger


def get_logger():
    """Get the application logger."""
    return logging.getLogger("palliative_care")
