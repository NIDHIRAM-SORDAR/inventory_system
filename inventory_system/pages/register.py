# inventory_system/pages/register.py
import reflex as rx
import reflex_local_auth
from inventory_system.models import UserInfo
import json
import os
from ..templates import template

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
    registration_error: str = ""  # Custom error message for validation

    def validate_user(self, form_data):
        """Validate user ID and email against user_data.json."""
        user_data = load_user_data()
        user_id = form_data.get("id")
        email = form_data.get("email")

        for user in user_data:
            if str(user["ID"]) == str(user_id) and user["Email"].lower() == email.lower():
                return True
        return False

    def handle_registration_with_email(self, form_data):
        """Handle registration and create UserInfo entry."""
        # Validate user ID and email
        if not self.validate_user(form_data):
            self.registration_error = "Invalid ID or email. Please check your details."
            return

        # Proceed with registration
        registration_result = self.handle_registration(form_data)
        if self.new_user_id >= 0:
            with rx.session() as session:
                user_info = UserInfo(
                        email=form_data["email"],
                        user_id=self.new_user_id,
                    )
                user_info.set_role()
                session.add(user_info)
                session.commit()
                session.refresh(user_info)

        else:
            self.registration_error = reflex_local_auth.RegistrationState.error_message or "Registration failed."
        return registration_result

def register_error() -> rx.Component:
    """Render the registration error message."""
    return rx.cond(
        CustomRegisterState.registration_error != "",
        rx.callout(
            CustomRegisterState.registration_error,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
        ),
    )

def register_form() -> rx.Component:
    """Render the registration form."""
    return rx.form(
        rx.vstack(
            rx.heading("Create an Account", size="7"),
            register_error(),
            rx.text("ID"),
            rx.input(name="id", width="100%"),
            rx.text("Username"),
            rx.input(name="username", width="100%"),
            rx.text("Email"),
            rx.input(name="email", width="100%"),
            rx.text("Password"),
            rx.input(name="password", type="password", width="100%"),
            rx.text("Confirm Password"),
            rx.input(name="confirm_password", type="password", width="100%"),
            rx.button("Sign Up", width="100%"),
            rx.center(
                rx.link("Login", href=reflex_local_auth.routes.LOGIN_ROUTE),
                width="100%",
            ),
            min_width="300px",
        ),
        on_submit=CustomRegisterState.handle_registration_with_email,
    )
@template(route="/register", title="Signin")
def register_page() -> rx.Component:
    """Render the registration page."""
    return rx.center(
        rx.cond(
            reflex_local_auth.RegistrationState.success,
            rx.vstack(
                rx.text("Registration successful!"),
                rx.link("Go to Login", href=reflex_local_auth.routes.LOGIN_ROUTE),
            ),
            rx.card(register_form()),
        ),
        padding_top="2em",
    )