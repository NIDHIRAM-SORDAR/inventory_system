# inventory_system/components/logout_dialog.py
import reflex as rx
from ..state.logout_state import LogoutState

def logout_dialog(
    title: str = "Log Out",
    description: str = "Are you sure you want to log out?",
    cancel_text: str = "Cancel",
    confirm_text: str = "Confirm",
    cancel_color: str = "gray",
    confirm_color: str = "red",
) -> rx.Component:
    """Reusable logout confirmation dialog component."""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(description),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        cancel_text,
                        on_click=LogoutState.cancel_logout,
                        color_scheme=cancel_color,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        confirm_text,
                        on_click=LogoutState.confirm_logout,
                        color_scheme=confirm_color,
                    ),
                ),
                spacing="2",
                justify="end",  # Align buttons to the right
            ),
        ),
        open=LogoutState.dialog_open,  # Use the built-in open prop
    )