import json
import os
import sys
from datetime import datetime

from loguru import logger

from inventory_system.constants import LOG_DIR


# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def ensure_log_dir_exists():
    """Ensure the log directory exists, recreating it if necessary."""
    log_dir = os.path.dirname(LOG_DIR.format(time=datetime.now()))
    try:
        os.makedirs(log_dir, mode=0o755, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        print(f"Failed to create log directory {log_dir}: {e}")
        return False


def filter_unwanted_messages(record):
    """Filter out log messages containing '1 change detected'."""
    return "1 change detected" not in record["message"]


def format_record(record):
    """Format the record into a readable message with context."""
    # Format the timestamp
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S")

    # Get the log message
    message = record["message"]

    # Start building the formatted log
    log_parts = [f"[{timestamp}] {message}"]

    # Add context based on the type of log
    extras = record["extra"]

    if "method" in extras and "url" in extras:
        # HTTP request/response logs
        http_context = []
        for field in ["method", "url", "status_code", "user_id", "ip_address"]:
            if field in extras and extras[field] is not None:
                http_context.append(f"{field}={extras[field]}")

        if http_context:
            log_parts.append(" | " + " ".join(http_context))

    elif "entity_type" in extras and "entity_id" in extras:
        # Database operation logs
        db_context = [
            f"entity={extras['entity_type']}",
            f"id={extras['entity_id']}",
        ]

        if "user_id" in extras and extras["user_id"] is not None:
            db_context.append(f"user_id={extras['user_id']}")

        log_parts.append(" | " + " ".join(db_context))

        # Add operation details if present
        if "details" in extras:
            details = extras["details"]
            # Use custom encoder for datetime objects
            log_parts.append("\n" + json.dumps(details, indent=2, cls=DateTimeEncoder))

    # For other types of logs, add any non-None extra fields
    else:
        extra_fields = []
        for key, value in extras.items():
            if key != "formatted_message" and value is not None:
                extra_fields.append(f"{key}={value}")

        if extra_fields:
            log_parts.append(" | " + " ".join(extra_fields))

    # Return the formatted message
    return "".join(log_parts)


def patch_logger(record):
    """Add formatted message to record extras."""
    record["extra"]["formatted_message"] = format_record(record)


def setup_loguru():
    """Set up Loguru logging."""
    # Remove default handler
    logger.remove()

    # Patch the logger with our formatter
    patched_logger = logger.patch(patch_logger)

    # Ensure log directory exists before adding file handler
    if ensure_log_dir_exists():
        # Add file handler with daily rotation
        patched_logger.add(
            LOG_DIR,
            level="INFO",
            filter=filter_unwanted_messages,
            format="{extra[formatted_message]}",
            catch=True,
            encoding="utf-8",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
            enqueue=True,  # Use a queue to avoid blocking
        )
    else:
        # Log a warning to console if we can't set up file logging
        patched_logger.warning(
            "Failed to set up file logging. Logs will only be sent to console."
        )

    # Add console handler - always works even if file logging fails
    patched_logger.add(
        sys.stderr,
        level="INFO",
        filter=filter_unwanted_messages,
        format="{extra[formatted_message]}",
        catch=True,
        colorize=True,
    )

    return patched_logger


# Set up and export the audit logger
audit_logger = setup_loguru()
