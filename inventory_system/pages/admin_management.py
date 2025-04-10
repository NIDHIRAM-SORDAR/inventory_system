import reflex as rx
import reflex_local_auth
from ..templates import template
from ..state import AdminManagementState
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


def _show_user(user: rx.Var, index: int) -> rx.Component:
    bg_color = rx.cond(index % 2 == 0, rx.color("gray", 1), rx.color("accent", 2))
    hover_color = rx.cond(index % 2 == 0, rx.color("gray", 3), rx.color("accent", 3))
    return rx.table.row(
        rx.table.row_header_cell(user["username"]),
        rx.table.cell(user["email"]),
        rx.table.cell(user["role"]),
        rx.table.cell(
            rx.hstack(
                rx.button(
                    "Make Admin",
                    on_click=lambda: AdminManagementState.confirm_change_role(user["id"], True),
                    color_scheme="blue",
                    disabled=(user["role"] == "admin") | (user["role"] == "supplier"),
                ),
                rx.button(
                    "Make Employee",
                    on_click=lambda: AdminManagementState.confirm_change_role(user["id"], False),
                    color_scheme="green",
                    disabled=(user["role"] == "employee") | (user["role"] == "supplier"),
                ),
                rx.button(
                    "Delete",
                    on_click=lambda: AdminManagementState.confirm_delete_user(user["id"]),
                    color_scheme="red",
                ),
                spacing="2",
                justify="center",
            ),
        ),
        # Updated confirmation dialogs with direct Var access
        confirmation_dialog(
            state=AdminManagementState,
            dialog_open_var=AdminManagementState.show_admin_dialog,
            action_handler=lambda: AdminManagementState.change_user_role(user["id"], True),
            cancel_handler=AdminManagementState.cancel_role_change,
            target_id_var=AdminManagementState.target_user_id,
            target_id=user["id"],
            title="Make Admin",
            description=f"Are you sure you want to make {user['username']} an admin?",
            confirm_color="blue",
        ),
        confirmation_dialog(
            state=AdminManagementState,
            dialog_open_var=AdminManagementState.show_employee_dialog,
            action_handler=lambda: AdminManagementState.change_user_role(user["id"], False),
            cancel_handler=AdminManagementState.cancel_role_change,
            target_id_var=AdminManagementState.target_user_id,
            target_id=user["id"],
            title="Make Employee",
            description=f"Are you sure you want to make {user['username']} an employee?",
            confirm_color="green",
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.content(
                rx.alert_dialog.title("Delete User"),
                rx.alert_dialog.description(f"Are you sure you want to delete user {user['username']}? This action cannot be undone."),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancel",
                            on_click=AdminManagementState.cancel_delete,
                            variant="soft",
                            color_scheme="gray"
                        )
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Delete",
                            on_click=AdminManagementState.delete_user,
                            color_scheme="red"
                        )
                    ),
                    spacing="3",
                    justify="end",
                ),
            ),
            open=AdminManagementState.show_delete_dialog & (AdminManagementState.user_to_delete == user["id"]),
        ),
        style={"_hover": {"bg": hover_color}, "bg": bg_color},
        align="center",
    )


def _pagination_view() -> rx.Component:
    return rx.hstack(
        rx.text(
            "Page ",
            rx.code(AdminManagementState.page_number),
            f" of {AdminManagementState.total_pages}",
            justify="end",
        ),
        rx.hstack(
            rx.icon_button(
                rx.icon("chevrons-left", size=18),
                on_click=AdminManagementState.first_page,
                opacity=rx.cond(AdminManagementState.page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    AdminManagementState.page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-left", size=18),
                on_click=AdminManagementState.prev_page,
                opacity=rx.cond(AdminManagementState.page_number == 1, 0.6, 1),
                color_scheme=rx.cond(
                    AdminManagementState.page_number == 1, "gray", "accent"
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevron-right", size=18),
                on_click=AdminManagementState.next_page,
                opacity=rx.cond(
                    AdminManagementState.page_number
                    == AdminManagementState.total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    AdminManagementState.page_number
                    == AdminManagementState.total_pages,
                    "gray",
                    "accent",
                ),
                variant="soft",
            ),
            rx.icon_button(
                rx.icon("chevrons-right", size=18),
                on_click=AdminManagementState.last_page,
                opacity=rx.cond(
                    AdminManagementState.page_number
                    == AdminManagementState.total_pages,
                    0.6,
                    1,
                ),
                color_scheme=rx.cond(
                    AdminManagementState.page_number
                    == AdminManagementState.total_pages,
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
    route=routes.ADMIN_MGMT,
    title="Admin Management",
    on_load=AdminManagementState.check_auth_and_load,
)
@reflex_local_auth.require_login
def admin_management() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.heading("Admin Management", size="3"),
                rx.spacer(),
                width="100%",
            ),
            rx.flex(
                rx.cond(
                    AdminManagementState.sort_reverse,
                    rx.icon(
                        "arrow-down-z-a",
                        size=28,
                        stroke_width=1.5,
                        cursor="pointer",
                        on_click=AdminManagementState.toggle_sort,
                    ),
                    rx.icon(
                        "arrow-down-a-z",
                        size=28,
                        stroke_width=1.5,
                        cursor="pointer",
                        on_click=AdminManagementState.toggle_sort,
                    ),
                ),
                rx.select(
                    ["username", "email", "role"],
                    placeholder="Sort By: Username",
                    size="3",
                    on_change=AdminManagementState.set_sort_value,
                ),
                rx.input(
                    rx.input.slot(rx.icon("search")),
                    rx.input.slot(
                        rx.icon("x"),
                        justify="end",
                        cursor="pointer",
                        on_click=AdminManagementState.setvar("search_value", ""),
                        display=rx.cond(
                            AdminManagementState.search_value, "flex", "none"
                        ),
                    ),
                    value=AdminManagementState.search_value,
                    placeholder="Search here...",
                    size="3",
                    max_width=["150px", "150px", "200px", "250px"],
                    width="100%",
                    variant="surface",
                    color_scheme="gray",
                    on_change=AdminManagementState.set_search_value,
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
            AdminManagementState.admin_error_message,
            rx.text(AdminManagementState.admin_error_message, color="red"),
            rx.fragment(),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    _header_cell("Username", "user"),
                    _header_cell("Email", "mail"),
                    _header_cell("Role", "shield"),
                    _header_cell("Actions", "settings"),
                ),
            ),
            rx.table.body(
                rx.foreach(
                    AdminManagementState.current_page,
                    lambda user, index: _show_user(user, index),
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
