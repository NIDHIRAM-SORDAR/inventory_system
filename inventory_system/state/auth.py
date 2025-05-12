import asyncio
import time
from functools import wraps
from typing import List, Optional

import reflex as rx
import reflex_local_auth
from email_validator import validate_email
from sqlalchemy.orm import selectinload
from sqlmodel import select

from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Role, UserInfo


def has_permission(permission_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if permission_name in self.user_permissions:
                return func(self, *args, **kwargs)
            audit_logger.warning(
                "permission_denied",
                user_id=self.authenticated_user.id if self.authenticated_user else None,
                permission=permission_name,
            )
            return rx.toast.error(f"Permission denied: {permission_name}")

        return wrapper

    return decorator


class AuthState(reflex_local_auth.LocalAuthState):
    authenticated_user_info: Optional[UserInfo] = None
    last_refresh: float = 0.0
    cache_ttl: float = 60.0  # 1 minute TTL for cache

    @rx.var
    def username(self) -> str | None:
        """Get the authenticated user's username."""
        return self.authenticated_user.username if self.authenticated_user else ""

    @rx.var
    def user_email(self) -> str:
        """Get the authenticated user's email for reactive UI."""
        return (
            self.authenticated_user_info.email if self.authenticated_user_info else ""
        )

    @rx.var(cache=True)
    def user_permissions(self) -> List[str]:
        """Return permissions for the authenticated user."""
        if self.authenticated_user_info:
            return self.authenticated_user_info.get_permissions()
        return []

    @rx.var(cache=True)
    def user_roles(self) -> List[str]:
        """Return roles for the authenticated user."""
        if self.authenticated_user_info:
            return self.authenticated_user_info.get_roles()
        return []

    @rx.event(background=True)
    async def refresh_user_data(self):
        """Refresh user data from the database."""
        if not self.is_authenticated or not self.authenticated_user:
            self.authenticated_user_info = None  # Direct assignment for state update
            audit_logger.warning(
                "refresh_user_data_skipped",
                reason="Not authenticated or no user",
            )
            return

        if time.time() - self.last_refresh < self.cache_ttl:
            audit_logger.info(
                "refresh_user_data_skipped",
                user_id=self.authenticated_user.id,
                reason="Cache still valid",
            )
            return

        try:
            with rx.session() as session:
                # Log the user_id being queried
                audit_logger.info(
                    "refresh_user_data_attempt",
                    user_id=self.authenticated_user.id,
                )
                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == self.authenticated_user.id)
                    .options(
                        selectinload(UserInfo.roles).selectinload(Role.permissions)
                    )
                ).one_or_none()

                if not user_info:
                    # Force re-computation of authenticated_user by
                    # updating its dependency (auth_token)
                    current_token = self.auth_token
                    self.auth_token = (
                        current_token  # Reassign to trigger re-computation
                    )
                    audit_logger.info(
                        "auth_token_reset",
                        user_id=self.authenticated_user.id,
                        reason="Forcing authenticated_user re-computation",
                    )

                    # Check if the user is still authenticated after re-computation
                    if not self.is_authenticated:
                        audit_logger.warning(
                            "refresh_user_data_failed",
                            user_id=self.authenticated_user.id,
                            error="User session invalid after auth_token reset",
                        )
                        self.authenticated_user_info = None
                        yield rx.toast.error("Session invalid. Please log in again.")
                        return

                    # Retry query with fresh authenticated_user
                    user_info = session.exec(
                        select(UserInfo)
                        .where(UserInfo.user_id == self.authenticated_user.id)
                        .options(
                            selectinload(UserInfo.roles).selectinload(Role.permissions)
                        )
                    ).one_or_none()

                    if not user_info:
                        audit_logger.error(
                            "refresh_user_data_failed",
                            user_id=self.authenticated_user.id,
                            error="UserInfo not found after auth_token reset",
                        )
                        self.authenticated_user_info = None
                        yield rx.toast.error("User info not found. Contact support.")
                        return

                # Log the loaded roles and permissions for debugging
                roles = user_info.get_roles()
                permissions = user_info.get_permissions(session=session)
                audit_logger.info(
                    "refresh_user_data_success",
                    user_id=self.authenticated_user.id,
                    roles=roles,
                    permissions=permissions,
                )

                self.authenticated_user_info = user_info
                self.last_refresh = time.time()

        except Exception as e:
            audit_logger.error(
                "refresh_user_data_failed",
                user_id=self.authenticated_user.id if self.authenticated_user else None,
                error=str(e),
            )
            self.authenticated_user_info = None
            yield rx.toast.error(f"Failed to refresh user data: {str(e)}")

    @rx.event(background=True)
    async def update_user_info(self, email: Optional[str] = None):
        """Update user info (e.g., email) and sync with database."""
        if not self.authenticated_user_info:
            yield rx.toast.error("No authenticated user")
            return

        try:
            with rx.session() as session:
                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == self.authenticated_user.id)
                    .with_for_update()
                ).one_or_none()
                if not user_info:
                    raise ValueError("User info not found")

                if email:
                    validate_email(email, check_deliverability=False)
                    existing_user = session.exec(
                        select(UserInfo).where(
                            UserInfo.email == email,
                            UserInfo.user_id != self.authenticated_user.id,
                        )
                    ).one_or_none()
                    if existing_user:
                        raise ValueError("This email is already in use by another user")
                    user_info.email = email

                user_info.update_timestamp()
                session.add(user_info)
                session.commit()

                # Refresh user data to sync state
                self.authenticated_user_info = user_info
                audit_logger.info(
                    "update_user_info_success",
                    user_id=self.authenticated_user.id,
                    email=email,
                )
                yield rx.toast.success("User info updated successfully")

        except Exception as e:
            audit_logger.error(
                "update_user_info_failed",
                user_id=self.authenticated_user.id,
                email=email,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to update user info: {str(e)}")

    @rx.event(background=True)
    async def update_roles(self, role_names: List[str]):
        """Update the user's roles and refresh user data."""
        if not self.authenticated_user_info:
            yield rx.toast.error("No authenticated user")
            return

        try:
            with rx.session() as session:
                user_info = session.merge(self.authenticated_user_info)
                user_info.set_roles(role_names, session)
                session.commit()
                await self.refresh_user_data()
                audit_logger.info(
                    "roles_updated",
                    user_id=self.authenticated_user.id,
                    role_names=role_names,
                )
                yield rx.toast.success("Roles updated successfully")
        except ValueError as e:
            audit_logger.error(
                "roles_update_failed",
                user_id=self.authenticated_user.id,
                role_names=role_names,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to update roles: {str(e)}")

    @rx.event(background=True)
    async def periodic_refresh(self):
        """Periodically refresh user data for long-lived sessions."""
        while self.is_authenticated:
            await asyncio.sleep(300)  # 5 minutes
            await self.refresh_user_data()
