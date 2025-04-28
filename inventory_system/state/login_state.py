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

    @rx.var
    def is_login(self) -> bool:
        """Computed var to check if the user is logged in."""
        return self.authenticated_user.id >= 0

    @rx.var(cache=True)
    def get_username(self) -> str | None:
        return self.authenticated_user.username if self.authenticated_user else None

    def route_calc(self):
        """Handle redirects for authenticated users on page load."""
        if self.is_login:
            if "manage_users" in self.user_permissions:
                return rx.redirect(routes.ADMIN_ROUTE)
            return rx.redirect(routes.OVERVIEW_ROUTE)

    def reset_form_state(self):
        """Reset form state on page load."""
        self.error_message = ""
        self.is_submitting = False

    # inventory_system/state/login_state.py

    async def on_submit(self, form_data: dict):
        """Handle login form submission and redirect based on role."""
        self.error_message = ""
        self.is_submitting = True

        # Log HTTP request
        audit_logger.info(
            "http_request",
            method="POST",
            url=self.router.page.raw_path,
            user_id=None,
            username=form_data.get("username"),
            ip_address=self.router.session.client_ip,
        )

        try:
            with rx.session() as session:
                try:
                    user = session.exec(
                        select(reflex_local_auth.LocalUser).where(
                            reflex_local_auth.LocalUser.username
                            == form_data["username"]
                        )
                    ).one_or_none()
                except sqlalchemy.exc.MultipleResultsFound:
                    self.error_message = (
                        "Multiple accounts found for this username."
                        "Please contact support."
                    )
                    self.is_submitting = False
                    audit_logger.error(
                        "login_failed_multiple_users",
                        username=form_data["username"],
                        error="Multiple LocalUser records found",
                        ip_address=self.router.session.client_ip,
                        method="POST",
                        url=self.router.page.raw_path,
                    )
                    return

                if not user or not user.verify(form_data["password"]):
                    self.error_message = "Invalid username or password"
                    self.is_submitting = False
                    audit_logger.info(
                        "login_failed",
                        username=form_data["username"],
                        error=self.error_message,
                        ip_address=self.router.session.client_ip,
                        method="POST",
                        url=self.router.page.raw_path,
                    )
                    return

                self._login(user.id, expiration_delta=timedelta(days=7))
                self.refresh_user_data()  # Cache permissions and roles

                audit_logger.info(
                    "login_success",
                    user_id=user.id,
                    username=self.get_username,
                    ip_address=self.router.session.client_ip,
                    method="POST",
                    url=self.router.page.raw_path,
                )

                try:
                    user_info = session.exec(
                        select(UserInfo).where(
                            UserInfo.user_id == self.authenticated_user.id
                        )
                    ).one_or_none()
                except sqlalchemy.exc.MultipleResultsFound:
                    self.error_message = (
                        "Multiple user profiles found. Please contact support."
                    )
                    self.is_submitting = False
                    audit_logger.error(
                        "login_failed_multiple_userinfo",
                        username=form_data["username"],
                        error="Multiple UserInfo records found",
                        ip_address=self.router.session.client_ip,
                        method="POST",
                        url=self.router.page.raw_path,
                    )
                    return
                if user_info and "manage_users" in self.user_permissions:
                    return rx.redirect(routes.ADMIN_ROUTE)
                return rx.redirect(routes.OVERVIEW_ROUTE)

        finally:
            self.is_submitting = False
            # Log HTTP response
            audit_logger.info(
                "http_response",
                method="POST",
                url=self.router.page.raw_path,
                user_id=user.id if user else None,
                username=self.get_username
                if self.get_username
                else form_data.get("username"),
                ip_address=self.router.session.client_ip,
                status_code=200 if user else 401,
            )
