from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import reflex as rx
from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field


def get_utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class OperationType(str, Enum):
    """Enumeration of audit operation types."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ROLE_CHANGE = "role_change"
    PERMISSION_CHANGE = "permission_change"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    """Enumeration of approval statuses."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditTrail(rx.Model, table=True):
    """Enhanced audit trail model for comprehensive logging and approval workflows.

    This model captures detailed information about all system operations,
    supporting both immediate logging and future approval workflow requirements.
    Compatible with SQLite (development) and PostgreSQL (production).
    """

    __tablename__ = "audittrail"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=get_utc_now, index=True)

    # User context
    user_id: Optional[int] = Field(default=None, index=True)
    username: str = Field(default="system", index=True, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 compatible

    # Operation context
    operation_type: OperationType = Field(index=True)
    operation_name: str = Field(index=True, max_length=255)

    # Entity context
    entity_type: str = Field(index=True, max_length=100)
    entity_id: Optional[str] = Field(default=None, index=True, max_length=255)

    # Change details - Always use Text for SQLite compatibility
    changes: Dict[str, Any] = Field(sa_column=Column(JSONB), default={})
    audit_metadata: Dict[str, Any] = Field(sa_column=Column(JSONB), default={})

    # Approval workflow fields
    requires_approval: bool = Field(default=False, index=True)
    approval_status: Optional[ApprovalStatus] = Field(default=None, index=True)
    approved_by: Optional[int] = Field(default=None, index=True)
    approved_at: Optional[datetime] = Field(default=None)
    approval_reason: Optional[str] = Field(default=None)

    # Grouping for multi-step operations
    transaction_id: Optional[str] = Field(
        default=None, index=True, max_length=36
    )  # UUID length
    parent_audit_id: Optional[int] = Field(default=None, index=True)

    # Additional HTTP/Request context
    session_id: Optional[str] = Field(default=None, max_length=255)
    request_path: Optional[str] = Field(default=None, max_length=500)
    user_agent: Optional[str] = Field(default=None, max_length=500)

    # Status tracking
    success: bool = Field(default=True, index=True)
    error_message: Optional[str] = Field(default=None)

    # Optimistic locking (following your pattern)
    version: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    # Timestamps (following your pattern)
    created_at: datetime = Field(default_factory=get_utc_now, index=True)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()

    def set_changes(self, changes_dict: Dict[str, Any]) -> None:
        self.changes = changes_dict or {}

    def get_changes(self) -> Dict[str, Any]:
        return self.changes or {}

    def set_audit_metadata(self, metadata_dict: Dict[str, Any]) -> None:
        self.audit_metadata = metadata_dict or {}

    def get_audit_metadata(self) -> Dict[str, Any]:
        return self.audit_metadata or {}

    @staticmethod
    def _json_serializer(obj):
        """Custom JSON serializer for complex objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return str(obj)
        else:
            return str(obj)

    @classmethod
    def create_audit_entry(
        cls,
        operation_type: OperationType,
        operation_name: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        username: str = "system",
        ip_address: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        audit_metadata: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False,
        transaction_id: Optional[str] = None,
        **kwargs,
    ) -> "AuditTrail":
        """Factory method to create audit trail entries with proper JSON handling."""
        audit_entry = cls(
            operation_type=operation_type,
            operation_name=operation_name,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            requires_approval=requires_approval,
            transaction_id=transaction_id,
            **kwargs,
        )

        # Set JSON fields using the helper methods
        audit_entry.set_changes(changes or {})
        audit_entry.set_audit_metadata(audit_metadata or {})

        return audit_entry
