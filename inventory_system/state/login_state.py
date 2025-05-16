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
    """Custom login state to manage authentication and redirect based on user permissions.

    Extends AuthState to leverage session validation, user data loading, and permission-based
    routing. Handles login form submission and page-load redirects, ensuring only valid
    sessions access protected routes. Provides UI feedback and audit logging for all actions.

    Attributes:
        error_message (str): Stores error messages for UI display (e.g., login failures).
        is_submitting (bool): Indicates if a login submission is in progress, used for UI feedback.
    """  # noqa: E501

    error_message: str = ""
    is_submitting: bool = False

    @rx.event
    def route_calc(self):
        """Handle redirects for authenticated users on page load by validating session.

        Validates the user's session using validate_session. If valid, loads user data and
        redirects based on permissions (admin or overview page). If invalid, validate_session
        redirects to login, halting further processing.

        Yields:
            rx.EventSpec: Events for session validation, data loading, and redirection.

        Notes:
            - Uses type(self).validate_session() to ensure session validity before proceeding.
            - Checks is_authenticated post-validation for robustness.
            - Redirects to ADMIN_ROUTE if 'manage_users' permission exists, else OVERVIEW_ROUTE.
        """  # noqa: E501
        if self.is_authenticated:
            yield type(self).validate_session()
            if self.is_authenticated:  # Proceed only if session remains valid
                yield type(self).load_user_data()
                if "manage_users" in self.permissions:
                    yield rx.redirect(routes.ADMIN_ROUTE)
                else:
                    yield rx.redirect(routes.OVERVIEW_ROUTE)

    @rx.event
    def reset_form_state(self):
        """Reset form state variables on page load.

        Clears error messages and submission status to ensure a clean UI state when the login
        page is accessed.

        Notes:
            - Called on page load to prevent stale data display.
        """  # noqa: E501
        self.error_message = ""
        self.is_submitting = False

    @rx.event
    def post_login(self, user):
        """Handle post-login actions including logging and redirection.

        Logs successful login to audit_logger and redirects the user based on permissions.
        Provides UI feedback via a success toast.

        Args:
            user: The LocalUser object of the authenticated user.

        Yields:
            rx.EventSpec: Toast notification and redirect events.

        Notes:
            - Uses self.roles and self.permissions from AuthState for consistency.
            - Redirects to ADMIN_ROUTE if 'manage_users' permission exists, else OVERVIEW_ROUTE.
        """  # noqa: E501
        audit_logger.info(
            "login_success",
            user_id=user["id"],
            username=user["username"],
            roles=self.roles,
            ip_address=self.router.session.client_ip,
        )
        yield rx.toast.success(
            "Login successful! Redirecting...",
            position="top-center",
            duration=1000,
        )
        if "manage_users" in self.permissions:
            yield rx.redirect(routes.ADMIN_ROUTE)
        else:
            yield rx.redirect(routes.OVERVIEW_ROUTE)

    @rx.event
    async def on_submit(self, form_data: dict):
        """Handle login form submission, authenticate user, and trigger post-login actions.

        Validates username/password, logs in the user, loads user data, and triggers post_login
        for redirection. Provides UI feedback via toasts and logs all actions to audit_logger.

        Args:
            form_data (dict): Form data containing 'username' and 'password'.

        Yields:
            rx.EventSpec: Events for UI updates, toasts, and post-login actions.

        Notes:
            - Sets is_submitting for UI feedback during processing.
            - Handles exceptions with detailed logging and user feedback.
            - Uses type(self).load_user_data() to align with AuthState.
        """  # noqa: E501
        self.error_message = ""
        self.is_submitting = True
        yield
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
                # Validate username and password
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
                    yield rx.toast.error(self.error_message)
                    return

                if not user or not user.verify(password):
                    self.error_message = "Invalid username or password"
                    audit_logger.info(
                        "login_failed",
                        username=username,
                        error=self.error_message,
                        ip_address=ip_address,
                    )
                    yield rx.toast.error(self.error_message)
                    return

                # Validate UserInfo
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
                        yield rx.toast.error(self.error_message)
                        return
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
                    yield rx.toast.error(self.error_message)
                    return

                # Perform login and load user data
                self._login(user.id, expiration_delta=timedelta(days=7))
                yield type(self).load_user_data()
                yield type(self).post_login(user)

        except Exception as e:
            self.error_message = "An unexpected error occurred. Please try again."
            audit_logger.error(
                "login_failed_unexpected",
                username=username,
                error=str(e),
                ip_address=ip_address,
                exception_type=type(e).__name__,
            )
            yield rx.toast.error(self.error_message)

        finally:
            self.is_submitting = False
            audit_logger.info(
                "http_response",
                method="POST",
                url=self.router.page.raw_path,
                user_id=user.id
                if "user" in locals() and self.is_authenticated
                else None,
                username=username,
                ip_address=ip_address,
                status_code=200 if self.is_authenticated else 401,
            )
