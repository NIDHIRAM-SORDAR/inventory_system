# components/confirmation.py
import reflex as rx


def confirmation_dialog(
    state: rx.State,
    dialog_open_var: rx.Var,
    action_handler: rx.EventHandler,
    cancel_handler: rx.EventHandler,  # Add cancel handler parameter
    target_id_var: rx.Var,
    target_id: str,
    title: str,
    description: str,
    confirm_color: str = "blue",
) -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(description),
            rx.hstack(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=cancel_handler,  # Add the cancel handler
                    )
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Confirm",
                        on_click=action_handler,
                        color_scheme=confirm_color,
                    )
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=dialog_open_var & (target_id_var == target_id),
    )
