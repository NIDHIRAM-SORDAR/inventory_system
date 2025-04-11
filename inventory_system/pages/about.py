"""The about page."""

import reflex as rx

from .. import styles
from ..templates import template
from inventory_system import routes


@template(route=routes.ABOUT_ROUTE, title="About", show_nav=False)
def about() -> rx.Component:
    """The about page.

    Returns:
        The UI for the about page.
    """
    return rx.center(
        rx.card(
            rx.vstack(
                # Heading with icon and gradient text
                rx.hstack(
                    rx.icon("info", size=32, color=rx.color("purple", 10)),
                    rx.heading(
                        "About Inventory System",
                        size="8",  # String number for Reflex convention
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
                # Description with modern typography
                rx.text(
                    "Welcome to the Inventory System—a sleek, modern solution for managing your telecom inventory with ease.",
                    font_size=["1rem", "1.1rem", "1.2rem"],  # Responsive font size
                    color=rx.color("gray", 11),
                    _dark={"color": rx.color("gray", 3)},
                    text_align="center",
                    max_width="600px",
                    line_height="1.6",
                ),
                rx.text(
                    "Streamline your operations, track assets, and stay organized—all in one place.",
                    font_size=["0.9rem", "1rem", "1rem"],  # Responsive font size
                    color=rx.color("gray", 10),
                    _dark={"color": rx.color("gray", 4)},
                    text_align="center",
                    max_width="600px",
                    line_height="1.6",
                ),
                # Call-to-action link
                rx.link(
                    rx.hstack(
                        rx.icon("arrow_right", size=16, color=rx.color("purple", 8)),
                        rx.text(
                            "Explore the System",
                            color=rx.color("purple", 8),
                            font_weight="500",
                        ),
                        spacing="2",
                    ),
                    href=routes.OVERVIEW_ROUTE,
                    _hover={"text_decoration": "underline"},
                    transition="color 0.3s ease",
                ),
                spacing="5",
                align_items="center",
                width="100%",
                padding=["1em", "1.5em", "2em"],  # Responsive padding
            ),
            width="100%",
            max_width=["90%", "80%", "700px"],  # Responsive max_width
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
        width="100%",
        max_width="100%",
        min_height="85vh",
        align="center",
        justify="center",
        background=rx.color("gray", 2),
        _dark={"background": rx.color("gray", 11)},
        overflow="hidden",
        box_sizing="border-box",
    )