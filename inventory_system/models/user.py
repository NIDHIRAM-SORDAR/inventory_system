# inventory_system/models/user.py
from datetime import datetime, timezone
from typing import List, Optional

import reflex as rx
from sqlmodel import Field, Relationship, Session, select

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
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
    roles: List["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermission
    )

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()


class Role(rx.Model, table=True):
    """Role model for RBAC, grouping permissions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
    permissions: List[Permission] = Relationship(
        back_populates="roles", link_model=RolePermission
    )
    users: List["UserInfo"] = Relationship(back_populates="roles", link_model=UserRole)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()

    def get_permissions(self) -> List[str]:
        """Get the list of permission names assigned to this role."""
        return [perm.name for perm in self.permissions]

    def set_permissions(self, permission_names: List[str], session: Session) -> None:
        """Set the permissions for this role atomically, replacing existing ones.

        Args:
            permission_names: List of permission names to assign.
            session: Database session for atomic operations.
        """
        try:
            # Lock the role to prevent concurrent updates
            session.exec(select(Role).where(Role.id == self.id).with_for_update()).one()

            # Clear existing permissions
            session.exec(
                RolePermission.__table__.delete().where(
                    RolePermission.role_id == self.id
                )
            )

            # Add new permissions
            for perm_name in permission_names:
                perm = session.exec(
                    select(Permission).where(Permission.name == perm_name)
                ).one_or_none()
                if not perm:
                    raise ValueError(f"Permission '{perm_name}' does not exist")
                role_perm = RolePermission(role_id=self.id, permission_id=perm.id)
                session.add(role_perm)

            self.update_timestamp()
            session.add(self)
        except Exception as e:
            session.rollback()
            raise ValueError(f"Failed to set permissions: {str(e)}")


class UserInfo(rx.Model, table=True):
    """User information model linked to LocalUser in a one-to-one relationship."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    user_id: int = Field(
        foreign_key="localuser.id", unique=True, index=True, ondelete="CASCADE"
    )
    profile_picture: Optional[str] = Field(default=None)
    supplier: Optional["Supplier"] = Relationship(
        back_populates="user_info", cascade_delete=True
    )
    roles: List[Role] = Relationship(back_populates="users", link_model=UserRole)
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()

    def get_roles(self) -> List[str]:
        """Get the list of role names assigned to this user."""
        return [role.name for role in self.roles]

    def set_roles(self, role_names: List[str], session: Session) -> None:
        """Set the roles for this user atomically, replacing existing ones.

        Args:
            role_names: List of role names to assign.
            session: Database session for atomic operations.
        """
        try:
            # Lock the user to prevent concurrent updates
            session.exec(
                select(UserInfo).where(UserInfo.id == self.id).with_for_update()
            ).one()

            # Clear existing roles
            session.exec(UserRole.__table__.delete().where(UserRole.user_id == self.id))

            # Add new roles
            for role_name in role_names:
                role = session.exec(
                    select(Role).where(Role.name == role_name)
                ).one_or_none()
                if not role:
                    raise ValueError(f"Role '{role_name}' does not exist")
                user_role = UserRole(user_id=self.id, role_id=role.id)
                session.add(user_role)

            self.update_timestamp()
            session.add(self)
        except Exception as e:
            session.rollback()
            raise ValueError(f"Failed to set roles: {str(e)}")


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
enable_audit_logging_for_models(
    UserInfo, Supplier, Permission, Role, UserRole, RolePermission
)
