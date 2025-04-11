import reflex as rx
import reflex_local_auth
from inventory_system.models import UserInfo
import json
import os
from ..templates import template
from inventory_system import routes
from inventory_system.state.login_state import LoginState
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
    registration_error: str = ""
    is_submitting: bool = False  # Added for loading state

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
                self.registration_error = "Invalid ID or email. Please check your details."
                self.is_submitting = False
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
            transition="all 0.3s ease-in-out",
        ),
    )


def register_form() -> rx.Component:
    """Render the registration form with styling similar to supplier registration."""
    return rx.form(
        rx.vstack(
            # Enhanced heading with icon and gradient text
            rx.hstack(
                rx.icon("user_plus", size=32, color=rx.color("purple", 10)),
                rx.heading(
                    "Create an Account",
                    size="8",  # Using string number as per Reflex convention
                    color=rx.color("purple", 10),
                    style={
                        "background": f"linear-gradient(45deg, {rx.color('purple', 10)}, {rx.color('purple', 8)})",
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                ),
                align="center",
                spacing="3",
            ),
            # Error message with animation
            register_error(),
            # ID Input with Icon
            rx.vstack(
                rx.text("ID", weight="bold", color=rx.color("gray", 12)),
                rx.input(
                    rx.input.slot(rx.icon("hash", color=rx.color("purple", 8))),
                    name="id",
                    type="text",
                    placeholder="Enter your ID",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Username Input with Icon
            rx.vstack(
                rx.text("Username", weight="bold", color=rx.color("gray", 12)),
                rx.input(
                    rx.input.slot(rx.icon("user", color=rx.color("purple", 8))),
                    name="username",
                    type="text",
                    placeholder="Enter your username",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Email Input with Icon
            rx.vstack(
                rx.text("Email", weight="bold", color=rx.color("gray", 12)),
                rx.input(
                    rx.input.slot(rx.icon("mail", color=rx.color("purple", 8))),
                    name="email",
                    type="email",
                    placeholder="Enter your email",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Password Input with Icon
            rx.vstack(
                rx.text("Password", weight="bold", color=rx.color("gray", 12)),
                rx.input(
                    rx.input.slot(rx.icon("lock", color=rx.color("purple", 8))),
                    name="password",
                    type="password",
                    placeholder="Enter your password",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Confirm Password Input with Icon
            rx.vstack(
                rx.text("Confirm Password", weight="bold", color=rx.color("gray", 12)),
                rx.input(
                    rx.input.slot(rx.icon("lock", color=rx.color("purple", 8))),
                    name="confirm_password",
                    type="password",
                    placeholder="Confirm your password",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Sign Up Button with Loading State
            rx.button(
                rx.cond(
                    CustomRegisterState.is_submitting,
                    rx.spinner(size="2"),
                    rx.text("Sign Up"),
                ),
                type="submit",
                width="100%",
                size="3",
                color_scheme="purple",
                variant="solid",
                style={
                    "background": f"linear-gradient(45deg, {rx.color('purple', 8)}, {rx.color('purple', 10)})",
                    "_hover": {
                        "background": f"linear-gradient(45deg, {rx.color('purple', 9)}, {rx.color('purple', 11)})",
                    },
                    "transition": "all 0.3s ease",
                },
            ),
            # Links for Login and Supplier Registration
            rx.center(
                rx.vstack(
                    rx.link(
                        rx.hstack(
                            rx.icon("log_in", size=16, color=rx.color("purple", 8)),
                            rx.text("Already have an account? Login here.", color=rx.color("purple", 8)),
                            spacing="2",
                        ),
                        href=reflex_local_auth.routes.LOGIN_ROUTE,
                        _hover={"text_decoration": "underline"},
                    ),
                    rx.link(
                        rx.hstack(
                            rx.icon("building", size=16, color=rx.color("purple", 8)),
                            rx.text("Register as a supplier instead.", color=rx.color("purple", 8)),
                            spacing="2",
                        ),
                        href=routes.SUPPLIER_REGISTER_ROUTE,
                        _hover={"text_decoration": "underline"},
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
            ),
            spacing="5",
            width="100%",
            min_width=["90%", "80%", "400px"],
        ),
        on_submit=CustomRegisterState.handle_registration_with_email,
        width="100%",
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
                rx.link(
                    rx.hstack(
                        rx.icon("log_in", size=16, color=rx.color("purple", 8)),
                        rx.text("Go to Login", color=rx.color("purple", 8)),
                        spacing="2",
                    ),
                    href=reflex_local_auth.routes.LOGIN_ROUTE,
                    _hover={"text_decoration": "underline"},
                ),
                spacing="4",
                align="center",
            ),
            rx.card(
                register_form(),
                width=["90%", "80%", "500px"],
                padding="2em",
                box_shadow="0 8px 32px rgba(0, 0, 0, 0.1)",
                border_radius="lg",
                background=rx.color("gray", 1),
                _dark={"background": rx.color("gray", 12)},
                transition="all 0.3s ease",
                _hover={
                    "box_shadow": "0 12px 48px rgba(0, 0, 0, 0.15)",
                    "transform": "translateY(-4px)",
                },
            ),
        ),
        padding_top="2em",
        width="100%",
        height="85vh",
        align="center",
        justify="center",
        background=rx.color("gray", 2),
        _dark={"background": rx.color("gray", 11)},
        opacity=rx.cond(LoginState.show_login, "1.0", "0.0"),
        transition="opacity 0.5s ease-in-out",
    )