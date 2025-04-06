# inventory_system/models/user.py
from sqlmodel import Field, Relationship, select
from typing import Optional
from datetime import datetime, timezone
import reflex as rx

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class UserInfo(rx.Model, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    is_admin: bool = False
    is_supplier: bool = False
    user_id: int = Field(foreign_key="localuser.id")
    supplier: Optional["Supplier"] = Relationship(
        back_populates="user_info",
        cascade_delete=True
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
        default=None,
        foreign_key="userinfo.id",
        nullable=True,
        ondelete="CASCADE"  # Corrected placement
    )
    user_info: Optional[UserInfo] = Relationship(
        back_populates="supplier",
    )
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self):
        self.updated_at = get_utc_now()