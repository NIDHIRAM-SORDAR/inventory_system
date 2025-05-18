# inventory_system/models/user.py
from datetime import datetime, timezone
from typing import List, Optional

import reflex as rx
from sqlalchemy import Column, Integer
from sqlalchemy.orm import selectinload
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
    category: Optional[str] = Field(default=None)  # New field for categorization
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
    roles: List["Role"] = Relationship(
        back_populates="permissions", link_model=RolePermission
    )

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()

    def update_permission(
        self,
        session: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
    ) -> None:
        """
        Update the permission's name, description, and/or category atomically
        with optimistic locking.

        Args:
            name: Optional new name for the permission. Must be unique if provided.
            description: Optional new description. Can be None to clear the description.
            category: Optional new category. Can be None to clear the category.
            session: SQLModel session for database operations.

        Raises:
            ValueError: If the permission is not persisted, not found, version mismatch,
            or new name already exists.
        """
        try:
            if self.id is None:
                raise ValueError("Permission must be persisted to the session")
            permission = session.exec(
                select(Permission).where(Permission.id == self.id).with_for_update()
            ).one_or_none()
            if not permission:
                raise ValueError(f"Permission with id={self.id} not found")
            if name and name != self.name:
                if session.exec(
                    select(Permission).where(Permission.name == name)
                ).one_or_none():
                    raise ValueError(f"Permission name '{name}' already exists")
                self.name = name
            if description is not None:
                self.description = description
            if category is not None:
                self.category = category
            self.update_timestamp()
            session.add(self)
            audit_logger.info(
                "update_permission_success",
                permission_id=self.id,
                name=name,
                description=description,
                category=category,
            )
        except Exception as e:
            session.rollback()
            audit_logger.error(
                "update_permission_failed",
                permission_id=self.id if self.id else "unknown",
                error=str(e),
            )
            raise ValueError(f"Failed to update permission: {str(e)}")

    @classmethod
    def create_permission(
        cls,
        name: str,
        description: Optional[str],
        category: Optional[str],
        session: Session,
    ) -> "Permission":
        try:
            if session.exec(
                select(Permission).where(Permission.name == name)
            ).one_or_none():
                raise ValueError(f"Permission '{name}' already exists")
            permission = Permission(
                name=name, description=description, category=category
            )
            session.add(permission)
            session.flush()
            audit_logger.info(
                "create_permission_success", permission_name=name, category=category
            )
            return permission
        except Exception as e:
            session.rollback()
            audit_logger.error(
                "create_permission_failed", permission_name=name, error=str(e)
            )
            raise ValueError(f"Failed to create permission: {str(e)}")

    @classmethod
    def delete_permission(cls, name: str, session: Session) -> None:
        try:
            permission = session.exec(
                select(Permission).where(Permission.name == name).with_for_update()
            ).one_or_none()
            if not permission:
                raise ValueError(f"Permission '{name}' not found")
            session.delete(permission)
            session.flush()
            audit_logger.info("delete_permission_success", permission_name=name)
        except Exception as e:
            session.rollback()
            audit_logger.error(
                "delete_permission_failed", permission_name=name, error=str(e)
            )
            raise ValueError(f"Failed to delete permission: {str(e)}")


