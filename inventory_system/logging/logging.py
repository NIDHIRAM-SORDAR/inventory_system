import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

from loguru import logger

from inventory_system.constants import LOG_DIR


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def get_log_file_path() -> str:
    """Generate the log file path with the current date."""
    log_dir_template = os.getenv("LOG_DIR", LOG_DIR)
    if "{time}" not in log_dir_template:
        logger.error(
            f"Invalid LOG_DIR format: '{log_dir_template}'. Expected '{time}' placeholder."  # noqa: E501
        )
        raise ValueError("LOG_DIR must contain '{time}' placeholder")
    try:
        return log_dir_template.format(time=datetime.now().strftime("%Y-%m-%d"))
    except ValueError as e:
        logger.error(
            f"Failed to format log file path with template '{log_dir_template}': {e}"
        )
        raise


def ensure_log_dir_exists() -> bool:
    """Ensure the log directory exists, recreating it if necessary."""
    log_dir = os.path.dirname(get_log_file_path())
    try:
        os.makedirs(log_dir, mode=0o755, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to create log directory {log_dir}: {e}")
        return False


def filter_unwanted_messages(record: Dict[str, Any]) -> bool:
    """Filter out log messages containing '1 change detected'."""
    return "1 change detected" not in record["message"]


def format_json_record(record: Dict[str, Any]) -> str:
    """Format the record as JSON for machine-readable output."""
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "extras": record["extra"],
        "file": record["file"].path,
        "line": record["line"],
    }
    return json.dumps(log_entry, cls=DateTimeEncoder)


def format_record(record: Dict[str, Any]) -> str:
    """Format the record into a readable message with context."""
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S")
    message = record["message"]
    log_parts = [f"[{timestamp}] {message}"]
    extras = record.get("extra", {})

    try:
        if "method" in extras and "url" in extras:
            http_context = []
            for field in [
                "method",
                "url",
                "status_code",
                "user_id",
                "ip_address",
                "username",
            ]:
                if field in extras and extras[field] is not None:
                    http_context.append(f"{field}={extras[field]}")
            if http_context:
                log_parts.append(" | " + " ".join(http_context))

        elif "entity_type" in extras and "entity_id" in extras:
            db_context = [
                f"entity={extras.get('entity_type')}",
                f"id={extras.get('entity_id')}",
                f"username={extras.get('username', 'unknown')}",
            ]
            if "user_id" in extras and extras["user_id"] is not None:
                db_context.append(f"user_id={extras['user_id']}")
            log_parts.append(" | " + " ".join(db_context))
            if "details" in extras:
                log_parts.append(
                    "\n" + json.dumps(extras["details"], indent=2, cls=DateTimeEncoder)
                )

        else:
            extra_fields = []
            for key, value in extras.items():
                if key != "formatted_message" and value is not None:
                    extra_fields.append(f"{key}={value}")
            if extra_fields:
                log_parts.append(" | " + " ".join(extra_fields))

    except Exception as e:
        log_parts.append(f" | formatting_error={str(e)}")

    return "".join(log_parts)


def patch_logger(record: Dict[str, Any]) -> None:
    """Add formatted message to record extras."""
    record["extra"]["formatted_message"] = format_record(record)


def setup_loguru():
    """Set up Loguru logging."""
    # Load configuration from environment variables
    log_config = {
        "level": os.getenv("LOG_LEVEL", "INFO").upper(),
        "format": os.getenv("LOG_FORMAT", "human").lower(),
        "rotation": os.getenv("LOG_ROTATION", "1 day"),
        "retention": os.getenv("LOG_RETENTION", "30 days"),
        "compression": os.getenv("LOG_COMPRESSION", "zip"),
    }

    file_format = (
        format_json_record
        if log_config["format"] == "json"
        else "{extra[formatted_message]}"
    )

    logger.remove()
    patched_logger = logger.patch(patch_logger)

    if ensure_log_dir_exists():
        patched_logger.add(
            get_log_file_path(),
            level=log_config["level"],
            filter=filter_unwanted_messages,
            format=file_format,
            catch=True,
            encoding="utf-8",
            rotation=log_config["rotation"],
            retention=log_config["retention"],
            compression=log_config["compression"],
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )
    else:
        patched_logger.warning(
            "Failed to set up file logging. Logs will only be sent to console."
        )

    patched_logger.add(
        sys.stderr,
        level=log_config["level"],
        filter=filter_unwanted_messages,
        format="{extra[formatted_message]}",
        catch=True,
        colorize=True,
    )

    return patched_logger


audit_logger = setup_loguru()
