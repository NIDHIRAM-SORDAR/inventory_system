import reflex as rx
import reflex_local_auth
from inventory_system.templates.template import template
from ..state import SupplierApprovalState
from inventory_system import routes
from ..components.comfirmation import confirmation_dialog


def _header_cell(text: str, icon: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="2",
        ),
    )

def _show_supplier(user: rx.Var, index: int) -> rx.Component:
    bg_color = rx.cond(index % 2 == 0, rx.color("gray", 1), rx.color("accent", 2))
    hover_color = rx.cond(index % 2 == 0, rx.color("gray", 3), rx.color("accent", 3))
    return rx.table.row(
        rx.table.row_header_cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(user["role"]),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Approve Supplier",
                    on_click=lambda: SupplierApprovalState.confirm_change_supplier_status(user["id"], True),
                    color_scheme="purple",
                    disabled=(user["role"] == "supplier") | (user["role"] == "admin"),
                ),
                rx.button(
                    "Revoke Supplier",
                    on_click=lambda: SupplierApprovalState.confirm_change_supplier_status(user["id"], False),
                    color_scheme="orange",
                    disabled=user["role"] != "supplier",
                ),
                spacing="2",
                justify="center",
            )
        ),
        confirmation_dialog(
            state=SupplierApprovalState,
            dialog_open_var=SupplierApprovalState.show_approve_dialog,
            action_handler=lambda: SupplierApprovalState.change_supplier_status(user["id"], True),
            cancel_handler=SupplierApprovalState.cancel_supplier_action,  # Add cancel handler
            target_id_var=SupplierApprovalState.target_supplier_id,
            target_id=user["id"],
            title="Approve Supplier",
            description=f"Are you sure you want to approve {user['username']} as a supplier?",
            confirm_color="purple",
        ),
        confirmation_dialog(
            state=SupplierApprovalState,
            dialog_open_var=SupplierApprovalState.show_revoke_dialog,
            action_handler=lambda: SupplierApprovalState.change_supplier_status(user["id"], False),
            cancel_handler=SupplierApprovalState.cancel_supplier_action,  # Add cancel handler
            target_id_var=SupplierApprovalState.target_supplier_id,
            target_id=user["id"],
            title="Revoke Supplier",
            description=f"Are you sure you want to revoke supplier status for {user['username']}?",
            confirm_color="orange",
        ),
        style={"_hover": {"bg": hover_color}, "bg": bg_color},
        align="center",
    )

def _pagination_view() -> rx.Component:
    return rx.hstack(
        rx.text("Page ", rx.code(SupplierApprovalState.page_number), f" of {SupplierApprovalState.total_pages}", justify="end"),
        rx.hstack(
            rx.icon_button(rx.icon("chevrons-left", size=18), on_click=SupplierApprovalState.first_page, opacity=rx.cond(SupplierApprovalState.page_number == 1, 0.6, 1), color_scheme=rx.cond(SupplierApprovalState.page_number == 1, "gray", "accent"), variant="soft"),
            rx.icon_button(rx.icon("chevron-left", size=18), on_click=SupplierApprovalState.prev_page, opacity=rx.cond(SupplierApprovalState.page_number == 1, 0.6, 1), color_scheme=rx.cond(SupplierApprovalState.page_number == 1, "gray", "accent"), variant="soft"),
            rx.icon_button(rx.icon("chevron-right", size=18), on_click=SupplierApprovalState.next_page, opacity=rx.cond(SupplierApprovalState.page_number == SupplierApprovalState.total_pages, 0.6, 1), color_scheme=rx.cond(SupplierApprovalState.page_number == SupplierApprovalState.total_pages, "gray", "accent"), variant="soft"),
            rx.icon_button(rx.icon("chevrons-right", size=18), on_click=SupplierApprovalState.last_page, opacity=rx.cond(SupplierApprovalState.page_number == SupplierApprovalState.total_pages, 0.6, 1), color_scheme=rx.cond(SupplierApprovalState.page_number == SupplierApprovalState.total_pages, "gray", "accent"), variant="soft"),
            align="center",
            spacing="2",
            justify="end",
        ),
        spacing="5",
        margin_top="1em",
        align="center",
        width="100%",
        justify="end",
    )

@template(route=routes.SUPPLIER_APPROV_ROUTE, title="Supplier Approval", on_load=SupplierApprovalState.check_auth_and_load)
@reflex_local_auth.require_login
def supplier_approval() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.heading("Supplier Approval", size="3"),
                rx.spacer(),
                width="100%",
            ),
            rx.flex(
                rx.cond(
                    SupplierApprovalState.sort_reverse,
                    rx.icon("arrow-down-z-a", size=28, stroke_width=1.5, cursor="pointer", on_click=SupplierApprovalState.toggle_sort),
                    rx.icon("arrow-down-a-z", size=28, stroke_width=1.5, cursor="pointer", on_click=SupplierApprovalState.toggle_sort),
                ),
                rx.select(
                    ["username", "email", "role"],
                    placeholder="Sort By: Username",
                    size="3",
                    on_change=SupplierApprovalState.set_sort_value,
                ),
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    rx.input.slot(rx.icon("x"), justify="end", cursor="pointer", on_click=SupplierApprovalState.setvar("search_value", ""), display=rx.cond(SupplierApprovalState.search_value, "flex", "none")),
                    value=SupplierApprovalState.search_value,
                    placeholder="Search here...",
                    size="3",
                    max_width=["150px", "150px", "200px", "250px"],
                    width="100%",
                    variant="surface",
                    color_scheme="gray",
                    on_change=SupplierApprovalState.set_search_value,
                ),
                align="center",
                justify="end",
                spacing="3",
            ),
            spacing="3",
            justify="between",
            wrap="wrap",
            width="100%",
            padding_bottom="1em",
        ),
        rx.cond(
            SupplierApprovalState.supplier_success_message,
            rx.callout(SupplierApprovalState.supplier_success_message, icon="check", color_scheme="green", width="100%"),
        ),
        rx.cond(
            SupplierApprovalState.supplier_error_message,
            rx.callout(SupplierApprovalState.supplier_error_message, icon="triangle_alert", color_scheme="red", width="100%"),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    _header_cell("Username", "user"),
                    _header_cell("Email", "mail"),
                    _header_cell("Status", "shield"),
                    _header_cell("Actions", "settings"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    SupplierApprovalState.current_page,
                    lambda user, index: _show_supplier(user, index),
                )
            ),
            variant="surface",
            size="3",
            width="100%",
        ),
        _pagination_view(),
        width="100%",
        padding="16px",
    )