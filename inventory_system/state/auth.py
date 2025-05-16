from typing import List, Optional

import reflex as rx
import reflex_local_auth
from email_validator import validate_email
from sqlalchemy.orm import selectinload
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Role, UserInfo


class AuthState(reflex_local_auth.LocalAuthState):
    """State class for managing user authentication, roles, and permissions.

    Extends reflex_local_auth.LocalAuthState to leverage built-in authentication
    features (e.g., is_authenticated, authenticated_user). Manages lightweight
    state variables for user data, roles, and permissions, ensuring no database
    queries in computed vars. Uses explicit event handlers for data loading and
    updates, with optimistic UI updates and comprehensive audit logging.

    Attributes:
        user_id (Optional[int]): The ID of the authenticated user from UserInfo.user_id.
            None if not authenticated or data not loaded.
        user_email (str): The email of the authenticated user from UserInfo.email.
            Empty string if not authenticated or data not loaded.
        roles (List[str]): List of role names assigned to the user (e.g., ["admin", "employee"]).
            Empty list if not authenticated or no roles assigned.
        permissions (List[str]): List of permission names granted to the user
            (e.g., ["manage_users", "view_inventory"]). Empty list if not authenticated.
        auth_processing (bool): Indicates if a database operation (e.g., load_user_data) is in progress.
            Used for UI feedback like spinners.
        auth_error_message (str): Stores the latest error message for UI display.
            Empty string if no error.
        auth_profile_picture (str|None): The Profile picture link for the authenticated user.
            None if not authenticated or data not loaded.
    """  # noqa: E501

    user_id: Optional[int] = None
    user_email: str = ""
    roles: List[str] = []
    permissions: List[str] = []
    auth_processing: bool = False
    auth_error_message: str = ""
    auth_profile_picture: str | None = None

    @rx.var
    def username(self) -> str:
        """Get the authenticated user's username from reflex_local_auth.

        Returns:
            str: The username if authenticated, else an empty string.
        """
        return getattr(self.authenticated_user, "username", "") or ""

    @rx.var
    def is_authenticated_and_ready(self) -> bool:
        """Check if the user is authenticated and data is loaded.

        Used in UI to conditionally render content requiring user data (e.g., profile page).
        Combines reflex_local_auth's is_authenticated with user_id to ensure data readiness.

        Returns:
            bool: True if authenticated and user_id is set, False otherwise.
        """  # noqa: E501
        return self.is_authenticated and bool(self.user_id)

    @rx.event
    async def load_user_data(self):
        """Load user data, roles, and permissions from the database.

        Triggered on page load (via on_load) or after authentication/role updates.
        Fetches UserInfo with eager loading of roles and permissions to minimize
        database queries. Updates state variables optimistically and provides UI
        feedback via rx.toast. Uses SELECT FOR UPDATE for concurrency safety.
        """
        if not self.is_authenticated or not self.authenticated_user:
            self.reset_state()
            audit_logger.warning(
                "load_user_data_skipped",
                reason="Not authenticated or no user",
            )
            yield rx.toast.error("Not authenticated or no user")

        self.auth_processing = True
        yield
        try:
            with rx.session() as session:
                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == self.authenticated_user.id)
                    .options(
                        selectinload(UserInfo.roles).selectinload(Role.permissions)
                    )
                ).one_or_none()

                if not user_info:
                    audit_logger.error(
                        "load_user_data_failed",
                        user_id=self.authenticated_user.id,
                        error="UserInfo not found",
                    )
                    self.reset_state()
                    yield rx.toast.error("User info not found. Please log in again.")

                # Update state with UserInfo
                self.auth_profile_picture = (
                    user_info.profile_picture
                )  # Store the profile pitcure
                self.user_id = user_info.user_id
                self.user_email = user_info.email
                self.roles = user_info.get_roles()
                self.permissions = user_info.get_permissions(session=session)

                audit_logger.info(
                    "load_user_data_success",
                    user_id=user_info.user_id,
                    roles=self.roles,
                    permissions=self.permissions,
                )
                yield rx.toast.success("User data loaded")
        except Exception as e:
            audit_logger.error(
                "load_user_data_failed",
                user_id=self.authenticated_user.id if self.authenticated_user else None,
                error=str(e),
            )
            self.auth_error_message = str(e)
            yield rx.toast.error(f"Failed to load user data: {str(e)}")
        finally:
            self.auth_processing = False

    @rx.event
    async def update_user_info(self, email: Optional[str] = None):
        """Update the authenticated user's email with optimistic UI update."""
        if not self.is_authenticated_and_ready:
            audit_logger.error(
                "update_user_info_failed",
                user_id=self.user_id,
                email=email,
                error="No authenticated user",
            )
            yield rx.toast.error("No authenticated user")

        if not email:
            yield rx.toast.error("Email is required")

        self.auth_processing = True
        yield
        try:
            with rx.session() as session:
                validate_email(email, check_deliverability=False)
                existing_user = session.exec(
                    select(UserInfo).where(
                        UserInfo.email == email,
                        UserInfo.user_id != self.user_id,
                    )
                ).one_or_none()
                if existing_user:
                    raise ValueError("This email is already in use by another user")

                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == self.user_id)
                    .with_for_update()
                ).one_or_none()
                if not user_info:
                    raise ValueError("User info not found")

                # Optimistic update for UI
                original_email = self.user_email
                self.user_email = email

                user_info.email = email
                user_info.update_timestamp()
                session.add(user_info)

                # Update LocalUser email
                local_user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == self.user_id
                    )
                ).one_or_none()
                if local_user:
                    local_user.email = email
                    session.add(local_user)

                session.commit()
                session.refresh(user_info)

                audit_logger.info(
                    "update_user_info_success",
                    user_id=self.user_id,
                    email=email,
                )
                yield rx.toast.success("User info updated successfully")
        except Exception as e:
            session.rollback()
            self.user_email = original_email
            audit_logger.error(
                "update_user_info_failed",
                user_id=self.user_id,
                email=email,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to update user info: {str(e)}")
        finally:
            self.auth_processing = False

    @rx.event
    async def update_roles(self, role_names: List[str]):
        """Update the authenticated user's roles with optimistic UI update."""
        if not self.is_authenticated_and_ready:
            audit_logger.error(
                "update_roles_failed",
                user_id=self.user_id,
                role_names=role_names,
                error="No authenticated user",
            )
            yield rx.toast.error("No authenticated user")

        self.auth_processing = True
        yield
        try:
            with rx.session() as session:
                user_info = session.exec(
                    select(UserInfo)
                    .where(UserInfo.user_id == self.user_id)
                    .with_for_update()
                ).one_or_none()
                if not user_info:
                    raise ValueError("User info not found")

                # Optimistic update for UI
                original_roles = self.roles
                self.roles = role_names
                self.user_info.set_roles(role_names, session)  # Update user_info

                user_info.set_roles(role_names, session)
                session.commit()
                session.refresh(user_info)

                self.permissions = user_info.get_permissions(session=session)

                audit_logger.info(
                    "roles_updated",
                    user_id=self.user_id,
                    role_names=role_names,
                )
                yield rx.toast.success("Roles updated successfully")
        except Exception as e:
            session.rollback()
            self.set_roles(original_roles)
            audit_logger.error(
                "roles_update_failed",
                user_id=self.user_id,
                role_names=role_names,
                error=str(e),
            )
            yield rx.toast.error(f"Failed to update roles: {str(e)}")
        finally:
            self.auth_processing = False

    @rx.event
    async def validate_session(self):
        """Validate the current user's session and authentication status."""
        self.auth_processing = True
        yield

        try:
            if (
                not self.is_authenticated
                or not self.authenticated_user
                or not self.auth_token
            ):
                audit_logger.warning(
                    "validate_session_failed",
                    user_id=self.user_id,
                    reason="Not authenticated, no user, or no token",
                )
                self.do_logout()
                self.reset_state()
                yield rx.toast.error("Session invalid. Please log in.")
                yield rx.redirect(routes.LOGIN_ROUTE)

            with rx.session() as session:
                local_user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == self.authenticated_user.id
                    )
                ).one_or_none()

                if not local_user:
                    audit_logger.error(
                        "validate_session_failed",
                        user_id=self.authenticated_user.id,
                        error="LocalUser not found",
                    )
                    self.do_logout()
                    self.reset_state()
                    yield rx.toast.error("Session invalid. Please log in.")
                    yield rx.redirect(routes.LOGIN_ROUTE)

                audit_logger.info(
                    "validate_session_success",
                    user_id=self.authenticated_user.id,
                )
                yield rx.toast.success("Session validated")
        except Exception as e:
            audit_logger.error(
                "validate_session_failed",
                user_id=self.authenticated_user.id if self.authenticated_user else None,
                error=str(e),
            )
            self.auth_error_message = str(e)
            self.do_logout()
            self.reset_state()
            yield rx.toast.error(f"Session validation failed: {str(e)}")
            yield rx.redirect(routes.LOGIN_ROUTE)
        finally:
            self.auth_processing = False

    def has_permission(self, permission_name: str) -> bool:
        """Check if the user has a specific permission."""
        return permission_name in self.permissions

    def reset_state(self):
        """Reset state variables to their default values."""
        self.user_id = None
        self.user_email = ""
        self.roles = []
        self.permissions = []
        self.auth_error_message = ""
        self.auth_profile_picture = ""
