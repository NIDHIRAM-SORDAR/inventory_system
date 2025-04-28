# inventory_system/models/user.py
from datetime import datetime, timezone
from typing import List, Optional

import reflex as rx
from sqlmodel import Field, Relationship, Session, select

from inventory_system.logging.audit import enable_audit_logging_for_models
from inventory_system.logging.logging import audit_logger


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

        Raises:
            ValueError: If Role is not persisted, permissions don't exist,
            or operation fails.
        """
        try:
            # Validate Role is persisted
            if self.id is None:
                raise ValueError(
                    "Role must be persisted to the session before setting permissions"
                )

            # Lock the role to prevent concurrent updates
            role = session.exec(
                select(Role).where(Role.id == self.id).with_for_update()
            ).one_or_none()
            if not role:
                raise ValueError(f"Role with id={self.id} not found in database")

            # Validate all permissions exist
            permissions = session.exec(
                select(Permission).where(Permission.name.in_(permission_names))
            ).all()
            if len(permissions) != len(permission_names):
                missing_permissions = set(permission_names) - {
                    perm.name for perm in permissions
                }
                raise ValueError(f"Permissions not found: {missing_permissions}")

            # Atomically replace permissions
            session.exec(
                RolePermission.__table__.delete().where(
                    RolePermission.role_id == self.id
                )
            )
            for perm in permissions:
                role_perm = RolePermission(role_id=self.id, permission_id=perm.id)
                session.add(role_perm)

            # Update timestamp and stage Role
            self.update_timestamp()
            session.add(self)

            # Log the operation for auditing
            audit_logger.info(
                "set_permissions_success",
                entity="role_permission",
                role_id=self.id,
                permission_names=permission_names,
            )

        except Exception as e:
            session.rollback()
            audit_logger.error(
                "set_permissions_failed",
                entity="role_permission",
                role_id=self.id if self.id else "unknown",
                permission_names=permission_names,
                error=str(e),
            )
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

        Raises:
            ValueError: If UserInfo is not persisted, roles don't exist,
            or operation fails.
        """
        try:
            # Validate UserInfo is persisted
            if self.id is None:
                raise ValueError(
                    "UserInfo must be persisted to the session before setting roles"
                )

            # Lock the user to prevent concurrent updates
            user_info = session.exec(
                select(UserInfo).where(UserInfo.id == self.id).with_for_update()
            ).one_or_none()
            if not user_info:
                raise ValueError(f"UserInfo with id={self.id} not found in database")

            # Validate all roles exist
            roles = session.exec(select(Role).where(Role.name.in_(role_names))).all()
            if len(roles) != len(role_names):
                missing_roles = set(role_names) - {role.name for role in roles}
                raise ValueError(f"Roles not found: {missing_roles}")

            # Atomically replace roles
            session.exec(UserRole.__table__.delete().where(UserRole.user_id == self.id))
            for role in roles:
                user_role = UserRole(user_id=self.id, role_id=role.id)
                session.add(user_role)

            # Update timestamp and stage UserInfo
            self.update_timestamp()
            session.add(self)

            # Log the operation for auditing
            audit_logger.info(
                "set_roles_success",
                entity="user_role",
                user_id=self.id,
                role_names=role_names,
            )

        except Exception as e:
            session.rollback()
            audit_logger.error(
                "set_roles_failed",
                entity="user_role",
                user_id=self.id if self.id else "unknown",
                role_names=role_names,
                error=str(e),
            )
            raise ValueError(f"Failed to set roles: {str(e)}")

    def get_permissions(self) -> list[str]:
        """Get all permissions from the user's roles."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.get_permissions())
        return list(permissions)

    def has_permission(self, permission_name: str) -> bool:
        """Check if the user has a specific permission."""
        return permission_name in self.get_permissions()


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
