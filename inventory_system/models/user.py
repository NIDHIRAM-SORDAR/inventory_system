# inventory_system/models/user.py
from datetime import datetime, timezone
from typing import List, Optional

import reflex as rx
from sqlmodel import Field, Relationship

from inventory_system.logging.audit import enable_audit_logging_for_models


def get_utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class RolePermission(rx.Model, table=True):
    """Association table for Role-Permission many-to-many relationship."""

    role_id: Optional[int] = Field(
        foreign_key="role.id", primary_key=True, index=True, ondelete="CASCADE"
    )
    permission_id: Optional[int] = Field(
        foreign_key="permission.id", primary_key=True, index=True, ondelete="CASCADE"
    )


class UserRole(rx.Model, table=True):
    """Association table for User-Role many-to-many relationship."""

    user_id: Optional[int] = Field(
        foreign_key="userinfo.user_id", primary_key=True, index=True, ondelete="CASCADE"
    )
    role_id: Optional[int] = Field(
        foreign_key="role.id", primary_key=True, index=True, ondelete="CASCADE"
    )


class Permission(rx.Model, table=True):
    """Permission model for RBAC, defining granular access rights."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(
        unique=True, index=True
    )  # Unique permission name (e.g., 'manage_users')
    description: Optional[str] = Field(default=None)  # Description of the permission
    created_at: datetime = Field(default_factory=get_utc_now)  # Timestamp for creation
    updated_at: datetime = Field(
        default_factory=get_utc_now
    )  # Timestamp for last update
    roles: List["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermission
    )

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()


class Role(rx.Model, table=True):
    """Role model for RBAC, grouping permissions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # Unique role name (e.g., 'Admin')
    description: Optional[str] = Field(default=None)  # Description of the role
    created_at: datetime = Field(default_factory=get_utc_now)  # Timestamp for creation
    updated_at: datetime = Field(
        default_factory=get_utc_now
    )  # Timestamp for last update
    permissions: List["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermission
    )
    users: List["UserInfo"] = Relationship(back_populates="roles", link_model=UserRole)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()


class UserInfo(rx.Model, table=True):
    """User information model linked to LocalUser in a one-to-one relationship."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    is_admin: bool = Field(default=False)  # Retained for migration
    is_supplier: bool = Field(default=False)  # Retained for migration
    user_id: int = Field(
        foreign_key="localuser.id", unique=True, index=True, ondelete="CASCADE"
    )
    profile_picture: Optional[str] = Field(default=None)
    supplier: Optional["Supplier"] = Relationship(
        back_populates="user_info", cascade_delete=True
    )
    role: str = Field(default="employee")  # Retained for migration
    roles: List[Role] = Relationship(back_populates="users", link_model=UserRole)
    created_at: datetime = Field(default_factory=get_utc_now)  # Added for consistency
    updated_at: datetime = Field(default_factory=get_utc_now)  # Added for consistency

    def set_role(self) -> None:
        """Set the role based on is_admin and is_supplier flags (legacy)."""
        if self.is_admin:
            self.role = "admin"
        elif self.is_supplier:
            self.role = "supplier"
        else:
            self.role = "employee"

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()


class Supplier(rx.Model, table=True):
    """Supplier model linked to UserInfo in a one-to-one relationship."""

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str = Field(unique=True, index=True)
    description: str
    contact_email: str = Field(unique=True, index=True)
    contact_phone: str
    status: str = Field(default="pending")
    user_info_id: Optional[int] = Field(
        default=None,
        foreign_key="userinfo.id",
        unique=True,
        nullable=True,
        index=True,
        ondelete="SET NULL",
    )
    user_info: Optional[UserInfo] = Relationship(back_populates="supplier")
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()


# Enable audit logging for all models
enable_audit_logging_for_models(UserInfo, Supplier, Permission, Role)
