import reflex as rx
import reflex_local_auth
from sqlmodel import select
from ..templates import template
from ..models import UserInfo
from ..state import AuthState  # Import your custom AuthState
from inventory_system import routes
from inventory_system.state.login_state import (
    LoginState,
)  # Import LoginState for transition


import reflex as rx
import reflex_local_auth
from inventory_system.templates.template import template
from inventory_system import routes
from sqlmodel import select
from inventory_system.models import UserInfo  # Assuming UserInfo is your model for user roles


class CustomLoginState(AuthState):
    """Custom login state to redirect based on user role."""
    error_message: str = ""
    is_submitting: bool = False

    async def on_submit(self, form_data: dict):
        """Handle login form submission and redirect based on role."""
        self.error_message = ""
        self.is_submitting = True

        try:
            with rx.session() as session:
                user = session.exec(
                    select(reflex_local_auth.LocalUser).where(
                        reflex_local_auth.LocalUser.username == form_data["username"]
                    )
                ).one_or_none()

                if not user or not user.verify(form_data["password"]):
                    self.error_message = "Invalid username or password"
                    self.is_submitting = False
                    return

                # Explicitly call our custom _login method
                self._login(user.id)

                # Check user role and redirect
                user_info = session.exec(
                    select(UserInfo).where(UserInfo.user_id == self.authenticated_user.id)
                ).one_or_none()
                if user_info and user_info.is_admin:
                    return rx.redirect(routes.ADMIN_MGMT)
                return rx.redirect(routes.OVERVIEW_ROUTE)

        finally:
            self.is_submitting = False  # Ensure is_submitting is reset even if an error occurs


def login_error() -> rx.Component:
    """Render the login error message."""
    return rx.cond(
        CustomLoginState.error_message != "",
        rx.callout(
            CustomLoginState.error_message,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
            transition="all 0.3s ease-in-out",
        ),
    )


def login_form() -> rx.Component:
    """Render the login form with styling similar to supplier registration."""
    return rx.form(
        rx.vstack(
            # Enhanced heading with icon and gradient text
            rx.hstack(
                rx.icon("log_in", size=32, color=rx.color("purple", 10)),
                rx.heading(
                    "Login",
                    size="8",
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
            login_error(),
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
            # Login Button with Loading State
            rx.button(
                rx.cond(
                    CustomLoginState.is_submitting,
                    rx.spinner(size="2"),
                    rx.text("Login"),
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
            # Register Link with Icon
            rx.center(
                rx.link(
                    rx.hstack(
                        rx.icon("user_plus", size=16, color=rx.color("purple", 8)),
                        rx.text("Don't have an account? Register here.", color=rx.color("purple", 8)),
                        spacing="2",
                    ),
                    href=reflex_local_auth.routes.REGISTER_ROUTE,
                    _hover={"text_decoration": "underline"},
                ),
                width="100%",
            ),
            spacing="5",
            width="100%",
            min_width=["90%", "80%", "400px"],
        ),
        on_submit=CustomLoginState.on_submit,
        width="100%",
    )


@template(
    route=routes.LOGIN_ROUTE,
    title="Login",
    show_nav=False,
    on_load=[LoginState.reset_transition, LoginState.start_transition],
)
def login_page() -> rx.Component:
    """Render the login page with a fade-in transition."""
    return rx.center(
        rx.card(
            login_form(),
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