# inventory_system/state/profile_state.py
import re

import reflex as rx
import reflex_local_auth
from email_validator import EmailNotValidError, validate_email
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import UserInfo
from inventory_system.state.auth import AuthState


class ProfileState(AuthState):
    notifications: bool = True
    password_error: str = ""
    email_error: str = ""

    email: str = ""
    is_updating_email: bool = False  # New loading state
    is_updating_password: bool = False  # New loading state

    def get_email(self) -> str:
        """Initialize email state on page load."""
        if self.is_authenticated and self.authenticated_user_info:
            self.email = self.authenticated_user_info.email

    def handle_submit(self, form_data: dict):
        if not self.is_authenticated:
            return rx.redirect(routes.LOGIN_ROUTE)

        self.is_updating_email = True  # Set loading state
        try:
            # Log profile update request
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
            previous_email = self.email
            self.email = email  # Optimistic update

            # Validate email using email-validator
            try:
                validate_email(email, check_deliverability=False)
            except EmailNotValidError as e:
                self.email_error = str(e)
                self.email = previous_email
                audit_logger.error(
                    "profile_update_failed",
                    user_id=self.authenticated_user.id,
                    username=self.authenticated_user.username,
                    ip_address=self.router.session.client_ip,
                    method="POST",
                    url=self.router.page.raw_path,
                    error=self.email_error,
                )
                return rx.toast.error(self.email_error, position="top-center")

            with rx.session() as session:
                existing_user = session.exec(
                    select(UserInfo).where(
                        UserInfo.email == email,
                        UserInfo.user_id != self.authenticated_user.id,
                    )
                ).one_or_none()
                if existing_user:
                    self.email_error = "This email is already in use by another user"
                    self.email = previous_email
                    audit_logger.error(
                        "profile_update_failed",
                        user_id=self.authenticated_user.id,
                        username=self.authenticated_user.username,
                        ip_address=self.router.session.client_ip,
                        method="POST",
                        url=self.router.page.raw_path,
                        error=self.email_error,
                    )
                    return rx.toast.error(self.email_error, position="top-center")

                user_info = session.exec(
                    select(UserInfo).where(
                        UserInfo.user_id == self.authenticated_user.id
                    )
                ).one_or_none()
                if user_info:
                    user_info.email = email
                    session.add(user_info)
                    session.commit()
                    session.refresh(user_info)
                else:
                    self.email = previous_email
                    self.email_error = "Failed to update email"
                    audit_logger.error(
                        "profile_update_failed",
                        user_id=self.authenticated_user.id,
                        username=self.authenticated_user.username,
                        ip_address=self.router.session.client_ip,
                        method="POST",
                        url=self.router.page.raw_path,
                        error=self.email_error,
                    )
                    return rx.toast.error(self.email_error, position="top-center")

            # Log profile update success
            audit_logger.info(
                "profile_update_success",
                user_id=self.authenticated_user.id,
                username=self.authenticated_user.username,
                ip_address=self.router.session.client_ip,
                method="POST",
                url=self.router.page.raw_path,
            )

            return rx.toast.success(
                "Profile email updated successfully", position="top-center"
            )
        finally:
            self.is_updating_email = False  # Reset loading state

    def _validate_password(self, new_password, confirm_password) -> bool:
        # --- Password Constraints ---
        if not new_password:
            self.password_error = "Password cannot be empty"
            return False
        if len(new_password) < 8:
            self.password_error = "Password must be at least 8 characters long"
            return False
        if not re.search(r"[A-Z]", new_password):
            self.password_error = "Password must contain an uppercase letter"
            return False
        if not re.search(r"[a-z]", new_password):
            self.password_error = "Password must contain a lowercase letter"
            return False
        if not re.search(r"[0-9]", new_password):
            self.password_error = "Password must contain a number"
            return False
        # Example: Check for at least one special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
            self.password_error = "Password must contain a special character"
            return False

        # --- Confirm Password Check ---
        if new_password != confirm_password:
            self.password_error = "Passwords do not match"
            return False

        # If all custom checks pass
        return True  # Indicate validation success

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
