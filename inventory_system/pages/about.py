"""The about page."""

import reflex as rx

from inventory_system import routes

from ..templates import template


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
                        style=rx.color_mode_cond(
                            light={
                                "background": "linear-gradient(45deg, #FF8C61 0%, #A3CFFA 100%)",
                                "-webkit-background-clip": "text",
                                "-webkit-text-fill-color": "transparent",
                            },
                            dark={
                                "background": "linear-gradient(45deg, #4A90E2 0%, #B19CD9 100%)",
                                "-webkit-background-clip": "text",
                                "-webkit-text-fill-color": "transparent",
                            },
                        ),
                        font_weight="bold",
                        text_align="center",
                        margin_bottom=[
                            "8px",
                            "10px",
                            "12px",
                        ],  # Responsive margin_bottom
                        transition="all 0.3s ease-in-out",
                        _hover={"transform": "scale(1.02)"},
                    ),
                    align="center",
                    spacing="3",
                ),
                # Description with modern typography
                rx.text(
                    "Welcome to the Inventory System—a sleek, modern solution for managing your telecom inventory with ease.",
                    font_size=["1rem", "1.2em", "1.3em"],  # Match Index page font size
                    color=rx.color_mode_cond(
                        light=rx.color("gray", 12),
                        dark="#E6F0FA",
                    ),
                    text_shadow=rx.color_mode_cond(
                        light="1px 1px 2px rgba(0, 0, 0, 0.3)",
                        dark="1px 1px 3px rgba(163, 207, 250, 0.5)",
                    ),
                    _hover={
                        "color": rx.color_mode_cond(
                            light=rx.color("gray", 11),
                            dark="#FFFFFF",
                        ),
                    },
                    text_align="center",
                    max_width=["90%", "80%", "600px"],  # Match Index page max_width
                    line_height="1.6",
                    margin_bottom=[
                        "20px",
                        "25px",
                        "30px",
                    ],  # Match Index page margin_bottom
                    transition="all 0.3s ease-in-out",
                ),
                rx.text(
                    "Streamline your operations, track assets, and stay organized—all in one place.",
                    font_size=[
                        "1rem",
                        "1.2em",
                        "1.3em",
                    ],  # Match Index page font size (adjusted for consistency)
                    color=rx.color_mode_cond(
                        light=rx.color("gray", 12),
                        dark="#E6F0FA",
                    ),
                    text_shadow=rx.color_mode_cond(
                        light="1px 1px 2px rgba(0, 0, 0, 0.3)",
                        dark="1px 1px 3px rgba(163, 207, 250, 0.5)",
                    ),
                    _hover={
                        "color": rx.color_mode_cond(
                            light=rx.color("gray", 11),
                            dark="#FFFFFF",
                        ),
                    },
                    text_align="center",
                    max_width=["90%", "80%", "600px"],  # Match Index page max_width
                    line_height="1.6",
                    margin_bottom=[
                        "20px",
                        "25px",
                        "30px",
                    ],  # Match Index page margin_bottom
                    transition="all 0.3s ease-in-out",
                ),
                # Call-to-action link (typography already aligns with Index page button styles)
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
                # Temporary toggle button for testing modes
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
        # Updated background to match Index page
        background=rx.color_mode_cond(
            light="linear-gradient(135deg, #D5E3F0 0%, #F5E8D8 100%)",  # Light mode gradient
            dark="linear-gradient(135deg, #0A0F2A 0%, #1A2A4A 100%)",  # Dark mode gradient
        ),
        background_position="center",
        background_size="cover",
        overflow="hidden",
        box_sizing="border-box",
    )
