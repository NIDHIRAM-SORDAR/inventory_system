from datetime import datetime, timezone
from typing import Optional

import reflex as rx
from sqlmodel import Field, Relationship

from inventory_system.logging.audit import enable_audit_logging_for_models


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


# Enable audit logging for all models
enable_audit_logging_for_models(UserInfo, Supplier)
