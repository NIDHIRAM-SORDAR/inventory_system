"""
Audit logging module for SQLModel/SQLAlchemy models.
Provides functions to automatically log database operations.
"""

from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapper

from inventory_system.logging.logging import audit_logger


def log_insert(mapper: Mapper, connection, target):
    """Log insertion of a new record."""
    user_id = getattr(target, "user_id", None)

    details = {"new": {k: v for k, v in target.dict().items() if not k.startswith("_")}}

    audit_logger.info(
        f"create_{target.__tablename__}",
        user_id=user_id,
        entity_type=target.__tablename__,
        entity_id=target.id,
        details=details,
    )


def log_update(mapper: Mapper, connection, target):
    """Log updates to an existing record."""
    state = inspect(target)
    user_id = getattr(target, "user_id", None)

    changes = {}
    for attr in state.attrs:
        if attr.history.has_changes():
            changes[attr.key] = {
                "old": attr.history.deleted[0] if attr.history.deleted else None,
                "new": attr.value,
            }

    # Only log if there are actual changes
    if not changes:
        return

    details = {"changes": changes}

    audit_logger.info(
        f"update_{target.__tablename__}",
        user_id=user_id,
        entity_type=target.__tablename__,
        entity_id=target.id,
        details=details,
    )


def log_delete(mapper: Mapper, connection, target):
    """Log deletion of a record."""
    user_id = getattr(target, "user_id", None)

    details = {
        "deleted": {
            attr: getattr(target, attr)
            for attr in target.__table__.columns.keys()
            if not attr.startswith("_")
        }
    }

    audit_logger.info(
        f"delete_{target.__tablename__}",
        user_id=user_id,
        entity_type=target.__tablename__,
        entity_id=target.id,
        details=details,
    )


def attach_audit_logging(model_class):
    """
    Attach audit logging to a SQLModel model class.

    Example usage:
        from inventory_system.audit import attach_audit_logging

        class MyModel(rx.Model, table=True):
            # model definition...

        attach_audit_logging(MyModel)
    """
    event.listen(model_class, "after_insert", log_insert)
    event.listen(model_class, "after_update", log_update)
    event.listen(model_class, "before_delete", log_delete)
    return model_class


def enable_audit_logging_for_models(*model_classes):
    """
    Enable audit logging for multiple model classes at once.

    Example usage:
        from inventory_system.audit import enable_audit_logging_for_models

        enable_audit_logging_for_models(User, Order, Product)
    """
    for model_class in model_classes:
        attach_audit_logging(model_class)
