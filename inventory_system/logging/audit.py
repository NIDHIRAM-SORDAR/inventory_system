# inventory_system/logging/audit.py
import contextvars
from typing import Any, Dict, Optional

import reflex as rx
import reflex_local_auth
from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapper
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.audit import AuditTrail, OperationType

# Context variable to store current user info during operations
current_user_context = contextvars.ContextVar("current_user", default=None)


class CurrentUserInfo:
    """Container for current user information during audit operations."""

    def __init__(self, user_id: int, username: str):
        self.user_id = user_id
        self.username = username


def set_current_user_context(user_id: int, username: str):
    """Set the current user context for audit logging."""
    current_user_context.set(CurrentUserInfo(user_id, username))


def get_current_user_context() -> Optional[CurrentUserInfo]:
    """Get the current user context for audit logging."""
    return current_user_context.get()


def clear_current_user_context():
    """Clear the current user context."""
    current_user_context.set(None)


def get_username_by_user_id(user_id):
    """Helper function to fetch username from LocalUser by user_id."""
    if user_id is None:
        return None
    try:
        with rx.session() as session:
            user = session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.id == user_id
                )
            ).one_or_none()
            return user.username if user else None
    except Exception:
        return None


def get_user_info_for_audit(target):
    """Get user information for audit logging with fallback strategies."""
    # Strategy 1: Use current user context
    # (for operations initiated by authenticated users)
    current_user = get_current_user_context()
    if current_user:
        return current_user.user_id, current_user.username

    # Strategy 2: Check if target has user_id (for user-owned entities)
    if hasattr(target, "user_id") and target.user_id:
        username = get_username_by_user_id(target.user_id)
        return target.user_id, username

    # Strategy 3: For association tables, try to derive user from relationships
    if target.__tablename__ == "userrole":
        # Try to get username from the user_id in the association
        username = get_username_by_user_id(target.user_id)
        return target.user_id, username

    # Strategy 4: System operation (no specific user)
    return None, "system"


def get_entity_id(target):
    """Generate an entity_id for a model, handling association tables."""
    if hasattr(target, "id"):
        return target.id
    # Handle association tables like UserRole and RolePermission
    if target.__tablename__ == "userrole":
        return f"{target.user_id}-{target.role_id}"
    if target.__tablename__ == "rolepermission":
        return f"{target.role_id}-{target.permission_id}"
    return None  # Fallback for unexpected cases


def log_insert(mapper: Mapper, connection, target):
    """Log insertion of a new record."""
    user_id, username = get_user_info_for_audit(target)
    details = {
        "new": {k: v for k, v in target.__dict__.items() if not k.startswith("_")}
    }

    audit_logger.info(
        f"create_{target.__tablename__}",
        user_id=user_id,
        entity_type=target.__tablename__,
        entity_id=get_entity_id(target),
        username=username,
        details=details,
    )


def log_update(mapper: Mapper, connection, target):
    """Log updates to an existing record."""
    state = inspect(target)
    user_id, username = get_user_info_for_audit(target)
    changes = {}
    for attr in state.attrs:
        if attr.history.has_changes():
            changes[attr.key] = {
                "old": attr.history.deleted[0] if attr.history.deleted else None,
                "new": attr.value,
            }
    if not changes:
        return
    details = {"changes": changes}
    audit_logger.info(
        f"update_{target.__tablename__}",
        user_id=user_id,
        entity_type=target.__tablename__,
        entity_id=get_entity_id(target),
        username=username,
        details=details,
    )


def log_delete(mapper: Mapper, connection, target):
    """Log deletion of a record."""
    user_id, username = get_user_info_for_audit(target)
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
        entity_id=get_entity_id(target),
        username=username,
        details=details,
    )


def attach_audit_logging(model_class):
    """Attach audit logging to a SQLModel model class."""
    event.listen(model_class, "after_insert", log_insert)
    event.listen(model_class, "after_update", log_update)
    event.listen(model_class, "before_delete", log_delete)
    return model_class


def enable_audit_logging_for_models(*model_classes):
    """Enable audit logging for multiple model classes at once."""
    for model_class in model_classes:
        attach_audit_logging(model_class)


# Add this helper function
def create_audit_entry(
    operation_type: OperationType,
    operation_name: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    requires_approval: bool = False,
    **kwargs,
) -> AuditTrail:
    """Create and save an audit trail entry to the database."""

    # Get user context
    user_id, username = get_user_info_for_audit_context(kwargs.get("target"))

    # Create audit entry
    audit_entry = AuditTrail.create_audit_entry(
        operation_type=operation_type,
        operation_name=operation_name,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        username=username,
        changes=changes,
        metadata=metadata,
        success=success,
        error_message=error_message,
        requires_approval=requires_approval,
        **kwargs,
    )

    # Save to database
    try:
        with rx.session() as session:
            session.add(audit_entry)
            session.commit()
            session.refresh(audit_entry)
    except Exception as e:
        audit_logger.error(f"Failed to save audit entry: {str(e)}")

    return audit_entry


def get_user_info_for_audit_context(target=None):
    """Enhanced version that works with context or target."""
    # Strategy 1: Use current user context
    current_user = get_current_user_context()
    if current_user:
        return current_user.user_id, current_user.username

    # Strategy 2: Check if target has user_id (for user-owned entities)
    if target and hasattr(target, "user_id") and target.user_id:
        username = get_username_by_user_id(target.user_id)
        return target.user_id, username

    # Strategy 3: For association tables
    if target and hasattr(target, "__tablename__"):
        if target.__tablename__ == "userrole":
            username = get_username_by_user_id(target.user_id)
            return target.user_id, username

    # Strategy 4: System operation
    return None, "system"
