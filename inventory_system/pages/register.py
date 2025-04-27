import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.register_state import CustomRegisterState

from ..templates import template


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
                        "background": f"linear-gradient(45deg, {rx.color('purple', 10)}"
                        ", {rx.color('purple', 8)})",
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
                rx.hstack(
                    rx.text("ID", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
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
                rx.hstack(  # Use hstack for label and asterisk
                    rx.text("Username", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
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
                rx.hstack(
                    rx.text("Email", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
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
                rx.hstack(
                    rx.text("Password", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
                    spacing="1",
                ),
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
                rx.hstack(
                    rx.text(
                        "Confirm Password", weight="bold", color=rx.color("gray", 12)
                    ),
                    rx.text("*", color="red"),  # Add asterisk
                    spacing="1",
                ),
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
                    "background": f"linear-gradient(45deg, {rx.color('purple', 8)}"
                    ", {rx.color('purple', 10)})",
                    "_hover": {
                        "background": f"linear-gradient(45deg, {rx.color('purple', 9)}"
                        ", {rx.color('purple', 11)})",
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
            min_width=["90%", "80%", "400px"],
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
    """Render the registration page with a fade-in transition."""
    return rx.center(
        rx.card(
            register_form(),
            width="100%",  # Ensure the card takes full width of its container
            max_width=[
                "90%",
                "80%",
                "500px",
            ],  # Responsive max_width: 90% on small, 80% on medium, 500px on large
            padding=[
                "1em",
                "1.5em",
                "2em",
            ],  # Responsive padding: smaller on small screens
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
        padding=["1em", "1.5em", "2em"],  # Responsive padding for the container
        width="100%",  # Ensure the container takes full viewport width
        max_width="100%",  # Prevent overflow by capping at 100%
        min_height="85vh",  # Use min_height to ensure the background fills the viewport
        align="center",
        justify="center",
        background=rx.color("gray", 2),
        _dark={"background": rx.color("gray", 11)},
        transition="opacity 0.5s ease-in-out",
        overflow="auto",  # Prevent content from stretching outside
        box_sizing="border-box",  # Ensure padding is included in width calculations
    )
