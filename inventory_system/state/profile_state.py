# inventory_system/state/profile_state.py
import re

import reflex as rx
import reflex_local_auth
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.state.auth import AuthState


class ProfileState(AuthState):
    notifications: bool = True
    password_error: str = ""
    email_error: str = ""
    is_updating_email: bool = False  # New loading state
    is_updating_password: bool = False  # New loading state

    def _handle_error(
        self, error_type: str, error_message: str, previous_email: str = None
    ):
        """Handle errors with logging and UI feedback."""
        self.email_error = error_message if error_type == "email" else ""
        self.password_error = error_message if error_type == "password" else ""
        if previous_email is not None:
            self.email = previous_email
        audit_logger.error(
            f"{error_type}_update_failed",
            user_id=self.authenticated_user.id,
            username=self.authenticated_user.username,
            ip_address=self.router.session.client_ip,
            method="POST",
            url=self.router.page.raw_path,
            error=error_message,
        )
        return rx.toast.error(error_message, position="top-center")

    def _validate_password(self, new_password, confirm_password) -> bool:
        errors = []
        if not new_password:
            errors.append("Password cannot be empty")
        if len(new_password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", new_password):
            errors.append("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", new_password):
            errors.append("Password must contain a lowercase letter")
        if not re.search(r"[0-9]", new_password):
            errors.append("Password must contain a number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
            errors.append("Password must contain a special character")
        if new_password != confirm_password:
            errors.append("Passwords do not match")

        if errors:
            self.password_error = "; ".join(errors)
            return False
        return True

    def handle_password_change(self, form_data: dict):
        if not self.is_authenticated:
            return rx.redirect(routes.LOGIN_ROUTE)

        self.is_updating_password = True
        try:
            audit_logger.info(
                "password_change_request",
                user_id=self.authenticated_user.id,
                username=self.authenticated_user.username,
                ip_address=self.router.session.client_ip,
                method="POST",
                url=self.router.page.raw_path,
            )

            current_password = form_data["current_password"]
            new_password = form_data["new_password"]
            confirm_password = form_data["confirm_password"]

            if not self._validate_password(new_password, confirm_password):
                return self._handle_error("password", self.password_error)

            with rx.session() as session:
                user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.id == self.authenticated_user.id
                    )
                ).one()

                if not user.verify(current_password):
                    return self._handle_error(
                        "password", "Current password is incorrect"
                    )

                user.password_hash = reflex_local_auth.LocalUser.hash_password(
                    new_password
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            self.password_error = ""
            audit_logger.info(
                "password_change_success",
                user_id=self.authenticated_user.id,
                username=self.authenticated_user.username,
                ip_address=self.router.session.client_ip,
                method="POST",
                url=self.router.page.raw_path,
            )
            return rx.toast.success(
                "Password updated successfully", position="top-center"
            )
        finally:
            self.is_updating_password = False

    def toggle_notifications(self):
        self.set_notifications(not self.notifications)
        audit_logger.info(
            "notification_settings_updated",
            user_id=self.authenticated_user.id,
            username=self.authenticated_user.username,
            ip_address=self.router.session.client_ip,
            method="POST",
            url=self.router.page.raw_path,
            notifications_enabled=self.notifications,
        )

    def validate_email_input(self, email: str):
        self.user_email = email  # Update shared state
        if not email:
            self.email_error = "Email is required"
            return
        try:
            validate_email(email, check_deliverability=False)
            self.email_error = ""
        except EmailNotValidError as e:
            self.email_error = str(e)

    def handle_submit(self, form_data: dict):
        if not self.is_authenticated:
            return rx.redirect(routes.LOGIN_ROUTE)
        self.is_updating_email = True
        try:
            audit_logger.info(
                "profile_update_request",
                user_id=self.authenticated_user.id,
                username=self.authenticated_user.username,
                ip_address=self.router.session.client_ip,
                method="POST",
                url=self.router.page.raw_path,
                data=form_data,
            )
            email = form_data["email"]
            previous_email = self.user_email
            try:
                self.set_user_email(email)
            except ValueError as e:
                self.user_email = previous_email
                return self._handle_error("email", str(e), previous_email)
            audit_logger.info(
                "profile_update_success",
                user_id=self.authenticated_user.id,
                username=self.authenticated_user.username,
                ip_address=self.router.session.client_ip,
                method="POST",
                url=self.router.page.raw_path,
                old_email=previous_email,
                new_email=email,
            )
            return rx.toast.success(
                "Profile email updated successfully", position="top-center"
            )
        finally:
            self.is_updating_email = False

    @rx.var
    def user_roles(self) -> str:
        return (
            ", ".join(self.authenticated_user_info.get_roles())
            if self.authenticated_user_info and self.authenticated_user_info.get_roles()
            else "N/A"
        )
