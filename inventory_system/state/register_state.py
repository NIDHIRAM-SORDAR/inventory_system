import asyncio
import json
import os

import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.models import UserInfo

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

    async def handle_registration_with_email(self, form_data):
        """Handle registration and create UserInfo entry with toast and delay."""
        self.registration_error = ""
        self.is_submitting = True

        try:
            # Validate user ID and email
            if not self.validate_user(form_data):
                self.registration_error = (
                    "Invalid ID or email. Please check your details."
                )
                self.is_submitting = False
                return

            # Proceed with registration
            self.handle_registration(form_data)
            if self.new_user_id >= 0:
                with rx.session() as session:
                    user_info = UserInfo(
                        email=form_data["email"],
                        user_id=self.new_user_id,
                        profile_picture=DEFAULT_PROFILE_PICTURE,
                    )
                    user_info.set_role()
                    session.add(user_info)
                    session.commit()
                    session.refresh(user_info)

                # Show success toast directly
                yield rx.toast.success(
                    "Registration successful! Redirecting to login...",
                    position="top-center",
                    duration=1000,
                )
                # Wait 1 second before redirecting
                await asyncio.sleep(1)
                self.registration_error = ""
                yield rx.redirect(routes.LOGIN_ROUTE)
            else:
                self.registration_error = (
                    reflex_local_auth.RegistrationState.error_message
                    | "Registration failed."
                )
                self.is_submitting = False

        except Exception as e:
            self.registration_error = "An unexpected error occurred. Please try again."
            print(f"Registration error: {str(e)}")  # Log for debugging
            self.is_submitting = False

        finally:
            self.is_submitting = False
