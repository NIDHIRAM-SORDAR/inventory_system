import os
import sys
import json
from loguru import logger

from inventory_system.constants import LOG_DIR


def ensure_log_file_exists(log_path: str):
    """Ensure the log file and its directories exist."""
    try:
        os.makedirs(os.path.dirname(log_path), mode=0o755, exist_ok=True)
        if not os.path.exists(log_path):
            with open(log_path, "w") as f:
                pass
    except (OSError, PermissionError) as e:
        print(f"Failed to create log file {log_path}: {e}")
        raise


def filter_unwanted_messages(record):
    """Filter out log messages containing '1 change detected'."""
    return "1 change detected" not in record["message"]


def json_formatter(record):
    """Custom JSON formatter for log records."""
    log_entry = {
        "time": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "file": record["file"].path,
        "line": record["line"],
        "function": record["function"],
        "event": record["extra"].get("event", record["message"]),
        "extra": {k: v for k, v in record["extra"].items() if k != "event"},
    }
    return json.dumps(log_entry) + "\n"


def setup_loguru():
    """Set up Loguru logging."""
    # Ensure log file exists
    ensure_log_file_exists(LOG_DIR)

    # Remove default handler
    logger.remove()

    # Add file handler
    logger.add(
        LOG_DIR,
        level="INFO",
        filter=filter_unwanted_messages,
        format=json_formatter,  # Use callable directly
        catch=True,  # Catch handler errors
        encoding="utf-8",
    )

    # Add console handler
    logger.add(
        sys.stderr,
        level="INFO",
        filter=filter_unwanted_messages,
        format=json_formatter,
        catch=True,
    )


# Export audit logger
audit_logger = logger.bind()