"""The about page."""

import reflex as rx

from .. import styles
from ..templates import template
from inventory_system import routes


@template(route=routes.ABOUT_ROUTE, title="About")
def about() -> rx.Component:
    """The about page.

    Returns:
        The UI for the about page.
    """
    return rx.vstack(
        rx.heading("About Inventory System", size="6"),
        rx.text("This is a temporary about page for the Inventory System application."),
        rx.text("More information will be added soon."),
        spacing="4",
        padding="6",
        width="100%",
        align_items="center",
    )
