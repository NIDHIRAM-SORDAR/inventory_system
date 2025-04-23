import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.supplier_approval_state import SupplierApprovalState
from inventory_system.templates.template import template

from ..components.status_badge import status_badge


def _header_cell(text: str, icon: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.icon(icon, size=18),
            rx.text(text),
            align="center",
            spacing="2",
        ),
    )


def _create_dialog(
    user: rx.Var,
    icon_name: str,
    color_scheme: str,
    dialog_title: str,
    action_handler: rx.EventHandler,
    disabled: rx.Var[bool] = rx.Var.create(False),
) -> rx.Component:
    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(
            rx.icon_button(
                rx.icon(icon_name),
                color_scheme=color_scheme,
                size="2",
                variant="solid",
                disabled=disabled,
            )
        ),
        rx.alert_dialog.content(
            rx.alert_dialog.title(dialog_title),
            rx.alert_dialog.description(
                f"Are you sure you want to {dialog_title.lower()} for {user['username']}? "  # noqa: E501
                "This action cannot be undone.",
                size="2",
            ),
            rx.inset(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Username"),
                            rx.table.column_header_cell("Email"),
                            rx.table.column_header_cell("Status"),
                        ),
                    ),
                    rx.table.body(
                        rx.table.row(
                            rx.table.row_header_cell(user["username"]),
                            rx.table.cell(user["email"]),
                            rx.table.cell(status_badge(user["role"].to(str))),
                        ),
                    ),
                ),
                side="x",
                margin_top="24px",
                margin_bottom="24px",
            ),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                        on_click=SupplierApprovalState.cancel_supplier_action,
                    )
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Confirm",
                        color_scheme=color_scheme,
                        size="2",
                        on_click=action_handler,
                    )
                ),
                spacing="3",
                justify="end",
            ),
            style={"max_width": 500},
        ),
    )


def _approve_dialog(user: rx.Var) -> rx.Component:
    return _create_dialog(
        user,
        "check",
        "grass",
        "Approve Supplier",
        SupplierApprovalState.approve_supplier(user["id"]),
        disabled=(user["role"] == "supplier") | (user["role"] == "admin"),
    )


def _revoke_dialog(user: rx.Var) -> rx.Component:
    return _create_dialog(
        user,
        "ban",
        "tomato",
        "Revoke Supplier",
        SupplierApprovalState.revoke_supplier(user["id"]),
        disabled=user["role"] != "supplier",
    )


def _delete_dialog(user: rx.Var) -> rx.Component:
    return _create_dialog(
        user,
        "trash-2",
        "tomato",
        "Delete Supplier",
        SupplierApprovalState.delete_supplier(user["id"]),
    )


def _dialog_group(user: rx.Var) -> rx.Component:
    return rx.hstack(
        _approve_dialog(user),
        _revoke_dialog(user),
        _delete_dialog(user),
        align="center",
        spacing="2",
        width="100%",
    )


def _show_supplier(user: rx.Var, index: int) -> rx.Component:
    bg_color = rx.cond(index % 2 == 0, rx.color("gray", 1), rx.color("accent", 2))
    hover_color = rx.cond(index % 2 == 0, rx.color("gray", 3), rx.color("accent", 3))
    return rx.table.row(
        rx.table.row_header_cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(status_badge(user["role"].to(str))),
        rx.table.cell(_dialog_group(user)),
        style={"_hover": {"bg": hover_color}, "bg": bg_color},
        align="center",
    )


def _pagination_view() -> rx.Component:
    return rx.hstack(
        rx.text(
            "Page ",
            rx.code(SupplierApprovalState.page_number),
            f" of {SupplierApprovalState.total_pages}",
            justify="end",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevrons-left", size=18),
                on_click=SupplierApprovalState.first_page,
                opacity=rx.cond(SupplierApprovalState.page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    SupplierApprovalState.page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-left", size=18),
                on_click=SupplierApprovalState.prev_page,
                opacity=rx.cond(SupplierApprovalState.page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    SupplierApprovalState.page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=18),
                on_click=SupplierApprovalState.next_page,
                opacity=rx.cond(
                    SupplierApprovalState.page_number
                    == SupplierApprovalState.total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    SupplierApprovalState.page_number
                    == SupplierApprovalState.total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevrons-right", size=18),
                on_click=SupplierApprovalState.last_page,
                opacity=rx.cond(
                    SupplierApprovalState.page_number
                    == SupplierApprovalState.total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    SupplierApprovalState.page_number
                    == SupplierApprovalState.total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
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


@template(
    route=routes.SUPPLIER_APPROVAL_ROUTE,
    title="Supplier Approval",
    on_load=SupplierApprovalState.check_auth_and_load,
)
@reflex_local_auth.require_login
def supplier_approval() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.heading("Supplier Approval", size="3"),
                rx.spacer(),
                rx.button(
                    "Back to Admin",
                    rx.icon("arrow-left"),
                    color_scheme="blue",
                    variant="soft",
                    size="2",
                    on_click=lambda: rx.redirect(routes.ADMIN_ROUTE),
                ),
                width="100%",
                align="center",
            ),
            rx.flex(
                rx.cond(
                    SupplierApprovalState.sort_reverse,
                    rx.icon(
                        "arrow-down-z-a",
                        size=28,
                        stroke_width=1.5,
                        cursor="pointer",
                        on_click=SupplierApprovalState.toggle_sort,
                    ),
                    rx.icon(
                        "arrow-down-a-z",
                        size=28,
                        stroke_width=1.5,
                        cursor="pointer",
                        on_click=SupplierApprovalState.toggle_sort,
                    ),
                ),
                rx.select(
                    ["username", "email"],
                    placeholder="Sort By: Username",
                    size="3",
                    on_change=SupplierApprovalState.set_sort_value,
                ),
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    rx.input.slot(
                        rx.icon("x"),
                        justify="end",
                        cursor="pointer",
                        on_click=SupplierApprovalState.setvar("search_value", ""),
                        display=rx.cond(
                            SupplierApprovalState.search_value, "flex", "none"
                        ),
                    ),
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
