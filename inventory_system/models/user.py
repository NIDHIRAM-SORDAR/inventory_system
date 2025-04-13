from datetime import datetime, timezone
from typing import Optional

import reflex as rx
import structlog
from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapper
from sqlmodel import Field, Relationship

from inventory_system.logging import audit_logger


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def log_db_changes(mapper: Mapper, connection, target: rx.Model):
    """Log database changes for SQLModel instances."""
    state = inspect(target)  # Use sqlalchemy.orm.inspect
    action = None
    details = {}
    user_id = None  # Default to None, as auth context is unavailable

    # Try to infer user_id from target if possible
    if hasattr(target, "user_id"):
        user_id = target.user_id  # For UserInfo or Supplier with user_id

    if state.pending:  # INSERT
        action = f"create_{target.__tablename__}"
        details["new"] = {
            k: v for k, v in target.dict().items() if not k.startswith("_")
        }
    elif state.persistent:  # UPDATE or post-INSERT state
        action = f"update_{target.__tablename__}"
        changes = {}
        for attr in state.attrs:
            if attr.history.has_changes():
                changes[attr.key] = {
                    "old": attr.history.deleted[0] if attr.history.deleted else None,
                    "new": attr.value,
                }
        if changes:  # Only log if there are actual changes
            details["changes"] = changes
        else:
            return  # Skip logging empty updates
    elif state.deleted:  # DELETE
        action = f"delete_{target.__tablename__}"
        # Use the target instance directly to capture attributes before deletion
        details["deleted"] = {
            attr: getattr(target, attr)
            for attr in target.__table__.columns.keys()
            if not attr.startswith("_")
        }

    if action:
        audit_logger.info(
            action,
            user_id=user_id,
            entity_type=target.__tablename__,
            entity_id=target.id,
            details=details,
        )


class UserInfo(rx.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    is_admin: bool = False
    is_supplier: bool = False
    user_id: int = Field(foreign_key="localuser.id")
    profile_picture: str | None = None
    supplier: Optional["Supplier"] = Relationship(
        back_populates="user_info", cascade_delete=True
    )
    role: str = "employee"

    def set_role(self):
        if self.is_admin:
            self.role = "admin"
        elif self.is_supplier:
            self.role = "supplier"
        else:
            self.role = "employee"


class Supplier(rx.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str
    description: str
    contact_email: str = Field(unique=True, index=True)
    contact_phone: str
    status: str = Field(default="pending")
    user_info_id: Optional[int] = Field(
        default=None, foreign_key="userinfo.id", nullable=True, ondelete="CASCADE"
    )
    user_info: Optional[UserInfo] = Relationship(
        back_populates="supplier",
    )
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self):
        self.updated_at = get_utc_now()


def attach_event_listeners(model):
    """Attach event listeners to a model."""
    event.listen(model, "after_insert", log_db_changes)
    event.listen(model, "after_update", log_db_changes)
    event.listen(model, "before_delete", log_db_changes)


# Attach event listeners to models
attach_event_listeners(UserInfo)
attach_event_listeners(Supplier)
