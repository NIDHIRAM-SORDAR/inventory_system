import reflex as rx
import reflex_local_auth

from inventory_system import routes
from inventory_system.state.supplier_approval_state import SupplierApprovalState
from inventory_system.styles import border_radius
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


def _edit_dialog(user: rx.Var) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.icon_button(
                rx.icon("square-pen"),
                color_scheme="blue",
                size=rx.breakpoints(initial="1", md="2"),
                variant="soft",
                on_click=SupplierApprovalState.open_edit_dialog(user["id"]),
            )
        ),
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Edit Supplier"),
                rx.desktop_only(
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
                                    rx.table.cell(status_badge(user["status"].to(str))),
                                ),
                            ),
                            width="100%",
                        ),
                        side="x",
                        margin_y="24px",
                    ),
                ),
                rx.mobile_and_tablet(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Username:", weight="bold"),
                            rx.text(user["username"]),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.text("Email:", weight="bold"),
                            rx.text(user["email"]),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.text("Status:", weight="bold"),
                            rx.text(user["status"]),
                            spacing="2",
                            align="center",
                        ),
                        spacing="4",
                        width="100%",
                        padding_y="16px",
                    ),
                ),
                rx.form.root(
                    rx.vstack(
                        rx.el.input(
                            type="hidden",
                            name="supplier_id",
                            value=user["id"],
                        ),
                        rx.checkbox(
                            "Approve Supplier",
                            name="approve",
                            checked=SupplierApprovalState.approve_checked,
                            on_change=SupplierApprovalState.toggle_approve,
                        ),
                        rx.checkbox(
                            "Revoke Supplier",
                            name="revoke",
                            checked=SupplierApprovalState.revoke_checked,
                            on_change=SupplierApprovalState.toggle_revoke,
                        ),
                        rx.button(
                            "Save",
                            type="submit",
                            color_scheme="blue",
                            size="2",
                            width=rx.breakpoints(initial="100%", md="auto"),
                            border_radius=border_radius,
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    on_submit=SupplierApprovalState.handle_submit,
                    reset_on_submit=True,
                ),
                rx.dialog.close(
                    rx.button(
                        "Close",
                        variant="soft",
                        color_scheme="gray",
                        size="2",
                        width=rx.breakpoints(initial="100%", md="120px"),
                        border_radius=border_radius,
                        on_click=SupplierApprovalState.cancel_dialog,
                    ),
                    justify=rx.breakpoints(initial="center", md="end"),
                    width="100%",
                    margin_top="16px",
                ),
                spacing="4",
                width="100%",
                padding="16px",
            ),
            style={
                "max_width": rx.breakpoints(initial="90vw", md="500px"),
                "width": "100%",
            },
        ),
        open=SupplierApprovalState.show_edit_dialog
        & (SupplierApprovalState.edit_supplier_id == user["id"]),
    )


def _delete_dialog(user: rx.Var) -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.icon_button(
                rx.icon("trash-2"),
                color_scheme="tomato",
                size=rx.breakpoints(initial="1", md="2"),
                variant="soft",
                on_click=SupplierApprovalState.open_delete_dialog(user["id"]),
            )
        ),
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Delete Supplier"),
                rx.dialog.description(
                    f"Are you sure you want to delete supplier {user['username']}? "
                    "This action cannot be undone.",
                    size="2",
                ),
                rx.desktop_only(
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
                                    rx.table.cell(status_badge(user["status"].to(str))),
                                ),
                            ),
                            width="100%",
                        ),
                        side="x",
                        margin_y="24px",
                    ),
                ),
                rx.mobile_and_tablet(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Username:", weight="bold"),
                            rx.text(user["username"]),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.text("Email:", weight="bold"),
                            rx.text(user["email"]),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.text("Status:", weight="bold"),
                            rx.text(user["status"]),
                            spacing="2",
                            align="center",
                        ),
                        spacing="4",
                        width="100%",
                        padding_y="16px",
                    ),
                ),
                rx.flex(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            size="2",
                            width=rx.breakpoints(initial="100%", md="120px"),
                            border_radius=border_radius,
                            on_click=SupplierApprovalState.cancel_dialog,
                        )
                    ),
                    rx.button(
                        "Delete",
                        color_scheme="tomato",
                        size="2",
                        width=rx.breakpoints(initial="100%", md="auto"),
                        border_radius=border_radius,
                        on_click=SupplierApprovalState.delete_supplier(user["id"]),
                    ),
                    direction=rx.breakpoints(initial="column", sm="row"),
                    spacing="3",
                    justify=rx.breakpoints(initial="center", md="end"),
                    width="100%",
                    padding_top="16px",
                ),
                spacing="4",
                width="100%",
                padding="16px",
            ),
            style={
                "max_width": rx.breakpoints(initial="90vw", md="500px"),
                "width": "100%",
            },
        ),
        open=SupplierApprovalState.show_delete_dialog
        & (SupplierApprovalState.edit_supplier_id == user["id"]),
    )


def _dialog_group(user: rx.Var) -> rx.Component:
    return rx.hstack(
        _edit_dialog(user),
        _delete_dialog(user),
        align="center",
        spacing="1",
        width="100%",
    )


def _show_supplier(user: rx.Var, index: int) -> rx.Component:
    bg_color = rx.cond(index % 2 == 0, rx.color("gray", 1), rx.color("accent", 2))
    hover_color = rx.cond(index % 2 == 0, rx.color("gray", 3), rx.color("accent", 3))
    return rx.table.row(
        rx.table.row_header_cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(status_badge(user["status"].to(str))),
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
        flex_direction=rx.breakpoints(initial="column", sm="row"),
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
                flex_direction=["column", "column", "row"],
                align="center",
                justify="end",
                spacing="3",
                width="100%",
            ),
            direction="column",
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
            width=rx.breakpoints(initial="100%", md="90%"),
        ),
        _pagination_view(),
        width="100%",
        padding_x=["auto", "auto", "2em"],
        padding_top=["1em", "1em", "2em"],
    )
