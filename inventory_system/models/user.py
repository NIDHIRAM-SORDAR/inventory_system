from datetime import datetime, timezone
from typing import Optional

import reflex as rx
from reflex_local_auth import LocalUser as BaseLocalUser
from sqlmodel import Field, Relationship

from inventory_system.logging.audit import enable_audit_logging_for_models


def get_utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class LocalUser(BaseLocalUser, table=True):
    """User model for authentication, extending reflex_local_auth.LocalUser."""

    username: str = Field(
        unique=True, index=True
    )  # Unique username with index for faster lookups
    # Other fields (e.g., password_hash) are inherited from BaseLocalUser


class UserInfo(rx.Model, table=True):
    """User information model linked to LocalUser in a one-to-one relationship."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)  # Index for faster email lookups
    is_admin: bool = Field(default=False)
    is_supplier: bool = Field(default=False)
    user_id: int = Field(
        foreign_key="localuser.id",
        unique=True,  # Ensure one-to-one with LocalUser
        index=True,  # Index for faster queries
        ondelete="CASCADE",  # Delete UserInfo if LocalUser is deleted
    )
    profile_picture: Optional[str] = Field(default=None)
    supplier: Optional["Supplier"] = Relationship(
        back_populates="user_info",
        sa_relationship_kwargs={
            "cascade": "all, delete"
        },  # Cascade deletes to Supplier
    )
    role: str = Field(default="employee")

    def set_role(self):
        """Set the role based on is_admin and is_supplier flags."""
        if self.is_admin:
            self.role = "admin"
        elif self.is_supplier:
            self.role = "supplier"
        else:
            self.role = "employee"


class Supplier(rx.Model, table=True):
    """Supplier model linked to UserInfo in a one-to-one relationship."""

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str
    description: str
    contact_email: str = Field(unique=True, index=True)  # Unique email for suppliers
    contact_phone: str
    status: str = Field(default="pending")
    user_info_id: Optional[int] = Field(
        default=None,
        foreign_key="userinfo.id",
        unique=True,  # Ensure one-to-one with UserInfo
        nullable=True,
        index=True,
        ondelete="SET NULL",  # Set to NULL if UserInfo is deleted
    )
    user_info: Optional[UserInfo] = Relationship(
        back_populates="supplier",
    )
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self):
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()


# Enable audit logging for UserInfo and Supplier models
enable_audit_logging_for_models(UserInfo, Supplier)
