import reflex as rx

from inventory_system import routes, styles
from inventory_system.state.auth import AuthState
from inventory_system.state.logout_state import LogoutState
from inventory_system.state.profile_picture_state import ProfilePictureState

from .logout import logout_dialog


def user_avatar() -> rx.Component:
    """User avatar component with dropdown menu for
    authenticated users or login icon for guests."""
    # Define menu item style to match navbar menu_item hover effect
    menu_item_style = {
        "color": styles.text_color,  # Gray 11 for text
        "background_color": "transparent",  # No background by default
        "border_radius": styles.border_radius,  # Rounded corners
        "padding": "0.35em 0.5em",  # Slightly adjusted padding for better spacing
        "width": "100%",
        "cursor": "pointer",  # Ensure pointer cursor for interactivity
        "_hover": {
            "background_color": styles.accent_bg_color,
            # Light gray background (gray.3)
            "color": styles.accent_text_color,  # Consistent text color (gray.11)
            "opacity": "1",  # Full opacity on hover
        },
        "opacity": "0.95",  # Slightly faded when not hovered
        "transition": "background-color 0.2s ease, color 0.2s ease, opacity 0.2s ease",
        # Smooth transition
        "text_align": "left",  # Align text for dropdown
    }

    return rx.fragment(
        rx.cond(
            AuthState.authenticated_user,
            rx.menu.root(
                rx.menu.trigger(
                    rx.avatar(
                        src=ProfilePictureState.profile_picture,
                        name=AuthState.authenticated_user.username,
                        size="2",
                        data_testid="user-avatar",
                    ),
                ),
                rx.menu.content(
                    rx.menu.item(
                        "Profile",
                        on_click=lambda: rx.redirect(routes.PROFILE_ROUTE),
                        style=menu_item_style,
                    ),
                    rx.menu.item(
                        "Settings",
                        on_click=lambda: rx.redirect(routes.SETTINGS_ROUTE),
                        style=menu_item_style,
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        "Logout",
                        on_click=LogoutState.toggle_dialog,
                        style=menu_item_style,
                    ),
                    # Ensure menu content background is consistent
                    background_color=rx.color("gray", 1),  # Match navbar background
                    border=styles.border,  # Add border for clarity
                    border_radius=styles.border_radius,
                ),
            ),
            rx.button(
                rx.icon("log-in", size=20),
                on_click=lambda: rx.redirect(routes.LOGIN_ROUTE),
                variant="ghost",
                size="2",
                color_scheme="gray",
                padding="0.5em",
                _hover={
                    "color": styles.accent_text_color,
                    "background_color": styles.gray_bg_color,
                    "transition": "color 0.2s ease, background-color 0.2s ease",
                },
            ),
        ),
        logout_dialog(),
    )
