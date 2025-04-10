import reflex as rx
import reflex_local_auth
from inventory_system.models import UserInfo
import json
import os
from ..templates import template
from inventory_system import routes
from inventory_system.state.login_state import (
    LoginState,
)  # Import LoginState for transition
import asyncio
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
    registration_error: str = ""  # Custom message for validation errors only

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
            # Wait 2 seconds before redirecting
            await asyncio.sleep(1)
            self.registration_error = ""  # Clear any previous error
            yield rx.redirect(routes.LOGIN_ROUTE)
        else:
            self.registration_error = (
                reflex_local_auth.RegistrationState.error_message
                | "Registration failed."
            )


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
            rx.heading("Create an Account", size="6"),
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
            spacing="1",
        ),
        on_submit=CustomRegisterState.handle_registration_with_email,
    )


@template(
    route=routes.REGISTER_ROUTE,
    title="Signup",
    show_nav=False,
    on_load=[LoginState.reset_transition, LoginState.start_transition],
)
def register_page() -> rx.Component:
    """Render the registration page with a fade-in transition."""
    return rx.center(
        rx.cond(
            reflex_local_auth.RegistrationState.success,
            rx.vstack(
                rx.text("Registration successful!"),
                rx.link("Go to Login", href=reflex_local_auth.routes.LOGIN_ROUTE),
            ),
            rx.card(
                register_form(),
                width="100%",
                max_width="400px",
                background="#2D3748",
                border="1px solid #4A5568",
                border_radius="12px",
                padding="10px",
                box_shadow="0 4px 12px rgba(0, 0, 0, 0.3)",
            ),
        ),
        padding="10px",
        min_height="85vh",
        width="100%",
        max_width="90%",
        align="center",
        justify="center",
        overflow="hidden",
        opacity=rx.cond(LoginState.show_login, "1.0", "0.0"),
        transition="opacity 0.5s ease-in-out",
        background="linear-gradient(135deg, #1A202C, #2D3748)",
    )
