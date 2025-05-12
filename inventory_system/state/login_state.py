from datetime import timedelta

import reflex as rx
import reflex_local_auth
import sqlalchemy
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import UserInfo
from inventory_system.state.auth import AuthState


class CustomLoginState(AuthState):
    """Custom login state to redirect based on user role."""

    error_message: str = ""
    is_submitting: bool = False

    @rx.event
    def route_calc(self):
        """Handle redirects for authenticated users on page load."""
        if self.is_login and not self.is_submitting:
            if "manage_users" in self.user_permissions:
                yield rx.redirect(routes.ADMIN_ROUTE)
            yield rx.redirect(routes.OVERVIEW_ROUTE)

    @rx.event
    def reset_form_state(self):
        """Reset form state on page load."""
        self.error_message = ""
        self.is_submitting = False

    @rx.event
    async def on_submit(self, form_data: dict):
        """Handle login form submission and redirect based on role."""
        self.error_message = ""
        self.is_submitting = True
        username = form_data.get("username", "N/A")
        password = form_data.get("password", "N/A")
        ip_address = self.router.session.client_ip

        # Log HTTP request
        audit_logger.info(
            "http_request",
            method="POST",
            url=self.router.page.raw_path,
            user_id=None,
            username=username,
            ip_address=ip_address,
        )

        try:
            with rx.session() as session:
                try:
                    user = session.exec(
                        select(reflex_local_auth.LocalUser).where(
                            reflex_local_auth.LocalUser.username == username
                        )
                    ).one_or_none()
                except sqlalchemy.exc.MultipleResultsFound:
                    self.error_message = (
                        "Multiple accounts found for this username. "
                        "Please contact support."
                    )
                    audit_logger.error(
                        "login_failed_multiple_users",
                        username=username,
                        error="Multiple LocalUser records found",
                        ip_address=ip_address,
                    )
                    self.set_authenticated_user(None)  # Revert optimistic update
                    yield rx.toast.error(self.error_message)

                if not user or not user.verify(password):
                    self.error_message = "Invalid username or password"
                    audit_logger.info(
                        "login_failed",
                        username=username,
                        error=self.error_message,
                        ip_address=ip_address,
                    )
                    self.set_authenticated_user(None)  # Revert optimistic update
                    yield rx.toast.error(self.error_message)

                # Optimistic update
                self.set_authenticated_user(user)
                self.is_submitting = False  # Early feedback

                # Log in and refresh data
                self._login(user.id, expiration_delta=timedelta(days=7))
                self.refresh_user_data()

                audit_logger.info(
                    "login_success",
                    user_id=user.id,
                    username=self.get_username,
                    roles=self.user_roles,
                    ip_address=ip_address,
                )

                try:
                    user_info = session.exec(
                        select(UserInfo).where(UserInfo.user_id == user.id)
                    ).one_or_none()
                    if not user_info:
                        self.error_message = (
                            "User profile not found. Please contact support."
                        )
                        audit_logger.error(
                            "login_failed_no_userinfo",
                            username=username,
                            error="No UserInfo record found",
                            ip_address=ip_address,
                        )
                        self.set_authenticated_user(None)  # Revert optimistic update
                        yield rx.toast.error(self.error_message)
                except sqlalchemy.exc.MultipleResultsFound:
                    self.error_message = (
                        "Multiple user profiles found. Please contact support."
                    )
                    audit_logger.error(
                        "login_failed_multiple_userinfo",
                        username=username,
                        error="Multiple UserInfo records found",
                        ip_address=ip_address,
                    )
                    self.set_authenticated_user(None)  # Revert optimistic update
                    yield rx.toast.error(self.error_message)

                # Redirect based on permissions
                if self.is_login:
                    yield rx.toast.success(
                        "Login successful! Redirecting...",
                        position="top-center",
                        duration=1000,
                    )
                    self.refresh_user_data()  # Ensure user data is up-to-date
                    print("User permissions:", self.user_permissions)
                    if "manage_users" in self.user_permissions:
                        yield rx.redirect(routes.ADMIN_ROUTE)
                    else:
                        yield rx.redirect(routes.OVERVIEW_ROUTE)
                else:
                    self.error_message = "Authentication failed unexpectedly."
                    audit_logger.error(
                        "login_failed_auth_state",
                        username=username,
                        user_id=user.id,
                        reason=self.error_message,
                        ip_address=ip_address,
                    )
                    self.set_authenticated_user(None)  # Revert optimistic update
                    yield rx.toast.error(self.error_message)

        except Exception as e:
            self.error_message = "An unexpected error occurred. Please try again."
            audit_logger.error(
                "login_failed_unexpected",
                username=username,
                error=str(e),
                ip_address=ip_address,
                exception_type=type(e).__name__,
            )
            self.set_authenticated_user(None)  # Revert optimistic update
            yield rx.toast.error(self.error_message)

        finally:
            self.is_submitting = False
            audit_logger.info(
                "http_response",
                method="POST",
                url=self.router.page.raw_path,
                user_id=user.id if user and self.is_login else None,
                username=self.get_username or username,
                ip_address=ip_address,
                status_code=200 if self.is_login else 401,
            )
