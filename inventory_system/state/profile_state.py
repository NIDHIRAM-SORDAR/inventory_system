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

    def handle_submit(self, form_data: dict):
        if not self.is_authenticated:
            return rx.redirect(routes.LOGIN_ROUTE)

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

        # Validate email using email-validator
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            self.email_error = str(e)
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
            # Check if the email is already in use by another user
            existing_user = session.exec(
                select(UserInfo).where(
                    UserInfo.email == email,
                    UserInfo.user_id != self.authenticated_user.id,
                )
            ).one_or_none()
            if existing_user:
                self.email_error = "This email is already in use by another user"
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
                select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
            ).one_or_none()
            if user_info:
                user_info.email = email
                session.add(user_info)
            else:
                new_user_info = UserInfo(
                    user_id=self.authenticated_user.id,
                    email=email,
                    role="employee",
                )
                session.add(new_user_info)

            session.commit()

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

        # Log password change request
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
            audit_logger.error(
                "password_change_failed",
                user_id=self.authenticated_user.id,
                username=self.authenticated_user.username,
                ip_address=self.router.session.client_ip,
                method="POST",
                url=self.router.page.raw_path,
                error=self.password_error,
            )
            return

        with rx.session() as session:
            user = session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.id == self.authenticated_user.id
                )
            ).one()

            if not user.verify(current_password):
                self.password_error = "Current password is incorrect"
                audit_logger.error(
                    "password_change_failed",
                    user_id=self.authenticated_user.id,
                    username=self.authenticated_user.username,
                    ip_address=self.router.session.client_ip,
                    method="POST",
                    url=self.router.page.raw_path,
                    error=self.password_error,
                )
                return
            user.password_hash = reflex_local_auth.LocalUser.hash_password(new_password)
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
        return rx.toast.success("Password updated successfully", position="top-center")

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
