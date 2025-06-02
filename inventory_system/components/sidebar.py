"""Sidebar component for the app."""

import reflex as rx

from inventory_system import routes
from inventory_system.state.auth import AuthState
from inventory_system.state.logout_state import LogoutState
from inventory_system.state.profile_picture_state import ProfilePictureState

from .. import styles


def sidebar_header() -> rx.Component:
    """Sidebar header."""
    return rx.hstack(
        rx.color_mode_cond(
            rx.image(src="/reflex_black.svg", height="1.5em"),
            rx.image(src="/reflex_white.svg", height="1.5em"),
        ),
        rx.spacer(),
        align="center",
        width="100%",
        padding="0.35em",
        margin_bottom="1em",
    )


def sidebar_footer() -> rx.Component:
    """Sidebar footer."""
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


def sidebar_item_icon(icon: str) -> rx.Component:
    return rx.icon(icon, size=18)


def sidebar_item(text: str, icon: str, url: str) -> rx.Component:
    """Sidebar item with icon support."""
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == routes.get_route("overview"))
        & (text == "Overview")
    )

    return rx.link(
        rx.hstack(
            sidebar_item_icon(icon),  # Use the provided icon
            rx.text(text, size="3", weight="regular"),
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
            transition="background-color 0.2s ease, color 0.2s ease",
        ),
        underline="none",
        href=url,
        width="100%",
    )


def sidebar_bottom_profile() -> rx.Component:
    """Sidebar bottom profile section."""

    # Define a helper to create a sidebar item with on_click instead of href
    def sidebar_item_with_onclick(
        text: str, icon: str, on_click: rx.EventHandler
    ) -> rx.Component:
        active = False  # Log out doesn't have an active state
        return rx.link(
            rx.hstack(
                sidebar_item_icon(icon),
                rx.text(text, size="3", weight="regular"),
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
                transition="background-color 0.2s ease, color 0.2s ease",
            ),
            on_click=on_click,
            underline="none",
            width="100%",
        )

    return rx.vstack(
        rx.divider(),
        rx.vstack(
            sidebar_item("Settings", "settings", routes.get_route("settings")),
            sidebar_item("Profile", "user-round-pen", routes.get_route("profile")),
            sidebar_item_with_onclick("Log out", "log-out", LogoutState.toggle_dialog),
            spacing="1",
            width="100%",
        ),
        rx.hstack(
            rx.avatar(
                src=ProfilePictureState.profile_picture,
                name=AuthState.authenticated_user.username,
                size="2",
                radius="full",
            ),
            rx.vstack(
                rx.box(
                    rx.text(
                        AuthState.authenticated_user.username,
                        size="3",
                        weight="bold",
                    ),
                    rx.text(
                        AuthState.user_email,
                        size="1",
                        weight="medium",
                    ),
                    width="100%",
                ),
                spacing="0",
                align="start",
                justify="start",
                width="100%",
            ),
            padding_x="0.5rem",
            align="center",
            justify="start",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


# Sidebar navigation configuration using your routes.py structure
SIDEBAR_NAVIGATION_CONFIG = [
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


def get_sidebar_navigation_pages():
    """Get sidebar navigation pages using the routes configuration."""
    return [
        {
            "route": routes.get_route(config["route_name"]),
            "title": config["title"],
            "icon": config["icon"],
            "show_for_all": config.get("show_for_all", True),
            "required_permission": config.get("required_permission"),
        }
        for config in SIDEBAR_NAVIGATION_CONFIG
    ]


def sidebar() -> rx.Component:
    """The sidebar."""
    pages = get_sidebar_navigation_pages()

    return rx.flex(
        rx.vstack(
            sidebar_header(),
            rx.vstack(
                *[
                    rx.cond(
                        # Show admin pages only if user has required permissions
                        page.get("required_permission") is not None,
                        rx.cond(
                            AuthState.permissions.contains(page["required_permission"]),
                            sidebar_item(
                                text=page["title"],
                                icon=page["icon"],
                                url=page["route"],
                            ),
                            rx.fragment(),
                        ),
                        # Show regular pages for everyone
                        rx.cond(
                            page["show_for_all"],
                            sidebar_item(
                                text=page["title"],
                                icon=page["icon"],
                                url=page["route"],
                            ),
                            rx.fragment(),
                        ),
                    )
                    for page in pages
                ],
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
            sidebar_bottom_profile(),
            sidebar_footer(),
            justify="end",
            align="end",
            width=styles.sidebar_content_width,
            height="100dvh",
            padding="1em",
        ),
        display=["none", "none", "none", "none", "none", "flex"],
        max_width=styles.sidebar_width,
        width="auto",
        height="100%",
        position="sticky",
        justify="end",
        top="0px",
        left="0px",
        flex="1",
        bg=rx.color("gray", 2),
        transition="width 0.3s ease",
        z_index="5",
    )
