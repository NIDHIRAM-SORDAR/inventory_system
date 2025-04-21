"""Sidebar component for the app."""

import reflex as rx

from inventory_system import routes
from inventory_system.components.avatar import user_avatar
from inventory_system.state.auth import AuthState

from .. import styles


def sidebar_header() -> rx.Component:
    """Sidebar header.

    Returns:
        The sidebar header component.

    """
    return rx.hstack(
        # The logo.
        rx.color_mode_cond(
            rx.image(src="/reflex_black.svg", height="1.5em"),
            rx.image(src="/reflex_white.svg", height="1.5em"),
        ),
        rx.spacer(),
        user_avatar(),  # Add the user avatar here
        align="center",
        width="100%",
        padding="0.35em",
        margin_bottom="1em",
    )


def sidebar_footer() -> rx.Component:
    """Sidebar footer.

    Returns:
        The sidebar footer component.

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


def sidebar_item_icon(icon: str) -> rx.Component:
    return rx.icon(icon, size=18)


def sidebar_item(text: str, url: str) -> rx.Component:
    """Sidebar item."""
    active = (rx.State.router.page.path == url.lower()) | (
        (rx.State.router.page.path == routes.OVERVIEW_ROUTE) & text == "Overview"
    )

    return rx.link(
        rx.hstack(
            rx.match(
                text,
                ("Overview", sidebar_item_icon("home")),
                ("Table", sidebar_item_icon("table-2")),
                ("About", sidebar_item_icon("book-open")),
                ("Admin Dashboard", sidebar_item_icon("shield")),
                sidebar_item_icon("layout-dashboard"),
            ),
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
            transition="background-color 0.2s ease, color 0.2s ease",  # Smooth hover
        ),
        underline="none",
        href=url,
        width="100%",
    )


def sidebar() -> rx.Component:
    """The sidebar."""
    from reflex.page import get_decorated_pages

    # Define ordered page routes
    ordered_page_routes = [
        routes.OVERVIEW_ROUTE,
        routes.TABLE_ROUTE,
        routes.ABOUT_ROUTE,
        routes.ADMIN_ROUTE,
    ]

    pages = get_decorated_pages()
    # Filter pages to include only those in ordered_page_routes
    filtered_pages = [page for page in pages if page["route"] in ordered_page_routes]
    ordered_pages = sorted(
        filtered_pages,
        key=lambda page: (
            ordered_page_routes.index(page["route"])
            if page["route"] in ordered_page_routes
            else len(ordered_page_routes)
        ),
    )

    return rx.flex(
        rx.vstack(
            sidebar_header(),
            rx.vstack(
                *[
                    rx.cond(
                        AuthState.is_admin & (page["route"] == routes.ADMIN_ROUTE),
                        sidebar_item(
                            text=page.get("title", "Admin Dashboard"),
                            url=page["route"],
                        ),
                        rx.cond(
                            page["route"] != routes.ADMIN_ROUTE,
                            sidebar_item(
                                text=page.get(
                                    "title", page["route"].strip("/").capitalize()
                                ),
                                url=page["route"],
                            ),
                            rx.fragment(),
                        ),
                    )
                    for page in ordered_pages
                ],
                spacing="1",
                width="100%",
            ),
            rx.spacer(),
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
        transition="width 0.3s ease",  # Smooth transition
    )
