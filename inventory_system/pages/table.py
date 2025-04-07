"""The table page."""

import reflex as rx

from ..backend.table_state import TableState
from ..templates import template
from ..views.table import main_table
from inventory_system import routes


@template(route=routes.TABLE_ROUTE, title="Table", on_load=TableState.load_entries)
def table() -> rx.Component:
    """The table page.

    Returns:
        The UI for the table page.

    """
    return rx.vstack(
        rx.heading("Table", size="5"),
        main_table(),
        spacing="8",
        width="100%",
    )