class Role(rx.Model, table=True):
    """Role model for RBAC, grouping permissions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)  # For soft deletion
    version: int = Field(
        default=0, sa_column=Column(Integer, nullable=False)
    )  # Optimistic locking
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
        """Set the permissions for this role atomically, replacing existing ones."""
        try:
            if self.id is None:
                raise ValueError("Role must be persisted to the session")
            role = session.exec(
                select(Role)
                .where(Role.id == self.id, Role.version == self.version)
                .with_for_update()
            ).one_or_none()
            if not role:
                raise ValueError(
                    f"Role with id={self.id} not found or version mismatch"
                )
            permissions = session.exec(
                select(Permission).where(Permission.name.in_(permission_names))
            ).all()
            if len(permissions) != len(permission_names):
                missing = set(permission_names) - {perm.name for perm in permissions}
                raise ValueError(f"Permissions not found: {missing}")
            session.exec(
                RolePermission.__table__.delete().where(
                    RolePermission.role_id == self.id
                )
            )
            for perm in permissions:
                session.add(RolePermission(role_id=self.id, permission_id=perm.id))
            self.version += 1  # Increment version for optimistic locking
            self.update_timestamp()
            session.add(self)
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

    def update_role(
        self,
        session: Session,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        try:
            if self.id is None:
                raise ValueError("Role must be persisted to the session")
            role = session.exec(
                select(Role)
                .where(Role.id == self.id, Role.version == self.version)
                .with_for_update()
            ).one_or_none()
            if not role:
                raise ValueError(
                    f"Role with id={self.id} not found or version mismatch"
                )
            if name and name != self.name:
                if session.exec(select(Role).where(Role.name == name)).one_or_none():
                    raise ValueError(f"Role name '{name}' already exists")
                self.name = name
            if description is not None:
                self.description = description
            self.version += 1
            self.update_timestamp()
            session.add(self)
            audit_logger.info(
                "update_role_success",
                role_id=self.id,
                name=name,
                description=description,
            )
        except Exception as e:
            session.rollback()
            audit_logger.error("update_role_failed", role_id=self.id, error=str(e))
            raise ValueError(f"Failed to update role: {str(e)}")

    @classmethod
    def create_role(
        cls, name: str, description: Optional[str], session: Session
    ) -> "Role":
        try:
            if session.exec(select(Role).where(Role.name == name)).one_or_none():
                raise ValueError(f"Role '{name}' already exists")
            role = Role(name=name, description=description)
            session.add(role)
            session.flush()
            audit_logger.info("create_role_success", role_name=name)
            return role
        except Exception as e:
            session.rollback()
            audit_logger.error("create_role_failed", role_name=name, error=str(e))
            raise ValueError(f"Failed to create role: {str(e)}")

    @classmethod
    def delete_role(cls, name: str, session: Session) -> None:
        try:
            role = session.exec(
                select(Role).where(Role.name == name, Role.is_active).with_for_update()
            ).one_or_none()
            if not role:
                raise ValueError(f"Active role '{name}' not found")
            role.is_active = False  # Soft deletion
            role.version += 1
            role.update_timestamp()
            session.add(role)
            audit_logger.info("delete_role_success", role_name=name)
        except Exception as e:
            session.rollback()
            audit_logger.error("delete_role_failed", role_name=name, error=str(e))
            raise ValueError(f"Failed to delete role: {str(e)}")


class UserInfo(rx.Model, table=True):
    """User information model linked to LocalUser in a one-to-one relationship."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    user_id: int = Field(
        foreign_key="localuser.id", unique=True, index=True, ondelete="CASCADE"
    )
    profile_picture: Optional[str] = Field(default=None)
    version: int = Field(
        default=0, sa_column=Column(Integer, nullable=False)
    )  # Optimistic locking
    supplier: Optional["Supplier"] = Relationship(
        back_populates="user_info", cascade_delete=True
    )
    roles: List[Role] = Relationship(
        back_populates="users", link_model=UserRole
    )  # Fixed back_populates
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp to current UTC time."""
        self.updated_at = get_utc_now()

    def get_roles(self) -> List[str]:
        """Get the list of role names assigned to this user."""
        return [role.name for role in self.roles if role.is_active]

    def set_roles(self, role_names: List[str], session: Session) -> None:
        """Set the roles for this user atomically, replacing existing ones."""
        try:
            if self.id is None:
                raise ValueError("UserInfo must be persisted to the session")
            user_info = session.exec(
                select(UserInfo)
                .where(UserInfo.id == self.id, UserInfo.version == self.version)
                .with_for_update()
            ).one_or_none()
            if not user_info:
                raise ValueError(
                    f"UserInfo with id={self.id} not found or version mismatch"
                )
            roles = session.exec(
                select(Role).where(Role.name.in_(role_names), Role.is_active)
            ).all()
            if len(roles) != len(role_names):
                missing = set(role_names) - {role.name for role in roles}
                raise ValueError(f"Roles not found or inactive: {missing}")
            session.exec(UserRole.__table__.delete().where(UserRole.user_id == self.id))
            for role in roles:
                session.add(UserRole(user_id=self.id, role_id=role.id))
            self.version += 1  # Increment version for optimistic locking
            self.update_timestamp()
            session.add(self)
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

    def get_permissions(self, session: Session = None) -> List[str]:
        """Get the user's permissions, using eager loading if session provided."""
        if session:
            user_info = session.exec(
                select(UserInfo)
                .where(UserInfo.id == self.id)
                .options(selectinload(UserInfo.roles).selectinload(Role.permissions))
            ).one_or_none()
            if not user_info:
                audit_logger.warning(
                    "get_permissions_failed",
                    user_id=self.id,
                    error="UserInfo not found during eager loading",
                )
                return []
            self.roles = user_info.roles
            audit_logger.info(
                "get_permissions_eager_load",
                user_id=self.id,
                roles=[role.name for role in self.roles if role.is_active],
            )
        permissions = set()
        for role in self.roles:
            if role.is_active:
                permissions.update(role.get_permissions())
        return list(permissions)

    def has_permission(self, permission_name: str, session: Session = None) -> bool:
        """Check if the user has a specific permission."""
        return permission_name in self.get_permissions(session)


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


enable_audit_logging_for_models(
    UserInfo, Supplier, Permission, Role, UserRole, RolePermission
)
