import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.login_state import CustomLoginState
from inventory_system.templates import template


def login_error() -> rx.Component:
    """Render the login error message with accessibility."""
    return rx.cond(
        CustomLoginState.error_message != "",
        rx.callout(
            CustomLoginState.error_message,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
            transition="all 0.3s ease-in-out",
            aria_live="assertive",
        ),
    )


def login_form() -> rx.Component:
    """Render the login form with validation and accessibility."""
    return rx.form(
        rx.vstack(
            rx.hstack(
                rx.icon("log_in", size=32, color=rx.color("purple", 10)),
                rx.heading(
                    "Login",
                    size="8",
                    color=rx.color("purple", 10),
                    style={
                        "background": f"linear-gradient(45deg, "
                        f"{rx.color('purple', 10)}, "
                        f"{rx.color('purple', 8)})",
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                ),
                align="center",
                spacing="3",
            ),
            login_error(),
            rx.vstack(
                rx.hstack(
                    rx.text("Username", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(rx.icon("user", color=rx.color("purple", 8))),
                    name="username",
                    type="text",
                    placeholder="Enter your username",
                    width="100%",
                    required=True,
                    pattern="[a-zA-Z0-9_]+",  # No spaces, alphanumeric
                    title="Username must be alphanumeric with underscores",
                    variant="soft",
                    color_scheme="purple",
                    aria_label="Username",
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
            rx.vstack(
                rx.hstack(
                    rx.text("Password", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(rx.icon("lock", color=rx.color("purple", 8))),
                    name="password",
                    type="password",
                    placeholder="Enter your password",
                    width="100%",
                    required=True,
                    min_length=8,  # Minimum password length
                    variant="soft",
                    color_scheme="purple",
                    aria_label="Password",
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
            rx.button(
                rx.cond(
                    CustomLoginState.is_submitting,
                    rx.spinner(),
                    rx.text("Login"),
                ),
                type="submit",
                width="100%",
                size="3",
                color_scheme="purple",
                variant="solid",
                disabled=CustomLoginState.is_submitting,
                aria_busy=CustomLoginState.is_submitting,
                style={
                    "background": f"linear-gradient(45deg, "
                    f"{rx.color('purple', 8)}, "
                    f"{rx.color('purple', 10)})",
                    "_hover": {
                        "background": f"linear-gradient(45deg, "
                        f"{rx.color('purple', 9)}, "
                        f"{rx.color('purple', 11)})",
                    },
                    "transition": "all 0.3s ease",
                },
            ),
            rx.center(
                rx.link(
                    rx.hstack(
                        rx.icon("user_plus", size=16, color=rx.color("purple", 8)),
                        rx.text(
                            "Don't have an account? Register here.",
                            color=rx.color("purple", 8),
                        ),
                        spacing="2",
                    ),
                    href=reflex_local_auth.routes.REGISTER_ROUTE,
                    _hover={"text_decoration": "underline"},
                ),
                width="100%",
            ),
            spacing="5",
            width="100%",
            min_width=["100%", "80%", "400px"],  # Responsive breakpoints
        ),
        on_submit=CustomLoginState.on_submit,
        width="100%",
    )


@template(
    route=routes.LOGIN_ROUTE,
    title="Login",
    show_nav=False,
    on_load=[
        CustomLoginState.reset_form_state,
        # CustomLoginState.route_calc,
    ],
)
def login_page() -> rx.Component:
    """Render the login page with responsive styling."""
    return rx.center(
        rx.card(
            login_form(),
            width=["95%", "80%", "500px"],
            max_width="90vw",
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
        transition="opacity 0.5s ease-in-out",
    )
