"""Navbar component for the app."""

import reflex as rx

from inventory_system import routes, styles
from inventory_system.state.auth import AuthState
from inventory_system.state.logout_state import LogoutState
from inventory_system.state.profile_picture_state import ProfilePictureState

from ..components.logout import logout_dialog


def menu_item_icon(icon: str) -> rx.Component:
    return rx.icon(icon, size=20)


def menu_item(text: str, url: str) -> rx.Component:
    """Menu item.

    Args:
        text: The text of the item.
        url: The URL of the item.

    Returns:
        rx.Component: The menu item component.
    """
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == routes.OVERVIEW_ROUTE) & text == "Overview"
    )

    return rx.link(
        rx.hstack(
            rx.match(
                text,
                ("Overview", menu_item_icon("home")),
                ("Table", menu_item_icon("table-2")),
                ("About", menu_item_icon("book-open")),
                ("Profile", menu_item_icon("user")),
                ("Settings", menu_item_icon("settings")),
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


def user_avatar() -> rx.Component:
    """User avatar component with dropdown menu for authenticated users or login button for guests."""
    return rx.fragment(
        rx.cond(
            AuthState.authenticated_user.id >= 0,
            rx.menu.root(
                rx.menu.trigger(
                    rx.avatar(
                        src=ProfilePictureState.profile_picture,
                        name=AuthState.authenticated_user.username,
                        size="2",
                    ),
                ),
                rx.menu.content(
                    rx.menu.item(
                        "Profile", on_click=lambda: rx.redirect(routes.PROFILE_ROUTE)
                    ),
                    rx.menu.item(
                        "Settings", on_click=lambda: rx.redirect(routes.SETTINGS_ROUTE)
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        "Logout", on_click=LogoutState.toggle_dialog
                    ),  # Trigger dialog
                ),
            ),
            rx.button(
                "Login", on_click=lambda: rx.redirect(routes.LOGIN_ROUTE), size="3"
            ),
        ),
        logout_dialog(),  # Include the reusable dialog
    )


def menu_button() -> rx.Component:
    """Menu button with drawer for navigation."""
    from reflex.page import get_decorated_pages

    ordered_page_routes = [
        routes.OVERVIEW_ROUTE,
        routes.TABLE_ROUTE,
        routes.ABOUT_ROUTE,
        routes.PROFILE_ROUTE,
        routes.SETTINGS_ROUTE,
    ]

    pages = get_decorated_pages()
    ordered_pages = sorted(
        pages,
        key=lambda page: (
            ordered_page_routes.index(page["route"])
            if page["route"] in ordered_page_routes
            else len(ordered_page_routes)
        ),
    )

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
                        menu_item(
                            text=page.get(
                                "title", page["route"].strip("/").capitalize()
                            ),
                            url=page["route"],
                        )
                        for page in ordered_pages
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
            padding_x=["1em", "1em", "2em"],
        ),
        display=["block", "block", "block", "block", "block", "none"],
        position="sticky",
        background_color=rx.color("gray", 1),
        top="0px",
        z_index="5",
        border_bottom=styles.border,
    )
