import asyncio
import json
import os
import re

import reflex as rx
import reflex_local_auth
from sqlmodel import select

from inventory_system import routes
from inventory_system.logging.logging import audit_logger
from inventory_system.models.user import UserInfo

from ..constants import DEFAULT_PROFILE_PICTURE

# Load user data from JSON file
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
    is_submitting: bool = False  # Added for loading state

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
        self, username, password, confirm_password
    ) -> bool:  # Returns True if valid, False otherwise
        """Override base validation to add specific constraints
        and only set error messages, not return DOM events."""

        self.registration_error = ""  # Use our custom error state var

        # --- Username Constraints ---
        if not username:
            self.registration_error = "Username cannot be empty"
            return False
        if len(username) < 4:
            self.registration_error = "Username must be at least 4 characters long"
            return False
        if len(username) > 20:
            self.registration_error = "Username cannot exceed 20 characters"
            return False
        # Example: Alphanumeric + underscore only
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            self.registration_error = (
                "Username can only contain letters, numbers, and underscores (_)"
            )
            return False
        # Uniqueness Check
        with rx.session() as session:
            existing_user = session.exec(
                select(reflex_local_auth.user.LocalUser).where(
                    reflex_local_auth.user.LocalUser.username == username
                )
            ).one_or_none()
        if existing_user is not None:
            self.registration_error = (
                f"Username {username} is already registered. Try a different name"
            )
            return False

        # --- Password Constraints ---
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
        # Example: Check for at least one special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            self.registration_error = "Password must contain a special character"
            return False

        # --- Confirm Password Check ---
        if password != confirm_password:
            self.registration_error = "Passwords do not match"
            return False

        # If all custom checks pass
        return True  # Indicate validation success

    async def handle_registration_with_email(self, form_data):
        """Handle registration and create UserInfo entry with toast and delay."""
        self.registration_error = ""
        self.error_message = ""  # Clear parent error message too initially
        self.is_submitting = True
        self.new_user_id = -1  # Ensure reset

        username = form_data.get("username", "N/A")
        email = form_data.get("email", "N/A")
        submitted_id = form_data.get("id", "N/A")
        ip_address = self.router.session.client_ip

        audit_logger.info(  # Log attempt
            "attempt_registration",
            username=username,
            email=email,
            submitted_id=submitted_id,
            ip_address=ip_address,
        )

        try:
            # 1. Custom Validation
            if not self.validate_user(form_data):
                self.registration_error = (
                    "Invalid ID or email. Please check your details."
                )
                # Log is handled inside validate_user
                self.is_submitting = False
                return

            # 2. Proceed with base registration (calls _validate_fields -> sets self.error_message on fail)
            # Store the result which might contain event specs (though we had issues with them)
            self.handle_registration(form_data)

            # **** CHECK FOR PARENT ERROR MESSAGE ****
            # If the base handler failed validation, it would have set self.error_message
            if self.error_message:
                # Copy the parent's error message to the child's variable
                self.registration_error = self.error_message
                self.is_submitting = False
                audit_logger.warning(  # Log base validation failure
                    "registration_validation_failed",
                    reason=self.registration_error,
                    username=username,
                    ip_address=ip_address,
                )
                # If validation_result contained focus/value events, yielding them caused errors.
                # So, we just return here, relying on the registration_error display.
                return

            # 3. Check if LocalUser was created successfully
            if self.new_user_id >= 0:
                # **** Log LocalUser creation success (part 1 of registration) ****
                audit_logger.info(
                    "registration_localuser_created",
                    username=username,
                    user_id=self.new_user_id,
                    ip_address=ip_address,
                )
                # 4. Create UserInfo
                with rx.session() as session:
                    try:
                        # ... (Check for existing UserInfo - good practice)
                        existing_info = session.exec(
                            select(UserInfo).where(UserInfo.user_id == self.new_user_id)
                        ).first()
                        if existing_info:
                            audit_logger.warning(
                                "registration_warning",
                                reason="UserInfo already exists",
                                username=username,
                                user_id=self.new_user_id,
                                ip_address=ip_address,
                            )

                        user_info = UserInfo(
                            email=form_data["email"],
                            user_id=self.new_user_id,
                            profile_picture=DEFAULT_PROFILE_PICTURE,
                        )
                        user_info.set_role()
                        session.add(user_info)
                        session.commit()
                        session.refresh(user_info)

                        # **** Log full registration success ****
                        audit_logger.info(
                            "success_registration",
                            username=username,
                            email=email,
                            user_id=self.new_user_id,
                            user_info_id=user_info.id,
                            role=user_info.role,
                            ip_address=ip_address,
                        )

                        # 5. Show success feedback and redirect (async part)
                        self.registration_error = ""
                        yield rx.toast.success(
                            "Registration successful! Redirecting to login...",
                            position="top-center",
                            duration=1000,  # Using 2 seconds delay
                        )
                        await asyncio.sleep(2)  # Using 2 seconds delay
                        yield rx.redirect(routes.LOGIN_ROUTE)
                        # No need to explicitly set success=False here if UI doesn't depend on it

                    except Exception as db_error:
                        # Error during UserInfo creation
                        self.registration_error = "Registration partially failed: Could not save user details."
                        audit_logger.error(
                            "registration_failed",
                            reason="Error creating UserInfo",
                            username=username,
                            user_id=self.new_user_id,
                            error=str(db_error),
                            ip_address=ip_address,
                        )
                        session.rollback()
                        # Fall through to finally block

            else:
                # Base registration validation passed, but LocalUser wasn't created (self.new_user_id < 0)
                # self.error_message might have been set by _register_user if it failed,
                # otherwise provide a generic message.
                self.registration_error = (
                    self.error_message
                    or "Registration failed: Could not create user account."
                )
                audit_logger.error(
                    "registration_failed",
                    reason=self.registration_error,
                    username=username,
                    ip_address=ip_address,
                )
                # Fall through to finally block

        except Exception as e:
            self.registration_error = "An unexpected error occurred. Please try again."
            print(f"Registration error: {str(e)}")  # Keep for debugging
            audit_logger.critical(  # Log unexpected errors
                "registration_failed_unexpected",
                reason=str(e),
                username=username,
                email=email,
                submitted_id=submitted_id,
                ip_address=ip_address,
                exception_type=type(e).__name__,
            )
            # Fall through to finally block

        finally:
            self.is_submitting = False  # Ensure this always runs
