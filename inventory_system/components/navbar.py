"""Navbar component for the app."""

import reflex as rx

from inventory_system import routes, styles
from inventory_system.components.avatar import user_avatar
from inventory_system.state.auth import AuthState


def menu_item_icon(icon: str) -> rx.Component:
    return rx.icon(icon, size=20)


def menu_item(text: str, url: str) -> rx.Component:
    """Menu item."""
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == routes.get_route("overview")) & text == "Overview"
    )

    return rx.link(
        rx.hstack(
            rx.match(
                text,
                ("Overview", menu_item_icon("home")),
                ("Table", menu_item_icon("table-2")),
                ("About", menu_item_icon("book-open")),
                ("Admin Dashboard", menu_item_icon("shield")),
                menu_item_icon("layout-dashboard"),
            ),
            rx.text(text, size="4", weight="regular"),
            color=rx.cond(
                active,
                styles.accent_text_color,
                styles.text_color,
            ),
            style={
                "_hover": {
                    "background_color": rx.cond(
                        active,
                        styles.accent_bg_color,
                        styles.gray_bg_color,
                    ),
                    "color": rx.cond(
                        active,
                        styles.accent_text_color,
                        styles.text_color,
                    ),
                    "opacity": "1",
                },
                "opacity": rx.cond(
                    active,
                    "1",
                    "0.95",
                ),
            },
            align="center",
            border_radius=styles.border_radius,
            width="100%",
            spacing="2",
            padding="0.35em",
            transition="background-color 0.2s ease, color 0.2s ease",  # Smooth hover
        ),
        underline="none",
        href=url,
        width="100%",
    )


def navbar_footer() -> rx.Component:
    """Navbar footer.

    Returns:
        The navbar footer component.
    """
    return rx.hstack(
        rx.link(
            rx.text("Docs", size="3"),
            href="https://reflex.dev/docs/getting-started/introduction/",
            color_scheme="gray",
            underline="none",
        ),
        rx.link(
            rx.text("Blog", size="3"),
            href="https://reflex.dev/blog/",
            color_scheme="gray",
            underline="none",
        ),
        rx.spacer(),
        rx.color_mode.button(style={"opacity": "0.8", "scale": "0.95"}),
        justify="start",
        align="center",
        width="100%",
        padding="0.35em",
    )


# Navigation configuration using your routes.py structure
NAVIGATION_CONFIG = [
    {
        "route_name": "overview",
        "title": "Overview",
        "icon": "home",
        "show_for_all": True,
    },
    {
        "route_name": "table",
        "title": "Table",
        "icon": "table-2",
        "show_for_all": True,
    },
    {
        "route_name": "about",
        "title": "About",
        "icon": "book-open",
        "show_for_all": True,
    },
    {
        "route_name": "admin",
        "title": "Admin Dashboard",
        "icon": "shield",
        "show_for_all": False,  # Only show for users with admin permissions
        "required_permission": "manage_users",
    },
]


def get_navigation_pages():
    """Get navigation pages using the routes configuration."""
    return [
        {
            "route": routes.get_route(config["route_name"]),
            "title": config["title"],
            "icon": config.get("icon", "layout-dashboard"),
            "show_for_all": config.get("show_for_all", True),
            "required_permission": config.get("required_permission"),
        }
        for config in NAVIGATION_CONFIG
    ]


def menu_button() -> rx.Component:
    """Menu button with drawer for navigation."""
    pages = get_navigation_pages()

    return rx.drawer.root(
        rx.drawer.trigger(
            rx.icon("align-justify"),
        ),
        rx.drawer.overlay(z_index="5"),
        rx.drawer.portal(
            rx.drawer.content(
                rx.vstack(
                    rx.hstack(
                        rx.spacer(),
                        rx.drawer.close(rx.icon(tag="x")),
                        justify="end",
                        width="100%",
                    ),
                    rx.divider(),
                    *[
                        rx.cond(
                            # Show admin pages only if user has required permissions
                            page.get("required_permission") is not None,
                            rx.cond(
                                AuthState.permissions.contains(
                                    page["required_permission"]
                                ),
                                menu_item(
                                    text=page["title"],
                                    url=page["route"],
                                ),
                                rx.fragment(),
                            ),
                            # Show regular pages for everyone
                            rx.cond(
                                page["show_for_all"],
                                menu_item(
                                    text=page["title"],
                                    url=page["route"],
                                ),
                                rx.fragment(),
                            ),
                        )
                        for page in pages
                    ],
                    rx.spacer(),
                    navbar_footer(),
                    spacing="4",
                    width="100%",
                ),
                top="auto",
                left="auto",
                height="100%",
                width="20em",
                padding="1em",
                bg=rx.color("gray", 1),
                transition="transform 0.3s ease",  # Smooth drawer transition
            ),
            width="100%",
        ),
        direction="right",
    )


def navbar() -> rx.Component:
    """The navbar.

    Returns:
        The navbar component.
    """
    return rx.el.nav(
        rx.hstack(
            rx.color_mode_cond(
                rx.image(src="/reflex_black.svg", height="1em"),
                rx.image(src="/reflex_white.svg", height="1em"),
            ),
            rx.spacer(),
            rx.hstack(
                user_avatar(),
                menu_button(),
                spacing="2",
            ),
            align="center",
            width="100%",
            padding_y="1.25em",
            padding_x=["0.5em", "0.5em", "1em", "1em", "1em", "2em"],  # Responsive
        ),
        display=["block", "block", "block", "block", "block", "none"],
        position="sticky",
        background_color=rx.color("gray", 1),
        top="0px",
        z_index="5",
        border_bottom=styles.border,
        transition="padding 0.3s ease",
    )
