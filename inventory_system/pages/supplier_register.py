# inventory_system/pages/supplier_register.py

import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.supplier_registerstater import SupplierRegisterState
from inventory_system.templates.template import template


def supplier_registration_form() -> rx.Component:
    return rx.form(
        rx.vstack(
            # Enhanced heading with icon and gradient text
            rx.hstack(
                rx.icon(
                    "building", size=32, color=rx.color("purple", 10)
                ),  # Changed "accent" to "purple"
                rx.heading(
                    "Supplier Registration",
                    size="8",
                    color=rx.color("purple", 10),  # Changed "accent" to "purple"
                    style={
                        "background": (
                            f"linear-gradient(45deg, {rx.color('purple', 10)},"
                            f"{rx.color('purple', 8)})"  # Changed "accent" to "purple"
                        ),
                        # Changed "accent" to "purple"
                        "-webkit-background-clip": "text",
                        "-webkit-text-fill-color": "transparent",
                    },
                ),
                align="center",
                spacing="3",
            ),
            # Success and error messages with animation
            rx.cond(
                SupplierRegisterState.success_message != "",
                rx.callout(
                    SupplierRegisterState.success_message,
                    icon="circle-check",
                    color_scheme="green",
                    role="alert",
                    width="100%",
                    transition="all 0.3s ease-in-out",
                ),
            ),
            rx.cond(
                SupplierRegisterState.error_message != "",
                rx.callout(
                    SupplierRegisterState.error_message,
                    icon="triangle-alert",
                    color_scheme="red",
                    role="alert",
                    width="100%",
                    transition="all 0.3s ease-in-out",
                ),
            ),
            # Company Name Input with Icon
            rx.vstack(
                rx.hstack(
                    rx.text("Company Name", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(
                        rx.icon("building_2", color=rx.color("purple", 8))
                    ),  # Changed "accent" to "purple"
                    value=SupplierRegisterState.company_name,
                    on_change=SupplierRegisterState.set_company_name,
                    placeholder="Enter company name",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",  # Changed "accent" to "purple"
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        # Changed "accent" to "purple"
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            # Changed "accent" to "purple"
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                            # Changed "accent" to "purple"
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Replace the Description Input section
            rx.vstack(
                rx.hstack(
                    rx.text("Description", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
                    spacing="1",
                ),
                rx.hstack(
                    rx.icon("file_text", color=rx.color("purple", 8), size=24),
                    rx.text_area(
                        value=SupplierRegisterState.description,
                        on_change=SupplierRegisterState.set_description,
                        placeholder="Describe your company",
                        width="100%",
                        required=True,
                        variant="soft",
                        color_scheme="purple",
                        rows="4",
                        style={
                            "border": f"1px solid {rx.color('purple', 4)}",
                            "_focus": {
                                "border": f"2px solid {rx.color('purple', 6)}",
                                "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                            },
                        },
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="1",
                width="100%",
            ),
            # Contact Email Input with Icon
            rx.vstack(
                rx.hstack(
                    rx.text("Contact Email", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(
                        rx.icon("mail", color=rx.color("purple", 8))
                    ),  # Changed "accent" to "purple"
                    value=SupplierRegisterState.contact_email,
                    on_change=SupplierRegisterState.set_contact_email,
                    type="email",
                    placeholder="Enter contact email",
                    width="100%",
                    required=True,
                    variant="soft",
                    color_scheme="purple",  # Changed "accent" to "purple"
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        # Changed "accent" to "purple"
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            # Changed "accent" to "purple"
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                            # Changed "accent" to "purple"
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Contact Phone Input with Icon
            rx.vstack(
                rx.hstack(
                    rx.text("Contact Phone", weight="bold", color=rx.color("gray", 12)),
                    rx.text("*", color="red"),  # Add asterisk
                    spacing="1",
                ),
                rx.input(
                    rx.input.slot(
                        rx.icon("phone", color=rx.color("purple", 8))
                    ),  # Changed "accent" to "purple"
                    value=SupplierRegisterState.contact_phone,
                    on_change=SupplierRegisterState.set_contact_phone,
                    placeholder="Enter contact phone",
                    width="100%",
                    type="tel",
                    required=True,
                    variant="soft",
                    color_scheme="purple",  # Changed "accent" to "purple"
                    style={
                        "border": f"1px solid {rx.color('purple', 4)}",
                        # Changed "accent" to "purple"
                        "_focus": {
                            "border": f"2px solid {rx.color('purple', 6)}",
                            # Changed "accent" to "purple"
                            "box-shadow": f"0 0 0 3px {rx.color('purple', 3)}",
                            # Changed "accent" to "purple"
                        },
                    },
                ),
                spacing="1",
                width="100%",
            ),
            # Register Button with Loading State
            rx.button(
                rx.cond(
                    SupplierRegisterState.is_submitting,
                    rx.spinner(size="2"),
                    rx.text("Register"),
                ),
                type="submit",
                width="100%",
                size="3",
                color_scheme="purple",  # Changed "accent" to "purple"
                variant="solid",
                style={
                    "background": (
                        f"linear-gradient(45deg, {rx.color('purple', 8)},"
                        f"{rx.color('purple', 10)})"
                    ),  # Changed "accent" to "purple"
                    "_hover": {
                        "background": (
                            f"linear-gradient(45deg, {rx.color('purple', 9)},"
                            f"{rx.color('purple', 11)})"
                        ),
                        # Changed "accent" to "purple"
                    },
                    "transition": "all 0.3s ease",
                },
            ),
            # Login Link with Icon
            rx.center(
                rx.link(
                    rx.hstack(
                        rx.icon(
                            "log_in", size=16, color=rx.color("purple", 8)
                        ),  # Changed "accent" to "purple"
                        rx.text(
                            "Already registered? Log in here.",
                            color=rx.color("purple", 8),
                        ),  # Changed "accent" to "purple"
                        spacing="2",
                    ),
                    href=reflex_local_auth.routes.LOGIN_ROUTE,
                    _hover={"text_decoration": "underline"},
                ),
                width="100%",
            ),
            spacing="5",
            width="100%",
        ),
        on_submit=SupplierRegisterState.register_supplier,
    )


@template(
    route=routes.SUPPLIER_REGISTER_ROUTE,
    title="Supplier Registration",
    show_nav=False,
    on_load=SupplierRegisterState.clear_messages,
)
def supplier_register() -> rx.Component:
    return rx.center(
        rx.card(
            supplier_registration_form(),
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
        overflow="auto",  # Prevent content from stretching outside
        box_sizing="border-box",  # Ensure padding is included in width calculations
    )
