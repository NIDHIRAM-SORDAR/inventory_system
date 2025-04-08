# inventory_system/pages/logout.py
import reflex as rx
from ..state import LogoutState
from ..templates import template
from inventory_system import routes

@template(route=routes.LOGOUT_ROUTE, title="Logout")
def logout_page() -> rx.Component:
    """Render a minimal logout confirmation page."""
    return rx.center(
        rx.vstack(
            rx.heading("Log Out", size="7"),
            rx.button(
                "Confirm Logout",
                on_click=LogoutState.confirm_logout,  # Direct handler
                color_scheme="red",
            ),
            rx.button(
                "Cancel",
                on_click=lambda: rx.redirect(routes.OVERVIEW_ROUTE),  # Simple redirect for cancel
                color_scheme="gray",
            ),
            spacing="4",
        ),
        padding_top="2em",
        width="100%",
        height="100vh",
        align="center",
        justify="center",
    )