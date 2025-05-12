import json
import os
import re

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import Role, UserInfo

from ..constants import DEFAULT_PROFILE_PICTURE

# Load user data from JSON files
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
USER_DATA_FILE = os.path.join(PROJECT_ROOT, "user_data.json")


def load_user_data():
    """Load user data from JSON file."""
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


class CustomRegisterState(reflex_local_auth.RegistrationState):
    registration_error: str = ""
    is_submitting: bool = False

    def reset_form_state(self):
        """Reset form state on page load."""
        self.registration_error = ""
        self.is_submitting = False

    def validate_user(self, form_data):
        """Validate user ID and email against user_data.json."""
        user_data = load_user_data()
        user_id = form_data.get("id")
        email = form_data.get("email")
        for user in user_data:
            if (
                str(user["ID"]) == str(user_id)
                and user["Email"].lower() == email.lower()
            ):
                return True
        return False

    def _validate_fields(
        self, username: str, password: str, confirm_password: str
    ) -> bool:
        """Validate username, password, and confirm password."""
        self.registration_error = ""

        # Username validation
        if not username:
            self.registration_error = "Username cannot be empty"
            return False
        if len(username) < 4 or len(username) > 20:
            self.registration_error = "Username must be 4-20 characters long"
            return False
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            self.registration_error = (
                "Username can only contain letters, numbers, and underscores"
            )
            return False
        with rx.session() as session:
            if session.exec(
                select(reflex_local_auth.LocalUser).where(
                    reflex_local_auth.LocalUser.username == username
                )
            ).one_or_none():
                self.registration_error = f"Username {username} is already taken"
                return False

        # Password validation
        if not password:
            self.registration_error = "Password cannot be empty"
            return False
        if len(password) < 8:
            self.registration_error = "Password must be at least 8 characters long"
            return False
        if not re.search(r"[A-Z]", password):
            self.registration_error = "Password must contain an uppercase letter"
            return False
        if not re.search(r"[a-z]", password):
            self.registration_error = "Password must contain a lowercase letter"
            return False
        if not re.search(r"[0-9]", password):
            self.registration_error = "Password must contain a number"
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            self.registration_error = "Password must contain a special character"
            return False

        # Confirm password
        if password != confirm_password:
            self.registration_error = "Passwords do not match"
            return False

        return True

    @rx.event
    async def handle_registration_with_email(self, form_data: dict):
        """Handle registration, create UserInfo, assign roles, and auto-login."""
        self.registration_error = ""
        self.is_submitting = True
        self.new_user_id = -1

        username = form_data.get("username", "N/A")
        password = form_data.get("password", "N/A")
        confirm_password = form_data.get("confirm_password", "N/A")
        email = form_data.get("email", "N/A")
        submitted_id = form_data.get("id", "N/A")
        ip_address = self.router.session.client_ip

        audit_logger.info(
            "attempt_registration",
            username=username,
            email=email,
            submitted_id=submitted_id,
            ip_address=ip_address,
        )

        try:
            # Validate ID/email against user_data.json
            if not self.validate_user(form_data):
                self.registration_error = (
                    "Invalid ID or email. Please check your details."
                )
                audit_logger.warning(
                    "registration_prevalidation_failed",
                    reason=self.registration_error,
                    username=username,
                    email=email,
                    submitted_id=submitted_id,
                    ip_address=ip_address,
                )
                yield rx.toast.error(self.registration_error)

            # Validate fields
            if not self._validate_fields(username, password, confirm_password):
                audit_logger.warning(
                    "registration_validation_failed",
                    reason=self.registration_error,
                    username=username,
                    ip_address=ip_address,
                )
                yield rx.toast.error(self.registration_error)

            with rx.session() as session:
                try:
                    # Register user
                    self._register_user(username, password)
                    if self.new_user_id < 0:
                        self.registration_error = (
                            "Registration failed: Could not create user account."
                        )
                        audit_logger.error(
                            "registration_failed_localuser",
                            reason=self.registration_error,
                            username=username,
                            ip_address=ip_address,
                        )
                        yield rx.toast.error(self.registration_error)
                        session.rollback()

                    audit_logger.info(
                        "registration_localuser_created",
                        username=username,
                        user_id=self.new_user_id,
                        ip_address=ip_address,
                    )

                    # Check for existing UserInfo
                    existing_info = session.exec(
                        select(UserInfo).where(UserInfo.user_id == self.new_user_id)
                    ).one_or_none()
                    if existing_info:
                        self.registration_error = (
                            "Registration failed: User profile already exists."
                        )
                        audit_logger.error(
                            "registration_failed_userinfo_exists",
                            reason=self.registration_error,
                            username=username,
                            user_id=self.new_user_id,
                            existing_user_info_id=existing_info.id,
                            ip_address=ip_address,
                        )
                        yield rx.toast.error(self.registration_error)
                        session.rollback()

                    # Create UserInfo
                    user_info = UserInfo(
                        email=email,
                        user_id=self.new_user_id,
                        profile_picture=DEFAULT_PROFILE_PICTURE,
                    )
                    session.add(user_info)
                    session.flush()

                    # Validate and assign employee role
                    employee_role = session.exec(
                        select(Role).where(Role.name == "employee", Role.is_active)
                    ).one_or_none()
                    if not employee_role:
                        self.registration_error = (
                            "Registration failed: Employee role not found."
                        )
                        audit_logger.error(
                            "registration_failed_role_missing",
                            reason=self.registration_error,
                            username=username,
                            user_id=self.new_user_id,
                            role="employee",
                            ip_address=ip_address,
                        )
                        yield rx.toast.error(self.registration_error)
                        session.rollback()

                    try:
                        user_info.set_roles(["employee"], session)
                    except ValueError as role_error:
                        self.registration_error = (
                            f"Registration failed: Could not assign employee role: "
                            f"{str(role_error)}"
                        )
                        audit_logger.error(
                            "registration_failed_role_assignment",
                            reason=self.registration_error,
                            username=username,
                            user_id=self.new_user_id,
                            role="employee",
                            error=str(role_error),
                            ip_address=ip_address,
                        )
                        yield rx.toast.error(self.registration_error)
                        session.rollback()

                    user_info_id = user_info.id
                    session.commit()

                    audit_logger.info(
                        "userinfo_created",
                        username=username,
                        user_id=self.new_user_id,
                        user_info_id=user_info_id,
                        ip_address=ip_address,
                    )

                    audit_logger.info(
                        "success_registration",
                        username=username,
                        email=email,
                        user_id=self.new_user_id,
                        user_info_id=user_info_id,
                        role=user_info.get_roles(),
                        ip_address=ip_address,
                    )

                    # Show success toast
                    yield rx.toast.success(
                        "Registration successful! Redirecting...",
                        position="top-center",
                        duration=1000,
                    )

                    yield rx.redirect(routes.LOGIN_ROUTE)

                except Exception as db_error:
                    self.registration_error = (
                        "Registration failed: Could not save user details."
                    )
                    audit_logger.error(
                        "registration_failed_userinfo",
                        reason=str(db_error),
                        username=username,
                        user_id=self.new_user_id,
                        error=str(db_error),
                        ip_address=ip_address,
                    )
                    session.rollback()
                    yield rx.toast.error(self.registration_error)

        except Exception as e:
            self.registration_error = "An unexpected error occurred. Please try again."
            audit_logger.critical(
                "registration_failed_unexpected",
                reason=str(e),
                username=username,
                email=email,
                submitted_id=submitted_id,
                ip_address=ip_address,
                exception_type=type(e).__name__,
            )
            yield rx.toast.error(self.registration_error)

        finally:
            self.is_submitting = False
