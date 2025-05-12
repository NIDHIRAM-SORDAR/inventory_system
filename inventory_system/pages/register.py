import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.register_state import CustomRegisterState

from ..templates import template


def register_error() -> rx.Component:
    """Render the registration error message with accessibility."""
    return rx.cond(
        CustomRegisterState.registration_error != "",
        rx.callout(
            CustomRegisterState.registration_error,
            icon="triangle_alert",
            color_scheme="red",
            role="alert",
            width="100%",
            transition="all 0.3s ease-in-out",
            aria_live="assertive",
        ),
    )


def register_form() -> rx.Component:
    """Render the registration form with validation and accessibility."""
    return rx.form(
        rx.vstack(
            rx.hstack(
                rx.icon("user_plus", size=32, color=rx.color("purple", 10)),
                rx.heading(
                    "Create an Account",
                    size="8",
                    color=rx.color("purple", 10),
                    style={
                        "background": f"linear-gradient(45deg, "
                        f"{rx.color('purple', 10)}, {rx.color('purple', 8)})",
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                ),
                align="center",
                spacing="3",
            ),
            register_error(),
            rx.vstack(
                rx.hstack(
                    rx.text("ID", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(rx.icon("hash", color=rx.color("purple", 8))),
                    name="id",
                    type="text",
                    placeholder="Enter your ID",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    aria_label="ID",
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
                    rx.text("Username", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(rx.icon("user", color=rx.color("purple", 8))),
                    name="username",
                    id="username",
                    type="text",
                    placeholder="Enter your username",
                    width="100%",
                    required=True,
                    pattern="[a-zA-Z0-9_]{4,20}",
                    title=(
                        "Username must be 4-20 characters, "
                        "alphanumeric with underscores"
                    ),
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
                    rx.text("Email", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(rx.icon("mail", color=rx.color("purple", 8))),
                    name="email",
                    type="email",
                    placeholder="Enter your email",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",
                    aria_label="Email",
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
                    min_length=8,
                    pattern='(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}',
                    title=(
                        "Password must be at least 8 characters, with uppercase, "
                        "lowercase, number, and special character"
                    ),
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
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Confirm Password", weight="bold", color=rx.color("gray", 12)
                    ),
                    rx.text("*", color="red"),
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(rx.icon("lock", color=rx.color("purple", 8))),
                    name="confirm_password",
                    type="password",
                    placeholder="Confirm your password",
                    width="100%",
                    required=True,
                    min_length=8,
                    variant="soft",
                    color_scheme="purple",
                    aria_label="Confirm Password",
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
                    CustomRegisterState.is_submitting,
                    rx.spinner(size="2"),
                    rx.text("Sign Up"),
                ),
                type="submit",
                width="100%",
                size="3",
                color_scheme="purple",
                variant="solid",
                disabled=CustomRegisterState.is_submitting,
                aria_busy=CustomRegisterState.is_submitting,
                style={
                    "background": f"linear-gradient(45deg, {rx.color('purple', 8)}, "
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
                rx.vstack(
                    rx.link(
                        rx.hstack(
                            rx.icon("log_in", size=16, color=rx.color("purple", 8)),
                            rx.text(
                                "Already have an account? Login here.",
                                color=rx.color("purple", 8),
                            ),
                            spacing="2",
                        ),
                        href=reflex_local_auth.routes.LOGIN_ROUTE,
                        _hover={"text_decoration": "underline"},
                    ),
                    rx.link(
                        rx.hstack(
                            rx.icon("building", size=16, color=rx.color("purple", 8)),
                            rx.text(
                                "Register as a supplier instead.",
                                color=rx.color("purple", 8),
                            ),
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
            min_width=["95%", "80%", "400px"],
        ),
        on_submit=CustomRegisterState.handle_registration_with_email,
        width="100%",
    )


@template(
    route=routes.REGISTER_ROUTE,
    title="Signup",
    show_nav=False,
    on_load=[
        CustomRegisterState.reset_form_state,
    ],
)
def register_page() -> rx.Component:
    """Render the registration page with responsive styling."""
    return rx.center(
        rx.card(
            register_form(),
            width="100%",
            max_width=["95%", "80%", "500px"],
            padding=["1em", "1.5em", "2em"],
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
        padding=["1em", "1.5em", "2em"],
        width="100%",
        max_width="100%",
        min_height="85vh",
        align="center",
        justify="center",
        background=rx.color("gray", 2),
        _dark={"background": rx.color("gray", 11)},
        transition="opacity 0.5s ease-in-out",
        overflow="auto",
        box_sizing="border-box",
    )
